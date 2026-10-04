"""ORCH-05C: append ONE entry at the very end of docs/milestones/M2/M2-REVIEW-RESPONSE.md (append-only).
Refuses unless the file still hashes to its pre-append value and the package's evidence manifest exists and the package
check is ok. Usage: append_response_r34.py"""
import hashlib
import json
import pathlib
import sys

R34 = pathlib.Path("C:/t/iso/work/r2x/r34")
sys.path.insert(0, str(R34 / "harness-r32"))
import inputs_r32 as I  # noqa: E402

RESPONSE = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/M2-REVIEW-RESPONSE.md")
BEFORE = "500d55f559f157a8ebbe695157d6c6cd3b83dac5c31e58820f871a4615d690ac"
PKG = I.PILOT / "review34"
HEADING = ("# Correction package review34: concentration rule v2, candidate outcome, pinned one-run dispatch guard, per-declaration "
           "allowance and resume (2026-10-03)")


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
    if not check["ok"] or man["package_check_sha256"] != sha_bytes((PKG / "evidence" / "PACKAGE-CHECK.json").read_bytes()):
        raise SystemExit("refused: the package check is not ok or not the one the manifest lists")
    dry = json.loads((PKG / "dry-run" / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))
    junit = check["checks"]["junit_packaged"]
    tests = {k[:-4]: v["tests"] for k, v in junit["files"].items()}
    drill = dry["drill"]
    lines = [
        "",
        HEADING,
        "",
        "**Task:** ORCH-05C, agent label R34HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities: A-03, A-05 and A-08. It answers Independent Review 34 (`75061210…bc8f47`, findings `af99a772…f9fd8`, verdict CHANGES REQUIRED): required corrections **RC-1 to RC-6** (R34-01, R34-02, R34-03, R34-04, R34-05, R34-08). It is a correction package pending Independent Review 35 (ORCH-05R2). It is not self-approved.",
        "",
        "**Package:** `docs/milestones/M2/real-project-pilot/review34/`.",
        f"- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `{msha}`. It was written last and lists {man['file_count']} files.",
        f"- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `{man['package_check_sha256']}`, ok. It re-hashed every input and manifest, re-ran {junit['tests']} tests in {len(junit['files'])} modules (0 failures), counted the AI ledger read-only at 483/17/0, found no frozen file modified after 2026-10-03T12:10:00Z, found no authorization file anywhere, and confirmed the guard's refusals.",
        f"- **Binding manifest:** `BINDING-MANIFEST-R34.json`, sha256 `{man['binding_manifest_sha256']}` ({check['checks']['binding']['files']} files). It supersedes review33's `d1a8a401…936e` and binds the frozen inputs, Review 34, the review33 manifest and binding, review31's harness, the review33 harness base, every review34 harness source and test, the carried files and the run set; it records the unchanged, changed and new module tables and candidate `a8aacedd` / baseline `3d5607d9`, both clean.",
        "",
        "**Corrections** (`scripts/harness-r32/`; junit in `tests/`; details in `CORRECTION-REPORT.md` §2):",
        f"- **RC-1 (R34-01, blocker):** `concentration_r32` version 2, `concentration-r32-2026-10-03.2` (`CONCENTRATION-RULE-R32.md` v2 with a change record): a positive net gain is never ELIGIBLE while more than half of it comes from one project, contractor or layout key, at any size (no net-gain floor); the negative-control and failure legs are kept; UNDETERMINED only for a net gain of 0 or less and never overriding NOT ELIGIBLE; the justification now rests on the scorer's project-stratified bootstrap (which excludes zero for a gain concentrated in one project at net 2 and 3). Tests: Review 34's S3a, S3b (decision +3 on F037, F009, F032 of EP-27331: now NOT ELIGIBLE), S3c (stays NOT ELIGIBLE), a spread control (ELIGIBLE), and monotonicity (`test_concentration_r32` {tests.get('test_concentration_r32')} tests).",
        f"- **RC-2 (R34-02):** `score_bcr_r32` gives one candidate-level outcome: ELIGIBLE FOR A SEPARATE SELECTION DECISION only when all three fields are ELIGIBLE, otherwise INVALID > NOT ELIGIBLE > INCOMPLETE over the field outcomes; fields stay as diagnostics; no default. S5 (decision recovery 0.7576) gives NOT ELIGIBLE (`test_score_bcr_r32` {tests.get('test_score_bcr_r32')} tests).",
        f"- **RC-3 (R34-03):** the authorization path is pinned beside the declaration (no `--auth-path`, a configured `auth_path` is refused); the authorization must carry the declaration hash, the owner token digest the declaration binds (the token is presented at run time and never stored) and a one-run nonce consumed into a run-bound record holding the authorization's own hash; a direct live `lane_r32.py` runs the same preflight and guard. Tests prove: wrong path, missing declaration hash, wrong digest and consumed nonce refused; a direct lane refused without authorization (`test_dispatch_guard_r32` {tests.get('test_dispatch_guard_r32')}, `test_runner_r32` {tests.get('test_runner_r32')}). **No authorization file was created.**",
        f"- **RC-4 (R34-04):** one allowance (caps 240/240/40/36 and the project-day counter, 60 per project per UTC day across all lanes) and one capture store per declaration, bound to its hash, in one run folder; `runner_r32 run` once, then `runner_r32 resume` (same stamp, never re-sends a bound fingerprint, serves a reserved request as `interrupted_charged`, never fresh caps); the ledger-unchanged assertion is dry-only; live, `LedgerProvider` writes to the declared scope and the runner and lanes verify that scope and its limits before dispatch (no scope created) (`test_allowance_r32` {tests.get('test_allowance_r32')}, `test_preflight_r32` {tests.get('test_preflight_r32')}).",
        "- **RC-5 (R34-05):** live lanes verify their switches and provider environment (provider, model aliases, effort, timeouts, CLI path, ledger wrapping) against the declaration, in the environment and the application's settings; no silent defaults in live mode; dry defaults labelled.",
        "- **RC-6 (R34-08):** a wrong acceptance is exactly one failure (failures once per document and field).",
        "- **Carried unchanged by hash:** the adapter, literal comparison, converter, selector, sandbox ingestion and the review31 copies (capture store, state check, stop rules); `TRUTH-R32` `4e237a4e…e064`, `RUN-SET-PROPOSAL` `9058f3d6…7ce8`, `LABELS-R32-EVAL-INPUT` `4b2c73d5…5cc`, `CONVERTER-RECONCILIATION` `e350d2fe…24f3`.",
        "",
        "**Dry run** (`DRY-RUN-REPORT.md`, `dry-run/`):",
        f"- **Provider or model calls:** 0. **AI ledger:** {dry['ledger_before']['entries']}/{dry['ledger_before']['scopes']} before and {dry['ledger_after']['entries']}/{dry['ledger_after']['scopes']} after; no scope created. No prediction (reader `none`).",
        f"- **Two-invocation drill:** a fresh run interrupted by a crash right after a send; a second fresh run refused; a same-stamp resume that re-sent nothing, served the reserved request once as `interrupted_charged`, kept the caps and completed; then resume and run refused ({sum(1 for v in drill['checks'].values() if v)} of {len(drill['checks'])} checks true).",
        "- **Scorer scenarios** (synthetic lanes made from the truth, not results): S3b and S5 give the candidate NOT ELIGIBLE; the spread control gives ELIGIBLE; EP-27331 decision gains of 1 to 6 documents are all NOT ELIGIBLE.",
        "",
        "**Out of scope (not done here):** evaluator .10 changes and its offline test (ORCH-06, ORCH-06V), the declaration and budget (ORCH-07), any owner authorization, ledger scope or dispatch.",
        "",
        "**Reference set:** independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.",
        "",
        "**Status, stated separately:**",
        "1. **Source permission and verification:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider **eligibility** for the six projects, not dispatch. Verification stands at 10 of 10, with no replacement.",
        "2. **Label drafting:** `r32-labels-draft-1` is frozen and unchanged; AI-drafted and not human-signed.",
        "3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) under amendment R32-01: independently AI-reviewed, not human-signed.",
        "4. **Field populations:** identity 57, revision 38, decision 38; 0 extensions.",
        "5. **Review 33 / Review 34 conditions:** C-4 and C-5 are answered again here and RC-1 to RC-6 are implemented and tested, all pending Review 35; C-6 is ORCH-06, C-7 is ORCH-07, C-8 is carried into the declaration.",
        "6. **Live-run authorization and budget:** none. No `OWNER-DISPATCH-AUTHORIZATION.json` exists anywhere; no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.",
        "7. **M2:** **CHANGES STILL REQUIRED.**",
        "8. **M3:** not started.",
    ]
    entry = "\n".join(lines) + "\n"
    assert "\r" not in entry and old.endswith(b"\n")
    with open(RESPONSE, "ab") as fh:
        fh.write(entry.encode("utf-8"))
    new = RESPONSE.read_bytes()
    assert new[:len(old)] == old and sha_bytes(new[:len(old)]) == BEFORE, "append-only violated"
    print(json.dumps({"before": BEFORE, "after": sha_bytes(new), "appended_bytes": len(new) - len(old), "offset": len(old)}))


if __name__ == "__main__":
    main()
