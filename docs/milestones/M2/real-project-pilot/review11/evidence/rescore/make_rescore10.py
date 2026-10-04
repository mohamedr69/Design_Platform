"""Derive rescore_r11.py from Review 10's rescore9.py: same runs, contexts and controls; frozen-r11 (reader .6,
evaluator .9 unchanged); compared with the Review 10 results (reader .5, evaluator .9)."""
import pathlib

s = pathlib.Path("C:/t/iso/work/r10/rescore9.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 10: every stored output re-scored with evaluator .9 (from the frozen worktree C:/t/iso/frozen-r10),',
     '"""Review 11: every stored output re-scored with evaluator .9 and reader .6 (from the frozen worktree C:/t/iso/frozen-r11),'),
    ('compared with the evaluator .8 result of the same run (C:/t/iso/work/r9/eval8).',
     'compared with the Review 10 result of the same run (reader .5, evaluator .9; C:/t/iso/work/r10/eval9).'),
    ('overwritten: new files under C:/t/iso/work/r10/eval9.', 'overwritten: new files under C:/t/iso/work/r11/eval9-reader6.'),
    ('sys.path.insert(0, "C:/t/iso/frozen-r10/backend")', 'sys.path.insert(0, "C:/t/iso/frozen-r11/backend")'),
    ('OUT = Path("C:/t/iso/work/r10/eval9")', 'OUT = Path("C:/t/iso/work/r11/eval9-reader6")'),
    ('"vs_evaluator_8": compare(result, f"C:/t/iso/work/r9/eval8/{name}.json")', '"vs_review10": compare(result, f"C:/t/iso/work/r10/eval9/{name}.json")'),
    ('"vs_evaluator_8": compare(result, f"C:/t/iso/work/r9/eval8/matched-{name.split()[0]}.json")',
     '"vs_review10": compare(result, f"C:/t/iso/work/r10/eval9/matched-{name.split()[0]}.json")'),
    ("v.get('vs_evaluator_8', '-')", "v.get('vs_review10', '-')"),
    ("| vs .8: {v.get", "| vs r10: {v.get"),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
# record the reader version with the evaluator version
old = 'summary = {"evaluator": ev.EVALUATOR_VERSION, "runs": {}, "matched": {}, "controls": {}}'
assert s.count(old) == 1
s = s.replace(old, 'from app.ai import evidence_reader as _er  # noqa: E402\nsummary = {"evaluator": ev.EVALUATOR_VERSION, "reader": _er.READER_VERSION, "runs": {}, "matched": {}, "controls": {}}')
pathlib.Path("C:/t/iso/work/r11/rescore_r11.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
