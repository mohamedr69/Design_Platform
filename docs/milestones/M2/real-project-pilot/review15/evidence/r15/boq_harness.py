"""R15-01: a document's allowance is consumed DURABLY before a request can leave the process.

HARNESS_VERSION r2x-boq-harness-2026-09-30.r15.1   (r14.1 is preserved unchanged in the Review 14 package)

What r14.1 did wrong: the consumed count was saved only after a whole chunk returned. A process that stopped inside a
chunk had sent requests the store never recorded, and a fresh process received them again (Review 15 probe: 5 sent,
0 persisted, 12 more on resume -- 17 for a 12-call allowance).

The contract now:
  * RESERVE = PERSIST. `DurableBudget.reserve` first takes the application JobBudget's own in-memory reservation
    (all of its limits: calls per document, elapsed, per-project day, escalations, cost), then commits the increment of
    the durable count in the allowance store (SQLite, BEGIN IMMEDIATE, refused at the cap). Only after that commit does
    `reserve` return -- and only after `reserve` returns does EvidenceRun dispatch a request. A process that dies at any
    point therefore finds every request it might have sent already counted. A reservation whose request never left
    (death between commit and dispatch, a provider exception, a refusal after the commit) stays CONSUMED:
    uncertain reservations are spent, never granted again.
  * ONE WRITER per (scope, profile, document): an exclusive OS file lock held for the whole sheet; a second writer is
    refused (AllowanceBusy). The OS releases the lock when a process dies, so a crashed writer never blocks for ever.
  * ATTEMPTS are labelled: each run opens an attempt ('open'); on normal return it is closed ('completed' or
    'stopped: <limit>'); an attempt still 'open' when the next writer takes the lock was interrupted and is marked
    'interrupted' with the count it had reached. Durable evidence (rows committed per chunk) is kept; nothing is erased.
  * The elapsed basis is the FIRST start of the key (persisted before any request); escalations are persisted too.
  * Nothing clears an exhausted state, and no new scope is opened to recover budget.

Resumption is therefore allowed and safe for the allowance (it continues from the durable count, conservatively
including uncertain reservations); it is not claimed to recover the interrupted chunk's un-committed evidence.

Which caps are per document / profile and which are shared: per (scope, profile, document): 12 calls, 120 s, 2
escalations; shared across tracks / processes: the per-project day limit (xtrack) and the ledger scope."""
from __future__ import annotations

import hashlib
import os
import sqlite3
import time

HARNESS_VERSION = "r2x-boq-harness-2026-09-30.r15.1"


class AllowanceBusy(RuntimeError):
    """Another live writer holds this (scope, profile, document) allowance."""


def _lock_file(path: str):
    """Exclusive, non-blocking OS lock on `path`; released by the OS when the holder dies."""
    fh = open(path, "a+b")
    try:
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        raise AllowanceBusy(path)
    return fh


def _unlock_file(fh) -> None:
    try:
        if os.name == "nt":
            import msvcrt
            fh.seek(0)
            msvcrt.locking(fh.fileno(), msvcrt.LK_UNLCK, 1)
    finally:
        fh.close()


