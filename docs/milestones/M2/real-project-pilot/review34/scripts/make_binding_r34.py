"""ORCH-05C: write BINDING-MANIFEST-R34.json (written once per freeze; a changed file is a new manifest, never an edit).
Usage: make_binding_r34.py <out path> <run-set proposal path (the review34 copy)>
Binds ("files", every entry re-hashed by the runner's preflight): every frozen input (inputs_r32.INPUTS), the Review 34
review and findings, the review33 manifest and binding, review31's harness originals, the harness-r33-base copy (review33's
37 harness files, the base of this correction), every harness-r32 source and test of this correction, the carried-unchanged
derived files (review34 copies) and the run-set proposal. Outside "files": the candidate / baseline HEADs, the
unchanged-module table (each carried module's hash equals its review33 hash), the changed-module table (review33 hash ->
review34 hash, with the Review 34 finding answered) and the rule version."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

R34 = pathlib.Path("C:/t/iso/work/r2x/r34")
sys.path.insert(0, str(R34 / "harness-r32"))
import concentration_r32 as K  # noqa: E402
import inputs_r32 as I  # noqa: E402

PKG = I.PILOT / "review34"
R33PKG = I.PILOT / "review33"
REVIEW34 = I.MR / "reviews" / "M2-review-34"
CARRY_MODULES = ["labels_adapter_r32.py", "literal_compare_r32.py", "converter_r32.py", "run_set_selector_r32.py", "sandbox_ingest_r32.py",
                 "capture_store.py", "state_check.py", "stop_rules.py"]
ALSO_UNCHANGED = ["lane_judge_r32.py", "inputs_r32.py", "coverage_v4.py", "score_lane_r32.py", "synthetic_r32.py", "tripwire_r32.py",
                  "test_capture_store.py", "test_converter_r32.py", "test_labels_adapter_r32.py", "test_lane_judge_r32.py", "test_literal_compare_r32.py",
                  "test_run_set_selector_r32.py", "test_state_check.py", "test_stop_rules.py", "test_tripwire_r32.py"]
CARRY_FILES = {"dry-run/TRUTH-R32.json": "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064",
               "RUN-SET-PROPOSAL.json": "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8",
               "LABELS-R32-EVAL-INPUT.json": None, "CONVERTER-RECONCILIATION.json": None, "ADAPTER-CONTRACT.md": None, "RUN-SET-RULE.md": None}
CHANGED = {
    "concentration_r32.py": "RC-1 (R34-01) rule version 2, no net-gain floor; RC-6 (R34-08) failures once per (document, field)",
    "score_bcr_r32.py": "RC-2 (R34-02) candidate-level outcome",
    "dispatch_guard_r32.py": "RC-3 (R34-03) pinned path, declaration hash, owner token digest, one-run nonce consumed into the run folder",
    "allowance_r32.py": "RC-4 (R34-04) one allowance per run key; caps and day limit bound in the file; capture store bound to the same key",
    "runner_r32.py": "RC-3/RC-4/RC-5 run/resume entry points, one run folder per declaration, no --auth-path, live ledger check, no default switches in live mode",
    "lane_r32.py": "RC-3/RC-5 the same preflight and guard in every live lane; switch and provider environment verification; RC-4 bound allowance and store",
    "sandbox_child_r32.py": "path only: the r34 sandbox base (task write rule)",
    "r32_test_helpers.py": "test helpers: temporary live declarations and fake ledgers (no authorization file)",
    "test_concentration_r32.py": "RC-1/RC-6 tests", "test_score_bcr_r32.py": "RC-1 justification, RC-2 and RC-6 tests",
    "test_dispatch_guard_r32.py": "RC-3 tests", "test_allowance_r32.py": "RC-4 tests", "test_runner_r32.py": "RC-3/RC-4/RC-5 tests",
    "test_sandbox_ingest_r32.py": "path only: the r34 sandbox base",
}
NEW = {"preflight_r32.py": "RC-3/RC-4/RC-5 the shared live preflight, declaration contract, ledger-scope and live ledger checks",
       "r34_scenarios.py": "Review 34 scenario structures over the real truth and run set (synthetic lanes made from the truth)",
       "test_preflight_r32.py": "RC-4/RC-5 tests"}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main(out, run_set):
    files = {"inputs": {}, "review": {}, "review33": {}, "review31_harness": {}, "harness_r33_base": {}, "harness_r32": {}, "carried": {}, "run_set": {}}
    for name, (path, expected) in sorted(I.INPUTS.items()):
        if pathlib.Path(path).is_dir():
            for f in sorted(pathlib.Path(path).glob("*.py")):
                files["inputs"][f.as_posix()] = sha(f)
            continue
        got = sha(path)
        if expected and got != expected:
            raise SystemExit(f"PACKET MISMATCH: {name} {got} != {expected}")
        files["inputs"][pathlib.Path(path).as_posix()] = got
    for f, want in (("INDEPENDENT-REVIEW.md", "75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47"),
                    ("FINDINGS.json", "af99a772cafac9ef24be67902e6769fb92f544be76df3ed2f25969c1642f9fd8")):
        if sha(REVIEW34 / f) != want:
            raise SystemExit(f"PACKET MISMATCH: Review 34 {f}")
        files["review"][(REVIEW34 / f).as_posix()] = want
    for f, want in (("evidence/EVIDENCE-MANIFEST.json", "c5001c95420ac76150f320f04b1edfc5785264d00662d97e8f92ec83c6c95919"),
                    ("BINDING-MANIFEST-R33.json", "d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e")):
        if sha(R33PKG / f) != want:
            raise SystemExit(f"PACKET MISMATCH: review33 {f}")
        files["review33"][(R33PKG / f).as_posix()] = want
    for f in sorted((I.PILOT / "review31" / "scripts" / "harness").glob("*.py")):
        files["review31_harness"][f.as_posix()] = sha(f)
    base = {}
    for f in sorted((R34 / "harness-r33-base").glob("*.py")):
        files["harness_r33_base"][f.as_posix()] = base[f.name] = sha(f)
    r33pkg = {f.name: sha(f) for f in (R33PKG / "scripts" / "harness-r32").glob("*.py")}
    if base != r33pkg:
        raise SystemExit("PACKET MISMATCH: harness-r33-base differs from PILOT/review33/scripts/harness-r32")
    now = {}
    for f in sorted((R34 / "harness-r32").glob("*.py")):
        files["harness_r32"][f.as_posix()] = now[f.name] = sha(f)
    carried_files = {}
    for rel, want in CARRY_FILES.items():
        a, b = sha(PKG / rel), sha(R33PKG / rel)
        if a != b or (want and a != want):
            raise SystemExit(f"PACKET MISMATCH: carried {rel} {a} / review33 {b} / expected {want}")
        files["carried"][(PKG / rel).as_posix()] = a
        carried_files[rel] = {"sha256": a, "equals_review33": True}
    files["run_set"][pathlib.Path(run_set).as_posix()] = sha(run_set)
    unchanged = {n: {"sha256": now[n], "review33_sha256": base[n], "unchanged": now[n] == base[n]} for n in CARRY_MODULES + ALSO_UNCHANGED}
    if not all(v["unchanged"] for v in unchanged.values()):
        raise SystemExit(f"a module to be carried unchanged differs: {[n for n, v in unchanged.items() if not v['unchanged']]}")
    changed = {n: {"review33_sha256": base[n], "review34_sha256": now[n], "answers": why} for n, why in CHANGED.items()}
    if any(v["review33_sha256"] == v["review34_sha256"] for v in changed.values()):
        raise SystemExit("a module listed as changed is unchanged")
    new = {n: {"review34_sha256": now[n], "answers": why} for n, why in NEW.items()}
    if set(now) != set(base) | set(new) or set(now) != set(CARRY_MODULES + ALSO_UNCHANGED) | set(CHANGED) | set(NEW):
        raise SystemExit(f"harness file list mismatch: {sorted(set(now) ^ (set(CARRY_MODULES + ALSO_UNCHANGED) | set(CHANGED) | set(NEW)))}")
    heads = {}
    for repo in ("C:/t/iso/cand-r29", "C:/t/iso/frozen-r12"):
        head = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
        heads[repo] = {"head": head, "clean": dirty == ""}
    if any(not v["clean"] or v["head"] != w for v, w in ((heads["C:/t/iso/cand-r29"], I.CANDIDATE_HEAD), (heads["C:/t/iso/frozen-r12"], I.BASELINE_HEAD))):
        raise SystemExit("PACKET MISMATCH: candidate or baseline HEAD / cleanliness")
    man = {"name": "Review 34 correction (ORCH-05C) binding manifest: concentration rule v2, candidate-level outcome, pinned one-run dispatch guard, "
                   "per-declaration allowance / capture store / resume, live lane verification, failures once per document",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
           "supersedes": {"file": "review33/BINDING-MANIFEST-R33.json", "sha256": "d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e"},
           "answers": "Independent Review 34 (75061210...8bc8f47) required corrections RC-1 to RC-6",
           "concentration_rule_version": K.RULE_VERSION,
           "candidate": {"tree": "C:/t/iso/cand-r29", "head": I.CANDIDATE_HEAD, "observed": heads["C:/t/iso/cand-r29"]},
           "baseline": {"tree": "C:/t/iso/frozen-r12", "head": I.BASELINE_HEAD, "observed": heads["C:/t/iso/frozen-r12"]},
           "policy_sha256": I.INPUTS["policy"][1], "policy_amendment_sha256": I.INPUTS["policy_amendment"][1],
           "reviewed2_labels_sha256": I.INPUTS["reviewed2_labels"][1], "reviewed2_package_manifest_sha256": I.INPUTS["reviewed2_manifest"][1],
           "packet_manifest_sha256": I.INPUTS["packet_manifest"][1], "review31_manifest_sha256": I.INPUTS["review31_manifest"][1],
           "review33_sha256": I.INPUTS["review33"][1], "review34_sha256": "75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47",
           "unchanged_modules": unchanged, "changed_modules": changed, "new_modules": new, "carried_files": carried_files,
           "unchanged_statement": ("the modules and files under unchanged_modules and carried_files are byte-identical to review33 "
                                   "(PILOT/review33/scripts/harness-r32 and the review33 package files)"),
           "reference_set_statement": I.REFERENCE_SET_STATEMENT, "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    if pathlib.Path(out).exists():
        raise SystemExit("refused: the binding manifest is written once per freeze")
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), sum(len(v) for v in files.values()))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
