"""M2 pilot evaluator .4 (M2 review 06: R6-01 .. R6-04). Evaluator .3 (`scripts/m2_pilot_eval.py`) stays unchanged as
history; its helpers (literal values, identity, revision tokens, system equivalence, floor keys) are reused as they are.

Field-accounting rules (frozen with `tests/test_m2_eval4.py`):

1. Denominators come from truth alone. Each expected record's field is readable (a clear value), negative (the source
   has no such fact: an absent revision, no consultant decision), conflict (the source contradicts itself), or
   unscorable (unknown / illegible / ambiguous / unlabelled). A document with no execution row, a failed or a partial
   run keeps every readable field in the recovery denominator, and its execution outcome is reported (R6-03).
2. Every emitted record is associated and judged -- none is skipped as a duplicate (R6-01). Association: same page and
   same identity; else, the page has exactly one expected component (association clear even when its identity is
   unknown, R6-03); else the same identity on another page of the document (a cross-page copy). Per expected field the
   accepted values of all its emissions are pooled: any accepted value that differs from the truth makes the field
   `wrong` (and critical, for reference / revision / decision) even beside a correct one; a correct value earns
   recovery once, however many redundant copies carry it. The result is independent of record order.
3. Conflict truth (R6-02): an accepted positive decision where the source contradicts itself is `accepted_on_conflict`
   -- accepted, wrong and critical. A held conflict (flag or disagreeing candidates) is `conflict_held`; a bare UR is
   `conflict_missing`. A sheet whose REV cell and revision history disagree: a business revision projected from the
   printed value without the `revision_conflict` flag is `conflict_resolved_silently` (critical).
4. Decision-absence labels are explicit: `UR`, `n/a`, `absent`, `none`, `no decision`, `not applicable` all mean "the
   source carries no consultant decision" and an accepted decision on them is a false positive. A revision labelled
   `absent` / `n/a` / `not applicable` is a negative that holds even when the whole record is missing (R6-03).
5. A reference the reader flags incomplete / uncertain is still the key the register files the record under, so the
   register layer counts it accepted (evaluator .3 counted it held); the flag is reported as `flagged_reference`.
6. Three layers are kept apart (R6-04): the *register* layer (emitted records, the legacy register shape), the *raw*
   layer (all evidence the reading kept -- records and every observation shape, through `ADAPTERS`, matched by page and
   identity), and the *projection* layer (the business revision the record carries). Raw evidence never makes a
   register record, and a register-ineligible truth record is never counted missing from the register.
7. The *evidence* layer = the raw layer + the AI evidence reader's observations (`extracted["ai_evidence"]`): a
   `validated` reading counts as accepted evidence (and is wrong / critical like any other when it disagrees with the
   truth); `candidate` and `conflict` readings count as held, never as recovered. It is reported apart from the raw
   layer, so what the model added -- and what it got wrong -- is visible (`evidence_introduced_errors`).

Usage: python -m scripts.m2_eval4 --labels L.json [--page-labels P.json] --rows rows.json --out out.json [--corrections]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

from scripts import m2_pilot_eval as v3

EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.4"
CRITICAL_FIELDS = ("reference", "revision", "decision")
UNSCORABLE = {"unknown", "illegible", "ambiguous", "unlabelled", "unlabeled"}
DECISION_NEGATIVE = {"ur", "n/a", "absent", "none", "no decision", "not applicable", "na"}
REVISION_NEGATIVE = {"absent", "n/a", "none", "not applicable", "na"}
REFERENCE_NEGATIVE = {"absent", "n/a", "none", "not applicable"}
POSITIVE = ("approved", "ANN", "rejected")
UNCERTAIN_REFERENCE_FLAGS = ("reference_incomplete", "reference_uncertain")
ACCEPTED_STATES = ("tp", "wrong", "fp", "accepted_on_conflict", "conflict_resolved_silently")


# --- truth states ----------------------------------------------------------------------------------------------------


def _word(value) -> str | None:
    lit = v3.literal(value)
    return None if lit is None else str(lit).strip().lower()


def decision_truth(value) -> tuple[str, str | None]:
    """(state, positive decision). state: readable | negative | conflict | unscorable."""
    word = _word(value)
    if word is None or word in UNSCORABLE:
        return "unscorable", None
    if word == "conflict":
        return "conflict", None
    if word in DECISION_NEGATIVE:
        return "negative", None
    mapped = v3.DECISION_WORDS.get(word)
    if mapped in POSITIVE:
        return "readable", mapped
    return "unscorable", None


def revision_truth(value, reference=None) -> tuple[str, str | None]:
    """(state, normalised printed revision). A reference's own -Rn suffix is its printed revision (as .3)."""
    word = _word(value)
    if reference:
        _, suffix = v3.split_suffix(v3.literal(reference) or "")
        if suffix and (word in (None, "absent") or str(value or "").upper().startswith("R")):
            return "readable", v3.norm_rev(suffix)
    if word is None or word in UNSCORABLE:
        return "unscorable", None
    if word in REVISION_NEGATIVE:
        return "negative", None
    return "readable", v3.norm_rev(value)


