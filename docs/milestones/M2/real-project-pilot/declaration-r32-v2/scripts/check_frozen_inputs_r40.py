"""ORCH-09 (R40DECL-IMPL): recompute every frozen input of the task table and print PACKET MATCH or PACKET MISMATCH.

Usage: check_frozen_inputs_r40.py <out json>
Read-only: files are hashed, the review39 / review38 / review36 / declaration-r32 / evaluator-offline-r32 / reviewed-2
manifests are re-verified entry by entry, the candidate and baseline HEADs and cleanliness are read with
GIT_OPTIONAL_LOCKS=0, the AI ledger is opened file:...?mode=ro (uri=True) only. Writes only <out json>.
Exit 0 on PACKET MATCH, 3 on PACKET MISMATCH."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import sys

PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
RESPONSE = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"

# (label, path, expected sha256 -- full, or (prefix, suffix) where the task gives an abbreviation)
FILES = [
    ("review39 manifest", f"{PILOT}/review39/evidence/EVIDENCE-MANIFEST.json", "2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990"),
    ("review39 BINDING-MANIFEST-R39.json", f"{PILOT}/review39/BINDING-MANIFEST-R39.json", "a6f703b427e59d47214a2f8e23f7af90263d19a93fcd35649cc3ead0b72c567b"),
    ("review39 work AUDIT-LOG.md (R40-20)", "C:/t/iso/work/r2x/r39/AUDIT-LOG.md", "62cac01271e46bbeb1fcdfe77afab6bbbe7ca7b6b79f493d090578210c9592d4"),
    ("review39 work PROGRESS.md (R40-20)", "C:/t/iso/work/r2x/r39/PROGRESS.md", "e0d6066792ac5e9f4755f83a278dce7b52d37a59cf313aa4e7ee2b61a39c3107"),
    ("Verification 40 INDEPENDENT-VERIFICATION.md", f"{MR}/reviews/M2-review-40/INDEPENDENT-VERIFICATION.md", "620ea60a63e871625c940f27ff50b2999d2403111b088275702eb68abf736cb2"),
    ("Verification 40 FINDINGS.json", f"{MR}/reviews/M2-review-40/FINDINGS.json", "f225540849a5097fa8c27e870b2001ca593b91735832e1424c0a19ce12d86e48"),
    ("Verification 40 INDEPENDENT-PACKAGE-CHECK.json", f"{MR}/reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK.json", "51222ad53fd3bf42a205ac0dc9c9e3f6bd5d65b0251fab1815b31c9216667c99"),
    ("Verification 39 INDEPENDENT-VERIFICATION.md", f"{MR}/reviews/M2-review-39/INDEPENDENT-VERIFICATION.md", ("5bb967f2", "6598")),
    ("Verification 38 INDEPENDENT-VERIFICATION.md", f"{MR}/reviews/M2-review-38/INDEPENDENT-VERIFICATION.md", ("006d0203", "f5c7")),
    ("review38 manifest", f"{PILOT}/review38/evidence/EVIDENCE-MANIFEST.json", ("07c2fb78", "8ce9")),
    ("review38 BINDING-MANIFEST-R38.json", f"{PILOT}/review38/BINDING-MANIFEST-R38.json", "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d"),
    ("review36 manifest", f"{PILOT}/review36/evidence/EVIDENCE-MANIFEST.json", ("5e950813", "9d0")),
    ("review36 BINDING-MANIFEST-R36.json", f"{PILOT}/review36/BINDING-MANIFEST-R36.json", ("5a1a6aad", "e568")),
    ("declaration-r32 manifest (superseded)", f"{PILOT}/declaration-r32/evidence/EVIDENCE-MANIFEST.json", ("59361b93", "e2c8")),
    ("declaration-r32 FRESH-VALIDATION-DECLARATION-R32.json (superseded)", f"{PILOT}/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json", ("38e08df9", "76b0")),
    ("RUN-SET-PROPOSAL.json (review34)", f"{PILOT}/review34/RUN-SET-PROPOSAL.json", "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"),
    ("TRUTH-R32.json (review34)", f"{PILOT}/review34/dry-run/TRUTH-R32.json", ("4e237a4e", "")),
    ("R32-LABELS-REVIEWED-2.json", f"{PILOT}/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json", "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    ("evaluator-offline-r32 manifest", f"{PILOT}/evaluator-offline-r32/evidence/EVIDENCE-MANIFEST.json", ("86dd81d3", "")),
    ("AI-ACCURACY-POLICY.md", f"{MR}/AI-ACCURACY-POLICY.md", ("7efa891b", "")),
    ("AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", f"{MR}/AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", ("815d43fd", "")),
]
# the review39 outputs bound by hash in the declaration: each must equal its entry in the review39 manifest
REVIEW39_OUTPUTS = ("PROJECT-REQUEST-BOUNDS.json", "RESUME-INVOCATIONS-R39.json", "VISIBILITY-RESULT.json", "MODEL-ID-EVIDENCE.md",
                    "MODEL-ID-EVIDENCE.json", "REQUEST-PATHS.md", "REQUEST-PATHS-STATIC.json", "DRAWINGS-AI-PROBE-R39.json",
                    "UNREAD-PAGES-PROBE-R39.json", "LIVE-RUN-CONTRACT.md", "REPORT-TEMPLATE.md", "SCORER-CHANGES.md", "CHANGE-RECORD-R39.md",
                    "VISIBILITY-REPORT.md", "evidence/SNAPSHOT-BEFORE.json")
MANIFESTS = {"review39": f"{PILOT}/review39", "review38": f"{PILOT}/review38", "review36": f"{PILOT}/review36",
             "declaration-r32": f"{PILOT}/declaration-r32", "evaluator-offline-r32": f"{PILOT}/evaluator-offline-r32",
             "fresh-cohort-r32-reviewed-2": f"{PILOT}/fresh-cohort-r32-reviewed-2"}
# files on disk that a frozen manifest does not list, known and disclosed before this task (R33-12: the PACKAGE-CHECK
# files of the cohort packets are not bound by their manifests); pinned by hash so any change is still a mismatch
KNOWN_UNLISTED = {"fresh-cohort-r32-reviewed-2": {"evidence/PACKAGE-CHECK.json": "1b807c404d426a65b3e316087fa85a431088ab19af4fa8dc8c115776da3756e2"}}
FILES.append(("fresh-cohort-r32-reviewed-2 manifest", f"{PILOT}/fresh-cohort-r32-reviewed-2/evidence/EVIDENCE-MANIFEST.json",
              "1f27a544fa9fb839f5ae9bed721f1e00e7d5cbe1f63f56dd5bbf6fa8086bdb76"))
REPOS = {"candidate": ("C:/t/iso/cand-r29", "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"),
         "baseline": ("C:/t/iso/frozen-r12", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3")}
RESPONSE_EXPECTED = ("caf949b2f878253049e0ae65421cad78b8d169009e3b2a024a4eb01d5aed10e4", 213865)


def sha(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _match(got: str, want) -> bool:
    if isinstance(want, tuple):
        return got.startswith(want[0]) and got.endswith(want[1])
    return got == want


def main(argv) -> int:
    out = {"taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "files": [], "manifests": {}, "review39_outputs": {},
           "authority_register": {}, "repos": {}, "ai_ledger": {}, "response_ledger": {}, "mismatches": []}
    for label, path, want in FILES:
        got = sha(path)
        ok = _match(got, want)
        out["files"].append({"label": label, "path": path, "sha256": got, "expected": want if isinstance(want, str) else f"{want[0]}...{want[1]}", "ok": ok})
        if not ok:
            out["mismatches"].append(label)
    for name, root in MANIFESTS.items():
        man = json.loads(pathlib.Path(root, "evidence", "EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))
        bad = [rel for rel, rec in man["files"].items()
               if not pathlib.Path(root, rel).is_file() or sha(pathlib.Path(root, rel)) != rec["sha256"] or pathlib.Path(root, rel).stat().st_size != rec["bytes"]]
        on_disk = sorted(p.relative_to(root).as_posix() for p in pathlib.Path(root).rglob("*") if p.is_file())
        known = KNOWN_UNLISTED.get(name, {})
        unlisted = [p for p in on_disk if p not in man["files"] and p != "evidence/EVIDENCE-MANIFEST.json"
                    and not (p in known and sha(pathlib.Path(root, p)) == known[p])]
        out["manifests"][name] = {"entries": len(man["files"]), "bad": bad, "unlisted": unlisted, "known_unlisted_pinned": sorted(known),
                                  "ok": not bad and not unlisted}
        if bad or unlisted:
            out["mismatches"].append(f"manifest {name}")
    r39 = json.loads(pathlib.Path(PILOT, "review39", "evidence", "EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    for rel in REVIEW39_OUTPUTS:
        got = sha(pathlib.Path(PILOT, "review39", rel))
        ok = r39.get(rel, {}).get("sha256") == got
        out["review39_outputs"][rel] = {"sha256": got, "bytes": pathlib.Path(PILOT, "review39", rel).stat().st_size, "in_review39_manifest": ok}
        if not ok:
            out["mismatches"].append(f"review39 output {rel}")
    snap = json.loads(pathlib.Path(PILOT, "review39", "evidence", "SNAPSHOT-BEFORE.json").read_text(encoding="utf-8"))
    out["review39_snapshot_before_taken_utc"] = snap.get("taken_utc")
    ar = f"{MR}/orchestrator/AUTHORITY-REGISTER.md"
    text = pathlib.Path(ar).read_text(encoding="utf-8")
    out["authority_register"] = {"path": ar, "sha256": sha(ar), "has_A09": "## A-09" in text, "has_A10": "## A-10" in text}
    if not (out["authority_register"]["has_A09"] and out["authority_register"]["has_A10"]):
        out["mismatches"].append("AUTHORITY-REGISTER lacks A-09 or A-10")
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    for name, (repo, want) in REPOS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
        out["repos"][name] = {"tree": repo, "head": head, "expected": want, "clean": not dirty}
        if head != want or dirty:
            out["mismatches"].append(f"repo {name}")
    con = sqlite3.connect(f"file:{LEDGER}?mode=ro", uri=True)
    try:
        out["ai_ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                            "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0], "opened": "file:...?mode=ro, uri=True"}
    finally:
        con.close()
    if (out["ai_ledger"]["entries"], out["ai_ledger"]["scopes"]) != (483, 17):
        out["mismatches"].append("AI ledger not 483/17")
    out["response_ledger"] = {"path": RESPONSE, "sha256": sha(RESPONSE), "bytes": pathlib.Path(RESPONSE).stat().st_size}
    out["response_ledger"]["ok"] = (out["response_ledger"]["sha256"], out["response_ledger"]["bytes"]) == RESPONSE_EXPECTED
    if len(argv) > 2 and argv[2] == "--after-append":
        # after this task's one append: the first 213,865 bytes still hash to caf949b2...
        with open(RESPONSE, "rb") as fh:
            prefix = fh.read(RESPONSE_EXPECTED[1])
        out["response_ledger"]["prefix_sha256"] = hashlib.sha256(prefix).hexdigest()
        out["response_ledger"]["ok"] = out["response_ledger"]["prefix_sha256"] == RESPONSE_EXPECTED[0]
    if not out["response_ledger"]["ok"]:
        out["mismatches"].append("response ledger")
    out["verdict"] = "PACKET MATCH" if not out["mismatches"] else "PACKET MISMATCH"
    pathlib.Path(argv[1]).write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"verdict": out["verdict"], "mismatches": out["mismatches"], "manifests": {k: (v["entries"], v["ok"]) for k, v in out["manifests"].items()},
                      "ai_ledger": out["ai_ledger"], "response": out["response_ledger"], "authority_register": out["authority_register"]["sha256"],
                      "r39_snapshot_before": out["review39_snapshot_before_taken_utc"]}))
    return 0 if not out["mismatches"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
