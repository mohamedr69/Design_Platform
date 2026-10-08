"""Run the M6 shadow-evaluation harness end to end through its command line
on the synthetic clone the tests build (tests/test_m6_attribution._clone),
for each arm; write the reports beside this evidence (ORCH-043). The test
package's conftest is imported first, so the platform settings point at a
temporary database, never the live one.

    cd backend && python -B ../docs/milestones/M6/evidence/attribution/scripts/harness_synthetic.py <workdir>"""
import json
import sys
from pathlib import Path

BACKEND = Path.cwd()
sys.path.insert(0, str(BACKEND))
EVIDENCE = Path(__file__).resolve().parents[1]

from tests import conftest  # noqa: E402,F401 -- temporary DATABASE_URL before anything imports the app
from tests.test_m6_attribution import _clone, _labels  # noqa: E402

sys.path.insert(0, str(BACKEND / "scripts"))
import m6_shadow_eval as harness  # noqa: E402

work = Path(sys.argv[1])
work.mkdir(parents=True, exist_ok=True)
labels = work / "labels.json"
labels.write_text(json.dumps(_labels()), encoding="utf-8")
answers = work / "answers.json"
answers.write_text(json.dumps([
    {"primary_type": "SHOP_DRAWING", "system_code": "FAS", "confidence": "high"},
    {"primary_type": "SHOP_DRAWING", "confidence": "medium"},
    {"primary_type": "SPECIFICATION"},
    {"primary_type": "OTHER", "confidence": "low"},
    {"primary_type": "IFC_DRAWING", "confidence": "low"},
]), encoding="utf-8")
summary = {}
for arm, stored in (("stored", True), ("rules", False), ("ai", False)):
    clone = _clone(work / f"clone-{arm}.db", stored=stored)
    out = EVIDENCE / f"harness-synthetic-{arm}.json"
    argv = ["--database", str(clone), "--arm", arm, "--labels", str(labels), "--out", str(out)]
    if arm == "ai":
        argv += ["--scripted-answers", str(answers)]
    assert harness.main(argv) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    report["labels"]["sha256"] = "synthetic"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    m = report["all"]
    summary[arm] = {k: m[k] for k in ("labelled", "joined", "answered", "type_accuracy", "system_accuracy", "attribution_accuracy",
                                      "false_supported_rate", "false_our_scope_rate", "false_our_scope_rate_incl_likely")}
print(json.dumps(summary, indent=1))
