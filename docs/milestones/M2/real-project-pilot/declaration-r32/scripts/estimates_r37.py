"""ORCH-07 (R37DECL-IMPL): request and token estimates for the declaration and the budget card (no model call).

Inputs (read-only): the frozen run set (RUN-SET-PROPOSAL.json 9058f3d6..., 24 documents with project, reason and
in_scope_pages) and the AI ledger (opened mode=ro, uri=True) for the per-request token averages actually recorded by the
four-arm-final evidence scopes (usage values only, never arm outputs). File names are never read or used.

Model (stated, not measured; every figure is an estimate):
  * C (and R's own requests) -- the evidence reader reads at most MAX_PAGES_PER_DOCUMENT = 4 pages and makes at most
    MAX_CALLS_PER_DOCUMENT = 8 calls per document (candidate app/ai/evidence_reader.py). Planning: 2 requests per page
    read (one discovery, one value read), capped at 8 per document. Low: plan v2's rate (135 per 30 documents = 4.5 per
    document). Structural maximum: 8 per document.
  * B -- the accepted path makes AI requests only where the baseline reads a submittal form (read_submittal_form).
    Planning: plan v2's 6. Per-project day-limit check: at most one form read per decision-bearing document (16 in all).
  * R -- served C's capture by content key; only requests C never made are dispatched (reference-only). Planning: plan
    v2's 10, split by C's planning share; maximum the R cap 40.
  * P -- a seeded 15 % of C's answered dispatches, re-sent once. Planning 15 % of C planning; maximum 15 % of C maximum
    (cap 36).
  * Tokens -- planning: requests x the per-request ledger average of the four-arm-final scopes (L1-L4 for the evidence
    lanes, A for B); conservative: requests x the ledger's own calibrated p95 of its largest task (discover_page 45,544 /
    10,870; read_submittal_form 25,057 / 3,881 for B)."""
from __future__ import annotations

import collections
import json
import math
import sqlite3

import r37common as C

CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
MAX_PAGES_PER_DOCUMENT = 4
MAX_CALLS_PER_DOCUMENT = 8
PLAN_V2_EXPECTED = {"B": 6, "C": 135, "R": 10, "P": 20, "documents": 30}
PROBE_RATE = 0.15
P95 = {"evidence": (45_544, 10_870), "B": (25_057, 3_881)}     # candidate app/ai/ledger.py CALIBRATION_P95
FOUR_ARM_EVIDENCE_SCOPES = tuple(f"m2-four-arm-final-2026-10-01-{x}" for x in ("L1", "L2", "L3", "L4"))
FOUR_ARM_BASE_SCOPE = "m2-four-arm-final-2026-10-01-A"
PROJECT_ORDER = ("EP-27331", "EP-26687", "EP-22349", "EP-3563", "EP-29255", "EP-15744")


def run_set_documents(run_set: dict) -> list:
    return [{"pool_id": d["pool_id"], "project": d["project"], "reason": d["reason"], "in_scope_pages": int(d["in_scope_pages"]),
             "decision_bearing": d["reason"] == "decision_bearing"} for d in run_set["documents"]]


def c_planning(doc) -> int:
    return min(MAX_CALLS_PER_DOCUMENT, 2 * min(MAX_PAGES_PER_DOCUMENT, doc["in_scope_pages"]))


def ledger_averages(path=C.AI_LEDGER) -> dict:
    """Per-request (input, output) averages of the four-arm-final scopes: the ledger's own accounting (actual usage, or the
    reservation where usage was unknown), over every dispatched entry (refused and cache-hit entries excluded)."""
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        def avg(scopes):
            q = ("select count(*), sum(coalesce(act_in, est_in)), sum(coalesce(act_out, est_out)) from entries where scope in (%s) "
                 "and coalesce(state, '') not in ('refused', 'cache_hit')" % ",".join("?" * len(scopes)))
            n, i, o = con.execute(q, scopes).fetchone()
            return {"requests": n, "input_total": i, "output_total": o, "input_per_request": round(i / n, 1), "output_per_request": round(o / n, 1)}
        return {"evidence_lanes": avg(FOUR_ARM_EVIDENCE_SCOPES) | {"scopes": list(FOUR_ARM_EVIDENCE_SCOPES)},
                "B": avg((FOUR_ARM_BASE_SCOPE,)) | {"scopes": [FOUR_ARM_BASE_SCOPE]}}
    finally:
        con.close()


