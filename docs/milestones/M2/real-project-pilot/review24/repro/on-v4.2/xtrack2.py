"""The cross-track rolling-day counter (a copy of run/xtrack.py) with (a) a clock hook -- XTRACK_FAKE_NOW=<epoch seconds>
replaces the wall clock for the dry-run scheduling probes only (never set in a real run: the runner refuses it unless
PILOT_DRY=1) -- and (b) `capacity(ep, limit)` for the whole-project batch check. Semantics otherwise unchanged: one row
per fresh request, BEGIN IMMEDIATE, a reservation that turned into no request is given back."""
import os
import sqlite3
import time

PATH = "C:/t/r2x/ledger/project-day.sqlite"
WINDOW_S = 24 * 3600


def now() -> float:
    fake = os.environ.get("XTRACK_FAKE_NOW")
    if fake:
        assert os.environ.get("PILOT_DRY") == "1", "a fake clock is a dry-run device only"
        return float(fake)
    return time.time()


def _con():
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    con = sqlite3.connect(PATH, timeout=60, isolation_level=None)
    con.execute("create table if not exists calls (id integer primary key autoincrement, ep text, at real, track text, task text, source text)")
    return con


def used(ep: str, at: float | None = None) -> int:
    con = _con()
    try:
        return con.execute("select count(*) from calls where ep = ? and at >= ?", (ep, (at or now()) - WINDOW_S)).fetchone()[0]
    finally:
        con.close()


def capacity(ep: str, limit: int) -> int:
    return max(0, limit - used(ep))


def take(ep: str, track: str, task: str, limit: int) -> bool:
    con = _con()
    try:
        con.execute("begin immediate")
        n = con.execute("select count(*) from calls where ep = ? and at >= ?", (ep, now() - WINDOW_S)).fetchone()[0]
        if n >= limit:
            con.execute("rollback")
            return False
        con.execute("insert into calls (ep, at, track, task, source) values (?, ?, ?, ?, 'reserved')", (ep, now(), track, task))
        con.execute("commit")
        return True
    finally:
        con.close()


def release_last(ep: str, track: str) -> None:
    con = _con()
    try:
        con.execute("delete from calls where id = (select max(id) from calls where ep = ? and track = ? and source = 'reserved')", (ep, track))
    finally:
        con.close()


def record(ep: str, track: str, rows) -> None:
    con = _con()
    try:
        con.execute("begin immediate")
        con.executemany("insert into calls (ep, at, track, task, source) values (?, ?, ?, ?, 'ai_usage')", [(ep, at, track, task) for at, task in rows])
        con.execute("commit")
    finally:
        con.close()
