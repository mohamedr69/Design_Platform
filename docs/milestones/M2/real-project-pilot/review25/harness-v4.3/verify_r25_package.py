"""Checker for review25/: manifest complete, markdown links, trees unchanged (no application change), harness v4.3 files
equal the hashes frozen BEFORE the final validation (workspace and package), arm_ev.py unchanged vs v4.2, scoring files
equal review22's frozen v4, reviewer files (Review 25) unchanged, earlier packages (review13..review24) and labels unchanged,
recorded tests (submitted 62-test set green with pytest exit 0; R25 regressions green; the reviewer's neutral regressions
3 failed / 3 passed on v4.2 and 6 passed on v4.3; the original R24 provider regressions 3 passed on v4.3), the mutation
evidence (exit 5 / zero sends / unchanged state; control streak 3 and reconstructed stop), the legacy recheck, and the live
ledger untouched (128 settled; no r21..r25 live scope). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review25")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.glob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
b = load(PKG / "bindings/SOURCE-BINDINGS.json")
fz = load(PKG / "bindings/FROZEN-HARNESS.json")
res["trees"] = {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == b["accepted"]["commit"] and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                "frozen_r21_candidate": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == b["frozen_r21_candidate"]["commit"] == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain"),
                "reader_unchanged": sha("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py") == b["frozen_r21_candidate"]["evidence_reader_sha256"], "application_change": b["application_change"]}
res["harness_frozen"] = {"frozen_before_final_validation": fz.get("frozen_before_final_validation") is True,
                         "packaged_files_equal_frozen_hashes": all(sha(PKG / "harness-v4.3" / f) == h for f, h in fz["files"].items()),
                         "workspace_files_equal_frozen_hashes": all(sha(pathlib.Path("C:/t/iso/work/r2x/review25/harness-v4.3") / f) == h for f, h in fz["files"].items()),
                         "arm_ev_unchanged_vs_v4_2": fz["arm_ev_unchanged_vs_v4_2"], "validator": fz["validator_revision"], "journal_format": fz["journal_version"],
                         "scoring_files_unchanged_vs_review22": all(fz["scoring_files_unchanged_vs_review22"].values()), "changed_vs_v4_2": fz["changed_vs_review24_v4_2"], "new_vs_v4_2": fz["new_vs_review24_v4_2"],
                         "durable_allowance_module_unchanged": sha(fz["durable_allowance_module"]["file"]) == fz["durable_allowance_module"]["sha256"]}
res["reviewer_files_unchanged"] = all((MR / "reviews/M2-review-25" / n).exists() and sha(MR / "reviews/M2-review-25" / n) == h for n, h in b["reviewer_files_review25"].items())
res["reviewer_copies_match"] = b["reviewer_copies_match"]
res["reviewer_runner_is_submitted_v4_2"] = b["reviewer_runner_equals_review24_frozen"]
earlier = {}
for pk, h in b["earlier_package_manifests"].items():
    mp = PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json"
    earlier[pk] = sha(mp) == h and all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in load(mp)["files"].items())
res["earlier_packages_unchanged"] = earlier
res["labels_r21_unchanged"] = all(sha(PKG.parent / "review21/labels-r21" / n) == h for n, h in b["labels_r21_files"].items())
res["dry_inputs_unchanged"] = b["dry_inputs_unchanged"]


def junit(p):
    r = ET.parse(p).getroot()
    s = r if r.tag == "testsuite" else r.find("testsuite")
    return {k: int(s.get(k, 0)) for k in ("tests", "failures", "errors", "skipped")}


green = lambda n: {"tests": n, "failures": 0, "errors": 0, "skipped": 0}
t = {"SUBMITTED-62": junit(PKG / "harness-v4.3/logs/SUBMITTED-62.xml"), "NEUTRAL-V4.3": junit(PKG / "harness-v4.3/logs/NEUTRAL-V4.3.xml"),
     "REVIEWER-NEUTRAL-on-v4.2": junit(PKG / "repro/on-v4.2/NEUTRAL-REGRESSIONS.xml"), "REVIEWER-NEUTRAL-on-v4.3": junit(PKG / "repro/on-v4.3/NEUTRAL-REGRESSIONS.xml"),
     "R24-PROVIDER-on-v4.3": junit(PKG / "repro/r24-provider-probe-on-v4.3/REVIEW24-REGRESSIONS.xml")}
exits = {"SUBMITTED-62": (PKG / "logs/SUBMITTED-62.exit").read_text().strip(), "NEUTRAL-V4.3": (PKG / "logs/NEUTRAL-TESTS.exit").read_text().strip(),
         "REVIEWER-NEUTRAL-on-v4.2": (PKG / "repro/on-v4.2/NEUTRAL-REGRESSIONS.exit").read_text().strip(), "REVIEWER-NEUTRAL-on-v4.3": (PKG / "repro/on-v4.3/NEUTRAL-REGRESSIONS.exit").read_text().strip(),
         "R24-PROVIDER-on-v4.3": (PKG / "repro/r24-provider-probe-on-v4.3/REVIEW24-REGRESSIONS.exit").read_text().strip()}
res["tests"], res["pytest_exit_codes"] = t, exits
res["tests_ok"] = (t["SUBMITTED-62"] == green(62) and exits["SUBMITTED-62"] == "0" and t["NEUTRAL-V4.3"]["failures"] == t["NEUTRAL-V4.3"]["errors"] == 0 and t["NEUTRAL-V4.3"]["tests"] >= 30 and exits["NEUTRAL-V4.3"] == "0"
                   and t["REVIEWER-NEUTRAL-on-v4.2"] == {"tests": 6, "failures": 3, "errors": 0, "skipped": 0} and exits["REVIEWER-NEUTRAL-on-v4.2"] == "1"
                   and t["REVIEWER-NEUTRAL-on-v4.3"] == green(6) and exits["REVIEWER-NEUTRAL-on-v4.3"] == "0" and t["R24-PROVIDER-on-v4.3"] == green(3) and exits["R24-PROVIDER-on-v4.3"] == "0")
N = load(PKG / "neutral-evidence/NEUTRAL.json")["scenarios"]
res["mutation_evidence"] = {k: all(v["checks"].values()) for k, v in N.items()}
L = load(PKG / "neutral-evidence/LEGACY-RECHECK.json")
res["legacy_recheck"] = {"journals": L["journals"], "all_equal": L["all_equal"], "kinds_seen": L["kinds_seen"]}
old, new = load(PKG / "repro/on-v4.2/NEUTRAL-KIND-PROBE.json"), load(PKG / "repro/on-v4.3/NEUTRAL-KIND-PROBE.json")
res["reviewer_probe"] = {k: {"v4_2": (old[k]["load_before_resume"]["state"], old[k]["resume_exit"], old[k]["new_sends"], old[k]["status"]),
                             "v4_3": (new[k]["load_before_resume"]["state"], new[k]["resume_exit"], new[k]["new_sends"], new[k]["status"])} for k in ("budget", "cache_hit", "none")}
p24 = load(PKG / "repro/r24-provider-probe-on-v4.3/PROVIDER-BOUNDARY-PROBE.json")
res["r24_probe_on_v4_3"] = {k: (p24[k]["initial_exit"], p24[k]["resume_exit"], p24[k]["new_sends"], p24[k]["resume_status"]) for k in ("before_file", "after_file")}
Lg = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = Lg.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
live = Lg.execute("select count(*) from entries where scope like 'r2%-four-arm%' or scope like 'r22%' or scope like 'r23%' or scope like 'r24%' or scope like 'r25%'").fetchone()[0]
scopes = [s for (s,) in Lg.execute("select scope from scopes") if s.startswith(("r22", "r21-four-arm", "r23", "r24", "r25"))]
Lg.close()
res["ledger"] = {"settled_original_experiment": settled, "r21_to_r25_live_entries": live, "r21_to_r25_live_scopes": scopes}
rp = res["reviewer_probe"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(v for v in res["trees"].values() if isinstance(v, bool))
             and all(v for k, v in res["harness_frozen"].items() if isinstance(v, bool)) and res["reviewer_files_unchanged"] and res["reviewer_copies_match"] and res["reviewer_runner_is_submitted_v4_2"]
             and all(earlier.values()) and res["labels_r21_unchanged"] and all(res["dry_inputs_unchanged"].values()) and res["tests_ok"] and all(res["mutation_evidence"].values())
             and L["all_equal"] and all(v["v4_2"] == ("ok", 0, 16, "completed") and v["v4_3"][:3] == ("indeterminate", 5, 0) for v in rp.values())   # v4.3 status: the untouched run record of the killed run
             and res["r24_probe_on_v4_3"] == {"before_file": (98, 4, 0, "stopped"), "after_file": (98, 4, 0, "stopped")} and settled == 128 and live == 0 and not scopes)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("tests",)}, indent=1, default=str)[:4000])
print("tests", t, exits)
print("OK" if res["ok"] else "NOT OK")
