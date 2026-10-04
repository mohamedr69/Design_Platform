"""ORCH-05.1 (Review 33 C-5, R33-07): the run-set selector of plan v2 section 2.3, from truth presence in the frozen
r32-labels-reviewed-2 only (never a prediction or a candidate output). A PROPOSAL: the run set is frozen only by the
ORCH-07 declaration.

Seeded order: ascending sha256("<seed>|EP-<ep>|<relative path>") with seed m2-r30-runset-2026-10-02 -- the construction of
FROZEN-SELECTION's pool order (metadata used as a sort KEY, never as evidence). Canonical ids only: the count-once aliases
(F031, F052, F059, F070) are never drawn.
  1. decision-bearing: every canonical document whose decision is resolved_for_scoring yes AND carries_fact yes; all of
     them when there are 16 or fewer, else the first 16 in the seeded order;
  2. top-up, at most 8: canonical documents without a decision fact that carry identity or revision (resolved yes,
     carries yes), in the seeded order; a document is added only while it carries a field whose run-set count is below
     16; stop when identity and revision both reach 16 or 8 were added;
  3. negative controls, 4: canonical, not yet drawn, decision resolved_for_scoring yes and EVERY in-scope decision row a
     scorable ABSENT (blank_decision_area or no_decision_area) -- the adapter's decision_control 'negative';
  4. unsupported controls, 2: canonical, not yet drawn, at least one in-scope page with a field labelled 'unsupported'
     or 'illegible';
  5. at most 30 documents. When the pool cannot supply a step's number, the shortfall is recorded; nothing is invented.
ORCH-08 (A-09 point 5): the selection rule is unchanged; replace_controls() is the only way to add unsupported-format
controls and it REFUSES once a prediction exists for the run (prediction_evidence: an invocation in RUN-STATE.json, a
request row in the capture store, or lane rows) -- the shortfall then stays a declared scope limitation.
Pure apart from build_proposal's inputs and prediction_evidence's read-only look at a run folder; writes nothing
(write_proposal is called by the dry run)."""
from __future__ import annotations

import collections
import hashlib
import json

import labels_adapter_r32 as A

SEED = "m2-r30-runset-2026-10-02"
RULE = {"decision_bearing_max": 16, "top_up_max": 8, "top_up_target_per_field": 16, "negative_controls": 4,
        "unsupported_controls": 2, "max_documents": 30, "seed": SEED, "version": "run-set-r32-2026-10-03.1"}


def order_key(doc: dict, seed: str = SEED) -> str:
    return hashlib.sha256(f"{seed}|EP-{doc['ep']}|{doc['relative_path']}".encode("utf-8")).hexdigest()


def _canonical(truth):
    return [d for d in truth["documents"].values() if not d["is_alias"]]


def unsupported_pages(truth, pid) -> list[str]:
    doc = truth["documents"][pid]
    return sorted({r["page"] for r in A.doc_rows(truth, pid) if r["state"] in ("unsupported", "illegible")
                   and int(r["page"]) <= doc["in_scope_pages"]}, key=int)


