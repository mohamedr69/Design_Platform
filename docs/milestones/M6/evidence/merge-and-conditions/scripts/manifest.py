"""ORCH-049: MANIFEST.json for this evidence folder and the changed code --
sha256 and size of each evidence file (LF-normalised bytes for text, as
committed) and the git blob of each file the merge and Part B changed."""
import hashlib
import json
import subprocess
from pathlib import Path

EVIDENCE = Path(__file__).resolve().parents[1]
WT = EVIDENCE.parents[4]
TEXT = {".py", ".json", ".log", ".xml", ".txt", ".md"}


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(WT), *args], capture_output=True, text=True, check=True).stdout.strip()


def digest(path: Path) -> dict:
    data = path.read_bytes()
    if path.suffix in TEXT:
        data = data.replace(b"\r\n", b"\n")
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


files = {str(p.relative_to(EVIDENCE)).replace("\\", "/"): digest(p) for p in sorted(EVIDENCE.rglob("*"))
         if p.is_file() and p.name != "MANIFEST.json"}
changed = {}
for rng in ("b3c4949..HEAD",):
    for name in git("diff", "--name-only", rng, "--", "backend", "docs/DOCUMENT_CLASSIFICATION_V2.md",
                    "docs/DOCUMENT_CLASSIFICATION_AI.md").splitlines():
        changed[name] = git("rev-parse", f"HEAD:{name}")
manifest = {"task": "ORCH-049", "branch": "task/m6-merge", "base": git("rev-parse", "b3c4949"),
            "head_at_manifest": git("rev-parse", "HEAD"), "note": "text files hashed with LF line endings (as committed)",
            "evidence": files, "changed_code_blobs_vs_base": changed}
(EVIDENCE / "MANIFEST.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8", newline="\n")
print(len(files), "evidence files;", len(changed), "changed files")