def reference_truth(value) -> tuple[str, str | None]:
    word = _word(value)
    if word is None or word in UNSCORABLE:
        return "unscorable", None
    if word in REFERENCE_NEGATIVE:
        return "negative", None
    return "readable", v3.literal(value)


# --- what a record accepted ----------------------------------------------------------------------------------------


def accepted_reference(record: dict) -> tuple[str | None, bool]:
    """(reference, held): a reference the reader flagged incomplete / uncertain is held evidence, not accepted."""
    ref = record.get("reference")
    return ref, bool(set(record.get("flags") or ()) & set(UNCERTAIN_REFERENCE_FLAGS))


def accepted_decision(record: dict) -> str | None:
    status = record.get("status")
    return status if status in POSITIVE else None


def held_decisions(record: dict) -> set:
    return {c[0] for c in record.get("decision_candidates") or () if c}


# --- raw evidence adapters (R6-04) ---------------------------------------------------------------------------------


def _obs_page(obs: dict) -> int:
    return int(obs.get("page") or 1)


def adapt_observation(obs: dict) -> list[dict]:
    """Every actual observation shape as raw facts: [{page, kind, identity, revision, decision, decisions}]."""
    kind = obs.get("kind")
    page = _obs_page(obs)
    out = []
    if kind == "title_block":
        out.append({"page": page, "kind": kind, "identity": obs.get("number"), "revision": obs.get("revision"),
                    "revision_conflict": bool(obs.get("conflict"))})
    elif kind == "transmittal":
        if obs.get("reference") or obs.get("raw_reference"):
            out.append({"page": page, "kind": kind, "identity": obs.get("reference"),
                        "held_identity": obs.get("raw_reference") if not obs.get("reference") else None})
        for rec in obs.get("records") or []:
            out.append({"page": page, "kind": kind, "identity": rec.get("reference")})
    elif kind in ("cover_untracked",):
        rec = obs.get("record") or {}
        out.append({"page": page, "kind": kind, "identity": rec.get("reference"), "revision": v3.raw_revision(rec),
                    "decision": rec.get("status") if rec.get("status") in POSITIVE else None,
                    "decisions": held_decisions(rec)})
    elif kind == "drawing_sheet":
        out.append({"page": page, "kind": kind, "identity": obs.get("reference")})
    elif kind == "decision_unpromoted":
        cands = {c.get("status") if isinstance(c, dict) else c[0] for c in obs.get("candidates") or obs.get("marks") or [] if c}
        out.append({"page": page, "kind": kind, "decisions": {c for c in cands if c}})
    elif kind == "consultant_comments":
        if obs.get("decision") in POSITIVE:
            out.append({"page": page, "kind": kind, "decisions": {obs["decision"]}})
    elif kind in ("form_identity", "evidence", "ai_observation", "own_identity"):
        # Review-06 evidence shapes: a literal own identity / revision / decision with page and region.
        out.append({"page": page, "kind": kind, "identity": obs.get("identity") or obs.get("literal"),
                    "revision": obs.get("revision"), "decisions": {obs["decision"]} if obs.get("decision") in POSITIVE else set()})
    return out


