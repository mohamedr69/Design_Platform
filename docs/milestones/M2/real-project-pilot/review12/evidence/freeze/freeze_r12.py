"""Review 12 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 11 candidate,
kept as history), the SHA-256 of every changed file's committed bytes, and every tree's status."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = "C:/t/iso/ep-platform"
OUT = Path("C:/t/iso/work/r12/freeze")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "a9773642c099b0924099bd8a86a72d4507137429"


def git(*args, repo=REPO, binary=False):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)
    return out.stdout if binary else out.stdout.decode("utf-8").strip()


head = git("rev-parse", "HEAD")
chain = git("log", "--format=%H %s", f"{BASE}..{head}").splitlines()
changed = git("diff", "--name-only", BASE, head).splitlines()
files = {}
for path in changed:
    blob = git("show", f"{head}:{path}", binary=True)
    files[path] = {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob),
                   "kind": "test" if "/tests/" in path else "evaluator script" if "/scripts/" in path else "application",
                   "crlf": blob.count(b"\r\n") > 0}
diff = git("diff", "--binary", BASE, head, binary=True)
(OUT / "candidate-r12.diff").write_bytes(diff)
trees = {}
for name, path in (("frozen-r12", "C:/t/iso/frozen-r12"), ("frozen-r11 (reviewed Review 11 tree)", "C:/t/iso/frozen-r11"),
                   ("scratch repository", REPO)):
    trees[name] = {"head": git("rev-parse", "HEAD", repo=path), "clean": git("status", "--porcelain", repo=path) == "",
                   "has_env": Path(path, "backend/.env").exists()}
owner = "C:/Users/moham/Desktop/dev/dev/ep-platform"
manifest = {
    "candidate_commit": head, "base": BASE, "commits_since_base": chain,
    "branch": "iso-baseline (isolated scratch repository C:/t/iso/ep-platform; core.autocrlf false)",
    "history_kept": {"a977364": "Review 11 candidate (frozen-r11, the tree Review 12 inspected, unchanged)",
                     "a34d3f8": "Review 10 candidate", "review11 package": "docs/milestones/M2/real-project-pilot/review11 (unchanged)"},
    "trees": trees,
    "versions": {"reader": "evidence-reader-2026-09-29.7 (legacy anchor reconstruction)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",
                 "evaluator": "m2-pilot-eval-2026-09-29.9 (unchanged)", "ledger": "ai-ledger-2026-09-29.2 (unchanged)", "parser": "parse-2026-09-29.9 (unchanged)"},
    "changed_files": files,
    "diff": {"file": "candidate-r9.diff", "against": BASE, "sha256": hashlib.sha256(diff).hexdigest()},
    "owner_checkout_head": git("rev-parse", "HEAD", repo=owner),
    "temporary_environment": {"tests": "tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r12 has no .env",
                              "temp": "TEMP=TMP=C:/t/iso/tmp; --basetemp under C:/t/iso/tmp", "models": "none called; scripted providers only"},
}
(OUT / "FREEZE-R12.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest[k] for k in ("candidate_commit", "commits_since_base", "trees", "owner_checkout_head")}, indent=1))
for p, v in files.items():
    print(v["sha256"], v["kind"].ljust(16), v["bytes"], p)
print("diff", manifest["diff"]["sha256"])
