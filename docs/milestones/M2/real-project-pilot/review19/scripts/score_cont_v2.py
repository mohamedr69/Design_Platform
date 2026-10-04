"""R19-02: continuation coverage replay, RESULT VERSION 2 (replaces the v1 `stop_of` / `matched_completed` reporting of
ai-pilot-r18-correction/scripts/score_cont.py; the stored attempts, rows and usage are read only, never altered).

Definitions (explicit):
  REQUIRED_FIELDS = own:identity, own:revision, own:decision -- the only fields that decide page / document coverage;
    optional keys (own:<f>:targeted, own:<f>:primary, own:<f>:escalation, discovery:route, refN:identity) never do.
  Field outcome classes (from the stored page fields):
    completed_read        'completed'                  -- a usable read of the field
    discovery_absent      'absent_by_discovery'        -- discovery reported no such field (NOT a read; kept apart)
    located_incomplete    'incomplete:located_region_only'
    no_region             'incomplete:no_region'
    unusable              'unusable:*'
    failed                'failed:*'
    budget                'budget'
    not_attempted         'not_attempted' / no attempt / page not triggered
  R19-01 reinterpretation (a separate column, stored values unchanged): a 'absent_by_discovery' recorded on a LOCATED
    (not whole-page) discovery is reported as 'located_incomplete' -- text-layer silence was the only basis.
  Transport state (per document, arm): 'no_transport_stop' when every request of the attempt returned ok and none was
    refused by a budget; otherwise the list of non-ok outcomes; 'not_attempted' when there is no attempt. Transport state
    says nothing about field coverage.
  Headline: all 7 planned documents, evaluator .9 recovery (must equal v1).
  Subgroups (never the headline): no_transport_stop_subgroup (v1's 'matched_completed', renamed); required_usable_matched
    (every required field completed_read or discovery_absent in BOTH arms), with and without the R19-01 reinterpretation;
    field-specific matched sets per field (completed_read in both arms; and usable in both arms), with document IDs.
Writes results-v2/{CONT-METRICS.v2.json, CONT-COVERAGE.v2.json, V1-TO-V2-DELTAS.json}.
Usage: score_cont_v2.py (paths are the frozen continuation's)"""
import collections
import hashlib
import json
import os
import pathlib
import sys

RESULT_VERSION = "cont-coverage-2026-09-30.v2"
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-pilot-r18-correction")
R18 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
RUNS = pathlib.Path("C:/t/r2x/runs")
OUT = pathlib.Path("C:/t/iso/work/r2x/review19/results-v2")
TAGS = {"A": "cont-A", "S": "cont-S", "T2": "cont-T2"}
REQUIRED_FIELDS = ("own:identity", "own:revision", "own:decision")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
decl_path = PKG / "declaration/CONT-DECLARATION.json"
assert sha(decl_path) == "7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3"
decl = json.loads(decl_path.read_text(encoding="utf-8"))
v1 = json.loads((PKG / "results/CONT-METRICS.json").read_text(encoding="utf-8"))
L = decl["labels"]
REG = json.loads((R18 / L["dir"] / L["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((R18 / L["dir"] / L["page"]).read_text(encoding="utf-8"))
for n, h in L["files"].items():
    assert sha(R18 / L["dir"] / n) == h
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/score-no-db.db")
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):
    os.environ.pop(k, None)
sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
os.chdir("C:/t/iso/frozen-r12/backend")
from scripts import m2_eval5 as EV  # noqa: E402

assert sha(EV.__file__) == decl["code"]["evaluator"]["sha256"]
meta = {d["doc"]: d for d in REG["documents"]}
CTX = {"A": {"variant": None}}
for arm in ("S", "T2"):
    CTX[arm] = {"variant": "EV1", "profile": "default", "policies": [decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]]}


def attempt(row, arm):
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    pol = CTX[arm]["policies"][0]
    atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pol]
    return atts[-1] if atts else None


def stop_of(att):
    """TRANSPORT state only (R19-02): whether the attempt's requests returned without failure or budget refusal. It is
    never document / field coverage."""
    if att is None:
        return "not_attempted"
    bad = sorted({str(c.get("outcome")) for c in att.get("calls") or [] if str(c.get("outcome", "")) != "ok"})
    return "no_transport_stop" if not bad else "transport_stop: " + "; ".join(b[:80] for b in bad)


