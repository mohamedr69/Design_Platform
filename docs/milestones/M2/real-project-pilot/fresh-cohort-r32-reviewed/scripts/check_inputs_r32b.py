"""ORCH-02.1 (R32APPLY-IMPL) step 0: recompute every frozen input hash.

Reads only; writes C:/t/iso/work/r2x/r32b/INPUT-HASH-CHECK.json.
Exit code 0 when every hash matches, 2 otherwise (PACKET MISMATCH).
"""
import datetime
import hashlib
import json
import os
import sys

PACKET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32"
REVIEW = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
          "master-roadmap/reviews/M2-label-review-r32-draft-1")
LEDGER_MD = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
OUT = "C:/t/iso/work/r2x/r32b/INPUT-HASH-CHECK.json"

EXPECTED = {
    PACKET + "/evidence/EVIDENCE-MANIFEST.json": "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed",
    PACKET + "/labels/R32-LABELS-DRAFT-1.json": "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334",
    PACKET + "/LABEL-CONVENTIONS-R32.md": "5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570",
    REVIEW + "/REVIEWER-RESPONSE.final.json": "920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b",
    REVIEW + "/REVIEWER-RESPONSE.json": "70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8",
    REVIEW + "/CRITIQUE.json": "ad6798dc9aba2b1bd20ec6f4db74fbe353bdad93e01144b3ee1d32ab48387eef",
    REVIEW + "/DISPOSITIONS.json": "e8828becdad00cec0ce18eec371fc1aeeb246496eda5e57aae71c5388e4d30a7",
    LEDGER_MD: "6e296c28160b138d140d6c6dd275e1cd41e0a19827b24136b76dbabbf33fa0d4",
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    rows = []
    ok = True
    for path, exp in EXPECTED.items():
        got = sha256_file(path) if os.path.isfile(path) else None
        match = got == exp
        ok = ok and match
        rows.append({"path": path, "expected_sha256": exp, "actual_sha256": got, "match": match})

    manifest_rows = []
    man_path = PACKET + "/evidence/EVIDENCE-MANIFEST.json"
    with open(man_path, "r", encoding="utf-8") as f:
        man = json.load(f)
    for rel, meta in sorted(man["files"].items()):
        p = PACKET + "/" + rel
        exists = os.path.isfile(p)
        got = sha256_file(p) if exists else None
        size = os.path.getsize(p) if exists else None
        match = got == meta["sha256"] and size == meta["bytes"]
        ok = ok and match
        manifest_rows.append({"path": rel, "expected_sha256": meta["sha256"], "actual_sha256": got,
                              "expected_bytes": meta["bytes"], "actual_bytes": size, "match": match})
    draft_bound = man.get("draft_labels_sha256") == EXPECTED[PACKET + "/labels/R32-LABELS-DRAFT-1.json"]
    ok = ok and draft_bound

    # sidecar hash files in the review folder (informational cross-check)
    sidecars = {}
    for name in ("RESPONSE.final.sha256", "RESPONSE.sha256"):
        p = REVIEW + "/" + name
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                sidecars[name] = f.read().strip()

    out = {
        "task": "ORCH-02.1 R32APPLY-IMPL step 0",
        "checked_at_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "frozen_files": rows,
        "packet_manifest": {"path": man_path, "listed_files": len(man["files"]),
                            "all_match": all(r["match"] for r in manifest_rows),
                            "manifest_binds_draft_sha256": draft_bound,
                            "files": manifest_rows},
        "review_sidecar_hash_files": sidecars,
        "result": "MATCH" if ok else "PACKET MISMATCH",
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print(out["result"], "frozen", sum(r["match"] for r in rows), "/", len(rows),
          "manifest", sum(r["match"] for r in manifest_rows), "/", len(manifest_rows))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
