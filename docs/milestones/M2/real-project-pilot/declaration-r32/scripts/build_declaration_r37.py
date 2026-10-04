"""ORCH-07 (R37DECL-IMPL): build and write ONCE the frozen fresh-validation declaration
`PILOT/declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json` and `DECLARATION.sha256` beside it.

The declaration is in the schema preflight_r32.validate_declaration requires (every required key) and is extended with the
ORCH-07 bindings, interpretations and disclosures. It is NOT an authorization: executed false, budget_approved false,
authorization status "none; owner decision pending", and authorization.owner_token_sha256 is an explicit placeholder that
the preflight refuses until the owner names the token digest in the budget authorization (no token exists; none is made
here). Every bound hash is recomputed at build time; a difference is PACKET MISMATCH and nothing is written.

Usage:  build_declaration_r37.py write            (refuses if the declaration or DECLARATION.sha256 exists)
        build_declaration_r37.py show             (prints the declaration it would write; writes nothing)
fill_owner_digest(frozen_bytes, digest) is the one-field derivation the owner's authorization step uses (pure; this task
never calls it with a real digest and never writes a filled declaration)."""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import sys

import estimates_r37 as E
import r37common as C

STAMP = "r32-fresh-validation-2026-10-03"
SCOPE = "m2-fresh-validation-r32-2026-10-03"
CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PROJECT_DAY_LIMIT = 60
LEDGER_LIMITS = {"requests": 556, "per_request_input": 90_000, "per_request_output": 20_000,
                 "input_tokens": 7_000_000 + 7_000_000 + 1_200_000 + 1_100_000, "output_tokens": 1_400_000 + 1_400_000 + 240_000 + 220_000,
                 "elapsed_s": (72 + 72 + 24) * 3600}
# the application's own AI limits, bound at the tree defaults (equal in the candidate and the baseline config.py; R35-16)
APPLICATION_LIMITS = {"AI_MAX_INPUT_TOKENS_PER_TASK": "6000", "AI_MAX_OUTPUT_TOKENS_PER_TASK": "800", "AI_MAX_CALLS_PER_DOCUMENT": "12",
                      "AI_MAX_CALLS_PER_PROJECT_PER_DAY": "60", "AI_MAX_COST_PER_JOB": "0.5", "AI_MAX_ELAPSED_S_PER_JOB": "120.0",
                      "AI_MAX_ESCALATIONS_PER_DOCUMENT": "2", "AI_MAX_CONCURRENCY": "2", "AI_MAX_RETRIES": "3",
                      "AI_PRICE_INPUT_PER_MILLION": "0.0", "AI_PRICE_OUTPUT_PER_MILLION": "0.0", "AI_PRICE_CACHED_INPUT_PER_MILLION": "0.0",
                      "AI_READ_MAX_CALLS_PER_DOCUMENT": "60", "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": "600", "AI_READ_MAX_ELAPSED_S": "1800.0",
                      "AI_READ_EFFORT": "high", "AI_CACHE_TTL_DAYS": "90"}
PROVIDER_CORE = {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus", "AI_EFFORT": "low",
                 "AI_TIMEOUT_S": "60", "AI_CLI_TIMEOUT_S": "300", "AI_CLAUDE_CLI": "claude"}
TREE_DEFAULTS = {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "claude-fable-5-1", "AI_MODEL_STANDARD": "claude-fable-5-1", "AI_EFFORT": "low",
                 "AI_TIMEOUT_S": "60.0", "AI_CLI_TIMEOUT_S": "300.0", "AI_CLAUDE_CLI": "claude"}

# frozen inputs bound by the declaration: name -> (path, expected sha256 or a task-given prefix)
BOUND = {
    "review36_manifest": (C.PILOT / "review36/evidence/EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0"),
    "binding_manifest_r36": (C.BINDING, "5a1a6aad63df91bbf6de1eb9d80fff44e4e05a2f70642bfa58f216ebf06fe568"),
    "literal_compare_r32": (C.HARNESS_PACKAGE / "literal_compare_r32.py", "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"),
    "test_literal_compare_r32": (C.HARNESS_PACKAGE / "test_literal_compare_r32.py", "66e0ddcf92ae4aaf350ca1143ad4f22f62ab777e12700c978652b276fdbb34c6"),
    "concentration_r32": (C.HARNESS_PACKAGE / "concentration_r32.py", "fc5052f80ea6d2454feadb84ccc863877cdc9851921f7c4dd551c58da914dffe"),
    "score_bcr_r32": (C.HARNESS_PACKAGE / "score_bcr_r32.py", "3436fe7d"),
    "runner_r32": (C.HARNESS_PACKAGE / "runner_r32.py", "22c71319"),
    "lane_r32": (C.HARNESS_PACKAGE / "lane_r32.py", "b46f5e0b"),
    "preflight_r32": (C.HARNESS_PACKAGE / "preflight_r32.py", "011c462c"),
    "dispatch_guard_r32": (C.HARNESS_PACKAGE / "dispatch_guard_r32.py", None),
    "allowance_r32": (C.HARNESS_PACKAGE / "allowance_r32.py", "803a65bb"),
    "lane_judge_r32": (C.HARNESS_PACKAGE / "lane_judge_r32.py", "a0b6b7c8"),
    "labels_adapter_r32": (C.HARNESS_PACKAGE / "labels_adapter_r32.py", "ff9d2e6b"),
    "tripwire_r32": (C.HARNESS_PACKAGE / "tripwire_r32.py", "42dc6226"),
    "score_lane_r32": (C.HARNESS_PACKAGE / "score_lane_r32.py", "c25f4d89"),
    "converter_r32": (C.HARNESS_PACKAGE / "converter_r32.py", "4095a496"),
    "sandbox_ingest_r32": (C.HARNESS_PACKAGE / "sandbox_ingest_r32.py", "3e0e906d"),
    "sandbox_child_r32": (C.HARNESS_PACKAGE / "sandbox_child_r32.py", "39bf11bc"),
    "capture_store": (C.HARNESS_PACKAGE / "capture_store.py", "84c05fc4"),
    "state_check": (C.HARNESS_PACKAGE / "state_check.py", "a9985b10"),
    "stop_rules": (C.HARNESS_PACKAGE / "stop_rules.py", "4632ffea"),
    "run_set_selector_r32": (C.HARNESS_PACKAGE / "run_set_selector_r32.py", "5c923ec8"),
    "h1_whatif_result": (C.PILOT / "review36/H1-WHATIF-RESULT.json", "19b14ab3"),
    "review34_manifest": (C.PILOT / "review34/evidence/EVIDENCE-MANIFEST.json", "64d5ba0d"),
    "binding_manifest_r34": (C.PILOT / "review34/BINDING-MANIFEST-R34.json", "3d0f8bfe"),
    "review33_manifest": (C.PILOT / "review33/evidence/EVIDENCE-MANIFEST.json", "c5001c95"),
    "review31_manifest": (C.PILOT / "review31/evidence/EVIDENCE-MANIFEST.json", "d5fe1649"),
    "live_run_contract": (C.PILOT / "review34/LIVE-RUN-CONTRACT.md", None),
    "concentration_rule_doc": (C.PILOT / "review34/CONCENTRATION-RULE-R32.md", None),
    "run_set_rule_doc": (C.PILOT / "review34/RUN-SET-RULE.md", None),
    "adapter_contract": (C.PILOT / "review34/ADAPTER-CONTRACT.md", None),
    "scorer_changes": (C.PILOT / "review34/SCORER-CHANGES.md", None),
    "run_set_proposal": (C.RUN_SET, "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"),
    "truth_r32": (C.PILOT / "review34/dry-run/TRUTH-R32.json", "4e237a4e"),
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
    "candidate_config": (pathlib.Path("C:/t/iso/cand-r29/backend/app/core/config.py"), None),
    "review33": (C.MR / "reviews/M2-review-33/INDEPENDENT-REVIEW.md", "8d20baec"),
    "review34": (C.MR / "reviews/M2-review-34/INDEPENDENT-REVIEW.md", "75061210"),
    "review35": (C.MR / "reviews/M2-review-35/INDEPENDENT-REVIEW.md", "f4f668ac"),
    "verification36": (C.MR / "reviews/M2-review-36/INDEPENDENT-VERIFICATION.md", "f698c2ff"),
    "verification37": (C.MR / "reviews/M2-review-37/INDEPENDENT-VERIFICATION.md", "288983f25996ce9143ea95f1b7d98f1ac1c581fcefb386014e407e8ecfe84126"),
    "review35_findings": (C.MR / "reviews/M2-review-35/FINDINGS.json", "b3ae349a"),
    "verification36_findings": (C.MR / "reviews/M2-review-36/FINDINGS.json", "9e65a5c0"),
    "verification37_findings": (C.MR / "reviews/M2-review-37/FINDINGS.json", "2f77e707"),
    "policy": (C.MR / "AI-ACCURACY-POLICY.md", "7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47"),
    "policy_amendment_r32_01": (C.MR / "AI-ACCURACY-POLICY-AMENDMENT-R32-01.md", "815d43fdb1e2177c5bc8e9bd680f6756acbdf3707ac8f19ca4fe9dc264205de6"),
    "authority_register": (C.MR / "orchestrator/AUTHORITY-REGISTER.md", None),
    "plan_v2": (C.PILOT / "review31/REVISED-FRESH-VALIDATION-PLAN.v2.md", None),
    "stop_and_safety_rules": (C.PILOT / "review31/STOP-AND-SAFETY-RULES.md", None),
    "budget_card_v2": (C.PILOT / "review31/BUDGET-DECISION-CARD.v2.md", None),
    "draft_declaration_v2": (C.PILOT / "review31/DRAFT-DECLARATION.v2.json", "19720ad9"),
    "binding_manifest_review31": (C.PILOT / "review31/BINDING-MANIFEST.json", "2dfef08e"),
    "four_arm_final_declaration": (C.PILOT / "four-arm-final/declaration/FINAL-DECLARATION.v2.json", "6c0189b3"),
    "four_arm_final_usage": (C.PILOT / "four-arm-final/USAGE-AND-BUDGET.json", None),
    "threshold_master_roadmap": (C.MR / "MASTER-ROADMAP.md", "f6dba0b2fce767955aed2b7508cfe7480637b02c44f502c3702c7862116e4c86"),
    "threshold_m2_acceptance_report": (C.M2 / "M2-ACCEPTANCE-REPORT.md", "7816ea793d0f4a0500ab3e2548c73975f7324b8ae0b37551683144844a14448b"),
    "threshold_review21_analysis_plan": (C.PILOT / "review21/ANALYSIS-PLAN.md", "76064b634dff6c32b1ec25f83e640a7170ed629ec219820c465553631b75b9c4"),
}


