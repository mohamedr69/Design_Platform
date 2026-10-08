"""ORCH-10 (R42PORT-IMPL): remove the STAGED PDF COPIES of finished dry invocations under C:/t/r2x/r42-sandbox (the
<run folder>/inv-<n>/B/s folders: byte copies of the frozen staging made by sandbox_ingest; a resume never reads them) and
keep every run record. Never touches C:/t/r2x/r42-sandbox/r32-v3 (the live run folder, which must not exist) or anything
outside the sandbox base. Appends what it removed to <work>/out/TRIMMED.jsonl. Usage: trim_sandbox_r42.py"""
import json
import os
import pathlib
import shutil
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402


def main() -> int:
    base = C.SANDBOX_BASE
    removed, total = [], 0
    for s in sorted(list(base.rglob("inv-*/B/s")) + list(base.rglob("ingest-*/s"))):
        if not s.is_dir() or C.RUN_FOLDER in s.parents:
            continue
        n = 0
        for dp, _ds, fs in os.walk(C.long_path(s)):
            for f in fs:
                n += os.path.getsize(os.path.join(dp, f))
        shutil.rmtree(C.long_path(s))
        removed.append({"path": s.as_posix(), "bytes": n})
        total += n
    rec = {"at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "removed": len(removed), "bytes": total, "free_bytes_after": C.free_bytes("C:/")}
    with open(C.WORK / "out" / "TRIMMED.jsonl", "a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(rec | {"paths": [r["path"] for r in removed]}) + "\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
