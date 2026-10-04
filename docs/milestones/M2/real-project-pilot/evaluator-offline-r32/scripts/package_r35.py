"""ORCH-06: write evidence/EVIDENCE-MANIFEST.json LAST: every package file except the manifest itself, with sha256 and bytes.
Usage: package_r35.py        (writes only evidence/EVIDENCE-MANIFEST.json)"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import common_r35 as C  # noqa: E402


def main():
    target = C.PACKAGE / "evidence/EVIDENCE-MANIFEST.json"
    files = {}
    for p in sorted(C.PACKAGE.rglob("*")):
        if p.is_file() and p != target:
            assert "__pycache__" not in p.parts, p
            files[p.relative_to(C.PACKAGE).as_posix()] = {"sha256": C.sha256_file(p), "bytes": p.stat().st_size}
    check = json.loads((C.PACKAGE / "evidence/PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    assert check["all_ok"], "PACKAGE-CHECK is not ok"
    manifest = {"kind": "EVIDENCE-MANIFEST (ORCH-06 package evaluator-offline-r32)",
                "written_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "package": str(C.PACKAGE).replace("\\", "/"), "files": files, "count": len(files),
                "not_listed": ["evidence/EVIDENCE-MANIFEST.json (this file)"],
                "statement": C.SYNTHETIC_STATEMENT, "reference_set_statement": C.REFERENCE_SET_STATEMENT}
    sha = C.write_json(manifest, target)
    print(json.dumps({"manifest_sha256": sha, "files": len(files)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
