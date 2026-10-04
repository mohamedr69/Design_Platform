"""ORCH-08 (A-09 points 1 and 3; R35-09, R35-10, R38-08, R38-13): the ONE durable experiment budget of a run -- an
immutable PARENT budget with separately auditable LANE allowances, the per-project ROLLING-WINDOW limit, durable refusal
and stop records, and the audit view. Successor of the review34 LaneAllowance (reserve before dispatch; never raised,
never reset, never re-created).

Parent budget (bound once in the file, never changed): total ceiling 556 requests, input / output token bounds and the
elapsed bound (seconds from the run's creation, i.e. this file's binding time). Lane allowances B 240, C 240, R 40,
P 36 (sum <= total): a charge is refused when its lane's own allowance is used -- a lane never borrows another lane's
allowance, whatever the others have left -- or when the parent total, a parent token bound or the elapsed bound is
reached. Charges are never refunded: a failed, timed-out, interrupted or dispatched-but-unsaved request stays charged
(its outcome stays 'dispatched' when the answer was never saved).
Project window (A-09 point 1): at most project_window.limit charges per project in any rolling project_window.window_s,
counted across ALL lanes. A request it refuses is NOT charged and NOT permanent: WindowDeferred carries the earliest
retry time (when the oldest charge that keeps the window full leaves it); the lane DEFERS the document and a resume
processes it once the window frees. A retry time beyond the elapsed bound is permanent instead ('deferral_beyond_bound':
the document ends INCOMPLETE, visibly).
Every refusal is recorded (table refusals: lane, project, document, page, task, kind, detail, retry time, invocation),
and every terminal stop of a lane (table stops) is kept for good: resume never resets an allowance, a charge, a refusal
or a terminal stop.
RC-4 (carried): the file is bound to ONE run key (the declaration sha256 in live mode) with its caps, window and parent;
opening it with another key or other values is refused; bind_store() binds the capture store to the same key.
AllowanceProvider sits between the capture store and the identity guard: it charges (or refuses) before the request
can leave, then settles the charge with the response's outcome, model, tokens and ledger entry id. audit() is the
ALLOWANCE-AUDIT view (also: allowance_r32.py audit <allowance.sqlite> <out json> [<ledger> <scope>], read-only).
ORCH-08C (Verification 39): a window deferral also carries retry_at_full {planning, structural} -- the time at which the
project's remaining requests (its PROJECT-REQUEST-BOUNDS totals minus its charges so far) fit the window, or the window is
empty when they exceed it (full_retry_time; R39-08) -- for the declared resume_policy; a charge carries a note, and the
audit lists every retry of a failed request ('retry N of <bound key>', R39-16) -- charged like any request, never refunded."""
from __future__ import annotations

import datetime
import json
import os
import sqlite3
import sys
import time

CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PARENT = {"total": 556, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 604800}
PROJECT_WINDOW = {"limit": 60, "window_s": 86400}
BINDING_TABLE = "r38_binding"
PERMANENT_KINDS = ("lane_allowance", "parent_ceiling", "parent_input_tokens", "parent_output_tokens", "parent_elapsed",
                   "deferral_beyond_bound", "unattributed", "terminal_stop", "identity_invalid")
REFUSAL_KINDS = PERMANENT_KINDS + ("project_window",)


class AllowanceRefused(RuntimeError):
    def __init__(self, kind: str, detail: str, *, retry_at: float | None = None, ep=None):
        super().__init__(f"{kind}: {detail}")
        self.kind, self.detail, self.retry_at, self.ep = kind, detail, retry_at, ep


class WindowDeferred(AllowanceRefused):
    """The project window is full: not charged, not permanent; retry_at = the earliest time the window frees (one slot);
    retry_at_full = {'planning': t, 'structural': t}: the time at which the project's REMAINING requests (its planning
    estimate / structural maximum minus what it was charged so far) fit within the window -- or, when they exceed one
    window, the time the window is empty (ORCH-08C, R39-08)."""

    def __init__(self, kind: str, detail: str, *, retry_at: float | None = None, ep=None, retry_at_full: dict | None = None,
                 remaining: dict | None = None):
        super().__init__(kind, detail, retry_at=retry_at, ep=ep)
        self.retry_at_full, self.remaining = retry_at_full, remaining


