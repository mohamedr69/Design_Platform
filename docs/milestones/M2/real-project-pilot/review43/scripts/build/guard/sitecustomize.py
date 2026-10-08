"""ORCH-10 (R42PORT-IMPL) audit guard, loaded by every Python process of this task through PYTHONPATH (the lanes, the
ingestion and scoring children inherit it). It REFUSES, by raising PermissionError, and logs to <work>/out/guard/:
  * any process whose program or arguments name a `claude` executable (by name, full path, shell or os.system);
  * every socket connect / name lookup (no network);
  * a write, mkdir, rename, remove, rmdir, chmod or utime outside the allowed roots;
  * a read-write sqlite3 connection outside the allowed roots (mode=ro URIs are allowed anywhere);
  * any open of the merged installation's .env.
Allowed write roots: the work folder, the dry sandbox base, the two new packages, the session scratchpad, the process'
own TEMP when it lies under one of those, and os.devnull. R42_GUARD_ALLOW_EXTRA may add ONE extra file (used only by the
response-ledger append, which writes that one file). Nothing else is changed in the process."""
import os
import sys

_ROOTS = [
    "c:/t/iso/work/r2x/r42",
    "c:/t/r2x/r42-sandbox",
    "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot/review42",
    "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot/declaration-r32-v3",
    "c:/users/moham/appdata/local/temp/claude/g--dev--2--dev-ep-platform-merged/a76bec7b-2218-48de-b634-4b877ef21099/scratchpad",
]
_EXTRA = (os.environ.get("R42_GUARD_ALLOW_EXTRA") or "").replace("\\", "/").lower()
_ENV_FILE = "g:/dev (2)/dev/ep-platform-merged/ep-platform/backend/.env"
_LOG = "C:/t/iso/work/r2x/r42/out/guard"


def _norm(p):
    try:
        p = os.fsdecode(p)
    except TypeError:
        return ""
    p = p.replace("\\", "/")
    if p.startswith("//?/"):
        p = p[4:]
    try:
        p = os.path.abspath(p).replace("\\", "/")
    except (TypeError, ValueError):
        pass
    try:
        lp = os.path.realpath(p).replace("\\", "/")      # resolves 8.3 short names where possible
    except (OSError, ValueError):
        lp = p
    return lp.lower()


def _allowed(p):
    n = _norm(p)
    if n in ("nul", "//./nul") or n.endswith("/nul"):
        return True
    if _EXTRA and n == _norm(_EXTRA):
        return True
    return any(n == r or n.startswith(r + "/") for r in _ROOTS)


def _record(kind, detail):
    try:
        os.makedirs(_LOG, exist_ok=True)
        with open(os.path.join(_LOG, f"refusals-{os.getpid()}.log"), "a", encoding="utf-8") as fh:
            fh.write(f"{kind}\t{detail}\n")
    except Exception:  # noqa: BLE001
        pass


def _refuse(kind, detail):
    _record(kind, detail)
    raise PermissionError(f"R42 guard refused {kind}: {detail}")


def _names_claude(args):
    items = args if isinstance(args, (list, tuple)) else [args]
    for a in items:
        if a is None:
            continue
        try:
            s = os.fsdecode(a) if not isinstance(a, str) else a
        except TypeError:
            continue
        low = s.replace("\\", "/").lower()
        for tok in low.replace('"', " ").split():
            base = tok.rsplit("/", 1)[-1]
            if base in ("claude", "claude.exe", "claude.cmd", "claude.bat", "claude.ps1"):
                return True
    return False


_WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC


def _hook(event, args):
    if event == "open":
        path, mode, flags = (list(args) + [None, None, None])[:3]
        if path is None or isinstance(path, int):
            return
        if _norm(path) == _ENV_FILE:
            _refuse("open .env", path)
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & _WRITE_FLAGS)
        if writing and not _allowed(path):
            _refuse("write", f"{path} mode={mode} flags={flags}")
    elif event in ("os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime", "os.truncate", "shutil.rmtree", "os.symlink", "os.link"):
        p = args[0] if args else None
        if p is not None and not isinstance(p, int) and not _allowed(p):
            _refuse(event, p)
    elif event in ("os.rename", "shutil.move", "shutil.copyfile", "shutil.copytree"):
        dst = args[1] if len(args) > 1 else None
        if dst is not None and not _allowed(dst):
            _refuse(event, f"{args[0]} -> {dst}")
        if event in ("os.rename", "shutil.move") and args and not _allowed(args[0]):
            _refuse(event, f"source {args[0]}")
    elif event == "sqlite3.connect":
        db = args[0] if args else None
        s = os.fsdecode(db) if isinstance(db, (bytes, os.PathLike)) else str(db or "")
        if s in ("", ":memory:"):
            return
        if s.startswith("file:"):
            if "mode=ro" in s:
                return
            s = s[5:].split("?", 1)[0]
        if not _allowed(s):
            _refuse("sqlite3 read-write", s)
    elif event in ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile"):
        payload = list(args)
        if _names_claude(payload[0] if event != "os.system" else payload[0]) or (len(payload) > 1 and _names_claude(payload[1])):
            _refuse("claude process", repr(payload[:2])[:400])
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto", "socket.bind"):
        _refuse("network", repr(args)[:200])


sys.addaudithook(_hook)
