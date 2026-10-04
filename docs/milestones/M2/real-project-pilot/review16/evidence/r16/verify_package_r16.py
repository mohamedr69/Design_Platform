"""Checker for the review16 package (run after the final edit): manifest (no missing / changed / unlisted file), relative
links, FREEZE-R16 hashes and the accepted application's source hashes, earlier packages unchanged, historical files
equal to Review 15's, recorded exit codes (focused 0; reviewer test 0 on r16.1, 1 on r15.1), replay deltas all zero
with complete accounting, overlay counts B=3 / C=2, and the probe outcomes. Writes PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review16")
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
            if not (md.parent / l).resolve().exists():
                broken.append((md.name, l))
res["markdown_links"] = {"checked": links, "broken": broken}
fz = json.loads((EV / "r16/FREEZE-R16.json").read_text(encoding="utf-8"))
res["freeze"] = {"files": len(fz["files_sha256"]), "mismatch": [k for k, v in fz["files_sha256"].items() if sha(EV / "r16" / k) != v],
                 "application_source_mismatch": [f for f, v in fz["application_baseline"]["source_sha256"].items() if sha(pathlib.Path("C:/t/iso/frozen-r12") / f) != v],
                 "unchanged_from_r15": fz["unchanged_from_r15"]}
head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
res["application"] = {"head": head, "clean": not dirty}
earlier = {}
for pk in ("review13", "review14", "review15"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
res["historical_equal_to_review15"] = all(sha(p) == sha(PKG.parent / "review15/evidence/historical" / p.relative_to(EV / "historical"))
                                          for p in (EV / "historical").rglob("*") if p.is_file())
rg = EV / "r16/regression"
res["exit_codes"] = {"focused_tests": (rg / "pytest_exit_code.txt").read_text().strip(),
                     "reviewer_test_on_r16": (rg / "review16_contract_on_r16.exit.txt").read_text().strip(),
                     "reviewer_test_on_r15": (rg / "review16_contract_on_r15.exit.txt").read_text().strip()}
junit = (rg / "r16__focused_tests.xml").read_text(encoding="utf-8")
res["focused_junit"] = {k: re.search(fr'{k}="(\d+)"', junit).group(1) for k in ("tests", "failures", "errors", "skipped")}
rp = json.loads((EV / "r16/REPLAY-BOQ-r16.json").read_text(encoding="utf-8"))
res["replay"] = {k: {"deltas": v["row_deltas"], "held": len(v["held_rows"]),
                     "accounting_ok": v["accounting"]["emitted"]["complete_and_disjoint"] and v["accounting"]["truth"]["complete"]} for k, v in rp["runs"].items()}
ovr = json.loads((EV / "r16/OVERLAY-RECHECK-r16.json").read_text(encoding="utf-8"))["runs"]
res["overlay"] = {k: (v["evaluator_critical"], v["overlay_critical"]) for k, v in ovr.items()}
a15 = json.loads((EV / "r16/probes/assoc-r15/ADDITIONAL-PROBES.json").read_text(encoding="utf-8"))
a16 = json.loads((EV / "r16/probes/assoc-r16/ADDITIONAL-PROBES.json").read_text(encoding="utf-8"))
p15 = json.loads((EV / "r16/probes/review15-probes-on-r16/PROBE-RESULTS.json").read_text(encoding="utf-8"))
res["probes"] = {"assoc_r15": [a15["mixed_geometry"]["crossed_verified_anchor"], a15["mixed_geometry"]["crossed_without_anchor_emitted"], a15["geometry_ambiguity"]["replay_outcomes"]],
                 "assoc_r16": [a16["mixed_geometry"]["crossed_verified_anchor"], a16["mixed_geometry"]["crossed_without_anchor_emitted"], a16["geometry_ambiguity"]["replay_outcomes"]],
                 "review15_on_r16": [p15["budget"]["total_scripted_provider_calls"], p15["row_join"]["single_misread_duplicate"]["held"],
                                     [v["critical_after_overlay"] for v in p15["overlay"].values()]]}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and not res["freeze"]["mismatch"]
             and not res["freeze"]["application_source_mismatch"] and head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty
             and all(earlier.values()) and res["historical_equal_to_review15"] and res["exit_codes"] == {"focused_tests": "0", "reviewer_test_on_r16": "0", "reviewer_test_on_r15": "1"}
             and res["focused_junit"] == {"tests": "66", "failures": "0", "errors": "0", "skipped": "0"}
             and all(all(d == 0 for d in v["deltas"].values()) and v["accounting_ok"] for v in res["replay"].values())
             and res["overlay"]["small-B__original"] == (3, 3) and res["overlay"]["small-C__original"] == (2, 2)
             and res["probes"]["assoc_r16"][:2] == [False, False] and set(res["probes"]["assoc_r16"][2].values()) == {"held_ambiguous_join"}
             and res["probes"]["review15_on_r16"][0] == 12)
(EV / "PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1)[:3000])
