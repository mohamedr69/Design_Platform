"""Derive rescore9.py (evaluator .9, frozen-r10) from Review 09's rescore8.py: same runs, contexts and controls."""
import pathlib

s = pathlib.Path("C:/t/iso/work/r9/rescore8.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 09: every stored output re-scored with evaluator .8 (from the frozen worktree C:/t/iso/frozen-r9),',
     '"""Review 10: every stored output re-scored with evaluator .9 (from the frozen worktree C:/t/iso/frozen-r10),'),
    ('compared with the evaluator .7 result of the same run (C:/t/iso/work/r8/eval7).', 'compared with the evaluator .8 result of the same run (C:/t/iso/work/r9/eval8).'),
    ('overwritten: new files under C:/t/iso/work/r9/eval8.', 'overwritten: new files under C:/t/iso/work/r10/eval9.'),
    ('sys.path.insert(0, "C:/t/iso/frozen-r9/backend")', 'sys.path.insert(0, "C:/t/iso/frozen-r10/backend")'),
    ('OUT = Path("C:/t/iso/work/r9/eval8")', 'OUT = Path("C:/t/iso/work/r10/eval9")'),
    ('"vs_evaluator_7": compare(result, f"C:/t/iso/work/r8/eval7/{name}.json")', '"vs_evaluator_8": compare(result, f"C:/t/iso/work/r9/eval8/{name}.json")'),
    ('"vs_evaluator_7": compare(result, f"C:/t/iso/work/r8/eval7/matched-{name.split()[0]}.json")',
     '"vs_evaluator_8": compare(result, f"C:/t/iso/work/r9/eval8/matched-{name.split()[0]}.json")'),
    ("v.get('vs_evaluator_7', '-')", "v.get('vs_evaluator_8', '-')"),
    ("| vs .7: {v.get", "| vs .8: {v.get"),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
# .8 already carries target / association on judgements; .9 adds target_revision / context_identity: set those apart
old = '''                j.pop("target", None)
                j.pop("association", None)'''
assert old in s
s = s.replace('j.pop("association", None)', 'j.pop("association", None)\n                j.pop("target_revision", None)\n                j.pop("context_identity", None)')
s = s.replace('''    """The .8 result without its evaluator stamp and without what .8 adds to judgements (`target`, `association`,
    compared apart in DELTAS), for comparison with .7 -- both carry the context and the per-document AI state."""''',
              '''    """Both results without their evaluator stamp and without the association metadata on judgements (`target`,
    `association`, `target_revision`, `context_identity` -- compared apart), for comparison of the scoring itself."""''')
# strip the same metadata from the stored .8 result before comparing
s = s.replace('''    old.pop("evaluator", None)
    a, b = strip(new), json.loads(json.dumps(old, default=str))''', '''    old.pop("evaluator", None)
    a, b = strip(new), strip(old)''')
pathlib.Path("C:/t/iso/work/r10/rescore9.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
