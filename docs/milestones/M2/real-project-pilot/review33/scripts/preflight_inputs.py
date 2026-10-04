"""ORCH-05.1 preflight: recompute every frozen input hash named in the task and
re-verify the three package manifests entry by entry. Read-only on all inputs.
The AI ledger is opened ONLY with file:...?mode=ro and uri=True.
Exit 0 and print PACKET OK, or exit 2 and print PACKET MISMATCH with details."""
import hashlib
import json
import os
import sqlite3
import subprocess
import sys

PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
RESPONSE = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md"

EXPECTED = {
    PILOT + "/review31/evidence/EVIDENCE-MANIFEST.json": "d5fe164918741014ded7425cda7679bd310a97b07511dd85bb65ec642077c460",
    PILOT + "/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json": "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6",
    PILOT + "/fresh-cohort-r32-reviewed-2/evidence/EVIDENCE-MANIFEST.json": "1f27a544fa9fb839f5ae9bed721f1e00e7d5cbe1f63f56dd5bbf6fa8086bdb76",
    PILOT + "/fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json": "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed",
    MR + "/reviews/M2-review-33/INDEPENDENT-REVIEW.md": "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804",
    MR + "/AI-ACCURACY-POLICY.md": "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47",
    MR + "/AI-ACCURACY-POLICY-AMENDMENT-R32-01.md": "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6",
}
HEADS = {
    "C:/t/iso/cand-r29": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d",
    "C:/t/iso/frozen-r12": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
}
MANIFESTS = {
    PILOT + "/review31": 58,
    PILOT + "/fresh-cohort-r32-reviewed-2": None,
    PILOT + "/fresh-cohort-r32": None,
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def ledger_counts(path=LEDGER):
    uri = "file:" + path.replace("\\", "/") + "?mode=ro"
    con = sqlite3.connect(uri, uri=True)
    try:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table'")]
        out = {"tables": sorted(tables)}
        if "entries" in tables:
            out["entries"] = con.execute("select count(*) from entries").fetchone()[0]
        if "scopes" in tables:
            out["scopes"] = con.execute("select count(*) from scopes").fetchone()[0]
        return out
    finally:
        con.close()


def verify_manifest(pkg_dir):
    man = json.load(open(pkg_dir + "/evidence/EVIDENCE-MANIFEST.json", encoding="utf-8"))
    files = man.get("files", {})
    bad = []
    for rel, meta in sorted(files.items()):
        p = pkg_dir + "/" + rel
        if not os.path.exists(p):
            bad.append((rel, "missing"))
            continue
        got = sha256_file(p)
        if got != meta["sha256"]:
            bad.append((rel, "sha256 %s != %s" % (got, meta["sha256"])))
    return len(files), bad


def main():
    problems = []
    report = {"hashes": {}, "heads": {}, "manifests": {}}
    for p, exp in EXPECTED.items():
        got = sha256_file(p)
        report["hashes"][p] = got
        if got != exp:
            problems.append("hash %s: %s != %s" % (p, got, exp))
    for repo, exp in HEADS.items():
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        report["heads"][repo] = {"head": head, "clean": dirty == ""}
        if head != exp or dirty:
            problems.append("head %s: %s clean=%s" % (repo, head, dirty == ""))
    for pkg, expected_n in MANIFESTS.items():
        n, bad = verify_manifest(pkg)
        report["manifests"][pkg] = {"entries": n, "mismatches": bad}
        if bad or (expected_n is not None and n != expected_n):
            problems.append("manifest %s: entries=%d bad=%s" % (pkg, n, bad))
    report["ledger"] = ledger_counts()
    if report["ledger"].get("entries") != 483 or report["ledger"].get("scopes") != 17:
        problems.append("ledger %s" % report["ledger"])
    report["response_sha256"] = sha256_file(RESPONSE)
    report["problems"] = problems
    print(json.dumps(report, indent=1, sort_keys=True))
    if problems:
        print("PACKET MISMATCH")
        return 2
    print("PACKET OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