def ai_facts(row: dict | None) -> list[dict]:
    """The AI evidence reader's observations as facts, one component per page (its identity, revision and decision
    read together): validated = accepted evidence, candidate / conflict = held (a held identity links nothing)."""
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    by_page: dict[int, dict] = {}
    for obs in ai.get("observations") or []:
        value, state, page = obs.get("value"), obs.get("state"), _obs_page(obs)
        if not value:
            continue
        fact = by_page.setdefault(page, {"page": page, "kind": "ai_evidence", "identity": None, "held_identity": None,
                                         "revision": None, "decisions": set()})
        accepted = state == "validated"
        if obs.get("field") == "identity":
            fact["identity" if accepted else "held_identity"] = value
        elif obs.get("field") == "revision" and accepted:
            fact["revision"] = value
        elif obs.get("field") == "decision" and accepted and value in POSITIVE:
            fact["decisions"].add(value)
    return list(by_page.values())


def ai_coverage(row: dict | None) -> dict:
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    if not ai:
        return {}
    pages = (ai.get("coverage") or {}).get("pages") or []
    return {"variant": ai.get("variant"), "outcome": (ai.get("coverage") or {}).get("outcome"),
            "pages_read": sum(1 for p in pages if p.get("calls")), "page_outcomes": dict(collections.Counter(str(p.get("outcome")) for p in pages)),
            "calls": sum(1 for c in ai.get("calls") or [] if not c.get("cache_hit") and not str(c.get("outcome", "")).startswith("budget")),
            "cache_hits": sum(1 for c in ai.get("calls") or [] if c.get("cache_hit")),
            "states": dict(collections.Counter(f"{o.get('field')}:{o.get('state')}" for o in ai.get("observations") or []))}


def raw_facts(row: dict | None) -> list[dict]:
    ex = (row or {}).get("extracted") or {}
    facts = []
    for rec in ex.get("records") or []:
        ref, held = accepted_reference(rec)
        facts.append({"page": int(rec.get("page") or 1), "kind": "record", "identity": None if held else ref,
                      "held_identity": ref if held else None, "revision": v3.raw_revision(rec),
                      "decisions": ({rec["status"]} if rec.get("status") in POSITIVE else set()) | held_decisions(rec)})
    for obs in ex.get("observations") or []:
        facts.extend(adapt_observation(obs))
    return facts


# --- expected records ----------------------------------------------------------------------------------------------


def expected_records(doc: dict, plabels: dict | None) -> tuple[list[dict], set, set, bool]:
    """(expected records with ids, no-record pages, unvalidated pages, page-labelled)."""
    lab = doc["labels"]
    if plabels is not None:
        exp = [dict(r, confidence=r.get("confidence", "high")) for r in plabels["records"]]
        no_record = {int(p) for p in (plabels.get("no_record_pages") or {})}
        unvalidated = {int(p) for p in (plabels.get("unvalidated_pages") or [])}
        labelled = True
    else:
        state, _ = reference_truth(lab.get("reference"))
        scope = v3.in_scope(v3.literal(lab.get("kind")) or lab.get("kind"))
        exp = [] if state == "negative" else [{
            "page": 1, "component": "page1", "reference": lab.get("reference"), "printed_revision": lab.get("revision"),
            "decision": lab.get("decision"), "system": lab.get("system"), "floor": lab.get("floor"), "title": lab.get("title"),
            "register": bool(lab.get("register", scope)), "confidence": doc.get("confidence"),
            "revision_conflict": bool(lab.get("revision_conflict"))}]
        no_record = {1} if state == "negative" else set()
        unvalidated = set()
        labelled = False
    for i, e in enumerate(exp):
        e["_id"] = i
    return exp, no_record, unvalidated, labelled


# --- association -----------------------------------------------------------------------------------------------------


