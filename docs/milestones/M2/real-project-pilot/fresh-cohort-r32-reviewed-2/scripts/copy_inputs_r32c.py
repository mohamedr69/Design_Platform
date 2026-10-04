"""ORCH-04.1 (R32APPLY2-IMPL) step 1: verbatim copies into the new package fresh-cohort-r32-reviewed-2.

Copies (byte copies, shutil.copyfile; refuses to overwrite; never writes into a source tree):
  labels/R32-LABELS-REVIEWED-1.json   from fresh-cohort-r32-reviewed/labels/
  labels/R32-LABELS-DRAFT-1.json      from fresh-cohort-r32/labels/
  review-33/                          the whole Review 33 folder, with review-33/COPY-MANIFEST.json
  packet-inputs/                      the whole fresh-cohort-r32-reviewed/packet-inputs/ folder, verbatim
Records labels and packet-inputs copies in evidence/COPY-MANIFEST.json (source and copy sha256).
"""
import hashlib
import json
import os
import shutil
import sys

PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
SRC = PILOT + "/fresh-cohort-r32-reviewed"
PACKET = PILOT + "/fresh-cohort-r32"
R33 = ("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/"
       "master-roadmap/reviews/M2-review-33")
PKG = PILOT + "/fresh-cohort-r32-reviewed-2"
FROZEN = {
    "labels/R32-LABELS-REVIEWED-1.json": (SRC + "/labels/R32-LABELS-REVIEWED-1.json",
                                          "00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779"),
    "labels/R32-LABELS-DRAFT-1.json": (PACKET + "/labels/R32-LABELS-DRAFT-1.json",
                                       "ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334"),
}
R33_FROZEN = {
    "INDEPENDENT-REVIEW.md": "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804",
    "ESCALATION-RULINGS.final.json": "e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0",
    "DISPOSITIONS.json": "ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b",
}


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
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n")


def tree(root):
    out = []
    for r, dirs, files in os.walk(root):
        dirs.sort()
        for name in sorted(files):
            src = os.path.join(r, name).replace("\\", "/")
            out.append((src, os.path.relpath(src, root).replace("\\", "/")))
    return out


def main():
    if os.path.exists(PKG + "/labels") or os.path.exists(PKG + "/review-33") or os.path.exists(PKG + "/packet-inputs"):
        raise SystemExit("refusing: package copy folders already exist")
    label_rows = []
    for rel, (src, exp) in FROZEN.items():
        row = copy_one(src, PKG + "/" + rel)
        if row["copy_sha256"] != exp:
            raise SystemExit("PACKET MISMATCH " + rel)
        row.update({"path": rel, "source": src, "copy": rel, "frozen_sha256": exp})
        label_rows.append(row)

    review_rows = []
    for src, rel in tree(R33):
        row = copy_one(src, PKG + "/review-33/" + rel)
        row["path"] = rel
        if rel in R33_FROZEN and row["copy_sha256"] != R33_FROZEN[rel]:
            raise SystemExit("PACKET MISMATCH review-33/" + rel)
        review_rows.append(row)
    dump({"source_folder": R33, "copy_folder": "review-33/", "files": review_rows, "file_count": len(review_rows),
          "all_equal": all(x["equal"] for x in review_rows),
          "frozen_sha256_checked": R33_FROZEN,
          "note": "verbatim byte copies (shutil.copyfile) of the whole Review 33 folder; this COPY-MANIFEST.json "
                  "is not part of the source folder"},
         PKG + "/review-33/COPY-MANIFEST.json")

    packet_rows = []
    for src, rel in tree(SRC + "/packet-inputs"):
        row = copy_one(src, PKG + "/packet-inputs/" + rel)
        row.update({"path": rel, "source": src, "copy": "packet-inputs/" + rel})
        packet_rows.append(row)

    dump({"groups": {
        "labels": {"files": label_rows, "all_equal": all(x["equal"] for x in label_rows),
                   "note": "verbatim byte copies of the frozen reviewed-1 and draft-1 labels"},
        "packet-inputs": {"source_folder": SRC + "/packet-inputs", "copy_folder": "packet-inputs/",
                          "files": packet_rows, "file_count": len(packet_rows),
                          "all_equal": all(x["equal"] for x in packet_rows),
                          "note": "the whole packet-inputs folder of fresh-cohort-r32-reviewed, copied verbatim "
                                  "(including its own COPY-MANIFEST.json, which records the original copy from the "
                                  "r32 packet)"}},
          "note": "copy record for labels/ and packet-inputs/; review-33/ has its own COPY-MANIFEST.json"},
         PKG + "/evidence/COPY-MANIFEST.json")
    print("labels", len(label_rows), "review-33 files", len(review_rows), "packet-inputs files", len(packet_rows),
          "all equal")
    return 0


if __name__ == "__main__":
    sys.exit(main())
