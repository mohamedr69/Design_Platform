"""WAL-consistent snapshot of the live SQLite DB via the backup API.

Source is opened read-only (URI mode=ro) so this connection can never write,
checkpoint or truncate the WAL. The backup runs as a single read transaction,
so the copy is one consistent point in time even while the owner's services
write. Destination is the isolated scratch area only.
"""
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.parse

SRC = r"G:\dev (2)\dev\ep-platform\backend\ep_platform.db"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(dst):
    if os.path.exists(dst):
        raise SystemExit("refusing to overwrite existing snapshot " + dst)
    before = {s: os.stat(SRC + s).st_size for s in ("", "-wal", "-shm") if os.path.exists(SRC + s)}
    uri = "file:" + urllib.parse.quote(SRC.replace("\\", "/")) + "?mode=ro"
    src = sqlite3.connect(uri, uri=True)
    src.execute("PRAGMA query_only=ON")
    journal = src.execute("PRAGMA journal_mode").fetchone()[0]
    out = sqlite3.connect(dst)
    t0 = time.time()
    # pages=-1: copy everything in one step = one read transaction = one consistent snapshot.
    src.backup(out, pages=-1)
    t1 = time.time()
    out.close()
    src.close()
    snap = sqlite3.connect("file:" + urllib.parse.quote(dst.replace("\\", "/")) + "?mode=ro", uri=True)
    snap.execute("PRAGMA query_only=ON")
    integrity = snap.execute("PRAGMA integrity_check").fetchall()
    user_version = snap.execute("PRAGMA user_version").fetchone()[0]
    try:
        alembic = [r[0] for r in snap.execute("SELECT version_num FROM alembic_version")]
    except sqlite3.Error as e:
        alembic = ["ERROR:%s" % e]
    tables = [r[0] for r in snap.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    counts = {t: snap.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for t in tables}
    total_changes = snap.total_changes
    snap.close()
    info = {
        "source_identity": "live ep-platform backend DB (path recorded privately)",
        "source_journal_mode": journal,
        "source_sizes_before": before,
        "snapshot_started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        "snapshot_finished_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t1)),
        "method": "sqlite3.Connection.backup(pages=-1) from mode=ro source",
        "snapshot_sha256": sha(dst),
        "snapshot_size": os.path.getsize(dst),
        "integrity_check": integrity,
        "user_version": user_version,
        "alembic_version": alembic,
        "table_counts": counts,
        "snapshot_total_changes_during_checks": total_changes,
        "sqlite_version": sqlite3.sqlite_version,
    }
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
