"""Review 09 source freeze: candidate commit on the isolated scratch repository, its parent chain back to the Review 08
candidate (kept as history), the SHA-256 of every changed file's committed bytes, and every tree's status."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = "C:/t/iso/ep-platform"
OUT = Path("C:/t/iso/work/r9/freeze")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "e02a8c1b9ef093534df4bd427c7f2c5e7fc1403c"


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
(OUT / "candidate-r9.diff").write_bytes(diff)
trees = {}
for name, path in (("frozen-r9", "C:/t/iso/frozen-r9"), ("frozen-r8 (reviewed Review 08 tree)", "C:/t/iso/frozen-r8"),
                   ("scratch repository", REPO)):
    trees[name] = {"head": git("rev-parse", "HEAD", repo=path), "clean": git("status", "--porcelain", repo=path) == "",
                   "has_env": Path(path, "backend/.env").exists()}
owner = "C:/Users/moham/Desktop/dev/dev/ep-platform"
manifest = {
    "candidate_commit": head, "base": BASE, "commits_since_base": chain,
    "superseded_freeze": {"ec4f0fc": "first freeze; superseded by the final commit before any result was reported (unscored-page judgements "
                                      "dropped target / association -- no score affected)"},
    "branch": "iso-baseline (isolated scratch repository C:/t/iso/ep-platform; core.autocrlf false)",
    "history_kept": {"e02a8c1": "Review 08 candidate (frozen-r8, the tree Review 09 inspected, unchanged)",
                     "1455f8b": "Review 07 evaluator amendment", "c9a1a14": "Review 07 frozen application",
                     "review08 package": "docs/milestones/M2/real-project-pilot/review08 (unchanged)"},
    "trees": trees,
    "versions": {"reader": "evidence-reader-2026-09-29.4", "policy": "evidence-policy-2026-09-29.4", "evaluator": "m2-pilot-eval-2026-09-29.8",
                 "ledger": "ai-ledger-2026-09-29.2 (unchanged; docstring wording only)", "parser": "parse-2026-09-29.9 (unchanged)"},
    "changed_files": files,
    "diff": {"file": "candidate-r9.diff", "against": BASE, "sha256": hashlib.sha256(diff).hexdigest()},
    "owner_checkout_head": git("rev-parse", "HEAD", repo=owner),
    "temporary_environment": {"tests": "tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r9 has no .env",
                              "temp": "TEMP=TMP=C:/t/iso/tmp; --basetemp under C:/t/iso/tmp", "models": "none called; scripted providers only"},
}
(OUT / "FREEZE-R9.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest[k] for k in ("candidate_commit", "commits_since_base", "trees", "owner_checkout_head")}, indent=1))
for p, v in files.items():
    print(v["sha256"], v["kind"].ljust(16), v["bytes"], p)
print("diff", manifest["diff"]["sha256"])
