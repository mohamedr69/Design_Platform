"""ORCH-044 evidence (U2M8V-02): recompute a MANIFEST.json and say, file by
file, whether it holds -- from the committed blobs of a commit, and from the
files of this checkout (as they are, and with CRLF taken back to LF, which is
what a Windows autocrlf checkout of a text file adds).

Run from the root of any checkout (fresh clone, worktree; Windows or not):
    python -B docs/milestones/M8/evidence/exit-fixes/scripts/check_manifest.py [REV] [MANIFEST] [OUT.json]
REV defaults to HEAD, MANIFEST to the exit-fixes MANIFEST.json. Also accepts
the ORCH-036 wall-index MANIFEST (sha256 strings instead of {blob, sha256}).
Exit status 0 when every recorded hash equals the committed blob's.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
DEFAULT = "docs/milestones/M8/evidence/exit-fixes/MANIFEST.json"


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=True).stdout


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main(rev: str = "HEAD", manifest_path: str = DEFAULT, out: str | None = None) -> int:
    manifest = json.loads(git("show", f"{rev}:{manifest_path}").decode("utf-8"))
    rows = {}
    for section in ("changed_source", "reports", "report", "evidence"):
        for path, rec in (manifest.get(section) or {}).items():
            want = rec["sha256"] if isinstance(rec, dict) else rec
            want_blob = rec.get("blob") if isinstance(rec, dict) else None
            try:
                blob_bytes = git("cat-file", "blob", f"{rev}:{path}")
                blob_id = git("rev-parse", f"{rev}:{path}").decode().strip()
            except subprocess.CalledProcessError:
                blob_bytes, blob_id = None, None
            file = ROOT / path
            disk = file.read_bytes() if file.is_file() else None
            rows[path] = {
                "committed_blob": None if blob_bytes is None else sha(blob_bytes) == want,
                "blob_id": None if want_blob is None else blob_id == want_blob,
                "checkout_as_is": None if disk is None else sha(disk) == want,
                "checkout_lf": None if disk is None else sha(disk.replace(b"\r\n", b"\n")) == want,
                "blob_as_crlf": None if blob_bytes is None else
                sha(blob_bytes.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")) == want,
            }
    summary = {"rev": git("rev-parse", rev).decode().strip(), "manifest": manifest_path, "files": len(rows)}
    for key in ("committed_blob", "blob_id", "checkout_as_is", "checkout_lf", "blob_as_crlf"):
        summary[key] = sum(1 for r in rows.values() if r[key])
    summary["holds_on_committed_blobs"] = summary["committed_blob"] == len(rows)
    result = {"summary": summary, "files": rows}
    if out:
        Path(out).write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0 if summary["holds_on_committed_blobs"] else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
