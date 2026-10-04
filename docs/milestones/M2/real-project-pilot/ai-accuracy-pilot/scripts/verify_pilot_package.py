"""Checker for the ai-accuracy-pilot package (run after the final edit): manifest (no missing / changed / unlisted file),
relative Markdown links, the declaration hash and its recorded identities (accepted tree head / clean, candidate commit,
evaluator, labels, sample, r16.1 harness), earlier packages unchanged, recorded test exit codes, the ledger totals
(<= 150 settled, earlier scope untouched), business hashes equal across arms, and zero critical acceptances as recorded.
Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-accuracy-pilot")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
res = {}
man = json.loads((PKG / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
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
D = PKG / "declaration/PILOT-DECLARATION.json"
decl = json.loads(D.read_text(encoding="utf-8"))
res["declaration_sha256"] = sha(D)
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
res["accepted_tree"] = {"head": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                        "source_mismatch": [f for f, v in decl["code"]["accepted_app"]["source_sha256"].items() if sha(pathlib.Path("C:/t/iso/frozen-r12") / f) != v]}
res["candidate"] = {"head": git("C:/t/iso/cand-ai", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/cand-ai", "status", "--porcelain"),
                    "changed_files_match": all(sha(pathlib.Path("C:/t/iso/cand-ai") / f) == v for f, v in decl["code"]["candidate"]["changed_files"].items()),
                    "packaged_copy_matches": sha(PKG / "candidate/evidence_reader.py") == decl["code"]["candidate"]["changed_files"]["backend/app/ai/evidence_reader.py"]}
res["labels_match_declaration"] = all(sha(PKG / "labels" / n) == v for n, v in decl["labels"]["files"].items())
res["sample_matches_declaration"] = sha(PKG / "sample/PILOT-SAMPLE.json") == decl["sources"]["sample"]["sha256"]
res["stage_matches_declaration"] = sha(PKG / "sample/PILOT-STAGE.json") == decl["stage"]["manifest_sha256"]
res["boq_extraction_matches"] = sha(PKG / "boq/PILOT-BOQ-A-extraction.json") == decl["sources"]["boq_extraction_A"]["sha256"]
res["r16_harness_unchanged"] = all(sha(pathlib.Path("C:/t/iso/work/r2x/r16") / f) == v for f, v in decl["code"]["boq_harness_r16"].items())
earlier = {}
for pk in ("review13", "review14", "review15", "review16"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
T = PKG / "tests"
res["exit_codes"] = {f.stem: f.read_text().strip() for f in sorted(T.glob("*EXIT.txt"))}
res["junit"] = {}
for x in sorted(T.glob("*.xml")):
    s = x.read_text(encoding="utf-8")
    res["junit"][x.stem] = {k: int(re.search(fr'{k}="(\d+)"', s).group(1)) for k in ("tests", "failures", "errors", "skipped")}
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = {s["scope"]: con.execute("select count(*) from entries where scope = ? and state = 'settled'", (s["scope"],)).fetchone()[0] for s in decl["ledger"]["scopes"].values()}
earlier_scope = con.execute("select count(*) from entries where scope = 'r2x-small-2026-09-29'").fetchone()[0]
con.close()
res["ledger"] = {"settled_by_scope": settled, "total_settled": sum(settled.values()), "cap": 150, "earlier_scope_entries": earlier_scope}
met = json.loads((PKG / "results/PILOT-METRICS.json").read_text(encoding="utf-8"))
res["no_business_change"] = {k: v for k, v in met["no_business_change"].items() if k != "A"}
res["critical"] = {a: len(v["critical"]["all"]) for a, v in met["arms"].items() if "critical" in v}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken
             and res["declaration_sha256"] == "6218bb8f9bd97f0a55419929385729449d45299e95843f7a43a43f24a13b71cd"
             and res["accepted_tree"] == {"head": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "clean": True, "source_mismatch": []}
             and res["candidate"]["head"].startswith("e5a0a94") and res["candidate"]["clean"] and res["candidate"]["changed_files_match"] and res["candidate"]["packaged_copy_matches"]
             and res["labels_match_declaration"] and res["sample_matches_declaration"] and res["stage_matches_declaration"] and res["boq_extraction_matches"]
             and res["r16_harness_unchanged"] and all(earlier.values())
             and res["junit"].get("FOCUSED-off", {}).get("failures") == 0 and res["junit"].get("FOCUSED-G", {}).get("failures") == 0
             and res["junit"].get("FOCUSED-T", {}).get("failures") == 3 and res["junit"].get("FULL-flags-off", {}).get("failures") == 2
             and res["junit"].get("ACCEPTED-two-failures", {}).get("failures") == 2 and res["junit"].get("BOQ-QUEUE", {}).get("failures") == 0
             and res["ledger"]["total_settled"] <= 150 and earlier_scope == 113
             and all(v["equal_to_A"] for v in res["no_business_change"].values()) and set(res["critical"].values()) == {0})
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1)[:2500])
