"""ORCH-05.1: the durable request allowance of the r32 run (reserve before dispatch; never raised, never reset).

Patterned on the reviewed DocAllowance (r16 boq_harness.DocAllowance: a SQLite row per key, persisted across processes and
resumes) and extended to the lane caps of plan v2 section 7 (B 240 = C 240, R 40, P 36; total 556) and the rolling
per-project day limit (60). charge(lane, ep) runs in one BEGIN IMMEDIATE transaction: it refuses when the lane cap or the
project's day limit is reached, otherwise it records the charge FIRST and only then may the caller dispatch. A charge is
never refunded: a request whose answer never came stays charged (the capture store serves it as 'interrupted_charged').
AllowanceProvider sits between the capture store and the dispatch guard: a refusal returns 'allowance_refused' without
reaching the guard. The allowance file lives in the run's own folder, never in the shared C:/t/r2x/ledger."""
from __future__ import annotations

import datetime
import os
import sqlite3
import time

CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PROJECT_DAY_LIMIT = 60


class AllowanceRefused(RuntimeError):
    pass


class LaneAllowance:
    def __init__(self, path, caps=None, project_day_limit=PROJECT_DAY_LIMIT):
        self.path, self.caps, self.project_day_limit = str(path), dict(caps or CAPS), project_day_limit
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        con = self._con()
        con.executescript("""create table if not exists caps (lane text primary key, cap integer, fixed_at real);
                             create table if not exists charges (id integer primary key autoincrement, lane text, ep text, day text,
                               at real, note text);""")
        for lane, cap in self.caps.items():
            row = con.execute("select cap from caps where lane = ?", (lane,)).fetchone()
            if row is None:
                con.execute("insert into caps values (?, ?, ?)", (lane, int(cap), time.time()))
            elif int(row[0]) != int(cap):
                con.close()
                raise AllowanceRefused(f"lane {lane}: the allowance was fixed at {row[0]}; a cap is never raised or changed ({cap})")
        con.close()

    def _con(self):
        return sqlite3.connect(self.path, timeout=60, isolation_level=None)

    def used(self, lane=None) -> int:
        con = self._con()
        try:
            if lane is None:
                return con.execute("select count(*) from charges").fetchone()[0]
            return con.execute("select count(*) from charges where lane = ?", (lane,)).fetchone()[0]
        finally:
            con.close()

    def charge(self, lane: str, ep: str | None, note: str = "") -> int:
        day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        con = self._con()
        try:
            con.execute("begin immediate")
            cap = con.execute("select cap from caps where lane = ?", (lane,)).fetchone()
            if cap is None:
                con.execute("rollback")
                raise AllowanceRefused(f"lane {lane} has no allowance")
            used = con.execute("select count(*) from charges where lane = ?", (lane,)).fetchone()[0]
            if used >= cap[0]:
                con.execute("rollback")
                raise AllowanceRefused(f"lane {lane}: allowance {cap[0]} used")
            if ep is not None:
                n = con.execute("select count(*) from charges where ep = ? and day = ?", (str(ep), day)).fetchone()[0]
                if n >= self.project_day_limit:
                    con.execute("rollback")
                    raise AllowanceRefused(f"EP-{ep}: rolling day limit {self.project_day_limit} reached")
            cur = con.execute("insert into charges (lane, ep, day, at, note) values (?, ?, ?, ?, ?)", (lane, None if ep is None else str(ep), day, time.time(), note))
            con.execute("commit")
            return cur.lastrowid
        finally:
            con.close()


class AllowanceProvider:
    """capture store -> AllowanceProvider -> dispatch guard (live) or dry refusing stub (dry)."""
    name, ready, status = "allowance", True, "r33 durable lane allowance"

    def __init__(self, allowance: LaneAllowance, lane: str, inner, response_cls, ep_of=lambda: None):
        self.allowance, self.lane, self.inner, self.response_cls, self.ep_of = allowance, lane, inner, response_cls, ep_of
        self.refused = 0
        self.charged = 0

    def complete(self, request):
        try:
            self.allowance.charge(self.lane, self.ep_of(), note=getattr(request, "task", ""))
        except AllowanceRefused as exc:
            self.refused += 1
            return self.response_cls(data=None, model="allowance", error="allowance_refused", error_detail=str(exc))
        self.charged += 1
        return self.inner.complete(request)
