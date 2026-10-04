"""Review 08 source freeze: the candidate commit on the isolated scratch repository, its parent (the Review 07 freeze
and evaluator amendment, kept as history), and the SHA-256 of every changed file's committed bytes."""
import hashlib
import json
import subprocess
from pathlib import Path

REPO = "C:/t/iso/ep-platform"
OUT = Path("C:/t/iso/work/r8/freeze")
OUT.mkdir(parents=True, exist_ok=True)


def git(*args, repo=REPO, binary=False):
    out = subprocess.run(["git", "-C", repo, *args], capture_output=True, check=True)
    return out.stdout if binary else out.stdout.decode("utf-8").strip()


head = git("rev-parse", "HEAD")
parent = git("rev-parse", "HEAD~1")
changed = git("diff", "--name-only", "1455f8b", head).splitlines()
files = {}
for path in changed:
    blob = git("show", f"{head}:{path}", binary=True)
    files[path] = {"sha256": hashlib.sha256(blob).hexdigest(), "bytes": len(blob),
                   "kind": "test" if "/tests/" in path else "evaluator script" if "/scripts/" in path else "application"}
diff = git("diff", "--binary", "1455f8b", head, binary=True)
(OUT / "candidate-r8.diff").write_bytes(diff)

fx = {}
for fixture, source in (("backend/tests/fixtures/evidence_reader_r7.py", "backend/app/ai/evidence_reader.py"),
                        ("backend/tests/fixtures/ledger_r7.py", "backend/app/ai/ledger.py")):
    a = hashlib.sha256(git("show", f"{head}:{fixture}", binary=True)).hexdigest()
    b = hashlib.sha256(git("show", f"1455f8b:{source}", binary=True)).hexdigest()
    fx[fixture] = {"pinned_from": f"1455f8b:{source}", "identical": a == b, "sha256": a}

frozen = git("rev-parse", "HEAD", repo="C:/t/iso/frozen-r8")
r7 = git("rev-parse", "HEAD", repo="C:/t/iso/frozen-r7")
owner = git("rev-parse", "HEAD", repo="C:/Users/moham/Desktop/dev/dev/ep-platform")
manifest = {
    "candidate_commit": head, "parent": parent, "branch": "iso-baseline (isolated scratch repository C:/t/iso/ep-platform; core.autocrlf false)",
    "history_kept": {"c9a1a14": "Review 07 frozen application candidate", "1455f8b": "Review 07 evaluator .6 amendment",
                     "frozen-r7 worktree HEAD": r7, "review07 package": "docs/milestones/M2/real-project-pilot/review07 (unchanged)"},
    "frozen_worktree": {"path": "C:/t/iso/frozen-r8", "head": frozen, "has_env": Path("C:/t/iso/frozen-r8/backend/.env").exists(),
                        "clean": git("status", "--porcelain", repo="C:/t/iso/frozen-r8") == ""},
    "versions": {"reader": "evidence-reader-2026-09-29.3", "policy": "evidence-policy-2026-09-29.3", "ledger": "ai-ledger-2026-09-29.2",
                 "evaluator": "m2-pilot-eval-2026-09-29.7", "parser": "parse-2026-09-29.9 (unchanged)"},
    "changed_files": files, "pinned_prior_fixtures": fx,
    "diff": {"file": "candidate-r8.diff", "against": "1455f8b", "sha256": hashlib.sha256(diff).hexdigest()},
    "unchanged_by_this_candidate": ["parser / profiles / register / request cache / submittal and transmittal code",
                                    "the owner's checkout", "live services, settings and data", "original sources", "sealed projects"],
    "owner_checkout_head": owner,
}
(OUT / "FREEZE-R8.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: manifest[k] for k in ("candidate_commit", "parent", "frozen_worktree", "owner_checkout_head")}, indent=1))
for p, v in files.items():
    print(v["sha256"][:16], v["kind"].ljust(16), p)
print(fx)
