"""ORCH-05C (R34HARNESS-IMPL) preflight: recompute every frozen input hash named by the task and re-verify the package
manifests entry by entry. Read-only on all inputs. The AI ledger is opened ONLY as file:...?mode=ro with uri=True.
Exit 0 and print PACKET OK, or exit 2 and print PACKET MISMATCH with details.
Usage: preflight_inputs.py [--response-any]   (--response-any: after the single response-ledger append, check that the
       ledger still STARTS with the pre-append bytes instead of equalling them)"""
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
RESPONSE_BEFORE = "500d55f559f157a8ebbe695157d6c6cd3b83dac5c31e58820f871a4615d690ac"
RESPONSE_BEFORE_BYTES = 172015

EXPECTED = {
    PILOT + "/review33/evidence/EVIDENCE-MANIFEST.json": "c5001c95420ac76150f320f04b1edfc5785264d00662d97e8f92ec83c6c95919",
    PILOT + "/review33/BINDING-MANIFEST-R33.json": "d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e",
    PILOT + "/review31/evidence/EVIDENCE-MANIFEST.json": "d5fe164918741014ded7425cda7679bd310a97b07511dd85bb65ec642077c460",
    PILOT + "/fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json": "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6",
    PILOT + "/fresh-cohort-r32-reviewed-2/evidence/EVIDENCE-MANIFEST.json": "1f27a544fa9fb839f5ae9bed721f1e00e7d5cbe1f63f56dd5bbf6fa8086bdb76",
    PILOT + "/fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json": "15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed",
    MR + "/reviews/M2-review-34/INDEPENDENT-REVIEW.md": "75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47",
    MR + "/reviews/M2-review-34/FINDINGS.json": "af99a772cafac9ef24be67902e6769fb92f544be76df3ed2f25969c1642f9fd8",
    MR + "/reviews/M2-review-33/INDEPENDENT-REVIEW.md": "8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804",
    MR + "/AI-ACCURACY-POLICY.md": "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47",
    MR + "/AI-ACCURACY-POLICY-AMENDMENT-R32-01.md": "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6",
    # carried unchanged from review33 (full hashes recorded in BINDING-MANIFEST-R34.json)
    PILOT + "/review33/dry-run/TRUTH-R32.json": "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064",
    PILOT + "/review33/RUN-SET-PROPOSAL.json": "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8",
}
HEADS = {
    "C:/t/iso/cand-r29": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d",
    "C:/t/iso/frozen-r12": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
}
MANIFESTS = {
    PILOT + "/review33": 112,
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
    con = sqlite3.connect("file:" + path.replace("\\", "/") + "?mode=ro", uri=True)
    try:
        return {"entries": con.execute("select count(*) from entries").fetchone()[0],
                "scopes": con.execute("select count(*) from scopes").fetchone()[0],
                "limit_amendments": con.execute("select count(*) from limit_amendments").fetchone()[0],
                "scope_names_sha256": hashlib.sha256("|".join(r[0] for r in con.execute("select scope from scopes order by scope")).encode()).hexdigest()}
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
        elif sha256_file(p) != meta["sha256"]:
            bad.append((rel, "sha256 differs"))
    return len(files), bad


def verify_binding(path):
    man = json.load(open(path, encoding="utf-8"))
    bad = [p for files in man["files"].values() for p, want in files.items() if not os.path.exists(p) or sha256_file(p) != want]
    return sum(len(v) for v in man["files"].values()), bad


def main(response_any=False):
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
    n, bad = verify_binding(PILOT + "/review33/BINDING-MANIFEST-R33.json")
    report["review33_binding"] = {"files": n, "mismatches": bad}
    if bad or n != 68:
        problems.append("review33 binding: files=%d bad=%s" % (n, bad))
    report["ledger"] = ledger_counts()
    if (report["ledger"]["entries"], report["ledger"]["scopes"], report["ledger"]["limit_amendments"]) != (483, 17, 0):
        problems.append("ledger %s" % report["ledger"])
    raw = open(RESPONSE, "rb").read()
    report["response_sha256"] = hashlib.sha256(raw).hexdigest()
    if response_any:
        report["response_prefix_sha256"] = hashlib.sha256(raw[:RESPONSE_BEFORE_BYTES]).hexdigest()
        if report["response_prefix_sha256"] != RESPONSE_BEFORE:
            problems.append("response ledger prefix %s != %s" % (report["response_prefix_sha256"], RESPONSE_BEFORE))
    elif report["response_sha256"] != RESPONSE_BEFORE:
        problems.append("response ledger %s != %s" % (report["response_sha256"], RESPONSE_BEFORE))
    report["problems"] = problems
    print(json.dumps(report, indent=1, sort_keys=True))
    if problems:
        print("PACKET MISMATCH")
        return 2
    print("PACKET OK")
    return 0


if __name__ == "__main__":
    sys.exit(main("--response-any" in sys.argv))