def associate(rec: dict, exp_by_page: dict, exp_all: list[dict]) -> tuple[dict | None, str]:
    """(expected record, how): same_page | single_component | cross_page | substituted | unassociated | none."""
    page = int(rec.get("page") or 1)
    here = exp_by_page.get(page, [])
    ref = rec.get("reference")
    for strength in ("exact", "suffix", "near"):
        for e in here:
            if reference_truth(e.get("reference"))[0] == "readable" and v3.same_identity(v3.literal(e["reference"]), ref) == strength:
                return e, "same_page"
    if len(here) == 1:
        e = here[0]
        # one component on the page: association is clear. A known different identity is a substitution (wrong
        # reference); an unknown identity leaves the reference unscorable but the other fields scorable.
        return e, "single_component" if reference_truth(e.get("reference"))[0] != "readable" else "substituted"
    for e in exp_all:
        if e["page"] != page and reference_truth(e.get("reference"))[0] == "readable" and \
                v3.same_identity(v3.literal(e["reference"]), ref) in ("exact", "suffix"):
            return e, "cross_page"
    if len(here) > 1:
        return None, "unassociated"
    return None, "none"


# --- field outcomes --------------------------------------------------------------------------------------------------


def pool(truth_state: str, truth_value, accepted: list, held: list, same) -> str:
    """One expected field over all its emissions. accepted / held: values; same(a, b) compares."""
    if truth_state == "unscorable":
        return "unscorable"
    if truth_state == "negative":
        return "fp" if accepted else "tn"
    if any(not same(truth_value, a) for a in accepted):
        return "wrong"
    if accepted:
        return "tp"
    if any(same(truth_value, h) for h in held):
        return "held"
    return "missed"


def judge_fields(e: dict, emissions: list[dict], executed: bool) -> dict:
    out = {}
    # reference
    rstate, rval = reference_truth(e.get("reference"))
    # Register layer: the register files a record under its reference whatever flags it carries (nothing withholds a
    # flagged record), so a reference flagged incomplete / uncertain is accepted here; the flag is raw evidence and is
    # counted apart (`flagged_reference`). Evaluator .3 counted it held.
    acc = [r.get("reference") for r in emissions if r.get("reference")]
    same_ref = lambda t, a: v3.same_identity(t, a) in ("exact", "suffix")
    out["reference"] = pool(rstate, rval, acc, [], same_ref)
    if any(accepted_reference(r)[1] for r in emissions):
        out["flagged_reference"] = "tp" if out["reference"] == "tp" else "wrong" if out["reference"] == "wrong" else out["reference"]
    # printed (raw) revision
    vstate, vval = revision_truth(e.get("printed_revision"), e.get("reference"))
    racc = [v3.norm_rev(x) for x in (v3.raw_revision(r) for r in emissions) if x]
    out["revision"] = pool(vstate, vval, racc, [], lambda t, a: t == a)
    # decision
    dstate, dval = decision_truth(e.get("decision"))
    dacc = [d for d in (accepted_decision(r) for r in emissions) if d]
    dheld = [d for r in emissions for d in held_decisions(r)]
    if dstate == "conflict":
        evidence = any("decision_conflict" in (r.get("flags") or ()) for r in emissions) or len(set(dheld)) > 1
        out["decision"] = "accepted_on_conflict" if dacc else "conflict_held" if evidence else "conflict_missing"
    else:
        out["decision"] = pool(dstate, dval, dacc, dheld, lambda t, a: t == a)
    # revision conflict: the business revision projected from a self-contradicting sheet
    if e.get("revision_conflict"):
        projected = [r for r in emissions if r.get("revision_source") == "printed"]
        flagged = any("revision_conflict" in (r.get("flags") or ()) for r in emissions)
        out["revision_conflict"] = ("conflict_resolved_silently" if projected and not flagged else
                                    "conflict_held" if flagged else "conflict_missing" if emissions else "missed")
    # other evaluated fields (non-critical)
    first = emissions[0] if emissions else None
    for f, judge in (("system", v3.judge_system), ("floor", v3.judge_floor), ("title", v3.judge_title)):
        if f in e:
            states = [judge(e.get(f), r) for r in emissions] or [judge(e.get(f), None)]
            out[f] = "wrong" if "wrong" in states else "fp" if "fp" in states else "tp" if "tp" in states else states[0]
    # projection layer: the business revision
    if emissions and vstate == "readable":
        proj = {r.get("revision") for r in emissions if r.get("revision")}
        out["projection_revision"] = "tp" if proj == {vval} else "differs" if proj else "absent"
    if not executed:
        out = {k: ("missed" if s in ("missed",) else s) for k, s in out.items()}
    return out


