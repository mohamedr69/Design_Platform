import pathlib

s = pathlib.Path("C:/t/iso/work/r10/freeze_r10.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 10 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 09 candidate,\nkept as history),',
     '"""Review 11 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 10 candidate,\nkept as history),'),
    ('OUT = Path("C:/t/iso/work/r10/freeze")', 'OUT = Path("C:/t/iso/work/r11/freeze")'),
    ('BASE = "689d95e53cc369c2397600daf2a46a3de93d5214"', 'BASE = "a34d3f8c0af7b6877eafd9f58cfede8a73c595a3"'),
    ('(OUT / "candidate-r10.diff")', '(OUT / "candidate-r11.diff")'),
    ('(OUT / "FREEZE-R10.json")', '(OUT / "FREEZE-R11.json")'),
    ('''    "history_kept": {"689d95e": "Review 09 candidate (frozen-r9, the tree Review 10 inspected, unchanged)",
                     "e02a8c1": "Review 08 candidate", "review09 package": "docs/milestones/M2/real-project-pilot/review09 (unchanged)"},''',
     '''    "history_kept": {"a34d3f8": "Review 10 candidate (frozen-r10, the tree Review 11 inspected, unchanged)",
                     "689d95e": "Review 09 candidate", "review10 package": "docs/milestones/M2/real-project-pilot/review10 (unchanged)"},'''),
    ('''for name, path in (("frozen-r10", "C:/t/iso/frozen-r10"), ("frozen-r9 (reviewed Review 09 tree)", "C:/t/iso/frozen-r9"),''',
     '''for name, path in (("frozen-r11", "C:/t/iso/frozen-r11"), ("frozen-r10 (reviewed Review 10 tree)", "C:/t/iso/frozen-r10"),'''),
    ('''    "versions": {"reader": "evidence-reader-2026-09-29.5 (selection / association only)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",
                 "evaluator": "m2-pilot-eval-2026-09-29.9", "ledger": "ai-ledger-2026-09-29.2 (unchanged)", "parser": "parse-2026-09-29.9 (unchanged)"},''',
     '''    "versions": {"reader": "evidence-reader-2026-09-29.6 (association context, attempt order)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",
                 "evaluator": "m2-pilot-eval-2026-09-29.9 (unchanged)", "ledger": "ai-ledger-2026-09-29.2 (unchanged)", "parser": "parse-2026-09-29.9 (unchanged)"},'''),
    ('"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r10 has no .env"',
     '"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r11 has no .env"'),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r11/freeze_r11.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
