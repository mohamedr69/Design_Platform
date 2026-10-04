# M2 Review 12: provenance and source freeze

## The candidate

- **Commit:** `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`, in the isolated scratch repository `C:/t/iso/ep-platform`, branch `iso-baseline`, with `core.autocrlf` false. Its parent is `a977364`, the Review 11 candidate the independent review inspected.
- **Frozen worktree:** `C:/t/iso/frozen-r12` at `3d5607d`, clean, **no `.env`**. It was used for the planned full suite, the focused runs, the probes (after) and the re-score.
- **Frozen before final validation.** The `_brief` shadowing defect found by the 188-test set was fixed *before* the freeze; the frozen commit contains the fix.
- **Kept as history, unchanged:**
  - `a977364`, whose worktree `C:/t/iso/frozen-r11` is still clean with no `.env`;
  - the earlier candidates;
  - the `review08/`–`review11/` packages;
  - the Review 11 re-score outputs (hashes checked before and after).
- **Freeze manifest:** [`evidence/freeze/FREEZE-R12.json`](evidence/freeze/FREEZE-R12.json). Diff against `a977364`: [`candidate-r12.diff`](evidence/freeze/candidate-r12.diff), SHA-256 `85f2b8188bec411ab12afd5e4520278dfc576c8dfef68e3dcb8fe835c2ac9103`.
- **Versions:**

| Component | Version |
|---|---|
| Reader | `evidence-reader-2026-09-29.7`: reconstruction only |
| Policy | `evidence-policy-2026-09-29.4`, unchanged |
| Evaluator | `m2-pilot-eval-2026-09-29.9`, unchanged |
| Ledger | `.2`, unchanged |
| Parser | `.9`, unchanged |

## Changed files (committed bytes)

| File | Kind | Bytes | SHA-256 |
|---|---|---|---|
| `backend/app/ai/evidence_reader.py` | application (CRLF, as at `a977364`) | 106038 | `22999476256a415a95f45dc865fc9858f1507e9ebebb60e74040dfcb6a70abd9` |
| `backend/tests/fixtures/evidence_reader_r11.py` | test fixture: `a977364`'s reader, byte-identical (the same hash as Review 11's reader) | 101300 | `d9002bc155631d8aadfa2d88d2bf4d49b5da2b8b646ffb1ce74d748cf3cc84bd` |
| `backend/tests/test_m2_review12.py` | test (new) | 15637 | `277682e7011d77ef90c1597d67ce3b7b2389081c3ad9dc1723308ceebcf2cf09` |

**What the reader diff touches:**
- the version line;
- the merge's stamping condition (`_needs_anchor` / `_anchor_of`);
- the removal of `.6`'s value-based `_value_at` and `_reconstruct_anchor`;
- the new order-based reconstruction (`_order_of`, `_entry_brief`, `_entry_in_effect`, `_reconstruct_anchor`, `_needs_anchor`, `_anchor_of`, with `_context_identity`, `_revision_now` and `_read_anchor` now taking `ai`);
- two call sites in `association_of`.

`_read_page`, the source-identity checks, `validate_boq_row` and `_brief(row)` (the BOQ verifier) are untouched.

## Test commands and temporary environment

- **Interpreter:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`.
- **Focused runs:** `TEMP=TMP=C:/t/iso/tmp python -B -m pytest <modules> -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/<run> --junitxml=...`, from `<tree>/backend`.
- **The planned full suite:** the exact command, tree, start and finish times are in [`evidence/suite/RUN.txt`](evidence/suite/RUN.txt). **pytest's own exit code** was written by `echo $?` immediately after pytest, to [`evidence/suite/pytest_exit_code.txt`](evidence/suite/pytest_exit_code.txt), separately from the log and the JUnit file.
- **Isolation.** `tests/conftest.py` points the database, library, cache and uploads at temporary folders and turns AI off. Every AI answer is scripted.
- **Trees:**

| Tree | Commit | Role |
|---|---|---|
| `C:/t/iso/frozen-r12` | `3d5607d` | the candidate |
| `C:/t/iso/prior-a97` | `a977364` | a new worktree that only adds the Review 12 module and its fixture, for the before run |
| `C:/t/iso/frozen-r11` | `a977364` | the reviewer's tree. It is read only by the before probes and never written. |

## What was not touched

| Item | Status |
|---|---|
| **The owner's checkout** | HEAD `2221b43`, unchanged; the original 11 Candidate C hashes still match. The only writes are this `review12/` folder and the appended response in `M2-REVIEW-RESPONSE.md`. |
| **Services, live database and rows, `.env`, symbol library, originals, sealed projects** | Not touched. There was no backfill. Live project policies are unchanged. |
| **Models** | None called. |
| **Commits** | Only on the scratch branch. None in the owner's repository, and no push. |
