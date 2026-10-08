"""R43-44: the v5 guard probes (review45 and declaration-r32-v4 denied, the never-created r32-v4 folder, the v5 package a root).
R43-40 (new): probes of the package audit guard (scripts/guard/sitecustomize.py, R43V-10), run under that guard.
Usage: <bound python> -B guard_probe_r43p.py <out json>    (PYTHONPATH = the guard folder; never with R43_GUARD_OWNER_RECORDS)
Every probe either must be REFUSED (PermissionError from the guard, nothing created) or ALLOWED; the refusing probes name
paths that do not exist and are never created (a refused open happens before the file system is touched). No claude
process is started (the guard refuses before any process exists), no socket connects, the AI ledger is opened mode=ro only."""
from __future__ import annotations

import json
import os
import pathlib
import socket
import sqlite3
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

W = C.WORK / "guard-probe"


def attempt(fn):
    try:
        fn()
        return "ALLOWED", None
    except PermissionError as exc:
        return "REFUSED", str(exc)[:200]
    except Exception as exc:  # noqa: BLE001
        return f"ERROR {type(exc).__name__}", str(exc)[:200]


def main(out: str) -> int:
    assert "sitecustomize" in sys.modules, "the guard is not loaded"
    W.mkdir(parents=True, exist_ok=True)
    probes = [
        ("write inside the work folder", lambda: (W / "ok.txt").write_text("ok", encoding="utf-8"), "ALLOWED"),
        ("write into the executed v3 run folder", lambda: open(C.V3_RUN_FOLDER / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("mkdir the future v5 run folder", lambda: os.mkdir(C.RUN_FOLDER), "REFUSED"),
        ("mkdir the never-created v4 run folder", lambda: os.mkdir(C.V4_RUN_FOLDER), "REFUSED"),
        ("mkdir another live-shaped run folder r32-v9", lambda: os.mkdir(C.SANDBOX_BASE / "r32-v9"), "REFUSED"),
        ("read a file in the owner records (no hash-only flag)", lambda: open(C.OWNER_RECORDS / "RUN-HASH.txt", "rb"), "REFUSED"),
        ("write into the owner records", lambda: open(C.OWNER_RECORDS / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("sqlite read-write in the v3 run folder", lambda: sqlite3.connect(str(C.V3_RUN_FOLDER / "PROBE-NEVER.sqlite")), "REFUSED"),
        ("sqlite read-write of the AI ledger", lambda: sqlite3.connect(str(C.AI_LEDGER)), "REFUSED"),
        ("sqlite mode=ro of the AI ledger", lambda: sqlite3.connect(f"file:{C.AI_LEDGER.as_posix()}?mode=ro", uri=True).close(), "ALLOWED"),
        ("write into review43", lambda: open(C.REVIEW43 / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("write into review45", lambda: open(C.REVIEW45 / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("write into declaration-r32-v4", lambda: open(C.V4 / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("write into declaration-r32-v3", lambda: open(C.V3 / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("write into frozen-r13", lambda: open("C:/t/iso/frozen-r13/PROBE-NEVER.txt", "w"), "REFUSED"),
        ("write at the sandbox base outside r45q", lambda: open(C.SANDBOX_BASE / "PROBE-NEVER.txt", "w"), "REFUSED"),
        ("open the merged .env", lambda: open(C.MERGED_ENV_FILE, "rb"), "REFUSED"),
        ("claude by name", lambda: subprocess.run(["claude", "--version"]), "REFUSED"),
        ("claude by full path", lambda: subprocess.run([C.CLI_EXE.as_posix(), "--version"]), "REFUSED"),
        ("claude through a shell", lambda: os.system("claude --version"), "REFUSED"),
        ("network name lookup", lambda: socket.getaddrinfo("example.com", 443), "REFUSED"),
        ("write (and remove) a file in the v5 package", lambda: ((C.PACKAGE / "guard-probe.tmp").write_text("x", encoding="utf-8"),
                                                                 (C.PACKAGE / "guard-probe.tmp").unlink()), "ALLOWED"),
    ]
    rows = []
    for name, fn, want in probes:
        got, why = attempt(fn)
        rows.append({"probe": name, "expected": want, "result": got, "as_expected": got == want, "reason": why})
    (W / "ok.txt").unlink(missing_ok=True)
    never = [p for p in (C.V3_RUN_FOLDER / "PROBE-NEVER.txt", C.RUN_FOLDER, C.SANDBOX_BASE / "r32-v9", C.OWNER_RECORDS / "PROBE-NEVER.txt",
                         C.V3_RUN_FOLDER / "PROBE-NEVER.sqlite", C.REVIEW43 / "PROBE-NEVER.txt", C.V3 / "PROBE-NEVER.txt",
                         C.V4_RUN_FOLDER, C.REVIEW45 / "PROBE-NEVER.txt", C.V4 / "PROBE-NEVER.txt",
                         pathlib.Path("C:/t/iso/frozen-r13/PROBE-NEVER.txt"), C.SANDBOX_BASE / "PROBE-NEVER.txt") if os.path.exists(p)]
    res = {"guard": sys.modules["sitecustomize"].__file__, "probes": rows, "all_as_expected": all(r["as_expected"] for r in rows),
           "created_by_refused_probes": never, "ok": all(r["as_expected"] for r in rows) and not never}
    C.write_json(out, res)
    print(json.dumps({"ok": res["ok"], "probes": f"{sum(r['as_expected'] for r in rows)}/{len(rows)}",
                      "unexpected": [r["probe"] for r in rows if not r["as_expected"]]}))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
