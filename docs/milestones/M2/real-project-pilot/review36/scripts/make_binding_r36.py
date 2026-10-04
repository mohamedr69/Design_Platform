"""ORCH-06C (R36HARNESS-IMPL): write PILOT/review36/BINDING-MANIFEST-R36.json (written once; a changed file is a new manifest).
Usage: make_binding_r36.py
"files" uses the runner's binding schema ({group: {absolute path: sha256}}, re-hashed by preflight_r32.verify_binding):
  harness_r36            every harness-r32 file of the r36 work copy C:/t/iso/work/r2x/r36/harness-r32 (40)
  harness_r36_package    the same 40 files as packaged in PILOT/review36/scripts/harness-r32 (byte-identical)
  harness_review34_base  the review34 harness the copy was made from (40), PILOT/review34/scripts/harness-r32
  review34               the review34 evidence manifest and binding manifest
  evaluator_offline_r32  its evidence manifest, binding, SYNTHETIC-PREDICTIONS.json and PARITY-MATRIX.json
  verification36         Independent Verification 36, its findings and its package check
  inputs, carried, run_set   carried from BINDING-MANIFEST-R34.json unchanged (every entry re-hashed equal)
Outside "files": the changed-module table (literal_compare_r32.py review34 -> r36 hash, the finding answered; the test
file with the review34 file as an exact byte prefix), the unchanged-module table (38 files, each equal to review34), the
candidate / baseline HEADs and cleanliness, and the statements."""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r36")
PKG = PILOT / "review36"
R34 = PILOT / "review34"
EO = PILOT / "evaluator-offline-r32"
V36 = MR / "reviews" / "M2-review-36"
OUT = PKG / "BINDING-MANIFEST-R36.json"
EXPECT = {R34 / "evidence/EVIDENCE-MANIFEST.json": "64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86",
          R34 / "BINDING-MANIFEST-R34.json": "3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27",
          EO / "evidence/EVIDENCE-MANIFEST.json": "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7",
          EO / "BINDING-MANIFEST-R35.json": "1de0773a23a38b39ffad770cf23d9d61d7e7ca1187693bbc29dbaccbcbbd62cb",
          EO / "SYNTHETIC-PREDICTIONS.json": "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774",
          EO / "PARITY-MATRIX.json": "73e189f2d0cfe05e55ba58837e991c008eaaf11fb928c300cf0670ead60aaccc",
          V36 / "INDEPENDENT-VERIFICATION.md": "f698c2ffebc44df0487edce762a3f1bd561b2cbbda7b3d844dbd7d6c15173a00",
          V36 / "FINDINGS.json": None, V36 / "INDEPENDENT-PACKAGE-CHECK.json": None}
OLD = {"literal_compare_r32.py": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6",
       "test_literal_compare_r32.py": "1d91cb5443ac5258b3fc60268b80a2815517badb5ebf5c77a3d0bf6b62831e4e"}
NEW = {"literal_compare_r32.py": "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09",
       "test_literal_compare_r32.py": "66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6"}
