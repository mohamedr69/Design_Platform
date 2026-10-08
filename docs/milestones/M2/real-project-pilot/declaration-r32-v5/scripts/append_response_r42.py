"""ORCH-10 (R42PORT-IMPL): the ONE append to docs/milestones/M2/M2-REVIEW-RESPONSE.md for review42 and declaration-r32-v3.

Usage: append_response_r42.py   (with the R42 audit guard: R42_GUARD_ALLOW_EXTRA=<the response ledger> allows this one file)
Refuses unless (1) the response ledger still hashes to 1143c685... (219,716 bytes: its state before this task), (2) both
packages' evidence manifests exist and their PACKAGE-CHECK files are all_ok. Appends exactly one entry (one top-level
heading) at the very end, verifies that the first 219,716 bytes still hash to 1143c685..., and records the old and new
hashes in WORK/RESPONSE-APPEND-RECORD.json. Writes only the response ledger (append) and the record."""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

PREFIX, PREFIX_BYTES = C.RESPONSE_BEFORE
HEADING = ("# Portability and safety correction of the fresh-validation harness (review42) and declaration v3 (ORCH-10, 2026-10-06): "
           "frozen, NOT authorized, NO dispatch")


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def entry() -> str:
    m42, m3 = C.REVIEW42 / "evidence/EVIDENCE-MANIFEST.json", C.PACKAGE / "evidence/EVIDENCE-MANIFEST.json"
    for p in (C.REVIEW42, C.PACKAGE):
        if not load(p / "evidence/PACKAGE-CHECK.json")["all_ok"]:
            raise SystemExit(f"refused: {p.name} PACKAGE-CHECK is not all_ok")
    man42, man3 = load(m42), load(m3)
    t42, t3 = load(C.REVIEW42 / "tests/SUMMARY.json"), load(C.PACKAGE / "tests/SUMMARY.json")
    demos = load(C.REVIEW42 / "evidence/demos/DEMOS-R42.json")
    dry = load(C.PACKAGE / "dry-run/DRY-EXERCISE.json")
    pre = load(C.PACKAGE / "dry-run/PREFLIGHT-RESULTS.json")
    diff = load(C.PACKAGE / "DECLARATION-DIFF.json")
    bsha = C.sha256_file(C.BINDING42)
    probes = pre["checks"]["3_negative_probes"]
    loops = [v["invocations"] for v in dry["deferral_loops"].values()]
    L = [HEADING, "",
         "- **Task:** ORCH-10 (orchestrator ledger ORCH-027), agent R42PORT-IMPL, Claude Opus 5.5 (`claude-opus-5-5`), effort High (self-reported). Authorities A-03, A-06, A-09, A-10, A-11. Work 2026-10-05 from about 20:01Z.",
         f"- **review42:** `PILOT/review42/`, `evidence/EVIDENCE-MANIFEST.json` **`{C.sha256_file(m42)}`** ({man42['file_count']} files); `BINDING-MANIFEST-R42.json` **`{bsha}`** (every one of the 239 bindings carried from R39 re-hashes equal at its merged path; the runnable harness bound from `review42/scripts/harness-r32` only).",
         f"- **Declaration v3:** `PILOT/declaration-r32-v3/FRESH-VALIDATION-DECLARATION-R32-V3.json` **`{man3['declaration_sha256']}`**, contract `r42-live-contract-5`; manifest **`{C.sha256_file(m3)}`** ({man3['file_count']} files). Supersedes v2 `f38fb281…25af` (A-11: not runnable as declared; never to be run). Placeholder digest exactly once; refused as written; an in-memory dummy-digest copy passes. Stamp `r32-v3`, run folder `C:/t/r2x/r42-sandbox/r32-v3` (absent), scope `{C.SCOPE}` (absent).",
         f"- **Every number of v2 carried** (DECLARATION-DIFF protected values unchanged: {diff['protected_all_ok']}): arms, run set, truth, reference set, parent 556 / 16.3 M / 3.26 M / 604,800 s, allowances 240/240/40/36, window 60 / 86,400 s, thresholds, \"96\" / \"600\" / \"12\" / \"120\", the gate C ≥ B only (a change from plan v2, A-10), `resume_policy` full, stop rules, concentration results, pins.",
         "- **Corrections:** portability (re-pointed bindings; the bound interpreter; extended-length hashing; the CLI pinned by absolute path, file sha256 and version line; isolation from the merged installation, whose bundled CLI 2.1.289 and `.env` are never used); **R40-04 closed by option 2** (a fail-closed refusing global provider in C, R and P; B unchanged); **R41-09** (every check before the run folder; the nonce consumed only after the allowance and the capture store exist; re-entry of a folder without an allowance); **R41-10** (the 2 GiB disk floor enforced by the runner and the scope command); **R41-11** (CLI file, version and disk re-checked before every resume's nonce); **A-11 §4** (one approval for up to 3 planned invocations, a separable proposal); R41-12 and R41-13 statements corrected; the four r40 work records bound by hash (R41-14).",
         f"- **Tests:** review42 {t42['total']['tests']} tests, {t42['total']['failures']} failures, {t42['total']['errors']} errors, {t42['total']['skipped']} skipped, {t42['guard_refusals']} audit-guard refusals; declaration package {t3['tests']} tests, {t3['failures']} failures.",
         f"- **Demonstrations (dry / live-shaped, 0 CLI invocations):** {sum(1 for v in demos['demos'].values() if v['ok'])}/{len(demos['demos'])} passed -- ordinary completion; refusal before dispatch; interruption at every phase and recovery without re-sending a charged request; Verification 41's dead-end cases T, A, B, C, D, E (none consumes an authorization or strands the run); durable charging; terminal-stop preservation; the window deferral and its resume at retry_at_full; complete page accounting; the global-provider boundary.",
         f"- **Preflight:** {sum(r['as_expected'] for r in probes['rows'])}/{probes['count']} probes as expected; binding, bounds, four lane environments with isolation, interpreter, CLI file, disk pass; the runner and guard refuse with no folder and no `--version`.",
         f"- **Dry exercise (stated exactly, R41-13):** ONE single 24-document dry run ({dry['single']['report']['run_state']}) AND six per-project dry runs; EP-27331 deferral loops {loops} invocations; a cross-project drill on all 24 documents ({dry['cross_project_drill']['loop']['invocations']} invocations); the CLI-version case no longer a dead-end. For the record: v2's own dry exercise was six per-project runs, and Verification 41 ran the single run.",
         "",
         "**Zero calls:** no provider or model request, no `claude` process of any kind (the installed binary read as bytes only; every process ran under an audit guard that refuses any `claude` process and any network use), no ledger scope, token, authorization file or RUN file; the AI ledger was opened read-only and reads 483 / 17 / 0 before and after.",
         "",
         "**Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed.",
         "",
         "**Status, stated separately:**",
         "1. **Correction readiness:** delivered for Independent Verification 42 (ORCH-10V); not self-approved.",
         "2. **Accuracy:** none. No prediction exists.",
         "3. **Label truth:** `r32-labels-reviewed-2` (`89c60e9d…b9a6`) independently AI-reviewed (Claude agents), not human-signed.",
         "4. **Permissions and budget:** eligibility only (A-06). Nothing is authorized: no scope, token, authorization file, RUN file, budget or dispatch.",
         "5. **M2:** **CHANGES STILL REQUIRED.**",
         "6. **M3:** not started.", ""]
    return "\n".join(L)


def main():
    old = C.RESPONSE_LEDGER.read_bytes()
    if C.sha256_bytes(old) != PREFIX or len(old) != PREFIX_BYTES:
        raise SystemExit(f"refused: the response ledger is not in its pre-task state ({C.sha256_bytes(old)}, {len(old)} bytes)")
    text = entry()
    sep = b"" if old.endswith(b"\n\n") else (b"\n" if old.endswith(b"\n") else b"\n\n")
    with open(C.RESPONSE_LEDGER, "ab") as fh:
        fh.write(sep + text.encode("utf-8"))
    new = C.RESPONSE_LEDGER.read_bytes()
    if C.sha256_bytes(new[:PREFIX_BYTES]) != PREFIX:
        raise SystemExit("the prefix changed (must never happen)")
    rec = {"file": C.RESPONSE_LEDGER.as_posix(), "before_sha256": PREFIX, "before_bytes": PREFIX_BYTES, "after_sha256": C.sha256_bytes(new),
           "after_bytes": len(new), "prefix_verified": True, "appended_bytes": len(new) - PREFIX_BYTES, "heading": HEADING}
    C.write_json(C.WORK / "RESPONSE-APPEND-RECORD.json", rec)
    print(json.dumps(rec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
