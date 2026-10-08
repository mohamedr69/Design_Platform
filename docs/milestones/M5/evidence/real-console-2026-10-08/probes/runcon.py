"""Probe runner: run the DWG TrueView Core Console on a script, capture and
decode its output (the same decoding as app.ifc.dxf.convert._decode), and
record the command line, return code, seconds and log.

usage: python runcon.py <name> <script> [<input dwg>] [--noisolate]
Writes <name>.log and <name>.run.json beside the script."""
import json
import subprocess
import sys
import time
from pathlib import Path

EXE = r"C:\Program Files\Autodesk\DWG TrueView 2026 - English\accoreconsole.exe"
PROFILE = r"C:\t\tmp\m5cad\profile"


def decode(raw: bytes) -> str:
    if raw[:200].count(b"\x00") > 20:
        return raw.decode("utf-16-le", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    name, script = args[0], Path(args[1]).resolve()
    dwg = Path(args[2]).resolve() if len(args) > 2 else None
    cmd = [EXE]
    if dwg:
        cmd += ["/i", str(dwg)]
    cmd += ["/s", str(script), "/l", "en-US"]
    if "--noisolate" not in flags:
        cmd += ["/isolate", "m5cad", PROFILE]
    import os
    env = dict(os.environ, TEMP="C:/t/tmp/m5cad/tmp".replace("/", os.sep), TMP="C:/t/tmp/m5cad/tmp".replace("/", os.sep))
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=300, cwd=str(script.parent), env=env,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        rc, out = p.returncode, decode(p.stdout) + decode(p.stderr)
    except subprocess.TimeoutExpired as exc:
        rc, out = "timeout", decode(exc.stdout or b"")
    secs = round(time.monotonic() - t0, 2)
    log = script.parent / f"{name}.log"
    log.write_text(out, encoding="utf-8")
    info = {"name": name, "cmd": cmd, "returncode": rc, "seconds": secs, "log": log.name}
    (script.parent / f"{name}.run.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(json.dumps(info))
    print("".join(l + "\n" for l in out.splitlines() if l.strip() and "CoreHeartBeat" not in l))


if __name__ == "__main__":
    main()
