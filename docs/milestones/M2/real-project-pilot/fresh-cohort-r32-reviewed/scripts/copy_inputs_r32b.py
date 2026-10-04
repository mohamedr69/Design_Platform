"""ORCH-02.1 (R32APPLY-IMPL) step 1: verbatim copies of the frozen draft, review folder and packet inputs.

Never writes into the frozen packet or the frozen review folder. Refuses to overwrite.
"""
import hashlib
import json
import os
import shutil
import sys

PACKET = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32"
REVIEW = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
          "master-roadmap/reviews/M2-label-review-r32-draft-1")
PKG = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed"
DRAFT_SHA = "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334"
PACKET_FILES = ["LABEL-CONVENTIONS-R32.md", "FROZEN-SELECTION.json", "SOURCE-MANIFEST.json",
                "AUTHORIZATION-2026-10-02.md", "EVIDENCE-INDEX.json"]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_one(src, dst):
    if os.path.exists(dst):
        raise SystemExit("refusing to overwrite " + dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    s, d = sha256_file(src), sha256_file(dst)
    bs, bd = os.path.getsize(src), os.path.getsize(dst)
    if s != d or bs != bd:
        raise SystemExit("copy mismatch " + src)
    return {"bytes": bs, "source_sha256": s, "copy_sha256": d, "equal": True}


def dump(obj, path):
    if os.path.exists(path):
        raise SystemExit("refusing to overwrite " + path)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def main():
    # draft
    r = copy_one(PACKET + "/labels/R32-LABELS-DRAFT-1.json", PKG + "/labels/R32-LABELS-DRAFT-1.json")
    if r["copy_sha256"] != DRAFT_SHA:
        raise SystemExit("draft copy hash differs from frozen value")
    packet_rows = [dict(r, path="labels/R32-LABELS-DRAFT-1.json",
                        source=PACKET + "/labels/R32-LABELS-DRAFT-1.json",
                        copy="labels/R32-LABELS-DRAFT-1.json")]
    # review folder, whole tree
    review_rows = []
    for root, dirs, files in os.walk(REVIEW):
        dirs.sort()
        for name in sorted(files):
            src = os.path.join(root, name).replace("\\", "/")
            rel = os.path.relpath(src, REVIEW).replace("\\", "/")
            row = copy_one(src, PKG + "/review-r32-draft-1/" + rel)
            row["path"] = rel
            review_rows.append(row)
    dump({"source_folder": REVIEW, "copy_folder": "review-r32-draft-1/", "files": review_rows,
          "file_count": len(review_rows), "all_equal": all(x["equal"] for x in review_rows),
          "note": "verbatim byte copies (shutil.copyfile); this COPY-MANIFEST.json is not part of the source folder"},
         PKG + "/review-r32-draft-1/COPY-MANIFEST.json")
    # packet inputs
    for name in PACKET_FILES:
        row = copy_one(PACKET + "/" + name, PKG + "/packet-inputs/" + name)
        row.update({"path": name, "source": PACKET + "/" + name, "copy": "packet-inputs/" + name})
        packet_rows.append(row)
    dump({"source_packet": PACKET, "files": packet_rows, "all_equal": all(x["equal"] for x in packet_rows),
          "note": "verbatim byte copies from the frozen packet; the packet itself is unchanged"},
         PKG + "/packet-inputs/COPY-MANIFEST.json")
    print("review files", len(review_rows), "packet files", len(packet_rows), "all equal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
