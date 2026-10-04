"""ORCH-08C (R39HARNESS-IMPL): the ONE append to docs/milestones/M2/M2-REVIEW-RESPONSE.md for review39.

Usage: append_response_r39.py
Refuses unless (1) the response ledger still hashes to 49b4ca01... (206,103 bytes: its state before this task), (2) the
package's evidence manifest exists, (3) PACKAGE-CHECK.json is all_ok. Appends exactly one entry (one top-level heading) at
the very end, verifies that the first 206,103 bytes still hash to 49b4ca01..., and records the old and new hashes in
WORK/evidence/RESPONSE-APPEND-RECORD.json. Writes only the response ledger (append) and the record."""
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review39"
WORK = pathlib.Path("C:/t/iso/work/r2x/r39")
RESP = PILOT.parent / "M2-REVIEW-RESPONSE.md"
PREFIX, PREFIX_BYTES = "49b4ca01f4135418129f0b5a1d863f06ba9cf9879d4ed51f579d9bf81fc9ffc7", 206103
HEADING = ("# Correction package review39: harness correction after Verification 39 (drawings-AI path disabled and gated, unread pages, "
           "retry_at_full and resume policy, failed reads retried, decision coverage gate C >= B only per owner ruling A-10) (2026-10-04)")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def entry() -> str:
    man_b = (PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    man = json.loads(man_b.decode("utf-8"))
    chk = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not chk["all_ok"]:
        raise SystemExit("refused: PACKAGE-CHECK.json is not all_ok")
    t = chk["checks"]["tests"]
    b = json.loads((PKG / "PROJECT-REQUEST-BOUNDS.json").read_text(encoding="utf-8"))
    p = b["projects"]["EP-27331"]
    ri = json.loads((PKG / "RESUME-INVOCATIONS-R39.json").read_text(encoding="utf-8"))["table"]
    v = json.loads((PKG / "VISIBILITY-RESULT.json").read_text(encoding="utf-8"))
    h = chk["checks"]["harness"]["counts"]
    L = [HEADING, "",
         "- **Task:** ORCH-08C (orchestrator ledger ORCH-021; owner decision A-10 relayed during the task), agent R39HARNESS-IMPL, Claude Opus 5.5 "
         "(`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06, A-09, A-10. Work 2026-10-04 from 09:00Z.",
         f"- **Package:** `PILOT/review39/`; `evidence/EVIDENCE-MANIFEST.json` sha256 **`{sha(man_b)}`** ({man['file_count']} files); "
         f"`BINDING-MANIFEST-R39.json` `{man['binding_manifest_sha256']}` (binds review38 `07c2fb78…8ce9` / `4c2904cd…f314d` and review36 "
         f"`5e950813…9de9d0` / `5a1a6aad…e568`); `evidence/PACKAGE-CHECK.json` `{man['package_check_sha256']}` (all checks ok).",
         "- **Nature:** a correction package, pending Verification 40. Not self-approved; it authorizes nothing. The corrected declaration is ORCH-09's.",
         f"- **Harness vs review38:** {h['unchanged']} files unchanged (byte-identical), {h['changed']} changed, {h['new']} new, 0 removed "
         "(`evidence/HARNESS-FILES-R38-R39.json`, every file with its review38 and review39 hash; changed tests listed as changed).",
         f"- **Tests:** {t['total']['tests']} tests in {t['modules']} modules, 0 failures, 0 errors, 0 write-guard refusals; junit in `tests/`.", "",
         "**Changes (finding; A-09 point):**",
         "1. **Undeclared request paths** (R39-04 major; A-09 points 1 and 3): `REQUEST-PATHS.md` enumerates every provider-call site each lane "
         "reaches (static over-approximation plus hand reading); the only reachable undeclared path is the baseline drawings-AI review "
         "(`document_processing.run` -> `shop_drawings.reconcile` -> `drawing_ai_review`, up to 10 per project per B invocation). Declaration "
         "contract 4 binds `application_env` = exactly `{\"DRAWINGS_AI_REVIEW_ENABLED\": \"false\"}` (refused otherwise); `sandbox_env` sets it; "
         "every lane (live and dry, every invocation and resume) verifies it in the environment, the application's settings and "
         "`drawing_ai_review.enabled()`. The gate refuses a task kind not declared for the lane (`lane_task_kinds`) or a request without the "
         "current document's context (the lane clears it after each document) as a contract breach: recorded, never charged, the run INVALID, "
         "never a failure-streak count. 1(d): drawings-AI outputs feed no measured field in either tree (code reading and the `feed` probe: the "
         "answer is applied to the shop-drawing records, every scored project_documents column unchanged).",
         f"2. **Unread pages** (R39-06; A-09 point 1): harness and resource refusals make a document INCOMPLETE; the reader's own cap, the "
         "JobBudget and a reader exception leave it COMPLETE with every unread page recorded per page (lane rows, run report, scorer, audit) and "
         "counted as unread in every denominator. Verification 39's scenarios A (4 + 4), B (7 + 5) and C (exception) are tests. The review38 claim "
         "\"the reader's 8 is recorded per page\" was wrong (corrected in CHANGE-RECORD-R39.md; review38's record stays frozen).",
         f"3. **Retry policy** (R39-08): every DEFERRED record carries `retry_at_earliest` and `retry_at_full` (planning / structural); the "
         f"declaration's `resume_policy` (`full` default, `earliest` allowed) is enforced (an early resume is refused and creates nothing). "
         f"EP-27331 invocations: planning demand full {ri['planning']['full']} / earliest {ri['planning']['earliest_paced']}-{ri['planning']['earliest_burst']}; "
         f"structural demand full {ri['structural']['full']} / earliest {ri['structural']['earliest_paced']}-{ri['structural']['earliest_burst']}; "
         "every resume needs its own owner authorization.",
         "4. **Failed reads and the capture store** (R39-16): the store serves bound answers only; a fingerprint whose dispatches all failed is "
         "dispatched again on the application's own retry path (charged, never refunded, recorded as a retry with its ordinal), identically for B "
         "and C; interrupted dispatches are still never re-sent; R is still served C's capture by content key; P's sample is frozen at its first run. "
         "Accuracy implication stated in LIVE-RUN-CONTRACT.md section 13. Consequence for the bounds: B is now 2 per document per invocation, "
         f"so EP-27331 is planning {p['planning']['all_lanes']} / structural {p['structural_maximum']['all_lanes']} (not the expected 154: +6 for B's "
         f"retry), 3 windows; with the drawings-AI path enabled it would be {p['drawings_ai']['if_enabled']['structural_all_lanes']} "
         f"({p['drawings_ai']['if_enabled']['r38_model_all_lanes']} on review38's model, Verification 39's 164); required application minimum "
         f"{b['compatible_limits']['required_minimum']['AI_MAX_CALLS_PER_PROJECT_PER_DAY']} unchanged.",
         "5. **Decision coverage gate** (R39-15; owner ruling A-10): eligibility is C >= B only. **This is a change from plan v2** (whose gate "
         "was C >= B and C >= R), ruled by the owner on 2026-10-04 -- not an unchanged gate. C >= R is a MANDATORY diagnostic in every scorer "
         "result and report (counts, missing coverage per document, reasons; INCOMPLETE when R is truncated); the scorer and the declaration "
         "contract refuse any definition that binds R into eligibility. Every other safety, accuracy and completeness gate is unchanged.",
         "6. **Model identity** (R39-09): `MODEL-ID-EVIDENCE.md` from a read-only byte search of the installed CLI (2.1.263, sha256 `0b35df94…5b03`; "
         "never executed): both pinned ids are in its catalog and a full id passes `--model` unchanged; `--output-format json` reports the "
         "REQUESTED model as the `modelUsage` key (no dated id); only `stream-json`'s `message.model` exposes the server's statement. Served-model "
         "identity: **UNRESOLVED** offline; the owner's probe command, expected evidence and interpretation are given (not run). The runtime check "
         "stays fail-closed for any verifiable mismatch (limits stated).",
         "7. **Records** (R39-02, R39-17): the binding manifest of review38 is `4c2904cd…398bcf7fee…f314d` (bound by hash here). Correction of the "
         "review38 response entry: its carried modules were unchanged by hash, but **two of their tests had changed** "
         "(`test_literal_compare_r32.py`: one judge-level expectation for the 25 formerly forgiven controls; `test_sandbox_ingest_r32.py`: a "
         "path-only change); and its \"R1 30, R2 24, R3 26\" were **case counts** -- the 40 kept fixtures are **R1 15, R2 12, R3 13**. The "
         "static request-path step failed twice before succeeding (a shell heredoc parse error, then a missing output folder); explained in "
         "REQUEST-PATHS.md section 3 and the audit log.",
         f"8. **Visibility:** `VISIBILITY-REPORT.md` re-run over the r39 harness, {len(v['scenarios'])} dry scenarios (12 of review38 plus undeclared "
         f"task kind, missing context, unread pages, the full resume policy, the failed-read retry); every event visible in every place it can reach: "
         f"{v['all_visible']}; contract breaches only where injected: {v['breaches_only_where_injected']}; model requests {v['model_requests']}.", "",
         f"**Zero calls:** no provider or model request of any kind, no `claude` invocation in any form, no network; no prediction; no ledger scope, "
         f"token, authorization file, run file or declaration created; the AI ledger was opened read-only only and reads "
         f"{chk['checks']['ai_ledger']['entries']} entries / {chk['checks']['ai_ledger']['scopes']} scopes / 0 amendments before and after.", "",
         "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed (AI-ACCURACY-POLICY-AMENDMENT-R32-01).", "",
         "**Status, stated separately:**",
         "1. **Correction readiness:** Verification 39's R39-04, R39-06, R39-08, R39-16, R39-15 (with A-10), R39-09, R39-02 and R39-17 are answered by "
         "this package, **pending Verification 40**; the corrected declaration is **pending ORCH-09** (needs Verification 40 and the owner's "
         "model-identity probe outcome or acceptance of UNRESOLVED identity).",
         "2. **Accuracy:** none. No prediction exists; every figure is from SYNTHETIC fixtures, dry stubs or models.",
         "3. **Label truth:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) independently AI-reviewed (Claude agents), not human-signed; populations "
         "identity 57, revision 38, decision 38.",
         "4. **Permissions and budget:** eligibility only (A-06). No declaration, authorization file, token, budget, ledger scope or dispatch exists.",
         "5. **M2:** **CHANGES STILL REQUIRED.**",
         "6. **M3:** not started."]
    return "\n".join(L) + "\n"


def main():
    old = RESP.read_bytes()
    if sha(old) != PREFIX or len(old) != PREFIX_BYTES:
        raise SystemExit(f"refused: the response ledger is not in its pre-task state ({sha(old)}, {len(old)} bytes)")
    text = entry()
    sep = b"" if old.endswith(b"\n\n") else (b"\n" if old.endswith(b"\n") else b"\n\n")
    with open(RESP, "ab") as fh:
        fh.write(sep + text.encode("utf-8"))
    new = RESP.read_bytes()
    if sha(new[:PREFIX_BYTES]) != PREFIX:
        raise SystemExit("the prefix changed (must never happen)")
    rec = {"file": RESP.as_posix(), "before_sha256": PREFIX, "before_bytes": PREFIX_BYTES, "after_sha256": sha(new), "after_bytes": len(new),
           "prefix_verified": True, "appended_bytes": len(new) - PREFIX_BYTES, "heading": HEADING}
    (WORK / "evidence" / "RESPONSE-APPEND-RECORD.json").write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
