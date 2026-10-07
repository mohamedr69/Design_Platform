# Verification 02 of the M4 test-health repair of commit d47fa70 (persistence test .env isolation) — ACCEPT WITH NOTES

Filed verbatim by the orchestrator, 7 October 2026. Role: ep-verifier, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a); read-only, independent of the implementer. Change: commit d47fa70 on the implementer's worktree branch, base f5c15f2; merged into claude/upbeat-lovelace-sa9j3w after this verdict. Defect: docs/milestones/M4/evidence/tests-2026-10-07-windows/TEST-RESULTS.md failure 6 (`test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches` read the developer's `backend/.env`). Machine: the owner's Windows PC.

---

## 1. Verdict: ACCEPT WITH NOTES

Commit d47fa70 on `worktree-agent-a7c510725a82aafe3` (worktree `G:/dev (2)/dev/ep-platform-merged/ep-platform/.claude/worktrees/agent-a7c510725a82aafe3`, parent f5c15f2, one commit in the range) meets all four gate clauses for M4 test-suite health, failure 6. I reproduced the original defect with a one-line scratch `.env`, and the fix removes it. No platform rule is broken. The notes are non-blocking and listed under the table.

## 2. Gate clauses and evidence

| Clause | Where I looked | Result | Note |
|---|---|---|---|
| (a) The test passes with a `.env` present in the backend folder it runs from, and also without one | Test run from the worktree's `backend/`, with and without a scratch `backend/.env` containing only `DATA_ROOT=C:/Users/moham/AppData/Local/Temp/ep-pt-v2/fake-data-root` | PASS | Without `.env`: 1 passed. With `.env`: 1 passed. Control: the f5c15f2 test function, copied verbatim into scratch and run against the worktree's code, gives 1 passed without the `.env` and 1 failed with it. The failure is `AssertionError: assert ('C:/Users/moham/AppData/Local/Temp/ep-pt-v2/fake-data-root' is None)`, the same mechanism as TEST-RESULTS.md failure 6 (line 272 onward), so the reproduction is real. |
| (b) `tests/test_persistence.py` passes in full | Full-file run, with and without the scratch `.env` | PASS | 3 passed both times. |
| (c) Assertions unchanged; only that file in `git diff --stat f5c15f2..d47fa70` | `git diff --stat` / `--name-only`; mechanical comparison of the `assert` lines | PASS | Diff stat: `backend/tests/test_persistence.py \| 7 ++++---`, the only file. I extracted every `assert` line from the file at both commits with whitespace stripped: 17 vs 17 lines, `diff` reports them identical. The changed lines are exactly the three `Settings(...)` calls (each gains `, _env_file=None`) plus one comment line. |
| (d) Commit message in the repository's style | `git log -1 d47fa70`, compared with the previous 10 subjects | PASS | Subject `M4 test health: keep the developer's .env out of the data-root settings test` follows the prefix of `M4 test health: migrate with foreign keys off in the archive upgrade test`. The body explains cause and fix, says the assertions are unchanged, and ends with the Co-Authored-By line. |

Supporting checks:
- **`_env_file=None` keeps real environment variables in force** (scratch script `env_check.py`, run against the worktree's `app/core/config.py` with the scratch `.env` present):
  - default constructor, no env var: data_root = fake-data-root (the `.env` is read)
  - `_env_file=None`, no env var: None
  - `_env_file=None` with `DATA_ROOT` set in the environment: data_root and database_url follow the env var
  - `_env_file=None` with `BACKUPS_ROOT` set in the environment: honoured

  So `_env_file=None` removes only the dotenv source. The existing `monkeypatch.delenv` loop is still what isolates the test from the suite's environment variables.
- **Version support:** the venv has pydantic-settings 2.7.1 and pydantic 2.10.4, which matches `requirements.txt`. `_env_file=None` is the existing pattern in `tests/test_config_paths.py:10,21,30`.

Notes (non-blocking):
1. As instructed, I tested (a) with a one-line scratch `.env`, not the real one. I did not reproduce the implementer's run with a copy of the real `.env`. This does not weaken the conclusion: with `_env_file=None`, the content of any `.env` cannot reach the three `Settings` objects the assertions inspect.
2. The new comment ("nor may it read this PC's backend/.env…") is accurate. The module-level `get_settings()` in the same file still reads `.env`, but none of this test's assertions use it.

## 3. Rule checks
1. **No work in ordinary GET handlers:** not applicable. No application code changed.
2. **Deterministic authority over AI:** not applicable. The runs used `AI_ENABLED=false`.
3. **Unknown never reads as complete:** not applicable.
4. **Approved records versioned, not overwritten:** not applicable.
5. **No parallel store:** not applicable. No store or config code was touched.
6. **No skipped or weakened test:** pass. No skip or xfail was added and the assertions are byte-identical (whitespace aside). Isolating the test from the dotenv source is the correct fix, because the test checks the code's defaults, which is what its own comment says.
7. **No secrets:** pass. The diff adds no secrets. I did not copy or read the real `.env`.

## 4. Tests run

I used scratch wrappers under `C:/Users/moham/AppData/Local/Temp/claude/g--dev--2--dev-ep-platform-merged/d223f746-dc1e-49c3-9577-b38529525a1e/scratchpad/verify-d47fa70/`. They were a convenience, not a response to a guard refusal.
- **`run.sh`:** runs from the worktree's `backend/` as `PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe" -m pytest <args> -q -p no:cacheprovider --basetemp=C:/Users/moham/AppData/Local/Temp/ep-pt-v2`.
- **`run_ctrl.sh`:** the same, but run from the scratch folder with `PYTHONPATH=<worktree>/backend` and `--rootdir=.`. Running the control file in place from the G: drive made pytest's collection scan `C:\` and fail with `PermissionError: 'C:\\Documents and Settings'`, so I moved the run into the scratch folder.