def judge_raw(e: dict, facts: list[dict]) -> dict:
    """Raw layer: evidence of this expected component anywhere the reading kept it, on its page."""
    page_facts = [f for f in facts if f["page"] == e["page"]]
    out = {}
    rstate, rval = reference_truth(e.get("reference"))
    ids = [f["identity"] for f in page_facts if f.get("identity")]
    held_ids = [f["held_identity"] for f in page_facts if f.get("held_identity")]
    if rstate == "readable":
        match = [i for i in ids if v3.same_identity(rval, i) in ("exact", "suffix", "near")]
        out["identity"] = "tp" if match else "held" if any(v3.same_identity(rval, h) in ("exact", "suffix", "near") for h in held_ids) else \
            "missed"
        linked = [f for f in page_facts if f.get("identity") and v3.same_identity(rval, f["identity"]) in ("exact", "suffix", "near")]
    else:
        out["identity"] = "unscorable" if rstate == "unscorable" else ("fp" if ids else "tn")
        linked = page_facts if len({f.get("identity") for f in page_facts if f.get("identity")}) <= 1 else []
    vstate, vval = revision_truth(e.get("printed_revision"), e.get("reference"))
    revs = [v3.norm_rev(f["revision"]) for f in linked if f.get("revision")]
    out["revision"] = "unscorable" if vstate == "unscorable" else ("fp" if revs else "tn") if vstate == "negative" else \
        ("tp" if vval in revs else "wrong" if revs else "missed")
    dstate, dval = decision_truth(e.get("decision"))
    decs = set().union(*[f.get("decisions") or set() for f in linked]) if linked else set()
    out["decision"] = "unscorable" if dstate == "unscorable" else ("fp" if decs else "tn") if dstate == "negative" else \
        ("tp" if len(decs) > 1 else "missed") if dstate == "conflict" else ("tp" if dval in decs else "wrong" if decs else "missed")
    return out


# --- the evaluation --------------------------------------------------------------------------------------------------


def execution_outcome(row: dict | None) -> str:
    if row is None:
        return "not_run"
    if (row.get("state") or "") == "failed":
        return "failed"
    cov = ((row.get("extracted") or {}).get("coverage") or {})
    return cov.get("outcome") or ("complete" if (row.get("extracted") or {}) else "no_reading")


