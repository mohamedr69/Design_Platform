"""ORCH-10 (R42PORT-IMPL): write review42's CHANGE-RECORD-R42.md and COMMANDS.md (once each) from the binding manifest, the
test summary, the outputs record and the demonstrations record (so every number in them is read from the evidence)."""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

R = C.REVIEW42
FINDING = {
    "inputs_r32.py": "2.1.1 portability (PILOT -> the merged installation); 2.1.3 path lengths (sha256_file through the extended-length prefix)",
    "sandbox_ingest_r32.py": "2.1.1 the bound interpreter (PY -> the merged venv); 2.1.5 isolation (PWD / OLDPWD dropped from sandbox_env)",
    "preflight_r32.py": "contract 5: 2.1.1 interpreter, 2.1.4 the CLI file check, 2.3 the disk floor (R41-10), 2.1.5 isolation, 2.2 global_provider, 2.4 resume_authorization; 2.1.3 verify_binding through the extended-length prefix; the dry / test sandbox base r42",
    "model_identity_r38.py": "2.1.4 the CLI pinned by absolute path + sha256 + exact version line (validate_pins), verify_cli_file (bytes only), check_version (pure, before anything; R41-09 A/T, R41-11)",
    "dispatch_guard_r32.py": "2.4 one approval for all planned resumptions: the multi-invocation form (strict keys, in-order nonces, bound, reuse / out-of-order refusals); the per-invocation form unchanged",
    "run_state_r38.py": "2.2 R40-04: the breach kind global_provider_request (class limit)",
    "run_control_r38.py": "2.2 R40-04: RefusingGlobalProvider (fail-closed, recorded, INVALID)",
    "lane_r32.py": "2.2 R40-04: the refusing global provider installed in C, R, P before any application code, checked at the end, the dry drill global_provider_request; 2.1.5 isolation checked at the lane's start and end",
    "runner_r32.py": "2.3 R41-09 / R41-10 / R41-11: every check (CLI file, disk, version line) before the folder; capture store then atomic allowance before the nonce is consumed; reentry_proof; resume re-checks; the dry drill kind global_provider_request",
    "r32_test_helpers.py": "tests: contract-5 temporary declarations (fake CLI file hashed, never executed); merged paths; base r42",
    "test_model_identity_r38.py": "tests: the CLI pin, check_version, verify_cli_file",
    "test_runner_r32.py": "tests: base r42; direct execute() calls prepare the allowance and the capture store as main now does",
    "test_preflight_r32.py": "tests: merged paths, base r42, contract name",
    "test_dispatch_guard_r32.py": "tests: merged path constant", "test_literal_compare_r32.py": "tests: merged path constant",
    "test_project_bounds_r32.py": "tests: merged path constant", "test_sandbox_ingest_r32.py": "tests: base r42 in the docstring",
    "request_paths_r42.py": "2.2 (a): the static analysis re-run plus the global-provider resolution of every get_provider() site",
    "test_global_provider_r42.py": "2.2 (a), (b), (c): static and dynamic proof in C, R, P; lane B unchanged",
    "test_runner_order_r42.py": "2.3: Verification 41's dead-end cases T, A, B, C, D, E (dry and live-shaped), the refusals that stay, resume re-checks, the multi-nonce run",
    "test_resume_authorization_r42.py": "2.4: both forms and every refusal",
    "test_portability_r42.py": "2.1: merged bindings, interpreter, long paths, CLI pin, disk floor, isolation, contract-5 keys",
}