def estimate(run_set: dict, averages: dict) -> dict:
    docs = run_set_documents(run_set)
    n = len(docs)
    by_project = collections.OrderedDict((p, [d for d in docs if d["project"] == p]) for p in PROJECT_ORDER)
    assert sum(len(v) for v in by_project.values()) == n, "every run-set document belongs to one of the six projects"
    c_plan = sum(c_planning(d) for d in docs)
    c_low = math.ceil(PLAN_V2_EXPECTED["C"] / PLAN_V2_EXPECTED["documents"] * n)
    lanes = {
        "B": {"planning": PLAN_V2_EXPECTED["B"], "conservative": sum(d["decision_bearing"] for d in docs), "cap": CAPS["B"],
              "basis": "plan v2 expected 6 (four-arm A base: 4 read_submittal_form requests over 26 PDFs); conservative: one form read per decision-bearing document"},
        "C": {"low": c_low, "planning": c_plan, "conservative": MAX_CALLS_PER_DOCUMENT * n, "cap": CAPS["C"],
              "basis": "planning: 2 requests per page read (pages read = min(4, in-scope pages)), at most 8 per document; low: plan v2 rate 4.5 per document; conservative: 8 per document (MAX_CALLS_PER_DOCUMENT)"},
        "R": {"planning": PLAN_V2_EXPECTED["R"], "conservative": CAPS["R"], "cap": CAPS["R"],
              "basis": "served C's capture by content key; reference-only requests only; plan v2 expected 10; conservative: the R cap"},
        "P": {"planning": round(PROBE_RATE * c_plan), "conservative": min(CAPS["P"], math.ceil(PROBE_RATE * MAX_CALLS_PER_DOCUMENT * n)), "cap": CAPS["P"],
              "basis": "seeded 15 % of C's answered dispatches, re-sent once"},
    }
    for k in ("planning", "conservative"):
        lanes.setdefault("total", {})[k] = sum(lanes[x][k] for x in ("B", "C", "R", "P"))
    lanes["total"]["cap"] = sum(CAPS.values())
    ev, bb = averages["evidence_lanes"], averages["B"]
    per_req = {"B": (bb["input_per_request"], bb["output_per_request"])} | {x: (ev["input_per_request"], ev["output_per_request"]) for x in ("C", "R", "P")}
    tokens = {}
    for x in ("B", "C", "R", "P"):
        p95 = P95["B"] if x == "B" else P95["evidence"]
        tokens[x] = {"planning_input": round(lanes[x]["planning"] * per_req[x][0]), "planning_output": round(lanes[x]["planning"] * per_req[x][1]),
                     "conservative_input": lanes[x]["conservative"] * p95[0], "conservative_output": lanes[x]["conservative"] * p95[1]}
    tokens["total"] = {k: sum(tokens[x][k] for x in ("B", "C", "R", "P")) for k in tokens["B"]}
    projects = collections.OrderedDict()
    for p, ds in by_project.items():
        cp = sum(c_planning(d) for d in ds)
        cmax = MAX_CALLS_PER_DOCUMENT * len(ds)
        bcons = sum(d["decision_bearing"] for d in ds)
        r_plan = round(PLAN_V2_EXPECTED["R"] * cp / c_plan, 1)
        p_plan = round(PROBE_RATE * cp, 1)
        projects[p] = {"documents": len(ds), "pool_ids": [d["pool_id"] for d in ds], "in_scope_pages": sum(d["in_scope_pages"] for d in ds),
                       "pages_read_by_c": sum(min(MAX_PAGES_PER_DOCUMENT, d["in_scope_pages"]) for d in ds), "decision_bearing": bcons,
                       "B_conservative": bcons, "C_low": round(4.5 * len(ds), 1), "C_planning": cp, "C_max": cmax,
                       "R_planning": r_plan, "R_max": min(CAPS["R"], cmax), "P_planning": p_plan, "P_max": round(PROBE_RATE * cmax, 1),
                       "B_plus_C_planning": bcons + cp, "B_plus_C_max": bcons + cmax,
                       "all_lanes_planning": round(bcons + cp + r_plan + p_plan, 1),
                       "all_lanes_conservative": round(bcons + cmax + min(CAPS["R"], cmax) + PROBE_RATE * cmax, 1)}
    return {"documents": n, "lanes": lanes, "tokens": tokens, "per_request_basis": averages, "projects": projects,
            "model": __doc__.split("Model (stated, not measured; every figure is an estimate):")[1].strip()}


def day_limit_assessment(est: dict, limit: int) -> dict:
    """Which projects can reach the project-day limit within one UTC day (all lanes counted; B then C then R then P)."""
    out = {}
    for p, v in est["projects"].items():
        out[p] = {"limit": limit, "B_plus_C_planning": v["B_plus_C_planning"], "B_plus_C_max": v["B_plus_C_max"],
                  "all_lanes_planning": v["all_lanes_planning"], "all_lanes_conservative": v["all_lanes_conservative"],
                  "b_or_c_refusal_possible_at_planning": v["B_plus_C_planning"] > limit,
                  "b_or_c_refusal_possible_at_maximum": v["B_plus_C_max"] > limit,
                  "r_or_p_refusal_possible_at_planning": v["all_lanes_planning"] > limit,
                  "r_or_p_refusal_possible_at_conservative": v["all_lanes_conservative"] > limit}
    return out


def load_run_set() -> dict:
    raw = C.RUN_SET.read_bytes()
    if C.sha256_bytes(raw) != C.FROZEN["run_set_proposal"][1]:
        raise C.PacketMismatch("PACKET MISMATCH: RUN-SET-PROPOSAL.json")
    return json.loads(raw.decode("utf-8"))


if __name__ == "__main__":
    e = estimate(load_run_set(), ledger_averages())
    print(json.dumps({"lanes": e["lanes"], "tokens": e["tokens"], "projects": {k: {x: v[x] for x in v if x != "pool_ids"} for k, v in e["projects"].items()},
                      "day_limit_60": day_limit_assessment(e, 60)}, indent=1))
