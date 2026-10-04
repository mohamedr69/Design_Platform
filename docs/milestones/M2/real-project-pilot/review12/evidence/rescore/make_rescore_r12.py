"""Derive rescore_r12.py from Review 11's rescore_r11.py: same runs, contexts and controls; frozen-r12 (reader .7,
evaluator .9 unchanged); compared with the Review 11 results (reader .6)."""
import pathlib

s = pathlib.Path("C:/t/iso/work/r11/rescore_r11.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 11: every stored output re-scored with evaluator .9 and reader .6 (from the frozen worktree C:/t/iso/frozen-r11),',
     '"""Review 12: every stored output re-scored with evaluator .9 and reader .7 (from the frozen worktree C:/t/iso/frozen-r12),'),
    ('compared with the Review 10 result of the same run (reader .5, evaluator .9; C:/t/iso/work/r10/eval9).',
     'compared with the Review 11 result of the same run (reader .6, evaluator .9; C:/t/iso/work/r11/eval9-reader6).'),
    ('overwritten: new files under C:/t/iso/work/r11/eval9-reader6.', 'overwritten: new files under C:/t/iso/work/r12/eval9-reader7.'),
    ('sys.path.insert(0, "C:/t/iso/frozen-r11/backend")', 'sys.path.insert(0, "C:/t/iso/frozen-r12/backend")'),
    ('OUT = Path("C:/t/iso/work/r11/eval9-reader6")', 'OUT = Path("C:/t/iso/work/r12/eval9-reader7")'),
    ('"vs_review10": compare(result, f"C:/t/iso/work/r10/eval9/{name}.json")', '"vs_review11": compare(result, f"C:/t/iso/work/r11/eval9-reader6/{name}.json")'),
    ('"vs_review10": compare(result, f"C:/t/iso/work/r10/eval9/matched-{name.split()[0]}.json")',
     '"vs_review11": compare(result, f"C:/t/iso/work/r11/eval9-reader6/matched-{name.split()[0]}.json")'),
    ("v.get('vs_review10', '-')", "v.get('vs_review11', '-')"),
    ("| vs r10: {v.get", "| vs r11: {v.get"),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r12/rescore_r12.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
