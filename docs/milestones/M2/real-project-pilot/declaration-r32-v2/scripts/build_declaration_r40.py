"""ORCH-09 (R40DECL-IMPL): build and write ONCE the corrected fresh-validation declaration
`PILOT/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.json` and `DECLARATION.sha256` beside it, bound to the
review39 harness (BINDING-MANIFEST-R39 a6f703b4...), live declaration contract 4 (preflight_r32.validate_declaration).

The declaration is NOT an authorization: executed false, budget_approved false, authorization status "none; owner decision
pending", and authorization.owner_token_sha256 is the explicit placeholder (exactly once in the file) that the preflight
and the guard refuse until the owner names the token digest. Every bound hash is recomputed at build time; a difference
is PACKET MISMATCH and nothing is written.

Usage (this task):   build_declaration_r40.py show      (prints the declaration it would write; writes nothing)
                     build_declaration_r40.py write     (refuses if the declaration or DECLARATION.sha256 exists)
Usage (OWNER ONLY, later, never by this task):
                     build_declaration_r40.py fill_owner_digest --digest <64 lower-case hex>
                         writes FRESH-VALIDATION-DECLARATION-R32-V2.RUN.json beside the frozen file (O_EXCL) = the frozen
                         bytes with ONLY the placeholder replaced by the digest; prints the RUN hash
                     build_declaration_r40.py write_authorization --run-sha <RUN hash> [--nonce <16-128 [A-Za-z0-9_-]>]
                         writes OWNER-DISPATCH-AUTHORIZATION.json at the pinned path (O_EXCL) naming the RUN hash (never
                         the frozen hash), the digest read from the RUN file, authorized_by owner and a fresh nonce
Usage (anyone, read-only):
                     build_declaration_r40.py verify_run_file --digest <hex> --run-sha <hex>
                         independent re-verification of the RUN file: the frozen file intact (= DECLARATION.sha256), the
                         RUN bytes == fill_owner_digest(frozen bytes, digest), sha256 == the given RUN hash
fill_owner_digest is a re-implementation of build_declaration_r37.fill_owner_digest (review37, 775d1e51...) with the
r40 placeholder; test_r40.py proves byte equality with the r37 function on the same input."""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import pathlib
import re
import secrets
import sys

sys.dont_write_bytecode = True
import r40common as C  # noqa: E402

PARENT = {"total": 556, "input_tokens": 16_300_000, "output_tokens": 3_260_000, "elapsed_s": 604_800}
LANE_ALLOWANCES = {"B": 240, "C": 240, "R": 40, "P": 36}
PROJECT_WINDOW = {"limit": 60, "window_s": 86_400}
LEDGER_LIMITS = {"requests": 556, "per_request_input": 90_000, "per_request_output": 20_000, "input_tokens": 16_300_000,
                 "output_tokens": 3_260_000, "elapsed_s": 604_800}
LANE_SWITCHES = {
    "B": {"AI_EVIDENCE_VARIANT": "off"},
    "C": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1", "AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1",
          "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"},
    "R": {"AI_EVIDENCE_VARIANT": "EV1", "AI_EVIDENCE_GUARD": "1", "AI_EVIDENCE_SUPPORT": "v2", "AI_EVIDENCE_SCHEDULING": "required_first",
          "AI_EVIDENCE_DEADLINE": "1", "AI_EVIDENCE_TARGETED": "1"},
    "P": {},
}
APPLICATION_ENV = {"DRAWINGS_AI_REVIEW_ENABLED": "false"}
# the application's own AI limits: every count and time limit an INTEGER string (R40-08); the per-project limits at a value
# >= the bounds' required minimum 84 (contract 4); AI_MAX_COST_PER_JOB is a currency amount (float setting), inert while
# every AI_PRICE_* is 0
APPLICATION_LIMITS = {"AI_MAX_INPUT_TOKENS_PER_TASK": "6000", "AI_MAX_OUTPUT_TOKENS_PER_TASK": "800", "AI_MAX_CALLS_PER_DOCUMENT": "12",
                      "AI_MAX_CALLS_PER_PROJECT_PER_DAY": "96", "AI_MAX_COST_PER_JOB": "0.5", "AI_MAX_ELAPSED_S_PER_JOB": "120",
                      "AI_MAX_ESCALATIONS_PER_DOCUMENT": "2", "AI_MAX_CONCURRENCY": "2", "AI_MAX_RETRIES": "3",
                      "AI_PRICE_INPUT_PER_MILLION": "0", "AI_PRICE_OUTPUT_PER_MILLION": "0", "AI_PRICE_CACHED_INPUT_PER_MILLION": "0",
                      "AI_READ_MAX_CALLS_PER_DOCUMENT": "60", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": "600", "AI_READ_MAX_ELAPSED_S": "1800",
                      "AI_READ_EFFORT": "high", "AI_CACHE_TTL_DAYS": "90"}
NON_INTEGER_ALLOWED = {"AI_MAX_COST_PER_JOB": "a currency amount in a float setting (0.50 tree default), inert while every AI_PRICE_* is 0"}
NON_NUMERIC = ("AI_READ_EFFORT", "AI_EFFORT", "AI_PROVIDER", "AI_MODEL_SMALL", "AI_MODEL_STANDARD", "AI_CLAUDE_CLI", "AI_LEDGER_PATH",
               "AI_LEDGER_SCOPE", "AI_LEDGER_LIMITS")
PROVIDER_CORE = {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "claude-sonnet-5", "AI_MODEL_STANDARD": "claude-opus-5", "AI_EFFORT": "low",
                 "AI_TIMEOUT_S": "60", "AI_CLI_TIMEOUT_S": "300", "AI_CLAUDE_CLI": "claude"}
MODEL_IDENTITY = {"provider": "claude-code", "models": {"small": "claude-sonnet-5", "standard": "claude-opus-5"},
                  "cli": {"path": "claude", "version": C.CLI_VERSION_LINE}}
DECISION_COVERAGE_GATE = "C_GE_B_ONLY"
RESUME_POLICY = "full"