class DocAllowance:
    """Durable, per (scope, profile, document) consumption; the only place the count ever grows."""

    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        con = self._con()
        con.execute("create table if not exists allowance (scope text, profile text, sha256 text, calls integer, escalations integer, "
                    "first_started real, updated real, primary key (scope, profile, sha256))")
        con.execute("create table if not exists attempts (id integer primary key autoincrement, scope text, profile text, sha256 text, "
                    "pid integer, started real, ended real, status text, calls_at_start integer, calls_at_end integer)")
        con.close()

    def _con(self):
        return sqlite3.connect(self.path, timeout=60, isolation_level=None)

    def _key_lock_path(self, scope, profile, sha256) -> str:
        d = self.path + ".locks"
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, hashlib.sha256(f"{scope}|{profile}|{sha256}".encode()).hexdigest()[:24] + ".lock")

    def acquire(self, scope, profile, sha256):
        return _lock_file(self._key_lock_path(scope, profile, sha256))

    def load(self, scope: str, profile: str, sha256: str) -> dict:
        """The durable state (created, with its first-start time, before any request)."""
        con = self._con()
        try:
            con.execute("begin immediate")
            r = con.execute("select calls, escalations, first_started from allowance where scope = ? and profile = ? and sha256 = ?",
                            (scope, profile, sha256)).fetchone()
            if r is None:
                now = time.time()
                con.execute("insert into allowance values (?, ?, ?, 0, 0, ?, ?)", (scope, profile, sha256, now, now))
                con.execute("commit")
                return {"calls": 0, "escalations": 0, "first_started": now, "resumed": False}
            con.execute("commit")
            return {"calls": r[0], "escalations": r[1], "first_started": r[2], "resumed": True}
        finally:
            con.close()

    def consume(self, scope, profile, sha256, *, cap_calls: int, escalation: bool, cap_escalations: int) -> tuple[int | None, str | None]:
        """Atomically count one more request. Returns (new count, None) or (None, refused limit)."""
        con = self._con()
        try:
            con.execute("begin immediate")
            calls, esc = con.execute("select calls, escalations from allowance where scope = ? and profile = ? and sha256 = ?",
                                     (scope, profile, sha256)).fetchone()
            if calls + 1 > cap_calls:
                con.execute("rollback")
                return None, "calls_per_document"
            if escalation and esc + 1 > cap_escalations:
                con.execute("rollback")
                return None, "escalations_per_document"
            con.execute("update allowance set calls = calls + 1, escalations = escalations + ?, updated = ? where scope = ? and profile = ? and sha256 = ?",
                        (1 if escalation else 0, time.time(), scope, profile, sha256))
            con.execute("commit")
            return calls + 1, None
        finally:
            con.close()

    def save(self, scope: str, profile: str, sha256: str, calls: int, escalations: int) -> None:
        """Kept for the r14 call signature; never lowers a durable count (consumption is written by `consume`)."""
        con = self._con()
        try:
            con.execute("update allowance set calls = max(calls, ?), escalations = max(escalations, ?), updated = ? where scope = ? and profile = ? and sha256 = ?",
                        (calls, escalations, time.time(), scope, profile, sha256))
        finally:
            con.close()

    def begin_attempt(self, scope, profile, sha256, calls_now: int) -> tuple[int, list]:
        con = self._con()
        try:
            con.execute("begin immediate")
            stale = con.execute("select id, pid, started, calls_at_start from attempts where scope = ? and profile = ? and sha256 = ? and status = 'open'",
                                (scope, profile, sha256)).fetchall()
            # we hold the key's exclusive lock: any attempt still 'open' belongs to a writer that died
            for aid, *_ in stale:
                con.execute("update attempts set status = 'interrupted', calls_at_end = ? where id = ?", (calls_now, aid))
            cur = con.execute("insert into attempts (scope, profile, sha256, pid, started, status, calls_at_start) values (?, ?, ?, ?, ?, 'open', ?)",
                              (scope, profile, sha256, os.getpid(), time.time(), calls_now))
            con.execute("commit")
            return cur.lastrowid, [{"attempt": a, "pid": p, "started": s, "calls_at_start": c} for a, p, s, c in stale]
        finally:
            con.close()

    def end_attempt(self, attempt_id: int, status: str, calls_now: int) -> None:
        con = self._con()
        try:
            con.execute("update attempts set status = ?, ended = ?, calls_at_end = ? where id = ?", (status, time.time(), calls_now, attempt_id))
        finally:
            con.close()

    def attempts(self, scope, profile, sha256) -> list[dict]:
        con = self._con()
        try:
            return [dict(zip(("id", "pid", "started", "ended", "status", "calls_at_start", "calls_at_end"), r)) for r in con.execute(
                "select id, pid, started, ended, status, calls_at_start, calls_at_end from attempts where scope = ? and profile = ? and sha256 = ? order by id",
                (scope, profile, sha256))]
        finally:
            con.close()


