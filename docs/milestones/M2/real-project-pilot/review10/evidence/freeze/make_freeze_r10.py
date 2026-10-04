import pathlib

s = pathlib.Path("C:/t/iso/work/r9/freeze_r9.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 09 source freeze: candidate commit on the isolated scratch repository, its parent chain back to the Review 08\ncandidate (kept as history),',
     '"""Review 10 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 09 candidate,\nkept as history),'),
    ('OUT = Path("C:/t/iso/work/r9/freeze")', 'OUT = Path("C:/t/iso/work/r10/freeze")'),
    ('BASE = "e02a8c1b9ef093534df4bd427c7f2c5e7fc1403c"', 'BASE = "689d95e53cc369c2397600daf2a46a3de93d5214"'),
    ('(OUT / "candidate-r9.diff")', '(OUT / "candidate-r10.diff")'),
    ('(OUT / "FREEZE-R9.json")', '(OUT / "FREEZE-R10.json")'),
    ('''    "superseded_freeze": {"ec4f0fc": "first freeze; superseded by the final commit before any result was reported (unscored-page judgements "
                                      "dropped target / association -- no score affected)"},\n''', ''),
    ('''    "history_kept": {"e02a8c1": "Review 08 candidate (frozen-r8, the tree Review 09 inspected, unchanged)",
                     "1455f8b": "Review 07 evaluator amendment", "c9a1a14": "Review 07 frozen application",
                     "review08 package": "docs/milestones/M2/real-project-pilot/review08 (unchanged)"},''',
     '''    "history_kept": {"689d95e": "Review 09 candidate (frozen-r9, the tree Review 10 inspected, unchanged)",
                     "e02a8c1": "Review 08 candidate", "review09 package": "docs/milestones/M2/real-project-pilot/review09 (unchanged)"},'''),
    ('''for name, path in (("frozen-r9", "C:/t/iso/frozen-r9"), ("frozen-r8 (reviewed Review 08 tree)", "C:/t/iso/frozen-r8"),''',
     '''for name, path in (("frozen-r10", "C:/t/iso/frozen-r10"), ("frozen-r9 (reviewed Review 09 tree)", "C:/t/iso/frozen-r9"),'''),
    ('''    "versions": {"reader": "evidence-reader-2026-09-29.4", "policy": "evidence-policy-2026-09-29.4", "evaluator": "m2-pilot-eval-2026-09-29.8",
                 "ledger": "ai-ledger-2026-09-29.2 (unchanged; docstring wording only)", "parser": "parse-2026-09-29.9 (unchanged)"},''',
     '''    "versions": {"reader": "evidence-reader-2026-09-29.5 (selection / association only)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",
                 "evaluator": "m2-pilot-eval-2026-09-29.9", "ledger": "ai-ledger-2026-09-29.2 (unchanged)", "parser": "parse-2026-09-29.9 (unchanged)"},'''),
    ('"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r9 has no .env"',
     '"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r10 has no .env"'),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r10/freeze_r10.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
