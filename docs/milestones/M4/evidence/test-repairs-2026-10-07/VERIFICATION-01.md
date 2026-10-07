# Verification 01 of the M4 test-health repairs (commit f6ab349) — ACCEPT WITH NOTES

Filed verbatim by the orchestrator, 7 October 2026. Role: ep-verifier, run as a general-purpose Claude Opus agent with the role's definition inlined (see docs/SESSION-LOG-2026-10-07-windows.md row 1a); read-only, independent of the implementer. Change: commit f6ab349 on the implementer's worktree branch, base 37ab7bb; merged into claude/upbeat-lovelace-sa9j3w after this verdict. Scope: docs/milestones/M4/evidence/diagnosis-2026-10-07/FIVE-PREEXISTING-FAILURES.md items 1–3 (the archive-model upgrade test, the migrations knock-on, the AI-assist Tesseract test). Machine: the owner's Windows PC, Tesseract installed, venv Python 3.12.10.

---

## ep-verifier report: f6ab349 (M4 test health, diagnosis items 1–3)

### 1. Verdict
**ACCEPT WITH NOTES.** Every gate clause has evidence from this machine, and no platform rule is broken. The notes in section 7 are non-blocking.

Change verified: commit f6ab3496608509d2b288ff8368c7d3f5d93c0070 on `worktree-agent-aacaf6434f797a22e`. It is the only commit on top of 37ab7bb (`git rev-list --count` = 1). The worktree was clean before and after my runs, and HEAD stayed at f6ab349.

### 2. Gate clause → evidence