CANDIDATE_HEAD, BASELINE_HEAD = "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    if OUT.exists():
        raise SystemExit("refused: the binding manifest is written once")
    for p, want in EXPECT.items():
        if want and sha(p) != want:
            raise SystemExit(f"PACKET MISMATCH: {p}")
    r34m = json.loads((R34 / "BINDING-MANIFEST-R34.json").read_text(encoding="utf-8"))
    work = {p.name: sha(p) for p in sorted((WORK / "harness-r32").iterdir()) if p.is_file()}
    pkg = {p.name: sha(p) for p in sorted((PKG / "scripts" / "harness-r32").iterdir()) if p.is_file()}
    base = {p.name: sha(p) for p in sorted((R34 / "scripts" / "harness-r32").iterdir()) if p.is_file()}
    r34_manifest = json.loads((R34 / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    if any(r34_manifest[f"scripts/harness-r32/{n}"]["sha256"] != h for n, h in base.items()) or len(base) != 40:
        raise SystemExit("PACKET MISMATCH: review34 harness vs its manifest")
    if work != pkg or set(work) != set(base):
        raise SystemExit("the package harness differs from the work copy, or the file list differs from review34")
    differ = sorted(n for n in work if work[n] != base[n])
    if differ != sorted(OLD) or any(base[n] != OLD[n] or work[n] != NEW[n] for n in OLD):
        raise SystemExit(f"unexpected changed files: {differ}")
    old_test, new_test = (R34 / "scripts/harness-r32/test_literal_compare_r32.py").read_bytes(), (WORK / "harness-r32/test_literal_compare_r32.py").read_bytes()
    if not new_test.startswith(old_test):
        raise SystemExit("the review34 test file is not a byte prefix of the r36 test file")
    files = {"harness_r36": {(WORK / "harness-r32" / n).as_posix(): h for n, h in work.items()},
             "harness_r36_package": {(PKG / "scripts" / "harness-r32" / n).as_posix(): h for n, h in pkg.items()},
             "harness_review34_base": {(R34 / "scripts" / "harness-r32" / n).as_posix(): h for n, h in base.items()},
             "review34": {(R34 / "evidence/EVIDENCE-MANIFEST.json").as_posix(): EXPECT[R34 / "evidence/EVIDENCE-MANIFEST.json"],
                          (R34 / "BINDING-MANIFEST-R34.json").as_posix(): EXPECT[R34 / "BINDING-MANIFEST-R34.json"]},
             "evaluator_offline_r32": {p.as_posix(): EXPECT[p] for p in (EO / "evidence/EVIDENCE-MANIFEST.json", EO / "BINDING-MANIFEST-R35.json",
                                                                       EO / "SYNTHETIC-PREDICTIONS.json", EO / "PARITY-MATRIX.json")},
             "verification36": {p.as_posix(): sha(p) for p in (V36 / "INDEPENDENT-VERIFICATION.md", V36 / "FINDINGS.json", V36 / "INDEPENDENT-PACKAGE-CHECK.json")}}
    for group in ("inputs", "carried", "run_set"):
        files[group] = {}
        for p, want in r34m["files"][group].items():
            if sha(p) != want:
                raise SystemExit(f"PACKET MISMATCH: carried {group} {p}")
            files[group][p] = want
    heads = {}
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    for repo, want in (("C:/t/iso/cand-r29", CANDIDATE_HEAD), ("C:/t/iso/frozen-r12", BASELINE_HEAD)):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
        heads[repo] = {"head": head, "clean": dirty == "", "expected": want}
        if head != want or dirty:
            raise SystemExit(f"PACKET MISMATCH: {repo} head / cleanliness")
    man = {"name": "ORCH-06C (R36HARNESS-IMPL) binding manifest: the r32 harness with the H1 whitespace fix in literal_compare_r32.norm_revision",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
           "supersedes": {"file": "review34/BINDING-MANIFEST-R34.json", "sha256": EXPECT[R34 / "BINDING-MANIFEST-R34.json"],
                          "for": "the harness-r32 code; every other review34 binding entry under inputs / carried / run_set is carried unchanged"},
           "answers": "Independent Verification 36 (f698c2ff...3a00), finding R36-08 (major, CONFIRMED): H1 is a harness defect in "
                      "literal_compare_r32.norm_revision; condition 1 for ORCH-07",
           "changed_modules": {"literal_compare_r32.py": {"review34_sha256": OLD["literal_compare_r32.py"], "r36_sha256": NEW["literal_compare_r32.py"],
                                                          "change": "norm_revision only: after the unchanged Arabic branch, dash folding, upper-casing "
                                                                    "and the optional REVISION / REV / REV. / R / R. prefix, every whitespace character "
                                                                    "is removed before the number pattern 0*(\\d+) is matched; the fallback is unchanged; "
                                                                    "docstring added to the function; every other line of the module is unchanged",
                                                          "answers": "R36-08 (H1)"}},
           "changed_test_files": {"test_literal_compare_r32.py": {"review34_sha256": OLD["test_literal_compare_r32.py"],
                                                                  "r36_sha256": NEW["test_literal_compare_r32.py"],
                                                                  "change": "35 tests appended; the review34 file is an exact byte prefix (its 13 tests unchanged)"}},
           "unchanged_modules": {n: {"sha256": work[n], "review34_sha256": base[n], "unchanged": True} for n in sorted(work) if n not in OLD},
           "unchanged_statement": "the 38 files under unchanged_modules are byte-identical to PILOT/review34/scripts/harness-r32 (review34 manifest 64d5ba0d...)",
           "fixtures_sha256": EXPECT[EO / "SYNTHETIC-PREDICTIONS.json"], "parity_matrix_sha256": EXPECT[EO / "PARITY-MATRIX.json"],
           "evaluator_offline_r32_manifest_sha256": EXPECT[EO / "evidence/EVIDENCE-MANIFEST.json"],
           "review34_manifest_sha256": EXPECT[R34 / "evidence/EVIDENCE-MANIFEST.json"], "review34_binding_sha256": EXPECT[R34 / "BINDING-MANIFEST-R34.json"],
           "verification36_sha256": EXPECT[V36 / "INDEPENDENT-VERIFICATION.md"],
           "candidate": {"tree": "C:/t/iso/cand-r29", "head": CANDIDATE_HEAD, "observed": heads["C:/t/iso/cand-r29"]},
           "baseline": {"tree": "C:/t/iso/frozen-r12", "head": BASELINE_HEAD, "observed": heads["C:/t/iso/frozen-r12"]},
           "concentration_rule_version": r34m["concentration_rule_version"],
           "reference_set_statement": REFERENCE_SET_STATEMENT, "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), sum(len(v) for v in files.values()))


if __name__ == "__main__":
    main()