def full_retry_time(ats: list[float], limit: int, window_s: int, remaining: int, now: float) -> float:
    """The earliest time t >= now at which `remaining` more charges fit in the rolling window given the charges `ats` now
    inside it: count(ats > t - window_s) + remaining <= limit; when remaining >= limit, the time the window is empty."""
    ats = sorted(ats)
    n = len(ats)
    keep = limit - int(remaining)
    if keep >= n:
        return now
    if keep <= 0:
        return max(now, ats[-1] + window_s) if ats else now
    return max(now, ats[n - keep - 1] + window_s)


class DeferDocument(BaseException):
    """Raised through the application (it catches Exception only) so the lane defers the whole document; carries the
    window refusal. BaseException on purpose: no application handler may swallow it as a failed call."""

    def __init__(self, refusal: WindowDeferred, lane: str):
        super().__init__(str(refusal))
        self.refusal, self.lane = refusal, lane


def _utc(ts) -> str | None:
    return None if ts is None else datetime.datetime.fromtimestamp(float(ts), datetime.timezone.utc).isoformat(timespec="seconds")


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
        raise AllowanceRefused("binding", f"the file is bound to another run or other limits: {diff}")
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


_SCHEMA = """
create table if not exists caps (lane text primary key, cap integer, fixed_at real);
create table if not exists charges (id integer primary key autoincrement, lane text, ep text, at real, invocation integer,
  doc text, page text, task text, bound_key text, outcome text, ledger_entry integer, model text, input_tokens integer,
  output_tokens integer, settled_at real, note text);
create table if not exists refusals (id integer primary key autoincrement, lane text, ep text, at real, invocation integer,
  doc text, page text, task text, kind text, detail text, retry_at real);
create table if not exists stops (lane text primary key, kind text, reason text, invocation integer, at real);
"""


