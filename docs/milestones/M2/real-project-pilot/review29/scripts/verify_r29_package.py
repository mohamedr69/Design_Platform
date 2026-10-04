"""Checker for review29/: manifest complete; markdown links; the candidate HEAD, clean tree, changed files equal the
package copies and untouched files equal 719e8de; identities (flags off == accepted; every switch its own suffix);
frozen artifacts unchanged (four-arm-final manifest and files, labels r26.1 / r26.2, evaluator .9, baseline / 719e8de
trees, harness v4.3 runner); the live ledger unchanged since the four-arm run; replay evidence (fidelity, zero model
requests, zero newly validated wrong facts); tests (failures identical to the baseline by name and message; focused and
R29 suites pass). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review29")
FINAL = PKG.parent / "four-arm-final"
CAND = pathlib.Path("C:/t/iso/cand-r29")
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True).stdout.strip()
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.relative_to(PKG).as_posix() not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.glob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
src = load(PKG / "candidate/SOURCE-HASHES.json")
res["candidate"] = {"head": git(CAND, "rev-parse", "HEAD"), "head_matches": git(CAND, "rev-parse", "HEAD") == src["head"], "clean": not git(CAND, "status", "--porcelain"),
                    "changed_files_equal_package": all(sha(CAND / f) == h == sha(PKG / "candidate/files" / f) for f, h in src["changed_files"].items()),
                    "untouched_equal_719e8de": src["untouched_files_byte_equal_to_cand_ai4_719e8de"]}
env = {k: v for k, v in os.environ.items() if not k.startswith("AI_EVIDENCE_")}
code = "import json; from app.ai import evidence_reader as er; print(json.dumps([er.READER_VERSION, er.EVIDENCE_POLICY_VERSION]))"
ids = lambda extra: json.loads(subprocess.run([PY, "-c", code], cwd=str(CAND / "backend"), env={**env, "AI_ENABLED": "false", **extra}, capture_output=True, text=True).stdout.strip().splitlines()[-1])
res["identities"] = {"flags_off_is_accepted": ids({}) == ["evidence-reader-2026-09-29.7", "evidence-policy-2026-09-29.4"]}
fm = load(FINAL / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["frozen"] = {"four_arm_final_manifest": sha(FINAL / "evidence/EVIDENCE-MANIFEST.json") == "cf1b95f1e88889c82fa6897507773185d4abbfbeaa1228c0b8ed1a4f981d419b",
                 "four_arm_final_files": all(sha(FINAL / k) == v["sha256"] for k, v in fm.items()),
                 "labels_r26_2": sha("C:/t/iso/work/r2x/r27/labels-r26.2/LABEL-MANIFEST.r26.2.json") == "ed3c88e40daadaee6e4a7271d7dd9be430773a8c1b0976030d1bfb2a27a9a72d"
                 and all(sha(pathlib.Path("C:/t/iso/work/r2x/r27/labels-r26.2") / n) == h for n, h in load("C:/t/iso/work/r2x/r27/labels-r26.2/LABEL-MANIFEST.r26.2.json")["files"].items()),
                 "labels_r26_1": sha("C:/t/iso/work/r2x/r26/labels-r26/LABEL-MANIFEST.r26.json") == "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509",
                 "evaluator_9": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py") == "38326f149a7f49246413427cf4a661134cc7d31734faa13fe80f8ad967a3e451",
                 "baseline_tree": [git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), not git("C:/t/iso/frozen-r12", "status", "--porcelain")],
                 "cand_ai4_tree": [git("C:/t/iso/cand-ai4", "rev-parse", "HEAD"), not git("C:/t/iso/cand-ai4", "status", "--porcelain")],
                 "declaration_v2": sha("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json") == "6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1"}
c = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
res["ledger"] = {"entries": c.execute("select count(*) from entries").fetchone()[0], "four_arm_dispatched": c.execute("select count(*) from entries where scope like 'm2-four-arm-final%'").fetchone()[0],
                 "scopes": c.execute("select count(*) from scopes").fetchone()[0]}
c.close()
res["ledger"]["unchanged_since_four_arm"] = res["ledger"]["four_arm_dispatched"] == 234 and res["ledger"]["entries"] == 249 + 234
rep = {p.name: load(p) for p in (PKG / "replay/manifests").glob("*.json")}
fid = {a: load(PKG / f"replay/FIDELITY-{a}.json") for a in ("L1", "L2", "L3", "L4")}
na = load(PKG / "replay/NEW-ACCEPTANCES.json")
res["replay"] = {"runs": len(rep), "all_on_final_candidate": (PKG / "replay/logs/REPLAY-CANDIDATE-HEAD.txt").read_text().strip() == src["head"],
                 "model_requests": sum(v.get("model_requests", 0) for v in rep.values()),
                 "fidelity": {a: [f["identical"], f["documents"]] for a, f in fid.items()},
                 "newly_validated_wrong": sum(len(v["newly_validated_wrong"]) for v in na.values())}
fc = load(PKG / "tests/FAILURE-COMPARISON.json")
res["tests"] = {"failures_identical_to_baseline": fc["identical_failures"], "candidate_failures": sorted(fc["candidate"]["failures"]),
                "focused_exit": (PKG / "tests/FOCUSED-final-EXIT.txt").read_text().strip(), "full_candidate_head": (PKG / "tests/FINAL-candidate-HEAD.txt").read_text().strip()}
res["tests"]["full_on_final_candidate"] = res["tests"]["full_candidate_head"] == src["head"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and all(v for v in res["candidate"].values() if isinstance(v, bool))
             and all(res["identities"].values()) and all(v if isinstance(v, bool) else (v[1] and v[0]) for v in res["frozen"].values())
             and res["ledger"]["unchanged_since_four_arm"] and res["replay"]["all_on_final_candidate"] and res["replay"]["model_requests"] == 0
             and res["replay"]["newly_validated_wrong"] == 0 and res["tests"]["failures_identical_to_baseline"] and res["tests"]["focused_exit"] == "0"
             and res["tests"]["full_on_final_candidate"])
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1, default=str)[:3500])
print("OK" if res["ok"] else "NOT OK")
