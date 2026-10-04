"""ORCH-09 (R40DECL-IMPL): the ONE append to docs/milestones/M2/M2-REVIEW-RESPONSE.md for declaration-r32-v2.

Usage: append_response_r40.py
Refuses unless (1) the response ledger still hashes to caf949b2... (213,865 bytes: its state before this task), (2) the
package's evidence manifest exists, (3) PACKAGE-CHECK.json is all_ok. Appends exactly one entry (one top-level heading) at
the very end, verifies that the first 213,865 bytes still hash to caf949b2..., and records the old and new hashes in
WORK/RESPONSE-APPEND-RECORD.json. Writes only the response ledger (append) and the record."""
import hashlib
import json
import sys

sys.dont_write_bytecode = True
import r40common as C  # noqa: E402

PREFIX, PREFIX_BYTES = C.RESPONSE_BEFORE
HEADING = ("# Corrected fresh-validation declaration R32 v2, runbook and scope-creation command (ORCH-09, 2026-10-04): frozen, NOT authorized, "
           "NO dispatch")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def entry() -> str:
    man_b = (C.PACKAGE / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    man = json.loads(man_b.decode("utf-8"))
    chk = json.loads((C.PACKAGE / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    ck = chk["checks"]
    pre = json.loads((C.PACKAGE / "dry-run" / "PREFLIGHT-RESULTS.json").read_text(encoding="utf-8"))
    dry = json.loads((C.PACKAGE / "dry-run" / "DRY-EXERCISE.json").read_text(encoding="utf-8"))
    diff = json.loads((C.PACKAGE / "DECLARATION-DIFF.json").read_text(encoding="utf-8"))
    loops = {k: v["invocations"] for k, v in dry["deferral_loops"].items()}
    L = [HEADING, "",
         "- **Task:** ORCH-09 (orchestrator ledger ORCH-024), agent R40DECL-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). "
         "Authorities A-03, A-06, A-08, A-09, A-10. Work 2026-10-04 from 11:21Z.",
         f"- **Package:** `PILOT/declaration-r32-v2/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`{sha(man_b)}`** ({man['file_count']} files); "
         f"`evidence/PACKAGE-CHECK.json` `{man['package_check_sha256']}` (all checks ok).",
         f"- **Declaration:** `FRESH-VALIDATION-DECLARATION-R32-V2.json` sha256 **`{man['declaration_sha256']}`** (= `DECLARATION.sha256`), contract "
         "`r39-live-contract-4`, bound to review39 (`BINDING-MANIFEST-R39` `a6f703b4…567b`, manifest `2430fa2b…d990`). The owner-token digest is an explicit "
         "placeholder (exactly once); the preflight and the guard refuse the file as written; an in-memory copy with a dummy digest passes contract 4 "
         "(never written). It supersedes `38e08df9…76b0` (A-09: never authorized, never run).",
         f"- **Differences from the superseded declaration** (`DECLARATION-DIFF.md`): {diff['top_level_counts']['changed']} top-level keys changed, "
         f"{diff['top_level_counts']['added']} added, {diff['top_level_counts']['removed']} removed (caps, caps_detail, project_day_limit, "
         f"project_day_limit_detail: replaced by contract 4's budget and project_window), {diff['top_level_counts']['unchanged']} unchanged.",
         "- **Values:** parent budget 556 / 16,300,000 / 3,260,000 / 604,800 s; lane allowances B 240, C 240, R 40, P 36; project window 60 per 86,400 s "
         "(all lanes); `resume_policy` `full`; `application_env` `{\"DRAWINGS_AI_REVIEW_ENABLED\": \"false\"}`; task kinds per lane from the switches; "
         "models `claude-sonnet-5` / `claude-opus-5`, provider `claude-code`, CLI line `2.1.263 (Claude Code)`; compatible limits as integer strings "
         "`AI_MAX_CALLS_PER_PROJECT_PER_DAY` \"96\" (required 84, margin 12 = one document's JobBudget), `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` \"600\", "
         "`AI_MAX_CALLS_PER_DOCUMENT` \"12\", `AI_MAX_ELAPSED_S_PER_JOB` \"120\"; ledger scope `m2-fresh-validation-r32-v2-2026-10-04` (limits = the "
         "parent; does not exist); run folder `C:/t/r2x/r40-sandbox/r32-v2` (short: the longest application path is 255 characters).",
         "- **The decision coverage gate is C >= B only: a change from plan v2** (owner ruling A-10; not an unchanged gate); C >= R a mandatory diagnostic.",
         "- **Verification 40 items:** R40-04 (the claim corrected: the gate's belt and braces holds for lane B only; C/R/P rest on two static analyses and "
         "a dynamic run with get_provider() raising, 0 calls, bound by hash; residual risk stated; two owner options); R40-13 (the failed-read retry named "
         "a change from plan v2 section 4; review39 contract v4 sections 4, 5, 6, 13 carried verbatim, replacing review34's resume rules); R40-16 (the "
         "amended probe in RUNBOOK section 1; no 'exactly one request' claim); R40-08 (integer strings; the R39-18 risk and its handling); R40-10 (the "
         "no_trigger exclusion and two unguarded corners); R40-12 (P's population drawn at its first run, cap 36, seed unchanged); R40-15 "
         "(acknowledgement requested); R40-19 (review39 SNAPSHOT-BEFORE 09:55:49Z); R40-20 (review39's final AUDIT-LOG.md / PROGRESS.md copied and bound).",
         f"- **Preflight (dry):** as written REFUSED (placeholder); dummy digest PASSED; {sum(r['as_expected'] for r in pre['checks']['3_negative_probes']['rows'])}"
         f"/{pre['checks']['3_negative_probes']['count']} negative probes as expected (the harness still accepts '12.0' / '120.0', R40-08, which the "
         "integer-string check refuses); binding 239/239; bounds recomputed equal; the four lanes' live environment checks pass offline; the live runner "
         "refused with no folder (no RUN file; no scope; no authorization); the guard refused and built no provider; the scope command's preview created "
         "nothing and its create mode refused without an authorization file.",
         f"- **Dry exercise:** the bound review39 harness unchanged (declared sandbox base, no twin), reader 'none', refusing stub: main run status "
         f"{dry['main']['report'].get('status')}; EP-27331 deferral loops under 'full' finished in {loops} invocations with every early resume refused "
         "and nothing created; the CLI-version dead-end shown (a version refusal at invocation 1 leaves a folder without an allowance: neither run nor "
         f"resume can continue); model requests {dry['model_requests_total']}; AI ledger 483 / 17 / 0 before and after.",
         f"- **Tests:** {ck['tests']['tests']} tests, {ck['tests']['failures']} failures, {ck['tests']['errors']} errors, {ck['tests']['guard_refused']} "
         "write-guard refusals (`tests/test_r40.xml`).",
         "- **Environment note:** drive C: reached 0 bytes free during the first dry-exercise attempt (other processes were writing ep-platform test "
         "temp folders); that attempt is recorded in the work folder and was re-run; nothing of anyone else was touched.",
         "",
         "**Zero calls:** no provider or model request of any kind, no `claude` invocation in any form, no network; no prediction; no ledger scope, token, "
         "authorization file or RUN file; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 amendments before and after.",
         "",
         "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).",
         "",
         "**Status, stated separately:**",
         "1. **Correction readiness:** the corrected declaration, runbook and scope-creation command are delivered, **pending Verification 41**; not self-approved.",
         "2. **Accuracy:** none. No prediction exists; every figure is an estimate, a bound or a dry-run exercise.",
         "3. **Label truth:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) independently AI-reviewed (Claude agents), not human-signed; populations 57 / 38 / 38.",
         "4. **Permissions and budget:** eligibility only (A-06). No authorization file, token, budget, ledger scope or dispatch exists. Open owner "
         "decisions: served-model identity UNRESOLVED (probe or accept); R40-04 (accept the proof or order a harness change); the budget authorization.",
         "5. **M2:** **CHANGES STILL REQUIRED.**",
         "6. **M3:** not started.", ""]
    return "\n".join(L)


def main():
    old = C.RESPONSE_LEDGER.read_bytes()
    if sha(old) != PREFIX or len(old) != PREFIX_BYTES:
        raise SystemExit(f"refused: the response ledger is not in its pre-task state ({sha(old)}, {len(old)} bytes)")
    text = entry()
    sep = b"" if old.endswith(b"\n\n") else (b"\n" if old.endswith(b"\n") else b"\n\n")
    with open(C.RESPONSE_LEDGER, "ab") as fh:
        fh.write(sep + text.encode("utf-8"))
    new = C.RESPONSE_LEDGER.read_bytes()
    if sha(new[:PREFIX_BYTES]) != PREFIX:
        raise SystemExit("the prefix changed (must never happen)")
    rec = {"file": C.RESPONSE_LEDGER.as_posix(), "before_sha256": PREFIX, "before_bytes": PREFIX_BYTES, "after_sha256": sha(new), "after_bytes": len(new),
           "prefix_verified": True, "appended_bytes": len(new) - PREFIX_BYTES, "heading": HEADING}
    (C.WORK / "RESPONSE-APPEND-RECORD.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