def hashes() -> dict:
    out = {}
    for name, (path, want) in BOUND.items():
        got = C.sha256_file(path)
        if want is not None and not got.startswith(want):
            raise C.PacketMismatch(f"PACKET MISMATCH: {name} {path} {got} does not match {want}")
        out[name] = {"path": pathlib.Path(path).as_posix(), "sha256": got}
    return out


def lines_verbatim(path, first: int, last: int, must_start: str) -> list:
    """Lines first..last (1-based, inclusive) of a source file, exactly as written (verbatim carry)."""
    lines = pathlib.Path(path).read_text(encoding="utf-8").split("\n")[first - 1:last]
    if not lines or not lines[0].startswith(must_start):
        raise C.PacketMismatch(f"PACKET MISMATCH: {path} line {first} does not start with {must_start!r}")
    return lines


def thresholds_verbatim(h) -> list:
    draft = json.loads((C.PILOT / "review31/DRAFT-DECLARATION.v2.json").read_text(encoding="utf-8"))
    src = {"AI-ACCURACY-POLICY.md section 1": "policy", "M2-ACCEPTANCE-REPORT.md Correction 5 targets": "threshold_m2_acceptance_report",
           "MASTER-ROADMAP.md M2": "threshold_master_roadmap", "review21/ANALYSIS-PLAN.md section 5": "threshold_review21_analysis_plan"}
    out = []
    for item in draft["thresholds_verbatim"]:
        name = src[item["source"]]
        if item["sha256"] != h[name]["sha256"]:
            raise C.PacketMismatch(f"PACKET MISMATCH: threshold source {item['source']}")
        text = pathlib.Path(h[name]["path"]).read_text(encoding="utf-8")
        for t in (item["text"] if isinstance(item["text"], list) else [item["text"]]):
            if t not in text:
                raise C.PacketMismatch(f"PACKET MISMATCH: threshold text not verbatim in {item['source']}: {t[:60]}")
        out.append({"source": item["source"], "path": h[name]["path"], "sha256": item["sha256"], "text": item["text"],
                    "verbatim_check": "every text item is a substring of the source file at this sha256 (checked at build time)"})
    return out


def lane_switches() -> dict:
    draft = json.loads((C.PILOT / "review31/DRAFT-DECLARATION.v2.json").read_text(encoding="utf-8"))
    arms = draft["arms"]
    assert arms["B"]["switches"] == {} and arms["B"]["meaning"] == "accepted path, evidence reader off"
    return {"B": {"AI_EVIDENCE_VARIANT": "off"}, "C": dict(arms["C"]["switches"]), "R": dict(arms["R"]["switches"]), "P": {}}


def fill_owner_digest(frozen: bytes, digest: str) -> bytes:
    """The ONE derivation of the runnable declaration: the placeholder value of authorization.owner_token_sha256 replaced
    by the owner's 64-hex token digest; nothing else changes. Pure (no file is read or written)."""
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


