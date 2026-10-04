"""ORCH-06C (R36HARNESS-IMPL): a pytest plugin (loaded with -p r36_write_guard) that installs a Python audit hook in the
pytest process and REFUSES every file write, directory creation, rename, removal or SQLite open outside the allowed roots
(R36_GUARD_ALLOW, ';'-separated absolute folders). Read-only SQLite URIs (mode=ro) and ':memory:' are allowed. Network
connections are refused. At the end of the session it writes R36_GUARD_REPORT (a JSON file inside an allowed root) with
the refused operations and the count of allowed write operations per root. It changes nothing in the code under test;
child processes are not covered (they are checked by before/after snapshots)."""
import collections
import json
import os
import sys

_ALLOW = [os.path.normcase(os.path.abspath(p)) for p in os.environ.get("R36_GUARD_ALLOW", "").split(";") if p.strip()]
_REPORT = os.environ.get("R36_GUARD_REPORT")
_STATE = {"refused": [], "allowed": collections.Counter(), "network": []}
_WRITE_EVENTS = {"os.mkdir": 0, "os.rename": (0, 1), "os.remove": 0, "os.rmdir": 0, "shutil.rmtree": 0, "os.truncate": 0,
                 "os.chmod": 0, "os.utime": 0, "os.symlink": (0, 1), "os.link": (0, 1), "shutil.copyfile": (1,), "shutil.move": (0, 1)}


def _norm(p):
    try:
        if isinstance(p, int) or p is None:
            return None
        if isinstance(p, bytes):
            p = p.decode("utf-8", "replace")
        p = os.fspath(p)
        if p.startswith((r"\\?" + "\\", "//?/")):     # an extended-length path (\\?\C:\...): the same file
            p = p[4:]
        return os.path.normcase(os.path.abspath(p))
    except Exception:  # noqa: BLE001
        return None


def _root(path):
    for a in _ALLOW:
        if path == a or path.startswith(a.rstrip("\\/") + os.sep):
            return a
    return None


_DEVNULL = {os.path.normcase(os.path.abspath(os.devnull)), os.path.normcase(os.devnull)}


def _check(event, path):
    if path is None:
        return
    if path in _DEVNULL:                      # the null device (pytest's logging opens it); nothing is stored
        _STATE["allowed"]["<null device>"] += 1
        return
    r = _root(path)
    if r is None:
        _STATE["refused"].append({"event": event, "path": path})
        raise PermissionError(f"r36 write guard: {event} outside the allowed roots refused: {path}")
    _STATE["allowed"][r] += 1


def _is_write(mode, flags):
    if isinstance(mode, str):
        return any(c in mode for c in "wax+")
    if isinstance(flags, int):
        return bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC))
    return False


def _hook(event, args):
    if event == "open":
        if args and _is_write(args[1] if len(args) > 1 else None, args[2] if len(args) > 2 else None):
            _check(event, _norm(args[0]))
    elif event in _WRITE_EVENTS:
        idx = _WRITE_EVENTS[event]
        for i in ((idx,) if isinstance(idx, int) else idx):
            if len(args) > i:
                _check(event, _norm(args[i]))
    elif event == "sqlite3.connect":
        db = args[0] if args else None
        s = os.fspath(db) if db is not None and not isinstance(db, int) else ""
        if isinstance(s, bytes):
            s = s.decode("utf-8", "replace")
        if s in ("", ":memory:") or "mode=ro" in s or "mode=memory" in s:
            return
        _check(event, _norm(s[5:].split("?")[0] if s.startswith("file:") else s))
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname"):
        _STATE["network"].append(event)
        raise PermissionError(f"r36 write guard: {event} refused (no network)")


sys.addaudithook(_hook)


def pytest_sessionfinish(session, exitstatus):
    if not _REPORT:
        return
    out = {"allowed_roots": _ALLOW, "refused": _STATE["refused"], "refused_count": len(_STATE["refused"]),
           "network_refused": _STATE["network"], "allowed_write_operations_by_root": dict(_STATE["allowed"]),
           "exitstatus": int(exitstatus)}
    with open(_REPORT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
