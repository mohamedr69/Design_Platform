"""The reviewer's Review 12 verify_package.py, pointed at the review12 package: same checks; only paths / key changed."""
import pathlib

src = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-12/verify_package.py")
s = src.read_text(encoding="utf-8")
subs = [
    ("ISO=Path('C:/t/iso/frozen-r11')", "ISO=Path('C:/t/iso/frozen-r12')"),
    ("PKG=ROOT/'docs/milestones/M2/real-project-pilot/review11'", "PKG=ROOT/'docs/milestones/M2/real-project-pilot/review12'"),
    ("OUT=Path(__file__).parent", "OUT=Path('C:/t/iso/work/r12/verify')"),
    ("m['candidate']['changed_files_sha256_at_a977364']", "m['candidate']['changed_files_sha256_at_3d5607d']"),
    ("list((PKG/'evidence/suite').glob('*.xml'))+[OUT/'independent-suite.xml']",
     "list((PKG/'evidence/suite').glob('*.xml'))+list((PKG/'evidence/focused').glob('*.xml'))+list((PKG/'evidence/prior').glob('*.xml'))"),
]
for a, b in subs:
    assert s.count(a) == 1, a
    s = s.replace(a, b)
pathlib.Path("C:/t/iso/work/r12/verify_package_r12.py").write_text(s, encoding="utf-8", newline="\n")
print("ok")
