"""The application's per-project daily limit (ai_max_calls_per_project_per_day, frozen default 60) applied ACROSS the
experiment's tracks. The application counts fresh AiUsage rows in its own database over the last 24 hours; each track
here is its own sandbox database, so one track cannot see another's calls. This file-backed counter (SQLite,
BEGIN IMMEDIATE, shared by every runner process) holds every fresh request per project with its time, and a runner
refuses a request -- recorded as a budget stop, never a negative -- once the project's rolling-24-hour total across all
tracks has reached the limit. It never raises the application's own limit: each sandbox still enforces it too."""
import sqlite3
import time

PATH = "C:/t/r2x/ledger/project-day.sqlite"
WINDOW_S = 24 * 3600


def _con():
    import os
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    con = sqlite3.connect(PATH, timeout=60, isolation_level=None)
    con.execute("create table if not exists calls (id integer primary key autoincrement, ep text, at real, track text, task text, source text)")
    return con


def used(ep: str, now: float | None = None) -> int:
    con = _con()
    try:
        return con.execute("select count(*) from calls where ep = ? and at >= ?", (ep, (now or time.time()) - WINDOW_S)).fetchone()[0]
    finally:
        con.close()


def take(ep: str, track: str, task: str, limit: int) -> bool:
    """Reserve one request for `ep` if the rolling-24-hour total across tracks is below `limit`."""
    con = _con()
    try:
        con.execute("begin immediate")
        n = con.execute("select count(*) from calls where ep = ? and at >= ?", (ep, time.time() - WINDOW_S)).fetchone()[0]
        if n >= limit:
            con.execute("rollback")
            return False
        con.execute("insert into calls (ep, at, track, task, source) values (?, ?, ?, ?, 'reserved')", (ep, time.time(), track, task))
        con.execute("commit")
        return True
    finally:
        con.close()


def release_last(ep: str, track: str) -> None:
    """A reservation that turned into no request (a ledger refusal) is given back."""
    con = _con()
    try:
        con.execute("delete from calls where id = (select max(id) from calls where ep = ? and track = ? and source = 'reserved')", (ep, track))
    finally:
        con.close()


def record(ep: str, track: str, rows: list[tuple[float, str]]) -> None:
    """Record requests a track made through the application's own path (counted afterwards from its AiUsage)."""
    con = _con()
    try:
        con.execute("begin immediate")
        con.executemany("insert into calls (ep, at, track, task, source) values (?, ?, ?, ?, 'ai_usage')", [(ep, at, track, task) for at, task in rows])
        con.execute("commit")
    finally:
        con.close()


def summary() -> list[dict]:
    con = _con()
    try:
        return [dict(zip(("ep", "track", "source", "n", "first", "last"), r)) for r in
                con.execute("select ep, track, source, count(*), min(at), max(at) from calls group by ep, track, source order by ep, track")]
    finally:
        con.close()