def evaluate(labels: dict, page_labels: dict | None, rows: dict, corrections: list[dict] | None = None) -> dict:
    rows = {k.replace("\\", "/"): v for k, v in rows.items()}
    plabels = {k.replace("\\", "/"): v for k, v in ((page_labels or {}).get("documents") or {}).items()}
    fixes = collections.defaultdict(list)
    for c in corrections or ():
        fixes[c["doc_suffix"]].append(c)
    docs = []
    for doc in labels["documents"]:
        key = doc["doc"].replace("\\", "/")
        lab = dict(doc["labels"])
        for suffix, items in fixes.items():
            if key.endswith(suffix):
                for c in items:
                    lab[c["field"]] = c["new"]
        doc = {**doc, "labels": lab}
        row = rows.get(key)
        outcome = execution_outcome(row)
        executed = outcome not in ("not_run", "failed")
        exp, no_record, unvalidated, page_labelled = expected_records(doc, plabels.get(key))
        exp_by_page = collections.defaultdict(list)
        for e in exp:
            exp_by_page[e["page"]].append(e)
        labelled_pages = set(exp_by_page) | no_record if page_labelled else {1}
        entry = {"doc": key, "ep": doc["ep"], "cohort": doc.get("cohort"), "stratum": doc.get("stratum"),
                 "extension": doc.get("extension"), "scan_like": doc.get("scan_like"), "confidence": doc.get("confidence"),
                 "in_scope": v3.in_scope(v3.literal(lab.get("kind")) or lab.get("kind")), "execution": outcome,
                 "records": [], "emissions": [], "unvalidated": [], "raw": [], "evidence": [], "ai": ai_coverage(row)}
        emitted = v3.records_of(row) if executed or outcome == "partial" else v3.records_of(row)
        assoc = collections.defaultdict(list)
        for r in emitted:
            page = int(r.get("page") or 1)
            if page not in labelled_pages or page in unvalidated:
                entry["unvalidated"].append({"page": page, "reference": r.get("reference"), "status": r.get("status")})
                continue
            e, how = associate(r, exp_by_page, exp)
            em = {"page": page, "how": how, "reference": r.get("reference"), "status": r.get("status"),
                  "printed_revision": v3.raw_revision(r)}
            if e is not None:
                assoc[e["_id"]].append(r)
                em["expected"] = e["_id"]
                if how == "substituted":
                    em["fields"] = {"reference": "wrong"}
            elif how == "unassociated":
                em["fields"] = {"reference": "wrong"}          # an identity of none of the page's components
            else:
                em["fields"] = {"reference": "fp", "decision": "fp" if r.get("status") in POSITIVE else "tn",
                                "revision": "fp" if v3.raw_revision(r) else "tn"}
            entry["emissions"].append(em)
        facts = raw_facts(row)
        evidence_facts = facts + ai_facts(row)
        for e in exp:
            ems = assoc.get(e["_id"], [])
            f = judge_fields(e, ems, executed)
            register = bool(e.get("register", True))
            how = "matched" if ems else ("missing" if register else "unregistered")
            if not ems and e.get("duplicate_of_page"):
                how = "component_not_repeated"
                f = {k: ("tn" if s == "tn" else "not_repeated") for k, s in f.items()}
            if not ems and not register:
                f = {}          # register layer: an ineligible record is not missing from the register
            if ems and not register:
                how = "matched_register_ineligible"
            substituted = [em for em in entry["emissions"] if em.get("expected") == e["_id"] and em["how"] == "substituted"]
            if substituted and how == "matched":
                how = "substituted"
                f["reference"] = "wrong"
            red = collections.Counter(json.dumps({k: r.get(k) for k in ("reference", "printed_revision", "status")}, sort_keys=True) for r in ems)
            entry["records"].append({"page": e["page"], "expected": {k: e.get(k) for k in ("component", "reference", "printed_revision", "decision", "register", "revision_conflict")},
                                     "how": how, "fields": f, "emissions": len(ems),
                                     "redundant_copies": sum(n - 1 for n in red.values()),
                                     "conflicting_emissions": len(red) > 1 and len({(json.loads(k)["status"], json.loads(k)["printed_revision"]) for k in red}) > 1})
            entry["raw"].append({"page": e["page"], "register": register, "fields": judge_raw(e, facts)})
            entry["evidence"].append({"page": e["page"], "register": register, "fields": judge_raw(e, evidence_facts),
                                      "expected": {k: e.get(k) for k in ("component", "reference", "printed_revision", "decision")}})
        docs.append(entry)
    return {"evaluator": EVALUATOR_VERSION, "documents": docs, "totals": totals(docs)}


# --- totals ----------------------------------------------------------------------------------------------------------


def rates(c: collections.Counter) -> dict:
    tp, wrong, fp = c["tp"], c["wrong"], c["fp"]
    aoc, crs = c["accepted_on_conflict"], c["conflict_resolved_silently"]
    accepted = tp + wrong + fp + aoc + crs
    readable = tp + wrong + c["missed"] + c["held"]
    negatives = c["tn"] + fp
    out = {k: c[k] for k in ("tp", "wrong", "fp", "tn", "held", "missed", "accepted_on_conflict", "conflict_held",
                             "conflict_missing", "conflict_resolved_silently", "unscorable", "not_repeated")}
    out.update({"accepted": accepted, "readable": readable,
                "precision_of_accepted": round(tp / accepted, 4) if accepted else None,
                "recovery_of_readable": round(tp / readable, 4) if readable else None,
                "specificity_of_negatives": round(c["tn"] / negatives, 4) if negatives else None})
    return out


