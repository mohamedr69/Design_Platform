"""ORCH-08 (R38HARNESS-IMPL): the ONE append to docs/milestones/M2/M2-REVIEW-RESPONSE.md for review38.

Usage: append_response_r38.py <record json (new, absolute)>
Refuses unless (1) the response ledger still hashes to 664fc295... (its state before this task), (2) the package's evidence
manifest exists, (3) PACKAGE-CHECK.json is all_ok. Appends exactly one entry (one top-level heading) at the very end, then
verifies that the first len(old) bytes still hash to 664fc295... and records the old and new hashes. Writes only the
response ledger (append) and the record."""
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review38"
RESP = PILOT.parent / "M2-REVIEW-RESPONSE.md"
PREFIX = "664fc295e4f8239b70cbec51a5a573e7e9943d60ee8ac1c255e6fe3426c55652"
HEADING = ("# Correction package review38: A-09 harness correction (deferral and visible INCOMPLETE, compatible limits, pinned model identity, "
           "lane allowances, evidenced cross-page identity, R/P no credit) (2026-10-03)")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def entry() -> str:
    man_b = (PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    man = json.loads(man_b.decode("utf-8"))
    chk = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    b = json.loads((PKG / "PROJECT-REQUEST-BOUNDS.json").read_text(encoding="utf-8"))
    w = json.loads((PKG / "CROSS-PAGE-WHATIF.json").read_text(encoding="utf-8"))
    v = json.loads((PKG / "VISIBILITY-RESULT.json").read_text(encoding="utf-8"))
    t = chk["checks"]["tests"]
    p = b["projects"]["EP-27331"]
    kept = w["associations_kept_with_evidence"]["by_relationship"]
    scen = ", ".join(f"{k} ({'/'.join(str(s['recorded_in'][x]) for x in ('run_state', 'lane_rows', 'scorer', 'audit'))})" for k, s in v["scenarios"].items())
    L = [HEADING, "",
         "- **Task:** ORCH-08 (orchestrator ledger ORCH-019), agent R38HARNESS-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). "
         "Authorities A-03, A-06, A-09. Work 2026-10-03 18:20Z to about 19:40Z (interrupted by the account usage limit) and 2026-10-04 from 07:39:51Z.",
         f"- **Package:** `PILOT/review38/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`{sha(man_b)}`** ({man['file_count']} files); "
         f"`BINDING-MANIFEST-R38.json` `{man['binding_manifest_sha256']}`; `evidence/PACKAGE-CHECK.json` `{man['package_check_sha256']}` (all checks ok).",
         "- **Nature:** a correction package, pending ORCH-08V (Verification 39). Not self-approved; it authorizes nothing. The corrected declaration is ORCH-09's.",
         f"- **Tests:** {t['total']['tests']} tests in {t['modules']} modules, 0 failures, 0 errors, 0 write-guard refusals; junit in `tests/`; the whole suite runs "
         "from the harness itself (the sandbox base is declared / parameterised, default `C:/t/r2x/r38-sandbox`; no test twin).", "",
         "**Changes (A-09 point; finding):**",
         f"1. **Request bounds and compatible limits** (point 1; R38-08): new `project_bounds_r32.py`, `PROJECT-REQUEST-BOUNDS.json` "
         f"(`{man['project_request_bounds_sha256']}`); EP-27331 planning {p['planning']['all_lanes']} (B {p['planning']['B']}, C {p['planning']['C']}, "
         f"R {p['planning']['R']}, P {p['planning']['P']}), structural maximum {p['structural_maximum']['all_lanes']} (B {p['structural_maximum']['B']}, "
         f"C {p['structural_maximum']['C']}, R {p['structural_maximum']['R']}, P {p['structural_maximum']['P']}); the harness rolling window (<= 60 per 86,400 s, "
         f"all lanes) governs; `validate_declaration` refuses `AI_MAX_CALLS_PER_PROJECT_PER_DAY` / `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` below "
         f"{b['compatible_limits']['required_minimum']['AI_MAX_CALLS_PER_PROJECT_PER_DAY']} (the largest row count of one lane database: EP-27331 12 + 72) "
         "and per-document limits other than 12 / 120 s; the live preflight recomputes the bounds file.",
         "2. **Visible refusals and rolling-window deferral** (point 1; R35-09, R38-08): every refusal (lane allowance, parent ceiling / tokens / elapsed, "
         "window, breaker, ledger, guard, identity, terminal stop, the application's own limits) is recorded per document and page in the lane rows, the run "
         "report, the scorer and the audit view; a window refusal is never charged: the document is DEFERRED with its earliest retry, a resume dispatches it "
         "once the window frees (never a bound fingerprint again), a deferral that cannot finish within the elapsed bound ends INCOMPLETE (or the run is CLOSED); "
         "B/C limit-affected documents make the comparison INCOMPLETE and stay in every denominator; silent skipping fails the tests.",
         "3. **Model identity** (point 2; R38-10): full ids pinned, `claude-sonnet-5` (small) / `claude-opus-5` (standard), aliases refused; "
         "`claude --version` and the provider identity recorded per invocation (held equal across the run); every response checked; a mismatch "
         "records the offending request in `IDENTITY-INVALID.json`, makes the run INVALID and refuses the next request and every resume.",
         "4. **Parent budget and lane allowances** (point 3; R35-10, R38-13): one immutable parent (556; token and elapsed bounds) with lane "
         "allowances B 240 / C 240 / R 40 / P 36; no borrowing; failed, timed-out, interrupted and dispatched-but-unsaved requests stay charged; durable "
         "stops and refusals survive resume; `ALLOWANCE-AUDIT.json` / `allowance_r32.py audit` list every charge with lane, document, outcome and ledger "
         "entry, reconciled with the single ledger scope (its limits must equal the parent's).",
         f"5. **Cross-page identity** (point 4; R34-06, R36-09): rule CP-R38 (source, document identity, target and the labels' recorded page "
         f"relationship R1 / R2 / R3; never the file alone; conflicting identity earns no credit). `CROSS-PAGE-WHATIF.json` (`{man['cross_page_whatif_sha256']}`): "
         f"{w['changed_target_verdicts']} target verdicts change on {len(w['changed_fixtures'])} fixtures (pair {w['changed_by_path']['pair']}, wired "
         f"{w['changed_by_path']['wired']}), all to critical_false_acceptance; {len(w['associations_kept_with_evidence']['fixtures'])} fixtures keep an "
         f"evidenced association ({kept}); the r36 copy reproduces the frozen matrix except exactly the 106 H1 cases.",
         "6. **Unsupported-control shortfall** (point 5): a declared scope limitation in every scorer result (no argument removes it), "
         "`REPORT-TEMPLATE.md` states that unsupported-format safety and generalization are not claimed; the selector refuses any replacement once a "
         "prediction exists for the run.",
         "7. **R and P** (point 6; R38-09): no accuracy or recovery credit anywhere; the decision coverage gate is C >= B only (the C >= R leg becomes a "
         "reported diagnostic: stated as a consequence); the candidate outcome reads only B and C; a truncated R or P is an INCOMPLETE diagnostic; tests "
         "prove a full, a truncated and no R give the identical candidate outcome.",
         f"8. **Visibility proof** (point 7): `VISIBILITY-REPORT.md` / `VISIBILITY-RESULT.json`, {len(v['scenarios'])} dry scenarios with the refusing stub "
         f"(records found in run state / lane rows / scorer / audit): {scen}. Every injected event visible in every place: {v['all_visible']}; "
         f"no bound fingerprint re-sent: {v['no_resend']}.",
         "9. **Carried unchanged by hash:** the adapter, literal comparison (H1 fix), converter, sandbox ingestion, concentration rule v2, the review31 / v4 "
         "copies (capture store, coverage, state check, stop rules), the dispatch guard and their tests; the selector's selection code is byte-identical "
         "(only the replacement refusal appended). Records: CHANGE-RECORD.md, SCORER-CHANGES.md v3, LIVE-RUN-CONTRACT.md v3, BINDING-MANIFEST-R38.json, "
         "COMMANDS.md, COMMANDS-AND-AUDIT-LOG.md.", "",
         f"**Dry exercise:** {v['model_requests']} provider calls; AI ledger (mode=ro) before {v['ai_ledger']['before']['entries']} / "
         f"{v['ai_ledger']['before']['scopes']}, after {v['ai_ledger']['after']['entries']} / {v['ai_ledger']['after']['scopes']}.", "",
         "**Zero calls:** no provider or model request of any kind, no `claude -p`, no network; no prediction (SYNTHETIC fixtures, refusing stubs and "
         "SYNTHETIC EP-990001 documents only); no ledger scope, token, authorization file, run file or declaration created; the AI ledger was opened "
         f"read-only only and reads {chk['checks']['ai_ledger']['entries']} entries / {chk['checks']['ai_ledger']['scopes']} scopes / "
         f"{chk['checks']['ai_ledger']['limit_amendments']} amendments before and after; no OneDrive; no sealed project. Disclosure: one local "
         "`claude --version` (2026-10-03T18:38:42Z, `2.1.263 (Claude Code)`; no -p, no model request).", "",
         "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).", "",
         "**Status, stated separately:**",
         "1. **Source permission:** unchanged. A-02 covers access, staging, drafting and preparation; A-06 grants project and provider eligibility only, not dispatch.",
         "2. **Drafting:** `r32-labels-draft-1` is frozen; AI-drafted, not human-signed.",
         "3. **Reference set:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) is independently AI-reviewed (Claude agents), not human-signed.",
         "4. **Field populations:** identity 57, revision 38, decision 38.",
         "5. **Conditions:** the A-09 harness points are answered by this package, **pending Verification 39 (ORCH-08V)**; the corrected declaration is **pending ORCH-09**.",
         "6. **Live-run authorization and budget:** none. The declaration `38e08df9…` stays superseded and NOT authorized; no new declaration, authorization "
         "file, token, budget, ledger scope or dispatch exists.",
         "7. **M2:** **CHANGES STILL REQUIRED.**",
         "8. **M3:** not started.", ""]
    return "\n".join(L)


def main(record):
    record = pathlib.Path(record)
    if record.exists():
        raise SystemExit("refused: the response append is made once")
    old = RESP.read_bytes()
    if sha(old) != PREFIX:
        raise SystemExit(f"PACKET MISMATCH: M2-REVIEW-RESPONSE.md is {sha(old)}, not {PREFIX}")
    text = entry()
    add = ("\n" if not old.endswith(b"\n\n") else "") + text
    with open(RESP, "ab") as fh:
        fh.write(add.encode("utf-8"))
    new = RESP.read_bytes()
    ok = sha(new[:len(old)]) == PREFIX and new.count(HEADING.encode("utf-8")) == 1
    rec = {"response_ledger": RESP.as_posix(), "before_sha256": PREFIX, "before_bytes": len(old), "after_sha256": sha(new), "after_bytes": len(new),
           "appended_bytes": len(new) - len(old), "prefix_unchanged": ok, "heading": HEADING,
           "manifest_sha256": sha((PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes())}
    record.write_text(json.dumps(rec, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rec, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