def build(est: dict, h: dict, declared_at: str) -> dict:
    pinned = (C.PACKAGE / C.AUTH_NAME).as_posix()
    run_folder = (C.LIVE_SANDBOX_BASE / STAMP).as_posix()
    rs = json.loads(C.RUN_SET.read_text(encoding="utf-8"))
    provider_env = dict(PROVIDER_CORE) | {"AI_LEDGER_PATH": C.AI_LEDGER.as_posix(), "AI_LEDGER_SCOPE": SCOPE,
                                           "AI_LEDGER_LIMITS": json.dumps(LEDGER_LIMITS, sort_keys=True)} | dict(APPLICATION_LIMITS)
    stop_table = lines_verbatim(h["stop_and_safety_rules"]["path"], 7, 20, "| Event | Lane |")
    resume_rules = lines_verbatim(h["live_run_contract"]["path"], 67, 73, "- **run** refuses")
    nonce_rules = lines_verbatim(h["live_run_contract"]["path"], 49, 53, "**One run, one nonce.**")
    sw = lane_switches()
    tok = est["tokens"]
    return {
        "schema": "orch07-fresh-validation-declaration-r32.1",
        "name": "M2 fresh validation R32: accepted baseline B vs Review 29 combined candidate C, with reference R and variation probe P",
        "task": "ORCH-07 (orchestrator ledger ORCH-016), implementation agent R37DECL-IMPL, Claude Opus 5.5 (claude-opus-5-5), effort High",
        "authorities": {"register": h["authority_register"], "applied": ["A-03", "A-06", "A-08"],
                        "summary": {"A-01": "Review 32 verdict: cohort preparation only", "A-02": "owner cohort access, staging, rendering, drafting and preparation for EP-3563, 22349, 27331, 15744, 26687, 29255 (no dispatch)",
                                    "A-03": "Claude-only workflow; Opus 5.5 High implementation agents, one write-capable agent at a time",
                                    "A-04": "AI-ACCURACY-POLICY section 8 amendment R32-01 (AI-reviewed reference set)",
                                    "A-05": "concentration rule replacement (stratum leg removed; project, contractor, layout legs)",
                                    "A-06": "project and provider ELIGIBILITY for the six cohort projects only: frozen staged sandbox copies, verified hashes, no OneDrive modification, no production or live-service writes, no sealed project, no use outside this final frozen declaration; NOT dispatch, ledger scope, budget, B/C/R/P execution, production use, M2 acceptance or M3",
                                    "A-07": "Review 33 rulings adopted without overrides (reviewed-2 is the reference set; 57/38/38)",
                                    "A-08": "the authorized sequence stops at ORCH-07 before any ledger scope, request, budget, run, default, M2 acceptance or M3"}},
        "declared_at_utc": declared_at,
        "status": "FROZEN DECLARATION, NOT AUTHORIZED: no ledger scope, no token, no authorization file and no dispatch exist; the owner's budget decision is pending",
        "executed": False,
        "budget_approved": False,
        "authorization_status": "none; owner decision pending",
        "standing_status": {"M2": "CHANGES STILL REQUIRED", "M3": "not started"},
        # ---- the preflight contract (preflight_r32.validate_declaration) -----------------------------------------------
        "binding_manifest_sha256": h["binding_manifest_r36"]["sha256"],
        "run_set_sha256": h["run_set_proposal"]["sha256"],
        "run": {"stamp": STAMP, "folder": run_folder,
                "rule": "one run folder, one allowance (caps and day limit bound in the file) and one capture store per declaration, all bound to the declaration sha256 (the run key); 'run' once, then 'resume' only, with the same stamp",
                "allowance": f"{run_folder}/allowance.sqlite", "capture_store": f"{run_folder}/capture.sqlite", "run_state": f"{run_folder}/RUN-STATE.json",
                "never_moved_or_deleted": "the run folder holds the one-run anchors (consumed nonces, allowance charges); it is never moved or deleted (R35-07)",
                "base_of_the_bound_code": "C:/t/r2x/r34-sandbox is the SANDBOX_BASE of the bound preflight_r32 / runner_r32 (Verification 37 item 1); the folder does not exist at declaration time"},
        "authorization": {
            "status": "none; owner decision pending",
            "path": pinned,
            "owner_token_sha256": C.TOKEN_PLACEHOLDER,
            "placeholder_rule": ("owner_token_sha256 holds an explicit placeholder, not a digest: preflight_r32.validate_declaration and dispatch_guard_r32 refuse "
                                 "it ('the declaration binds no owner token digest'). No token exists and none was generated. The owner names the 64-hex "
                                 "sha256 of a token the owner chooses in the budget authorization; the runnable declaration is this file with that one value "
                                 "replaced and nothing else changed (build_declaration_r37.fill_owner_digest); its own sha256 is the hash the runner, the lanes, "
                                 "the guard and the authorization file use"),
            "file_fields": {"declaration_sha256": "the sha256 of the runnable (digest-filled) declaration file", "owner_token_sha256": "the same digest the runnable declaration binds",
                            "authorized_by": "owner", "nonce": "a fresh one-run nonce, 16-128 characters [A-Za-z0-9_-], one per invocation"},
            "nonce_rule_verbatim": {"source": h["live_run_contract"]["path"], "sha256": h["live_run_contract"]["sha256"], "lines": "49-53", "text": nonce_rules},
            "token_holder": "owner",
            "token_presentation": "the owner presents the token in the environment variable R34_OWNER_DISPATCH_TOKEN at each invocation; it is compared by digest and never written to any file",
            "one_invocation_per_authorization": "run and every resume each consume one authorization with a fresh nonce into <run folder>/authorization/consumed-<sha256(nonce)[:32]>.json (O_EXCL)",
            "runbook": [
                "R35-07 / R35-10: the owner creates the ledger scope NEW and EMPTY with exactly ledger.limits and a closed breaker, immediately before the first invocation (the ledger measures elapsed_s from the scope's creation); the harness never creates a scope",
                "R35-07: before each invocation the scope's dispatch entries are reconciled with the allowance charges (allowance.sqlite) and any difference stops the run until explained",
                "R35-06: the owner withdraws or replaces OWNER-DISPATCH-AUTHORIZATION.json at the end of every invocation",
                "R35-06 / R35-08: live lanes are started only by runner_r32 (never lane_r32 directly, never a hand-made lane configuration)",
                "R35-19: absolute paths for --declaration, --binding and --run-set; no python -O; PYTHONDONTWRITEBYTECODE=1; GIT_OPTIONAL_LOCKS=0 (the HEAD check runs git status in the candidate and baseline trees)",
                "R35-07: the run folder is never moved or deleted",
                "after a crashed runner the operator removes WRITER.lock only once no runner process is alive",
                "R35-09: a budget stop or provider-failure stop is not undone by a resume; resume is refused after a terminal comparison (RESULT, INVALID) and after a complete run"],
            "invocation": {"working_directory": C.HARNESS_BOUND.as_posix(),
                           "run": "python runner_r32.py run --mode live --declaration <absolute path of the runnable declaration in PILOT/declaration-r32/> --declaration-sha <its sha256> --run-set " + C.RUN_SET.as_posix() + " --binding " + C.BINDING.as_posix() + " --binding-sha " + h["binding_manifest_r36"]["sha256"],
                           "resume": "the same with 'resume' (a new authorization with a fresh nonce first)",
                           "harness_copy": "C:/t/iso/work/r2x/r36/harness-r32 is the copy BINDING-MANIFEST-R36 binds as harness_r36; PILOT/review36/scripts/harness-r32 is byte-identical (harness_r36_package)"}},
        "caps": dict(CAPS),
        "project_day_limit": PROJECT_DAY_LIMIT,
        "lane_switches": sw,
        "provider_env": provider_env,
        "ledger": {"path": C.AI_LEDGER.as_posix(), "scope": SCOPE, "limits": dict(LEDGER_LIMITS), "wrap_provider": True},
        # ---- extended bindings --------------------------------------------------------------------------------------
        "caps_detail": {"total": sum(CAPS.values()), "equal_allowance_B_C": "B 240 = C 240 (8 per document x 30 documents): the request gate is defined at equal caps (R31-03)",
                        "per_document_cap_basis": "8 requests per document x 30 documents = 240; the run set holds 24 documents (192 at 8 per document)",
                        "enforcement": "allowance_r32 reserves before dispatch per lane (never refunded, never raised) and the ledger scope's 'requests' limit 556 is the cumulative backstop"},
        "project_day_limit_detail": {
            "value": PROJECT_DAY_LIMIT, "range_allowed_by_preflight": "1..60",
            "justification": ["60 is the largest value the frozen preflight accepts and equals plan v2 section 7 and the application's own ai_max_calls_per_project_per_day",
                              "a lower value only adds refusals: it adds no safety that the lane caps, the ledger scope's request limit (556) and its token and elapsed limits do not already give",
                              "per-project estimate (estimated_usage.per_project): EP-27331 is the binding project: 6 documents, 23 pages read by C, every document decision-bearing; B + C planning 52 and at most 54 (B one form read per decision-bearing document, C 8 per document) in one UTC day, below 60; all lanes planning 63 (B 6, C 46, R 4.1, P 6.9)"],
            "incomplete_risk": ["a B or C request refused by the day limit is a budget stop of that lane and makes the comparison INCOMPLETE; for EP-27331 that needs B's EP-27331 requests above 12 together with C's maximum of 48 in one UTC day, which the estimates do not expect but cannot exclude",
                                "R and P run after C: at the planning estimate EP-27331 reaches 60 during P (63 in all), so P (report-only) and, in a conservative case, R can be refused for EP-27331; a refusal stops that lane for the rest of the invocation (R's contrasts, including decision coverage C >= R, are then computed on a truncated R)",
                                "R35-09: a day-limit refusal is settled as a failed row and served again on every resume, even on a later UTC day: it is permanent for the run",
                                "a run that crosses 00:00 UTC starts a new day count for every project"],
            "owner_alternative": "accept this risk with the authorization, or order a harness change (a higher ceiling or a refusal retryable after the UTC day changes) with re-freeze, independent re-review and a new declaration before any authorization"},
        "lanes": {
            "B": {"meaning": "the accepted baseline: the application's accepted processing path, evidence reader off", "tree": C.BASELINE[0], "commit": C.BASELINE[1],
                  "switch_basis": "DRAFT-DECLARATION.v2 arm B has switches {} meaning 'accepted path, evidence reader off'; the preflight requires B to state AI_EVIDENCE_VARIANT, so it is stated explicitly as 'off' (the tree default)",
                  "runs": "first, on a sandbox where sandbox_ingest_r32 registered exactly the run set without processing; tripwire after every document; B's database sha256 recorded at the end"},
            "C": {"meaning": "the combined candidate: L3 switch set plus IG (AI_EVIDENCE_IDGUARD), CA (AI_EVIDENCE_ADJUDICATE), DR (AI_EVIDENCE_DECISION_REGION) and PA (AI_EVIDENCE_ASSOC)",
                  "tree": C.CANDIDATE[0], "commit": C.CANDIDATE[1], "starts_from": "a copy of B's final database; state_check.check_c_start must pass (recorded B file hash, equal logical content, no C-policy or unattributed evidence, no evidence-task cache row)",
                  "runs": "after the C-from-B state check, one run-set document at a time, tripwire after every document"},
            "R": {"meaning": "the reference (L3 switch set): served C's capture by content key whatever its outcome; a request C never made is sent once as reference-only in lane R",
                  "tree": C.CANDIDATE[0], "commit": C.CANDIDATE[1], "starts_from": "a copy of B's final database (state check as for C)",
                  "role": "offline contrast only; never a gate input except decision coverage C >= R; never a live stop (a resolved-truth critical in R is a reference finding)"},
            "P": {"meaning": "the variation probe: a seeded 15 % of C's answered dispatches (seed m2-r30-variation-2026-10-02) re-sent once in lane P", "switches": {},
                  "role": "reported only; never served to B or C; never a score", "tree": C.CANDIDATE[0]}},
        "switch_names": {"IG": "AI_EVIDENCE_IDGUARD", "CA": "AI_EVIDENCE_ADJUDICATE", "DR": "AI_EVIDENCE_DECISION_REGION", "PA": "AI_EVIDENCE_ASSOC",
                         "L3": ["AI_EVIDENCE_VARIANT=EV1", "AI_EVIDENCE_GUARD=1", "AI_EVIDENCE_SUPPORT=v2", "AI_EVIDENCE_SCHEDULING=required_first", "AI_EVIDENCE_DEADLINE=1", "AI_EVIDENCE_TARGETED=1"],
                         "source": "DRAFT-DECLARATION.v2 arms (restated here, not inherited); candidate app/ai/evidence_reader.py switch definitions; four-arm-final arm L3 env"},
        "dispatch_order": ["preflight (binding manifest and every bound file, the declaration contract, run set, candidate and baseline HEADs clean, truth and population gate, the declared ledger scope exists with exactly the declared limits and a closed breaker, the dispatch guard preview)",
                           "B: sandbox_ingest_r32 registers exactly the 24 run-set documents (no processing); lane B processes them with the tripwire after every document; B's final database sha256 recorded",
                           "C-from-B state check: C's and R's sandboxes are copies of B's final database; state_check.check_c_start must pass for each (B INVALID means C never starts)",
                           "C: the evidence stage on each run-set document with C's switches; tripwire after every document",
                           "R: served from C's capture by content key; requests C never made are dispatched once as reference-only",
                           "P: the probe over C's answered dispatches",
                           "offline scoring: score_lane_r32 per lane, then score_bcr_r32.evaluate with the candidate-level outcome"],
        "provider": {
            "environment_keys": "the ten required keys plus the application's own AI limits, all strings, all verified by every live lane (provider_env)",
            "proposed_vs_tree_defaults": {k: {"declared": provider_env[k], "candidate_and_baseline_tree_default": TREE_DEFAULTS[k]} for k in PROVIDER_CORE},
            "basis": {"four_arm_final_declaration": {"sha256": h["four_arm_final_declaration"]["sha256"], "provider_env": {"AI_PROVIDER": "claude-code", "AI_MODEL_SMALL": "sonnet", "AI_MODEL_STANDARD": "opus"},
                                                     "cli_version_recorded": "2.1.263 (Claude Code)", "effort": "not declared (tree default low)"},
                      "ai_ledger_models_recorded": {"claude-sonnet-5": 457, "claude-opus-5": 5, "sonnet": 13, "(blank)": 8, "note": "read-only count over the 483 entries: the claude-code adapter records the model the CLI reports (claude-sonnet-5 for the 'sonnet' alias, claude-opus-5 for 'opus'); 'sonnet' / blank are timeouts and unknown usage"}},
            "owner_confirmable": {
                "AI_MODEL_SMALL": "declared 'sonnet' (the four-arm alias; recorded as claude-sonnet-5); alternatives: the full id 'claude-sonnet-5' (pins the model if the alias moves), or the tree default 'claude-fable-5-1'",
                "AI_MODEL_STANDARD": "declared 'opus' (recorded as claude-opus-5; used only for escalations, at most 2 per document); alternatives: 'claude-opus-5', or the tree default 'claude-fable-5-1'",
                "AI_EFFORT": "declared 'low' (the tree default; the four-arm declaration bound no effort, so its tree default 'low' applied); the claude-code adapter passes no effort flag to the CLI, so with AI_PROVIDER claude-code the effort does not change a request; it applies only to the API provider",
                "project_day_limit": "declared 60 (project_day_limit_detail)",
                "ledger.scope": f"declared {SCOPE!r} (a new name; no scope of that name exists)",
                "rule": "cost and accuracy depend on these values; changing any of them is a new declaration with a new sha256, frozen and verified before any authorization"},
            "ledger_provider": "the application's LedgerProvider wraps the real provider and writes to the declared scope (wrap_provider true)",
            "cost_note": "the claude-code adapter bills the signed-in Claude subscription; the application has no price configured (AI_PRICE_* 0.0), so the application's cost column is 0 and reported as unknown, never as zero cost"},
        "application_ai_limits": {
            "bound": dict(APPLICATION_LIMITS),
            "statement": "bound in provider_env at the candidate and baseline tree defaults (equal in both config.py files; no .env file exists in either tree; sandbox_env strips every AI_* variable of the operator's environment); every other AI setting stays at its tree default",
            "silent_stops": ["the evidence reader opens one JobBudget per document: at most 12 calls (the reader's own MAX_CALLS_PER_DOCUMENT 8 binds first), 120 s elapsed per document job, at most 2 escalations, 6,000 estimated input / 800 output tokens per task; a limit that trips stops that document's reading silently (recorded as a budget stop in the attempt, not a harness stop)",
                             "the application's own 60 calls per project per rolling 24 h counts AiUsage rows in the lane's sandbox; C and R sandboxes are copies of B's database, so B's calls count toward C's and R's limit",
                             "B's submittal-form reader uses the ai_read_* limits (60 calls per document, 600 per project per day, 1,800 s)"]},
        "token_thresholds": {
            "per_request": {"input": 90_000, "output": 20_000, "semantics": "reservation thresholds on ESTIMATES before dispatch (the ledger's estimator: the larger of an analytic estimate and the task's calibrated p95); an actual overshoot opens the breaker for later requests; the claude-code CLI has no hard input or output bound; never hard limits"},
            "per_lane_estimated": {"B": [7_000_000, 1_400_000], "C": [7_000_000, 1_400_000], "R": [1_200_000, 240_000], "P": [1_100_000, 220_000], "unit": "[input, output] tokens, estimated"},
            "enforced": "only the single scope's totals input_tokens 16,300,000 and output_tokens 3,260,000 (the sum of the lane thresholds) and the per-request thresholds; per-lane token equality between B and C is NOT enforced (R35-10)"},
        "elapsed_bounds": {"B_hours": 72, "C_hours": 72, "R_and_P_hours_after_C": 24,
                           "enforced": "only the scope's elapsed_s 604,800 s (168 h), which the application's ledger measures from the scope's CREATION (scopes.created_at), not from its first use; per-lane elapsed bounds are declared, not enforced (R35-10); every resume and any delay between creating the scope and the first invocation count"},
        "estimated_usage": {"documents": est["documents"], "lanes": est["lanes"], "tokens": est["tokens"], "per_project": est["projects"],
                            "per_request_basis": est["per_request_basis"], "model": est["model"],
                            "plan_v2_expected_for_comparison": {"B": "about 6", "C": "about 135", "R": "about 10", "P": "about 20", "note": "for up to 30 documents, from the four-arm sample (Review 33 asked for a re-estimate on the r32 run set: this section)"},
                            "statement": "estimates, not limits and not measurements; the caps and the ledger limits are the bounds"},
        "cost": {"status": "unknown", "rule": "never treated as zero; no authoritative price is configured for the declared provider (claude-code on the owner's subscription; AI_PRICE_* 0.0)"},
        "ledger_detail": {
            "one_scope_for_all_lanes": "one scope serves B, C, R and P; the owner may instead order per-lane scopes, which is a new declaration (R35-10)",
            "r35_10_consequence": "only the request caps are per lane (the allowance); the lane token and elapsed thresholds of plan v2 section 7 are not enforced per lane, so equality of tokens and elapsed time between B and C is not enforced; the scope's totals are the sum of the lane thresholds",
            "limits_keys": "every key is a field of the application's ledger Limits (requests, input_tokens, output_tokens, per_request_input, per_request_output, elapsed_s); requests 556 = the caps",
            "creation": "created only by the owner's budget authorization naming the declaration hash; new and empty, exactly these limits, closed breaker; this task created no scope (AI ledger 483 entries / 17 scopes / 0 amendments before and after)",
            "live_check": "after the run the ledger may have grown only inside the declared scope (no new scope, no limit amendment, every other scope unchanged) and by at most 556 dispatch entries"},
        "stop_rules": {
            "verbatim_stop_and_safety_rules": {"source": h["stop_and_safety_rules"]["path"], "sha256": h["stop_and_safety_rules"]["sha256"], "lines": "7-20", "text": stop_table},
            "verbatim_review34_resume_rules": {"source": h["live_run_contract"]["path"], "sha256": h["live_run_contract"]["sha256"], "lines": "67-73", "text": resume_rules},
            "implementation": "stop_rules.StopController (unchanged copy, 4632ffea...) replays every lane's events; the tripwire is per field (pool id, page, field)",
            "summary": ["budget stops and provider-failure stops are not undone by a resume", "resume is refused after a terminal comparison (RESULT, INVALID) and after a complete run",
                        "R and P stops affect only their own lane"]},
        "harness": {
            "package": "PILOT/review36/", "package_manifest": h["review36_manifest"], "binding_manifest": h["binding_manifest_r36"] | {"entries": 155,
                        "supersedes": "review34/BINDING-MANIFEST-R34.json 3d0f8bfe... for the harness code; every other review34 binding entry is carried unchanged"},
            "changed_module": {"literal_compare_r32.py": h["literal_compare_r32"] | {"replaces": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6"},
                               "test_literal_compare_r32.py": h["test_literal_compare_r32"]},
            "modules": {k: h[k] for k in ("runner_r32", "lane_r32", "preflight_r32", "dispatch_guard_r32", "allowance_r32", "score_bcr_r32", "concentration_r32",
                                          "lane_judge_r32", "labels_adapter_r32", "tripwire_r32", "score_lane_r32", "converter_r32", "sandbox_ingest_r32",
                                          "sandbox_child_r32", "capture_store", "state_check", "stop_rules", "run_set_selector_r32")},
            "concentration_rule": {"version": "concentration-r32-2026-10-03.2", "code": h["concentration_r32"], "document": h["concentration_rule_doc"]},
            "contracts": {"live_run_contract": h["live_run_contract"], "adapter_contract": h["adapter_contract"], "scorer_changes": h["scorer_changes"], "run_set_rule": h["run_set_rule_doc"]},
            "lineage": {"review34": {"manifest": h["review34_manifest"], "binding": h["binding_manifest_r34"], "accepted_by": "Review 35"},
                        "review33": {"manifest": h["review33_manifest"], "accepted_by": "Review 34 (with corrections RC-1 to RC-6, closed by review34)"},
                        "review31": {"manifest": h["review31_manifest"], "binding": h["binding_manifest_review31"]}},
            "accepted_by": "Verification 37 (ORCH-06C VERIFIED); H1 closed",
            "h1_whatif": h["h1_whatif_result"],
            "bound_code_used_as_is": "the bound code runs unchanged from C:/t/iso/work/r2x/r36/harness-r32 (its SANDBOX_BASE C:/t/r2x/r34-sandbox); a relocated copy would be a new binding (Verification 37 item 1)"},
        "evaluator": {"file": h["evaluator_10"], "version": "m2-pilot-eval-2026-10-02.10", "role": "EMISSION ONLY (Verification 36 section 6 item 1)",
                      "bound_functions": ["record_groups", "observation_groups", "ai_groups (with ai_envelope and evidence_reader.evidence_for), through tripwire_r32.facts_from_row"],
                      "not_bound": ["evaluate", "associate_group", "judge_group", "score_layer", "_same"],
                      "judging": "every verdict, metric, tripwire, coverage figure, control and gate comes from lane_judge_r32 + literal_compare_r32; .10 judging is never bound; plan v2 section 4 step 7 is read this way",
                      "candidate_unchanged": "no candidate correction; a .10 judging verdict would first need a candidate correction (R1 to R6, R7 optional) with its own review",
                      "offline_test": {"package_manifest": h["evaluator_offline_r32_manifest"], "binding": h["evaluator_offline_binding_r35"], "verified_by": "Verification 36 (with conditions, closed by review36 and Verification 37)"}},
        "trees": {"candidate": {"tree": C.CANDIDATE[0], "head": C.CANDIDATE[1], "clean": True, "config_py": h["candidate_config"]},
                  "baseline": {"tree": C.BASELINE[0], "head": C.BASELINE[1], "clean": True}},
        "run_set": {"path": C.RUN_SET.as_posix(), "sha256": h["run_set_proposal"]["sha256"], "documents": rs["count"], "by_reason": rs["by_reason"],
                    "pool_ids": [d["pool_id"] for d in rs["documents"]], "selector": h["run_set_selector_r32"], "seed": rs["rule"]["seed"], "rule_version": rs["rule"]["version"],
                    "truth": h["truth_r32"], "labels_eval_input": h["labels_r32_eval_input"], "per_field_matched_projection": {f: {"documents": v["documents"], "margin_over_12": v["margin_over_minimum_12"], "by_project": v["by_project"]}
                                                                                                                           for f, v in rs["per_field_matched_projection"].items()},
                    "decision_controls": rs["decision_controls_in_run_set"], "aliases_excluded": rs["aliases_excluded"], "frozen_by": "this declaration (RUN-SET-RULE.md: the proposal is frozen only by the ORCH-07 declaration)"},
        "controls": {"positive_decision": 16, "negative_decision": {"documents": 8, "pool_ids": ["F042", "F043", "F046", "F047", "F051", "F057", "F060", "F066"],
                                                                    "composition": "the 4 negative controls (F051, F042, F047, F066) plus the 4 revision top-ups (F060, F043, F057, F046), whose decision truth is a resolved absence"},
                     "negative_controls_drawn": 4,
                     "executable_definitions": {"negative": "canonical, not yet drawn, decision resolved_for_scoring yes, every in-scope decision row a scorable ABSENT (blank_decision_area or no_decision_area): the adapter's decision_control == 'negative'",
                                                "unsupported": "canonical, not yet drawn, at least one in-scope page with a field labelled 'unsupported' or 'illegible'"},
                     "unsupported_control_shortfall": {"required": 2, "found": 0, "deviation": "plan v2 section 2.3 deviation: no canonical pool document has an in-scope page labelled unsupported or illegible in r32-labels-reviewed-2; NO substitute is drawn; unsupported-input behaviour is not validated by this run; any substitute is an owner decision, from the pool only, and a new declaration"}},
        "reference_set": {"labels": h["reviewed2_labels"], "name": "r32-labels-reviewed-2", "field_population": h["reviewed2_field_population"] | {"identity": 57, "revision": 38, "decision": 38, "extensions_used": 0},
                          "packages": {"fresh-cohort-r32": h["package_fresh_cohort_r32"], "fresh-cohort-r32-reviewed": h["package_fresh_cohort_r32_reviewed"], "fresh-cohort-r32-reviewed-2": h["package_fresh_cohort_r32_reviewed_2"]},
                          "conventions": h["label_conventions"], "label_review_response_final": h["label_review_response_final"],
                          "assurance_level": "AI-drafted (Claude Opus 5.5) and independently AI-reviewed by separate Claude agents under AI-ACCURACY-POLICY-AMENDMENT-R32-01: an AI-reviewed reference set, NOT human-signed labels, NOT human Golden Truth, NOT independently human-verified evidence; the reviewers and the evaluated extraction models (Claude Sonnet 5 / Opus 5) are of the same model family",
                          "statement": "reference set independently AI-reviewed (Claude agents), not human-signed"},
        "cohort": {"projects": ["EP-3563", "EP-22349", "EP-27331", "EP-15744", "EP-26687", "EP-29255"], "access_authority": h["cohort_authorization_a02"] | {"entry": "A-02"},
                   "eligibility_authority": "A-06 (project and provider eligibility; C-9)", "verification": "10 of 10, no replacement", "sealed": "none opened; excluded",
                   "selection": h["frozen_selection"] | {"seed": "m2-r30-pool-2026-10-02"}, "project_verification": h["project_verification"],
                   "staging": {"root": "C:/t/r2x/r32-stage", "source_manifest": h["source_manifest"], "renders": h["renders"], "evidence_index": h["evidence_index"]},
                   "onedrive": "originals never modified; the run reads only frozen staged sandbox copies"},
        "reviews": {k: h[k] for k in ("review33", "review34", "review35", "verification36", "verification37", "review35_findings", "verification36_findings", "verification37_findings")},
        "policy": {"policy": h["policy"], "amendment_r32_01": h["policy_amendment_r32_01"], "statement": "the original policy is unchanged; amendment R32-01 (A-04) is bound by its own hash and applies only to the frozen R32 cohort and its declared extensions"},
        "plan_sources": {k: h[k] for k in ("plan_v2", "stop_and_safety_rules", "budget_card_v2", "draft_declaration_v2", "binding_manifest_review31", "four_arm_final_declaration", "four_arm_final_usage")}
                        | {"draft_status": "DRAFT-DECLARATION.v2 is superseded by this declaration; its arm switches are restated here, its stale bindings (Review 33 section 5.2) are replaced"},
        "revision_comparison_rule": {
            "implementation": h["literal_compare_r32"] | {"function": "norm_revision"},
            "rule": "Arabic literals: whitespace removed, compared byte for byte (no case or dash folding, Arabic-Indic digits not mapped). Otherwise dash variants are read as '-', the value is upper-cased, runs of whitespace collapse to one space and the ends are stripped; then after an OPTIONAL prefix REVISION / REV / REV. / R / R. every whitespace character inside the value is removed before 0*(\\d+) is matched, and a number is compared by value: '0 1' == '01' == 'REV 0 1' == 'R 01' -> R1; '0 0' -> R0; 'Rev. 0 2' -> R2. A value that is not a number keeps its own characters with every whitespace character removed ('A 1' -> 'A1').",
            "not_ignored": "whitespace INSIDE the prefix word or before its dot is NOT ignored: 'R EV 01', 'R E V 0 1', 'REV . 1' and 'R ev. 0' do not match their number (Verification 37 R37-04)",
            "exposure": "0 truth literals and 0 fixture values in the frozen r32 material (Verification 37)",
            "residual_risk": "a letter-spaced labelled revision read by C's AI path (validate_value keeps the literal) is not normalised and, where the truth is resolved, is a critical acceptance on resolved truth that stops C (RESULT): a false C stop on a correct reading is possible but has not been observed in the frozen material",
            "h1": "H1 (whitespace inside the number, 53 ws_inside_number rows, 23 in the run set) is corrected by review36 and verified by Verification 37"},
        "emission_rules": {"source": "Verification 36 R36-07 (bound emission semantics of evaluator .10; application semantics, not .10 judging)", "rules": {
            "a": "a register decision is emitted only for the statuses approved, ANN and rejected",
            "b": "the revision is printed_revision; failing that, the business revision is emitted only when its source is printed, cover or suffix (in the application's R<n> form); folder and default revisions are never emitted",
            "c": "held, not asserted: an identity whose reference is flagged incomplete or uncertain; every fact of a pending-evidence record; decision candidates",
            "d": "a fact without a page goes to page 1",
            "e": "AI path (C and R only): only the current envelope for the row's sha256, profile, variant and policy is used; identities whose role is not own are dropped; non-validated observations are held; a dependent fact whose application association is held:* is held",
            "f": "deterministic observations are emitted as observed; a transmittal's listed record numbers become observed identity facts on that page (never critical, but the row becomes recovered_mixed and y = 0)"}},
        "interpretations": {
            "review33_c2": [
                "(c)(ii) count-once for render-identical duplicates without an added field fact: ADOPTED by Review 33 as an amendment to convention section 1 for this cohort (F031 -> F001 with the caveat that F031 has pages 3 and 4, which add no field value; F059 -> F046); byte-identical F052 -> F038 and F070 -> F067 under frozen section 1; populations 57/38/38 (59/40/39 without it)",
                "(d1) mixed options such as 'Approved as noted / Resubmit', 'Code B+Resubmit' and 'B+R' are class 'approved as noted' with the literal kept and resubmission_required = yes (9 rows); the scorer tolerates a prediction that reports the resubmission condition (the (d1) tolerance below)",
                "(e) / D-001: a code letter's class follows the meaning of its printed legend, never the letter alone (wording that sends the document back for resubmission is 'revise and resubmit'; a plain refusal is 'rejected'); F025 Code C 'Not Approved (Re-submit...)' is revise and resubmit",
                "(g)(1): a tail on the page's own reference that carries its own 'Rev.' label is a labelled revision with association resolved; the identity is the number without the tail, and the scorer accepts either form; an unlabelled own-number suffix ((g)(2)) is present with association uncertain and is not counted (conventions section 4)",
                "(g2) / D-002: on a reply-to-comments or comments-resolution sheet the reference is the page identity (association resolved) when it equals the own number of a submittal in the same staged file (F028 p4, F031 p3); its revision is the page revision only when labelled and equal to that submittal's current revision; D-002: a consultant's own comment sheet (F006 p2) is outside (g2)",
                "(h) / D-003: a compilation file is one pool document with page-level truth keyed by (pool id, page); a file carries a field when at least one in-scope page has it present and resolved; D-003: a labelled value in the running header of a page's own document belongs to that page's document (F043 p2-p4 'Rev. 0'; F043 revision yes/yes)",
                "(d2): an authority's approval stamp or letter without document-specific comments is class 'approved'; marks that are not review decisions (an authority's authentication of its own licence, company seals and similar) assert no decision",
                "(f): EMAAR drawing-register status letters are recorded present with actor inferred and association uncertain; they never count toward carries_fact and never carry the document decision",
                "D-005: the page-specific reading of sections 2 and 4 on F019-p1 (revision ambiguous, candidates 00 / 01, excluded from scoring) is an interpretation, not a general topic (i) rule"],
            "review35_item10": [
                "the unlabelled '- R0n' suffix base form is accepted (8 rows)",
                "the (d1) tolerance, including the application's 'rejected' (7 scorable rows)",
                "the application's 'rejected' means revise-and-resubmit (disclosure H2: the harness applies this to any text containing 'rejected')",
                "the cross-page identity rule keeps evaluator .10 parity (a wrong value equal to another page's identity of the same document is missed, never a critical) and is disclosed; its scope is every non-compilation document, 11 of the 24 run-set documents (F006, F009, F016, F020, F021, F030, F032, F037, F038, F039, F040); the owner decides on that scope between this parity and page keying (R34-06 / R36-09); .10 additionally credits the other page (R6)",
                "F069 p2 and p4 are NOT_SCORABLE (R34-11); F069 is not in the run set",
                "candidate-level gates: the candidate outcome is the comparison outcome; per-field outcomes are diagnostics (RC-2)",
                "B is attempted when its registered row exists",
                "the layout key comes from ADAPTER-CONTRACT section 5 (the reviewed labels' own kind / page_role text; file and folder names are never used)",
                "failures count once per (document, field) (RC-6)",
                "UNDETERMINED (net gain 0 or below) adds no reason and does not block by itself; the field's other gates still apply",
                "the comparison state (INCOMPLETE, INVALID) applies to every field before the field gates (R35-14)"],
            "verification36_section6": [
                "whitespace-insensitive comparison (i2); for revisions it holds after the H1 correction, except whitespace inside the prefix word (R37-04; revision_comparison_rule)",
                "dash-glyph folding for non-Arabic literals (a harness choice with no convention source; .10 differs, R1)",
                "identity is case-insensitive",
                "Arabic literals are compared byte for byte after whitespace removal; Arabic-Indic digits are not mapped",
                "a revision is compared by value with an optional R / REV / REV. / REVISION prefix (.10 differs, R2 / R2b)",
                "the (g)(1) either form is accepted",
                "the unlabelled '- R0n' suffix base form is accepted (8 rows)",
                "a decision is compared by class",
                "the application's 'rejected' means revise-and-resubmit (H2: any text containing 'rejected')",
                "the (d1) tolerance including the application's 'rejected' (7 scorable rows; .10 has no such tolerance, R4)",
                "negative words (UR, n/a, ...) assert no decision",
                "the cross-page identity rule with its actual scope (11 run-set documents; see review35_item10)",
                "compilations are keyed by (pool id, page) in the value branch (F035 and F043 in the run set); the H4 gap in the ABSENT branch is disclosed (F002 p3 only, not in the run set)",
                "NOT_SCORABLE rows (32 rows, including F069 p2 and p4) are excluded; an acceptance contradicting every literal is reported as critical_on_unresolved_truth and is never a stop",
                "one failure per (document, field)"],
            "cross_page_rule_scope": {"documents": ["F006", "F009", "F016", "F020", "F021", "F030", "F032", "F037", "F038", "F039", "F040"], "of_run_set": 24},
            "not_scorable": "F069 p2 and p4 (and every NOT_SCORABLE row) never enter y",
            "one_failure_per_document_field": True,
            "undetermined_non_blocking": "UNDETERMINED at net gain 0 or below does not block by itself"},
        "disclosures": [
            "matched margin: the projected matched populations are identity 23, revision 16, decision 16 against the minimum of 12 (margins 11 / 4 / 4); a document that B or C does not attempt or cannot read, an allowance or day-limit refusal, or a silent application limit can take revision or decision below 12, and the field then fails the matched-population gate (R33-10, R34-09); Review 33's own approximation put P(matched < 12) at 1.7 / 20 / 55 % for 10 / 20 / 30 % per-document loss",
            "the first processing of the real cohort PDFs by the application happens in live B; no dry run processed a cohort document with an application reader (R34-18)",
            "every metric carries the statement 'reference set independently AI-reviewed (Claude agents), not human-signed' (AI-ACCURACY-POLICY-AMENDMENT-R32-01)",
            "concentration rule v2: a net gain of 1 in a field is never ELIGIBLE; a net gain of 2 is ELIGIBLE only when the two documents differ in project (= contractor) and layout key; a gain confined to one project or one layout key (for decision: the EMAAR template, 6 of 16 decision documents) is never ELIGIBLE; losses elsewhere can make a spread gain concentrated; within-group churn (+3 -2) is flagged by neither leg; net 0 fields do not block; the contractor leg equals the project leg in this cohort and the cross-project issuing subcontractor is not measured (R35-15, R34-07)",
            "budget stops and provider-failure stops are not undone by a resume; a project-day refusal is permanent for the run (R35-09)",
            "the application's internal AI limits act as silent stops (application_ai_limits.silent_stops; R35-16)",
            "one ledger scope serves all four lanes: lane token and elapsed thresholds are not enforced per lane (R35-10)",
            "H2: any text containing 'rejected' maps to {revise and resubmit, rejected}; 13 'Code D - Rejected' wrong-value controls are accepted on the wired path (26 on the pair), unchanged by the H1 fix",
            "H3: a code letter without its legend is unrecognised and becomes a critical (not reachable)",
            "H4: the ABSENT branch forgives another page's identity on a compilation (F002 p3 only; F002 is not in the run set)",
            "H5: a wrong value equal to another page's identity of the same document is missed, never a critical; scope 11 of 24 run-set documents",
            "earlier evaluator-scored results (the four-arm run and before) are not comparable one to one with r32 harness scores (dashes, labelled revisions, the F043 'Rev. 0' rows, (g)(1) tails, (d1) rows, compilations, cross-page credit, the decision vocabulary)",
            "'application reachable' in the evaluator analysis was read from the code, not from application output",
            "consent-record qualification (A-02, R33-15): the owner's recorded answer is 'I authorize this' to a dialog option worded by the assistant (stated in the A-02 register entry, not in the consent record itself); 'and preparation' is the scope the label review rests on; A-03's owner message is not reproduced verbatim; the record's 'does NOT cover any provider or model request' carries no 'through the application or harness' qualifier although Claude agents read the staged images; this declaration records no owner confirmation of these points (R33-15's optional owner action)",
            "the selection universe was 3,046 against 2,455 in the feasibility basis; the difference leaves the accepted feasibility basis unchanged (R33-25)",
            "extension capacity was 34 of 36 (extension 1) and 22 of 36 (extension 2); no extension was drawn; an alternate for capacity would need a new owner decision (A-02 open point, R33-19)",
            "the label review is a same-model-family AI review under amendment R32-01: drafting (Claude Opus 5.5) and review (separate Claude agents) are AI, not human sign-off, and of the same family as the evaluated extraction models; the 98-item image re-check (0 rows refuted) was a same-model sample re-read (R33-02, R33-26)",
            "R33-12: the PACKAGE-CHECK files of the cohort packet and review31 are not bound by their manifests (disclosed, not re-bound)",
            "R33-13: the 149 words.json files of the packet are unbound",
            "R33-16: 930 of 959 databases were read in the earlier census",
            "R33-17: the extension order uses the pool seed, not the declared extension seeds (no extension was drawn)",
            "R33-18: the duplicate rule leaves 68 distinct documents in the pool",
            "R33-20: parallel writers (the seven batch label reviewers; Review 33's D1-D4) relied on the orchestrator's reading of A-03",
            "R33-21: A-03's list of documents naming Codex is incomplete (M2-REVIEW-RESPONSE.md lines 1070 and 1098)",
            "R33-22: the r26.2 labels were opened after their freeze (earlier package; disclosed)",
            "R33-14: the packet verifier ran the validator from the drafter's folder",
            "R33-15: see the consent-record qualification above",
            "the dry exercise of this declaration ran the bound code relocated to C:/t/r2x/r37-sandbox (a test twin, not bound) with reader 'none': it exercises the chain and the scorer and is not a result"],
        "thresholds_verbatim": thresholds_verbatim(h),
        "gates": {
            "per_field": {"accepted_precision_min": 0.98, "clean_recovery_min": 0.90, "matched_min": 12},
            "safety": "zero critical acceptance on resolved truth in C (a resolved-truth critical stops C: RESULT, NOT ELIGIBLE)",
            "request_gate": "at equal caps (B 240 = C 240): net correct facts x 8 >= extra requests (C's total including what it inherits from B, minus B's total), no new false acceptance, and the project-stratified bootstrap interval (2,000 resamples, seed m2-r30-bootstrap-2026-10-02) of the net gain per document excluding zero; no unequal-cap version exists",
            "decision_coverage": "completed reads + verified absences of C >= those of B and >= those of R; wrong absences and located_incomplete never count; NOT_SCORABLE rows never count",
            "concentration": "rule v2 (concentration-r32-2026-10-03.2): NOT ELIGIBLE when more than half of a positive net gain comes from one project, contractor or layout key (any size); or failures >= 2 (once per document) with more than half in one group whose net gain is negative; or any C false acceptance on a negative decision control; decision type and stratum report-only",
            "candidate_outcome": "ELIGIBLE FOR A SEPARATE SELECTION DECISION only when all three fields are ELIGIBLE; otherwise the first of INVALID > NOT ELIGIBLE > INCOMPLETE among the field outcomes; a comparison state other than INVALID / INCOMPLETE (PREPARATION BLOCKED, NOT DISPATCHABLE) is the outcome",
            "outcomes": ["ELIGIBLE FOR A SEPARATE SELECTION DECISION", "NOT ELIGIBLE", "INCOMPLETE", "INVALID", "PREPARATION BLOCKED"],
            "default_selection": "never by this run (default_selected is always None)"},
        "primary_outcomes": {
            "predeclared": ["association: false or cross-page association counts per lane, C vs B and C vs R (score_bcr_r32.primary_outcomes 'association'; judged by the harness, .10 emission only)",
                            "revision lost or gained under PA, C vs R on identical captured responses (revision_under_PA_C_vs_R)",
                            "decision outcomes under DR: completed reads, verified absences, wrong absences, accepted decisions (correct / wrong), held conflicts, C vs B and C vs R",
                            "critical acceptances on resolved and on unresolved truth, for each lane and field",
                            "new requests and tokens (actual and estimated) per lane"],
            "source": "plan v2 section 6 and DRAFT-DECLARATION.v2 primary_outcomes, restated for the harness judge (evaluator .10 is bound for emission only)"},
        "what_this_run_can_show": "every gate met: evidence toward closing M2, still subject to independent review and a separate owner selection decision",
        "forbidden_after_authorization": ["selecting a default variant", "M2 acceptance by this run", "starting M3", "production use or production database writes",
                                           "any OneDrive change", "opening a sealed project", "any project outside the six", "any use outside this declaration",
                                           "raising, resetting or re-creating a cap, the allowance or the ledger limits", "human sign-off claims for AI-reviewed labels"],
        "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed",
    }


def main(mode: str) -> int:
    C.check_frozen()
    h = hashes()
    est = E.estimate(E.load_run_set(), E.ledger_averages())
    led = C.ledger_state()
    if {k: led[k] for k in C.LEDGER_EXPECTED} != C.LEDGER_EXPECTED or SCOPE in led["scope_names"]:
        raise C.PacketMismatch(f"PACKET MISMATCH: AI ledger {led} (expected 483/17/0 and no scope {SCOPE!r})")
    if (C.LIVE_SANDBOX_BASE / STAMP).exists():
        raise C.PacketMismatch(f"refused: the run folder {(C.LIVE_SANDBOX_BASE / STAMP).as_posix()} already exists")
    declared_at = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    decl = build(est, h, declared_at)
    text = C.json_text(decl)
    if text.count(json.dumps(C.TOKEN_PLACEHOLDER)) != 1:
        raise RuntimeError("the placeholder must occur exactly once (as authorization.owner_token_sha256)")
    if mode == "show":
        sys.stdout.flush()
        sys.stdout.buffer.write(text.encode("utf-8"))
        return 0
    target = C.PACKAGE / C.DECLARATION_NAME
    shafile = C.PACKAGE / "DECLARATION.sha256"
    if target.exists() or shafile.exists():
        raise SystemExit("refused: the declaration is written once; it exists")
    sha = C.write_once(target, text)
    C.write_once(shafile, f"{sha}  {C.DECLARATION_NAME}\n")
    print(json.dumps({"declaration": target.as_posix(), "sha256": sha, "bytes": len(text.encode('utf-8')), "declared_at_utc": declared_at}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "show"))
