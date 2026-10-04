"""Review 10 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 09 candidate,
kept as history), the SHA-256 of every changed file's committed bytes, and every tree's status."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = "C:/t/iso/ep-platform"
OUT = Path("C:/t/iso/work/r10/freeze")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "689d95e53cc369c2397600daf2a46a3de93d5214"


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
(OUT / "candidate-r10.diff").write_bytes(diff)
trees = {}
for name, path in (("frozen-r10", "C:/t/iso/frozen-r10"), ("frozen-r9 (reviewed Review 09 tree)", "C:/t/iso/frozen-r9"),
                   ("scratch repository", REPO)):
    trees[name] = {"head": git("rev-parse", "HEAD", repo=path), "clean": git("status", "--porcelain", repo=path) == "",
                   "has_env": Path(path, "backend/.env").exists()}
owner = "C:/Users/moham/Desktop/dev/dev/ep-platform"
manifest = {
    "candidate_commit": head, "base": BASE, "commits_since_base": chain,
    "branch": "iso-baseline (isolated scratch repository C:/t/iso/ep-platform; core.autocrlf false)",
    "history_kept": {"689d95e": "Review 09 candidate (frozen-r9, the tree Review 10 inspected, unchanged)",
                     "e02a8c1": "Review 08 candidate", "review09 package": "docs/milestones/M2/real-project-pilot/review09 (unchanged)"},
    "trees": trees,
    "versions": {"reader": "evidence-reader-2026-09-29.5 (selection / association only)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",
                 "evaluator": "m2-pilot-eval-2026-09-29.9", "ledger": "ai-ledger-2026-09-29.2 (unchanged)", "parser": "parse-2026-09-29.9 (unchanged)"},
    "changed_files": files,
    "diff": {"file": "candidate-r9.diff", "against": BASE, "sha256": hashlib.sha256(diff).hexdigest()},
    "owner_checkout_head": git("rev-parse", "HEAD", repo=owner),
    "temporary_environment": {"tests": "tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r10 has no .env",
                              "temp": "TEMP=TMP=C:/t/iso/tmp; --basetemp under C:/t/iso/tmp", "models": "none called; scripted providers only"},
}
(OUT / "FREEZE-R10.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest[k] for k in ("candidate_commit", "commits_since_base", "trees", "owner_checkout_head")}, indent=1))
for p, v in files.items():
    print(v["sha256"], v["kind"].ljust(16), v["bytes"], p)
print("diff", manifest["diff"]["sha256"])
