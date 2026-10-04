"""ORCH-08C (R39HARNESS-IMPL): BINDING-MANIFEST-R39.json -- every harness file with its review38 and r39 hash, review38 and
review36 bound by hash, the carried inputs (re-hashed now; every one must equal the review38 binding), the application
sources the bounds and the request-path table read, the candidate and baseline HEADs. Written once; a changed file is a
new manifest, never an edit.

Usage: make_binding_r39.py <out json (new)>
Groups under "files" (preflight_r32.verify_binding re-hashes every one at every live invocation):
  harness_r39            C:/t/iso/work/r2x/r39/harness-r32 (the copy a live run executes)
  harness_r39_package    PILOT/review39/scripts/harness-r32 (byte-identical)
  harness_review38_base  PILOT/review38/scripts/harness-r32 (the frozen base, unchanged)
  inputs, carried, run_set, evaluator_offline_r32   as BINDING-MANIFEST-R38 (re-hashed: PACKET MISMATCH on any difference)
  review38, review36     the two frozen harness packages, by their manifests and binding manifests
  declaration_r32_superseded, reviews               the superseded declaration and the reviews this correction answers
  application_bound_sources       the files project_bounds_r32 reads (hash-checked there too)
  application_request_path_sources the files of REQUEST-PATHS.md (both trees)
  outputs                PILOT/review39/PROJECT-REQUEST-BOUNDS.json, RESUME-INVOCATIONS-R39.json, REQUEST-PATHS-STATIC.json"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r39")
PKG = PILOT / "review39"
R38_BINDING = (PILOT / "review38" / "BINDING-MANIFEST-R38.json", "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d")
R38_MANIFEST = (PILOT / "review38" / "evidence" / "EVIDENCE-MANIFEST.json", "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9")
R36_BINDING = (PILOT / "review36" / "BINDING-MANIFEST-R36.json", "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568")
R36_MANIFEST = (PILOT / "review36" / "evidence" / "EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0")
CARRIED_GROUPS = ("inputs", "carried", "run_set", "evaluator_offline_r32")
BASE_T, CAND_T = "C:/t/iso/frozen-r12/backend", "C:/t/iso/cand-r29/backend"
REQUEST_PATH_SOURCES = [f"{BASE_T}/app/services/document_processing.py", f"{BASE_T}/app/services/shop_drawings.py",
                        f"{BASE_T}/app/services/drawing_ai_review.py", f"{BASE_T}/app/ai/submittal_reader.py", f"{BASE_T}/app/compliance/assist.py",
                        f"{BASE_T}/app/core/config.py", f"{BASE_T}/app/ai/provider.py", f"{BASE_T}/app/services/document_sync.py",
                        f"{CAND_T}/app/ai/evidence_reader.py", f"{CAND_T}/app/core/config.py", f"{CAND_T}/app/ai/provider.py",
                        f"{CAND_T}/app/services/shop_drawings.py", f"{CAND_T}/app/services/drawing_ai_review.py"]


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(folder) -> dict:
    return {p.as_posix(): sha(p) for p in sorted(pathlib.Path(folder).iterdir()) if p.is_file()}


def head(repo):
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    h = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"], capture_output=True, text=True, env=env).stdout.strip()
    dirty = subprocess.run(["git", "-C", repo, "status", "--porcelain"], capture_output=True, text=True, env=env).stdout.strip()
    return {"tree": repo, "head": h, "clean": not dirty}


def main(out):
    out = pathlib.Path(out)
    if out.exists():
        raise SystemExit("refused: a binding manifest is written once")
    for p, want in (R38_BINDING, R38_MANIFEST, R36_BINDING, R36_MANIFEST):
        if sha(p) != want:
            raise SystemExit(f"PACKET MISMATCH: {p}")
    r38 = json.loads(R38_BINDING[0].read_text(encoding="utf-8"))
    files = {}
    for g in CARRIED_GROUPS:
        grp = {}
        for p, want in r38["files"][g].items():
            got = sha(p)
            if got != want:
                raise SystemExit(f"PACKET MISMATCH: {g} {p}")
            grp[p] = got
        files[g] = grp
    files["harness_r39"] = tree(WORK / "harness-r32")
    files["harness_r39_package"] = tree(PKG / "scripts" / "harness-r32")
    files["harness_review38_base"] = tree(PILOT / "review38" / "scripts" / "harness-r32")
    if {pathlib.Path(p).name: h for p, h in files["harness_r39"].items()} != {pathlib.Path(p).name: h for p, h in files["harness_r39_package"].items()}:
        raise SystemExit("refused: the package harness copy differs from the work copy")
    files["review38"] = {p.as_posix(): sha(p) for p in (R38_BINDING[0], R38_MANIFEST[0], PILOT / "review38" / "CROSS-PAGE-WHATIF.json")}
    files["review36"] = {p.as_posix(): sha(p) for p in (R36_BINDING[0], R36_MANIFEST[0], PILOT / "review36" / "H1-WHATIF-RESULT.json")}
    files["declaration_r32_superseded"] = {p.as_posix(): sha(p) for p in (PILOT / "declaration-r32" / "FRESH-VALIDATION-DECLARATION-R32.json",
                                                                         PILOT / "declaration-r32" / "evidence" / "EVIDENCE-MANIFEST.json")}
    revs = [("34", "INDEPENDENT-REVIEW.md"), ("34", "FINDINGS.json"), ("35", "INDEPENDENT-REVIEW.md"), ("35", "FINDINGS.json"),
            ("36", "INDEPENDENT-VERIFICATION.md"), ("36", "FINDINGS.json"), ("37", "INDEPENDENT-VERIFICATION.md"), ("37", "FINDINGS.json"),
            ("38", "INDEPENDENT-VERIFICATION.md"), ("38", "FINDINGS.json"), ("39", "INDEPENDENT-VERIFICATION.md"), ("39", "FINDINGS.json"),
            ("39", "INDEPENDENT-PACKAGE-CHECK.json")]
    files["reviews"] = {p.as_posix(): sha(p) for p in [MR / "reviews" / f"M2-review-{n}" / f for n, f in revs]}
    sys.path.insert(0, str(WORK / "harness-r32"))
    import project_bounds_r32 as PB
    files["application_bound_sources"] = {str(p).replace("\\", "/"): want for p, want in PB.SOURCES.values()}
    for p, want in files["application_bound_sources"].items():
        if sha(p) != want:
            raise SystemExit(f"PACKET MISMATCH: {p}")
    files["application_request_path_sources"] = {p: sha(p) for p in REQUEST_PATH_SOURCES}
    files["outputs"] = {(PKG / n).as_posix(): sha(PKG / n) for n in ("PROJECT-REQUEST-BOUNDS.json", "RESUME-INVOCATIONS-R39.json", "REQUEST-PATHS-STATIC.json")}
    table = json.loads((WORK / "evidence" / "HARNESS-FILES-R38-R39.json").read_text(encoding="utf-8"))["files"]
    for n, rec in table.items():
        if files["harness_r39"].get((WORK / "harness-r32" / n).as_posix()) != rec["r39_sha256"]:
            raise SystemExit(f"refused: the file table is stale for {n}")
    cli = json.loads((WORK / "out" / "MODEL-ID-EVIDENCE.json").read_text(encoding="utf-8"))
    man = {"name": "ORCH-08C (R39HARNESS-IMPL) binding manifest: the r32 harness corrected after Verification 39 (review39)",
           "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "answers": ("Verification 39 R39-04 (major), R39-06, R39-08, R39-16, R39-15 (gate as a named constant; owner ruling A-10: C >= B only, "
                       "a change from plan v2, C >= R a mandatory diagnostic), R39-09 (model-identity evidence), R39-02 and R39-17 (records)"),
           "binds": {"review38": {"manifest": R38_MANIFEST[1], "binding": R38_BINDING[1]}, "review36": {"manifest": R36_MANIFEST[1], "binding": R36_BINDING[1]}},
           "supersedes": {"file": R38_BINDING[0].as_posix(), "sha256": R38_BINDING[1], "for": "the harness-r32 code; the carried groups are re-hashed and equal"},
           "candidate": head("C:/t/iso/cand-r29") | {"expected": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"},
           "baseline": head("C:/t/iso/frozen-r12") | {"expected": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"},
           "harness_files": table,
           "unchanged_from_review38": sorted(n for n, r in table.items() if r["status"] == "unchanged"),
           "changed_from_review38": sorted(n for n, r in table.items() if r["status"] == "changed"),
           "new_in_review39": sorted(n for n, r in table.items() if r["status"] == "new"),
           "run_set_sha256": "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8",
           "truth_sha256": "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064",
           "reference_set": {"name": "r32-labels-reviewed-2", "sha256": "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6",
                             "populations": {"identity": 57, "revision": 38, "decision": 38}},
           "contract": "r39-live-contract-4",
           "application_env": {"DRAWINGS_AI_REVIEW_ENABLED": "false"},
           "decision_coverage_gate": {"bound": "C_GE_B_ONLY", "authority": "owner ruling A-10 (2026-10-04)",
                                      "change_from_plan_v2": "plan v2 gated on C >= B and C >= R; C >= R is now a mandatory diagnostic, never eligibility"},
           "pinned_model_ids": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
           "compatible_limits_required_minimum": {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": 84, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": 84},
           "project_request_bounds_EP_27331": {"planning": 63.0, "structural": 160, "drawings_ai_enabled_alternative": 170},
           "sandbox_base": "declared by the declaration (run.sandbox_base); dry / tests default C:/t/r2x/r39-sandbox",
           "not_bound_but_recorded": {
               "claude_cli": {"path": cli["cli_file"], "bytes": cli["bytes"], "sha256": cli["sha256"], "embedded_version": cli["embedded_version"],
                              "why": "an external program: the runner records `claude --version` per invocation and refuses a different declared version"},
               "authority_register": {"path": (MR / "orchestrator" / "AUTHORITY-REGISTER.md").as_posix(),
                                      "sha256_at_binding": sha(MR / "orchestrator" / "AUTHORITY-REGISTER.md"), "why": "append-only, updated by the orchestrator"},
               "decision_ledger": {"path": (MR / "orchestrator" / "DECISION-LEDGER.md").as_posix(),
                                   "sha256_at_binding": sha(MR / "orchestrator" / "DECISION-LEDGER.md"), "why": "append-only, updated by the orchestrator"}},
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed",
           "statement": "binds code and inputs only; it authorizes nothing (no run, budget, scope, token or default); M2 CHANGES STILL REQUIRED; M3 not started",
           "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "groups": {k: len(v) for k, v in files.items()}}))


if __name__ == "__main__":
    main(sys.argv[1])
