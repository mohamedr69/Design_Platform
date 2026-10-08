"""R43-40 (declaration-r32-v4) audit guard for tests, dry runs, demonstrations and package builds, loaded by every Python
process through PYTHONPATH (the lanes, the ingestion and scoring children inherit it). It answers Verification 43 R43V-10:
the v3 (R42) guard allowed writes to the whole sandbox base (including the live run folder r32-v3 and the owner records),
the R42 work folder, review42 and declaration-r32-v3. This guard REFUSES, by raising PermissionError, and logs to
R43_GUARD_LOG (default C:/t/r2x/r42-sandbox/r43p/guard-log):
  * any process whose program or arguments name a `claude` executable (by name, full path, shell or os.system);
  * every socket connect / name lookup / bind (no network);
  * DENIED FIRST, whatever the allowed roots say: any write, mkdir, rename, remove, rmdir, chmod, utime, copy target or
    read-write sqlite3 connection inside
      - every live run folder <C:/t/r2x/r<NN>-sandbox>/r32-v<N> (and r32-v<N>-<anything>, e.g. the owner records),
      - the AI ledger folder C:/t/r2x/ledger,
      - every application tree under C:/t/iso,
      - the frozen packages review42, review43, declaration-r32, declaration-r32-v2 and declaration-r32-v3;
  * ANY open (read included) inside an owner-records folder (r32-v<N>-owner-records), unless the process was started
    with R43_GUARD_OWNER_RECORDS=hash-only (the before/after snapshot hashes that folder as a whole; nothing else may);
  * a write, mkdir, rename, remove, rmdir, chmod or utime outside the allowed roots;
  * a read-write sqlite3 connection outside the allowed roots (mode=ro URIs are allowed outside the denied set);
  * any open of the merged installation's .env.
Allowed write roots: R43_GUARD_ROOTS (';'-separated) when set -- each must lie strictly inside C:/t/r2x/r42-sandbox (not
the base itself) or be the v4 package folder; anything else is ignored and recorded -- otherwise the defaults
C:/t/r2x/r42-sandbox/r43p and PILOT/declaration-r32-v4; plus os.devnull. Nothing else is changed in the process.
R43-42 (review45) copy, three changes: (1) declaration-r32-v4 is DENIED like the other frozen packages; (2) the defaults are
C:/t/r2x/r42-sandbox/r45p only (log r45p/guard-log), and the v4 package is never a root; (3) the sandbox base ITSELF is
accepted as a root only when R45_GUARD_TEST_BASE=1 (the harness test suite creates its sandboxes as siblings at the base);
the deny list still applies first (r32-v<N> folders, owner records, ledger, trees, frozen packages)."""
import os
import re
import sys

_SANDBOX = "c:/t/r2x/r42-sandbox"
_PILOT = "g:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/m2/real-project-pilot"
_V4 = _PILOT + "/declaration-r32-v4"
_DEFAULT_ROOTS = [_SANDBOX + "/r45p"]
_ENV_FILE = "g:/dev (2)/dev/ep-platform-merged/ep-platform/backend/.env"
_LOG = os.environ.get("R43_GUARD_LOG") or "C:/t/r2x/r42-sandbox/r45p/guard-log"
_DENY = re.compile(r"^(?:c:/t/r2x/r\d{2}-sandbox/r32-v\d+(?:-[^/]*)?(?:/|$)|c:/t/r2x/ledger(?:/|$)|c:/t/iso(?:/|$)|"
                   + re.escape(_PILOT) + r"/(?:review42|review43|declaration-r32|declaration-r32-v2|declaration-r32-v3|declaration-r32-v4)(?:/|$))")
_OWNER_RECORDS = re.compile(r"^c:/t/r2x/r\d{2}-sandbox/r32-v\d+-owner-records(?:/|$)")
_OWNER_HASH_ONLY = os.environ.get("R43_GUARD_OWNER_RECORDS") == "hash-only"
_IGNORED = []


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
        lp = os.path.realpath(p).replace("\\", "/")      # resolves 8.3 short names and junctions where possible
    except (OSError, ValueError):
        lp = p
    return lp.lower().rstrip("/")


def _roots():
    raw = os.environ.get("R43_GUARD_ROOTS")
    if not raw:
        return list(_DEFAULT_ROOTS)
    out = []
    for r in raw.split(";"):
        n = _norm(r.strip()) if r.strip() else ""
        if n and (((n.startswith(_SANDBOX + "/") or (n == _SANDBOX and os.environ.get("R45_GUARD_TEST_BASE") == "1")) and not _DENY.match(n))):
            out.append(n)
        elif n:
            _IGNORED.append(n)
    return out


_ROOTS = _roots()


def _allowed(p):
    n = _norm(p)
    if n in ("nul", "//./nul") or n.endswith("/nul"):
        return True
    if _DENY.match(n):
        return False
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
    raise PermissionError(f"R43 guard refused {kind}: {detail}")


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
        n = _norm(path)
        if n == _ENV_FILE:
            _refuse("open .env", path)
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & _WRITE_FLAGS)
        if _OWNER_RECORDS.match(n) and (writing or not _OWNER_HASH_ONLY):
            _refuse("open owner records", path)
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
        ro = False
        if s.startswith("file:"):
            ro = "mode=ro" in s
            s = s[5:].split("?", 1)[0]
        n = _norm(s)
        if _OWNER_RECORDS.match(n):
            _refuse("sqlite3 owner records", s)
        if ro:
            return
        if not _allowed(s):
            _refuse("sqlite3 read-write", s)
    elif event in ("subprocess.Popen", "os.system", "os.exec", "os.spawn", "os.posix_spawn", "os.startfile"):
        payload = list(args)
        if _names_claude(payload[0] if event != "os.system" else payload[0]) or (len(payload) > 1 and _names_claude(payload[1])):
            _refuse("claude process", repr(payload[:2])[:400])
    elif event in ("socket.connect", "socket.getaddrinfo", "socket.gethostbyname", "socket.sendto", "socket.bind"):
        _refuse("network", repr(args)[:200])


if _IGNORED:
    _record("ignored R43_GUARD_ROOTS entries", repr(_IGNORED))
sys.addaudithook(_hook)
