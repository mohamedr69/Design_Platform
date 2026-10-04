"""Assemble docs/milestones/M2/real-project-pilot/fresh-cohort-r32/ (NEW folder, never rebuilt in place); the evidence
manifest is written LAST. Copies only. Images stay in the isolated staging area and are bound by sha256 (EVIDENCE-INDEX)."""
import hashlib
import json
import pathlib
import shutil
import sys

R = pathlib.Path(__file__).resolve().parent
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
if PKG.exists():
    sys.exit("the package folder exists; never rebuilt in place")


def cp(src, dst):
    d = PKG / dst
    d.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, d)


for f in ("PREPARATION-REPORT.md", "REVIEWER-PACKET.md", "COMMANDS-AND-AUDIT-LOG.md"):
    cp(R / "pkg-src" / f, f)
for f in ("AUTHORIZATION-2026-10-02.md", "PRE-AUTHORIZATION-HASH-CHECK.json", "PROJECT-AND-CONTRACTOR-VERIFICATION.csv", "PROJECT-VERIFICATION.json", "FROZEN-SELECTION.json",
          "SOURCE-MANIFEST.json", "RENDERS.json", "CROPS.jsonl", "EVIDENCE-INDEX.json", "LABEL-CONVENTIONS-R32.md", "LABEL-CONVENTIONS-R32.sha256", "FIELD-POPULATION.json"):
    cp(R / f, f)
for f in ("R32-LABELS-DRAFT-1.json", "DRAFT-PROJECTION.json"):
    cp(R / "labels" / f, f"labels/{f}")
for f in ("PAGE-FIELD-WORKLIST.csv", "DOCUMENT-FIELD-WORKLIST.csv", "DOCUMENT-QUESTIONS.json", "REVIEWER-RESPONSE-TEMPLATE.json"):
    cp(R / "review" / f, f"review/{f}")
for p in sorted((R / "drafts").glob("F*.json")):
    cp(p, f"labels/drafts/{p.name}")
for f in ("verify_projects_r32.py", "select_pool_r32.py", "stage_r32.py", "render_r32.py", "crop_r32.py", "words_r32.py", "validate_drafts_r32.py", "assemble_draft_r32.py",
          "make_review_packet_r32.py", "package_r32.py", "verify_r32_packet.py", "append_response_r32.py"):
    cp(R / f, f"scripts/{f}")
for p in sorted((R / "lib").glob("*.py")):
    cp(p, f"scripts/lib/{p.name}")
man = {p.relative_to(PKG).as_posix(): {"sha256": sha(p), "bytes": p.stat().st_size} for p in sorted(PKG.rglob("*")) if p.is_file()}
(PKG / "evidence").mkdir(exist_ok=True)
(PKG / "evidence/EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "fresh-cohort-r32 (cohort preparation, initial pool drafted; awaiting independent label review)",
                                                                 "draft_labels_sha256": sha(R / "labels" / "R32-LABELS-DRAFT-1.json"),
                                                                 "staging": "C:/t/r2x/r32-stage (files, renders, crops; bound by SOURCE-MANIFEST / EVIDENCE-INDEX)", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 3), "MB")