def select(truth: dict, rule: dict = RULE) -> dict:
    canon = sorted(_canonical(truth), key=lambda d: order_key(d, rule["seed"]))
    picked, reasons = [], {}

    def take(doc, reason):
        picked.append(doc["pool_id"])
        reasons[doc["pool_id"]] = reason

    dec = [d for d in canon if A.has_fact(truth, d["pool_id"], "decision")]
    for d in dec[:rule["decision_bearing_max"]]:
        take(d, "decision_bearing")
    counts = collections.Counter({f: sum(1 for p in picked if A.has_fact(truth, p, f)) for f in ("identity", "revision")})
    added = 0
    topup_candidates = [d for d in canon if d["pool_id"] not in picked and not A.has_fact(truth, d["pool_id"], "decision")
                        and (A.has_fact(truth, d["pool_id"], "identity") or A.has_fact(truth, d["pool_id"], "revision"))]
    for d in topup_candidates:
        if added >= rule["top_up_max"] or all(counts[f] >= rule["top_up_target_per_field"] for f in ("identity", "revision")):
            break
        helps = [f for f in ("identity", "revision") if A.has_fact(truth, d["pool_id"], f) and counts[f] < rule["top_up_target_per_field"]]
        if not helps:
            continue
        take(d, "top_up:" + "+".join(helps))
        added += 1
        for f in ("identity", "revision"):
            if A.has_fact(truth, d["pool_id"], f):
                counts[f] += 1
    neg_candidates = [d for d in canon if d["pool_id"] not in picked and d["decision_control"] == "negative"]
    for d in neg_candidates[:rule["negative_controls"]]:
        take(d, "negative_control")
    uns_candidates = [d for d in canon if d["pool_id"] not in picked and unsupported_pages(truth, d["pool_id"])]
    for d in uns_candidates[:rule["unsupported_controls"]]:
        take(d, "unsupported_control")
    over = picked[rule["max_documents"]:]
    picked = picked[:rule["max_documents"]]
    shortfalls = {}
    n_neg = sum(1 for p in picked if reasons[p] == "negative_control")
    n_uns = sum(1 for p in picked if reasons[p] == "unsupported_control")
    if n_neg < rule["negative_controls"]:
        shortfalls["negative_controls"] = {"required": rule["negative_controls"], "found": n_neg}
    if n_uns < rule["unsupported_controls"]:
        shortfalls["unsupported_controls"] = {"required": rule["unsupported_controls"], "found": n_uns,
                                              "why": "no canonical pool document has an in-scope page labelled 'unsupported' or 'illegible' in r32-labels-reviewed-2; no document is invented and no file outside the pool is drawn"}
    proj = {f: sum(1 for p in picked if A.has_fact(truth, p, f)) for f in A.FIELDS}
    short_fields = {f: rule["top_up_target_per_field"] - n for f, n in proj.items() if f != "decision" and n < rule["top_up_target_per_field"]}
    if short_fields:
        shortfalls["top_up_target"] = {"target": rule["top_up_target_per_field"], "reached": proj, "short": short_fields}
    return {"picked": picked, "reasons": reasons, "dropped_over_cap": over, "shortfalls": shortfalls,
            "candidates": {"decision_bearing": len(dec), "top_up": len(topup_candidates), "negative_control": len(neg_candidates),
                           "unsupported_control": len(uns_candidates)}}


def build_proposal(truth: dict, *, inputs: dict, rule: dict = RULE) -> dict:
    sel = select(truth, rule)
    docs = []
    for pid in sel["picked"]:
        d = truth["documents"][pid]
        docs.append({"pool_id": pid, "canonical_id": d["canonical_id"], "doc_key": d["doc_key"], "ep": d["ep"], "project": d["project"],
                     "contractor": d["contractor"], "stratum": d["stratum"], "layout_key": d["layout_key"], "decision_type": d["decision_type"],
                     "decision_control": d["decision_control"], "reason": sel["reasons"][pid], "order_key": order_key(d, rule["seed"]),
                     "staged_sha256": d["staged_sha256"], "in_scope_pages": d["in_scope_pages"],
                     "fields_carried": [f for f in A.FIELDS if A.has_fact(truth, pid, f)],
                     "fields_resolved": [f for f in A.FIELDS if A.primary(truth, pid, f)],
                     "unsupported_pages": unsupported_pages(truth, pid)})
    proj = {f: {"documents": sum(1 for x in docs if f in x["fields_carried"]),
                "by_project": dict(sorted(collections.Counter(x["project"] for x in docs if f in x["fields_carried"]).items())),
                "by_layout_key": dict(sorted(collections.Counter(x["layout_key"] for x in docs if f in x["fields_carried"]).items())),
                "margin_over_minimum_12": sum(1 for x in docs if f in x["fields_carried"]) - 12} for f in A.FIELDS}
    for x in docs:
        x["per_field_matched_projection"] = {f: (f in x["fields_carried"]) for f in A.FIELDS}
    return {"name": "RUN-SET-PROPOSAL (r32)", "status": "PROPOSAL: frozen only by the ORCH-07 declaration; no dispatch, no prediction",
            "rule": rule, "inputs": inputs, "documents": docs, "count": len(docs),
            "by_reason": dict(collections.Counter(x["reason"].split(":")[0] for x in docs)),
            "per_field_matched_projection": proj,
            "projection_note": "documents in the run set that carry the field (resolved, independently reviewed, canonical); the realised matched population also needs B and C to attempt each document",
            "decision_controls_in_run_set": dict(collections.Counter(x["decision_control"] for x in docs)),
            "shortfalls": sel["shortfalls"], "candidates": sel["candidates"], "dropped_over_cap": sel["dropped_over_cap"],
            "aliases_excluded": sorted(truth["aliases"]),
            "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed"}


