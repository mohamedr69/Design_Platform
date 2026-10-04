"""Review 08: every stored output re-scored with evaluator .7, each with the AI context its run manifest declares, and
compared with the evaluator .6 result of the same run (C:/t/iso/work/r7/eval5, C:/t/iso/work/r7/matched). Nothing
overwritten: new files under C:/t/iso/work/r8/eval7. Negative controls score a run under a context it did not run in."""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
sys.path.insert(0, r"C:\t\iso\work\r7")
from scripts import m2_eval5 as ev  # noqa: E402

# rescore5's run table and label restriction only: its source up to the scoring loop (importing it would re-score
# and overwrite the stored .6 results)
_src = Path("C:/t/iso/work/r7/rescore5.py").read_text(encoding="utf-8")
_ns: dict = {"__file__": "rescore5.py"}
exec(compile(_src[:_src.index("summary = {}")].replace("extra = sys.argv[1:]", "extra = []"), "rescore5.py (table)", "exec"), _ns)
r5 = type("R5", (), _ns)
for _p in ("default", "promoted"):   # the review 07 frozen deterministic runs (scored in review 07 through rescore5's extra arguments)
    r5.RUNS += [(f"r7-det9-pilot-{_p}", r5.GOLD, r5.PAGES, Path(f"C:/t/r6/det9-pilot/out/rows-{_p}.json"), None),
                (f"r7-det9-holdout-{_p}", r5.HOLD, r5.HOLD_PAGES, Path(f"C:/t/r6/det9-holdout/out/rows-{_p}.json"), None)]

OUT = Path(r"C:\t\iso\work\r8\eval7")
OUT.mkdir(parents=True, exist_ok=True)
MATCHED = json.load(open(r"C:\t\iso\work\r7\matched\MATCHED-DECLARATION.json", encoding="utf-8"))

DET = {"variant": None, "declared": "no AI stage in this run"}
CONTEXT = {  # from each run's RUN-default.json / rows (profile) and the review 06 package (variant)
    "r6-ai-ev0-eligible-default": DET, "r6-ai-ev0-ep29076-default": DET,
    "r6-ai-ev1-eligible-default": {"variant": "EV1", "profile": "default", "accept_unknown_profile": True,
                                   "declared": "review 06 AI-EV1 (default profile; flat envelopes store no profile)"},
    "r6-ai-ev1-ep29076-default": {"variant": "EV1", "profile": "default", "accept_unknown_profile": True,
                                  "declared": "review 06 AI-EV1 (default profile; flat envelopes store no profile)"},
    "r6-ai-ev2-ep29076-default": {"variant": "EV2", "profile": "default", "accept_unknown_profile": True,
                                  "declared": "review 06 AI-EV2 (RUN-default.json: variant EV2, profile default; flat envelopes store no profile)"},
}
CONTROLS = {  # a context the run did not run in: its AI evidence must not be scored
    "control-r6-ai-ev1-eligible-without-legacy-declaration": ("r6-ai-ev1-eligible-default", {"variant": "EV1", "profile": "default"}),
    "control-r6-ai-ev1-eligible-as-EV2": ("r6-ai-ev1-eligible-default", {"variant": "EV2", "profile": "default", "accept_unknown_profile": True}),
}


def strip(result):
    """The .7 result without what .7 adds (the context and per-document AI state), for comparison with .6."""
    r = copy.deepcopy(result)
    r.pop("ai_context", None)
    r.pop("evaluator", None)
    r["totals"].pop("ai_evidence_states", None)
    for d in r["documents"]:
        d.pop("ai_evidence_state", None)
    return json.loads(json.dumps(r, default=str))


def compare(new, old_path):
    if not Path(old_path).exists():
        return "no .6 result stored"
    old = json.load(open(old_path, encoding="utf-8"))
    old.pop("evaluator", None)
    a, b = strip(new), json.loads(json.dumps(old, default=str))
    if a == b:
        return "identical"
    diffs = [k for k in set(a["totals"]) | set(b["totals"]) if a["totals"].get(k) != b["totals"].get(k)]
    return {"differs_in_totals": sorted(diffs), "documents_differing": sum(1 for x, y in zip(a["documents"], b["documents"]) if x != y)}


