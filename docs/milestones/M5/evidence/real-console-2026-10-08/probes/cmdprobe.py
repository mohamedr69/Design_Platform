"""Which commands the DWG TrueView 2026 Core Console knows.

For each command a one-command script is run on a scratch copy of the
GC-01 copy (never the source): the command line, then QUIT and Y. The log
says "Unknown command" when the console has no such command; any other
echo (a prompt) means it is known. Each run: own folder, 60 s limit.
Writes cmdprobe.json and cmdprobe-<cmd>.log."""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

EXE = r"C:\Program Files\Autodesk\DWG TrueView 2026 - English\accoreconsole.exe"
PROFILE = r"C:\t\tmp\m5cad\profile"
HERE = Path(__file__).resolve().parent
SRC = Path(r"C:\t\tmp\m5cad\src\GC-01-copy.dwg")

COMMANDS = sys.argv[1:] or [
    "SAVEAS", "QSAVE", "SAVE", "DXFOUT", "-INSERT", "INSERT", "ERASE", "LIST", "DWGCONVERT", "-DWGCONVERT",
    "AUDIT", "-PLOT", "PLOT", "-EXPORT", "EXPORT", "-PURGE", "PURGE", "SETVAR", "TILEMODE", "MODEL",
    "-LAYER", "BLOCK", "-BLOCK", "WBLOCK", "-WBLOCK", "OPEN", "DXFIN", "SCRIPT", "APPLOAD", "ARX", "NETLOAD",
    "ID", "COUNT", "-ATTEXT", "SELECT", "UNDO", "U", "EXPORTPDF", "-EXPORTPDF", "RECOVER", "SAVEALL",
    "CLOSE", "QUIT", "LINE", "MOVE", "COPY", "EXPLODE", "REGEN", "ZOOM", "-LAYOUT", "XREF", "-XREF",
    "SYSVARMONITOR", "ETRANSMIT", "-ETRANSMIT", "DWGPROPS", "PUBLISH", "-PUBLISH", "TEXT", "-TEXT",
    "SECURITYOPTIONS", "TRUSTEDPATHS", "VLISP", "(", "JSLOAD", "MARKUP", "DWFOUT", "BATTMAN", "ATTSYNC",
]


def decode(raw: bytes) -> str:
    if raw[:200].count(b"\x00") > 20:
        return raw.decode("utf-16-le", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


def main() -> None:
    work = HERE / "cmdprobe"
    work.mkdir(exist_ok=True)
    results = {}
    for cmd in COMMANDS:
        safe = cmd.replace("-", "dash_").replace("(", "paren")
        folder = work / safe
        if folder.exists() and False:
            time.sleep(1); shutil.rmtree(folder, ignore_errors=True)
        folder.mkdir(exist_ok=True)
        dwg = folder / "scratch.dwg"
        shutil.copyfile(SRC, dwg)
        scr = folder / "probe.scr"
        scr.write_bytes("\n".join([cmd, "_.QUIT", "_Y", ""]).encode("utf-8"))
        t0 = time.monotonic()
        try:
            p = subprocess.run([EXE, "/i", str(dwg), "/s", str(scr), "/l", "en-US", "/isolate", "m5cad", PROFILE],
                               capture_output=True, timeout=60, cwd=str(folder),
                               creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            rc, out = p.returncode, decode(p.stdout) + decode(p.stderr)
        except subprocess.TimeoutExpired as exc:
            rc, out = "timeout", decode(exc.stdout or b"")   # subprocess.run killed its own child
        lines = [l for l in out.splitlines() if l.strip() and "CoreHeartBeat" not in l]
        tail = lines[lines.index(next((l for l in lines if l.startswith("1 of the monitored")), lines[0])) + 1:] \
            if lines else []
        unknown = any("Unknown command" in l or "is not available" in l for l in tail[:3])
        (HERE / f"cmdprobe-{safe}.log").write_text(out, encoding="utf-8")
        results[cmd] = {"known": not unknown, "returncode": rc, "seconds": round(time.monotonic() - t0, 1),
                        "after_open": tail[:6]}
        print(cmd, "KNOWN" if not unknown else "unknown", rc, tail[:3], flush=True)
        time.sleep(1); shutil.rmtree(folder, ignore_errors=True)
    (HERE / "cmdprobe.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
