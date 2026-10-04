"""ORCH-04.1 (R32APPLY2-IMPL) step 0: recompute every frozen input hash before acting.

Reads only; writes C:/t/iso/work/r2x/r32c/INPUT-HASH-CHECK.json.
Exit code 0 when every hash matches, 2 otherwise (PACKET MISMATCH).
"""
import datetime
import hashlib
import json
import os
import sys

PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
SRC = PILOT + "/fresh-cohort-r32-reviewed"
PACKET = PILOT + "/fresh-cohort-r32"
R33 = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
       "master-roadmap/reviews/M2-review-33")
TASK = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
        "master-roadmap/orchestrator/NEXT-BOUNDED-TASK.md")
RESPONSE_MD = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
OUT = "C:/t/iso/work/r2x/r32c/INPUT-HASH-CHECK.json"

# full values; the task text gives ESCALATION-RULINGS.final.json and DISPOSITIONS.json by 16-hex prefix only
EXPECTED = {
    SRC + "/evidence/EVIDENCE-MANIFEST.json": "64c0366737a5567284c6b862e5addbb0091f7bf98066745f081407a8b3fe31c6",
    SRC + "/labels/R32-LABELS-REVIEWED-1.json": "00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779",
    PACKET + "/labels/R32-LABELS-DRAFT-1.json": "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334",
    R33 + "/INDEPENDENT-REVIEW.md": "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804",
    RESPONSE_MD: "f0a4ffacba2c7765133475352e939a8149e119f7eb1efef73c2faec77774c65b",
}
PREFIX_ONLY = {
    R33 + "/ESCALATION-RULINGS.final.json": "e2fe503d96a3bc08",
    R33 + "/DISPOSITIONS.json": "ceb8fdcc6cc3e542",
}
SOURCE_MANIFEST_FILES = 45


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ok = True
    rows = []
    for path, exp in EXPECTED.items():
        got = sha256_file(path) if os.path.isfile(path) else None
        match = got == exp
        ok = ok and match
        rows.append({"path": path, "expected_sha256": exp, "actual_sha256": got, "match": match})
    recorded = {}
    for path, prefix in PREFIX_ONLY.items():
        got = sha256_file(path) if os.path.isfile(path) else None
        match = bool(got) and got.startswith(prefix)
        ok = ok and match
        recorded[os.path.basename(path)] = got
        rows.append({"path": path, "expected_sha256_prefix": prefix, "actual_sha256": got, "match": match,
                     "note": "the task states only this prefix; the full value is recorded here"})

    # the final review names the full hashes of its own rulings and dispositions; cross-check them
    with open(R33 + "/INDEPENDENT-REVIEW.md", encoding="utf-8") as f:
        review_text = f.read()
    named_in_review = {name: (sha in review_text) for name, sha in recorded.items() if sha}
    ok = ok and all(named_in_review.values())
    with open(R33 + "/REVIEW.sha256", encoding="utf-8") as f:
        review_sidecar = f.read().strip()
    sidecar_ok = review_sidecar.split()[0] == EXPECTED[R33 + "/INDEPENDENT-REVIEW.md"]
    ok = ok and sidecar_ok
    with open(R33 + "/ESCALATION-RULINGS.final.json", encoding="utf-8") as f:
        final_rulings = json.load(f)
    disp_bound = final_rulings.get("dispositions_sha256") == recorded.get("DISPOSITIONS.json")
    ok = ok and disp_bound

    # the source package manifest: re-hash every listed file
    man_path = SRC + "/evidence/EVIDENCE-MANIFEST.json"
    with open(man_path, encoding="utf-8") as f:
        man = json.load(f)
    mrows = []
    for rel, meta in sorted(man["files"].items()):
        p = SRC + "/" + rel
        exists = os.path.isfile(p)
        got = sha256_file(p) if exists else None
        size = os.path.getsize(p) if exists else None
        match = got == meta["sha256"] and size == meta["bytes"]
        ok = ok and match
        mrows.append({"path": rel, "expected_sha256": meta["sha256"], "actual_sha256": got,
                      "expected_bytes": meta["bytes"], "actual_bytes": size, "match": match})
    count_ok = len(man["files"]) == SOURCE_MANIFEST_FILES
    ok = ok and count_ok
    binds_reviewed = man.get("reviewed_labels_sha256") == EXPECTED[SRC + "/labels/R32-LABELS-REVIEWED-1.json"]
    binds_check = man.get("package_check_sha256") == sha256_file(SRC + "/evidence/PACKAGE-CHECK.json")
    ok = ok and binds_reviewed and binds_check

    out = {
        "task": "ORCH-04.1 R32APPLY2-IMPL step 0",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_files": rows,
        "full_hashes_recorded": recorded,
        "full_hashes_named_in_INDEPENDENT-REVIEW.md": named_in_review,
        "review_sidecar_REVIEW.sha256": {"content": review_sidecar, "matches_review_sha256": sidecar_ok},
        "escalation_rulings_final_binds_dispositions_sha256": disp_bound,
        "task_definition": {"path": TASK, "sha256": sha256_file(TASK), "note": "recorded for reference, not frozen"},
        "source_manifest": {"path": man_path, "listed_files": len(man["files"]),
                            "expected_listed_files": SOURCE_MANIFEST_FILES,
                            "all_match": all(r["match"] for r in mrows),
                            "binds_reviewed_labels_sha256": binds_reviewed,
                            "binds_package_check_sha256": binds_check,
                            "files": mrows},
        "result": "MATCH" if ok else "PACKET MISMATCH",
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print(out["result"], "frozen", sum(r["match"] for r in rows), "/", len(rows),
          "manifest", sum(r["match"] for r in mrows), "/", len(mrows), "recorded", recorded)
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
