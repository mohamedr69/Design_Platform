"""ORCH-05.1: append ONE entry at the very end of docs/milestones/M2/M2-REVIEW-RESPONSE.md (append-only).
Refuses unless the file still hashes to its pre-append value and the package's evidence manifest exists. Usage: append_response_r33.py"""
import hashlib
import json
import pathlib
import sys

R33 = pathlib.Path("C:/t/iso/work/r2x/r33")
sys.path.insert(0, str(R33 / "harness-r32"))
import inputs_r32 as I  # noqa: E402

RESPONSE = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
BEFORE = "da5cc7981f6e65e05e843ee5a3b8e3520b2daa957acb8b1e7981e17abf7997f7"
PKG = I.PILOT / "review33"


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    old = RESPONSE.read_bytes()
    if sha_bytes(old) != BEFORE:
        raise SystemExit(f"refused: the response ledger is {sha_bytes(old)}, not {BEFORE}")
    mpath = PKG / "evidence" / "EVIDENCE-MANIFEST.json"
    man = json.loads(mpath.read_text(encoding="utf-8"))
    msha = sha_bytes(mpath.read_bytes())
    check = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    dry = json.loads((PKG / "dry-run" / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))
    rec = json.loads((PKG / "CONVERTER-RECONCILIATION.json").read_text(encoding="utf-8"))["totals"]
    prop = json.loads((PKG / "RUN-SET-PROPOSAL.json").read_text(encoding="utf-8"))
    junit = check["checks"]["junit_packaged"]
    tests = {k[:-4]: v["tests"] for k, v in junit["files"].items()}
    proj = {f: v["documents"] for f, v in prop["per_field_matched_projection"].items()}
    lines = [
        "",
        "# Correction package review33: r32 harness adapter, per-field scorer, C-4 concentration rule, run-set selector, guarded runner (2026-10-03)",
        "",
        "**Task:** ORCH-05.1, agent R33HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. Authorities: A-03, A-05 and A-08. It answers Review 33 conditions **C-4** (concentration rule, owner decision A-05) and **C-5** (harness adapter). It is a correction package, pending its independent review (ORCH-05R). It is not self-approved.",
        "",
        f"**Package:** `docs/milestones/M2/real-project-pilot/review33/`.",
        f"- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `{msha}`. It was written last and lists {man['file_count']} files.",
        f"- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `{man['package_check_sha256']}`, ok. The check re-hashed every input and manifest, re-ran {junit['tests']} tests (0 failures), counted the AI ledger read-only at 483/17, found no frozen file modified after 2026-10-03T10:30:00Z, found no `OWNER-DISPATCH-AUTHORIZATION.json`, and confirmed that the guard refuses.",
        f"- **Binding manifest:** `BINDING-MANIFEST-R33.json`, sha256 `{man['binding_manifest_sha256']}`. It binds 68 files: the frozen inputs, the policy `7efa891b…4f47` and its amendment `815d43fd…5de6`, the reviewed-2, packet and review31 manifests, review31's harness as `harness-base`, every `harness-r32` source and test, and the run-set proposal. It also records candidate `a8aacedd` and baseline `3d5607d9`, both clean.",
        "",
        "**What was built** (`scripts/harness-r32/`; junit in `tests/`):",
        f"- `labels_adapter_r32` ({tests.get('test_labels_adapter_r32')} tests): per (pool id, page, field) truth, with per-field `resolved_for_scoring` and a NOT_SCORABLE sentinel distinct from None and ABSENT. 32 rows on 32 pages in 25 documents are not scorable. Aliases are canonical. Compilations are keyed by page. It adds project, contractor, stratum, a deterministic layout key and decision type. It reproduces FIELD-POPULATION 57/38/38 with the same ids. Truth `{man['truth_r32_sha256']}`.",
        f"- `literal_compare_r32` ({tests.get('test_literal_compare_r32')} tests): whitespace-insensitive; folds dash variants; accepts either-form labelled tails ((g)(1)); compares decisions by class with the application vocabulary and the (d1) tolerance; byte-compares Arabic literals.",
        f"- `lane_judge_r32` ({tests.get('test_lane_judge_r32')}), `score_bcr_r32` ({tests.get('test_score_bcr_r32')}): the Review 31 rules per field (equal caps 240/240, request gate, 0.98 precision, 0.90 recovery, outcomes, no default), with NOT_SCORABLE excluded and a per-field critical tripwire. Review 31's `score_bcr.py` is untouched, and `SCORER-CHANGES.md` lists 17 differences.",
        f"- `concentration_r32` ({tests.get('test_concentration_r32')} tests) and `CONCENTRATION-RULE-R32.md`, the C-4 replacement:",
        "  - **NOT ELIGIBLE** when: net gain ≥ 4 and more than half of it comes from one project, contractor or layout key; or failures ≥ 2 with more than half in one such group whose own net gain is negative; or decision has any false acceptance on a negative decision control.",
        "  - **UNDETERMINED** (not blocking) below a net gain of 4.",
        "  - Decision type and stratum are reported only.",
        f"- `run_set_selector_r32` ({tests.get('test_run_set_selector_r32')} tests) and `RUN-SET-PROPOSAL.json` (`{man['run_set_proposal_sha256']}`): a proposal, frozen only by ORCH-07.",
        f"  - It holds {prop['count']} documents: {prop['by_reason'].get('decision_bearing')} decision-bearing, {prop['by_reason'].get('top_up')} revision top-ups and {prop['by_reason'].get('negative_control')} negative controls.",
        "  - **The unsupported controls are short by 2**: no pool page is labelled unsupported or illegible, and nothing was invented.",
        f"  - Projection: identity {proj['identity']}, revision {proj['revision']}, decision {proj['decision']} (margin 4 for revision and decision).",
        f"- `converter_r32` ({tests.get('test_converter_r32')} tests) and `LABELS-R32-EVAL-INPUT.json`, in evaluator .10 format. Reconciliation: {rec['truth_rows']} truth rows = {rec['mapped']} mapped + {rec['excluded']} explicit exclusions (the aliases F031 and F059), each exactly once. The frozen evaluator's truth functions read every converted row as its r32 kind.",
        f"- `sandbox_ingest_r32` ({tests.get('test_sandbox_ingest_r32')} tests): the 72 staged files were registered PENDING in an isolated sandbox under `C:/t/r2x/r33-sandbox/`, by the baseline tree, without processing. `state_check` is ok.",
        f"- `runner_r32` and `lane_r32` ({tests.get('test_runner_r32')} tests), `dispatch_guard_r32` ({tests.get('test_dispatch_guard_r32')}), `allowance_r32` ({tests.get('test_allowance_r32')}), `tripwire_r32` ({tests.get('test_tripwire_r32')}), plus the unchanged copies of `capture_store` ({tests.get('test_capture_store')}), `stop_rules` ({tests.get('test_stop_rules')}) and `state_check` ({tests.get('test_state_check')}).",
        "  - The provider path is reachable only through `dispatch_guard_r32.authorize()`. It refuses unless `OWNER-DISPATCH-AUTHORIZATION.json` exists and names the ORCH-07 declaration hash and an owner budget token. This task did not create that file.",
        "  - Resume contract: a reserved request without an answer is charged and never re-sent.",
        "",
        f"**Dry run** (`DRY-RUN-REPORT.md`, `dry-run/`):",
        f"- **Provider or model calls:** 0. No provider was built.",
        f"- **AI ledger:** {dry['ledger_before']['entries']}/{dry['ledger_before']['scopes']} before and {dry['ledger_after']['entries']}/{dry['ledger_after']['scopes']} after. No ledger scope was created.",
        "- **No prediction.** No application reader ran on any cohort document (reader `none`).",
        "- **What ran:**",
        "  - the binding was verified;",
        "  - the guard refused;",
        "  - the run set was ingested and the C/R-from-B state checks passed;",
        "  - capture-store lanes B/C/R/P exchanged synthetic probes with a refusing stub, and R was served C's capture;",
        "  - the resume drill passed with 0 re-sends.",
        "- **The scorer and the concentration rule** were exercised on synthetic results built from the truth, not predictions. ELIGIBLE is reachable for all three fields under the new rule.",
        "",
        "**Out of scope (not done here):** evaluator .10 changes and its offline test (ORCH-06), the declaration (ORCH-07), and any dispatch.",
        "",
        "**Reference set:** independently AI-reviewed (Claude agents), not human-signed. It is used under AI-ACCURACY-POLICY-AMENDMENT-R32-01, and it is not human Golden Truth.",
        "",
        "**Status, stated separately:**",
        "1. **Source permission and verification:** unchanged. A-02 covers access, staging, drafting and preparation. A-06 grants project and provider **eligibility** for the six projects, but not dispatch. Verification stands at 10 of 10, with no replacement.",
        "2. **Label drafting:** `r32-labels-draft-1` is frozen and unchanged. It is AI-drafted and not human-signed.",
        "3. **Independent label review and reference-set status:** the owner-delegated independent Claude AI review, with the Review 33 rulings applied as `r32-labels-reviewed-2` (`89c60e9d…b9a6`). Under amendment R32-01 it is an AI-reviewed reference set: not human-signed, not human Golden Truth.",
        "4. **Field populations:** identity 57, revision 38, decision 38 (reproduced by the adapter), with 0 extensions.",
        "5. **Preparation gate and Review 33 conditions:**",
        "   - The pool gate is met.",
        "   - **C-4 and C-5 are answered by this package, pending the independent review (ORCH-05R).**",
        "   - C-6 is ORCH-06, and C-7 is ORCH-07.",
        "6. **Live-run authorization and budget:** none. No owner dispatch authorization exists. No budget, ledger scope or dispatch. The ledger is untouched at 483/17.",
        "7. **M2:** **CHANGES STILL REQUIRED.**",
        "8. **M3:** not started.",
    ]
    entry = "\n".join(lines) + "\n"
    assert "\r" not in entry
    with open(RESPONSE, "ab") as fh:
        fh.write(entry.encode("utf-8"))
    new = RESPONSE.read_bytes()
    assert new[:len(old)] == old and sha_bytes(new[:len(old)]) == BEFORE, "append-only violated"
    print(json.dumps({"before": BEFORE, "after": sha_bytes(new), "appended_bytes": len(new) - len(old), "offset": len(old)}))


if __name__ == "__main__":
    main()
