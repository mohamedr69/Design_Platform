"""Copy the Review 07 evidence into the docs package and write its manifest (SHA-256 of every file). Docs only."""
import datetime
import hashlib
import json
import pathlib
import shutil
import subprocess

DOCS = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\review07")
EV = DOCS / "evidence"
W = pathlib.Path(r"C:\t\iso\work")
R7 = W / "r7"
REPO = pathlib.Path(r"C:\t\iso\ep-platform")
copies = {}


def add(dest, src):
    src = pathlib.Path(src)
    if src.exists() and src.is_file():
        copies[dest] = src


for f in (R7 / "eval5").glob("*.json"):
    add(f"eval6/{f.name}", f)
for f in (R7 / "eval5_superseded").glob("*.json"):
    add(f"eval5_superseded/{f.name}", f)
for name in ("replay-ai-ev1.json", "replay-ai-ev2.json", "replay-ai-ev1-transitions.json", "replay-ai-ev2-transitions.json",
             "ADJUDICATIONS.json", "GUARD-DRY-RUN-default.json", "GUARD-DRY-RUN-promoted.json", "LIVE-READONLY-UNCERTAIN-REFERENCE-CASES.json",
             "tables.md", "full_frozen_hermetic.log", "r9__suite_full_frozen_hermetic.xml", "run_det9_pilot.log", "run_det9_holdout.log"):
    add(name if not name.endswith((".log", ".xml")) else f"suite/{name}" if "suite" in name or "hermetic" in name else f"runs/{name}", R7 / name)
for f in (R7 / "adjudication_crops").glob("*"):
    add(f"adjudication_crops/{f.name}", f)
for f in (R7 / "freeze").glob("*"):
    add(f"freeze/{f.name}", f)
for f in (R7 / "matched").glob("*"):
    if f.suffix in (".json", ".log", ".py"):
        add(f"matched/{f.name}", f)
add("matched/ledger-matched.sqlite", r"C:\t\r7\ledger\matched.sqlite")
for tag in ("m-ev0", "m-ev1", "m-ev2"):
    for f in (pathlib.Path(r"C:\t\r7") / tag / "out").glob("*"):
        add(f"runs/{tag}/{f.name}", f)
for tag in ("det9-pilot", "det9-holdout"):
    for f in (pathlib.Path(r"C:\t\r6") / tag / "out").glob("*"):
        add(f"runs/{tag}/{f.name}", f)
for f in R7.glob("*.py"):
    add(f"scripts/{f.name}", f)
add("scripts/evidence_reader_before_r7.py", W / "evidence_reader_before_r7.py")
for f in W.glob("*.py"):
    if f.stat().st_mtime > datetime.datetime(2026, 9, 29, 5, 0).timestamp():
        add(f"scripts/patches/{f.name}", f)

manifest = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "files": {}}
for dest, src in sorted(copies.items()):
    target = EV / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
    manifest["files"][dest] = {"sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "from": str(src)}

git = lambda *a: subprocess.run(["git", *a], cwd=REPO, capture_output=True).stdout
diff = git("diff", "043dee9", "1455f8b")
(EV / "candidate-r7.diff").write_bytes(diff)
names = git("diff", "--name-status", "043dee9", "1455f8b").decode().splitlines()
new = [l.split("\t", 1)[1] for l in names if l.startswith("A")]
for rel in new:
    blob = git("show", f"1455f8b:{rel}")
    target = EV / "candidate_new_files" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(blob)
changed = [l.split("\t", 1)[1] for l in names]
manifest["candidate"] = {
    "repository": str(REPO), "baseline": "c692f1e", "review06_final_reconstructed": "043dee9",
    "frozen_candidate": git("rev-parse", "c9a1a14").decode().strip(), "evaluator_amendment": git("rev-parse", "1455f8b").decode().strip(),
    "diff": "candidate-r7.diff = git diff 043dee9 1455f8b", "diff_sha256": hashlib.sha256(diff).hexdigest(),
    "changed_files": changed,
    "changed_files_sha256_at_1455f8b": {rel: hashlib.sha256(git("show", f"1455f8b:{rel}")).hexdigest() for rel in changed},
}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print(len(manifest["files"]), "files;", len(changed), "changed candidate files;", len(new), "new")
