"""ORCH-08 (R38HARNESS-IMPL): BINDING-MANIFEST-R38.json -- every harness file with its review36 and r38 hash, the bound
inputs (re-hashed now; every one must still equal the review36 binding where it carries one), the application sources the
request bounds read, the candidate and baseline HEADs. Written once; a changed file is a new manifest, never an edit.

Usage: make_binding_r38.py <out json (new)>
Groups under "files" (preflight_r32.verify_binding re-hashes every one at every live invocation):
  harness_r38            C:/t/iso/work/r2x/r38/harness-r32 (the copy a live run executes)
  harness_r38_package    PILOT/review38/scripts/harness-r32 (byte-identical)
  harness_review36_base  PILOT/review36/scripts/harness-r32 (the frozen base, unchanged)
  inputs, carried, run_set, evaluator_offline_r32   as BINDING-MANIFEST-R36 (re-hashed: PACKET MISMATCH on any difference)
  review36, declaration_r32_superseded, reviews     the frozen packages and reviews this correction answers
  application_bound_sources                        the candidate / baseline files project_bounds_r32 reads (hash-checked there too)
  outputs                PILOT/review38/PROJECT-REQUEST-BOUNDS.json, CROSS-PAGE-WHATIF.json"""
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
WORK = pathlib.Path("C:/t/iso/work/r2x/r38")
PKG = PILOT / "review38"
R36_BINDING = (PILOT / "review36" / "BINDING-MANIFEST-R36.json", "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568")
CARRIED_GROUPS = ("inputs", "carried", "run_set", "evaluator_offline_r32")


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
    raw = R36_BINDING[0].read_bytes()
    if hashlib.sha256(raw).hexdigest() != R36_BINDING[1]:
        raise SystemExit("PACKET MISMATCH: BINDING-MANIFEST-R36")
    r36 = json.loads(raw.decode("utf-8"))
    files = {}
    for g in CARRIED_GROUPS:
        grp = {}
        for p, want in r36["files"][g].items():
            got = sha(p)
            if got != want:
                raise SystemExit(f"PACKET MISMATCH: {g} {p}")
            grp[p] = got
        files[g] = grp
    files["harness_r38"] = tree(WORK / "harness-r32")
    files["harness_r38_package"] = tree(PKG / "scripts" / "harness-r32")
    files["harness_review36_base"] = tree(PILOT / "review36" / "scripts" / "harness-r32")
    if {pathlib.Path(p).name: h for p, h in files["harness_r38"].items()} != {pathlib.Path(p).name: h for p, h in files["harness_r38_package"].items()}:
        raise SystemExit("refused: the package harness copy differs from the work copy")
    files["review36"] = {p.as_posix(): sha(p) for p in (PILOT / "review36" / "BINDING-MANIFEST-R36.json", PILOT / "review36" / "evidence" / "EVIDENCE-MANIFEST.json",
                                                       PILOT / "review36" / "H1-WHATIF-RESULT.json")}
    files["declaration_r32_superseded"] = {p.as_posix(): sha(p) for p in (PILOT / "declaration-r32" / "FRESH-VALIDATION-DECLARATION-R32.json",
                                                                         PILOT / "declaration-r32" / "evidence" / "EVIDENCE-MANIFEST.json")}
    files["reviews"] = {p.as_posix(): sha(p) for p in [MR / "reviews" / f"M2-review-{n}" / f for n, f in
                                                       (("34", "INDEPENDENT-REVIEW.md"), ("34", "FINDINGS.json"), ("35", "INDEPENDENT-REVIEW.md"),
                                                        ("35", "FINDINGS.json"), ("36", "INDEPENDENT-VERIFICATION.md"), ("36", "FINDINGS.json"),
                                                        ("37", "INDEPENDENT-VERIFICATION.md"), ("37", "FINDINGS.json"), ("38", "INDEPENDENT-VERIFICATION.md"),
                                                        ("38", "FINDINGS.json"))]}
    sys.path.insert(0, str(WORK / "harness-r32"))
    import project_bounds_r32 as PB
    files["application_bound_sources"] = {str(p).replace("\\", "/"): want for p, want in PB.SOURCES.values()}
    for p, want in files["application_bound_sources"].items():
        if sha(p) != want:
            raise SystemExit(f"PACKET MISMATCH: {p}")
    files["outputs"] = {(PKG / n).as_posix(): sha(PKG / n) for n in ("PROJECT-REQUEST-BOUNDS.json", "CROSS-PAGE-WHATIF.json")}
    table = json.loads((WORK / "evidence" / "HARNESS-FILES-R36-R38.json").read_text(encoding="utf-8"))["files"]
    for n, rec in table.items():
        if files["harness_r38"].get((WORK / "harness-r32" / n).as_posix()) != rec["r38_sha256"]:
            raise SystemExit(f"refused: the file table is stale for {n}")
    man = {"name": "ORCH-08 (R38HARNESS-IMPL) binding manifest: the r32 harness corrected for owner decision A-09 (review38)",
           "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "answers": "A-09 points 1-7 (owner decision after Verification 38); findings R38-08, R38-09, R38-10, R38-13, R34-06, R35-09, R35-10, R36-09",
           "supersedes": {"file": R36_BINDING[0].as_posix(), "sha256": R36_BINDING[1], "for": "the harness-r32 code; the carried groups are re-hashed and equal"},
           "candidate": head("C:/t/iso/cand-r29") | {"expected": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d"},
           "baseline": head("C:/t/iso/frozen-r12") | {"expected": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"},
           "harness_files": table,
           "unchanged_from_review36": sorted(n for n, r in table.items() if r["status"] == "unchanged"),
           "changed_from_review36": sorted(n for n, r in table.items() if r["status"] == "changed"),
           "new_in_review38": sorted(n for n, r in table.items() if r["status"] == "new"),
           "run_set_sha256": "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8",
           "truth_sha256": "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064",
           "reference_set": {"name": "r32-labels-reviewed-2", "sha256": "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6",
                             "populations": {"identity": 57, "revision": 38, "decision": 38}},
           "fixtures_sha256": "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774",
           "pinned_model_ids": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
           "compatible_limits_required_minimum": {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": 84, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": 84},
           "sandbox_base": "declared by the declaration (run.sandbox_base); dry / tests default C:/t/r2x/r38-sandbox",
           "not_bound_but_recorded": {"authority_register": {"path": (MR / "orchestrator" / "AUTHORITY-REGISTER.md").as_posix(),
                                                             "sha256_at_binding": sha(MR / "orchestrator" / "AUTHORITY-REGISTER.md"),
                                                             "why": "append-only, updated by the orchestrator"},
                                      "next_bounded_task": {"path": (MR / "orchestrator" / "NEXT-BOUNDED-TASK.md").as_posix(),
                                                            "sha256_at_binding": sha(MR / "orchestrator" / "NEXT-BOUNDED-TASK.md"),
                                                            "why": "overwritten when the next task is issued"}},
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed",
           "statement": "binds code and inputs only; it authorizes nothing (no run, budget, scope, token or default); M2 CHANGES STILL REQUIRED; M3 not started",
           "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "groups": {g: len(v) for g, v in files.items()}}))


if __name__ == "__main__":
    main(sys.argv[1])