def klass(outcome) -> str:
    o = str(outcome or "not_attempted")
    if o == "completed":
        return "completed_read"
    if o == "absent_by_discovery":
        return "discovery_absent"
    if o == "incomplete:located_region_only":
        return "located_incomplete"
    if o == "incomplete:no_region":
        return "no_region"
    for p, k in (("unusable", "unusable"), ("failed", "failed"), ("budget", "budget")):
        if o.startswith(p):
            return k
    return "not_attempted"


coverage, docs_fields = {}, collections.defaultdict(dict)
for arm in ("S", "T2"):
    rows = json.loads((RUNS / TAGS[arm] / "out/rows.json").read_text(encoding="utf-8"))
    for doc in meta:
        att = attempt(rows.get(doc), arm)
        pages = (att or {}).get("pages") or {}
        calls = [c for c in (att or {}).get("calls") or [] if not c.get("cache_hit")]
        per_field = {}
        for f in REQUIRED_FIELDS:
            stored = [(p, (pg.get("fields") or {}).get(f)) for p, pg in sorted(pages.items()) if isinstance(pg, dict)]
            stored = [(p, v) for p, v in stored if v is not None] or [("1", None)]
            p, v = stored[0]                                     # every continuation document read one page
            located = str((pages.get(p) or {}).get("fields", {}).get("discovery:route", "")).startswith("located")
            k = klass(v)
            k19 = "located_incomplete" if (k == "discovery_absent" and located) else k
            per_field[f] = {"stored": v, "class": k, "class_under_R19_01": k19, "page": p, "located_discovery": located}
        usable = lambda key: all(per_field[f][key] in ("completed_read", "discovery_absent") for f in REQUIRED_FIELDS)
        coverage.setdefault(doc, {})[arm] = {"transport": stop_of(att), "requests": len(calls),
                                             "fields": {pn: dict((pg or {}).get("fields") or {}) for pn, pg in pages.items() if isinstance(pg, dict)}, "request_outcomes": dict(collections.Counter(str(c.get("outcome"))[:40] for c in calls)),
                                             "required_fields": per_field, "all_required_usable": usable("class"),
                                             "all_required_usable_under_R19_01": usable("class_under_R19_01"),
                                             "all_required_read": all(per_field[f]["class"] == "completed_read" for f in REQUIRED_FIELDS)}
        docs_fields[arm][doc] = per_field

# headline: all planned, evaluator recovery (must equal v1)
headline, per_doc = {}, collections.defaultdict(dict)
for arm in ("A", "S", "T2"):
    rows = json.loads((RUNS / TAGS[arm] / "out/rows.json").read_text(encoding="utf-8"))
    ev = EV.evaluate(REG, PAGE, rows, PAGE.get("page1_corrections"), ai_context=CTX[arm])
    headline[arm] = {f: {"recovery": x["recovery_counts"], "precision_numerator": x["precision_counts"].get("correct", 0), "precision_denominator": x["asserted_distinct"]}
                     for f, x in ev["totals"]["evidence"]["fields"].items()}
    for d in ev["documents"]:
        for f in EV.FIELDS:
            per_doc[(d["doc"], f)][arm] = {k: n for k, n in (d["layers"]["evidence"]["recovery"].get(f) or {}).items() if n}
for arm in ("A", "S", "T2"):
    assert {f: v["recovery_counts"] for f, v in v1["arms"][arm]["evidence_layer"].items()} == {f: v["recovery"] for f, v in headline[arm].items()}, \
        f"all-planned recovery changed for {arm}"


def recovery(subset, field):
    out = {}
    for arm in ("A", "S", "T2"):
        c = collections.Counter()
        for d in subset:
            c.update(per_doc[(d, field)].get(arm, {}))
        out[arm] = dict(c)
    return out


