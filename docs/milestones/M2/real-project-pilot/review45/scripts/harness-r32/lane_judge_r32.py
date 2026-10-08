"""ORCH-05.1 (Review 33 C-5, R33-05/R33-06): judge one lane's emitted facts against the r32 truth, per (pool id, page, field).

Normalised r32 lane (written by score_lane_r32.py from a lane's rows, or built synthetically in tests):
  {"lane": "B"|"C"|"R", "requests": {"own_dispatched": n, "inherited_from_b": n, ...}, "tokens": {...},
   "documents": {pool_id: {"attempted": bool, "unsupported": bool,
                           "facts": [{"page": "1", "field": "identity|revision|decision", "value": str, "state": s}],
                           "coverage": {"<page>": {"decision": class, ...}}}}}
  fact states: accepted | validated (automatic acceptances), observed (asserted raw evidence), held (not asserted)
  -- the states of evaluator .10 (ASSERTED = accepted, observed, validated; ACCEPTANCE = accepted, validated).

Per row (judge_row) the outcome follows the truth kind of the adapter (labels_adapter_r32):
  value         recovered_clean | recovered_mixed | wrong_only | held_only | missed   (+ precision over distinct values)
  ABSENT        tn | fp            an asserted identity on a page whose identity is ABSENT that equals the document's
                                   resolved identity on ANOTHER page is a cross-page copy (never fp; evaluator .10 rule)
  cross-page identity (ORCH-08, A-09 point 4): an asserted identity that differs from the page's own value (or is
                                   asserted on an ABSENT identity page) is a cross-page association -- never wrong, never
                                   correct for this page, never credit for another page -- ONLY when page_relations_r38
                                   (rule CP-R38) finds it evidenced: the lane document's source sha256 is the staged
                                   sha256, the document's identity is resolved, the value equals a resolved identity of
                                   another page, and the reviewed labels record the pages' relationship (R1 listed on the
                                   page, R2 listed enclosure of that package, R3 same identity on both pages); otherwise it
                                   is judged as asserted (wrong / fp; critical when automatically accepted). Never on a
                                   compilation ((h)). A page whose asserted identities include a permitted cross-page value
                                   besides its correct own value is 'recovered_conflict' (no recovery credit)
  decision values 'UR', 'n/a', 'none', 'absent' or empty assert no decision: never a fact, never wrong
  NOT_SCORABLE  not_scorable       never in precision, recovery, coverage or y; each automatic acceptance on it is
                                   reported: matching the row's literal or a candidate -> 'not_scorable_matching'
                                   (reported only), differing from every literal and candidate -> a critical on
                                   UNRESOLVED truth (reported, never a stop), no literal or candidate -> 'not_scorable_unjudgeable'
A critical acceptance is an AUTOMATIC acceptance (accepted / validated) that is wrong or a false positive on a scorable
row: critical on RESOLVED truth, attributed to its pool id, page and field (the per-field tripwire). Pure."""
from __future__ import annotations

import collections

import labels_adapter_r32 as A
import literal_compare_r32 as LC
import page_relations_r38 as REL

FIELDS = A.FIELDS
ASSERTED = ("accepted", "observed", "validated")
ACCEPTANCE = ("accepted", "validated")


def _facts(ldoc, page, field):
    return [f for f in (ldoc or {}).get("facts") or [] if str(f.get("page")) == str(page) and f.get("field") == field
            and f.get("value") not in (None, "")]


