"""R14-01: one declared document unit has ONE effective budget across every chunk, retry and escalation.

HARNESS_VERSION r2x-boq-harness-2026-09-30.1

The submitted r2x_boq.py (review13/evidence/scripts/run/r2x_boq.py, lines 124-132) split a sheet's rows into chunks of
(ai_max_calls_per_document - 1) and, for EACH chunk, assigned `run.budget = open_budget(db, None)` -- a new JobBudget
whose call counter and elapsed clock start at zero -- and cleared any per-document stop (`run.exhausted = None`)
unless it was a run-level stop. The per-document limit (12) and the 120 s elapsed limit therefore applied per chunk,
not per document: EP-8430 took 25 requests under EV1 and 35 under EV2 on one PDF. `verify_sheet_submitted` below is
that loop, verbatim in behaviour, kept for the before / after tests.

`verify_sheet` is the corrected loop:
  * the document's budget is opened ONCE and shared by every chunk (its call count, escalation count and elapsed
    basis carry across chunks);
  * a per-document stop (calls_per_document, elapsed_time, ...) is never cleared; later rows are recorded as
    budget-refused reads (state unverified, 'no reading'), earlier evidence is kept;
  * the consumed allowance is persisted per (declaration scope, profile, document sha256) in a small SQLite store,
    so a resume, a new process or a new chunk list cannot create a fresh allowance for the same document and profile;
    the elapsed basis resumes from the first start (wall clock).

Which caps are per document / profile and which are shared (stated for the declaration):
  * per document per profile: ai_max_calls_per_document (12), ai_max_elapsed_s_per_job (120 s), escalations (2) --
    one JobBudget per (scope, profile, document);
  * shared across profiles / tracks / processes: the per-project day limit (60, xtrack.py) and the ledger scope's
    request / elapsed caps."""
from __future__ import annotations

import os
import sqlite3
import time

HARNESS_VERSION = "r2x-boq-harness-2026-09-30.1"


class DocAllowance:
    """Consumed per-document allowance, persisted across chunks, retries, resumes and processes."""

    def __init__(self, path: str) -> None:
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        con = self._con()
        con.execute("create table if not exists allowance (scope text, profile text, sha256 text, calls integer, escalations integer, "
                    "first_started real, updated real, primary key (scope, profile, sha256))")
        con.close()

    def _con(self):
        return sqlite3.connect(self.path, timeout=60, isolation_level=None)

    def load(self, scope: str, profile: str, sha256: str) -> dict:
        con = self._con()
        try:
            r = con.execute("select calls, escalations, first_started from allowance where scope = ? and profile = ? and sha256 = ?",
                            (scope, profile, sha256)).fetchone()
            if r is None:
                now = time.time()
                con.execute("insert into allowance values (?, ?, ?, 0, 0, ?, ?)", (scope, profile, sha256, now, now))
                return {"calls": 0, "escalations": 0, "first_started": now, "resumed": False}
            return {"calls": r[0], "escalations": r[1], "first_started": r[2], "resumed": True}
        finally:
            con.close()

    def save(self, scope: str, profile: str, sha256: str, calls: int, escalations: int) -> None:
        con = self._con()
        try:
            con.execute("update allowance set calls = ?, escalations = ?, updated = ? where scope = ? and profile = ? and sha256 = ?",
                        (calls, escalations, time.time(), scope, profile, sha256))
        finally:
            con.close()


def _work(er, lines: list, issues: list, variant: str, sha256: str, chunk: int) -> list[dict]:
    selected = er.boq_rows_to_verify([dict(l, _accepted=True) for l in lines], [], variant=variant, sha256=sha256)
    accepted_selected = [r for r, _ in selected]
    held_issues = [i for i in issues if str(i.get("target") or "").startswith("boq_line:")]
    work = [{"lines": [dict(l) for l in accepted_selected[i:i + chunk]], "issues": []} for i in range(0, len(accepted_selected), chunk)]
    work += [{"lines": [], "issues": held_issues[i:i + chunk]} for i in range(0, len(held_issues), chunk)]
    return work


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
    """The corrected loop: one budget for the document across chunks, persisted allowance, no stop cleared."""
    state = allowance.load(scope, profile, sha256)
    budget = open_budget(db, None)
    budget.calls = state["calls"]                      # consumed allowance carries over (resume / new process / new chunks)
    budget.escalations = state["escalations"]
    budget.started = time.monotonic() - (time.time() - state["first_started"])   # elapsed basis from the first start
    run.budget = budget
    results = []
    chunk = max(1, max_calls_per_document - 1)
    for part in _work(er, lines, issues, variant, sha256, chunk):
        # the same budget object for every chunk; run.exhausted is never cleared here
        results += er.verify_boq_rows(run, pdf, sha256=sha256, extraction={"lines": part["lines"], "issues": part["issues"], "geometry_lines": lines},
                                      render_dpi=render_dpi, preselected=True)
        db.commit()
        allowance.save(scope, profile, sha256, budget.calls, budget.escalations)
    return results, {"resumed": state["resumed"], "calls_before": state["calls"], "calls_after": budget.calls, "exhausted": run.exhausted,
                     "harness": HARNESS_VERSION}
