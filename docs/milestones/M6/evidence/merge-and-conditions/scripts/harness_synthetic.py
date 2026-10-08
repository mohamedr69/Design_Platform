"""ORCH-049: run the M6 shadow-evaluation harness (HARNESS_VERSION .2)
through its command line on the synthetic clone the tests build
(tests/test_m6_attribution._clone), for each arm, and once more for the
stored arm with one stored answer marked as the model's (source "ai",
stored supported) -- to show the review-only cap and the per-source
breakdown. Writes the reports beside this evidence. The test package's
conftest is imported first, so the platform settings point at a temporary
database, never the live one. No model is called (RecordingProvider).

    cd backend && python -B ../docs/milestones/M6/evidence/merge-and-conditions/scripts/harness_synthetic.py <workdir>"""
import json
import sqlite3
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
for arm, stored, ai_row in (("stored", True, False), ("stored-with-ai-row", True, True), ("rules", False, False),
                            ("ai", False, False)):
    clone = _clone(work / f"clone-{arm}.db", stored=stored)
    if ai_row:
        conn = sqlite3.connect(clone)
        conn.execute("UPDATE document_classifications SET source = 'ai' WHERE document_id = "
                     "(SELECT id FROM project_documents WHERE sha256 = ?)", ("a2" * 32,))
        conn.commit()
        conn.close()
    out = EVIDENCE / f"harness-synthetic-{arm}.json"
    argv = ["--database", str(clone), "--arm", arm.split("-")[0], "--labels", str(labels), "--out", str(out)]
    if arm == "ai":
        argv += ["--scripted-answers", str(answers)]
    assert harness.main(argv) == 0
    report = json.loads(out.read_text(encoding="utf-8"))
    report["labels"]["sha256"] = "synthetic"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8", newline="\n")
    keys = ("labelled", "joined", "answered", "type_accuracy", "system_accuracy", "attribution_accuracy",
            "false_supported_rate", "false_our_scope_rate", "false_our_scope_rate_incl_likely")
    summary[arm] = {"harness_version": report["harness_version"], "all": {k: report["all"][k] for k in keys},
                    "by_source": {s: {k: m[k] for k in ("answered", "type_accuracy", "false_supported_rate")}
                                  for s, m in report["by_source"].items()},
                    **({"ai": report["ai"]} if "ai" in report else {}),
                    **({"stored": report["stored"]} if "stored" in report else {})}
print(json.dumps(summary, indent=1))
