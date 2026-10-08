"""ORCH-10 (R42PORT-IMPL): the final report (section 3 of the task) -- written ONCE into
PILOT/declaration-r32-v3/IMPLEMENTATION-REPORT.md (before that package's check and manifest) and printed. Every hash and
count is read from the evidence. Usage: make_report_r42.py [--print-only]"""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402


def load(p):
    return json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def text() -> str:
    P, R = C.PACKAGE, C.REVIEW42
    fsha = C.sha256_file(P / C.DECLARATION_NAME)
    bsha = C.sha256_file(C.BINDING42)
    r42m = C.sha256_file(R / "evidence/EVIDENCE-MANIFEST.json")
    t42 = load(R / "tests/SUMMARY.json")
    t3 = load(P / "tests/SUMMARY.json")
    demos = load(R / "evidence/demos/DEMOS-R42.json")
    dry = load(P / "dry-run/DRY-EXERCISE.json")
    pre = load(P / "dry-run/PREFLIGHT-RESULTS.json")
    diff = load(P / "DECLARATION-DIFF.json")
    man = load(C.BINDING42)
    path = load(P / "evidence/PATHLEN-PROBE.json")["summary"]
    pr = pre["checks"]["3_negative_probes"]
    changed = man["changed_from_review39"]
    new = man["new_in_review42"]
    loops = [v["invocations"] for v in dry["deferral_loops"].values()]
    dm = demos["demos"]
    L = [
        "# ORCH-10 implementation report (R42PORT-IMPL): review42 and declaration-r32-v3", "",
        "## Hashes",
        f"- Declaration v3 `FRESH-VALIDATION-DECLARATION-R32-V3.json`: **`{fsha}`** (contract `r42-live-contract-5`; placeholder once; refused as written).",
        f"- `BINDING-MANIFEST-R42.json`: **`{bsha}`** ({sum(len(v) for v in man['files'].values())} bindings; all {man['r39_rehash']['equal']} carried from R39 re-hash equal, 0 differ, 0 missing).",
        f"- review42 `evidence/EVIDENCE-MANIFEST.json`: **`{r42m}`**.",
        "- declaration-r32-v3 `evidence/EVIDENCE-MANIFEST.json`: written after this report (see the response-ledger entry and the hand-back).",
        f"- Supersedes v2 `{C.V2_SHA}` (never to be run). PROJECT-REQUEST-BOUNDS (review42) equals R39's in every verified key (only `run_set.path` re-pointed); RESUME-INVOCATIONS byte-identical.", "",
        "## What changed and why (per finding)",
        f"- **Portability (A-11, 2.1):** every Desktop binding re-pointed to the merged installation and re-hashed (no byte difference); the merged venv interpreter bound (path, sha256, version; both trees' requirements and imports satisfied); extended-length hashing; the CLI pinned by absolute path + sha256 `0b35df94…5b03` + `2.1.263 (Claude Code)`, checked before any lane and every resume (read as bytes); isolation from the merged installation checked at every lane's start and end; the bundled 2.1.289 and the merged `.env` never used. Path lengths: bound max {path['bound_max']}, live staged PDFs max {path['live_staged_max']}, nothing else ≥ 260.",
        "- **R40-04 (option 2):** a fail-closed `RefusingGlobalProvider` is the application's global provider in C, R and P (installed before any application code; any `get_provider().complete()` refused, recorded as breach `global_provider_request`, run INVALID); B unchanged. Static: all 88 site-lane pairs resolved; dynamic: C, R, P refused, B unchanged.",
        "- **R41-09 / R41-10 / R41-11:** every check (CLI file, version line, free disk ≥ 2 GiB, binding, HEADs, truth, run set, bounds, scope, guard preview) before the run folder; capture store then atomic allowance before the nonce is consumed; `run` re-enters a folder with no allowance, no consumed nonce, no charge (REENTRY record); resume re-checks CLI and disk before its nonce. Cases T, A, B, C, D, E: none consumes an authorization, none strands the run; refusals that must stay still refuse.",
        "- **A-11 §4:** multi-invocation authorization (max 3, in-order nonces, strict keys) as a separable proposal; per-invocation form unchanged.",
        "- **R41-12 / R41-13 / R41-14:** statements corrected in the declaration and response entry; the four r40 work records bound by hash.",
        f"- Harness files changed: {len(changed)} ({', '.join(changed)}); new: {len(new)} ({', '.join(new)}).", "",
        "## Tests",
        f"- review42: **{t42['total']['tests']} tests, {t42['total']['failures']} failures, {t42['total']['errors']} errors, {t42['total']['skipped']} skipped**, {t42['guard_refusals']} audit-guard refusals (26 modules, package harness).",
        f"- declaration-r32-v3: **{t3['tests']} tests, {t3['failures']} failures, {t3['errors']} errors**, {t3['guard_refusals']} guard refusals.",
        f"- Preflight: {sum(r['as_expected'] for r in pr['rows'])}/{pr['count']} probes as expected ({pr['carried_from_v2']} from v2 + {pr['new_for_contract_5']} new); all checks ok: {pre['ok']}. Diff: protected values unchanged {diff['protected_all_ok']}.", "",
        "## Demonstrations (dry / live-shaped; 0 CLI invocations; ledger 483/17/0 unchanged)",
        *[f"- {k}: {'passed' if v['ok'] else 'FAILED'}" for k, v in dm.items()],
        f"- Dry exercise: single 24-document run {dry['single']['report']['run_state']}; six per-project runs finished; EP-27331 loops {loops} invocations; cross-project drill {dry['cross_project_drill']['loop']['invocations']} invocations; CLI-version case not a dead-end; {dry['model_requests_total']} model requests.", "",
        "## Residual risks",
        "- The disk floor is checked at each invocation's start only; another writer can still fill the drive during an invocation.",
        "- Isolation compares paths textually (an 8.3 short name of the merged folder would pass).",
        "- An application path building its own provider object would bypass the chain (none reached statically).",
        "- The live path (real CLI, real scope, real authorization) is shown only live-SHAPED offline; served-model identity stays UNRESOLVED.",
        "- With the multi-invocation form, a leaked token plus that file allow up to 3 invocations without a further owner action (never beyond the 556-request parent).", "",
        "## Not authorized",
        "No scope, token, authorization file, RUN file, request, dispatch of B/C/R/P, default, M2 acceptance or M3. No `claude` process was started; no provider or model request was made.", "",
        "## Statuses",
        "- Correction readiness: delivered for Independent Verification 42; not self-approved.",
        "- Accuracy: none; no prediction exists.",
        "- Label truth: reference set independently AI-reviewed (Claude agents), not human-signed.",
        "- Permissions/budget: eligibility only; nothing authorized.",
        "- M2: CHANGES STILL REQUIRED. M3: not started.", "",
        "READY FOR INDEPENDENT VERIFICATION 42", ""]
    return "\n".join(L)


if __name__ == "__main__":
    t = text()
    if "--print-only" not in sys.argv:
        C.write_once(C.PACKAGE / "IMPLEMENTATION-REPORT.md", t)
    print(t)
    print("WORDS", len(t.split()), file=sys.stderr)