class DurableBudget:
    """Wraps the application's JobBudget: its own limits first (in memory), then the durable count, then return.
    Everything else (reconcile, remaining_s, limits, ...) is the JobBudget's own."""

    def __init__(self, inner, allowance: DocAllowance, key: tuple, cap_calls: int) -> None:
        self.__dict__.update(_inner=inner, _allowance=allowance, _key=key, _cap=cap_calls)
        self.__dict__["_budget_exceeded"] = type(inner).reserve.__globals__["BudgetExceeded"]   # the SAME class the caller catches

    def reserve(self, estimated_input, max_output, *, escalation: bool = False):
        inner = self._inner
        reservation = inner.reserve(estimated_input, max_output, escalation=escalation)   # application limits (raises as before)
        count, refused = self._allowance.consume(*self._key, cap_calls=self._cap, escalation=escalation,
                                                 cap_escalations=inner.limits.max_escalations_per_document)
        if refused:
            inner.calls -= 1                     # undo the in-memory reservation: nothing will be sent
            if escalation:
                inner.escalations -= 1
            inner.reserved_cost -= reservation
            raise self._budget_exceeded(refused)
        inner.calls = count                      # in-memory count follows the durable count
        return reservation

    def __getattr__(self, name):
        return getattr(self.__dict__["_inner"], name)

    def __setattr__(self, name, value):
        setattr(self.__dict__["_inner"], name, value)


def _work(er, lines: list, issues: list, variant: str, sha256: str, chunk: int) -> list[dict]:
    selected = er.boq_rows_to_verify([dict(l, _accepted=True) for l in lines], [], variant=variant, sha256=sha256)
    accepted_selected = [r for r, _ in selected]
    held_issues = [i for i in issues if str(i.get("target") or "").startswith("boq_line:")]
    work = [{"lines": [dict(l) for l in accepted_selected[i:i + chunk]], "issues": []} for i in range(0, len(accepted_selected), chunk)]
    work += [{"lines": [], "issues": held_issues[i:i + chunk]} for i in range(0, len(held_issues), chunk)]
    return work


# the Review 13 loop (submitted r2x_boq.py lines 118-133), kept verbatim ONLY for before / after demonstrations
def verify_sheet_submitted(er, run, pdf, *, db, open_budget, lines, issues, variant, sha256, max_calls_per_document, render_dpi) -> list[dict]:
    """The submitted loop (r2x_boq.py lines 118-133): a NEW JobBudget per chunk and per-document stops cleared."""
    results = []
    chunk = max(1, max_calls_per_document - 1)
    for part in _work(er, lines, issues, variant, sha256, chunk):
        run.budget = open_budget(db, None)
        if run.exhausted and not (run.exhausted.startswith("stop:") or "across tracks" in run.exhausted or "ledger" in run.exhausted):
            run.exhausted = None
        results += er.verify_boq_rows(run, pdf, sha256=sha256, extraction={"lines": part["lines"], "issues": part["issues"], "geometry_lines": lines},
                                      render_dpi=render_dpi, preselected=True)
        db.commit()
    return results


def verify_sheet(er, run, pdf, *, db, open_budget, allowance: DocAllowance, scope: str, profile: str, lines, issues, variant, sha256,
                 max_calls_per_document, render_dpi) -> tuple[list[dict], dict]:
    """One durable budget for the document across chunks, retries, resumes and processes; one writer per key."""
    key = (scope, profile, sha256)
    lock = allowance.acquire(*key)                                   # AllowanceBusy if another live writer holds it
    try:
        state = allowance.load(*key)
        attempt, interrupted = allowance.begin_attempt(*key, state["calls"])
        budget = open_budget(db, None)
        budget.calls = state["calls"]
        budget.escalations = state["escalations"]
        budget.started = time.monotonic() - (time.time() - state["first_started"])
        run.budget = DurableBudget(budget, allowance, key, max_calls_per_document)
        results = []
        chunk = max(1, max_calls_per_document - 1)
        for part in _work(er, lines, issues, variant, sha256, chunk):
            results += er.verify_boq_rows(run, pdf, sha256=sha256, extraction={"lines": part["lines"], "issues": part["issues"], "geometry_lines": lines},
                                          render_dpi=render_dpi, preselected=True)
            db.commit()                                              # durable evidence per chunk
        after = allowance.load(*key)["calls"]
        allowance.end_attempt(attempt, "completed" if not run.exhausted else f"stopped: {run.exhausted}", after)
        return results, {"resumed": state["resumed"], "calls_before": state["calls"], "calls_after": after, "exhausted": run.exhausted,
                         "attempt": attempt, "interrupted_attempts_found": interrupted, "harness": HARNESS_VERSION}
    finally:
        _unlock_file(lock)