def judge_row(truth, rec, ldoc) -> dict:
    field, page, pid = rec["field"], rec["page"], rec["pool_id"]
    facts = _facts(ldoc, page, field)
    if field == "decision":
        facts = [f for f in facts if LC.asserts_decision(f["value"])]
    kind = rec["truth_kind"]
    out = {"pool_id": pid, "page": page, "field": field, "truth_kind": kind, "facts": len(facts), "critical": [],
           "unresolved": [], "accepted_correct": 0, "accepted_wrong": 0, "cross_page": 0}
    if kind == "not_scorable":
        out["outcome"] = "not_scorable"
        for f in facts:
            if f.get("state") not in ACCEPTANCE:
                continue
            refs = [x for x in [rec.get("literal"), *(rec.get("candidates") or [])] if x not in (None, "")]
            if not refs:
                out["unresolved"].append({"pool_id": pid, "page": page, "field": field, "value": f["value"], "kind": "not_scorable_unjudgeable"})
                continue
            matches = [r for r in refs if LC.compare(r, f["value"], field, alternates=rec.get("alternates") or (),
                                                    truth_class=rec.get("class"), resubmission_required=rec.get("resubmission_required"))["match"]]
            item = {"pool_id": pid, "page": page, "field": field, "value": f["value"],
                    "kind": "not_scorable_matching" if matches else "critical_on_unresolved_truth", "references": refs}
            out["unresolved"].append(item)
        return out
    if kind == "absent":
        asserted = []
        for f in facts:
            if f.get("state") not in ASSERTED:
                continue
            if field == "identity":
                cp = REL.cross_page(truth, pid, page, f["value"], ldoc)
                out.setdefault("cross_page_checks", []).append({"value": f["value"], **cp})
                if cp["permitted"]:
                    out["cross_page"] += 1                 # an EVIDENCED association with another page's identity (CP-R38)
                    continue
            asserted.append(f)
        out["outcome"] = "fp" if asserted else "tn"
        distinct = {LC.norm_text(f["value"]).upper() for f in asserted if f.get("state") in ACCEPTANCE}
        out["accepted_wrong"] = len(distinct)
        for f in asserted:
            if f.get("state") in ACCEPTANCE:
                out["critical"].append({"pool_id": pid, "page": page, "field": field, "value": f["value"], "outcome": "fp", "truth": None})
        return out
    # a value
    judged = [(f, LC.compare_row(rec, f["value"])) for f in facts]
    if field == "identity":
        kept = []
        for f, c in judged:
            if not c["match"] and f.get("state") in ASSERTED:
                cp = REL.cross_page(truth, pid, page, f["value"], ldoc)
                out.setdefault("cross_page_checks", []).append({"value": f["value"], **cp})
                if cp["permitted"]:
                    out["cross_page"] += 1         # an EVIDENCED association with another page's identity (CP-R38)
                    continue
            kept.append((f, c))
        judged = kept
    asserted = [(f, c) for f, c in judged if f.get("state") in ASSERTED]
    correct = any(c["match"] for _, c in asserted)
    wrong = any(not c["match"] for _, c in asserted)
    held_correct = any(c["match"] for f, c in judged if f.get("state") == "held")
    out["outcome"] = ("recovered_mixed" if wrong else "recovered_conflict" if out["cross_page"] else "recovered_clean") if correct else \
        "wrong_only" if wrong else "held_only" if held_correct else "missed"
    acc = {}
    for f, c in asserted:
        if f.get("state") in ACCEPTANCE:
            acc.setdefault(c.get("predicted_norm") or LC.norm_text(f["value"]), (f, c))
    out["accepted_correct"] = sum(1 for _, c in acc.values() if c["match"])
    out["accepted_wrong"] = sum(1 for _, c in acc.values() if not c["match"])
    out["match_kinds"] = sorted({c["kind"] for _, c in asserted if c["match"]})
    for f, c in acc.values():
        if not c["match"]:
            out["critical"].append({"pool_id": pid, "page": page, "field": field, "value": f["value"], "outcome": "wrong",
                                    "truth": rec.get("literal") if field != "decision" else rec.get("class")})
    return out


