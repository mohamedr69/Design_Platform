"""Checker for review30/: manifest (written last) complete and matching; markdown links; R30-01 commit and count checks over
every owner-facing document of this package AND the overlay, against the manifest candidate; the checker tests re-run
and pass; the candidate commit and clean tree; review29/ and four-arm-final/ unchanged (manifests and every file);
labels, evaluators, trees and the ledger unchanged; the verbatim thresholds present in their sources; the draft
declaration not executed and not authorized; the fresh-project candidates metadata-only; no authorization document.
Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess
import sys

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review30")
R29 = PKG.parent / "review29"
FINALPKG = PKG.parent / "four-arm-final"
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True).stdout.strip()
sys.path.insert(0, str(PKG / "scripts"))
import r30_checks as C  # noqa: E402

res = {}
mf = load(PKG / "evidence/EVIDENCE-MANIFEST.json")
man, final = mf["files"], mf["candidate_head"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.relative_to(PKG).as_posix() not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json")
                                and "__pycache__" not in p.parts]}
links, broken = 0, []
for md in list(PKG.glob("*.md")) + list((PKG / "review29-overlay").glob("*.md")):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
owner = {p.relative_to(PKG).as_posix(): p.read_text(encoding="utf-8") for p in list(PKG.glob("*.md")) + list((PKG / "review29-overlay").glob("*.md"))}
owner["DRAFT-DECLARATION.json"] = (PKG / "DRAFT-DECLARATION.json").read_text(encoding="utf-8")
junit = {**C.junit_module_counts(R29 / "tests" / "FOCUSED-final.xml"), **C.junit_module_counts(PKG / "tests" / "CHECKER-TESTS.xml")}   # R29 suites + this package's checker tests
res["r30_01"] = {"candidate_from_manifest": final, "commit_violations": C.check_commit_statements(owner, final, ["a4ce6a3", final]),
                 "count_violations": C.check_test_counts(owner, junit),
                 "original_review29_change_map_flagged": bool(C.check_commit_statements({"x": (R29 / "CHANGE-MAP.md").read_text(encoding="utf-8")}, final, ["a4ce6a3", final]))
                 and bool(C.check_test_counts({"x": (R29 / "CHANGE-MAP.md").read_text(encoding="utf-8")}, junit))}
t = subprocess.run([PY, "-m", "pytest", "-q", str(PKG / "scripts" / "test_r30_checks.py"), "-p", "no:cacheprovider"], capture_output=True, text=True,
                   cwd=str(PKG / "scripts"), env={**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"})
res["checker_tests"] = {"exit": t.returncode, "summary": t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr[-300:]}
res["candidate"] = {"head": git("C:/t/iso/cand-r29", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/cand-r29", "status", "--porcelain")}
r29m = load(R29 / "evidence/EVIDENCE-MANIFEST.json")
fam = load(FINALPKG / "evidence/EVIDENCE-MANIFEST.json")
res["frozen"] = {"review29_manifest": sha(R29 / "evidence/EVIDENCE-MANIFEST.json") == "ca3f33ad4fadec2072d52b6f90e618c90bfabc16b12bae054c21a8739210d87b",
                 "review29_files": all(sha(R29 / k) == v["sha256"] for k, v in r29m["files"].items()),
                 "review29_candidate_head": r29m["candidate_head"] == final,
                 "four_arm_final_manifest": sha(FINALPKG / "evidence/EVIDENCE-MANIFEST.json") == "cf1b95f1e88889c82fa6897507773185d4abbfbeaa1228c0b8ed1a4f981d419b",
                 "four_arm_final_files": all(sha(FINALPKG / k) == v["sha256"] for k, v in fam["files"].items()),
                 "labels_r26_2": sha("C:/t/iso/work/r2x/r27/labels-r26.2/LABEL-MANIFEST.r26.2.json") == "ed3c88e40daadaee6e4a7271d7dd9be430773a8c1b0976030d1bfb2a27a9a72d",
                 "labels_r26_1": sha("C:/t/iso/work/r2x/r26/labels-r26/LABEL-MANIFEST.r26.json") == "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509",
                 "evaluator_9": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py") == "38326f149a7f49246413427cf4a661134cc7d31734faa13fe80f8ad967a3e451",
                 "baseline_tree": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                 "cand_ai4_tree": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain")}
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
res["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0]}
con.close()
res["ledger"]["unchanged"] = res["ledger"] == {"entries": 483, "scopes": 17}
dd = load(PKG / "DRAFT-DECLARATION.json")
src_ok = []
for th in dd["thresholds_verbatim"]:
    texts = th["text"] if isinstance(th["text"], list) else [th["text"]]
    path = {"AI-ACCURACY-POLICY.md section 1": "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/AI-ACCURACY-POLICY.md",
            "M2-ACCEPTANCE-REPORT.md Correction 5 targets": "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-ACCEPTANCE-REPORT.md",
            "MASTER-ROADMAP.md M2": "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/MASTER-ROADMAP.md",
            "review21/ANALYSIS-PLAN.md section 5": "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21/ANALYSIS-PLAN.md"}[th["source"]]
    body = pathlib.Path(path).read_text(encoding="utf-8")
    src_ok.append({"source": th["source"], "hash_matches": sha(path) == th["sha256"], "verbatim": all(x in body for x in texts)})
res["thresholds_verbatim"] = src_ok
fc = load(PKG / "cohort/FRESH-PROJECT-CANDIDATES.json")
res["plan"] = {"declaration_not_executed": dd["executed"] is False and dd["budget_approved"] is False and dd["authorization"] is None and dd["cohort"]["chosen"] is None,
               "candidate_in_declaration": dd["code"]["candidate"]["commit"] == final,
               "minimum_12_per_field": dd["analysis"]["minimum_matched_per_claimed_field"] == 12,
               "fresh_candidates_metadata_only": fc["content_read"].startswith("none") and "NOT permitted" in fc["permission"],
               "fresh_projects_disjoint_from_used": not ({p["ep"] for p in fc["picked"] + fc["alternates"]} & set(load(PKG / "cohort/M2-USED-PROJECTS.json")["ep_referenced_in_m1_m2_docs_and_tests"])),
               "fresh_contractors_distinct": len({p["contractor"] for p in fc["picked"]}) == len(fc["picked"]) >= 4,
               "no_authorization_document": not any("AUTHORIZATION" in k.upper() for k in man)}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken
             and not res["r30_01"]["commit_violations"] and not res["r30_01"]["count_violations"] and res["r30_01"]["original_review29_change_map_flagged"]
             and res["checker_tests"]["exit"] == 0 and res["candidate"] == {"head": final, "clean": True} and all(res["frozen"].values())
             and res["ledger"]["unchanged"] and all(x["hash_matches"] and x["verbatim"] for x in src_ok) and all(res["plan"].values()))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1, default=str)[:3500])
print("OK" if res["ok"] else "NOT OK")
