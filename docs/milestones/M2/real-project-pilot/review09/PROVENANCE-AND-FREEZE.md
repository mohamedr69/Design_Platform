# M2 Review 09: provenance and source freeze

## The candidate

- **Commit:** `689d95e53cc369c2397600daf2a46a3de93d5214`, in the isolated scratch repository `C:/t/iso/ep-platform`, branch `iso-baseline`, with `core.autocrlf` false.
- **Parent chain:** `689d95e` → `ec4f0fc` → `e02a8c1`, the Review 08 candidate the independent review inspected.
  - `ec4f0fc` was the first freeze. It was superseded before any result was reported: while the .8 re-score was being explained, judgements on unscored pages turned out to still drop `target` and `association`. No score was affected. Everything reported here was run on `689d95e`.
- **Frozen worktree:** `C:/t/iso/frozen-r9` at `689d95e`, clean, **no `.env`**. It was used for the full suite, the focused runs, the reviewer's probes (after) and the re-score.
- **Kept as history, unchanged:**
  - `e02a8c1`, whose worktree `C:/t/iso/frozen-r8` is still clean with no `.env`;
  - the Review 07 commits `1455f8b` and `c9a1a14`;
  - the `review08/` package and the evaluator .7 outputs (hashes checked).
- **Freeze manifest:** [`evidence/freeze/FREEZE-R9.json`](evidence/freeze/FREEZE-R9.json). Diff against `e02a8c1`: [`candidate-r9.diff`](evidence/freeze/candidate-r9.diff), SHA-256 `3fd62de53b1dd4fa033466291bfc32f757bb29cec730f9e2e3a5035b565c8239`.
- **Versions were frozen before final scoring:**

| Component | Version |
|---|---|
| Reader | `evidence-reader-2026-09-29.4` |
| Policy | `evidence-policy-2026-09-29.4` |
| Evaluator | `m2-pilot-eval-2026-09-29.8` |
| Ledger | `ai-ledger-2026-09-29.2`, unchanged; docstring wording only |
| Parser | `parse-2026-09-29.9`, unchanged |

## Changed files (committed bytes)

| File | Kind | Bytes | Line endings | SHA-256 |
|---|---|---|---|---|
| `backend/app/ai/evidence_reader.py` | application | 86555 | CRLF (as at `e02a8c1`) | `e9d7e8755de5f931fc963c1d50b4b5dd465bdfdc9f781467c191cfcf3a288e8a` |
| `backend/app/ai/ledger.py` | application (docstring only) | 21618 | LF | `d9f92297f29ee9caa044705261ce8323c269918aa09ad5f704c865aa549b7dca` |
| `backend/scripts/m2_eval5.py` | evaluator script | 30196 | LF | `af6ab7a434be127abd7849a2420ac2bf27364d2fbcc439b6b666d4f0ae08a6de` |
| `backend/tests/test_m2_eval5.py` | test (fixture records its source hash) | 10465 | LF | `60c0d2fe6609c9dd852a52ee0bfe137fe88b54d1d9aaf2325dd2820e2ca47424` |
| `backend/tests/test_m2_review09.py` | test (new) | 28218 | LF | `8790988c869356cf76941e2c63d59f6e41643c5f34c807bd4edc860596bb4d56` |

## Test commands and temporary environment

- **Interpreter:** `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`. It is the only one available; it is used only as an interpreter.
- **Every run:** `TEMP=TMP=C:/t/iso/tmp python -B -m pytest <modules> -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/<run> [--junitxml=...]`, from `<tree>/backend`.
- **Isolation.** `tests/conftest.py` points the database, library, cache and uploads at temporary folders, and turns AI off. Every AI answer is scripted (`RecordingProvider`, and `LedgerProvider` over a disposable SQLite ledger).
- **Trees:**

| Tree | Commit | Role |
|---|---|---|
| `C:/t/iso/frozen-r9` | `689d95e` | the candidate |
| `C:/t/iso/prior-e02` | `e02a8c1` | a new worktree that only adds `tests/test_m2_review09.py`, for the before run |
| `C:/t/iso/frozen-r8` | `e02a8c1` | the reviewer's tree. It is read only by the before probe and the BOQ replay, and never written. |

- **The scratch repository's main worktree** has a sandbox `.env`: `DATABASE_URL` points at `C:/t/iso/sandbox`, and `AI_ENABLED=false`. No reported run used it.

## What was not touched

| Item | Status |
|---|---|
| **The owner's checkout** | HEAD `2221b43`, unchanged; the original 11 Candidate C hashes still match. No source, test, script, migration or library file under its `backend/` was written in this round. The only file written there since the round began is `ep_platform.db-wal`, which the owner's own running services write (uvicorn and workers, started 2026-09-28). |
| **The owner's `.env`** | Not written (last written 2026-09-27). |
| **Services, settings, data, symbol library, OneDrive originals, sealed cohort** | Not touched. No source document was opened in this round. The BOQ replay reads only the stored JSON outputs of Review 06. |
| **Models** | None called. No accuracy experiment was run. |
| **Commits** | Only on the scratch branch. None in the owner's repository, and no push. The only writes to the owner's checkout are this `review09/` folder and the response appended to `M2-REVIEW-RESPONSE.md`. |
