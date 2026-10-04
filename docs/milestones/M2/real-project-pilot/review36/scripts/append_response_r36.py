"""ORCH-06C (R36HARNESS-IMPL): append ONE entry at the very end of docs/milestones/M2/M2-REVIEW-RESPONSE.md, after verifying
its current hash. Usage: append_response_r36.py   (refuses unless the file is exactly 44b5ae38... and holds no such entry yet,
and unless the review36 evidence manifest exists and the package check is ok)"""
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review36"
RESPONSE = PILOT.parent / "M2-REVIEW-RESPONSE.md"
BEFORE = "44b5ae386cc3f993547921cf094ebe6d308b4c1aef851bc6e1cf2b0c99bc1b25"
HEADING = "# Correction package review36: H1 whitespace fix in literal_compare_r32.norm_revision (2026-10-03)"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def entry() -> str:
    man_path = PKG / "evidence" / "EVIDENCE-MANIFEST.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    chk = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    w = json.loads((PKG / "H1-WHATIF-RESULT.json").read_text(encoding="utf-8"))
    assert chk["ok"] and not chk["skip_tests"] and w["ok"]
    c = chk["checks"]
    lc, tl = c["harness"]["literal_compare_r32"], c["harness"]["test_literal_compare_r32"]
    jt, jb = c["junit_packaged"]["whole_suite_twin"], c["junit_packaged"]["bound_copy_sandbox_free_modules"]
    rl, cl = w["row_level"], w["case_level"]
    wv = cl["wrong_value_controls"]
    ns = cl["not_scorable"]
    led = c["ledger"]
    pairs = "; ".join(f"{x['before']} -> {x['after']} {x['n']}" for x in cl["class_vs_pair_changes"])
    lines = [
        "",
        HEADING,
        "",
        "**Task:** ORCH-06C, agent label R36HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities "
        "A-03 and A-08. The only write-capable agent. It answers Independent Verification 36 (`f698c2ff…3a00`), finding **R36-08** "
        "(major, CONFIRMED: H1 is a harness defect), condition 1 for ORCH-07. It is a correction package pending the independent "
        "read-only check ORCH-06CV (Verification 37). It is not self-approved.",
        "",
        "**Package:** `docs/milestones/M2/real-project-pilot/review36/`.",
        f"- **Manifest:** `evidence/EVIDENCE-MANIFEST.json`, sha256 `{sha(man_path)}`, written last, {man['file_count']} files.",
        f"- **Package check:** `evidence/PACKAGE-CHECK.json`, sha256 `{man['package_check_sha256']}`, ok: frozen inputs re-hashed (PACKET OK); "
        "only one module differs from review34; the suite re-run passes; AI ledger 483/17/0 read-only; no frozen file modified after "
        "2026-10-03T15:30:00Z and every frozen tree digest equal to the task-start snapshot; no authorization file.",
        f"- **Binding manifest:** `BINDING-MANIFEST-R36.json`, sha256 `{man['binding_manifest_sha256']}`: every harness file (work copy, "
        "package copy, review34 base), the review34 manifest and binding, the evaluator-offline-r32 manifest, binding, fixtures and "
        "matrix, Verification 36, and the review34 inputs / carried files / run set carried unchanged; it passes the runner's own "
        "`preflight_r32.verify_binding`.",
        "",
        "**The change (exactly one function):** `literal_compare_r32.py` `norm_revision` only. After the unchanged Arabic branch, dash "
        "folding, upper-casing and the optional REVISION / REV / REV. / R / R. prefix (same alternatives, same order), every whitespace "
        "character is removed before the number pattern `0*(\\d+)` is matched; the non-numeric fallback, leading-zero handling and "
        "the module docstring are unchanged; a function docstring was added. `0 1` and `REV 0 1` and `R 01` -> `R1`, `0 0` -> `R0`, "
        "`Rev. 0 2` -> `R2`.",
        f"- `literal_compare_r32.py`: review34 `{lc['review34']}` -> r36 `{lc['r36']}`.",
        f"- `test_literal_compare_r32.py`: review34 `{tl['review34']}` -> r36 `{tl['r36']}` (35 tests appended; the review34 file "
        "is an exact byte prefix). The other 38 harness files are byte-identical to review34.",
        "",
        "**Effect (H1-WHATIF-RESULT.json):**",
        f"- Row level: {rl['accepted']['rows_judged']:,} row judgements per state (Verification 36's population); exactly "
        f"**{rl['accepted']['changed']}** change on `accepted` and **{rl['validated']['changed']}** on `validated`: the 53 "
        "`ws_inside_number` truth rows, each `wrong_only` + 1 critical -> `recovered_clean` (kind `normalised`), 0 side rows.",
        f"- Parity run re-executed (harness side with the fixed harness, evaluator side re-run read-only): {cl['cases']:,} cases; exactly "
        f"**{cl['changed_cases']}** change (the 53 rows x 2 channels; {len(cl['changed_rows_in_run_set'])} rows in the run set), "
        f"critical -> correct on both the pair and the wired facts; evaluator side identical; class changes: {pairs}.",
        f"- **Wrong-value controls:** {wv['fixtures']:,} fixtures / {wv['cases']:,} cases, **0 verdicts changed, 0 newly accepted**. "
        f"(Before and after, the frozen harness accepts 13 decision controls by its H2 vocabulary, `Code D - Rejected`: "
        f"{wv['harness_pair_accepted_before']} pair cases and {wv['harness_wired_accepted_before']} wired cases; the fix touches no decision "
        "comparison.)",
        f"- **NOT_SCORABLE:** {ns['rows']} rows / {ns['cases']} cases, all excluded by the harness before and after; 0 read as absent.",
        "- Verification 36's what-if numbers are reproduced exactly (42,804 rows, 53 changed, 0 wrong controls newly accepted; 106 "
        "cases, 74 where .10 accepts and 32 where both were critical; 23 rows in the run set).",
        "",
        f"**Tests:** the whole review34 suite from the copy, {jt['modules']} modules, **{jt['tests']} tests ({jt['tests'] - 35} review34 + 35 new), "
        f"{jt['failures']} failures, {jt['errors']} errors**. Disclosure: the review34 suite hard-codes the sandbox base "
        "`C:/t/r2x/r34-sandbox`, so the whole-suite run uses a test-run twin of the bound copy that differs only by that string -> "
        "`C:/t/r2x/r36-sandbox` (15 occurrences in 8 files; verified byte for byte); the 14 sandbox-free modules also ran from the "
        f"bound copy itself ({jb['tests']} tests, {jb['failures']} failures). The new H1 tests fail on the review34 module (16 of 48) "
        "and pass on the r36 module.",
        "",
        "**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; the parity run's guard constructed no "
        "provider and blocked no attempt; no prediction exists or was created (the values are the frozen SYNTHETIC fixtures); the AI "
        f"ledger was opened read-only only and reads {led['entries']} entries / {led['scopes']} scopes / {led['limit_amendments']} "
        "amendments before and after; no ledger scope; no OneDrive; no sealed project; no authorization file created; review34, "
        "evaluator-offline-r32, the cohort packages, staging, the candidate and the baseline were not written (digests unchanged).",
        "",
        "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01); not human Golden Truth.",
        "",
        "**Status, stated separately:**",
        "1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.",
        "2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.",
        "3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.",
        "4. **Field populations:** identity 57, revision 38, decision 38.",
        "5. **Conditions:** R36-08 answered by this package, **pending ORCH-06CV**; the other ORCH-07 conditions of Verification 36 (R36-07, R36-09, the disclosures) are carried into the declaration.",
        "6. **Live-run authorization and budget:** none. No authorization file, no budget, no ledger scope, no dispatch; the ledger is untouched at 483/17.",
        "7. **M2:** **CHANGES STILL REQUIRED.**",
        "8. **M3:** not started.",
    ]
    return "\n".join(lines) + "\n"


def main():
    got = sha(RESPONSE)
    if got != BEFORE:
        raise SystemExit(f"PACKET MISMATCH: response ledger {got} != {BEFORE}")
    raw = RESPONSE.read_bytes()
    assert raw.endswith(b"\n") and HEADING.encode("utf-8") not in raw
    t = entry()
    with open(RESPONSE, "ab") as fh:
        fh.write(t.encode("utf-8"))
    after = sha(RESPONSE)
    new = RESPONSE.read_bytes()
    print(json.dumps({"before": BEFORE, "after": after, "bytes_before": len(raw), "bytes_appended": len(t.encode("utf-8")),
                      "prefix_unchanged": hashlib.sha256(new[:len(raw)]).hexdigest() == BEFORE}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
