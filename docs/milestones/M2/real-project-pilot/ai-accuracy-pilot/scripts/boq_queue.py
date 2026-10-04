"""AI accuracy pilot, BOQ-T: a risk-ordered row queue verified within the SAME per-document allowance as BOQ-S.

QUEUE_VERSION ai-pilot-boq-queue-2026-09-30.1

The order is computed from the deterministic reader's own signals only -- never from labels, expected quantities, row
ids of a control sheet or a model answer -- and is written to disk (declared) before the first request:

  tier 1  held rows        every issue that kept a row (target boq_line:*), in the reader's issue order
  tier 2  risky accepted   accepted lines carrying at least one uncertainty signal of the reader:
                             no_part                  no catalog number
                             quantity_not_from_cell   the quantity came from a "( n )" description count / no cell literal
                             quantity_rewritten       the cell's raw literal differs from the parsed quantity
                             low_quantity_confidence  quantity_confidence missing or < RECHECK_QUANTITY_BELOW (application, 90)
                             low_catalog_confidence   catalog_confidence missing or < CONFIRM_CATALOG_BELOW (application, 90)
                             reader_flag              catalog_uncertain / verify_quantity set by the reader
                           ordered by number of signals (desc), then the lowest confidence (asc), then position
  tier 3  seeded audit     AUDIT_N (2) apparently confident accepted lines, order = sha256(seed | sha256 | page | y)
  tier 4  residual audit   the remaining confident lines in the same seeded order, until the cap

One row per request; the cap is the document's allowance (12). Rows beyond the cap are listed as NOT REACHED.
The allowance, attempt labelling and one-writer lock are the accepted r16.1 harness's (`boq_harness.DocAllowance`,
`DurableBudget`), unchanged: one allowance per (scope, profile, document) across chunks, retries and restarts."""
from __future__ import annotations

import hashlib
import time

QUEUE_VERSION = "ai-pilot-boq-queue-2026-09-30.1"
AUDIT_SEED = "ai-pilot-boq-audit-2026-09-30"
AUDIT_N = 2


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def signals(line: dict, *, recheck_quantity_below: float, confirm_catalog_below: float) -> list[str]:
    s = []
    if not str(line.get("catalog_no") or "").strip():
        s.append("no_part")
    qp = line.get("quantity_parse") or {}
    if qp.get("source") == "description_count" or line.get("raw_quantity") in (None, ""):
        s.append("quantity_not_from_cell")
    raw = str(line.get("raw_quantity") or "").strip()
    if raw and raw != str(line.get("quantity") or "").strip():
        s.append("quantity_rewritten")
    qc = _num(line.get("quantity_confidence"))
    if qc is None or qc < recheck_quantity_below:
        s.append("low_quantity_confidence")
    cc = _num(line.get("catalog_confidence"))
    if str(line.get("catalog_no") or "").strip() and (cc is None or cc < confirm_catalog_below):
        s.append("low_catalog_confidence")
    if line.get("catalog_uncertain") or line.get("verify_quantity"):
        s.append("reader_flag")
    return s


def _audit_rank(sha256: str, line: dict) -> str:
    return hashlib.sha256(f"{AUDIT_SEED}|{sha256}|{int(line.get('page') or 1)}|{line.get('y_px')}".encode()).hexdigest()


def risk_queue(lines: list[dict], issues: list[dict], *, sha256: str, cap: int, recheck_quantity_below: float,
               confirm_catalog_below: float) -> dict:
    """The declared order: [{"kind": "issue"|"line", "index": i, "tier": ..., "signals": [...]}], plus not-reached rows."""
    held = [{"kind": "issue", "index": i, "tier": "1_held", "signals": [str(s.get("reason_code") or s.get("code") or "held")]}
            for i, s in enumerate(issues) if str(s.get("target") or "").startswith("boq_line:")]
    risky, confident = [], []
    for i, l in enumerate(lines):
        sg = signals(l, recheck_quantity_below=recheck_quantity_below, confirm_catalog_below=confirm_catalog_below)
        (risky if sg else confident).append((i, l, sg))

    def lowest(l):
        vals = [v for v in (_num(l.get("quantity_confidence")), _num(l.get("catalog_confidence"))) if v is not None]
        return min(vals) if vals else -1.0

    risky.sort(key=lambda x: (-len(x[2]), lowest(x[1]), int(x[1].get("page") or 1), x[1].get("y_px") or 0))
    confident.sort(key=lambda x: _audit_rank(sha256, x[1]))
    order = held + [{"kind": "line", "index": i, "tier": "2_risk", "signals": sg} for i, _, sg in risky]
    order += [{"kind": "line", "index": i, "tier": "3_audit" if n < AUDIT_N else "4_residual_audit", "signals": []}
              for n, (i, _, _) in enumerate(confident)]
    for n, item in enumerate(order):
        item["position"] = n + 1
    return {"version": QUEUE_VERSION, "cap": cap, "order": order[:cap], "not_reached": order[cap:],
            "thresholds": {"recheck_quantity_below": recheck_quantity_below, "confirm_catalog_below": confirm_catalog_below},
            "audit": {"seed": AUDIT_SEED, "n": AUDIT_N}}


def verify_queue(er, run, pdf, *, db, open_budget, harness, allowance, scope: str, profile: str, lines: list, issues: list, queue: dict,
                 sha256: str, max_calls_per_document: int, render_dpi: int) -> tuple[list[dict], dict]:
    """`boq_harness.verify_sheet` with the declared queue in place of the EV1 selection: same lock, durable budget,
    attempt labelling and per-row commit; each result carries its queue position, tier and signals."""
    key = (scope, profile, sha256)
    lock = allowance.acquire(*key)
    try:
        state = allowance.load(*key)
        attempt, interrupted = allowance.begin_attempt(*key, state["calls"])
        budget = open_budget(db, None)
        budget.calls = state["calls"]
        budget.escalations = state["escalations"]
        budget.started = time.monotonic() - (time.time() - state["first_started"])
        run.budget = harness.DurableBudget(budget, allowance, key, max_calls_per_document)
        results = []
        for item in queue["order"]:
            part = {"lines": [dict(lines[item["index"]])], "issues": []} if item["kind"] == "line" else {"lines": [], "issues": [issues[item["index"]]]}
            n_log = len(run.log)
            got = er.verify_boq_rows(run, pdf, sha256=sha256, extraction={**part, "geometry_lines": lines}, render_dpi=render_dpi, preselected=True)
            assert len(got) == 1, "one queue item is one row"
            new = run.log[n_log:]
            request = new[-1]["outcome"] if new else "no_request"     # 'ok', a provider error, or 'budget: <limit>'
            results.append({**got[0], "request": request, "queue": {k: item[k] for k in ("position", "tier", "signals", "kind", "index")}})
            db.commit()
        after = allowance.load(*key)["calls"]
        allowance.end_attempt(attempt, "completed" if not run.exhausted else f"stopped: {run.exhausted}", after)
        return results, {"resumed": state["resumed"], "calls_before": state["calls"], "calls_after": after, "exhausted": run.exhausted,
                         "attempt": attempt, "interrupted_attempts_found": interrupted, "harness": harness.HARNESS_VERSION, "queue": QUEUE_VERSION}
    finally:
        harness._unlock_file(lock)
