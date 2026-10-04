"""ORCH-08C (R39HARNESS-IMPL): evidence/EVIDENCE-MANIFEST.json of PILOT/review39/, written LAST (after PACKAGE-CHECK.json).

Usage: write_manifest_r39.py
Lists every file of the package except the manifest itself (path, bytes, sha256) with the package facts. Refuses when
PACKAGE-CHECK.json is missing or not all_ok, or when the manifest exists. Writes only the manifest."""
import datetime
import hashlib
import json
import pathlib
import sys

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review39")


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    out = PKG / "evidence" / "EVIDENCE-MANIFEST.json"
    if out.exists():
        raise SystemExit("refused: the evidence manifest is written once")
    chk = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    files = {p.relative_to(PKG).as_posix(): {"bytes": p.stat().st_size, "sha256": sha(p)} for p in sorted(PKG.rglob("*")) if p.is_file() and p != out}
    man = {"package": "PILOT/review39 (ORCH-08C: the harness correction after Verification 39)", "written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "file_count": len(files), "binding_manifest_sha256": sha(PKG / "BINDING-MANIFEST-R39.json"), "package_check_sha256": sha(PKG / "evidence" / "PACKAGE-CHECK.json"),
           "project_request_bounds_sha256": sha(PKG / "PROJECT-REQUEST-BOUNDS.json"), "resume_invocations_sha256": sha(PKG / "RESUME-INVOCATIONS-R39.json"),
           "request_paths_static_sha256": sha(PKG / "REQUEST-PATHS-STATIC.json"), "model_id_evidence_sha256": sha(PKG / "MODEL-ID-EVIDENCE.json"),
           "visibility_result_sha256": sha(PKG / "VISIBILITY-RESULT.json"),
           "candidate_head": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "baseline_head": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
           "review38_manifest_sha256": "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9",
           "review38_binding_sha256": "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d",
           "review36_manifest_sha256": "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0",
           "review36_binding_sha256": "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568",
           "ai_ledger": {k: chk["checks"]["ai_ledger"][k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256", "opened")},
           "tests": chk["checks"]["tests"]["total"],
           "statuses": {"source_permission": "unchanged (A-02 access / staging / drafting; A-06 project and provider eligibility only; no dispatch)",
                        "label_drafting": "r32-labels-draft-1 frozen; AI-drafted (Claude Opus 5.5), not human-signed",
                        "reference_set": "r32-labels-reviewed-2 (89c60e9d...b9a6): reference set independently AI-reviewed (Claude agents), not human-signed",
                        "populations": {"identity": 57, "revision": 38, "decision": 38},
                        "decision_coverage_gate": "C >= B only, a change from plan v2 (owner ruling A-10); C >= R a mandatory diagnostic",
                        "model_identity": "served-model identity UNRESOLVED offline; the owner runs the probe in MODEL-ID-EVIDENCE.md before dispatch",
                        "conditions": "Verification 39 R39-04/06/08/16/15/09/02/17 answered pending Verification 40; the corrected declaration pending ORCH-09",
                        "live_run_authorization_and_budget": "none: no declaration, scope, token, authorization file, run file, budget or dispatch",
                        "M2": "CHANGES STILL REQUIRED", "M3": "not started"},
           "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed",
           "files": files}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "files": len(files)}))


if __name__ == "__main__":
    sys.exit(main())
