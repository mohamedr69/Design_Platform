"""M2 pilot evaluator .10 (M2 review 29, C4): derived from .9 (scripts/m2_eval5.py, unchanged) with ONE change -- association
is decided per fact. When a group associates with another page's component (cross_page / target_cross_page), only its
identity facts take that association (a copy of the document's identity on a continuation page, the .6 rule); its
dependent facts (revision, decision) are judged on their OWN page: a no-record page makes them false positives when
asserted and held_on_negative when held; a page with exactly one component judges them against that component
(own_page_component); otherwise they are unassociated. So a fact's outcome never depends on whether another fact of
its group was asserted. Everything else is .9.

M2 pilot evaluator .5 (M2 review 07, R7-01): every emitted fact is scored. Evaluator .4 (`scripts/m2_eval4.py`)
stays unchanged as history; its truth states, expected records and register layer are reused as they are (the
register-layer corrections R6-01..R6-03 were reproduced by the reviewer).

What changes is the raw / evidence / AI accounting, which in .4 merged facts per page, judged only facts linked by a
matching identity, and let a correct value mask a wrong one. In .5:

1. **Facts, not pages.** Each emission unit -- a register record, a deterministic observation, an AI component read --
   is a *group* of facts ``{field, value, state}`` with its page, component key, reader and provenance. Every value is
   kept: two identities on one page are two groups; nothing is overwritten.
2. **States.** ``accepted`` (a register record's values), ``observed`` (a deterministic source observation -- raw
   evidence, not an automatic acceptance), ``validated`` (the AI validation policy accepted it), and the non-accepted
   ``held`` (a flagged reference, an untrusted OCR number, an AI candidate / conflict, a decision candidate). Only the
   first three are *asserted* facts; held facts earn evidence credit and are never precision errors.
3. **Association is explicit.** A group is associated with a truth component by an asserted identity on its page
   (exact / suffix), else on another page of the document (cross-page copy), else -- when the page has exactly one
   component -- by that single component (and an asserted identity that does not match it is *wrong*, never missing),
   else it stays ``unassociated``: its asserted identity is a wrong identity of no component on the page (critical),
   and its other asserted facts are ``association_unknown`` (counted, never scored right or wrong). On a labelled page
   with no component (a no-record page) every asserted fact is a false positive. Facts on unlabelled / unvalidated
   pages are counted as ``unscored_page``.
4. **Two measures, kept apart.**
   - *accepted-output precision*: over **distinct** asserted facts (component, field, normalised value) -- a redundant
     identical copy is one fact (counted in ``redundant``); each distinct wrong value is one error, whatever else is
     correct;
   - *deduplicated source-fact recovery*: per truth component and field, ``recovered_clean`` (a correct asserted value
     and no wrong one), ``recovered_mixed`` (correct and wrong both asserted -- the wrong one is also a precision
     error), ``wrong_only``, ``held_only`` (a correct value exists only as held evidence), ``missed``; negatives are
     ``tn`` / ``fp``; conflict truth gives ``accepted_on_conflict`` (critical) / ``conflict_held`` / ``conflict_missing``.
5. **Layers.** ``raw`` = register records (flagged references held) + deterministic observations; ``evidence`` = raw
   + AI; ``ai`` = AI groups alone. ``introduced`` lists every asserted AI fact that is wrong or a false positive -- not
   only fields whose raw verdict was clean.
6. **Order does not matter.** Groups are judged independently and aggregated as sets.

Usage: python -m scripts.m2_eval5 --labels L.json [--page-labels P.json] --rows rows.json --out out.json
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

from scripts import m2_eval4 as ev4
from scripts import m2_pilot_eval as v3

EVALUATOR_VERSION = "m2-pilot-eval-2026-10-02.10"  # .10: association per fact -- no dependent fact crosses pages (review 29 C4)
# m2-pilot-eval-2026-09-29.9: targetless retained facts held when their context changed (review 10)
# m2-pilot-eval-2026-09-29.8: retained facts judged under their association; source identity (review 09)
# m2-pilot-eval-2026-09-29.7: AI evidence selected for the run's declared context (review 08)
# m2-pilot-eval-2026-09-29.6   # .6: a no-record page associates a cross-page copy of the document's own identity (as .4); pending-evidence records hold all their facts
FIELDS = ("identity", "revision", "decision")
ASSERTED = ("accepted", "observed", "validated")
ACCEPTANCE = ("accepted", "validated")          # automatic acceptances: a register value, an AI-validated fact
CRITICAL_OUTCOMES = ("wrong", "fp", "accepted_on_conflict", "wrong_unassociated")
CARRIED = ("target", "target_revision", "association", "context_identity")   # association metadata kept on judgements


# --- emitted facts ---------------------------------------------------------------------------------------------------


def _group(page, layer, kind, reader, component, facts, provenance=None) -> dict:
    return {"page": int(page or 1), "layer": layer, "kind": kind, "reader": reader, "component": component,
            "facts": [f for f in facts if f.get("value") not in (None, "")], "provenance": provenance or {}}


def _fact(field, value, state, **extra) -> dict:
    return {"field": field, "value": value, "state": state, **extra}


def record_groups(row: dict | None) -> list[dict]:
    """Register records as raw groups: values accepted, a flagged reference held (the raw layer's view)."""
    ex = (row or {}).get("extracted") or {}
    pending = {int(str(p["key"]).rsplit(":r", 1)[1]) for p in ex.get("pending_evidence") or [] if ":r" in str(p.get("key"))}
    out = []
    for i, rec in enumerate(ex.get("records") or []):
        ref, held = ev4.accepted_reference(rec)
        # a record the application holds as pending evidence (review 07 guard) accepts nothing: all its facts are held
        state = "held" if i in pending else "accepted"
        facts = [_fact("identity", ref, "held" if held or i in pending else "accepted"),
                 _fact("revision", v3.raw_revision(rec), state)]
        if rec.get("status") in ev4.POSITIVE:
            facts.append(_fact("decision", rec["status"], state))
        facts += [_fact("decision", d, "held") for d in ev4.held_decisions(rec)]
        out.append(_group(rec.get("page"), "raw", "record", "parser", f"record:{i}", facts,
                          {"source": rec.get("source"), "flags": rec.get("flags")}))
    return out


def observation_groups(row: dict | None) -> list[dict]:
    """Deterministic observations: every shape, every value (a transmittal's listed records are groups of their own)."""
    ex = (row or {}).get("extracted") or {}
    out = []
    for i, obs in enumerate(ex.get("observations") or []):
        kind, page = obs.get("kind"), ev4._obs_page(obs)
        key = f"obs:{i}"
        if kind == "title_block":
            facts = [_fact("identity", obs.get("number"), "observed"), _fact("revision", obs.get("revision"), "observed")]
            if not obs.get("number") and (obs.get("number_candidate") or obs.get("number_literal")):
                facts.append(_fact("identity", obs.get("number_candidate") or obs.get("number_literal"), "held"))
            out.append(_group(page, "raw", kind, "title_block", key, facts, {"source": obs.get("source")}))
        elif kind == "transmittal":
            own = obs.get("reference")
            facts = [_fact("identity", own, "observed")] if own else [_fact("identity", obs.get("raw_reference"), "held")]
            out.append(_group(page, "raw", kind, "transmittal", key, facts))
            for j, rec in enumerate(obs.get("records") or []):
                out.append(_group(page, "raw", "transmittal_record", "transmittal", f"{key}:rec:{j}",
                                  [_fact("identity", rec.get("reference"), "observed")]))
        elif kind == "cover_untracked":
            rec = obs.get("record") or {}
            facts = [_fact("identity", rec.get("reference"), "observed"), _fact("revision", v3.raw_revision(rec), "observed")]
            if rec.get("status") in ev4.POSITIVE:
                facts.append(_fact("decision", rec["status"], "observed"))
            facts += [_fact("decision", d, "held") for d in ev4.held_decisions(rec)]
            out.append(_group(page, "raw", kind, "parser", key, facts))
        elif kind == "drawing_sheet":
            out.append(_group(page, "raw", kind, "parser", key, [_fact("identity", obs.get("reference"), "observed")]))
        elif kind == "decision_unpromoted":
            cands = {c.get("status") if isinstance(c, dict) else c[0] for c in obs.get("candidates") or obs.get("marks") or [] if c}
            out.append(_group(page, "raw", kind, "parser", key, [_fact("decision", c, "held") for c in sorted(c for c in cands if c)]))
        elif kind == "consultant_comments":
            if obs.get("decision") in ev4.POSITIVE:
                out.append(_group(page, "raw", kind, "parser", key, [_fact("decision", obs["decision"], "observed")]))
        elif kind in ("form_identity", "evidence", "ai_observation", "own_identity"):
            facts = [_fact("identity", obs.get("identity") or obs.get("literal"), "observed"),
                     _fact("revision", obs.get("revision"), "observed")]
            if obs.get("decision") in ev4.POSITIVE:
                facts.append(_fact("decision", obs["decision"], "observed"))
            out.append(_group(page, "raw", kind, obs.get("source") or "fields", key, facts))
    return out


def ai_envelope(row: dict | None, ai_context: dict | None, doc: str | None = None) -> tuple[dict, str]:
    """(envelope, state) of the AI evidence that applies to the evaluated run's declared context -- its variant,
    its extraction profile (default: the row's own) and optionally the compatible policies -- through
    `evidence_reader.evidence_for`. No context, no AI evidence: another run's envelope is never scored for this one
    (review 08, R8-02). A historical run whose stored envelopes carry no profile is scored only when its context
    declares `accept_unknown_profile` (from the run manifest). Evidence that records no source hash is scored only
    under a declared historical binding -- `historical_source` {"manifest", "sha256_by_doc"} from a run manifest --
    and only for the bytes that manifest names for this document (review 09, R9-03)."""
    if ai_context is None:
        return {}, "no_context"
    from app.ai import evidence_reader

    row = row or {}
    ai = (row.get("extracted") or {}).get("ai_evidence") or {}
    if not ai:
        return {}, "none"
    profile = ai_context.get("profile", (row.get("extracted") or {}).get("profile"))
    hs = ai_context.get("historical_source") or None
    binding = ({"manifest": hs.get("manifest"), "sha256": (hs.get("sha256_by_doc") or {}).get(doc)} if hs and doc else None)
    got = evidence_reader.evidence_for(ai, sha256=row.get("sha256"), profile=profile, variant=ai_context.get("variant"),
                                       policies=ai_context.get("policies"), accept_unknown_profile=bool(ai_context.get("accept_unknown_profile")),
                                       historical_source=binding)
    return (got.get("envelope") or {}) if got["state"] == "current" else {}, got["state"]


def ai_groups(row: dict | None, ai_context: dict | None = None, doc: str | None = None) -> list[dict]:
    """One group per AI component read. Review 07 observations carry a `component` key; review 06 observations do
    not, so their page's single own-identity read is one component -- and where a page has several AI identity
    observations, each is its own group and that page's revision / decision observations stay unassociated with any
    of them (`component: None`), never merged into one.
    Review 09 (R9-02): a dependent fact keeps its explicit association (`evidence_reader.association_of`). One whose
    target is not the component's current identity -- `held:*` (held) or `by_target` (its own state) -- is a group of
    its own, associated by its target (`association_identity`), never beside another identity. Target and association
    travel with the fact into the judgement; a fact that never recorded a target is grouped as before.
    Review 10 (R10-01): a held fact that never recorded a target (its component's identity or revision changed since it
    was read) is a group of its own with no association (`unassigned_component`): judged held and unassociated -- no
    target is invented and it is never reassigned. Target revision and recorded context identity travel with it."""
    env, _state = ai_envelope(row, ai_context, doc)
    obs_list = [o for o in env.get("observations") or [] if o.get("value") not in (None, "")]
    state_of = lambda o: "validated" if o.get("state") == "validated" else "held"
    groups: dict = {}
    by_page = collections.defaultdict(list)
    for o in obs_list:
        by_page[ev4._obs_page(o)].append(o)
    for page, items in by_page.items():
        own_ids = [o for o in items if o.get("field") == "identity"]
        for i, o in enumerate(items):
            role = o.get("role") or "own"
            assoc = o.get("association") or {}
            status = assoc.get("status")
            if status and (status.startswith("held:") or status == "by_target"):
                key = (f"ai:{page}:{o.get('component') or 'own'}@{assoc['target']}" if assoc.get("target") else
                       f"ai:{page}:{o.get('component') or 'own'}~unassociated")
            elif o.get("component") is not None:
                key = f"ai:{page}:{o['component']}"
            elif len(own_ids) <= 1:
                key = f"ai:{page}:0"
            else:
                key = f"ai:{page}:id{own_ids.index(o)}" if o in own_ids else f"ai:{page}:unassigned"
            g = groups.setdefault(key, _group(page, "ai", "ai_evidence", f"ai:{o.get('variant') or env.get('variant')}", key, [],
                                              {"version": o.get("version"), "policy": o.get("policy"), "profile": env.get("profile")}))
            if "@" in key:
                g["association_identity"] = assoc["target"]
            if key.endswith("~unassociated"):
                g["unassigned_component"] = True
            if role != "own" and o.get("field") == "identity":
                g["facts"].append(_fact("referenced_identity", o["value"], "observed_reference", role=role))
                continue
            state = "held" if status and status.startswith("held:") else state_of(o)
            extra = {k: v for k, v in (("target", o.get("target")), ("target_revision", o.get("target_revision")),
                                       ("association", status), ("context_identity", assoc.get("context_identity"))) if v}
            g["facts"].append(_fact(o.get("field"), o["value"], state, ai_state=o.get("state"), **extra))
            if key.endswith(":unassigned"):
                g["unassigned_component"] = True
    return list(groups.values())


# --- judging -----------------------------------------------------------------------------------------------------------


def _truth(e: dict, field: str):
    if field == "identity":
        return ev4.reference_truth(e.get("reference"))
    if field == "revision":
        return ev4.revision_truth(e.get("printed_revision"), e.get("reference"))
    return ev4.decision_truth(e.get("decision"))


def _norm(field: str, value) -> str:
    if field == "identity":
        return v3.norm_ref(str(value))
    if field == "revision":
        return v3.norm_rev(value) or ""
    return str(value)


def _same(field: str, truth, value) -> bool:
    if field == "identity":
        return v3.same_identity(truth, value) in ("exact", "suffix")
    if field == "revision":
        return truth == v3.norm_rev(value)
    return truth == value


def associate_group(g: dict, exp_by_page: dict, exp_all: list[dict]) -> tuple[dict | None, str]:
    """(truth component, how): identity | cross_page | single_component | single_component_wrong_identity |
    unassociated | no_component. Only asserted identities associate by value. A group of retained facts whose
    association is their own recorded target (`association_identity`, review 09) associates by that target only:
    target | target_cross_page | target_unmatched -- never by the page's other component."""
    here = exp_by_page.get(g["page"], [])
    if g.get("association_identity"):
        target = g["association_identity"]
        for strength in ("exact", "suffix"):
            for e in here:
                if ev4.reference_truth(e.get("reference"))[0] == "readable" and v3.same_identity(v3.literal(e["reference"]), target) == strength:
                    return e, "target"
        for e in exp_all:
            if e["page"] != g["page"] and ev4.reference_truth(e.get("reference"))[0] == "readable" and \
                    v3.same_identity(v3.literal(e["reference"]), target) in ("exact", "suffix"):
                return e, "target_cross_page"
        return None, "target_unmatched"
    ids = [f["value"] for f in g["facts"] if f["field"] == "identity" and f["state"] in ASSERTED]
    for strength in ("exact", "suffix"):
        for e in here:
            if ev4.reference_truth(e.get("reference"))[0] == "readable" and any(
                    v3.same_identity(v3.literal(e["reference"]), i) == strength for i in ids):
                return e, "identity"
    for e in exp_all:
        if e["page"] != g["page"] and ev4.reference_truth(e.get("reference"))[0] == "readable" and any(
                v3.same_identity(v3.literal(e["reference"]), i) in ("exact", "suffix") for i in ids):
            return e, "cross_page"
    if not here:
        return None, "no_component"
    if len(here) == 1 and not g.get("unassigned_component"):
        known = ev4.reference_truth(here[0].get("reference"))[0] == "readable"
        return here[0], "single_component_wrong_identity" if (ids and known) else "single_component"
    return None, "unassociated"


def judge_group(g: dict, e: dict | None, how: str, negative_page: bool) -> list[dict]:
    """Every fact of the group with its outcome (and the truth it was judged against)."""
    out = []
    for f in g["facts"]:
        field, state = f["field"], f["state"]
        asserted = state in ASSERTED
        rec = {"field": field, "value": f["value"], "state": state, "how": how,
               **{k: f[k] for k in CARRIED if f.get(k)}}
        if field not in FIELDS:
            rec["outcome"] = "not_scored"
        elif negative_page:
            rec["outcome"] = "fp" if asserted else "held_on_negative"
        elif e is None:
            rec["outcome"] = ("wrong_unassociated" if field == "identity" else "association_unknown") if asserted else "held_unassociated"
        else:
            tstate, tval = _truth(e, field)
            rec["truth"] = tval
            if tstate == "unscorable":
                rec["outcome"] = "unscorable"
            elif tstate == "negative":
                rec["outcome"] = "fp" if asserted else "held_on_negative"
            elif tstate == "conflict":
                rec["outcome"] = "accepted_on_conflict" if asserted else "conflict_held"
            else:
                right = _same(field, tval, f["value"])
                if field == "identity" and not right and v3.same_identity(tval, f["value"]) == "near":
                    rec["near"] = True
                rec["outcome"] = ("correct" if right else "wrong") if asserted else ("held_correct" if right else "held_wrong")
        out.append(rec)
    return out


def score_layer(groups: list[dict], exp: list[dict], no_record: set, unvalidated: set, labelled_pages: set) -> dict:
    exp_by_page = collections.defaultdict(list)
    for e in exp:
        exp_by_page[e["page"]].append(e)
    judged, association = [], collections.Counter()
    for g in groups:
        if g["page"] not in labelled_pages or g["page"] in unvalidated:
            for f in g["facts"]:
                judged.append({"field": f["field"], "value": f["value"], "state": f["state"], "how": "unscored_page",
                               "outcome": "unscored_page", "page": g["page"], "reader": g["reader"], "group": g["component"], "expected": None,
                               **{k: f[k] for k in CARRIED if f.get(k)}})
            association["unscored_page"] += 1
            continue
        negative_page = g["page"] in no_record and not exp_by_page.get(g["page"])
        e, how = associate_group(g, exp_by_page, exp)
        if negative_page and how not in ("cross_page", "target_cross_page"):
            # a no-record page: only a copy of the document's own identity from another page associates (as .4 does);
            # anything else asserted there is a false positive
            e, how = None, "negative_page"
        association[how] += 1
        parts = [(g, e, how)]
        if how in ("cross_page", "target_cross_page"):
            # .10 (C4 A4 / A6): only identity facts cross pages; dependent facts are judged on their own page
            ident = [f for f in g["facts"] if f["field"] in ("identity", "referenced_identity")]
            deps = [f for f in g["facts"] if f["field"] not in ("identity", "referenced_identity")]
            here = exp_by_page.get(g["page"], [])
            if negative_page:
                e_dep, how_dep = None, "negative_page"
            elif len(here) == 1 and not g.get("unassigned_component"):
                e_dep, how_dep = here[0], "own_page_component"
            else:
                e_dep, how_dep = None, "unassociated"
            parts = [(dict(g, facts=ident), e, how)] + ([(dict(g, facts=deps), e_dep, how_dep)] if deps else [])
            if deps:
                association["dependents_on_own_page"] += 1
        for gg, ee, hh in parts:
            for rec in judge_group(gg, ee, hh, hh == "negative_page"):
                rec.update(page=gg["page"], reader=gg["reader"], group=gg["component"], layer=gg["layer"],
                           expected=ee["_id"] if ee is not None else None)
                judged.append(rec)
    # precision over distinct asserted facts: (component-or-group, field, normalised value)
    distinct: dict = {}
    for r in judged:
        if r["state"] not in ASSERTED or r["field"] not in FIELDS or r["outcome"] in ("unscored_page", "not_scored"):
            continue
        anchor = f"exp:{r['expected']}" if r["expected"] is not None else f"page:{r['page']}:{r['group']}"
        key = (anchor, r["field"], _norm(r["field"], r["value"]))
        distinct.setdefault(key, []).append(r)
    precision = collections.defaultdict(collections.Counter)
    by_state = collections.defaultdict(collections.Counter)
    for (anchor, field, _v), rs in distinct.items():
        precision[field][rs[0]["outcome"]] += 1
        precision[field]["redundant"] += len(rs) - 1
        # the strongest state any copy of this distinct fact carries: an automatic acceptance outranks an observation
        state = "accepted" if any(r["state"] in ACCEPTANCE for r in rs) else "observed"
        by_state[f"{field}:{state}"][rs[0]["outcome"]] += 1
    # recovery per truth component and field
    recovery = collections.defaultdict(collections.Counter)
    per_component = []
    for e in exp:
        mine = [r for r in judged if r["expected"] == e["_id"]]
        entry = {"page": e["page"], "expected": {k: e.get(k) for k in ("component", "reference", "printed_revision", "decision")}, "fields": {}}
        for field in FIELDS:
            tstate, _ = _truth(e, field)
            rs = [r for r in mine if r["field"] == field]
            outs = {r["outcome"] for r in rs}
            if tstate == "unscorable":
                s = "unscorable"
            elif tstate == "negative":
                s = "fp" if "fp" in outs else "tn"
            elif tstate == "conflict":
                s = "accepted_on_conflict" if "accepted_on_conflict" in outs else "conflict_held" if "conflict_held" in outs else "conflict_missing"
            else:
                s = ("recovered_mixed" if "wrong" in outs else "recovered_clean") if "correct" in outs else \
                    "wrong_only" if "wrong" in outs else "held_only" if "held_correct" in outs else "missed"
            entry["fields"][field] = s
            recovery[field][s] += 1
        per_component.append(entry)
    # critical: a wrong automatic acceptance (register value / AI-validated). A wrong deterministic *observation* is
    # raw evidence that is wrong -- counted apart (`observed_errors`), never hidden, never called an acceptance.
    critical = [r for r in judged if r["state"] in ACCEPTANCE and r["field"] in FIELDS and r["outcome"] in CRITICAL_OUTCOMES]
    observed_errors = [r for r in judged if r["state"] == "observed" and r["field"] in FIELDS and r["outcome"] in CRITICAL_OUTCOMES]
    return {"judged": judged, "association": dict(association), "precision": {f: dict(c) for f, c in precision.items()},
            "precision_by_state": {k: dict(c) for k, c in by_state.items()},
            "recovery": {f: dict(c) for f, c in recovery.items()}, "components": per_component, "critical": critical,
            "observed_errors": observed_errors}


# --- the evaluation --------------------------------------------------------------------------------------------------


def register_view(rows: dict) -> dict:
    """The rows as the register builders see them: a record the application holds as pending evidence (an incomplete
    / uncertain reference, `extracted.pending_evidence`, review 07) keys no business row, so it is no register
    emission. Rows read before that guard carry no such list and are scored as they were."""
    out = {}
    for key, row in rows.items():
        ex = (row or {}).get("extracted") or {}
        pending = ex.get("pending_evidence") or []
        if not pending:
            out[key] = row
            continue
        held = {int(str(p["key"]).rsplit(":r", 1)[1]) for p in pending if ":r" in str(p.get("key"))}
        out[key] = {**row, "extracted": {**ex, "records": [r for i, r in enumerate(ex.get("records") or []) if i not in held]}}
    return out


def evaluate(labels: dict, page_labels: dict | None, rows: dict, corrections: list[dict] | None = None,
             ai_context: dict | None = None) -> dict:
    """Register layer as .4 over the register view (pending evidence withheld); raw / evidence / ai layers fact by fact."""
    base = ev4.evaluate(labels, page_labels, register_view(rows), corrections)
    rows = {k.replace("\\", "/"): v for k, v in rows.items()}
    plabels = {k.replace("\\", "/"): v for k, v in ((page_labels or {}).get("documents") or {}).items()}
    fixes = collections.defaultdict(list)
    for c in corrections or ():
        fixes[c["doc_suffix"]].append(c)
    by_doc = {d["doc"]: d for d in base["documents"]}
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
        exp, no_record, unvalidated, page_labelled = ev4.expected_records(doc, plabels.get(key))
        pages_with_components = {e["page"] for e in exp}
        labelled_pages = pages_with_components | no_record if page_labelled else {1}
        raw = record_groups(row) + observation_groups(row)
        ai = ai_groups(row, ai_context, key)
        ai_state = ai_envelope(row, ai_context, key)[1]
        entry = dict(by_doc[key])
        entry["ai_evidence_state"] = ai_state
        entry.pop("raw", None)
        entry.pop("evidence", None)
        entry["layers"] = {name: score_layer(groups, exp, no_record, unvalidated, labelled_pages)
                           for name, groups in (("raw", raw), ("evidence", raw + ai), ("ai", ai))}
        docs.append(entry)
    t = totals(docs, base["totals"])
    t["ai_evidence_states"] = dict(collections.Counter(d["ai_evidence_state"] for d in docs))
    return {"evaluator": EVALUATOR_VERSION, "register_evaluator": ev4.EVALUATOR_VERSION, "ai_context": ai_context and
            {k: (sorted(v) if isinstance(v, set) else v) for k, v in ai_context.items()}, "documents": docs, "totals": t}


def layer_rates(precision: collections.Counter, recovery: collections.Counter) -> dict:
    correct, wrong, fp = precision["correct"], precision["wrong"] + precision["wrong_unassociated"], precision["fp"]
    aoc = precision["accepted_on_conflict"]
    asserted = correct + wrong + fp + aoc
    rec_ok = recovery["recovered_clean"] + recovery["recovered_mixed"]
    readable = rec_ok + recovery["wrong_only"] + recovery["held_only"] + recovery["missed"]
    return {"precision_counts": dict(precision), "recovery_counts": dict(recovery),
            "asserted_distinct": asserted, "readable": readable,
            "accepted_precision": round(correct / asserted, 4) if asserted else None,
            "recovery": round(rec_ok / readable, 4) if readable else None,
            "clean_recovery": round(recovery["recovered_clean"] / readable, 4) if readable else None,
            "evidence_recovery_incl_held": round((rec_ok + recovery["held_only"]) / readable, 4) if readable else None}


def totals(docs: list[dict], register_totals: dict) -> dict:
    layers = {}
    for name in ("raw", "evidence", "ai"):
        precision = collections.defaultdict(collections.Counter)
        recovery = collections.defaultdict(collections.Counter)
        association, critical, observed = collections.Counter(), [], []
        by_state = collections.defaultdict(collections.Counter)
        for d in docs:
            L = d["layers"][name]
            for k, c in L.get("precision_by_state", {}).items():
                by_state[k].update(c)
            observed += [{"doc": d["doc"], **{k: r.get(k) for k in ("page", "field", "value", "state", "outcome", "truth", "how", "reader", "group")}}
                         for r in L.get("observed_errors", [])]
            for f, c in L["precision"].items():
                precision[f].update(c)
            for f, c in L["recovery"].items():
                recovery[f].update(c)
            association.update(L["association"])
            critical += [{"doc": d["doc"], **{k: r.get(k) for k in ("page", "field", "value", "state", "outcome", "truth", "how", "reader", "group")}}
                         for r in L["critical"]]
        layers[name] = {"fields": {f: layer_rates(precision[f], recovery[f]) for f in FIELDS}, "association": dict(association),
                        "critical": critical, "observed_errors": observed,
                        "precision_by_state": {k: dict(c) for k, c in sorted(by_state.items())}}
    introduced = [c for c in layers["evidence"]["critical"] if str(c.get("reader") or "").startswith("ai:")]
    return {"register": register_totals, "raw": layers["raw"], "evidence": layers["evidence"], "ai": layers["ai"],
            "introduced_ai_errors": introduced}


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
    Path(args.out).write_text(json.dumps(result, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
    t = result["totals"]
    print(json.dumps({"register_critical": len(t["register"]["critical"]),
                      **{name: {"critical": len(t[name]["critical"]),
                                **{f: {k: v[k] for k in ("asserted_distinct", "accepted_precision", "recovery", "readable")}
                                   for f, v in t[name]["fields"].items()}} for name in ("raw", "evidence", "ai")},
                      "introduced_ai_errors": len(t["introduced_ai_errors"])}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
