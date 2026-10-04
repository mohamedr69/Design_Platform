"""Checker for the review14 package, run after the final edit:
  1. every file listed in EVIDENCE-MANIFEST.json exists with its hash, and no unlisted file exists (except the manifest);
  2. every relative Markdown link in the package resolves;
  3. the frozen harness files equal FREEZE-R14.json;
  4. the original labels, packet v2 index and Review 13 worklist are byte-unchanged (hashes recorded in the amendment);
  5. the accepted application tree is 3d5607d and clean;
  6. the recorded test run's exit code is 0.
Writes PACKAGE-CHECK.json next to the manifest."""
import hashlib
import json
import pathlib
import re
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review14")
EV = PKG / "evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
res = {}
man = json.loads((EV / "EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
bad = [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]]
extra = [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
         and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]
res["manifest"] = {"files": len(man), "mismatched_or_missing": bad, "unlisted": extra}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for l in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if l.startswith(("http:", "https:", "mailto:")):
            continue
        links += 1
        if not (md.parent / l.strip("<>")).resolve().exists():
            broken.append((md.relative_to(PKG).as_posix(), l))
res["markdown_links"] = {"checked": links, "broken": broken}
fz = json.loads((EV / "r14/FREEZE-R14.json").read_text(encoding="utf-8"))
res["freeze"] = {"files": len(fz["files_sha256"]), "mismatch": [k for k, v in fz["files_sha256"].items() if sha(EV / "r14" / k) != v]}
amend = json.loads((EV / "labels/r14/AI-REVIEW-AMENDMENT-r14.1.json").read_text(encoding="utf-8"))
res["originals_unchanged"] = {k: sha(v["file"]) == v["sha256"] for k, v in amend["originals_sha256"].items()}
pv2 = PKG.parent / "review08/human-review-packet-v2/FINDINGS-INDEX.json"
res["packet_v2_findings_index"] = sha(pv2) == "530ed24ba903a2328c02bd27aea57ba329300012722a3faa4c40576d843703e2"
r13 = json.loads((PKG.parent / "review13/evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["review13_unchanged"] = all(sha(PKG.parent / "review13" / k) == v["sha256"] for k, v in r13.items())
head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
res["application"] = {"head": head, "clean": not dirty, "expected": head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"}
res["recorded_tests_exit_code"] = (EV / "r14/regression/pytest_exit_code.txt").read_text().strip()
res["ok"] = not bad and not extra and not broken and not res["freeze"]["mismatch"] and all(res["originals_unchanged"].values()) and \
    res["packet_v2_findings_index"] and res["review13_unchanged"] and res["application"]["expected"] and res["application"]["clean"] and res["recorded_tests_exit_code"] == "0"
(EV / "PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1)[:2500])
