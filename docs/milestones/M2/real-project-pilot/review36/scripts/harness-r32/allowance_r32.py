"""ORCH-05.1 and ORCH-05C (Review 34 RC-4 / R34-04): the ONE durable request allowance of a declaration (reserve before
dispatch; never raised, never reset, never re-created).

Patterned on the reviewed DocAllowance (r16 boq_harness.DocAllowance: a SQLite row per key, persisted across processes and
resumes) and extended to the lane caps of plan v2 section 7 (B 240 = C 240, R 40, P 36; total 556) and the per-project
UTC-day limit (60 charges per project per UTC day, counted across ALL lanes). charge(lane, ep) runs in one BEGIN IMMEDIATE
transaction: it refuses when the lane cap or the project's day limit is reached, otherwise it records the charge FIRST and
only then may the caller dispatch. A charge is never refunded: a request whose answer never came stays charged (the
capture store serves it as 'interrupted_charged').
RC-4: the allowance file is bound to ONE run key -- the declaration sha256 in live mode (a dry run's key in dry mode) --
in its r34_binding table, together with its caps and its project-day limit. Opening it with another key, other caps or
another day limit is refused; a second invocation (a resume) re-opens the same caps and counters and NEVER receives fresh
caps. bind_store() puts the same run key into the capture store file (the capture_store module is unchanged).
AllowanceProvider sits between the capture store and the dispatch guard: a refusal returns 'allowance_refused' without
reaching the guard. In live mode (require_project=True) a request that cannot be attributed to a project is refused, so the
day limit can never be bypassed. The allowance lives in the declaration's run folder, never in the shared C:/t/r2x/ledger."""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import time

CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PROJECT_DAY_LIMIT = 60
BINDING_TABLE = "r34_binding"


class AllowanceRefused(RuntimeError):
    pass


def _bind(con, run_key: str, extra: dict) -> dict:
    """Create the binding row once, or verify it (same key and same extra values); raise AllowanceRefused otherwise."""
    con.execute(f"create table if not exists {BINDING_TABLE} (k text primary key, v text)")
    rows = dict(con.execute(f"select k, v from {BINDING_TABLE}").fetchall())
    want = {"run_key": run_key} | {k: json.dumps(v, sort_keys=True) for k, v in extra.items()}
    if not rows:
        for k, v in want.items():
            con.execute(f"insert into {BINDING_TABLE} (k, v) values (?, ?)", (k, v))
        con.execute(f"insert into {BINDING_TABLE} (k, v) values (?, ?)", ("bound_at", str(time.time())))
        return {"created": True}
    diff = {k: {"stored": rows.get(k), "given": v} for k, v in want.items() if rows.get(k) != v}
    if diff:
        raise AllowanceRefused(f"the file is bound to another run or other limits: {diff}")
    return {"created": False}


def bind_store(path, run_key: str) -> dict:
    """Bind the capture-store file of a run to its run key (created once; a different key is refused)."""
    con = sqlite3.connect(str(path), timeout=60, isolation_level=None)
    try:
        con.execute("begin immediate")
        try:
            out = _bind(con, run_key, {})
        except AllowanceRefused:
            con.execute("rollback")
            raise
        con.execute("commit")
        return out
    finally:
        con.close()


def bound_key(path) -> str | None:
    con = sqlite3.connect(f"file:{str(path).replace(os.sep, '/')}?mode=ro", uri=True)
    try:
        row = con.execute(f"select v from {BINDING_TABLE} where k = 'run_key'").fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError:
        return None
    finally:
        con.close()


class LaneAllowance:
    def __init__(self, path, caps=None, project_day_limit=PROJECT_DAY_LIMIT, *, run_key: str, require_project: bool = False, create: bool = True):
        if not run_key:
            raise AllowanceRefused("an allowance is always bound to a run key (the declaration sha256 in live mode)")
        self.path, self.caps, self.project_day_limit = str(path), dict(caps or CAPS), int(project_day_limit)
        self.run_key, self.require_project = run_key, require_project
        if not create and not os.path.exists(self.path):
            raise AllowanceRefused(f"{self.path} does not exist: a lane never creates the run's allowance")
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        con = self._con()
        try:
            con.execute("begin immediate")
            con.execute("create table if not exists caps (lane text primary key, cap integer, fixed_at real)")
            con.execute("create table if not exists charges (id integer primary key autoincrement, lane text, ep text, day text, at real, note text)")
            try:
                self.binding = _bind(con, run_key, {"caps": dict(sorted(self.caps.items())), "project_day_limit": self.project_day_limit})
            except AllowanceRefused:
                con.execute("rollback")
                raise
            for lane, cap in self.caps.items():
                row = con.execute("select cap from caps where lane = ?", (lane,)).fetchone()
                if row is None:
                    con.execute("insert into caps values (?, ?, ?)", (lane, int(cap), time.time()))
                elif int(row[0]) != int(cap):
                    con.execute("rollback")
                    raise AllowanceRefused(f"lane {lane}: the allowance was fixed at {row[0]}; a cap is never raised or changed ({cap})")
            con.execute("commit")
        finally:
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

    def caps_fixed(self) -> dict:
        con = self._con()
        try:
            return {lane: cap for lane, cap in con.execute("select lane, cap from caps order by lane")}
        finally:
            con.close()

    def charge(self, lane: str, ep: str | None, note: str = "") -> int:
        day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        if ep is None and self.require_project:
            raise AllowanceRefused(f"lane {lane}: a request that cannot be attributed to a project is refused (the project-day limit applies to every request)")
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
                    raise AllowanceRefused(f"EP-{ep}: UTC-day limit {self.project_day_limit} reached ({day}, all lanes)")
            cur = con.execute("insert into charges (lane, ep, day, at, note) values (?, ?, ?, ?, ?)", (lane, None if ep is None else str(ep), day, time.time(), note))
            con.execute("commit")
            return cur.lastrowid
        finally:
            con.close()


class AllowanceProvider:
    """capture store -> AllowanceProvider -> dispatch guard (live) or dry refusing stub (dry)."""
    name, ready, status = "allowance", True, "r34 durable per-declaration lane allowance"

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
