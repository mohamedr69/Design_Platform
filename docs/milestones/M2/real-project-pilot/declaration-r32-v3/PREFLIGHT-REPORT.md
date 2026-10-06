# Preflight report: declaration v3 (ORCH-10; dry, offline; no request, no `claude` process)

- **Declaration:** `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`; **binding:** `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c`; **harness:** `G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review42/scripts/harness-r32`.
- **Results file:** `dry-run/PREFLIGHT-RESULTS.json` (`0557d674ce522a68f7b728417e8c32029e81f338f917fd17f09f1a53b44f913b`), ok **True**.

## 1. Contract 5

- As written: **REFUSED** (refused: the declaration binds no owner token digest).
- In memory with a dummy digest (never written): **PASSED**.
- Negative probes: **73/73 as expected** (48 carried from v2 and adjusted to contract 5, 25 new for the CLI pin, the interpreter, the disk floor, the isolation, the resume authorization and the global provider). As in v2 the contract still accepts '12.0' / '120.0' (R39-18; the RUN-file equality keeps them out); it accepts an interpreter sha256 of another file and the bundled CLI path, which the runtime checks (`verify_interpreter`, `verify_cli`) refuse.

## 2. Binding, bounds, lanes, interpreter, CLI file, disk

- `verify_binding`: **PASSED**, 319 files (extended-length opens).
- Bounds recomputed and equal: **PASSED**; population gate DISPATCH_ELIGIBLE; 24 documents.
- Lane environments offline (live environment): B True, C True, P True, R True -- switches, provider values, `application_env`, drawings-AI review off, **isolation**, **interpreter** (`dry-run/lane-env/`).
- Interpreter True; CLI file `0b35df94c130…` (218746016 bytes, read only, never executed); free disk 16352399360 bytes ≥ 2147483648.
- Interpreter against the trees (`evidence/INTERPRETER-CHECK.json`): requirement differences {'baseline': 0, 'candidate': 0}; lane modules import {'baseline': True, 'candidate': True}; other app modules failing {'baseline': 0, 'candidate': 0}; differences from the recorded merged-venv freeze: {"pip": {"installed": "25.0.1", "record": null}}.

## 3. Refusals before any folder

- The runner as the owner would type it, without a RUN file or token: **REFUSED**.
- In process with the in-memory RUN copy: **REFUSED** at the ledger scope.
- With the scope pretended: **REFUSED** by the guard ("no owner dispatch authorization"), before the run folder and **before `--version`** (version runner calls: 0).
- The guard alone: **REFUSED**; the scope command: **PASSED** (preview created nothing; create refused).
- Invariants: {"ai_ledger_483_17_0_before_and_after": true, "dummy_digest_never_written": true, "harness_unchanged_no_pycache": true, "model_requests": 0, "no_authorization_run_or_token_file": true, "no_token_in_the_environment": true, "package_unchanged_by_the_preflight_outside_its_outputs": true, "run_folder_never_created": true, "version_runner_never_called": true}.

## 4. Path lengths (`evidence/PATHLEN-PROBE.json`)

LongPathsEnabled 0; bound paths max 151; package paths max {'declaration-r32-v2': 172, 'declaration-r32-v3': 134, 'review39': 141, 'review42': 145}; live staged PDFs max 256 (255 for inv-1..9); run-folder records max 58; owner records max 147. every bound path, package path and live run-folder record stays below 260 characters; every harness hash and binding check opens files through the extended-length prefix anyway; the staged PDFs reach 256 characters at most (inv-1..12) and are opened by the application's own extended-length helper.

## 5. The dry exercise (`dry-run/DRY-EXERCISE.json`, ok True)

- **Single run** over all 24 documents: FINISHED (R41-13: the run v2 could not make).
- **Six per-project runs:** EP-15744 FINISHED, EP-22349 FINISHED, EP-26687 FINISHED, EP-27331 FINISHED, EP-29255 FINISHED, EP-3563 FINISHED.
- **EP-27331 deferral loops under `full`:** {'deferral-loop-planning-shape-window-10': 2, 'deferral-loop-structural-shape-window-6': 3} invocations; every early resume refused and nothing created.
- **Cross-project drill** (24 documents, window 10 per 20 s): 2 invocations, 1 early resume(s) refused, final FINISHED.
- **The CLI-version case:** a version refusal at invocation 1 created nothing and the same `run` then finished (True).
- Model requests 0; AI ledger 483 / 17 / 0 throughout (True); the live run folder absent (True).
