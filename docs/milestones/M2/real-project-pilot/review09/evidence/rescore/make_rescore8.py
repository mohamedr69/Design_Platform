"""Derive rescore8.py (evaluator .8, frozen-r9) from Review 08's rescore7.py: same runs, contexts and controls."""
import pathlib

s = pathlib.Path("C:/t/iso/work/r8/rescore7.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 08: every stored output re-scored with evaluator .7,', '"""Review 09: every stored output re-scored with evaluator .8 (from the frozen worktree C:/t/iso/frozen-r9),'),
    ('compared with the evaluator .6 result of the same run (C:/t/iso/work/r7/eval5, C:/t/iso/work/r7/matched).', 'compared with the evaluator .7 result of the same run (C:/t/iso/work/r8/eval7).'),
    ('overwritten: new files under C:/t/iso/work/r8/eval7.', 'overwritten: new files under C:/t/iso/work/r9/eval8.'),
    ('sys.path.insert(0, r"C:\\t\\iso\\ep-platform\\backend")', 'sys.path.insert(0, "C:/t/iso/frozen-r9/backend")'),
    ('OUT = Path(r"C:\\t\\iso\\work\\r8\\eval7")', 'OUT = Path("C:/t/iso/work/r9/eval8")'),
    ('"vs_evaluator_6": compare(result, rf"C:\\t\\iso\\work\\r7\\eval5\\{name}.json")', '"vs_evaluator_7": compare(result, f"C:/t/iso/work/r8/eval7/{name}.json")'),
    ('"vs_evaluator_6": compare(result, rf"C:\\t\\iso\\work\\r7\\matched\\{old}")', '"vs_evaluator_7": compare(result, f"C:/t/iso/work/r8/eval7/matched-{name.split()[0]}.json")'),
    ("v.get('vs_evaluator_6', '-')", "v.get('vs_evaluator_7', '-')"),
    ('''def strip(result):
    """The .7 result without what .7 adds (the context and per-document AI state), for comparison with .6."""
    r = copy.deepcopy(result)
    r.pop("ai_context", None)
    r.pop("evaluator", None)
    r["totals"].pop("ai_evidence_states", None)
    for d in r["documents"]:
        d.pop("ai_evidence_state", None)
    return json.loads(json.dumps(r, default=str))''', '''def strip(result):
    """The .8 result without its evaluator stamp and without what .8 adds to judgements (`target`, `association`,
    compared apart in DELTAS), for comparison with .7 -- both carry the context and the per-document AI state."""
    r = json.loads(json.dumps(copy.deepcopy(result), default=str))
    r.pop("evaluator", None)
    for d in r["documents"]:
        for layer in d["layers"].values():
            for j in layer["judged"]:
                j.pop("target", None)
                j.pop("association", None)
            for key in ("critical", "observed_errors"):
                for j in layer.get(key) or []:
                    j.pop("target", None)
                    j.pop("association", None)
    for layer in ("raw", "evidence", "ai"):
        for key in ("critical", "observed_errors"):
            for j in r["totals"].get(layer, {}).get(key) or []:
                j.pop("target", None)
                j.pop("association", None)
    for j in r["totals"].get("introduced_ai_errors") or []:
        j.pop("target", None)
        j.pop("association", None)
    return r'''),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r9/rescore8.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
