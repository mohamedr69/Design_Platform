# M2 Review 10: provenance and source freeze

## The candidate

- **Commit:** `a34d3f8c0af7b6877eafd9f58cfede8a73c595a3`, in the isolated scratch repository `C:/t/iso/ep-platform`, branch `iso-baseline`, with `core.autocrlf` false. Its parent is `689d95e`, the Review 09 candidate the independent review inspected.
- **Frozen worktree:** `C:/t/iso/frozen-r10` at `a34d3f8`, clean, **no `.env`**. It was used for the full suite, the focused runs, the probes (after) and the re-score.
- **Kept as history, unchanged:**
  - `689d95e`, whose worktree `C:/t/iso/frozen-r9` is still clean with no `.env`;
  - the earlier candidates;
  - the `review08/` and `review09/` packages;
  - the evaluator .8 outputs (hashes checked before and after the re-score).
- **Freeze manifest:** [`evidence/freeze/FREEZE-R10.json`](evidence/freeze/FREEZE-R10.json). Diff against `689d95e`: [`candidate-r10.diff`](evidence/freeze/candidate-r10.diff), SHA-256 `98849c36abef9d55bac9f908fcd9766343c65c4a43dd52996b562ff03fb94ce2`.
- **Versions, frozen before final scoring:**

| Component | Version |
|---|---|
| Reader | `evidence-reader-2026-09-29.5`: selection and association only |
| Policy | `evidence-policy-2026-09-29.4`, unchanged |
| Evaluator | `m2-pilot-eval-2026-09-29.9` |
| Ledger | `ai-ledger-2026-09-29.2`, unchanged |
| Parser | `parse-2026-09-29.9`, unchanged |

## Changed files (committed bytes)

| File | Kind | Bytes | Line endings | SHA-256 |
|---|---|---|---|---|
| `backend/app/ai/evidence_reader.py` | application | 90743 | CRLF (as at `689d95e`) | `4404abfa4d1c8d54f0b1b6a6bfa498b9a0fbb5b3529d8bc3441498be805e8e27` |
| `backend/scripts/m2_eval5.py` | evaluator script | 31072 | LF | `38326f149a7f49246413427cf4a661134cc7d31734faa13fe80f8ad967a3e451` |
| `backend/tests/test_m2_review10.py` | test (new) | 15433 | LF | `dfb36277165f24551bceb645e0b26e37b27c6c79387f7df83783e8dd56580481` |

**The reader diff has three hunks:**
- the version line;
- the association helpers (`_attempt_no`, `_entry_value`, `_read_entry`, `_entry_at`, `_same`, `_revision_for`, `association_of`), which replace `_usable_value` and the old `association_of`;
- the one call site in `evidence_for`.

`_read_page`, `merge_evidence`, the source-identity checks and `validate_boq_row` are untouched.

## Test commands and temporary environment

- **Interpreter:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`, used only as an interpreter.
- **Every run:** `TEMP=TMP=C:/t/iso/tmp python -B -m pytest <modules> -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/<run> [--junitxml=...]`, from `<tree>/backend`.
- **Isolation.** `tests/conftest.py` points the database, library, cache and uploads at temporary folders and turns AI off. Every AI answer is scripted.
- **Trees:**

| Tree | Commit | Role |
|---|---|---|
| `C:/t/iso/frozen-r10` | `a34d3f8` | the candidate |
| `C:/t/iso/prior-689` | `689d95e` | a new worktree that only adds `tests/test_m2_review10.py`, for the before run |
| `C:/t/iso/frozen-r9` | `689d95e` | the reviewer's tree. It is read only by the before probes and never written. |

- **The scratch repository's main worktree** has the sandbox `.env` (`C:/t/iso/sandbox`, AI off). No reported run used it.
- **Probes** import the frozen trees through `sys.path` with `AI_ENABLED=false`. They make no model or service call and open no source document.

## What was not touched

| Item | Status |
|---|---|
| **The owner's checkout** | HEAD `2221b43`, unchanged; the original 11 Candidate C hashes still match. The only writes are this `review10/` folder and the appended response in `M2-REVIEW-RESPONSE.md`. |
| **Services, database, settings, symbol library, OneDrive originals, sealed cohort** | Not touched. The owner's own running services write their database, as in earlier rounds. |
| **Models** | None called. No corpus expansion, migration, backfill or AI adjudication. |
| **Commits** | Only on the scratch branch. None in the owner's repository, and no push. |