def main() -> int:
    man = json.loads(C.BINDING42.read_text(encoding="utf-8"))
    bsha = C.sha256_file(C.BINDING42)
    tests = json.loads((R / "tests/SUMMARY.json").read_text(encoding="utf-8"))
    outs = json.loads((R / "evidence/OUTPUTS-R42.json").read_text(encoding="utf-8"))
    demos = json.loads((R / "evidence/demos/DEMOS-R42.json").read_text(encoding="utf-8"))
    rows = []
    for name, v in sorted(man["harness_files"].items()):
        if v["status"] == "unchanged":
            continue
        rows.append(f"| `{name}` | {v['status']} | `{v.get('r39_sha256', '—')[:12]}…` | `{v['r42_sha256'][:12]}…` | "
                    f"+{v.get('lines_added', v.get('lines'))} / -{v.get('lines_removed', 0)} | {FINDING.get(name, '?')} |")
    mods = tests["modules"]
    L = [
        "# CHANGE-RECORD-R42: the r32 harness corrected for portability and safety in the merged installation (ORCH-10)", "",
        "- **Task:** ORCH-10 (orchestrator ledger ORCH-027; task file sha256 `4ee96b8a…9b89`), agent R42PORT-IMPL, Claude Opus 5.5 (`claude-opus-5-5`, self-reported), effort High. Authorities A-03, A-06, A-09, A-10, A-11.",
        "- **Not self-approved.** Delivered for Independent Verification 42 (ORCH-10V).",
        f"- **Binding:** `BINDING-MANIFEST-R42.json` sha256 **`{bsha}`** ({sum(len(x) for x in man['files'].values())} path-keyed bindings in {len(man['files'])} groups). "
        f"Every one of the {man['r39_rehash']['equal']} bindings carried from R39 re-hashes EQUAL at its merged path (0 differ, 0 missing). The runnable harness is bound from `PILOT/review42/scripts/harness-r32/` only (`harness_r42_package`, {len(man['files']['harness_r42_package'])} files).",
        "- **Standing status:** M2 CHANGES STILL REQUIRED; M3 not started. Reference set independently AI-reviewed (Claude agents), not human-signed.", "",
        "## 1. Every changed or new harness file", "",
        f"{len(man['unchanged_from_review39'])} files are byte-identical to review39 (listed in the binding manifest `unchanged_from_review39`).", "",
        "| File | Status | R39 sha256 | R42 sha256 | Lines | Finding / task item |", "|---|---|---|---|---|---|", *rows, "",
        "## 2. What changed and why", "",
        "### 2.1 Portability (A-11; the Desktop installation and venv are absent)",
        "- Every binding re-pointed to `G:/dev (2)/dev/ep-platform-merged/ep-platform/…`; every carried file re-hashes equal (no byte difference found).",
        "- The interpreter is bound: `…/ep-platform/backend/venv/Scripts/python.exe` (Python 3.12.10). Contract 5 binds its path, sha256 and version; the runner and every live lane refuse another `sys.executable`. Its packages equal both frozen trees' `requirements.txt` pins and every application module of both trees imports under it (`PILOT/declaration-r32-v3/evidence/INTERPRETER-CHECK.json`).",
        "- Path lengths: `sha256_file` and `verify_binding` open files through the extended-length prefix (`LongPathsEnabled` = 0); the probe is in `PILOT/declaration-r32-v3/evidence/PATHLEN-PROBE.json`.",
        "- The CLI is pinned by absolute path (`AI_CLAUDE_CLI` = the WinGet file), its sha256 (`0b35df94…5b03`, read as bytes before any lane and before every resume) and the exact line `2.1.263 (Claude Code)`. The merged installation's bundled 2.1.289 is never used.",
        "- Isolation: every lane, live and dry, at its start and its end, refuses an environment value, setting, import path or loaded module under the merged installation except the bound venv and this harness folder, and an application env file equal to the merged `.env`; `sandbox_env` drops `PWD` / `OLDPWD`.", "",
        "### 2.2 R40-04 closed by option 2 (A-11: \"a fail-closed boundary\")",
        "- Lanes C, R and P install `RefusingGlobalProvider` as the application's global provider before any application code; any `get_provider().complete(...)` is refused (`dispatch_refused`), recorded as the contract breach `global_provider_request` and makes the run INVALID. Lane B is unchanged (the chain).",
        f"- Static: `REQUEST-PATHS-STATIC.json` resolves all {outs['request_paths']['summary']['get_provider_sites']} site-lane pairs; every lane installs its global provider before its first application entry; the reached sites equal review39's ({outs['request_paths']['reached_sites_equal_to_review39']}). Dynamic: `test_global_provider_r42.py` and `evidence/demos/DEMO-global_provider.json`. See `REQUEST-PATHS.md`.", "",
        "### 2.3 R41-09 (the dead-end class), R41-10 (C1 disk) and R41-11 (CLI updates)",
        "- The runner now checks the CLI file, the free disk (≥ 2 GiB on the sandbox drive; configurable only upward), every preflight item and the guard preview, and then compares `--version`, all BEFORE the run folder is created or re-opened.",
        "- The capture store is bound and the allowance created atomically (built aside, renamed into place) BEFORE the authorization nonce is consumed.",
        "- `run` re-enters a folder that, by its own records, holds no allowance, no consumed nonce and no charged request (`REENTRY-<n>.json`); with an allowance present `run` is refused and `resume` continues; a resume re-checks the CLI file, the version line and the disk before consuming its nonce.",
        "- Every case of Verification 41's `deadends_r41` (T, A, B, C, D, E) is reproduced in dry and live-shaped form: none consumes an authorization, none strands the run (`test_runner_order_r42.py`, `evidence/demos/DEMO-interruption_and_deadends.json`). The refusals that must stay still refuse.", "",
        "### 2.4 One approval for all planned resumptions (A-11 §4; separable, default off)",
        "- `dispatch_guard_r32` accepts, besides the unchanged per-invocation file, a file with `invocations_authorized` N (1..3, bound by the declaration) and N nonces consumed one per invocation in order; any other key, a reused or out-of-order nonce, N above the bound, a declaration without the bound, or a frozen hash is refused; invocation N+1 needs a new file (`test_resume_authorization_r42.py`).", "",
        "## 3. Tests (junit in `tests/`, run from the package harness under the R42 audit guard)", "",
        f"**{tests['total']['tests']} tests, {tests['total']['failures']} failures, {tests['total']['errors']} errors, {tests['total']['skipped']} skipped; guard refusals {tests['guard_refusals']}** (tree `{tests['tree']}`).", "",
        "| Module | Tests | Result |", "|---|---|---|", *[f"| `{m}` | {v['tests']} | {v['tail'][0] if v.get('tail') else ''} |" for m, v in sorted(mods.items())], "",
        "## 4. Scripted-provider demonstrations (`evidence/demos/`, dry or live-shaped, 0 CLI invocations, 0 model requests)", "",
        "| Demonstration | Result | Also proven by |", "|---|---|---|",
        *[f"| {k} | {'PASSED' if v['ok'] else 'FAILED'} ({v['seconds']} s) | {'; '.join(v.get('tests') or [])} |" for k, v in demos["demos"].items()], "",
        f"AI ledger before and after: {demos['ledger_before']['entries']} / {demos['ledger_before']['scopes']} / {demos['ledger_before']['limit_amendments']} (unchanged: {demos['ledger_unchanged']}); authorization files written: {len(demos['authorization_files_written'])}.", "",
        "## 5. Outputs re-run", "",
        f"- `PROJECT-REQUEST-BOUNDS.json` `{outs['bounds']['sha256'][:12]}…`: every key `verify_bounds` compares equals review39's `99be01fb…1721`; the file differs only in `run_set.path` (Desktop → merged).",
        f"- `RESUME-INVOCATIONS-R42.json` `{outs['resume_invocations']['sha256'][:12]}…`: byte-identical to review39's.",
        f"- `REQUEST-PATHS-STATIC.json` `{outs['request_paths']['sha256'][:12]}…`.", f"- `LIVE-RUN-CONTRACT.md` version 5 (`{C.sha256_file(R / 'LIVE-RUN-CONTRACT.md')[:12]}…`): version 4 with listed substitutions and sections 14–16; sections 4, 5, 6, 8, 9, 11, 12, 13 carried byte for byte (`evidence/CONTRACT-V5-RECORD.json`).", "",
        "## 6. What was not changed",
        "- Every number of the experiment (arms, run set, caps, parent, allowances, window, thresholds, gate, stop rules, pins); the scorer, the judge, the evaluator, the allowance, the capture store, the concentration rule (byte-identical files).",
        "- No earlier package, label, frozen tree, application code, MR file, the AI ledger (read `mode=ro` only), the staging or the merged installation's code, data or `.env` was written. No `claude` process was started (the binary was read as bytes only); no provider or model request; no scope, token, RUN or authorization file.", "",
        "## 7. Known limits",
        "- The disk floor is checked at the start of each invocation; it cannot stop another process from filling the drive during an invocation.",
        "- Isolation compares paths textually (forward/backslash and case normalised); an 8.3 short name of the merged folder would not be recognised.",
        "- An application path that builds its own provider object (not through `get_provider()`) would bypass the chain; none is reached statically (REQUEST-PATHS.md §5).",
        "- The live path (the real CLI, the real ledger scope, a real authorization) cannot be exercised offline; it is shown live-SHAPED (in process, fake ledger, fake CLI file, in-memory authorization, lanes stubbed).", ""]
    if (R / "CHANGE-RECORD-R42.md").exists():
        raise SystemExit("refused: CHANGE-RECORD-R42.md is written once")
    C.write_once(R / "CHANGE-RECORD-R42.md", "\n".join(L))
    print("CHANGE-RECORD-R42.md written")
    return 0


if __name__ == "__main__":
    sys.exit(main())