# every file the declaration binds by hash: name -> (path, expected sha256 or a task-given prefix, or None = recorded)
BOUND = {
    # the bound harness (review39) and its outputs
    "review39_manifest": (C.REVIEW39 / "evidence/EVIDENCE-MANIFEST.json", "2430fa2bf6bcb5bf3775efe143575dcd9cdc55723ab994cfaec5f63fbdded990"),
    "binding_manifest_r39": (C.BINDING, C.BINDING_SHA),
    "project_request_bounds": (C.BOUNDS, C.BOUNDS_SHA),
    "resume_invocations": (C.REVIEW39 / "RESUME-INVOCATIONS-R39.json", "9791fa897587fd83e1a087e302487ce245470a41c32f9aa10b48c1211e7dcf6b"),
    "visibility_result": (C.REVIEW39 / "VISIBILITY-RESULT.json", "1811e4561ae2cd157aeb9e7b599ac094b0141743f8113fea0a0944c88638192c"),
    "visibility_report": (C.REVIEW39 / "VISIBILITY-REPORT.md", None),
    "model_id_evidence_md": (C.REVIEW39 / "MODEL-ID-EVIDENCE.md", "37bec20e9bfdcedfd788a5831dae37adb7013b083587a529989e8a1659d1f0fb"),
    "model_id_evidence_json": (C.REVIEW39 / "MODEL-ID-EVIDENCE.json", None),
    "request_paths_md": (C.REVIEW39 / "REQUEST-PATHS.md", "0359ba769e38f87e96d9d1b88c75372e8811c8653072458d71d503b6e9faa619"),
    "request_paths_static": (C.REVIEW39 / "REQUEST-PATHS-STATIC.json", None),
    "drawings_ai_probe": (C.REVIEW39 / "DRAWINGS-AI-PROBE-R39.json", "19dcd79b682d40e47ba52ee29754d54d042880503d01c9c4ebc72f70852ea4b8"),
    "unread_pages_probe": (C.REVIEW39 / "UNREAD-PAGES-PROBE-R39.json", None),
    "live_run_contract_v4": (C.REVIEW39 / "LIVE-RUN-CONTRACT.md", None),
    "scorer_changes_v4": (C.REVIEW39 / "SCORER-CHANGES.md", None),
    "report_template": (C.REVIEW39 / "REPORT-TEMPLATE.md", None),
    "change_record_r39": (C.REVIEW39 / "CHANGE-RECORD-R39.md", None),
    "review39_snapshot_before": (C.REVIEW39 / "evidence/SNAPSHOT-BEFORE.json", None),
    "review39_package_check": (C.REVIEW39 / "evidence/PACKAGE-CHECK.json", "fad730b9403db6e8ea995a47a9a6b2727c0316db982f5a0b10d05279cfb05cf1"),
    "review39_work_audit_log": (pathlib.Path("C:/t/iso/work/r2x/r39/AUDIT-LOG.md"), "62cac01271e46bbeb1fcdfe77afab6bbbe7ca7b6b79f493d090578210c9592d4"),
    "review39_work_progress": (pathlib.Path("C:/t/iso/work/r2x/r39/PROGRESS.md"), "e0d6066792ac5e9f4755f83a278dce7b52d37a59cf313aa4e7ee2b61a39c3107"),
    # lineage
    "review38_manifest": (C.PILOT / "review38/evidence/EVIDENCE-MANIFEST.json", "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9"),
    "binding_manifest_r38": (C.PILOT / "review38/BINDING-MANIFEST-R38.json", "4c2904cd0f3c78131bdc15910db4206398bcf7fee871f4496cee97fa5e9f314d"),
    "live_run_contract_v3": (C.PILOT / "review38/LIVE-RUN-CONTRACT.md", None),
    "scorer_changes_v3": (C.PILOT / "review38/SCORER-CHANGES.md", None),
    "change_record_r38": (C.PILOT / "review38/CHANGE-RECORD.md", None),
    "cross_page_whatif": (C.PILOT / "review38/CROSS-PAGE-WHATIF.json", "491f9590e775fa5367569787cbc3394d8db1b82908f5f6111a2a7491da8c6fe6"),
    "review36_manifest": (C.PILOT / "review36/evidence/EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"),
    "binding_manifest_r36": (C.PILOT / "review36/BINDING-MANIFEST-R36.json", "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568"),
    "h1_whatif_result": (C.PILOT / "review36/H1-WHATIF-RESULT.json", "19b14ab3"),
    "review34_manifest": (C.PILOT / "review34/evidence/EVIDENCE-MANIFEST.json", "64d5ba0d"),
    "binding_manifest_r34": (C.PILOT / "review34/BINDING-MANIFEST-R34.json", "3d0f8bfe"),
    "live_run_contract_v2": (C.PILOT / "review34/LIVE-RUN-CONTRACT.md", "0658e2a8"),
    "concentration_rule_doc": (C.PILOT / "review34/CONCENTRATION-RULE-R32.md", "0affc814"),
    "run_set_rule_doc": (C.PILOT / "review34/RUN-SET-RULE.md", "9ee2ccec"),
    "adapter_contract": (C.PILOT / "review34/ADAPTER-CONTRACT.md", "871c103d"),
    "review33_manifest": (C.PILOT / "review33/evidence/EVIDENCE-MANIFEST.json", "c5001c95"),
    "review31_manifest": (C.PILOT / "review31/evidence/EVIDENCE-MANIFEST.json", "d5fe1649"),
    # the superseded declaration (structure and numbers carried; never authorized, never run)
    "superseded_declaration": (C.SUPERSEDED / "FRESH-VALIDATION-DECLARATION-R32.json", C.SUPERSEDED_SHA),
    "superseded_manifest": (C.SUPERSEDED / "evidence/EVIDENCE-MANIFEST.json", C.SUPERSEDED_MANIFEST_SHA),
    "superseded_builder": (C.BUILD_R37, C.BUILD_R37_SHA),
    "superseded_concentration_on_proposal": (C.SUPERSEDED / "concentration/CONCENTRATION-ON-PROPOSAL.json", None),
    # run set, truth, reference set, fixtures
    "run_set_proposal": (C.RUN_SET, C.RUN_SET_SHA),
    "truth_r32": (C.TRUTH, C.TRUTH_SHA),
    "labels_r32_eval_input": (C.PILOT / "review34/LABELS-R32-EVAL-INPUT.json", "4b2c73d5"),
    "reviewed2_labels": (C.PILOT / "fresh-cohort-r32-reviewed-2/labels/R32-LABELS-REVIEWED-2.json", "89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6"),
    "reviewed2_field_population": (C.PILOT / "fresh-cohort-r32-reviewed-2/FIELD-POPULATION.json", "799a4b8f"),
    "package_fresh_cohort_r32": (C.PILOT / "fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json", "15c4114d"),
    "package_fresh_cohort_r32_reviewed": (C.PILOT / "fresh-cohort-r32-reviewed/evidence/EVIDENCE-MANIFEST.json", "64c03667"),
    "package_fresh_cohort_r32_reviewed_2": (C.PILOT / "fresh-cohort-r32-reviewed-2/evidence/EVIDENCE-MANIFEST.json", "1f27a544"),
    "source_manifest": (C.PILOT / "fresh-cohort-r32/SOURCE-MANIFEST.json", "951e8697"),
    "renders": (C.PILOT / "fresh-cohort-r32/RENDERS.json", "175a3a10"),
    "evidence_index": (C.PILOT / "fresh-cohort-r32/EVIDENCE-INDEX.json", "0d0db4f8"),
    "project_verification": (C.PILOT / "fresh-cohort-r32/PROJECT-VERIFICATION.json", "4cecf2fc"),
    "frozen_selection": (C.PILOT / "fresh-cohort-r32/FROZEN-SELECTION.json", "bf71779a"),
    "label_conventions": (C.PILOT / "fresh-cohort-r32/LABEL-CONVENTIONS-R32.md", "5c09d4d2"),
    "cohort_authorization_a02": (C.PILOT / "fresh-cohort-r32/AUTHORIZATION-2026-10-02.md", "fd20167a"),
    "label_review_response_final": (C.MR / "reviews/M2-label-review-r32-draft-1/REVIEWER-RESPONSE.final.json", "920a21d6"),
    "evaluator_10": (pathlib.Path("C:/t/iso/cand-r29/backend/scripts/m2_eval6.py"), "268d86231260392dc5592a6937803b8fcd15a41e9590b442f3f0a70dc57b4b4f"),
    "evaluator_offline_r32_manifest": (C.PILOT / "evaluator-offline-r32/evidence/EVIDENCE-MANIFEST.json", "86dd81d3"),
    "evaluator_offline_binding_r35": (C.PILOT / "evaluator-offline-r32/BINDING-MANIFEST-R35.json", "1de0773a"),
    "candidate_config": (C.CANDIDATE_BACKEND / "app/core/config.py", "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"),
    "baseline_config": (C.BASELINE_BACKEND / "app/core/config.py", "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"),
    "application_ledger_py": (C.APPLICATION_LEDGER_PY, C.APPLICATION_LEDGER_PY_SHA),
    "application_provider_py": (C.CANDIDATE_BACKEND / "app/ai/provider.py", "d465961e"),
    # reviews and verifications
    "review33": (C.MR / "reviews/M2-review-33/INDEPENDENT-REVIEW.md", "8d20baec"),
    "review34": (C.MR / "reviews/M2-review-34/INDEPENDENT-REVIEW.md", "75061210"),
    "review35": (C.MR / "reviews/M2-review-35/INDEPENDENT-REVIEW.md", "f4f668ac"),
    "review35_findings": (C.MR / "reviews/M2-review-35/FINDINGS.json", "b3ae349a"),
    "verification36": (C.MR / "reviews/M2-review-36/INDEPENDENT-VERIFICATION.md", "f698c2ff"),
    "verification36_findings": (C.MR / "reviews/M2-review-36/FINDINGS.json", "9e65a5c0"),
    "verification37": (C.MR / "reviews/M2-review-37/INDEPENDENT-VERIFICATION.md", "288983f25996ce9143ea95f1b7d98f1ac1c581fcefb386014e407e8ecfe84126"),
    "verification37_findings": (C.MR / "reviews/M2-review-37/FINDINGS.json", "2f77e707"),
    "verification38": (C.MR / "reviews/M2-review-38/INDEPENDENT-VERIFICATION.md", "006d0203aaa98a9973de140ab73ac2e127df06f827c686b1f2629c1ae607f5c7"),
    "verification38_findings": (C.MR / "reviews/M2-review-38/FINDINGS.json", "d432e3f5"),
    "verification39": (C.MR / "reviews/M2-review-39/INDEPENDENT-VERIFICATION.md", "5bb967f278fd331047df3b8026432bc01ac4b678d4cc48286e50dbc6fba46598"),
    "verification39_findings": (C.MR / "reviews/M2-review-39/FINDINGS.json", "5976db3818000242ec32ef16323516ca29270e74027f7b10cef22fe3e2b8028a"),
    "verification40": (C.MR / "reviews/M2-review-40/INDEPENDENT-VERIFICATION.md", "620ea60a63e871625c940f27ff50b2999d2403111b088275702eb68abf736cb2"),
    "verification40_findings": (C.MR / "reviews/M2-review-40/FINDINGS.json", "f225540849a5097fa8c27e870b2001ca593b91735832e1424c0a19ce12d86e48"),
    "verification40_package_check": (C.MR / "reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK.json",
                                     "51222ad53fd3bf42a205ac0dc9c9e3f6bd5d65b0251fab1815b31c9216667c99"),
    # policy, authority, plan
    "policy": (C.MR / "AI-ACCURACY-POLICY.md", "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47"),
    "policy_amendment_r32_01": (C.MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6"),
    "authority_register": (C.MR / "orchestrator/AUTHORITY-REGISTER.md", "346597d3c482cf66b7daeaec17a1334715d6e000be68725679013184361ffcfd"),
    "plan_v2": (C.PILOT / "review31/REVISED-FRESH-VALIDATION-PLAN.v2.md", "83c120c939c28351a7a1a70e54e9b9ab2487724aa19cdb979f16f043f2c56bfb"),
    "stop_and_safety_rules": (C.PILOT / "review31/STOP-AND-SAFETY-RULES.md", "e2ee3504c1711b5b9497b7292c9161af58ae6c2fdef5f3f7b4ef24a1cd30b0ca"),
    "budget_card_v2": (C.PILOT / "review31/BUDGET-DECISION-CARD.v2.md", "b36fb571"),
    "draft_declaration_v2": (C.PILOT / "review31/DRAFT-DECLARATION.v2.json", "19720ad9"),
    "binding_manifest_review31": (C.PILOT / "review31/BINDING-MANIFEST.json", "2dfef08e"),
    "four_arm_final_declaration": (C.PILOT / "four-arm-final/declaration/FINAL-DECLARATION.v2.json", "6c0189b3"),
    "four_arm_final_usage": (C.PILOT / "four-arm-final/USAGE-AND-BUDGET.json", "90b4702c"),
    "threshold_master_roadmap": (C.MR / "MASTER-ROADMAP.md", "f6dba0b2fce767955aed2b7508cfe7480637b02c44f502c3702c7862116e4c86"),
    "threshold_m2_acceptance_report": (C.M2 / "M2-ACCEPTANCE-REPORT.md", "7816ea793d0f4a0500ab3e2548c73975f7324b8ae0b37551683144844a14448b"),
    "threshold_review21_analysis_plan": (C.PILOT / "review21/ANALYSIS-PLAN.md", "76064b634dff6c32b1ec25f83e640a7170ed629ec219820c465553631b75b9c4"),
}
# the R40-04 proof (Verification 40's own dynamic and static evidence), copied into this package and bound by hash; each
# file must equal the hash Verification 40 recorded in INDEPENDENT-PACKAGE-CHECK.json (51222ad5...)
R40_04_PROOF_SRC = pathlib.Path("C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/r40")
R40_04_PROOF = {"out/UNREAD-R40.json": "raw_outputs_sha256", "scripts/unread_r40.py": "scripts_sha256",
                "out/PATHS-MINE-R40.json": "raw_outputs_sha256", "scripts/paths_mine_r40.py": "scripts_sha256",
                "out/PATHS-WHY-R40.json": "raw_outputs_sha256", "scripts/paths_why_r40.py": "scripts_sha256"}
PROOF_DIR = "evidence/r40-04-proof"
RECORDS_DIR = "evidence/review39-work-records"


def hashes() -> dict:
    out = {}
    for name, (path, want) in BOUND.items():
        got = C.sha256_file(path)
        if want is not None and not got.startswith(want):
            raise C.PacketMismatch(f"PACKET MISMATCH: {name} {path} {got} does not match {want}")
        out[name] = {"path": pathlib.Path(path).as_posix(), "sha256": got}
    return out


def package_copies() -> dict:
    """The R40-04 proof files and the review39 work-folder records (R40-20), as copied into THIS package: each copy must
    exist and equal its source (and, for the proof, the hash Verification 40 recorded)."""
    v40 = json.loads((C.MR / "reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    out = {"r40_04_proof": {}, "review39_work_records": {}}
    for rel, group in R40_04_PROOF.items():
        src = R40_04_PROOF_SRC / rel
        dst = C.PACKAGE / PROOF_DIR / pathlib.Path(rel).name
        want = v40[group][rel]
        got_src, got_dst = C.sha256_file(src), C.sha256_file(dst)
        if not (got_src == got_dst == want):
            raise C.PacketMismatch(f"PACKET MISMATCH: R40-04 proof {rel}: source {got_src}, copy {got_dst}, Verification 40 {want}")
        out["r40_04_proof"][pathlib.Path(rel).name] = {"package_path": f"{PROOF_DIR}/{pathlib.Path(rel).name}", "sha256": got_dst,
                                                       "verification40_recorded": f"INDEPENDENT-PACKAGE-CHECK.json {group}['{rel}']",
                                                       "original": src.as_posix()}
    for name, key in (("AUDIT-LOG.md", "review39_work_audit_log"), ("PROGRESS.md", "review39_work_progress")):
        src, want = BOUND[key]
        dst = C.PACKAGE / RECORDS_DIR / name
        got = C.sha256_file(dst)
        if got != want or C.sha256_file(src) != want:
            raise C.PacketMismatch(f"PACKET MISMATCH: review39 work record {name}")
        out["review39_work_records"][name] = {"package_path": f"{RECORDS_DIR}/{name}", "sha256": got, "original": pathlib.Path(src).as_posix()}
    return out


def lines_between(path, start_heading: str, stop_heading: str) -> tuple[list, str]:
    """The lines of a markdown section, verbatim: from the line equal to start_heading up to (not including) the next line
    starting with stop_heading (or the end). Returns (lines, 'first-last' 1-based)."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
    try:
        i = lines.index(start_heading)
    except ValueError as exc:
        raise C.PacketMismatch(f"PACKET MISMATCH: {path} has no line {start_heading!r}") from exc
    j = next((k for k in range(i + 1, len(lines)) if lines[k].startswith(stop_heading)), len(lines))
    while j > i and not lines[j - 1].strip():
        j -= 1
    return lines[i:j], f"{i + 1}-{j}"


def lines_verbatim(path, first: int, last: int, must_start: str) -> list:
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")[first - 1:last]
    if not lines or not lines[0].startswith(must_start):
        raise C.PacketMismatch(f"PACKET MISMATCH: {path} line {first} does not start with {must_start!r}")
    return lines


def verbatim_line(path, needle: str) -> dict:
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")
    hits = [i + 1 for i, ln in enumerate(lines) if needle in ln]
    if len(hits) != 1:
        raise C.PacketMismatch(f"PACKET MISMATCH: {path}: {needle!r} found on lines {hits}")
    return {"line": hits[0], "text": lines[hits[0] - 1]}


def thresholds_verbatim(sup: dict, h: dict) -> list:
    """Carried from the superseded declaration and re-verified: every text item a substring of its source at its hash."""
    names = {"AI-ACCURACY-POLICY.md section 1": "policy", "M2-ACCEPTANCE-REPORT.md Correction 5 targets": "threshold_m2_acceptance_report",
             "MASTER-ROADMAP.md M2": "threshold_master_roadmap", "review21/ANALYSIS-PLAN.md section 5": "threshold_review21_analysis_plan"}
    out = []
    for item in sup["thresholds_verbatim"]:
        name = names[item["source"]]
        if item["sha256"] != h[name]["sha256"]:
            raise C.PacketMismatch(f"PACKET MISMATCH: threshold source {item['source']}")
        text = pathlib.Path(h[name]["path"]).read_text(encoding="utf-8")
        for t in (item["text"] if isinstance(item["text"], list) else [item["text"]]):
            if t not in text:
                raise C.PacketMismatch(f"PACKET MISMATCH: threshold text not verbatim in {item['source']}")
        out.append(dict(item))
    return out


def integer_string_problems(provider_env: dict) -> list:
    """R40-08: every numeric application value must be an integer string ('84', '12', '120'; never '84.0'), except the
    explicitly allowed non-integer currency amount."""
    probs = []
    for k, v in provider_env.items():
        if k in NON_NUMERIC:
            continue
        if k in NON_INTEGER_ALLOWED:
            try:
                float(v)
            except ValueError:
                probs.append(f"{k} = {v!r} is not a number")
            continue
        if not isinstance(v, str) or not re.fullmatch(r"(0|[1-9][0-9]*)", v):
            probs.append(f"{k} = {v!r} is not an integer string")
    return probs


def fill_owner_digest(frozen: bytes, digest: str) -> bytes:
    """The ONE derivation of the runnable (RUN) declaration: the placeholder value of authorization.owner_token_sha256
    replaced by the owner's 64-hex token digest; nothing else changes. Pure (no file is read or written). Same algorithm as
    build_declaration_r37.fill_owner_digest (review37, 775d1e51...)."""
    if not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        raise ValueError("the owner token digest is 64 lower-case hex characters")
    needle = json.dumps(C.TOKEN_PLACEHOLDER).encode("utf-8")
    if frozen.count(needle) != 1:
        raise ValueError("the frozen declaration must hold the placeholder exactly once")
    filled = frozen.replace(needle, json.dumps(digest).encode("utf-8"))
    a, b = json.loads(frozen.decode("utf-8")), json.loads(filled.decode("utf-8"))
    assert a["authorization"]["owner_token_sha256"] == C.TOKEN_PLACEHOLDER and b["authorization"]["owner_token_sha256"] == digest
    a["authorization"]["owner_token_sha256"] = digest
    assert a == b, "the filled declaration differs from the frozen one in more than the owner token digest"
    return filled


def authorization_text(run_sha: str, digest: str, nonce: str, *, frozen_sha: str) -> str:
    """The owner's OWNER-DISPATCH-AUTHORIZATION.json content (pure; returned, never written here): it names the RUN hash,
    never the frozen hash."""
    if not re.fullmatch(r"[0-9a-f]{64}", run_sha or "") or not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
        raise ValueError("the RUN hash and the digest are 64 lower-case hex characters")
    if run_sha == frozen_sha:
        raise ValueError("the authorization names the RUN hash, never the frozen hash (the frozen file is never used with the runner)")
    if not re.fullmatch(r"[A-Za-z0-9_-]{16,128}", nonce or ""):
        raise ValueError("the nonce is 16-128 characters [A-Za-z0-9_-], fresh for every invocation")
    return json.dumps({"authorized_by": "owner", "declaration_sha256": run_sha, "nonce": nonce, "owner_token_sha256": digest},
                      sort_keys=True, indent=1) + "\n"


def frozen_bytes_checked() -> tuple[bytes, str]:
    frozen = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
    sha = C.sha256_bytes(frozen)
    recorded = (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    if sha != recorded:
        raise C.PacketMismatch(f"PACKET MISMATCH: the frozen declaration {sha} != DECLARATION.sha256 {recorded}")
    return frozen, sha


def verify_run_file(digest: str, run_sha: str, run_path=None) -> dict:
    """Independent, read-only re-verification of the owner's RUN file (R38-07)."""
    frozen, fsha = frozen_bytes_checked()
    run_path = pathlib.Path(run_path or C.PACKAGE / C.RUN_NAME)
    if not run_path.is_file():
        raise C.PacketMismatch(f"no RUN file at {run_path.as_posix()}")
    raw = run_path.read_bytes()
    want = fill_owner_digest(frozen, digest)
    out = {"frozen_sha256": fsha, "run_path": run_path.as_posix(), "run_sha256": C.sha256_bytes(raw), "expected_run_sha256": C.sha256_bytes(want),
           "bytes_equal_to_single_replacement": raw == want, "given_run_sha256": run_sha}
    out["verified"] = out["bytes_equal_to_single_replacement"] and out["run_sha256"] == run_sha == out["expected_run_sha256"] and run_sha != fsha
    return out


# ---- the declaration ---------------------------------------------------------------------------------------------------
def _load(path) -> dict:
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def section_text(sup_lines: list) -> list:
    return list(sup_lines)


def build(h: dict, copies: dict, declared_at: str) -> dict:
    sup = _load(h["superseded_declaration"]["path"])
    bounds = _load(C.BOUNDS)
    resume = _load(h["resume_invocations"]["path"])
    binding = _load(C.BINDING)
    mid = _load(h["model_id_evidence_json"]["path"])
    pinned = (C.PACKAGE / C.AUTH_NAME).as_posix()
    run_folder = C.RUN_FOLDER.as_posix()
    run_path = (C.PACKAGE / C.RUN_NAME).as_posix()
    provider_env = dict(PROVIDER_CORE) | {"AI_LEDGER_PATH": C.AI_LEDGER.as_posix(), "AI_LEDGER_SCOPE": C.SCOPE,
                                           "AI_LEDGER_LIMITS": json.dumps(LEDGER_LIMITS, sort_keys=True)} | dict(APPLICATION_LIMITS)
    probs = integer_string_problems(provider_env)
    if probs:
        raise C.PacketMismatch(f"integer strings (R40-08): {probs}")
    sys.path.insert(0, str(C.HARNESS))
    import preflight_r32 as PF          # noqa: E402  (the bound review39 copy; imported after harness_import_path checked it)
    import score_bcr_r32 as S           # noqa: E402
    kinds = PF.task_kinds_for(LANE_SWITCHES)
    gate_def = S.DECISION_COVERAGE_GATE_DEFINITIONS[DECISION_COVERAGE_GATE]
    assert S.DECISION_COVERAGE_GATE == DECISION_COVERAGE_GATE and PF.APPLICATION_ENV == APPLICATION_ENV
    stop_table = lines_verbatim(h["stop_and_safety_rules"]["path"], 7, 20, "| Event | Lane |")
    v4_s5, v4_s5_lines = lines_between(h["live_run_contract_v4"]["path"], "## 5. The project rolling window, deferral and resume (A-09; R39-08)", "## ")
    v4_s13, v4_s13_lines = lines_between(h["live_run_contract_v4"]["path"],
                                         "## 13. Failed reads and the capture store: behaviour and its accuracy implication (R39-16)", "## ")
    v4_s4, v4_s4_lines = lines_between(h["live_run_contract_v4"]["path"], "## 4. One run folder, one parent budget, one capture store", "## ")
    v4_s6, v4_s6_lines = lines_between(h["live_run_contract_v4"]["path"], "## 6. Visibility: every event is recorded per document and page", "## ")
    v4_s3, v4_s3_lines = lines_between(h["live_run_contract_v4"]["path"], "## 3. The authorization (`dispatch_guard_r32`, unchanged)", "## ")
    v4_s12, v4_s12_lines = lines_between(h["live_run_contract_v4"]["path"],
                                         "## 12. The decision coverage gate (R39-15; the owner's ruling A-10, 2026-10-04)", "## ")
    nonce_rules = lines_verbatim(h["live_run_contract_v2"]["path"], 49, 53, "**One run, one nonce.**")
    plan_v2_resume = verbatim_line(h["plan_v2"]["path"], "never re-sends a bound fingerprint")
    harness_files = binding["files"]["harness_r39_package"]
    modules = {pathlib.Path(p).stem: {"path": p, "sha256": s} for p, s in harness_files.items() if not pathlib.Path(p).name.startswith("test_")}
    cli = mid.get("cli") or {}
    est_sup = sup["estimated_usage"]
    struct = {lane: bounds["lanes"][lane]["structural_maximum"] for lane in ("B", "C", "R", "P")}
    p95 = {"evidence": (45_544, 10_870), "B": (25_057, 3_881)}
    struct_tok = {lane: {"input": struct[lane] * (p95["B"] if lane == "B" else p95["evidence"])[0],
                         "output": struct[lane] * (p95["B"] if lane == "B" else p95["evidence"])[1]} for lane in struct}
    struct_tok["total"] = {k: sum(v[k] for v in struct_tok.values()) for k in ("input", "output")}
    per_project = {p: {"documents": v["documents"], "pool_ids": v["pool_ids"], "pages_read": v["pages_read"], "planning": v["planning"],
                       "structural_maximum": v["structural_maximum"], "windows_needed_structural": v["windows_needed_structural"],
                       "planning_exceeds_window": v["planning_exceeds_window"], "structural_exceeds_window": v["structural_exceeds_window"],
                       "application_rows_maximum": v["application_rows_maximum"],
                       "drawings_ai_if_enabled_all_lanes": v["drawings_ai"]["if_enabled"]["structural_all_lanes"]}
                   for p, v in bounds["projects"].items()}
    app_project_limit = int(APPLICATION_LIMITS["AI_MAX_CALLS_PER_PROJECT_PER_DAY"])
    required = bounds["compatible_limits"]["required_minimum"]["AI_MAX_CALLS_PER_PROJECT_PER_DAY"]
    unsupported = copy.deepcopy(sup["controls"])
    unsupported["unsupported_control_shortfall"]["declared_scope_limitation"] = (
        "A-09 point 6 (owner): accepted ONLY as a declared scope limitation; no control is replaced after predictions exist "
        "(run_set_selector_r32.replace_controls refuses once a prediction exists); unsupported-format safety and generalization are not "
        "claimed; the shortfall never disappears from a report (score_bcr_r32.SCOPE_LIMITATIONS, in every result and REPORT-TEMPLATE)")
    interp = copy.deepcopy(sup["interpretations"])
    interp["review35_item10"] = [
        ("SUPERSEDED BY RULE CP-R38 (A-09 point 5; review38 SCORER-CHANGES v3 Part B rows 1-2): the cross-page identity rule no longer keeps "
         "evaluator .10 parity; see cross_page_identity") if x.startswith("the cross-page identity rule keeps evaluator .10 parity") else x
        for x in interp["review35_item10"]]
    interp["verification36_section6"] = [
        ("the cross-page identity rule is rule CP-R38 (A-09 point 5; see cross_page_identity)") if x.startswith("the cross-page identity rule with its actual scope")
        else ("compilations are keyed by (pool id, page) in the value branch (F035 and F043 in the run set); CP-R38 condition (D) gives a compilation "
              "no cross-page association in either branch (the former ABSENT-branch gap H4 is closed)") if x.startswith("compilations are keyed by (pool id, page)")
        else x for x in interp["verification36_section6"]]
    interp["cross_page_rule_scope"] = {"superseded": "the .10-parity scope (11 run-set documents) is replaced by rule CP-R38, which applies to every document",
                                       "documents_formerly_in_scope": sup["interpretations"]["cross_page_rule_scope"]["documents"], "of_run_set": 24}
    disclosures_carried = [d for d in sup["disclosures"] if not d.startswith((
        "budget stops and provider-failure stops are not undone by a resume; a project-day refusal",
        "the application's internal AI limits act as silent stops",
        "H4: the ABSENT branch forgives", "H5: a wrong value equal to another page's identity",
        "the dry exercise of this declaration ran the bound code relocated"))]
    matched = [i for i, d in enumerate(disclosures_carried) if d.startswith("matched margin:")]
    assert len(matched) == 1
    disclosures_carried[matched[0]] = (
        "matched margin: the projected matched populations are identity 23, revision 16, decision 16 against the minimum of 12 (margins 11 / 4 / 4); "
        "a document that B or C does not attempt or cannot read, a limit refusal or a deferral that cannot complete (both make the comparison "
        "INCOMPLETE and exclude the document from the matched sets, listed), or pages left unread under the application's per-document limits "
        "can take revision or decision below 12, and the field then fails the matched-population gate (R33-10, R34-09); Review 33's own "
        "approximation put P(matched < 12) at 1.7 / 20 / 55 % for 10 / 20 / 30 % per-document loss")
    gates = copy.deepcopy(sup["gates"])
    gates["decision_coverage"] = ("C_GE_B_ONLY (owner ruling A-10): completed reads + verified absences of C >= those of B on the resolved decision "
                                  "documents of the run set; wrong absences, located_incomplete and NOT_SCORABLE rows never count. CHANGED from plan v2, "
                                  "whose gate was C >= B AND C >= R; this is NOT an unchanged gate. C >= R is a MANDATORY diagnostic in every result and "
                                  "report (both lanes' counts, missing coverage per document and page with each lane's class and the reason; INCOMPLETE "
                                  "when R did not complete its declared population) and never determines eligibility")
    gates["decision_coverage_superseded_text"] = sup["gates"]["decision_coverage"]
    gates["comparison_state"] = ("A-09 point 1: a B or C document refused by a limit (classes limit / failure) or DEFERRED makes the comparison "
                                 "INCOMPLETE; it stays in every denominator and is excluded from the matched sets with each exclusion listed; a "
                                 "contract breach or a model-identity mismatch makes the run INVALID")
    gates["other_gates"] = ("every other safety, accuracy and completeness gate is carried verbatim from the superseded declaration (per_field, "
                            "safety, request_gate, concentration, candidate_outcome, outcomes, default_selection)")
    lanes = copy.deepcopy(sup["lanes"])
    lanes["B"]["task_kinds"] = kinds["B"]
    lanes["B"]["drawings_ai_review"] = "switched off by application_env in every lane (REQUEST-PATHS.md; Verification 40 R40-03)"
    lanes["C"]["task_kinds"] = kinds["C"]
    lanes["R"]["task_kinds"] = kinds["R"]
    lanes["R"]["role"] = ("offline contrast only; R earns NO accuracy or recovery credit (A-09 point 7); it never determines eligibility: the C >= R "
                          "decision coverage contrast is a MANDATORY diagnostic only (A-10); never a live stop (a resolved-truth critical in R is a "
                          "reference finding)")
    lanes["P"]["task_kinds"] = kinds["P"]
    lanes["P"]["meaning"] = ("the variation probe: a seeded 15 % (seed m2-r30-variation-2026-10-02) of C's answered dispatches AS DRAWN AT P's FIRST "
                             "RUN, re-sent once in lane P, cap 36")
    lanes["P"]["role"] = "reported only; never served to B or C; never a score; no credit (A-09 point 7)"
    dispatch_order = [
        "owner, before invocation 1: the model-identity probe (RUNBOOK section 1), `claude --version` == '2.1.263 (Claude Code)', the two-hash procedure and the scope creation (create_scope_r40.py)",
        "runner preflight before anything is created: the binding manifest and every bound file (verify_binding), the declaration contract 4 (validate_declaration: parent budget, lane allowances, project window, compatible limits, pinned model identity, application_env, lane_task_kinds, resume_policy, decision_coverage_gate), the run set, candidate and baseline HEADs clean, the truth and the population gate, PROJECT-REQUEST-BOUNDS recomputed and equal, the declared ledger scope exists with exactly the declared limits and a closed breaker, the dispatch-guard preview (the pinned authorization, the token digest, an unconsumed nonce)",
        "the run folder (invocation 1 only), the WRITER lock, `claude --version` recorded and compared with the pin (CLI-VERSIONS.jsonl, PROVIDER-IDENTITY.json), the authorization nonce consumed (O_EXCL record)",
        "B: sandbox_ingest_r32 registers exactly the 24 run-set documents (no processing); lane B processes them with the tripwire after every document; B's final database sha256 recorded",
        "C only when no B document is DEFERRED; C-from-B state check: C's and R's sandboxes are copies of B's final database; state_check.check_c_start must pass (B INVALID means C never starts)",
        "C: the evidence stage on each run-set document with C's switches; tripwire after every document; unread pages recorded per page",
        "R and P only when no C document is DEFERRED; R: served from C's capture by content key; requests C never made are dispatched once as reference-only",
        "P: the probe over C's answered dispatches as drawn at P's first run (frozen sample)",
        "offline scoring: score_lane_r32 per lane, then score_bcr_r32.evaluate with the candidate-level outcome, the mandatory C >= R diagnostic and the unread pages",
        "a DEFERRED invocation ends with resume_not_before (resume_policy 'full'); every later invocation is a resume with a new owner authorization",
    ]
    return {
        "schema": "orch09-fresh-validation-declaration-r32-v2.1",
        "contract": PF.CONTRACT,
        "name": "M2 fresh validation R32, corrected declaration v2: accepted baseline B vs Review 29 combined candidate C, with reference R and variation probe P",
        "task": "ORCH-09 (orchestrator ledger ORCH-024), implementation agent R40DECL-IMPL, Claude Opus 5.5 (claude-opus-5-5, self-reported), effort High",
        "supersedes": {"declaration": h["superseded_declaration"], "manifest": h["superseded_manifest"],
                       "status": "superseded by owner decision A-09 (2026-10-03): never authorized, never run, never to be run",
                       "differences": "DECLARATION-DIFF.md and DECLARATION-DIFF.json in this package list every difference",
                       "structure": "the superseded declaration's structure and numbers are kept wherever A-09, A-10 and Verification 40 do not change them"},
        "declared_at_utc": declared_at,
        "status": ("FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file, no run file and no dispatch exist; "
                   "Verification 41 and the owner's budget decision are pending"),
        "executed": False,
        "budget_approved": False,
        "authorization_status": "none; owner decision pending",
        "standing_status": {"M2": "CHANGES STILL REQUIRED", "M3": "not started"},
        "authorities": {"register": h["authority_register"], "applied": ["A-03", "A-06", "A-08", "A-09", "A-10"],
                        "summary": dict(sup["authorities"]["summary"]) | {
                            "A-09": ("the frozen R32 declaration 38e08df9...76b0 is not authorized and is superseded; one bounded preparation correction "
                                     "and a NEW declaration hash: compatible limits and visible INCOMPLETE / deferral (1), pinned model identities and "
                                     "the CLI version (2), one immutable parent budget with lane allowances (3), evidenced cross-page identity (4), the "
                                     "unsupported-control shortfall as a declared scope limitation (5), R/P no credit and diagnostic INCOMPLETE (6, 7), "
                                     "no scope / token / run file / request before the corrected declaration passes independent re-verification with an "
                                     "exact runbook and scope-creation command (8)"),
                            "A-10": ("decision coverage eligibility C >= B only, C >= R a mandatory diagnostic, explicitly a change from plan v2 (1); the "
                                     "owner runs the model-identity probe before dispatch, an alias is never proof, runtime identity checking fail-closed, "
                                     "unverifiable identity reported UNRESOLVED (2); ORCH-08C -> Verification 40 -> ORCH-09 -> Verification 41 -> STOP "
                                     "before authorization, scope creation or dispatch (3)")}},
        # ---- the live declaration contract 4 (preflight_r32.validate_declaration) ----------------------------------------
        "binding_manifest_sha256": h["binding_manifest_r39"]["sha256"],
        "run_set_sha256": h["run_set_proposal"]["sha256"],
        "run": {"stamp": C.STAMP, "sandbox_base": C.SANDBOX_BASE.as_posix(), "folder": run_folder,
                "allowance": f"{run_folder}/allowance.sqlite", "capture_store": f"{run_folder}/capture.sqlite", "run_state": f"{run_folder}/RUN-STATE.json",
                "rule": ("one run folder, one allowance (parent budget, lane allowances and project window bound in the file) and one capture store per "
                         "declaration, all bound to the RUN declaration's sha256 (the run key); 'run' once, then 'resume' only, with the same stamp"),
                "never_moved_or_deleted": "the run folder holds the one-run anchors (consumed nonces, allowance charges, durable stops); it is never moved or deleted (R35-07)",
                "base_justification": [
                    "C:/t/r2x/r40-sandbox matches the bound preflight's declared-base rule C:/t/r2x/r<NN>-sandbox; it is this task's own sandbox base, used by no test or dry default of the review39 harness (whose default is C:/t/r2x/r39-sandbox); this task's dry runs use stamps beginning 'r40d', never 'r32-v2'",
                    "Windows' 260-character path limit: this machine has LongPathsEnabled = 0 and ordinary file APIs fail at 260 characters or more (evidence/PATHLEN-PROBE.json); the longest application path of the run is F032's staged PDF, <run folder>/inv-<n>/B/s/EP-27331/<208-character relative path>: 255 characters with this 20-character base and the 6-character stamp (256 from inv-10), below 260 even without the application's own extended-length helper (document_control._os_path / _open_pdf, which every PDF open on the B, C and R paths uses); the superseded run folder C:/t/r2x/r34-sandbox/r32-fresh-validation-2026-10-03 would have made that path 280 characters",
                    "the folder does not exist at declaration time and must not exist before the owner's first invocation (the runner refuses 'run' when it exists; create_scope_r40.py refuses when it exists)"]},
        "authorization": {
            "status": "none; owner decision pending",
            "path": pinned,
            "owner_token_sha256": C.TOKEN_PLACEHOLDER,
            "placeholder_rule": ("owner_token_sha256 holds an explicit placeholder, exactly once in this file, not a digest: preflight_r32.validate_declaration "
                                 "and dispatch_guard_r32 refuse it ('the declaration binds no owner token digest'). No token exists and none was generated. "
                                 "The RUN declaration is this file with that one value replaced and nothing else changed (build_declaration_r40.py "
                                 "fill_owner_digest); the RUN file's own sha256 (the RUN hash) is the hash the runner, the lanes, the guard, the allowance "
                                 "(run key), the authorization file and the scope-creation command use; the frozen hash is never used with the runner"),
            "two_hash_procedure": {
                "frozen_hash": "the sha256 of THIS file (DECLARATION.sha256); it identifies what the owner reviewed and is never given to the runner",
                "token": ("generated by the owner, high-entropy (for example 32 random bytes as 64 hex characters), held only by the owner, never stored in "
                          "any file, presented only in the environment variable R34_OWNER_DISPATCH_TOKEN; its digest becomes readable in the repository"),
                "digest": "sha256 of the token's UTF-8 bytes with no trailing newline, written as 64 lower-case hex characters",
                "run_file": run_path,
                "run_hash": "the sha256 of the RUN file, computed by the owner when the file is written (fill_owner_digest prints it)",
                "independent_verification": ("before any authorization file or scope exists, the orchestrator (or an independent verifier) re-computes it with "
                                             "build_declaration_r40.py verify_run_file --digest <digest> --run-sha <RUN hash>: the frozen file intact, the RUN "
                                             "bytes equal to the single replacement, the sha256 equal"),
                "budget_authorization_names": ["the frozen hash", "the digest", "the RUN hash", f"the absolute RUN-file path {run_path}",
                                               f"the absolute authorization path {pinned}",
                                               f"the scope {C.SCOPE} with limits {json.dumps(LEDGER_LIMITS, sort_keys=True)}",
                                               "the first invocation (runner_r32.py run --mode live, RUNBOOK section 5.1)"],
                "authorization_file": "names the RUN hash (declaration_sha256), never the frozen hash"},
            "file_fields": {"declaration_sha256": "the RUN hash (the sha256 of the digest-filled RUN declaration file), never the frozen hash",
                            "owner_token_sha256": "the same digest the RUN declaration binds", "authorized_by": "owner",
                            "nonce": "a fresh one-run nonce, 16-128 characters [A-Za-z0-9_-], one per invocation"},
            "nonce_rule_verbatim": {"source": h["live_run_contract_v2"]["path"], "sha256": h["live_run_contract_v2"]["sha256"], "lines": "49-53", "text": nonce_rules},
            "authorization_rule_v4_verbatim": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s3_lines,
                                               "text": v4_s3},
            "token_holder": "owner",
            "token_presentation": "the owner presents the token in the environment variable R34_OWNER_DISPATCH_TOKEN at each invocation and at the scope creation; it is compared by digest and never written to any file",
            "one_invocation_per_authorization": "run and every resume each consume one authorization with a fresh nonce into <run folder>/authorization/consumed-<sha256(nonce)[:32]>.json (O_EXCL)",
            "runbook": "RUNBOOK.md in this package (exact, ordered, absolute paths); SCOPE-CREATION-COMMAND.md for the scope",
            "invocation": {"working_directory": C.HARNESS.as_posix(), "python": C.PY,
                           "environment": {"PYTHONDONTWRITEBYTECODE": "1", "GIT_OPTIONAL_LOCKS": "0", "R34_OWNER_DISPATCH_TOKEN": "<the owner's token, never written>"},
                           "run": (f"{C.PY} -B runner_r32.py run --mode live --declaration {run_path} --declaration-sha <RUN hash> --run-set {C.RUN_SET.as_posix()} "
                                   f"--binding {C.BINDING.as_posix()} --binding-sha {h['binding_manifest_r39']['sha256']}"),
                           "resume": "the same with 'resume' instead of 'run' (a new authorization file with a fresh nonce first; not before RUN-STATE.json resume_not_before_utc)",
                           "harness_copy": ("PILOT/review39/scripts/harness-r32 is the copy BINDING-MANIFEST-R39 binds as harness_r39_package; "
                                            "C:/t/iso/work/r2x/r39/harness-r32 is byte-identical (harness_r39); the runbook uses the package copy")}},
        "budget": {"parent": dict(PARENT), "lane_allowances": dict(LANE_ALLOWANCES)},
        "budget_detail": {
            "rule": ("A-09 point 3: one immutable parent experiment budget with separately auditable lane allowances; no lane borrows another's allowance; "
                     "the declared total ceiling 556 is preserved; failed, interrupted, timed-out and dispatched-but-unsaved requests stay charged; a "
                     "resume never resets an allowance or a terminal state"),
            "enforcement": ("allowance_r32 charges before dispatch per lane (never refunded, never raised); the parent total 556, input tokens 16,300,000, "
                            "output tokens 3,260,000 and the elapsed bound 604,800 s are bound in the run's allowance; the single ledger scope's limits "
                            "equal the parent's and are the backstop"),
            "equal_allowance_B_C": "B 240 = C 240 (8 per document x 30 documents): the request gate is defined at equal caps (R31-03)",
            "per_document_cap_basis": "8 requests per document x 30 documents = 240; the run set holds 24 documents",
            "total": sum(LANE_ALLOWANCES.values()), "replaces": "the superseded keys caps / caps_detail (contract 4 names them budget.lane_allowances)"},
        "project_window": dict(PROJECT_WINDOW),
        "project_window_detail": {
            "rule": ("the harness per-project ROLLING-window limit: at most 60 charges per project within any 86,400 s, counted over ALL lanes (the "
                     "probe lane is attributed to the project of the payload it re-sends); it GOVERNS (the application's own per-project limits are "
                     "bound above the bounds' required minimum so they can never refuse first)"),
            "a_refusal_is_a_deferral": ("a request the window would exceed is never charged and never permanent: the document is DEFERRED with "
                                        "retry_at_earliest and retry_at_full {planning, structural}; the lane continues; C starts only when no B document is "
                                        "DEFERRED, R and P only when no C document is DEFERRED; a deferral that cannot complete within the elapsed bound "
                                        "ends INCOMPLETE (at once, or by the CLOSE record)"),
            "replaces": ("the superseded project_day_limit 60 per UTC day and project_day_limit_detail: a day-limit refusal was permanent for the run "
                         "(R35-09); the rolling window defers instead (A-09 point 1)"),
            "value_basis": "60 is the largest value contract 4 accepts and equals plan v2 section 7; PROJECT-REQUEST-BOUNDS.json was computed for exactly this window"},
        "project_request_bounds": h["project_request_bounds"],
        "project_request_bounds_detail": {
            "version": bounds["version"], "recomputed_by": "the live preflight (verify_bounds) and every live lane; a difference refuses the run",
            "EP-27331": {"planning": bounds["projects"]["EP-27331"]["planning"]["all_lanes"],
                         "structural": bounds["projects"]["EP-27331"]["structural_maximum"]["all_lanes"],
                         "structural_by_lane": {k: bounds["projects"]["EP-27331"]["structural_maximum"][k] for k in ("B", "C", "R", "P")},
                         "drawings_ai_enabled_alternative": bounds["projects"]["EP-27331"]["drawings_ai"]["if_enabled"]["structural_all_lanes"],
                         "windows_needed_structural": bounds["projects"]["EP-27331"]["windows_needed_structural"],
                         "note": "structural 160, not 154: B's reconcile repeat of a failed form read is dispatched again (review39 change 4), so B is bounded at 2 per document per invocation; 170 only if the drawings-AI path were enabled (it is not: application_env)"},
            "all_projects_structural": {p: v["structural_maximum"]["all_lanes"] for p, v in bounds["projects"].items()},
            "all_projects_planning": {p: v["planning"]["all_lanes"] for p, v in bounds["projects"].items()},
            "required_application_minimum": bounds["compatible_limits"]["required_minimum"],
            "retries_across_resumes": bounds["retries_across_resumes"]},
        "resume_policy": RESUME_POLICY,
        "resume_detail": {
            "rule": ("'full' (the default contract 4 offers and this declaration binds): a DEFERRED run may be resumed only at the LATEST structural-basis "
                     "retry_at_full of its deferred documents (the project's remaining structural maximum fits the window, or the window is empty); a "
                     "resume before that time is refused and creates nothing; if the full time falls after the elapsed bound the policy falls back to "
                     "the earliest retry (recorded)"),
            "resume_invocations": {"path": h["resume_invocations"]["path"], "sha256": h["resume_invocations"]["sha256"], "version": resume["version"],
                                   "EP-27331_full": {"planning_demand_63": resume["table"]["planning"]["full"], "structural_demand_160": resume["table"]["structural"]["full"]},
                                   "EP-27331_earliest_for_comparison": {"planning": [resume["table"]["planning"]["earliest_paced"], resume["table"]["planning"]["earliest_burst"]],
                                                                        "structural": [resume["table"]["structural"]["earliest_paced"], resume["table"]["structural"]["earliest_burst"]]},
                                   "last_invocation_starts_after_s": {"planning": resume["results"]["planning|full|paced"]["finished_after_s"],
                                                                      "structural": resume["results"]["structural|full|paced"]["finished_after_s"]},
                                   "statement": resume["statement"]},
            "invocations_expected": ("2 at the planning estimate (the last starts about 24.3 h after the first), 3 at the structural maximum (about 48.5 h); "
                                     "every other project needs at most 3 windows at its structural maximum and 1 at planning; each invocation after the "
                                     "first is a resume with its own owner authorization (one nonce per invocation); retries of failed requests on resumes "
                                     "add charges and can add invocations; a refused resume (before the policy's time) consumes no authorization")},
        "lane_switches": copy.deepcopy(LANE_SWITCHES),
        "lane_task_kinds": kinds,
        "lane_task_kinds_detail": ("preflight_r32.task_kinds_for(lane_switches) (REQUEST-PATHS.md): B the baseline form read only; C the candidate evidence "
                                   "reader's kinds under C's switches; R the same without locate_decision; P = C; the gate refuses any other task kind, "
                                   "and any request without the current document's context, as a contract breach (the run INVALID); a declaration "
                                   "cannot widen them"),
        "application_env": dict(APPLICATION_ENV),
        "application_env_detail": ("exactly the allowlist contract 4 requires: the baseline's drawings-AI review (document_processing.run -> "
                                   "shop_drawings.reconcile -> drawing_ai_review, enabled by default, up to 10 requests per project per B invocation) is "
                                   "switched off in every lane; every lane of every invocation and resume verifies it in its environment, in the "
                                   "application's settings and through drawing_ai_review.enabled(); its outputs feed no measured field in either tree "
                                   "(DRAWINGS-AI-PROBE-R39.json; Verification 40 R40-06)"),
        "provider_env": provider_env,
        "application_ai_limits": {
            "bound": dict(APPLICATION_LIMITS),
            "integer_strings": ("R40-08: every count and time limit is written as an integer string ('96', '600', '12', '120', '1800'; never '84.0'); "
                                "the only non-integer numeric value is AI_MAX_COST_PER_JOB '0.5' (a currency amount in a float setting, inert while every "
                                "AI_PRICE_* is '0'); build_declaration_r40.integer_string_problems refuses anything else at build time; the bound "
                                "validate_declaration still accepts '12.0' / '120.0' (R39-18, not implemented in the harness), so this declaration does "
                                "not rely on it"),
            "compatible_limits": {
                "required_minimum": bounds["compatible_limits"]["required_minimum"],
                "AI_MAX_CALLS_PER_PROJECT_PER_DAY": {"value": APPLICATION_LIMITS["AI_MAX_CALLS_PER_PROJECT_PER_DAY"], "margin": app_project_limit - required,
                                                     "justification": (f"the required minimum {required} is the largest AiUsage row count any lane database "
                                                                       "can hold in one invocation (EP-27331: B's 12 rows + C's JobBudget 12 x 6 documents; "
                                                                       "Verification 40 R40-07 reproduced it); the margin 12 equals one document's whole "
                                                                       "per-document JobBudget (AI_MAX_CALLS_PER_DOCUMENT 12), so one unmodelled document's "
                                                                       "rows cannot make the application refuse before the harness window; it stays close to "
                                                                       "the derived maximum so the application's own counter remains a near second backstop "
                                                                       "in lanes C and R (the evidence reader's JobBudget reads it); the harness window (60 "
                                                                       "per 24 h, all lanes), the lane allowances and the parent total bound every dispatch "
                                                                       "whatever this value is")},
                "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": {"value": APPLICATION_LIMITS["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"],
                                                          "margin": int(APPLICATION_LIMITS["AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY"]) - required,
                                                          "justification": ("the tree default and the superseded declaration's value, unchanged: it governs only "
                                                                            "B's form reads (sheet_reader uses max(read limit, project limit)), whose maximum per "
                                                                            "lane database is 12 (EP-27331); B's form reads are bounded by the B allowance 240, "
                                                                            "the window and B's per-document job (60); a lower value would add no safety")},
                "AI_MAX_CALLS_PER_DOCUMENT": {"value": APPLICATION_LIMITS["AI_MAX_CALLS_PER_DOCUMENT"], "basis": "required equal to the bounds' assumption (tree default 12)"},
                "AI_MAX_ELAPSED_S_PER_JOB": {"value": APPLICATION_LIMITS["AI_MAX_ELAPSED_S_PER_JOB"], "basis": "required equal to the bounds' assumption (tree default 120.0, written '120')"},
                "check": "project_bounds_r32.check_compatible(provider_env, PROJECT-REQUEST-BOUNDS) returns [] (no problem)"},
            "statement": ("bound in provider_env; every other application limit stays at the candidate and baseline tree default (equal in both "
                          "config.py files, b4fbc07f...; no .env file in either tree; sandbox_env strips every AI_* variable of the operator's environment)"),
            "not_silent": ("replaces the superseded 'silent_stops': the application's per-document limits (the reader's cap 8, the JobBudget 12 / 120 s, a "
                           "reader exception) are recorded per page as unread pages (unread_page_rule); the application's per-project limit cannot refuse "
                           "before the harness window at these values, and if it did it would be a visible application_project_limit event "
                           "(INCOMPLETE)")},
        "model_identity": copy.deepcopy(MODEL_IDENTITY),
        "model_identity_detail": {
            "pins": "full ids, no aliases (A-09 point 2): AI_MODEL_SMALL claude-sonnet-5 (every B, C and R read), AI_MODEL_STANDARD claude-opus-5 (EV2 escalations only, not reached under the declared EV1 switches); provider claude-code",
            "cli": {"path_setting": "claude (AI_CLAUDE_CLI; resolved on PATH to the WinGet package file below; the owner confirms with `where claude`)",
                    "version_pinned": C.CLI_VERSION_LINE, "file": C.CLI_EXE.as_posix(), "file_sha256": C.CLI_EXE_SHA, "file_bytes": C.CLI_EXE_BYTES,
                    "embedded_version": cli.get("embedded_version") or "2.1.263",
                    "rule": ("the runner records `claude --version` before any lane of every invocation (CLI-VERSIONS.jsonl, PROVIDER-IDENTITY.json) and "
                             "refuses an invocation whose version line differs from '2.1.263 (Claude Code)' or from the run's first; a CLI change before "
                             "dispatch requires a NEW declaration hash")},
            "served_model_identity": "UNRESOLVED",
            "unresolved_statement": ("MODEL-ID-EVIDENCE (review39; reproduced by Verification 40 R40-17): claude-sonnet-5 and claude-opus-5 are catalog ids that "
                                     "the CLI passes unchanged; the json output's modelUsage key is the REQUESTED model; only stream-json's assistant "
                                     "message.model carries the server's statement, which is a self-report, never proof of the underlying model; no "
                                     "dated id exists in the CLI. The served-model identity is therefore UNRESOLVED offline. The owner decides: run the "
                                     "probe (RUNBOOK section 1) or accept UNRESOLVED identity with the fail-closed runtime check"),
            "runtime_check": ("fail-closed under the declared INVALID rule: every response's reported model and provider are compared with the pins "
                              "(IdentityGuard); a mismatch writes IDENTITY-INVALID.json, the answer is never used, the request stays charged, every "
                              "lane becomes terminal, the run is INVALID and every resume is refused"),
            "runtime_check_limits": ["limit 1: it compares what the CLI reports, which in json mode is the REQUESTED id: it verifies the CLI's resolution of --model and the absence of a fallback or remap, not the served model",
                                     "limit 2: an echoed id passes: a response with no non-haiku modelUsage key (and a timeout or transport failure) echoes the configured id"],
            "evidence": {"md": h["model_id_evidence_md"], "json": h["model_id_evidence_json"]},
            "probe": "the owner's probe is RUNBOOK section 1 (Verification 40 section 6, amended per R40-16): not run by this task; its request count cannot be verified offline"},
        "ledger": {"path": C.AI_LEDGER.as_posix(), "scope": C.SCOPE, "limits": dict(LEDGER_LIMITS), "wrap_provider": True},
        "ledger_detail": {
            "creation": ("created only by the owner, with create_scope_r40.py create (SCOPE-CREATION-COMMAND.md), after the budget authorization, with "
                         "the authorization file naming the RUN hash and the token presented; new and empty, exactly these limits, closed breaker, "
                         "immediately before the first invocation; this task created no scope (AI ledger 483 entries / 17 scopes / 0 amendments "
                         "before and after); the harness never creates a scope"),
            "limits_keys": ("every key is a field of the application's ledger Limits (requests, input_tokens, output_tokens, per_request_input, "
                            "per_request_output, elapsed_s); requests / input_tokens / output_tokens / elapsed_s equal the parent budget (contract 4)"),
            "one_scope_for_all_lanes": "one scope serves B, C, R and P (R35-10); per-lane token and elapsed thresholds are not enforced per lane",
            "elapsed": "the scope's elapsed_s counts from the scope's CREATION; the allowance's elapsed bound counts from the first invocation; both are bounds, the earlier one stops first",
            "live_check": "after every invocation the ledger may have grown only inside the declared scope (no new scope, no limit amendment, every other scope unchanged) and by at most 556 dispatch entries (preflight_r32.ledger_live_check)",
            "reconciliation": "before every resume: allowance_r32.py audit with the ledger and scope (charges <= 556; ledger dispatch entries <= charges; every charge names its ledger entry or why not); a difference stops the run until explained"},
        "decision_coverage_gate": DECISION_COVERAGE_GATE,
        "decision_coverage_gate_detail": {
            "bound": DECISION_COVERAGE_GATE, "text": gate_def["text"], "change_from_plan_v2": gate_def["change_from_plan_v2"],
            "statement": ("A CHANGE FROM PLAN V2 (review31 REVISED-FRESH-VALIDATION-PLAN.v2.md), whose gate was C >= B AND C >= R. It is NOT an unchanged "
                          "gate. The owner ruled it on 2026-10-04 (A-10 item 1): 'Bind decision coverage eligibility to C >= B only'."),
            "plan_v2_definition": dict(S.PLAN_V2_DECISION_COVERAGE_GATE),
            "mandatory_diagnostic": S.C_GE_R_DIAGNOSTIC_RULE,
            "contract_v4_section_12_verbatim": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s12_lines,
                                                "text": v4_s12},
            "other_gates": "every other safety, accuracy and completeness gate is preserved verbatim from the superseded declaration"},
        # ---- extended bindings and statements ----------------------------------------------------------------------------
        "lanes": lanes,
        "switch_names": copy.deepcopy(sup["switch_names"]),
        "dispatch_order": dispatch_order,
        "probe_population": {
            "definition": ("P's population is C's ANSWERED dispatches AS DRAWN AT P's FIRST RUN: the seeded 15 % sample (seed m2-r30-variation-2026-10-02) "
                           "is drawn once, when lane P first runs, and kept in the capture store's probe_sample table; a later C retry (in a resume) can "
                           "never change it (R40-12)"),
            "cap": LANE_ALLOWANCES["P"], "seed": "m2-r30-variation-2026-10-02", "rate": 0.15,
            "example": "Verification 40 T7: P drew 3 of C's 20 answered dispatches at its first run; after C's retries C had 25, where an unfrozen draw would give 4 of 25; P keeps its 3",
            "why": ("a necessary consequence of the failed-read retry rule (review39 change 4): without the freeze, a resume that re-runs C after P "
                    "would redraw P's sample from a changed population and abandon probed items; the cap 36 and the seed are unchanged from plan "
                    "v2 section 1 and the superseded declaration"),
            "diagnostic": "P earns no credit; when P cannot complete its frozen sample its diagnostic is INCOMPLETE"},
        "r_and_p": {
            "credit": "none (A-09 point 7): R and P earn no accuracy or recovery credit anywhere and never select a default; the candidate outcome reads only B and C",
            "diagnostic_incomplete": ("when truncation (a lane stop, a refusal, a deferral, a lane that never started) prevents R from completing its declared "
                                      "diagnostic population (the run set) or P its frozen sample, the diagnostic is INCOMPLETE and the C >= R contrast's "
                                      "holds is null (score_bcr_r32)")},
        "retry_rule": {
            "change_from_plan_v2": True,
            "plan_v2_section_4_verbatim": {"source": h["plan_v2"]["path"], "sha256": h["plan_v2"]["sha256"]} | plan_v2_resume,
            "now_reads": ("a resume never re-sends a request with a bound ANSWER; a fingerprint whose dispatches all FAILED is dispatched again on the "
                          "application's own retry path, charged (never refunded), recorded as a retry with its ordinal (retry_key(base, ordinal), the "
                          "capture store's retries table, charge note 'retry N of <bound key>', lane rows retry_dispatched, ALLOWANCE-AUDIT retries); "
                          "a reserved request without an outcome (interrupted) is still served interrupted_charged and never re-sent"),
            "statement": ("this is a CHANGE FROM PLAN V2 section 4 ('A resume never re-sends a bound fingerprint') and from review34's verbatim resume "
                          "rules carried by the superseded declaration (a failed row 'is served as its failure on resume'); ordered by ORCH-021 decision "
                          "3 (R39-16); named as a change here per Verification 40 R40-13"),
            "within_one_invocation": "B's reconcile check repeats a failed form read: the repeat is dispatched (retry 2), attributed to its own document",
            "accuracy_implication": ("B and C can obtain an answer on a retry where the stored failure was served before; results can depend on the number "
                                     "of invocations; the rule is identical for B and C (symmetric in rule, not necessarily in count); see stop_rules.verbatim_review39_resume_rules"),
            "budget_stops_stay_durable": "a ledger, breaker, guard, allowance or parent refusal stops the lane durably; a resume never undoes it and refuses its retries visibly (terminal_stop)"},
        "unread_page_rule": {
            "rule": ("A-09 point 1 as read by ORCH-021: harness and resource refusals (lane allowance, parent ceiling / tokens / elapsed, window, breaker, "
                     "ledger, guard, identity, timeout, provider failure, interruption, the application's per-project limit) make a document INCOMPLETE; "
                     "application-internal per-document behaviour under the declared limits (the reader's own cap MAX_CALLS_PER_DOCUMENT 8 checked "
                     "between pages, the JobBudget 12 calls / 120 s, a reader exception) leaves the document COMPLETE with every unread page recorded "
                     "per page (kind, reason, partial) in the lane rows, RUN-REPORT, the scorer and the audit view, and counted as unread in every "
                     "denominator"),
            "no_trigger_exclusion": ("pages whose outcome is 'no_trigger' (the reader's own trigger rule: the page was never meant to be read) are NOT listed "
                                     "as unread pages; they stay in the coverage denominators as not attempted (run_state_r38.unread_pages_of_attempt; "
                                     "Verification 40 R40-10 (b))"),
            "unguarded_corners": [
                ("R40-10 (a): if evidence_stage stores no new attempt for a document (its own skip when row.sha256 is missing or row.extracted is not a "
                 "dict, or a bounded attempts list already at MAX_ATTEMPTS_KEPT 12), the lane derives no unread page and marks the document COMPLETE "
                 "'read by the application's evidence stage' with no event; declared scope statement: not reachable in this run (the lane first "
                 "requires a fresh PDF row of B's state, B's own evidence stage is off, so every C / R sandbox starts with 0 attempts)"),
                ("R40-10 (b): 'no_trigger' pages are excluded from unread_pages by design (above); declared scope statement: in-scope pages are <= 4 for "
                 "every run-set document, so MAX_PAGES_PER_DOCUMENT 4 hides none")],
            "acknowledgement_R40_15": ("documents with application-internal page limits are COMPLETE with unread pages (ORCH-021's interpretation of A-09 "
                                       "point 1, made by the orchestrator): for B and C no eligibility outcome changes (Verification 40's differential); "
                                       "for R it changes only the C >= R diagnostic's completeness (a document with a JobBudget exhaustion or a reader "
                                       "exception counts COMPLETE in that population), never eligibility; owner acknowledgement recommended")},
        "request_path_coverage": {
            "finding": "Verification 40 R40-04 (minor)",
            "corrected_claim": ("review39's REQUEST-PATHS.md section 4 and CHANGE-RECORD-R39 section 7 say the runtime gate refuses any undeclared request "
                                "'that a missed static edge might produce'. That 'belt and braces' holds for lane B only: lane B installs the harness "
                                "chain as the application's global provider (prov.set_provider(chain)); lanes C, R and P do not. In C, R and P an "
                                "application get_provider() call would build the configured provider from the settings (live: ClaudeCodeProvider "
                                "wrapped by the declared ledger scope) and its request would bypass the gate, the lane allowance, the capture store, "
                                "the identity guard and the dispatch guard."),
            "coverage_for_C_R_P": ("C, R and P rest on proof under the declared switches: no get_provider() call is reachable on their path -- two static "
                                   "analyses (review39 request_paths_r39.py, REQUEST-PATHS-STATIC.json; Verification 40's own paths_mine_r40.py / "
                                   "paths_why_r40.py) find only evidence_stage's 'provider or get_provider()' (not taken: the lane passes its chain) "
                                   "and submittal_reader.available (replaced by the lane); and one dynamic run of the candidate's REAL evidence_stage "
                                   "with every get_provider() replaced by a raising recorder (scenarios A-D) recorded 0 calls (UNREAD-R40.json "
                                   "get_provider_calls 0); P is harness-only (it re-sends captured payloads through its own chain)"),
            "proof_bound": copies["r40_04_proof"] | {"request_paths_static": h["request_paths_static"], "verification40_package_check": h["verification40_package_check"]},
            "residual_risk": ("stated plainly: an application path that calls get_provider() in lane C, R or P, not found by either static analysis and not "
                              "exercised by the dynamic run (for example code reached only by real cohort data), would send a request outside the "
                              "harness chain: not gated, not counted against the lane allowance or the window, not captured, not identity-checked, "
                              "with no owner-nonce check; the declared ledger scope (LedgerProvider, 556 requests, token and elapsed limits) and the "
                              "post-run ledger_live_check (growth only inside the scope, at most 556 dispatch entries; reconciliation finds ledger "
                              "entries without a charge record) would still bound and expose it, and the application's own JobBudget and per-project "
                              "limits would bound it where that path uses them; in dry mode such a call reaches the NullProvider silently, so the "
                              "dry drills cannot show its absence"),
            "owner_options": ["(1) accept the proof-based coverage for C, R and P with the residual risk as stated (no harness change; this declaration as frozen)",
                              "(2) order a bounded harness change that installs a refusing (or the harness-chain) global provider in lanes C, R and P, with "
                              "its own independent verification and a re-declaration (a new declaration hash); this declaration would then not be used"],
            "lane_B": "lane B's belt and braces holds: the chain is the global provider, so any request reaches the gate (undeclared kind or missing context: contract breach, run INVALID, never charged)"},
        "cross_page_identity": {
            "rule": "CP-R38 (A-09 point 5; review38 SCORER-CHANGES v3 Part B rows 1-2; lane_judge_r32 + page_relations_r38, unchanged in review39)",
            "text": ("an asserted identity that differs from the page's own value (or is asserted on an ABSENT identity page) is a cross-page association "
                     "-- neither correct nor wrong for the page, never credit for another page, never critical -- ONLY when (S) the lane document's source "
                     "sha256 equals the staged sha256, (D) the document is no compilation and its identity is resolved for scoring, (T) the value equals a "
                     "resolved identity of another page, and (P) the reviewed labels record the pages' relationship (R1 listed among the page's own "
                     "other_identities; R2 the page's identity listed as an enclosure on a page whose identity is the target's; R3 both pages carry the "
                     "same resolved identity literal); file names, file membership and page order are never evidence; otherwise the value is judged on "
                     "the page (critical when automatically accepted); held or conflicting identity earns no recovery credit (recovered_conflict)"),
            "whatif": h["cross_page_whatif"] | {"summary": "356 target verdicts change on 89 fixtures, all to critical_false_acceptance; 40 fixtures keep an evidenced association (R1 15, R2 12, R3 13); the 25 formerly forgiven wrong-value controls are criticals without recorded evidence"},
            "supersedes": "the superseded declaration's .10-parity cross-page rule (review35_item10, verification36_section6, H4, H5)"},
        "scope_limitations": {"items": [dict(x) for x in S.SCOPE_LIMITATIONS], "not_claimed": list(S.NOT_CLAIMED),
                              "statement": "A-09 point 6: the unsupported-control shortfall is a declared scope limitation, never replaced after predictions exist, never removed from a report"},
        "controls": unsupported,
        "estimated_usage": {
            "statement": "estimates, not limits and not measurements; the lane allowances, the parent budget, the window and the ledger limits are the bounds",
            "documents": est_sup["documents"],
            "lanes": est_sup["lanes"],
            "lanes_note": ("carried from the superseded declaration (planning B 6, C 112, R 10, P 17 = 145; low C 108). Its 'conservative' C 192 "
                                   "(8 per document) is NOT a bound (Verification 38 R38-08: the reader's 8 is checked only between pages; the JobBudget's "
                                   "12 per document is the hard bound); the structural maxima below replace it as the upper figure"),
            "structural_maximum": {"source": "PROJECT-REQUEST-BOUNDS.json (project-bounds-r39-2026-10-04.1)", "by_lane": struct,
                                   "by_lane_before_caps": {lane: bounds["lanes"][lane]["structural_sum_before_cap"] for lane in ("B", "C", "R", "P")},
                                   "total": sum(struct.values()),
                                   "note": "one dispatch per request per invocation; retries of failed requests across resumes are not included (bounded by the lane allowances, the parent 556 and the window)"},
            "tokens": est_sup["tokens"],
            "tokens_at_structural_maximum_p95": struct_tok | {"basis": "structural maximum x the ledger's calibrated p95 of the largest task (discover_page 45,544 / 10,870; B read_submittal_form 25,057 / 3,881): a deliberately pessimistic upper figure",
                                                              "versus_parent": {"input_tokens": PARENT["input_tokens"], "output_tokens": PARENT["output_tokens"]},
                                                              "consequence": ("at the structural maximum with every request sized at that p95 the output total would exceed the "
                                                                              "parent / scope output bound 3,260,000: the ledger would refuse first (a visible budget stop, "
                                                                              "INCOMPLETE if in B or C); the planning estimate is 257,047 output tokens")},
            "per_request_basis": est_sup["per_request_basis"],
            "model": est_sup["model"],
            "per_project": per_project,
            "per_project_note": "replaces the superseded per-project figures (whose 'C_max' 8 per document was not a bound): planning and structural maxima of PROJECT-REQUEST-BOUNDS.json",
            "plan_v2_expected_for_comparison": est_sup["plan_v2_expected_for_comparison"]},
        "token_thresholds": copy.deepcopy(sup["token_thresholds"]) | {
            "enforced": ("the parent budget's input 16,300,000 / output 3,260,000 tokens by the allowance on the provider-reported usage of every settled charge (parent_input_tokens / parent_output_tokens refusals, durable) and by the single ledger scope's equal totals; the per-request thresholds by the ledger's reservation on ESTIMATES before dispatch (an actual overshoot opens the breaker); per-lane token equality between B and C is NOT enforced (R35-10)"),
            "breaker_margins": ("Verification 38 R38-13: the largest actual per-request usage in the AI ledger is input 81,625 and 70,264 and output 19,568 "
                                "against the declared 90,000 / 20,000; one actual overshoot opens the single scope's breaker for every later request of "
                                "every lane (B or C: INCOMPLETE); disclosed, unchanged")},
        "elapsed_bounds": copy.deepcopy(sup["elapsed_bounds"]) | {
            "enforced": ("two clocks, both bounds, the earlier one stops first: the allowance's parent elapsed_s 604,800 s counts from the run's allowance "
                         "binding (the first invocation); the ledger scope's elapsed_s 604,800 s counts from the scope's CREATION (scopes.created_at); "
                         "per-lane elapsed bounds are declared, not enforced (R35-10); every resume and any delay between creating the scope and the first "
                         "invocation count; under resume_policy 'full' EP-27331 needs about 24.3 h (planning) or 48.5 h (structural) of waiting")},
        "cost": copy.deepcopy(sup["cost"]),
        "provider": {
            "basis": copy.deepcopy(sup["provider"]["basis"]),
            "cost_note": sup["provider"]["cost_note"],
            "environment_keys": "the ten required keys plus the application's own AI limits, all strings, integer strings for every count and time limit, all verified by every live lane (provider_env)",
            "ledger_provider": sup["provider"]["ledger_provider"],
            "proposed_vs_tree_defaults": {k: {"declared": provider_env[k], "candidate_and_baseline_tree_default": v}
                                          for k, v in {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "claude-fable-5-1", "AI_MODEL_STANDARD": "claude-fable-5-1",
                                                       "AI_EFFORT": "low", "AI_TIMEOUT_S": "60.0", "AI_CLI_TIMEOUT_S": "300.0", "AI_CLAUDE_CLI": "claude"}.items()},
            "owner_confirmable": {
                "AI_MODEL_SMALL": "declared 'claude-sonnet-5' (full id, A-09 point 2; the four-arm alias 'sonnet' was recorded as claude-sonnet-5)",
                "AI_MODEL_STANDARD": "declared 'claude-opus-5' (full id; EV2 escalations only, not reached under EV1)",
                "AI_EFFORT": "declared 'low' (the tree default); the claude-code adapter sends no effort flag, so it does not change a request",
                "cli_version": f"pinned {C.CLI_VERSION_LINE!r}",
                "ledger.scope": f"declared {C.SCOPE!r} (a new name; no scope of that name exists)",
                "AI_MAX_CALLS_PER_PROJECT_PER_DAY": "declared '96' (application_ai_limits.compatible_limits)",
                "rule": "cost and accuracy depend on these values; changing any of them is a new declaration with a new sha256, frozen and verified before any authorization"}},
        "stop_rules": {
            "implementation": "run_state_r38.ControllerR38 (subclassing the unchanged stop_rules.StopController, 4632ffea...) replays every lane's events; the tripwire is per field (pool id, page, field)",
            "verbatim_stop_and_safety_rules": {"source": h["stop_and_safety_rules"]["path"], "sha256": h["stop_and_safety_rules"]["sha256"], "lines": "7-20", "text": stop_table},
            "verbatim_review39_resume_rules": {
                "replaces": "the superseded declaration's verbatim review34 resume rules (review34 LIVE-RUN-CONTRACT lines 67-73), per Verification 40 R40-13",
                "section_5": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s5_lines, "text": v4_s5},
                "section_13": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s13_lines, "text": v4_s13},
                "section_4": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s4_lines, "text": v4_s4},
                "section_6": {"source": h["live_run_contract_v4"]["path"], "sha256": h["live_run_contract_v4"]["sha256"], "lines": v4_s6_lines, "text": v4_s6}},
            "terminal_states": {
                "INCOMPLETE": "a B or C document refused by a limit (classes limit / failure) or still DEFERRED, a budget stop of B or C, three consecutive provider failures in C, or a deferral that cannot complete within the elapsed bound; the comparison is INCOMPLETE; a resume is allowed (it never undoes a budget stop)",
                "DEFERRED": "the run state of an invocation that ended with deferred documents (the project window); not terminal; resume allowed at resume_not_before (policy 'full')",
                "INVALID": "a resolved-truth critical in B, three consecutive provider failures in B, a model-identity mismatch (IDENTITY-INVALID.json), or a contract breach (CONTRACT-BREACH.json); terminal; never resumed",
                "CLOSED": "a DEFERRED run whose elapsed bound passed: closed INCOMPLETE by the runner (the deferred documents listed); terminal; never resumed",
                "RESULT": "a resolved-truth critical in C: C terminal, NOT ELIGIBLE; terminal; never resumed",
                "FINISHED": "every lane complete; scored; a complete run is never resumed"},
            "summary": ["budget stops and provider-failure stops are not undone by a resume", "a window refusal is a deferral, never charged and never permanent",
                        "resume is refused after a terminal comparison (RESULT, INVALID), after CLOSED and after a complete run, and before the resume policy's time",
                        "R and P stops affect only their own lane", "a failed fingerprint is retried on a resume (charged, with an ordinal): a change from plan v2 section 4 (retry_rule)"]},
        "harness": {
            "package": "PILOT/review39/", "package_manifest": h["review39_manifest"],
            "binding_manifest": h["binding_manifest_r39"] | {"entries": sum(len(v) for v in binding["files"].values()),
                                                             "supersedes": "review38/BINDING-MANIFEST-R38.json 4c2904cd... for the harness code; carried groups re-hashed and equal"},
            "accepted_by": "Verification 40 (ORCH-08C VERIFIED; 0 blockers, 0 majors, 3 minors routed to this declaration: R40-04, R40-13, R40-16)",
            "modules": modules,
            "contracts": {"live_run_contract_v4": h["live_run_contract_v4"], "scorer_changes_v4": h["scorer_changes_v4"], "report_template": h["report_template"],
                          "request_paths": h["request_paths_md"], "request_paths_static": h["request_paths_static"], "change_record_r39": h["change_record_r39"],
                          "visibility_report": h["visibility_report"], "visibility_result": h["visibility_result"], "drawings_ai_probe": h["drawings_ai_probe"],
                          "unread_pages_probe": h["unread_pages_probe"], "model_id_evidence": h["model_id_evidence_md"],
                          "adapter_contract": h["adapter_contract"], "run_set_rule": h["run_set_rule_doc"]},
            "concentration_rule": {"version": "concentration-r32-2026-10-03.2", "code": modules["concentration_r32"], "document": h["concentration_rule_doc"]},
            "lineage": {"review38": {"manifest": h["review38_manifest"], "binding": h["binding_manifest_r38"], "contract_v3": h["live_run_contract_v3"],
                                     "scorer_changes_v3": h["scorer_changes_v3"], "change_record": h["change_record_r38"], "accepted_by": "Verification 39 (with conditions; closed by review39 and Verification 40)"},
                        "review36": {"manifest": h["review36_manifest"], "binding": h["binding_manifest_r36"], "h1_whatif": h["h1_whatif_result"], "accepted_by": "Verification 37"},
                        "review34": {"manifest": h["review34_manifest"], "binding": h["binding_manifest_r34"], "contract_v2": h["live_run_contract_v2"], "accepted_by": "Review 35"},
                        "review33": {"manifest": h["review33_manifest"], "accepted_by": "Review 34"},
                        "review31": {"manifest": h["review31_manifest"], "binding": h["binding_manifest_review31"]}},
            "bound_code_used_as_is": ("the bound code runs unchanged from PILOT/review39/scripts/harness-r32: the sandbox base is DECLARED (run.sandbox_base), "
                                      "not a code constant, so no relocated copy (twin) is needed; the dry exercise of this declaration ran the same "
                                      "files"),
            "review39_snapshot_before": h["review39_snapshot_before"] | {"taken_utc": "2026-10-04T09:55:49+00:00",
                                                                        "note": "R40-19: review39's SNAPSHOT-BEFORE was taken at 09:55:49Z (after the code changes of 09:21-09:53Z), not 'about 10:13Z' as CHANGE-RECORD-R39 section 8 says; the task-start check is the 09:00:34Z audit entry"},
            "review39_work_records": copies["review39_work_records"] | {"why": "R40-20: the package's audit log stops one entry short (10:19:54Z); the final work-folder AUDIT-LOG.md and PROGRESS.md are copied into this package byte for byte and bound here; review39 is not re-packaged (its manifest 2430fa2b... is what Verification 40 covers)"},
            "package_check": h["review39_package_check"]},
        "evaluator": copy.deepcopy(sup["evaluator"]) | {"judging": ("every verdict, metric, tripwire, coverage figure, control and gate comes from lane_judge_r32 "
                                                                    "(with rule CP-R38) + literal_compare_r32 of the review39 harness; .10 judging is never bound")},
        "trees": {"candidate": {"tree": C.CANDIDATE[0], "head": C.CANDIDATE[1], "clean": True, "config_py": h["candidate_config"],
                                "ledger_py": h["application_ledger_py"], "provider_py": h["application_provider_py"]},
                  "baseline": {"tree": C.BASELINE[0], "head": C.BASELINE[1], "clean": True, "config_py": h["baseline_config"]}},
        "run_set": copy.deepcopy(sup["run_set"]) | {"selector": modules["run_set_selector_r32"],
                                                    "truth": h["truth_r32"], "labels_eval_input": h["labels_r32_eval_input"],
                                                    "frozen_by": "the ORCH-07 declaration (superseded) and again by this declaration (RUN-SET-RULE.md)"},
        "reference_set": copy.deepcopy(sup["reference_set"]),
        "cohort": copy.deepcopy(sup["cohort"]),
        "reviews": {k: h[k] for k in ("review33", "review34", "review35", "review35_findings", "verification36", "verification36_findings", "verification37",
                                      "verification37_findings", "verification38", "verification38_findings", "verification39", "verification39_findings",
                                      "verification40", "verification40_findings", "verification40_package_check")},
        "policy": copy.deepcopy(sup["policy"]),
        "plan_sources": {k: h[k] for k in ("plan_v2", "stop_and_safety_rules", "budget_card_v2", "draft_declaration_v2", "binding_manifest_review31",
                                            "four_arm_final_declaration", "four_arm_final_usage")}
                        | {"draft_status": sup["plan_sources"]["draft_status"]},
        "revision_comparison_rule": copy.deepcopy(sup["revision_comparison_rule"]) | {"implementation": modules["literal_compare_r32"] | {"function": "norm_revision"}},
        "emission_rules": copy.deepcopy(sup["emission_rules"]),
        "interpretations": interp,
        "concentration_on_proposal": h["superseded_concentration_on_proposal"] | {
            "carried": ("concentration_r32.py is byte-identical in review36 and review39 (fc5052f8...) and the run set is unchanged, so the superseded "
                        "package's results on the proposal carry: ELIGIBLE reachable in every field, smallest ELIGIBLE net gain 2, never ELIGIBLE "
                        "for a net gain of 1 or a gain confined to one project / one layout (EP-27331 = the EMAAR template, 6 of 16 decision and 6 of "
                        "16 revision documents); 1,084 gain sets cross-checked, 0 mismatches (Verification 38 R38-12 reproduced it)")},
        "primary_outcomes": copy.deepcopy(sup["primary_outcomes"]),
        "thresholds_verbatim": thresholds_verbatim(sup, h),
        "gates": gates,
        "verification40_items": {
            "R40-04": "request_path_coverage (claim corrected, proof bound, residual risk, owner options)",
            "R40-08": "application_ai_limits.integer_strings; the R39-18 risk in disclosures and RUNBOOK section 6",
            "R40-10": "unread_page_rule.no_trigger_exclusion and unread_page_rule.unguarded_corners",
            "R40-12": "probe_population",
            "R40-13": "retry_rule (a change from plan v2 section 4) and stop_rules.verbatim_review39_resume_rules (replacing review34's)",
            "R40-15": "unread_page_rule.acknowledgement_R40_15",
            "R40-16": "model_identity_detail.probe and RUNBOOK section 1 (amended probe; the request count cannot be verified offline)",
            "R40-19": "harness.review39_snapshot_before (09:55:49Z)",
            "R40-20": "harness.review39_work_records (copied and bound by hash)"},
        "disclosures": disclosures_carried + [
            "window, not day: a project-window refusal is a deferral (never charged, never permanent); budget stops (lane allowance, parent, ledger, breaker, guard, identity, terminal) and provider-failure stops are durable and never undone by a resume (A-09 point 1; replaces the superseded R35-09 day-limit statement)",
            "the application's per-document limits are recorded as unread pages with the document COMPLETE, not as silent stops (R39-06, R40-15); the application's per-project limit is bound at 96 >= the required 84 and cannot refuse before the harness window",
            "rule CP-R38 replaces the .10-parity cross-page rule and closes H4 and H5: a wrong value equal to another page's identity is judged on the page (critical when automatically accepted) unless an R1-R3 relationship is recorded in the reviewed labels (CROSS-PAGE-WHATIF 491f9590...: 356 verdicts change on 89 fixtures)",
            "R40-04: the runtime gate's belt and braces holds for lane B only; C, R and P rest on proof (two static analyses, one dynamic run with get_provider() raising: 0 calls); residual risk and the owner's two options in request_path_coverage",
            "R40-13: the failed-read retry is a change from plan v2 section 4 (retry_rule); B and C can obtain an answer on a retry; results can depend on the number of invocations",
            "R40-12: P's population is drawn at P's first run (frozen sample), cap 36, seed unchanged",
            "R40-10: 'no_trigger' pages are not unread pages; two unguarded corners are declared out of reach in this run (unread_page_rule)",
            "R40-08 / R39-18: the bound validate_declaration still accepts '12.0' and '120.0'; such a value would pass the preflight, consume an owner authorization and then fail closed in every lane with no request sent (a wasted invocation, a run folder created); this declaration writes integer strings and the runbook's pre-invocation check refuses non-integer strings",
            "the runner records `claude --version` AFTER creating the run folder and BEFORE consuming the authorization: a version refusal at invocation 1 leaves a run folder without an allowance, which neither 'run' (folder exists) nor 'resume' (no allowance) can continue -- a new declaration with a new stamp would be needed; the runbook has the owner confirm the version line before invocation 1 (code reading of runner_r32.main, shown dry in PREFLIGHT-REPORT section 7)",
            "the served-model identity is UNRESOLVED offline; the runtime identity check is fail-closed with two stated limits (model_identity_detail)",
            "at the structural maximum with every request at the calibrated p95 of the largest task the output total (3,621,208) exceeds the scope output bound (3,260,000): the ledger would refuse first (estimated_usage.tokens_at_structural_maximum_p95); breaker margins are thin and shared (R38-13)",
            "path length: this machine has LongPathsEnabled = 0; the declared base and stamp keep the longest application path at 255 characters (run.base_justification); the application also opens long paths through its own extended-length helper",
            "the dry exercise of this declaration ran the bound review39 code unchanged (declared sandbox base C:/t/r2x/r40-sandbox, no twin) with reader 'none' and the refusing stub: it exercises the chain, the deferral / resume loop and the scorer and is not a result",
            "R40-19 / R40-20: review39's SNAPSHOT-BEFORE was taken at 09:55:49Z; review39's final work-folder AUDIT-LOG.md and PROGRESS.md are copied and bound here"],
        "forbidden_after_authorization": list(sup["forbidden_after_authorization"]) + [
            "using the frozen declaration file or the frozen hash with the runner (only the RUN file and the RUN hash)",
            "creating the ledger scope more than once, under another name or with other limits, or before the authorization file names the RUN hash",
            "running the model-identity probe through the harness or inside the experiment's ledger scope",
            "starting lane_r32 directly or with a hand-made configuration"],
        "what_this_run_can_show": sup["what_this_run_can_show"],
        "reference_set_statement": sup["reference_set_statement"],
    }