| Clause | Where I looked | Result | Note |
|---|---|---|---|
| (a) The three named tests pass here | Ran them from the worktree's backend folder. | PASS | `3 passed, 4 warnings in 5.31s`. The warning paths show the worktree's `alembic/` was imported. **Baseline at 37ab7bb** (a `git archive` copy): `2 failed, 1 passed`. The archive test fails with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`. The migrations test fails with `AssertionError: assert [('remove_tab...` (the stray `_alembic_tmp_` table). The AI-assist test passes at base too, because Tesseract is installed here. |
| (b) test_migrations.py and test_ep_archive_models.py pass together, in both orders | Ran both orders with `-v -rs`. | PASS | migrations first: `7 passed, 9 warnings in 9.50s`. archive first: `7 passed, 9 warnings in 8.65s`. |
| (b) hardening: does the conftest fix work on its own? | Scratch copy with the head conftest plus the **old** archive test, archive file first. | PASS | `1 failed, 6 passed`. The old archive test still fails (FK error), but the migrations test after it passes. This confirms the implementer's hardening claim. |
| (c) test_ai_assist.py passes in full, no skips | Ran it with `-q -rs`. | PASS | `32 passed, 11 warnings in 22.99s`, and no SKIPPED lines. |
| (d) No assertion removed or weakened | `git diff 37ab7bb..f6ab349`, plus a mechanical comparison of the assert and migration-command lines with leading whitespace stripped. | PASS | The archive test's assert, downgrade and upgrade lines are identical to base apart from indentation. test_ai_assist.py has 87 `assert` occurrences before and after; its only difference is the `@requires_tesseract` line at 227. test_migrations.py is unchanged (0-line diff). |
| (d) No application code changed; diff stat shows only the three test files | `git diff --stat 37ab7bb..f6ab349` | PASS | Only `backend/tests/conftest.py` (13), `test_ai_assist.py` (1) and `test_ep_archive_models.py` (35): `3 files changed, 37 insertions(+), 12 deletions(-)`. |
| (e) Commit message in the repository's style | `git log -8 37ab7bb` compared with f6ab349 | PASS | Matches the repository's style: a short imperative subject with an "M4 test health:" prefix, a body explaining cause and effect, a diagnosis reference, and the Co-Authored-By trailer. |

### 3. Independent checks the orchestrator asked for

- **Same `@requires_tesseract` as the sibling: yes.**
  - `test_ai_assist.py:36` has `from .test_design_sheet_extractor import requires_tesseract`. That import was already there at base.
  - The sibling at :210 and the new one at :227 use that same object.
  - It is defined at `test_design_sheet_extractor.py:28` as `pytest.mark.skipif(not _tesseract_available(), ...)`, which probes `pytesseract.get_tesseract_version()`.
  - Eight tests in test_design_sheet_extractor.py already use it.
- **The conftest change cannot drop a model table or a user table.**
  - `reset_database` lists the test engine's tables and drops only names starting with `_alembic_tmp_`, quoted with `DROP TABLE IF EXISTS`.
  - No model `__tablename__` has that prefix (grep found none). The prefix is Alembic's batch-mode temporary-copy name.
  - The engine is the test database. conftest.py sets `DATABASE_URL` to a `tempfile.mkdtemp` SQLite file before `app` is imported. Its scope is the same as the existing `Base.metadata.drop_all`, so it reaches nothing that drop_all did not already reach.
  - Another test, `test_project_log_and_drawing_scan.py:437`, asserts that no `_alembic_tmp` table is left after a downgrade. It uses its own engine on `tmp_path`, so this cleanup does not affect it.
- **Nothing weakens the migrations schema test.**
  - test_migrations.py is unchanged.
  - The cleanup runs inside the `client` fixture *before* app startup runs the migrations. Any temporary table that startup's `upgrade head` itself leaves behind would still appear in `compare_metadata`.
  - Only debris from an *earlier* test is removed.
- **The foreign-key toggle is restored even when the downgrade raises: proven.** I ran a scratch probe in a copy of head:
  - It monkeypatches `alembic.command.downgrade` to record the raw DB-API connection and the pragma value, then raise `RuntimeError`, and calls the real test function.
  - It asserts the pragma was 0 during the downgrade and is 1 on the same raw connection after the exception. No pool checkout runs in between, so only the test's `finally` can have switched it back on.
  - Result: `1 passed`.
  - Control: the same probe on a copy with the `finally` restore removed gave `assert 0 == 1`, `1 failed`, so the probe does tell the two apart.
  - The pattern matches `app/migrations.py` `upgrade_to_head` (lines ~86–103) line for line, with downgrade+upgrade in place of upgrade.
  - The checkout listener in `app/database.py` also turns foreign keys back on at the next checkout, as a second safeguard.
- **Is the skip consistent with the owner's "Windows-only tests stay failing on Linux" rule? I agree it is.**
  - That decision (M4 README, "Owner decision, 7 October 2026") covers the three named tests that exercise Windows-only *behavior*.
  - This test needs Tesseract, not Windows. It runs on Linux wherever Tesseract is installed, and it skips on any OS, Windows included, where Tesseract is missing.
  - It is a capability skip, the same as its sibling and the eight design-sheet tests. Diagnosis item 3 classed this failure as ENVIRONMENT.
  - Unknown-is-never-complete still holds without Tesseract, because the extractor raises `TesseractNotFoundError` rather than reporting complete.
- **The implementer's wrapper script** (`<scratchpad>/runtests.sh`, which still exists) does only four things:
  1. `cd` into the worktree's backend folder.
  2. `export PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT=`.
  3. `exec` the venv python with `-m pytest "$@" -q -p no:cacheprovider --basetemp=<scratchpad>/pytest-temp-impl`.

  It does nothing else. The only departure from the mandated command is the basetemp folder name (`pytest-temp-impl`).

### 4. Rule checks (the six, plus secrets)
1. **No work in ordinary GET handlers:** not applicable; no application code changed.
2. **Deterministic authority over AI:** not applicable; the AI-assist assertions are unchanged.
3. **Unknown never reads as complete:** upheld. The AI-assist test still requires attention for unprocessed pages, and on machines without Tesseract the extractor raises rather than reporting complete.
4. **Approved records versioned, not overwritten:** not applicable.
5. **No parallel store:** not applicable. The conftest change cleans up test debris only.
6. **No skipped or weakened test:** no assertion was weakened (verified mechanically). One conditional capability skip was added. It is the existing shared decorator, it was the fix the diagnosis recommended, and it does not fire here, so the test ran.
7. **No secrets:** none in the diff.

The evidence folders are untouched, since the diff covers only the three test files.

### 5. Tests run
All from `G:/dev (2)/dev/ep-platform-merged/ep-platform/.claude/worktrees/agent-aacaf6434f797a22e/backend`, unless a scratch copy is named. Every run used this prefix and flags:

```
PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false DATA_ROOT= "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe" -m pytest <files> -q -p no:cacheprovider --basetemp="C:/Users/moham/AppData/Local/Temp/claude/g--dev--2--dev-ep-platform-merged/d223f746-dc1e-49c3-9577-b38529525a1e/scratchpad/verify-f6ab349/pytest-temp"
```

`-rs` was added where shown.

| Run | Files | Result |
|---|---|---|
| 1 | the three named node ids, `-rs` | `3 passed, 4 warnings in 5.31s` |
| 2 | `tests/test_migrations.py tests/test_ep_archive_models.py` (`-v -rs`) | `7 passed, 9 warnings in 9.50s` |
| 3 | `tests/test_ep_archive_models.py tests/test_migrations.py` (`-v -rs`) | `7 passed, 9 warnings in 8.65s` |
| 4 | `tests/test_ai_assist.py -rs` | `32 passed, 11 warnings in 22.99s`, no skips |
| 5 | wider set: `test_auth.py test_design_sheet_extractor.py test_project_log_and_drawing_scan.py test_ep_archive_models.py test_migrations.py test_ai_assist.py`, `-rs` | `96 passed, 7 skipped, 34 warnings in 55.76s`. All 7 skips are `Set EP_PLATFORM_LIVE_ARCHIVE_ROOT…` (live-archive opt-in), none for Tesseract. |
| 6 | `test_data_controls.py test_fa_evidence.py test_submittal_one_per_system.py` (the other suites that touch alembic) | `18 passed, 51 warnings, 34 errors` |
| 6, base copy | same files, scratch copy of 37ab7bb, same basetemp | identical: `18 passed, 51 warnings, 34 errors` |
| 6, shorter basetemp | same files, basetemp `<scratchpad>/v`, at both base and head | `52 passed` at both |

About run 6:
- The errors are `FileNotFoundError` at setup in test_fa_evidence. The cause is the Windows 260-character path limit: the mandated basetemp is about 150 characters, plus the fixture's `EP-40900 Tower\03- Drawings\IFC\Mechanical\HVAC\GROUND FLOOR VENTILATION LAYOUT.dxf`.
- The identical base result and the clean shorter-basetemp runs show this comes from the environment, not from the change.

Scratch experiments, run from `git archive` copies under `verify-f6ab349/`:

| Copy | Run | Result |
|---|---|---|
| `base/` (37ab7bb) | three named tests | `2 failed, 1 passed` |
| `hybrid/` (head plus the old archive test) | archive file then migrations file | `1 failed, 6 passed` (the migrations test passes) |
| `probe/` | FK restore after a raising downgrade | `1 passed` |
| `control/` | same probe, restore removed | `1 failed` (`assert 0 == 1`) |

### 6. Out-of-scope changes
None. Only the three test files changed, and there are no application, migration, documentation or evidence changes.

### 7. Notes (non-blocking)
- **N1, skip on Tesseract-less machines:** wherever Tesseract is absent, including the Linux container, the AI-assist test will now show as SKIPPED ("tesseract is not installed/configured in this environment") instead of FAILED. Linux evidence runs should list it under capability skips, not under "expected on Linux: Windows-only behavior".
- **N2, mandated basetemp too long on Windows:** the mandated basetemp path is long enough that test_fa_evidence.py hits the Windows path limit (34 setup errors at both base and head). Future full-suite runs on this PC should use a shorter basetemp, or record this.
- **N3, optional extra check:** neither the old nor the new archive test runs `PRAGMA foreign_key_check` after the FK-off migration. That would be an additional check, not a requirement of this gate.
- **N4, my own deviation from the write rule:** one of my comparison runs used basetemp `<scratchpad>/v`, outside `verify-f6ab349/`. I removed that folder afterwards. Everything else I wrote is under `verify-f6ab349/`: the `base/`, `head/`, `hybrid/`, `probe/` and `control/` copies, `pytest-temp/`, and `asserts-*.txt`. No checkout, process, live database or OneDrive was touched.

### 8. Owner decisions assumed
- **Tesseract skip:** the change uses the capability skip that diagnosis item 3 recommended. It is consistent with existing practice but is not a recorded owner decision. I judge it consistent with the Windows-first rule, which governs platform-behavior tests only.
- **SQLite migrations not atomic:** the conftest cleanup mitigates this in tests only. It does not decide open decision 3 (M7: make SQLite migrations atomic, or accept the pre-migration backup as the safeguard).
- **Not touched:** diagnosis items 4 and 5 (open-folder test, part catalogue) and their owner questions are outside this change.
