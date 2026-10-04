import pathlib

s = pathlib.Path("C:/t/iso/work/r11/freeze_r11.py").read_text(encoding="utf-8")
subs = [
    ('"""Review 11 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 10 candidate,\nkept as history),',
     '"""Review 12 source freeze: candidate commit on the isolated scratch repository, its parent (the Review 11 candidate,\nkept as history),'),
    ('OUT = Path("C:/t/iso/work/r11/freeze")', 'OUT = Path("C:/t/iso/work/r12/freeze")'),
    ('BASE = "a34d3f8c0af7b6877eafd9f58cfede8a73c595a3"', 'BASE = "a9773642c099b0924099bd8a86a72d4507137429"'),
    ('(OUT / "candidate-r11.diff")', '(OUT / "candidate-r12.diff")'),
    ('(OUT / "FREEZE-R11.json")', '(OUT / "FREEZE-R12.json")'),
    ('''    "history_kept": {"a34d3f8": "Review 10 candidate (frozen-r10, the tree Review 11 inspected, unchanged)",
                     "689d95e": "Review 09 candidate", "review10 package": "docs/milestones/M2/real-project-pilot/review10 (unchanged)"},''',
     '''    "history_kept": {"a977364": "Review 11 candidate (frozen-r11, the tree Review 12 inspected, unchanged)",
                     "a34d3f8": "Review 10 candidate", "review11 package": "docs/milestones/M2/real-project-pilot/review11 (unchanged)"},'''),
    ('''for name, path in (("frozen-r11", "C:/t/iso/frozen-r11"), ("frozen-r10 (reviewed Review 10 tree)", "C:/t/iso/frozen-r10"),''',
     '''for name, path in (("frozen-r12", "C:/t/iso/frozen-r12"), ("frozen-r11 (reviewed Review 11 tree)", "C:/t/iso/frozen-r11"),'''),
    ('''    "versions": {"reader": "evidence-reader-2026-09-29.6 (association context, attempt order)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",''',
     '''    "versions": {"reader": "evidence-reader-2026-09-29.7 (legacy anchor reconstruction)", "policy": "evidence-policy-2026-09-29.4 (unchanged)",'''),
    ('"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r11 has no .env"',
     '"tests/conftest.py: temporary database, library, cache, uploads; AI off; frozen-r12 has no .env"'),
]
for a, b in subs:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r12/freeze_r12.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