def totals(docs: list[dict]) -> dict:
    reg = collections.defaultdict(collections.Counter)
    raw = collections.defaultdict(collections.Counter)
    evidence = collections.defaultdict(collections.Counter)
    introduced = []
    ai_states, ai_outcomes = collections.Counter(), collections.Counter()
    ai_calls = ai_hits = ai_docs = 0
    how = collections.Counter()
    emission_how = collections.Counter()
    execution = collections.Counter()
    critical, redundant, conflicting, unvalidated = [], 0, 0, 0
    for d in docs:
        execution[d["execution"]] += 1
        unvalidated += len(d["unvalidated"])
        for rec in d["records"]:
            how[rec["how"]] += 1
            redundant += rec["redundant_copies"]
            conflicting += bool(rec["conflicting_emissions"])
            for f, s in rec["fields"].items():
                reg[f][s] += 1
                if f in CRITICAL_FIELDS + ("revision_conflict",) and s in ("wrong", "fp", "accepted_on_conflict", "conflict_resolved_silently"):
                    critical.append({"kind": f"{f}: {s}", "doc": d["doc"], "page": rec["page"], "expected": rec["expected"]})
        for em in d["emissions"]:
            emission_how[em["how"]] += 1
            for f, s in (em.get("fields") or {}).items():
                if em["how"] in ("none", "unassociated"):
                    reg[f][s] += 1
                    if s in ("wrong", "fp") and f in CRITICAL_FIELDS:
                        critical.append({"kind": f"{f}: {s} ({'record where truth has none' if em['how'] == 'none' else 'identity of no component on the page'})",
                                         "doc": d["doc"], "page": em["page"], "actual": {k: em.get(k) for k in ("reference", "status", "printed_revision")}})
        for r in d["raw"]:
            for f, s in r["fields"].items():
                raw[f][s] += 1
        for r, base in zip(d.get("evidence") or [], d["raw"]):
            for f, s in r["fields"].items():
                evidence[f][s] += 1
                if s in ("wrong", "fp") and base["fields"].get(f) not in ("wrong", "fp"):
                    introduced.append({"kind": f"{f}: {s}", "doc": d["doc"], "page": r["page"], "expected": r.get("expected")})
        ai = d.get("ai") or {}
        if ai:
            ai_docs += 1
            ai_calls += ai.get("calls", 0)
            ai_hits += ai.get("cache_hits", 0)
            ai_states.update(ai.get("states") or {})
            ai_outcomes.update(ai.get("page_outcomes") or {})
    return {"execution": dict(execution), "records": dict(how), "emissions": dict(emission_how),
            "redundant_copies": redundant, "conflicting_emission_sets": conflicting, "unvalidated_emitted_records": unvalidated,
            "register": {f: rates(c) for f, c in reg.items()}, "raw": {f: rates(c) for f, c in raw.items()}, "critical": critical,
            "evidence": {f: rates(c) for f, c in evidence.items()}, "evidence_introduced_errors": introduced,
            "ai": {"documents": ai_docs, "calls": ai_calls, "cache_hits": ai_hits, "states": dict(ai_states),
                   "page_outcomes": dict(ai_outcomes)}}


def grouped(result: dict, keyfn) -> dict:
    groups = collections.defaultdict(list)
    for d in result["documents"]:
        groups[keyfn(d)].append(d)
    return {str(k): {"documents": len(v), **totals(v)} for k, v in sorted(groups.items(), key=lambda kv: str(kv[0]))}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--page-labels")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    labels = json.loads(Path(args.labels).read_text(encoding="utf-8-sig"))
    page_labels = json.loads(Path(args.page_labels).read_text(encoding="utf-8-sig")) if args.page_labels else None
    rows = json.loads(Path(args.rows).read_text(encoding="utf-8-sig"))
    result = evaluate(labels, page_labels, rows, (page_labels or {}).get("page1_corrections"))
    result["by"] = {
        "project": grouped(result, lambda d: d["ep"]), "cohort": grouped(result, lambda d: d["cohort"]),
        "format": grouped(result, lambda d: "word" if d["extension"] != ".pdf" else ("scan" if d["scan_like"] else "text")),
        "label_confidence": grouped(result, lambda d: d.get("confidence")), "execution": grouped(result, lambda d: d["execution"]),
    }
    Path(args.out).write_text(json.dumps(result, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    t = result["totals"]
    print(json.dumps({"critical": len(t["critical"]), "records": t["records"], "execution": t["execution"],
                      **{f: {k: v[k] for k in ("accepted", "tp", "readable", "precision_of_accepted", "recovery_of_readable")}
                         for f, v in t["register"].items() if f in CRITICAL_FIELDS}}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
