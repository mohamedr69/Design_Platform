"""Assemble the review14 correction package (new folder; earlier packages untouched) and write EVIDENCE-MANIFEST.json."""
import datetime
import hashlib
import json
import pathlib
import shutil

H = pathlib.Path("C:/t/iso/work/r2x/r14")
W = pathlib.Path("C:/t/iso/work/r2x")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review14")
R = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14")
EV = PKG / "evidence"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def put(src, rel):
    dst = EV / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


for p in sorted(H.glob("*.py")) + sorted((H / "tests").glob("*.py")):
    put(p, f"r14/{p.relative_to(H).as_posix()}")
for n in ("FREEZE-R14.json", "REPRO-R14.json", "REPLAY-BOQ.json", "BINDING.json", "BINDING.defective-run-1.json", "BINDING-REGEN.json", "LITERAL-CHECK.json",
          "SHORTFALL-REALLOCATION-PROPOSAL.json", "BOQ-CANDIDATE-TRIAGE.json", "WORKLOAD-ESTIMATE.json", "bind-run-2.log", "regen.log", "rescore.log"):
    put(H / n, f"r14/{n}")
for p in sorted((H / "rescore").glob("*")):
    put(p, f"r14/rescore/{p.name}")
for p in sorted((H / "regression").glob("*")):
    put(p, f"r14/regression/{p.name}")
for p in sorted((W / "labels/r14").glob("*")):
    put(p, f"labels/r14/{p.name}")
# historical: the stored Review 13 BOQ runs, copied read-only, with the deviation marker
marker = {"marker": "HISTORICAL -- obtained with the per-document budget deviation (R14-01)", "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
          "runs": {}}
for tag, n in (("r2x-small-boq-B", 25), ("r2x-small-boq-C", 35)):
    for f in ("BOQ.json", "usage.json"):
        src = pathlib.Path(f"C:/t/r2x/runs/{tag}/out/{f}")
        put(src, f"historical/{tag}/{f}")
        marker["runs"].setdefault(tag, {})[f] = sha(src)
    marker["runs"][tag].update({"requests_on_one_document": n, "declared_per_document": 12,
                                "effective_budget": "12 calls and 120 s PER CHUNK of 11 rows (a fresh JobBudget per chunk, per-document stops cleared)",
                                "status": "exploratory evidence under a different effective budget; not comparable to a run under the declared contract",
                                "caps_not_exceeded": ["60 per project per rolling day (EP-8430 reached exactly 60)", "150 requests in the experiment scope (113 used)"],
                                "same_file_in_review13": f"review13/evidence/run/runs/{tag}/{'BOQ.json'}"})
(EV / "historical").mkdir(parents=True, exist_ok=True)
(EV / "historical/HISTORICAL-DEVIATION-MARKER.json").write_text(json.dumps(marker, indent=1) + "\n", encoding="utf-8")
rv = {"folder": str(R).replace("\\", "/"), "files": {p.relative_to(R).as_posix(): sha(p) for p in sorted(R.rglob("*")) if p.is_file()}}
(EV / "reviewer").mkdir(parents=True, exist_ok=True)
(EV / "reviewer/REVIEWER-FILES-SHA256.json").write_text(json.dumps(rv, indent=1) + "\n", encoding="utf-8")
man = {}
for p in sorted(PKG.rglob("*")):
    if p.is_file() and p.name not in ("EVIDENCE-MANIFEST.json",):
        man[p.relative_to(PKG).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review14", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 1), "MB")
