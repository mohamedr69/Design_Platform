# M2 Review 11: provenance and source freeze

## The candidate

- **Commit:** `a9773642c099b0924099bd8a86a72d4507137429`, in the isolated scratch repository `C:/t/iso/ep-platform`, branch `iso-baseline`, with `core.autocrlf` false. Its parent is `a34d3f8`, the Review 10 candidate the independent review inspected.
- **Frozen worktree:** `C:/t/iso/frozen-r11` at `a977364`, clean, **no `.env`**. It was used for the full suite, the focused runs, the probes (after) and the re-score.
- **Kept as history, unchanged:**
  - `a34d3f8`, whose worktree `C:/t/iso/frozen-r10` is still clean with no `.env`;
  - the earlier candidates;
  - the `review08/`, `review09/` and `review10/` packages;
  - the Review 10 re-score outputs (hashes checked before and after).
- **Freeze manifest:** [`evidence/freeze/FREEZE-R11.json`](evidence/freeze/FREEZE-R11.json). Diff against `a34d3f8`: [`candidate-r11.diff`](evidence/freeze/candidate-r11.diff), SHA-256 `bfb29ca9aab88f332a241a2b065fb3d40b6ce0c63c1adbcbb18085269bc5e7f4`.
- **Versions:**

| Component | Version |
|---|---|
| Reader | `evidence-reader-2026-09-29.6`: association context and attempt order |
| Policy | `evidence-policy-2026-09-29.4`, unchanged |
| Evaluator | `m2-pilot-eval-2026-09-29.9`, unchanged (no evaluator code changed) |
| Ledger | `.2`, unchanged |
| Parser | `.9`, unchanged |

## Changed files (committed bytes)

| File | Kind | Bytes | SHA-256 |
|---|---|---|---|
| `backend/app/ai/evidence_reader.py` | application (CRLF, as at `a34d3f8`) | 101300 | `d9002bc155631d8aadfa2d88d2bf4d49b5da2b8b646ffb1ce74d748cf3cc84bd` |
| `backend/tests/fixtures/evidence_reader_r10.py` | test fixture: `a34d3f8`'s reader, byte-identical | 90743 | `4404abfa4d1c8d54f0b1b6a6bfa498b9a0fbb5b3529d8bc3441498be805e8e27` |
| `backend/tests/test_m2_review11.py` | test (new) | 11764 | `9190999a493e3d46c5f50cd0a4967e5bfd50a6afdf4a1d57582e03281f1c3931` |

**What the reader changes touch:**
- the version line;
- `_normalise_ai`, which keeps `attempt_seq`;
- `merge_evidence`, for the sequence, `provenance.seq`, `summary.seq`, and anchor stamping before pruning and on what the attempt writes;
- the association helpers and `association_of`, which read the durable anchor;
- `evidence_for`, which passes each fact's entry;
- the attempt numbering in `evidence_stage`.

`_read_page`, the source-identity checks, `validate_boq_row` and the validation policy are untouched.

## Test commands and temporary environment

- **Interpreter:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`.
- **Every run:** `TEMP=TMP=C:/t/iso/tmp python -B -m pytest <modules> -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/<run> [--junitxml=...]`, from `<tree>/backend`.
- **Isolation.** `tests/conftest.py` points the database, library, cache and uploads at temporary folders and turns AI off. Every AI answer is scripted.
- **Trees:**

| Tree | Commit | Role |
|---|---|---|
| `C:/t/iso/frozen-r11` | `a977364` | the candidate |
| `C:/t/iso/prior-a34` | `a34d3f8` | a new worktree that only adds `tests/test_m2_review11.py` and the pinned fixture, for the before run |
| `C:/t/iso/frozen-r10` | `a34d3f8` | the reviewer's tree. It is read only by the before probes and never written. |

- **The scratch repository's main worktree** has the sandbox `.env` (`C:/t/iso/sandbox`, AI off). No reported run used it.

## What was not touched

| Item | Status |
|---|---|
| **The owner's checkout** | HEAD `2221b43`, unchanged; the original 11 Candidate C hashes still match. The only writes are this `review11/` folder and the appended response in `M2-REVIEW-RESPONSE.md`. |
| **Services, database and live rows, settings, libraries, originals, sealed cohort** | Not touched. There was no migration or backfill of live rows. The owner's running services write their own database, as before. |
| **Models** | None called. No corpus expansion and no AI adjudication. |
| **Commits** | Only on the scratch branch. None in the owner's repository, and no push. |