def headline(t):
    return {"register_critical": len(t["register"]["critical"]), "evidence_critical": len(t["evidence"]["critical"]),
            "ai_critical": len(t["ai"]["critical"]), "introduced_ai_errors": len(t["introduced_ai_errors"]),
            "raw_observed_errors": len(t["raw"]["observed_errors"]), "ai_evidence_states": t.get("ai_evidence_states")}


summary = {"evaluator": ev.EVALUATOR_VERSION, "runs": {}, "matched": {}, "controls": {}}
for name, labels, pages, rows_path, eps in r5.RUNS:
    if not rows_path.exists():
        summary["runs"][name] = {"not_run": str(rows_path)}
        continue
    rows = json.load(open(rows_path, encoding="utf-8"))
    if eps:
        labels_, pages_ = r5.restrict(labels, pages, eps)
        rows = {k: v for k, v in rows.items() if any(k.replace("\\", "/").startswith(f"EP-{e}/") for e in eps)}
    else:
        labels_, pages_ = labels, pages
    ctx = CONTEXT.get(name, DET)
    result = ev.evaluate(labels_, pages_, rows, (pages_ or {}).get("page1_corrections"), ai_context=ctx)
    json.dump(result, open(OUT / f"{name}.json", "w", encoding="utf-8"), indent=1, default=str)
    summary["runs"][name] = {"ai_context": ctx, **headline(result["totals"]), "vs_evaluator_6": compare(result, rf"C:\t\iso\work\r7\eval5\{name}.json")}
    for cname, (base, cctx) in CONTROLS.items():
        if base == name:
            c = ev.evaluate(labels_, pages_, rows, (pages_ or {}).get("page1_corrections"), ai_context=cctx)
            summary["controls"][cname] = {"ai_context": cctx, **headline(c["totals"])}

docs = {d.replace("\\", "/") for d in MATCHED["selection"]["files_sha256"]}
labels = {**r5.GOLD, "documents": [d for d in r5.GOLD["documents"] if d["doc"].replace("\\", "/") in docs]}
plabels = {**r5.PAGES, "documents": {k: v for k, v in r5.PAGES["documents"].items() if k.replace("\\", "/") in docs}}
for name, path, ctx, old in [("model-disabled (det9)", r"C:\t\r6\det9-pilot\out\rows-default.json", DET, "eval6-model-disabled.json"),
                             ("AI-EV0", r"C:\t\r7\m-ev0\out\rows-default.json", DET, "eval6-AI-EV0.json"),
                             ("AI-EV1", r"C:\t\r7\m-ev1\out\rows-default.json", {"variant": "EV1", "profile": "default", "declared": "matched run declaration: default profile, EV1"}, "eval6-AI-EV1.json"),
                             ("AI-EV2", r"C:\t\r7\m-ev2\out\rows-default.json", {"variant": "EV2", "profile": "default", "declared": "matched run declaration: default profile, EV2"}, "eval6-AI-EV2.json")]:
    rows = {k: v for k, v in json.load(open(path, encoding="utf-8")).items() if k.replace("\\", "/") in docs}
    result = ev.evaluate(labels, plabels, rows, plabels.get("page1_corrections"), ai_context=ctx)
    json.dump(result, open(OUT / f"matched-{name.split()[0]}.json", "w", encoding="utf-8"), indent=1, default=str)
    summary["matched"][name] = {"ai_context": ctx, **headline(result["totals"]), "vs_evaluator_6": compare(result, rf"C:\t\iso\work\r7\matched\{old}")}
    if name == "AI-EV1":
        for cname, cctx in [("control-matched-EV1-as-EV2", {"variant": "EV2", "profile": "default"}),
                            ("control-matched-EV1-as-promoted", {"variant": "EV1", "profile": "promoted"})]:
            c = ev.evaluate(labels, plabels, rows, plabels.get("page1_corrections"), ai_context=cctx)
            summary["controls"][cname] = {"ai_context": cctx, **headline(c["totals"])}

json.dump(summary, open(OUT / "SUMMARY.json", "w", encoding="utf-8"), indent=1, default=str)
for section in ("runs", "matched", "controls"):
    for name, v in summary[section].items():
        if "not_run" in v:
            print(section, name, "NOT RUN")
            continue
        print(f"{section:8s} {name:52s} reg {v['register_critical']} evid {v['evidence_critical']} ai {v['ai_critical']} intro {v['introduced_ai_errors']} "
              f"states {v['ai_evidence_states']} | vs .6: {v.get('vs_evaluator_6', '-')}")
