"""ORCH-07 (R37DECL-IMPL): the ONE response-ledger append, at the very end of docs/milestones/M2/M2-REVIEW-RESPONSE.md.

Refuses unless the file still hashes to b055b6a6...72e8 (the task-time hash) and the package manifest exists; after the
append it checks that the old bytes are an exact prefix and that exactly one entry was added. Usage: append_response_r37.py"""
from __future__ import annotations

import json
import sys

import r37common as C

HEADING = "# Fresh-validation declaration R32 and budget decision card v3 (ORCH-07, 2026-10-03): frozen, NOT authorized, NO dispatch"


def entry() -> str:
    man_path = C.PACKAGE / "evidence/EVIDENCE-MANIFEST.json"
    man_sha = C.sha256_file(man_path)
    man = json.loads(man_path.read_text(encoding="utf-8"))
    chk_sha = C.sha256_file(C.PACKAGE / "evidence/PACKAGE-CHECK.json")
    chk = json.loads((C.PACKAGE / "evidence/PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    decl_sha = C.sha256_file(C.PACKAGE / C.DECLARATION_NAME)
    assert decl_sha == man["declaration_sha256"] == (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]
    assert chk["ok"] is True
    tests = chk["checks"]["tests_packaged"]
    lines = [
        "",
        HEADING,
        "",
        "**Task:** ORCH-07 (orchestrator ledger ORCH-016), agent label R37DECL-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). "
        "Authorities A-03, A-06 and A-08. The only write-capable agent. It produces the frozen declaration the owner can authorize by hash, the budget "
        "decision card v3 and a dry preflight. It authorizes nothing and does not self-approve; ORCH-07V (independent verification) is next.",
        "",
        "**Package:** `docs/milestones/M2/real-project-pilot/declaration-r32/`.",
        f"- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `{man_sha}`, written last, {man['file_count']} files.",
        f"- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `{chk_sha}`, ok: frozen inputs re-hashed (PACKET OK); the declaration hash equals "
        "`DECLARATION.sha256`; no authorization file; no token; AI ledger 483/17/0 read-only; no frozen file modified after 2026-10-03T16:55:00Z "
        f"(and none after the task start); frozen trees equal before and after; candidate and baseline clean; tests {tests['tests']} passed, "
        f"{tests['failures']} failures, {tests['errors']} errors (re-run equal).",
        f"- **Declaration:** `FRESH-VALIDATION-DECLARATION-R32.json`, sha256 **`{decl_sha}`**, written once; `executed: false`, `budget_approved: false`, "
        "authorization \"none; owner decision pending\"; `authorization.owner_token_sha256` is the explicit placeholder `TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION`, "
        "which the preflight refuses until the owner names the token digest; the runnable declaration is this file with only that value replaced.",
        "",
        "**A-08 items in brief:**",
        "- **Arms:** B = baseline `3d5607d`, `AI_EVIDENCE_VARIANT=off`; C = candidate `a8aaced`, L3 set (EV1, GUARD, SUPPORT v2, SCHEDULING required_first, "
        "DEADLINE, TARGETED) + IG/CA/DR/PA (IDGUARD, ADJUDICATE, DECISION_REGION, ASSOC); R = candidate, L3 set, served C's capture, reference-only requests; "
        "P = `{}`, seeded 15 % probe of C's answered dispatches. Dispatch order: B, the C-from-B state check, C, R, P, offline scoring.",
        "- **Run set:** `9058f3d6…7ce8`, 24 documents (16 decision-bearing, 4 revision top-ups, 4 negative controls); matched projection identity 23 / "
        "revision 16 / decision 16 (minimum 12); decision controls 16 positive / 8 negative; unsupported controls short by 2 (plan v2 section 2.3 deviation, no substitute).",
        "- **Caps:** B 240 = C 240, R 40, P 36 (556). **Token thresholds:** 90,000 / 20,000 per request (estimates, breakers); lanes B 7.0M/1.4M = C, R 1.2M/0.24M, "
        "P 1.1M/0.22M, enforced only as one scope's totals 16.3M / 3.26M (R35-10). **Elapsed:** B 72 h, C 72 h, R and P 24 h; enforced only as the scope's "
        "604,800 s from its creation.",
        "- **Estimated usage:** planning B 6, C 112, R 10, P 17 = 145 requests (conservative 277); about 1.71M input / 0.26M output tokens; EP-27331 "
        "(6 documents, 23 pages) B + C 52 planning / 54 maximum, all lanes 63 planning against the project-day limit **60** (R and P may be refused for "
        "EP-27331; refusals are permanent for the run, R35-09).",
        "- **Cost:** unknown, never zero (claude-code on the owner's subscription; no price configured). **Owner-confirmable:** `AI_MODEL_SMALL` `sonnet`, "
        "`AI_MODEL_STANDARD` `opus` (the four-arm aliases; the AI ledger recorded claude-sonnet-5 457 and claude-opus-5 5), `AI_EFFORT` `low` (not sent by "
        "the CLI adapter), project-day limit 60, scope `m2-fresh-validation-r32-2026-10-03`; tree defaults are claude-fable-5-1 / claude-fable-5-1 / low.",
        "- **Stop rules:** verbatim from STOP-AND-SAFETY-RULES and the review34 resume rules (resolved-truth critical in B -> INVALID, in C -> RESULT, in R/P "
        "a finding; three provider failures; budget stops never raised; resume never undoes a budget or provider-failure stop and is refused after a terminal comparison).",
        "- **Concentration on the proposal:** ELIGIBLE reachable in every field (smallest net gain 2); a net gain of 1, or any gain confined to one project "
        "or layout (EP-27331 / EMAAR: 6 of 16 decision documents), is never ELIGIBLE; frozen code equals the oracle on 1,084 gain sets (0 mismatches).",
        "",
        "**Preflight (dry, `dry-run/`):** `validate_declaration` on the file as written REFUSED (\"the declaration binds no owner token digest\", by design); "
        "on an in-memory copy with a syntactically valid dummy digest (never written) PASSED; `verify_binding` on `BINDING-MANIFEST-R36` PASSED (155 files); "
        "`runner_r32 run --mode live` from the bound copy without authorization and without a token REFUSED before creating any folder; in-process with the "
        "dummy-digest copy it REFUSED at the ledger-scope check (no scope exists); the guard refused (no authorization file). Dry exercise from a test twin "
        "(sandbox base C:/t/r2x/r37-sandbox) with the declaration's switches and the refusing stub: every lane verified its switches equal the declaration, "
        "0 model requests, reader 'none'.",
        "",
        "**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; no prediction; no ledger scope; no token generated; no "
        "`OWNER-DISPATCH-AUTHORIZATION.json` or similar file created; the AI ledger was opened read-only only and reads 483 entries / 17 scopes / 0 "
        "amendments before and after; no OneDrive; no sealed project. Disclosure: one local `claude --version` (no -p, no model request).",
        "",
        "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.",
        "",
        "**Status, stated separately:**",
        "1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.",
        "2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.",
        "3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.",
        "4. **Field populations:** identity 57, revision 38, decision 38.",
        "5. **Conditions:** C-7 answered by this declaration, **pending ORCH-07V**; C-8 carried into the declaration's disclosures; R37-04 stated as the exact revision rule (exposure 0, residual risk named).",
        f"6. **Live-run authorization and budget:** none. Declaration `{decl_sha[:8]}…` is frozen and NOT authorized; no authorization file, no token, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.",
        "7. **M2:** **CHANGES STILL REQUIRED.**",
        "8. **M3:** not started.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    before = C.RESPONSE_LEDGER.read_bytes()
    if C.sha256_bytes(before) != C.RESPONSE_BEFORE_SHA256:
        raise SystemExit(f"refused: the response ledger hashes to {C.sha256_bytes(before)}, not {C.RESPONSE_BEFORE_SHA256}")
    if HEADING.encode("utf-8") in before:
        raise SystemExit("refused: the entry exists")
    text = entry().encode("utf-8")
    with open(C.RESPONSE_LEDGER, "ab") as fh:
        fh.write(text)
    after = C.RESPONSE_LEDGER.read_bytes()
    assert after[:len(before)] == before and after[len(before):] == text and after.count(HEADING.encode("utf-8")) == 1
    print(json.dumps({"before_sha256": C.sha256_bytes(before), "before_bytes": len(before), "appended_bytes": len(text),
                      "after_sha256": C.sha256_bytes(after), "after_bytes": len(after)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