planned = list(meta)
no_stop = [d for d in planned if all(coverage[d][a]["transport"] == "no_transport_stop" for a in ("S", "T2"))]
req_usable = [d for d in planned if all(coverage[d][a]["all_required_usable"] for a in ("S", "T2"))]
req_usable19 = [d for d in planned if all(coverage[d][a]["all_required_usable_under_R19_01"] for a in ("S", "T2"))]
field_sets = {}
for f, ef in (("own:identity", "identity"), ("own:revision", "revision"), ("own:decision", "decision")):
    read_both = [d for d in planned if all(docs_fields[a][d][f]["class"] == "completed_read" for a in ("S", "T2"))]
    usable_both = [d for d in planned if all(docs_fields[a][d][f]["class"] in ("completed_read", "discovery_absent") for a in ("S", "T2"))]
    usable_both19 = [d for d in planned if all(docs_fields[a][d][f]["class_under_R19_01"] in ("completed_read", "discovery_absent") for a in ("S", "T2"))]
    field_sets[f] = {"read_in_both_arms": {"docs": read_both, "n": len(read_both), "recovery": recovery(read_both, ef)},
                     "usable_in_both_arms": {"docs": usable_both, "n": len(usable_both), "recovery": recovery(usable_both, ef)},
                     "usable_in_both_arms_under_R19_01": {"docs": usable_both19, "n": len(usable_both19)}}
field_counts = {arm: {f: dict(collections.Counter(docs_fields[arm][d][f]["class"] for d in planned)) for f in REQUIRED_FIELDS} for arm in ("S", "T2")}
field_counts19 = {arm: {f: dict(collections.Counter(docs_fields[arm][d][f]["class_under_R19_01"] for d in planned)) for f in REQUIRED_FIELDS} for arm in ("S", "T2")}
metrics = {"result_version": RESULT_VERSION, "replaces": "v1 CONT-METRICS.json 'coverage_planned[*].state' / 'matched_completed' (transport success reported as completion)",
           "stored_outputs_unchanged": {t: sha(RUNS / t / "out/rows.json") for t in TAGS.values()},
           "required_fields": list(REQUIRED_FIELDS), "headline_all_planned": {"n": len(planned), "docs": planned, "recovery": headline},
           "field_outcome_counts_all_planned": field_counts, "field_outcome_counts_all_planned_under_R19_01": field_counts19,
           "no_transport_stop_subgroup": {"docs": no_stop, "n": len(no_stop), "meaning": "every request of both arms returned ok (v1 'matched_completed'); "
                                                                                         "a TRANSPORT comparison, not fully read documents"},
           "required_usable_matched": {"docs": req_usable, "n": len(req_usable), "under_R19_01": {"docs": req_usable19, "n": len(req_usable19)}},
           "field_specific_matched": field_sets,
           # the reviewer's contract reads this key: now the correctly defined set (all required fields usable in both arms)
           "matched_completed": req_usable,
           # the stored page fields per document / arm (as recorded; the reviewer's contract reads 'fields') and the transport state
           "coverage_planned": {d: {a: {"transport": coverage[d][a]["transport"], "fields": coverage[d][a]["fields"]} for a in ("S", "T2")} for d in planned}}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "CONT-METRICS.v2.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "CONT-COVERAGE.v2.json").write_text(json.dumps({"result_version": RESULT_VERSION, "coverage": coverage}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
deltas = {"result_version": RESULT_VERSION, "all_planned_recovery_changed": False,
          "v1_matched_completed": v1["matched_completed"], "v2_no_transport_stop_subgroup": no_stop,
          "v2_required_usable_matched": req_usable, "v2_required_usable_matched_under_R19_01": req_usable19,
          "removed_from_the_completed_claim": sorted(set(v1["matched_completed"]) - set(req_usable)),
          "per_document_state": {d: {arm: {"v1_state": v1["coverage_planned"][d][arm]["state"], "v2_transport": coverage[d][arm]["transport"],
                                             "v2_all_required_usable": coverage[d][arm]["all_required_usable"],
                                             "v2_all_required_usable_under_R19_01": coverage[d][arm]["all_required_usable_under_R19_01"]}
                                     for arm in ("S", "T2")} for d in planned}}
(OUT / "V1-TO-V2-DELTAS.json").write_text(json.dumps(deltas, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
short = lambda ds: [d.split("/")[-1][:28] for d in ds]
print("no_transport_stop", len(no_stop), short(no_stop))
print("required_usable", len(req_usable), short(req_usable), "| under R19-01", len(req_usable19), short(req_usable19))
for f, v in field_sets.items():
    print(f, "read both", v["read_in_both_arms"]["n"], short(v["read_in_both_arms"]["docs"]), "| usable both", v["usable_in_both_arms"]["n"], "| R19-01", v["usable_in_both_arms_under_R19_01"]["n"])
    print("    recovery (read both)", v["read_in_both_arms"]["recovery"])
print("field counts", json.dumps(field_counts))
