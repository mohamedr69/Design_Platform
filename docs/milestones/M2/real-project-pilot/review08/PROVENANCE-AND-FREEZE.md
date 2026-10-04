# M2 Review 08: provenance and source freeze

## The candidate

- **Commit:** `e02a8c1b9ef093534df4bd427c7f2c5e7fc1403c` ("review08-candidate").
- **Where:** the isolated scratch repository `C:/t/iso/ep-platform`, branch `iso-baseline`, with `core.autocrlf` false, so the committed bytes are the tested bytes.
- **Parent:** `1455f8b` (the Review 07 evaluator .6 amendment), whose parent is `c9a1a14` (the Review 07 frozen application). Both stay in history unchanged.
  - The Review 07 frozen worktree `C:/t/iso/frozen-r7` still points at `c9a1a14`.
  - The `review07/` package is not edited.
- **Frozen worktree:** `C:/t/iso/frozen-r8` at `e02a8c1`. It is clean and has **no `.env`**. The hermetic suite and the focused runs used it.
- **Manifest:** [`evidence/freeze/FREEZE-R8.json`](evidence/freeze/FREEZE-R8.json). Diff against `1455f8b`: [`evidence/freeze/candidate-r8.diff`](evidence/freeze/candidate-r8.diff), SHA-256 `e9819c77c254b943726557af10ebd4b3655f5606a718208e3133b2fdda6c9c4e`.

## Changed files (committed bytes)

| File | Kind | Bytes | SHA-256 |
|---|---|---|---|
| `backend/app/ai/evidence_reader.py` | application | 76577 | `7d534b8ff07ab3c724e9d3e597b39f482feb0ac5fc17fb4ec2d700e3ade5f050` |
| `backend/app/ai/ledger.py` | application | 21324 | `a474e9ab1c581931d60c449a8314928144be48fd006b827575c7ced73ae0eb2b` |
| `backend/scripts/m2_eval5.py` | evaluator script | 27467 | `649fb83254e982705cb09ebedede1e362a48d33a0654ed75b960fe5e681a3797` |
| `backend/tests/fixtures/evidence_reader_r7.py` | test (pinned prior) | 63139 | `771c41884c0eb88d09229e5128d1d0d5ee7a06b2712081493c124f164c59133c` |
| `backend/tests/fixtures/ledger_r7.py` | test (pinned prior) | 15791 | `b413c40a919eb4ab2cc254dcd625310590def8899bbc0b866476129b57b0212f` |
| `backend/tests/test_ai_ledger.py` | test | 8859 | `5d7fbef65531ca2e603ba8fdb57c711001507acafb039687f64d28077ee214e7` |
| `backend/tests/test_evidence_reader.py` | test | 18995 | `af4332feb76a44047a222ab75d71474c619c5e7acb0ca65f28be0b96973ee9cc` |
| `backend/tests/test_evidence_reader_r7.py` | test | 19208 | `476429d75549bdf90916957c6204801fca65a37da681c3c0bb6ec2242491ff74` |
| `backend/tests/test_m2_eval5.py` | test | 10301 | `4bd49682f03110eb6032e8a24a1926f329e516270e244c4b6506094ed9aea6c8` |
| `backend/tests/test_m2_review08.py` | test | 28625 | `74578fe96eedf0c4f2c0b54f9590ef5c7e3ef9445608b9fc95cbc9781dc6a1d4` |

- **Pinned fixtures.** The two files under `tests/fixtures/` are byte-identical to `1455f8b:backend/app/ai/evidence_reader.py` and `1455f8b:backend/app/ai/ledger.py`, as the freeze script checks. They exist only so that the "before" behaviour runs in the same test module.
- **Application change.** Confined to `evidence_reader.py` and `ledger.py`: 352 insertions and 82 deletions against `1455f8b`.
- **Unchanged:** the parser (`parse-2026-09-29.9`), extraction profiles, register, request cache, and submittal and transmittal code.
- **Line endings.** Every changed file keeps the line endings it has at `1455f8b`: CRLF for `evidence_reader.py`, `test_evidence_reader.py` and `test_ai_ledger.py`, LF otherwise. The diff shows only real changes.

## What was not touched

| Item | Status |
|---|---|
| **The owner's checkout** (`C:/Users/moham/Desktop/dev/dev/ep-platform`) | HEAD `2221b43`, unchanged. Its application files for this candidate do not exist there (`evidence_reader.py`, `ledger.py` and `m2_eval5.py` are candidate-only). No source file under its `backend/` was written in this round. The only files written since the round began are `ep_platform.db` and its `-wal`, and the owner's own running services write those: `uvicorn` on port 8000 and the document, sync and IFC workers, all started 2026-09-28 09:10. |
| **The owner's `.env`** | Not read for configuration and not written (last written 2026-09-27). |
| **The scratch `.env`** | Points at `C:/t/iso/sandbox/db/iso.db`, with AI off. The tests ignore it: `tests/conftest.py` sets temporary databases. |
| **Live services, settings and data; original source documents; sealed projects** | Not touched. The sealed cohort was not inspected. |
| **Models** | No model call was made in this round. Every AI answer in the tests comes from a scripted provider. The metrics re-score outputs stored by earlier rounds. |
| **Commits** | None in the owner's repository, and no push. The only writes to the owner's checkout are this documentation folder and the appended response in `M2-REVIEW-RESPONSE.md`. |

## Review 07 history kept

These stay exactly as they were:
- the Review 07 application freeze (`c9a1a14`);
- the evaluator .6 amendment (`1455f8b`);
- their package (`review07/`: report, adjudications, packet v1, evidence and freeze manifest);
- their stored outputs (`C:/t/iso/work/r7/eval5`, `C:/t/iso/work/r7/matched`).

Evaluator .7 wrote its re-scores to a new folder. The hashes of the .6 outputs were checked before and after, and are unchanged.