class LaneAllowance:
    def __init__(self, path, caps=None, project_window=None, *, parent=None, run_key: str, require_project: bool = False, create: bool = True,
                 project_totals: dict | None = None):
        """project_totals (ORCH-08C, R39-08): {project: {'planning': n, 'structural': n}} -- the project's all-lane request
        totals from PROJECT-REQUEST-BOUNDS.json; used only to compute a deferral's retry_at_full (never a limit)."""
        if not run_key:
            raise AllowanceRefused("binding", "an allowance is always bound to a run key (the declaration sha256 in live mode)")
        self.project_totals = {str(k).replace("EP-", ""): dict(v) for k, v in (project_totals or {}).items()}
        self.path, self.caps = str(path), {k: int(v) for k, v in dict(caps or CAPS).items()}
        self.window = {k: int(v) for k, v in dict(project_window or PROJECT_WINDOW).items()}
        self.parent = {k: int(v) for k, v in dict(parent or PARENT).items()}
        if set(self.window) != {"limit", "window_s"} or self.window["limit"] < 1 or self.window["window_s"] < 1:
            raise AllowanceRefused("binding", f"project_window must be {{limit >= 1, window_s >= 1}} ({self.window})")
        if set(self.parent) != set(PARENT) or sum(self.caps.values()) > self.parent["total"]:
            raise AllowanceRefused("binding", f"the lane allowances {self.caps} must fit the parent total {self.parent.get('total')}")
        self.run_key, self.require_project = run_key, require_project
        if not create and not os.path.exists(self.path):
            raise AllowanceRefused("binding", f"{self.path} does not exist: a lane never creates the run's allowance")
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        con = self._con()
        try:
            con.executescript(_SCHEMA)
            con.execute("begin immediate")
            try:
                self.binding = _bind(con, run_key, {"caps": dict(sorted(self.caps.items())), "project_window": self.window, "parent": self.parent})
            except AllowanceRefused:
                con.execute("rollback")
                raise
            for lane, cap in self.caps.items():
                row = con.execute("select cap from caps where lane = ?", (lane,)).fetchone()
                if row is None:
                    con.execute("insert into caps values (?, ?, ?)", (lane, int(cap), time.time()))
                elif int(row[0]) != int(cap):
                    con.execute("rollback")
                    raise AllowanceRefused("binding", f"lane {lane}: the allowance was fixed at {row[0]}; a cap is never raised or changed ({cap})")
            self.bound_at = float(con.execute(f"select v from {BINDING_TABLE} where k = 'bound_at'").fetchone()[0])
            con.execute("commit")
        finally:
            con.close()

    def _con(self):
        return sqlite3.connect(self.path, timeout=60, isolation_level=None)

    # ---- reads ---------------------------------------------------------------------------------------------------------
    def bound_end(self) -> float:
        return self.bound_at + self.parent["elapsed_s"]

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

    def stops(self) -> dict:
        con = self._con()
        try:
            return {r[0]: {"kind": r[1], "reason": r[2], "invocation": r[3], "at_utc": _utc(r[4])}
                    for r in con.execute("select lane, kind, reason, invocation, at from stops order by lane")}
        finally:
            con.close()

    def _rows(self, sql, args=()):
        con = self._con()
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql, args)]
        finally:
            con.close()

    # ---- the checks (one function: precheck writes nothing, charge runs it inside its transaction) -------------------------
    def _check(self, con, lane: str, ep, now: float):
        if ep is None and self.require_project:
            raise AllowanceRefused("unattributed", f"lane {lane}: a request that cannot be attributed to a project is refused (the project window applies to every request)")
        stop = con.execute("select kind, reason from stops where lane = ?", (lane,)).fetchone()
        if stop:
            raise AllowanceRefused("terminal_stop", f"lane {lane} is terminally stopped ({stop[0]}: {stop[1]}); a resume never resets it")
        cap = con.execute("select cap from caps where lane = ?", (lane,)).fetchone()
        if cap is None:
            raise AllowanceRefused("lane_allowance", f"lane {lane} has no allowance")
        if con.execute("select count(*) from charges where lane = ?", (lane,)).fetchone()[0] >= cap[0]:
            raise AllowanceRefused("lane_allowance", f"lane {lane}: its own allowance {cap[0]} is used (lanes never borrow)")
        total, tin, tout = con.execute("select count(*), coalesce(sum(input_tokens), 0), coalesce(sum(output_tokens), 0) from charges").fetchone()
        if total >= self.parent["total"]:
            raise AllowanceRefused("parent_ceiling", f"the parent budget {self.parent['total']} is used")
        if tin >= self.parent["input_tokens"]:
            raise AllowanceRefused("parent_input_tokens", f"{tin} input tokens >= the parent bound {self.parent['input_tokens']}")
        if tout >= self.parent["output_tokens"]:
            raise AllowanceRefused("parent_output_tokens", f"{tout} output tokens >= the parent bound {self.parent['output_tokens']}")
        if now > self.bound_end():
            raise AllowanceRefused("parent_elapsed", f"the elapsed bound ended at {_utc(self.bound_end())}")
        if ep is not None:
            since = now - self.window["window_s"]
            ats = [r[0] for r in con.execute("select at from charges where ep = ? and at > ? order by at", (str(ep), since))]
            if len(ats) >= self.window["limit"]:
                retry = ats[len(ats) - self.window["limit"]] + self.window["window_s"]
                detail = (f"EP-{ep}: {len(ats)} charges in the rolling {self.window['window_s']} s window (limit {self.window['limit']}, all lanes); "
                          f"earliest retry {_utc(retry)}")
                if retry > self.bound_end():
                    raise AllowanceRefused("deferral_beyond_bound", detail + f" is after the elapsed bound {_utc(self.bound_end())}", retry_at=retry, ep=ep)
                full, remaining = None, None
                totals = self.project_totals.get(str(ep))
                if totals:
                    charged = con.execute("select count(*) from charges where ep = ?", (str(ep),)).fetchone()[0]
                    remaining = {b: max(1, int(-(-float(totals[b]) // 1)) - charged) for b in ("planning", "structural") if b in totals}
                    full = {b: full_retry_time(ats, self.window["limit"], self.window["window_s"], q, now) for b, q in remaining.items()}
                    detail += "; retry_at_full " + ", ".join(f"{b} {_utc(t)} ({remaining[b]} remaining)" for b, t in full.items())
                raise WindowDeferred("project_window", detail, retry_at=retry, ep=ep, retry_at_full=full, remaining=remaining)

    def precheck(self, lane: str, ep, now: float | None = None) -> None:
        con = self._con()
        try:
            self._check(con, lane, ep, time.time() if now is None else now)
        finally:
            con.close()

    def charge(self, lane: str, ep, *, invocation=None, doc=None, page=None, task="", bound_key=None, note="", now: float | None = None) -> int:
        now = time.time() if now is None else now
        con = self._con()
        try:
            con.execute("begin immediate")
            try:
                self._check(con, lane, ep, now)
            except AllowanceRefused:
                con.execute("rollback")
                raise
            cur = con.execute("insert into charges (lane, ep, at, invocation, doc, page, task, bound_key, outcome, note) values (?,?,?,?,?,?,?,?,?,?)",
                              (lane, None if ep is None else str(ep), now, invocation, doc, None if page is None else str(page), task, bound_key,
                               "dispatched", note))
            con.execute("commit")
            return cur.lastrowid
        finally:
            con.close()

    def settle(self, charge_id: int, outcome: str, *, model=None, ledger_entry=None, input_tokens=None, output_tokens=None) -> None:
        con = self._con()
        try:
            con.execute("update charges set outcome = ?, model = ?, ledger_entry = coalesce(?, ledger_entry), input_tokens = ?, output_tokens = ?, "
                        "settled_at = ? where id = ?", (outcome, model, ledger_entry, input_tokens, output_tokens, time.time(), charge_id))
        finally:
            con.close()

    def record_refusal(self, lane, kind, detail, *, ep=None, invocation=None, doc=None, page=None, task=None, retry_at=None) -> int:
        con = self._con()
        try:
            cur = con.execute("insert into refusals (lane, ep, at, invocation, doc, page, task, kind, detail, retry_at) values (?,?,?,?,?,?,?,?,?,?)",
                              (lane, None if ep is None else str(ep), time.time(), invocation, doc, None if page is None else str(page), task, kind,
                               detail, retry_at))
            return cur.lastrowid
        finally:
            con.close()

    def record_stop(self, lane, kind, reason, invocation=None) -> bool:
        """A terminal stop of a lane, kept for good (the first one wins; never deleted)."""
        con = self._con()
        try:
            cur = con.execute("insert or ignore into stops (lane, kind, reason, invocation, at) values (?, ?, ?, ?, ?)",
                              (lane, kind, reason, invocation, time.time()))
            return cur.rowcount == 1
        finally:
            con.close()

    # ---- the audit view --------------------------------------------------------------------------------------------------
    def audit(self, ledger_path=None, scope=None) -> dict:
        charges = self._rows("select * from charges order by id")
        refusals = self._rows("select * from refusals order by id")
        caps = self.caps_fixed()
        lanes = {}
        for lane in sorted(caps):
            mine = [c for c in charges if c["lane"] == lane]
            by = {}
            for c in mine:
                by[c["outcome"]] = by.get(c["outcome"], 0) + 1
            lanes[lane] = {"allowance": caps[lane], "charged": len(mine), "remaining": caps[lane] - len(mine), "by_outcome": by,
                           "dispatched_never_settled": sum(1 for c in mine if c["outcome"] == "dispatched"),
                           "refusals": sum(1 for r in refusals if r["lane"] == lane)}
        out = {"schema": "r38-allowance-audit-1", "run_key": self.run_key, "parent": self.parent, "project_window": self.window,
               "bound_at_utc": _utc(self.bound_at), "elapsed_bound_ends_utc": _utc(self.bound_end()), "lanes": lanes,
               "total_charged": len(charges), "parent_remaining": self.parent["total"] - len(charges),
               "tokens_charged": {"input": sum(c["input_tokens"] or 0 for c in charges), "output": sum(c["output_tokens"] or 0 for c in charges)},
               "charges": [{"id": c["id"], "lane": c["lane"], "project": f"EP-{c['ep']}" if c["ep"] else None, "document": c["doc"], "page": c["page"],
                            "task": c["task"], "outcome": c["outcome"], "ledger_entry": c["ledger_entry"], "model": c["model"], "invocation": c["invocation"],
                            "charged_at_utc": _utc(c["at"]), "settled_at_utc": _utc(c["settled_at"]), "bound_key": c["bound_key"],
                            "note": c.get("note") or ""} for c in charges],
               "retries": [{"id": c["id"], "lane": c["lane"], "document": c["doc"], "page": c["page"], "task": c["task"], "outcome": c["outcome"],
                            "note": c["note"]} for c in charges if str(c.get("note") or "").startswith("retry ")],
               "refusals": [{"id": r["id"], "lane": r["lane"], "project": f"EP-{r['ep']}" if r["ep"] else None, "document": r["doc"], "page": r["page"],
                             "task": r["task"], "kind": r["kind"], "detail": r["detail"], "retry_at_utc": _utc(r["retry_at"]), "invocation": r["invocation"],
                             "at_utc": _utc(r["at"])} for r in refusals],
               "stops": self.stops(),
               "rules": {"no_borrowing": "a lane's charge is refused once its OWN allowance is used, whatever other lanes have left",
                         "never_refunded": "failed, timed-out, interrupted and dispatched-but-unsaved requests stay charged",
                         "resume": "a resume re-opens this file: no allowance, charge, refusal or stop is reset",
                         "retries": "a failed request dispatched again on the application's retry path is a new charge (note 'retry N of ...'), never refunded"}}
        out["reconciliation"] = reconcile(out, ledger_path, scope) if ledger_path else {
            "ledger": None, "note": "no ledger in this run (dry): ledger_entry is null for every charge"}
        return out


def reconcile(audit: dict, ledger_path, scope) -> dict:
    """The lane allowances against the ONE ledger scope (the backstop with the total ceiling), read-only."""
    con = sqlite3.connect(f"file:{str(ledger_path).replace(os.sep, '/')}?mode=ro", uri=True)
    try:
        entries = {r[0]: {"state": r[1], "outcome": r[2]} for r in con.execute("select id, state, outcome from entries where scope = ?", (scope,))}
        lim = con.execute("select limits from scopes where scope = ?", (scope,)).fetchone()
    finally:
        con.close()
    linked = {c["ledger_entry"] for c in audit["charges"] if c["ledger_entry"] is not None}
    dispatch_entries = [i for i, e in entries.items() if e["state"] not in ("refused", "cache_hit")]
    problems = []
    unknown = sorted(linked - set(entries))
    if unknown:
        problems.append(f"charges name ledger entries that are not in the scope: {unknown[:10]}")
    orphans = sorted(i for i in entries if i not in linked and entries[i]["state"] != "cache_hit")
    limits = json.loads(lim[0]) if lim else None
    if limits and limits.get("requests") is not None and audit["parent"]["total"] != limits["requests"]:
        problems.append(f"the scope's request limit {limits['requests']} differs from the parent total {audit['parent']['total']}")
    if len(dispatch_entries) > audit["total_charged"]:
        problems.append(f"{len(dispatch_entries)} ledger dispatch entries > {audit['total_charged']} charges")
    return {"ledger": str(ledger_path), "scope": scope, "scope_limits": limits, "ledger_entries": len(entries),
            "ledger_dispatch_entries": len(dispatch_entries), "ledger_refused_entries": sum(1 for e in entries.values() if e["state"] == "refused"),
            "charges_with_ledger_entry": len(linked), "charges_without_ledger_entry": audit["total_charged"] - len(linked),
            "ledger_entries_without_charge_record": orphans,
            "rule": ("every charge precedes at most one ledger reservation (the ledger is inside the guard): ledger dispatch entries <= "
                     "charges <= parent total = the scope's request limit; a charge without a ledger entry was refused before the ledger "
                     "(guard, identity) or never settled; a ledger entry without a charge record was reserved by a process that died before "
                     "its charge was settled"),
            "consistent": not problems, "problems": problems}


class AllowanceProvider:
    """capture store -> AllowanceProvider -> IdentityGuard -> dispatch guard (live) or dry refusing stub (dry)."""
    name, ready, status = "allowance", True, "r38 parent budget and lane allowances"

    def __init__(self, allowance: LaneAllowance, lane: str, inner, response_cls, ep_of=lambda: None, *, context_of=dict, invocation=None,
                 ledger_entry_of=lambda: None, on_refusal=None):
        self.allowance, self.lane, self.inner, self.response_cls, self.ep_of = allowance, lane, inner, response_cls, ep_of
        self.context_of, self.invocation, self.ledger_entry_of, self.on_refusal = context_of, invocation, ledger_entry_of, on_refusal
        self.refused, self.charged = 0, 0

    def complete(self, request, *, doc=None, bound_key=None, note=""):
        ctx = self.context_of() or {}
        ep = self.ep_of()
        try:
            cid = self.allowance.charge(self.lane, ep, invocation=self.invocation, doc=doc or ctx.get("sha256"), page=ctx.get("page"),
                                        task=getattr(request, "task", ""), bound_key=bound_key, note=note or "")
        except WindowDeferred as exc:
            raise DeferDocument(exc, self.lane) from None
        except AllowanceRefused as exc:
            self.refused += 1
            self.allowance.record_refusal(self.lane, exc.kind, exc.detail, ep=ep, invocation=self.invocation, doc=doc or ctx.get("sha256"),
                                          page=ctx.get("page"), task=getattr(request, "task", None), retry_at=exc.retry_at)
            if self.on_refusal:
                self.on_refusal(exc, request)
            return self.response_cls(data=None, model="allowance", error="budget", error_detail=f"harness allowance refused ({exc.kind}): {exc.detail}")
        self.charged += 1
        resp = self.inner.complete(request)
        usage = getattr(resp, "usage", None)
        self.allowance.settle(cid, getattr(resp, "error", None) or "ok", model=getattr(resp, "model", None), ledger_entry=self.ledger_entry_of(),
                              input_tokens=getattr(usage, "input_tokens", None), output_tokens=getattr(usage, "output_tokens", None))
        return resp


def main(argv) -> int:
    """allowance_r32.py audit <allowance.sqlite> <out json> [<ledger path> <scope>]  (read-only on both databases)."""
    if len(argv) < 4 or argv[1] != "audit":
        print(main.__doc__)
        return 2
    con = sqlite3.connect(f"file:{argv[2].replace(os.sep, '/')}?mode=ro", uri=True)
    try:
        b = dict(con.execute(f"select k, v from {BINDING_TABLE}").fetchall())
        caps = dict(con.execute("select lane, cap from caps").fetchall())
    finally:
        con.close()
    a = object.__new__(LaneAllowance)
    a.path, a.caps, a.run_key = argv[2], caps, b["run_key"]
    a.window, a.parent, a.bound_at = json.loads(b["project_window"]), json.loads(b["parent"]), float(b["bound_at"])
    a._con = lambda: sqlite3.connect(f"file:{argv[2].replace(os.sep, '/')}?mode=ro", uri=True)
    out = a.audit(argv[4] if len(argv) > 5 else None, argv[5] if len(argv) > 5 else None)
    with open(argv[3], "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: out[k] for k in ("total_charged", "parent_remaining")} | {"lanes": {k: v["charged"] for k, v in out["lanes"].items()}}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
