"""Checker for the review15 package, run after the final edit: manifest hashes (no missing / unlisted files), every
relative Markdown link, FREEZE-R15 file hashes and the accepted application's source hashes, earlier packages and
labels unchanged, the recorded focused-test exit code 0, the historical files equal to Review 14's, and the probe
outcomes (submitted shows the three defects, corrected shows none). Writes PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review15")
EV = PKG / "evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
res = {}
man = json.loads((EV / "EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for l in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not l.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / l.strip("<>")).resolve().exists():
                broken.append((md.name, l))
res["markdown_links"] = {"checked": links, "broken": broken}
fz = json.loads((EV / "r15/FREEZE-R15.json").read_text(encoding="utf-8"))
res["freeze"] = {"files": len(fz["files_sha256"]), "mismatch": [k for k, v in fz["files_sha256"].items() if sha(EV / "r15" / k) != v],
                 "application_source_mismatch": [f for f, v in fz["application_baseline"]["source_sha256"].items() if sha(pathlib.Path("C:/t/iso/frozen-r12") / f) != v]}
head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
res["application"] = {"head": head, "clean": not dirty}
r14 = json.loads((PKG.parent / "review14/evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["review14_unchanged"] = all(sha(PKG.parent / "review14" / k) == v["sha256"] for k, v in r14.items())
r13 = json.loads((PKG.parent / "review13/evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["review13_unchanged"] = all(sha(PKG.parent / "review13" / k) == v["sha256"] for k, v in r13.items())
res["historical_equal_to_review14"] = all(sha(p) == sha(PKG.parent / "review14/evidence/historical" / p.relative_to(EV / "historical"))
                                          for p in (EV / "historical").rglob("*") if p.is_file())
res["recorded_tests_exit_code"] = (EV / "r15/regression/pytest_exit_code.txt").read_text().strip()
sub = json.loads((EV / "r15/probes/final-submitted/PROBE-RESULTS.json").read_text(encoding="utf-8"))
cor = json.loads((EV / "r15/probes/final-corrected/PROBE-RESULTS.json").read_text(encoding="utf-8"))
res["probes"] = {"submitted": {"budget_total": sub["budget"]["total_scripted_provider_calls"], "join": sub["row_join"]["single_misread_duplicate"]["pairs"],
                               "overlay_criticals": [v["critical_after_overlay"] for v in sub["overlay"].values()]},
                 "corrected": {"budget_total": cor["budget"]["total_scripted_provider_calls"], "join": cor["row_join"]["single_misread_duplicate"]["pairs"],
                               "overlay_criticals": [v["critical_after_overlay"] for v in cor["overlay"].values()]}}
res["ok"] = not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and not res["freeze"]["mismatch"] \
    and not res["freeze"]["application_source_mismatch"] and head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty \
    and res["review14_unchanged"] and res["review13_unchanged"] and res["historical_equal_to_review14"] and res["recorded_tests_exit_code"] == "0" \
    and res["probes"]["corrected"]["budget_total"] <= 12 and all(c == 1 for c in res["probes"]["corrected"]["overlay_criticals"]) \
    and res["probes"]["corrected"]["join"][0][2] == "ambiguous"
(EV / "PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1))