# ---- ORCH-08 (A-09 point 5): no replacement once a prediction exists ------------------------------------------------------
class ReplacementRefused(RuntimeError):
    pass


def prediction_evidence(run_folder) -> list[str]:
    """What shows that a prediction exists for the run: an invocation in RUN-STATE.json, a request row in the capture
    store, or any lane rows / normalised lane file in an invocation folder. [] when none (the run never started)."""
    import pathlib
    import sqlite3

    rf = pathlib.Path(run_folder)
    ev = []
    st = rf / "RUN-STATE.json"
    if st.is_file() and json.loads(st.read_text(encoding="utf-8")).get("invocations"):
        ev.append(f"{st.as_posix()} records an invocation")
    cs = rf / "capture.sqlite"
    if cs.is_file():
        con = sqlite3.connect(f"file:{cs.as_posix()}?mode=ro", uri=True)
        try:
            n = con.execute("select count(*) from requests").fetchone()[0] if con.execute(
                "select count(*) from sqlite_master where name = 'requests'").fetchone()[0] else 0
        finally:
            con.close()
        if n:
            ev.append(f"{cs.as_posix()} holds {n} request row(s)")
    ev += [p.as_posix() for pat in ("inv-*/out/rows-*.json", "inv-*/out/lane-*.r32.json", "inv-*/out/LANE-*.json") for p in sorted(rf.glob(pat))]
    return ev


def replace_controls(truth: dict, proposal: dict, replacements: list[str], *, run_folder, rule: dict = RULE) -> dict:
    """The ONLY way to add unsupported-format controls to a frozen proposal. Refused once a prediction exists for the run
    (A-09 point 5: the shortfall stays a declared scope limitation); before that, each replacement must satisfy the
    executable definition (canonical, not drawn, an in-scope page labelled unsupported or illegible)."""
    ev = prediction_evidence(run_folder)
    if ev:
        raise ReplacementRefused("refused: a prediction exists for this run (" + "; ".join(ev[:3]) + "); no control is replaced -- "
                                 "the unsupported-control shortfall stays a declared scope limitation (A-09 point 5)")
    drawn = {d["pool_id"] for d in proposal["documents"]}
    for pid in replacements:
        d = truth["documents"].get(pid)
        if d is None or d["is_alias"] or pid in drawn or not unsupported_pages(truth, pid):
            raise ReplacementRefused(f"refused: {pid} is not an eligible unsupported control (canonical, not drawn, an in-scope page labelled unsupported or illegible)")
    if len(drawn) + len(replacements) > rule["max_documents"]:
        raise ReplacementRefused("refused: more than 30 documents")
    return {"replacements": list(replacements), "status": "a new proposal is needed: the run set is frozen only by a declaration"}


def write_proposal(proposal: dict, path) -> str:
    text = json.dumps(proposal, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
