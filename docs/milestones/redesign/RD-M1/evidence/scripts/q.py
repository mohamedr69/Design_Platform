"""Query-only access to the audit snapshot. Usage: python q.py "SQL" [json]

The snapshot is opened with mode=ro + PRAGMA query_only=ON, and total_changes
is asserted to be 0 after every query.
"""
import json
import sqlite3
import sys
import urllib.parse

DB = r"<PC-B user profile>\AppData\Local\Temp\claude\g--dev--2--dev\6f67ec6f-cb75-49d6-9946-10047734e054\scratchpad\rdm1\db\ep_platform.audit-snapshot.db"


def connect():
    c = sqlite3.connect("file:" + urllib.parse.quote(DB.replace("\\", "/")) + "?mode=ro", uri=True)
    c.execute("PRAGMA query_only=ON")
    c.row_factory = sqlite3.Row
    return c


def run(sql, params=()):
    c = connect()
    try:
        rows = [dict(r) for r in c.execute(sql, params)]
        assert c.total_changes == 0, "snapshot changed!"
        return rows
    finally:
        c.close()


if __name__ == "__main__":
    rows = run(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "json":
        print(json.dumps(rows, indent=1, default=str))
    else:
        for r in rows:
            print({k: (str(v)[:300] if v is not None else None) for k, v in r.items()})
