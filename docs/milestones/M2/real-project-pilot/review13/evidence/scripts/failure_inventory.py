"""M2 Round 2: source-backed failure inventory on EXPOSED data, from the reviewed baseline's stored evaluator outputs
(evaluator .9 + reader .7, C:/t/iso/work/r12/eval9-reader7 -- the accepted Review 12 re-score). Nothing is re-read.

Every clear, applicable labelled fact (identity / revision / decision of a labelled component) that the evidence layer
did not recover cleanly is put in exactly one category, first match wins:
  disputed_label        the page belongs to one of the eight unresolved Review 07 finding groups (DECIDE): truth open
  withheld_correct      the correct value was read but held (held_only) -- correct but withheld
  failed_reading        the document's execution was not complete (bounded / failed): the read stopped
  wrong_association     the page has readings of the field, but they were associated with another / no component
  missed_discovery      no reading of the field at all on that page
  literal_misread       an asserted wrong value that is no other component's identifier on the document
  association_swap      an asserted wrong value equal to another labelled component's value on the document
Critical errors (wrong automatic acceptances) and raw observed errors are listed as the evaluator reports them."""
import collections
import json
import pathlib

E = pathlib.Path("C:/t/iso/work/r12/eval9-reader7")
FIND = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review08/human-review-packet-v2/FINDINGS-INDEX.json")
OUT = pathlib.Path("C:/t/iso/work/r2x/failure-inventory")
RUNS = {"deterministic baseline, pilot (r7-det9, default)": "r7-det9-pilot-default.json",
        "deterministic baseline, holdout (r7-det9, default)": "r7-det9-holdout-default.json",
        "matched: model-disabled (det9)": "matched-model-disabled.json",
        "matched: AI-EV1 (default|EV1)": "matched-AI-EV1.json",
        "matched: AI-EV2 (default|EV2)": "matched-AI-EV2.json"}
FIELDS = ("identity", "revision", "decision")
groups = json.loads(FIND.read_text(encoding="utf-8"))["groups"]
decide_pages = {(i["doc"].replace("\\", "/"), int(i["page"])): g["group"] for g in groups if g["status"] == "unresolved" for i in g["items"]}
TRUTH_KEY = {"identity": "reference", "revision": "printed_revision", "decision": "decision"}

OUT.mkdir(parents=True, exist_ok=True)
summary = {}
examples = collections.defaultdict(list)
for label, name in RUNS.items():
    r = json.loads((E / name).read_text(encoding="utf-8"))
    counts = collections.defaultdict(collections.Counter)
    denominators = collections.Counter()
    for d in r["documents"]:
        doc = d["doc"].replace("\\", "/")
        ev = d["layers"]["evidence"]
        judged = ev["judged"]
        comps = ev["components"]
        other_values = collections.defaultdict(set)
        for c in comps:
            for f in FIELDS:
                v = (c["expected"] or {}).get(TRUTH_KEY[f])
                if v:
                    other_values[f].add(str(v).strip().upper())
        for idx, c in enumerate(comps):
            for f in FIELDS:
                status = c["fields"].get(f)
                if status in (None, "unscorable", "tn", "not_applicable"):
                    continue
                denominators[f] += 1
                if status == "recovered_clean":
                    counts[f]["recovered_clean"] += 1
                    continue
                page = c["page"]
                mine = [j for j in judged if j["field"] == f and j.get("expected") == idx]
                on_page = [j for j in judged if j["field"] == f and j.get("page") == page]
                if (doc, page) in decide_pages:
                    cat = "disputed_label"
                elif status == "held_only":
                    cat = "withheld_correct"
                elif d.get("execution") not in ("complete", None):
                    cat = "failed_reading"
                elif status in ("wrong_only", "recovered_mixed", "accepted_on_conflict", "fp"):
                    wrong = [j for j in mine if j["outcome"] in ("wrong", "held_wrong", "accepted_on_conflict", "fp")]
                    swap = any(str(j.get("value")).strip().upper() in other_values[f] for j in wrong)
                    cat = "association_swap" if swap else "literal_misread"
                    if status == "recovered_mixed":
                        cat += " (alongside a correct reading)"
                elif status == "missed":
                    cat = "wrong_association" if on_page else "missed_discovery"
                else:
                    cat = status
                counts[f][cat] += 1
                if len(examples[(label, f, cat)]) < 8:
                    examples[(label, f, cat)].append({"doc": doc, "page": page, "truth": (c["expected"] or {}).get(TRUTH_KEY[f]), "status": status,
                                                      "readings_on_page": sorted({f"{j.get('value')} [{j.get('state')}/{j.get('outcome')}]" for j in on_page})[:6],
                                                      "finding_group": decide_pages.get((doc, page)), "execution": d.get("execution")})
    t = r["totals"]
    summary[label] = {"denominators": dict(denominators), "by_field": {f: dict(counts[f]) for f in FIELDS},
                      "critical": [{k: c.get(k) for k in ("doc", "page", "field", "value", "truth", "outcome", "state")} for c in t["evidence"]["critical"]],
                      "observed_errors": len(t["evidence"]["observed_errors"])}
out = {"source": str(E), "evaluator": "m2-pilot-eval-2026-09-29.9 with evidence-reader-2026-09-29.7 (accepted Review 12 re-score)",
       "decide_groups": sorted(set(decide_pages.values())), "summary": summary,
       "examples": [{"run": k[0], "field": k[1], "category": k[2], "items": v} for k, v in examples.items()]}
(OUT / "FAILURE-INVENTORY.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for label, s in summary.items():
    print("==", label, "| denominators", s["denominators"], "| critical", len(s["critical"]), "| observed errors", s["observed_errors"])
    for f in FIELDS:
        print("   ", f, dict(sorted(s["by_field"][f].items(), key=lambda kv: -kv[1])))