Results:
- No `.env`, `tests/test_persistence.py::test_a_data_root_gathers_the_database_uploads_backups_and_caches`: `1 passed, 1 warning in 0.14s`
- No `.env`, `tests/test_persistence.py`: `3 passed, 3 warnings in 3.57s`
- No `.env`, control (original f5c15f2 function): `1 passed in 0.31s`
- Scratch `.env`, the single test: `1 passed, 1 warning in 0.16s`
- Scratch `.env`, `tests/test_persistence.py`: `3 passed, 3 warnings in 3.49s`
- Scratch `.env`, control: `1 failed in 0.38s` (assertion quoted in the table above)
- Scratch `.env`, `env_check.py`: the four results listed in section 2

**Clean-up:** the scratch `.env` was created and removed by `envfile.py`, which refuses to overwrite an existing `.env` and checks the content before deleting. In the worktree, `git status --short --ignored backend` was empty before and after, and `git status --short` was empty after. No `fake-data-root` folder was created. I touched no process, the main clone, `data/` or OneDrive.

## 5. Out-of-scope changes
None. Only `backend/tests/test_persistence.py` changed, and no evidence folder was touched: `git diff --name-only f5c15f2..d47fa70 | grep -c evidence` = 0.

## 6. Owner decisions assumed
None.

## The two `test_provider_honesty.py` calls (lines 71 and 73)
They do not need the same treatment for correctness:
- Init arguments take precedence over the `.env` in pydantic-settings, and the asserted field `ai_claude_cli` is derived only from itself (`_expand_cli`, `config.py:276-279`).
- A `.env` value for another field changes other attributes but not the asserted one.
- A malformed `.env` would break the module-level `get_settings()` and the whole suite as well, so it is not a risk specific to these two calls.

Adding `_env_file=None` there would be optional consistency hardening, the pattern of `test_config_paths.py`, not a defect fix. I would not block on it or widen this change to include it.