def judge_document(truth, pool_id, ldoc) -> dict:
    """Every labelled row of the document, plus facts on pages without a row (unscored)."""
    rows = sorted(A.doc_rows(truth, pool_id), key=lambda r: (int(r["page"]), FIELDS.index(r["field"])))
    judged = [judge_row(truth, r, ldoc) for r in rows]
    labelled = {(r["page"], r["field"]) for r in rows}
    unscored = [f for f in (ldoc or {}).get("facts") or [] if (str(f.get("page")), f.get("field")) not in labelled]
    by_field = {}
    for f in FIELDS:
        jr = [j for j in judged if j["field"] == f]
        rec = collections.Counter(j["outcome"] for j in jr if j["truth_kind"] == "value")
        neg = collections.Counter(j["outcome"] for j in jr if j["truth_kind"] == "absent")
        by_field[f] = {"recovery": dict(rec), "negatives": dict(neg),
                       "accepted": {"correct": sum(j["accepted_correct"] for j in jr), "wrong": sum(j["accepted_wrong"] for j in jr)},
                       "critical": [c for j in jr for c in j["critical"]],
                       "unresolved": [u for j in jr for u in j["unresolved"]],
                       "not_scorable_rows": sum(1 for j in jr if j["truth_kind"] == "not_scorable"),
                       "y": int(rec.get("recovered_clean", 0) > 0 and not rec.get("recovered_mixed") and not rec.get("wrong_only")
                                and not rec.get("recovered_conflict"))}
    return {"pool_id": pool_id, "rows": judged, "fields": by_field, "unscored_facts": len(unscored)}


def critical_split(judged_doc) -> dict:
    """Per-field tripwire classification of one judged document: resolved criticals (stop) and unresolved (report)."""
    out = {"resolved": [], "unresolved": []}
    for f, v in judged_doc["fields"].items():
        out["resolved"] += v["critical"]
        out["unresolved"] += [u for u in v["unresolved"] if u["kind"] == "critical_on_unresolved_truth"]
    return out


def credit_of(lane) -> str:
    """ORCH-08 (A-09 point 6): only B and C are scored; R (reference) and P (probe) are diagnostics that earn no accuracy or
    recovery credit anywhere -- their judged documents carry credit 'none'."""
    return "scored" if (lane or {}).get("lane") in ("B", "C", None) else "none"


def judge_lane(lane, truth) -> dict:
    """{pool_id: judged document} for every document of the lane (aliases included: their own rows are real labels)."""
    credit = credit_of(lane)
    return {pid: judge_document(truth, pid, d) | {"credit": credit} for pid, d in (lane.get("documents") or {}).items() if pid in truth["documents"]}


def y(judged, pid, f) -> int:
    d = judged.get(pid)
    return int(d["fields"][f]["y"]) if d else 0


def attempted(lane, pid) -> bool:
    d = (lane.get("documents") or {}).get(pid) or {}
    return bool(d.get("attempted")) and not d.get("unsupported")


def coverage_counts(lane, truth, f, docs=None) -> dict:
    """Coverage over SCORABLE rows only: completed_read; discovery_absent on ABSENT truth = verified absence, on a value =
    wrong absence (never coverage); located_incomplete and everything else is not coverage; NOT_SCORABLE rows are counted
    apart and never enter coverage."""
    c = collections.Counter({"pages": 0, "completed_read": 0, "verified_absence": 0, "wrong_absence": 0, "not_scorable": 0})
    for r in truth["rows"].values():
        if r["field"] != f or (docs is not None and r["pool_id"] not in docs):
            continue
        if r["truth_kind"] == "not_scorable":
            c["not_scorable"] += 1
            continue
        cov = ((lane.get("documents") or {}).get(r["pool_id"]) or {}).get("coverage") or {}
        cls = (cov.get(str(r["page"])) or {}).get(f, "not_attempted")
        c["pages"] += 1
        if cls == "completed_read":
            c["completed_read"] += 1
        elif cls == "discovery_absent":
            c["verified_absence" if r["truth_kind"] == "absent" else "wrong_absence"] += 1
        else:
            c["other:" + cls] += 1
    c["coverage"] = c["completed_read"] + c["verified_absence"]
    return dict(c)