def main(argv=None) -> int:
    a = argparse.ArgumentParser(prog="build_declaration_r40.py")
    a.add_argument("command", choices=("show", "write", "fill_owner_digest", "verify_run_file", "write_authorization"))
    a.add_argument("--digest")
    a.add_argument("--run-sha")
    a.add_argument("--nonce")
    args = a.parse_args(argv)
    if args.command == "verify_run_file":
        r = verify_run_file(args.digest, args.run_sha)
        print(json.dumps(r, indent=1))
        return 0 if r["verified"] else 1
    if args.command == "fill_owner_digest":            # OWNER ONLY (never run by this task)
        frozen, fsha = frozen_bytes_checked()
        target = C.PACKAGE / C.RUN_NAME
        if target.exists():
            raise SystemExit("refused: the RUN file exists (one RUN file per declaration)")
        run = fill_owner_digest(frozen, args.digest)
        sha = C.write_once(target, run.decode("utf-8"))
        print(json.dumps({"frozen_sha256": fsha, "run_file": target.as_posix(), "run_sha256": sha}, indent=1))
        return 0
    if args.command == "write_authorization":          # OWNER ONLY (never run by this task)
        frozen, fsha = frozen_bytes_checked()
        run_path = C.PACKAGE / C.RUN_NAME
        run_decl = json.loads(run_path.read_text(encoding="utf-8"))
        digest = run_decl["authorization"]["owner_token_sha256"]
        check = verify_run_file(digest, args.run_sha, run_path)
        if not check["verified"]:
            raise SystemExit(f"refused: the RUN file does not verify: {check}")
        nonce = args.nonce or secrets.token_urlsafe(24)
        text = authorization_text(args.run_sha, digest, nonce, frozen_sha=fsha)
        C.write_once(C.PACKAGE / C.AUTH_NAME, text)
        print(json.dumps({"authorization": (C.PACKAGE / C.AUTH_NAME).as_posix(), "declaration_sha256": args.run_sha, "nonce_sha256": C.sha256_bytes(nonce.encode())}))
        return 0
    C.harness_import_path()
    h = hashes()
    copies = package_copies()
    led = C.ledger_state()
    if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or C.SCOPE in led["scope_names"]:
        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led['entries']}/{led['scopes']}/{led['limit_amendments']} (expected 483/17/0 and no scope {C.SCOPE!r})")
    if C.RUN_FOLDER.exists():
        raise C.PacketMismatch(f"refused: the run folder {C.RUN_FOLDER.as_posix()} already exists")
    for repo, head in (C.CANDIDATE, C.BASELINE):
        g = C.git_state(repo)
        if g["head"] != head or not g["clean"]:
            raise C.PacketMismatch(f"PACKET MISMATCH: {repo} {g}")
    declared_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    decl = build(h, copies, declared_at)
    text = C.json_text(decl)
    if text.count(json.dumps(C.TOKEN_PLACEHOLDER)) != 1:
        raise RuntimeError("the placeholder must occur exactly once (as authorization.owner_token_sha256)")
    import preflight_r32 as PF  # noqa: E402
    mem = json.loads(text)
    mem["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    PF.validate_declaration(mem, C.PACKAGE / C.DECLARATION_NAME)        # in memory: every contract-4 key passes
    try:
        PF.validate_declaration(json.loads(text), C.PACKAGE / C.DECLARATION_NAME)
        raise RuntimeError("the frozen declaration as written must be refused (placeholder digest)")
    except PF.Refused as exc:
        assert "binds no owner token digest" in str(exc), exc
    if args.command == "show":
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode("utf-8"))
        return 0
    target = C.PACKAGE / C.DECLARATION_NAME
    shafile = C.PACKAGE / "DECLARATION.sha256"
    if target.exists() or shafile.exists():
        raise SystemExit("refused: the declaration is written once; it exists")
    sha = C.write_once(target, text)
    C.write_once(shafile, f"{sha}  {C.DECLARATION_NAME}\n")
    print(json.dumps({"declaration": target.as_posix(), "sha256": sha, "bytes": len(text.encode("utf-8")), "declared_at_utc": declared_at}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
