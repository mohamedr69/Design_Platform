"""Copy Review 06 evidence into the docs package and write its manifest (SHA-256 of every file, plus the isolated
candidate's source identities). Docs only: nothing in the owner's code tree is touched."""
import datetime, hashlib, json, pathlib, shutil, subprocess

DOCS = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot\review06")
EV = DOCS / "evidence"
W = pathlib.Path(r"C:\t\iso\work")
ISO = pathlib.Path("C:/t/iso/ep-platform")   # the scratch repository root (backend/ is inside it)
R6 = pathlib.Path(r"C:\t\r6")
copies = {
    "FREEZE-evaluators.json": W / "FREEZE-evaluators.json",
    "reviewer_probes_eval4.txt": W / "reviewer_probes_eval4.txt",
    "realmodel/EXPERIMENT-DECLARATION.json": W / "realmodel/EXPERIMENT-DECLARATION.json",
    "realmodel/SMOKE.txt": W / "realmodel/SMOKE.txt",
    "realmodel/budget_ev0.json": W / "realmodel/budget_ev0.json",
    "realmodel/budget_ev.json": W / "realmodel/budget_ev.json",
}
for f in (W / "eval4b").glob("*.json"):
    copies[f"eval4/{f.name}"] = f
for f in (W / "boq3").glob("*.json"):
    copies[f"boq3/{f.name}"] = f
for f in (W / "boqexp").glob("*"):
    if f.suffix in (".json", ".log"):
        copies[f"boqexp/{f.name}"] = f
for f in (W / "eval_r6").glob("*.json"):
    copies[f"eval_r6/{f.name}"] = f
for f in (W / "realmodel").glob("*.json"):
    copies.setdefault(f"realmodel/{f.name}", f)
for f in (W / "realmodel").glob("*.log"):
    copies[f"realmodel/{f.name}"] = f
for f in (W / "realmodel").glob("*.md"):
    copies[f"realmodel/{f.name}"] = f
for f in W.glob("r8__*"):
    copies[f"suite/{f.name}"] = f
for name in ("full_baseline.log", "full_candidate.log", "reader_tests_1.log"):
    if (W / name).exists():
        copies[f"suite/{name}"] = W / name
for tag in ("det-holdout", "det-pilot", "ai-ev0", "ai-ev1", "ai-ev2", "boq-app-off", "boq-app-ev0", "boq-ev1", "boq-ev2"):
    for f in (R6 / tag / "out").glob("*"):
        copies[f"runs/{tag}/{f.name}"] = f
for f in W.glob("*.py"):
    copies[f"scripts/{f.name}"] = f
for f in (W / "realmodel").glob("*.py"):
    copies[f"scripts/realmodel_{f.name}"] = f
manifest = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "files": {}}
for dest, src in sorted(copies.items()):
    if not src.exists():
        continue
    target = EV / dest
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, target)
    manifest["files"][dest] = {"sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "bytes": target.stat().st_size, "from": str(src)}
status = subprocess.run(["git", "status", "--porcelain"], cwd=ISO, capture_output=True, text=True).stdout.splitlines()
changed = sorted(l[3:].strip().strip('"') for l in status if l.strip())
manifest["candidate"] = {
    "isolated_copy": str(ISO),
    "baseline_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ISO, capture_output=True, text=True).stdout.strip(),
    "changed_files_sha256": {f: hashlib.sha256((ISO / f).read_bytes()).hexdigest() for f in changed if (ISO / f).is_file()},
}
diff = subprocess.run(["git", "diff", "HEAD"], cwd=ISO, capture_output=True).stdout
(EV / "candidate.diff").write_bytes(diff)
manifest["candidate"]["tracked_diff_sha256"] = hashlib.sha256(diff).hexdigest()
for f in changed:
    if f.startswith("??") or not (ISO / f).is_file():
        continue
for f in changed:
    p = ISO / f
    if p.is_file() and subprocess.run(["git", "ls-files", "--error-unmatch", f], cwd=ISO, capture_output=True).returncode != 0:
        target = EV / "candidate_new_files" / f
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print(len(manifest["files"]), "files;", len(manifest["candidate"]["changed_files_sha256"]), "candidate files")
