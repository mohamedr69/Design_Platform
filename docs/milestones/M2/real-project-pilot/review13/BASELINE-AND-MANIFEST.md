# Round 2 exploration: the reviewed baseline, and the file-level manifest (deliverable 1)

## 1. The baseline this work builds on

| | |
|---|---|
| Accepted candidate | `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`, accepted by the reviewer in Review 13 (`reviews/M2-review-13/M2-REREVIEW.md`) |
| Frozen worktree | `C:/t/iso/frozen-r12`: clean (`git status --porcelain` empty, checked again when the experiment was declared), no `.env` |
| Freeze manifest | `review12/evidence/freeze/FREEZE-R12.json`, sha256 `431af30c23b88be809ddd38fb219a4e9c46e779f0f7f942dfbe819ac0ea996ff` |
| Versions | reader `evidence-reader-2026-09-29.7`, policy `evidence-policy-2026-09-29.4`, schema `evidence-schema-1`, ledger `ai-ledger-2026-09-29.2`, parser `parse-2026-09-29.9`, design-sheet extractor `2026-09-29.2`, evaluator `m2-pilot-eval-2026-09-29.9`, BOQ evaluator `m2-boq-eval-2026-09-29.3` |
| Prompts | discover `discover-2026-09-29.1`, identity / revision / decision `read-*-2026-09-29.1`, BOQ row `read-boq-row-2026-09-29.2` |
| Source hashes | eleven application and evaluator files, hashed in the declaration (`evidence/run/EXPERIMENT-DECLARATION-SMALL.json`, `candidate.source_sha256`) |

**Nothing in the candidate was changed in this round.** Section 3 of [DEFECT-INVENTORY.md](DEFECT-INVENTORY.md) explains why.

### The full suite, recorded as it stands

The full suite was not run again in this round.

**Review 12's run on `3d5607d`:** 1,694 tests, 1,657 passed, **2 failed**, 35 skipped, pytest exit code **1** (captured). Both failures are pre-existing, with the same identity and message as in Reviews 10 and 11:

| Test | Failure |
|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` | `IntegrityError: FOREIGN KEY constraint failed` |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` | `AssertionError` on the part set |

**Review 11's `test_sync_worker.py::test_two_worker_processes_cannot_both_claim` timeout (`TimeoutExpired`, 60.8 s)** remains a failure of the submitted Review 11 run. Its cause is **unconfirmed**. It passed in Review 12's run (4.8 s) and in this round's focused run ([REGRESSION.md](REGRESSION.md)), but neither pass establishes the cause.

## 2. The frozen 34-project allocation and what this round may touch

The file is `review06/evidence/round2/ROUND2-SELECTION.json` (sha256 `5437e164…`, asserted by every script). Membership is unchanged:

| Cohort | Projects | This round |
|---|---|---|
| Regression / exposed | 14 (10 pilot + 4 Review 05 holdout) | Only EP-8430's BOQ sheet (H-06) and the packet v2 finding pages, which are already exposed |
| Exploration (new) | 10: 16830, 17428, 19144, 22510, 23091, 23323, 26208, 27421, 28745, 30549 | Inventoried, selected, staged, rendered, labelled (small batch), read by the model (small batch) |
| **Sealed validation** | 10 | **Not opened, rendered, OCR'd, labelled or sent.** Every script refuses sealed entries. |

**One slip is recorded.** While listing `ROUND2-SELECTION.json`, a print filter matched the cohort string `sealed validation (new)` incorrectly and printed the sealed projects' metadata lines. Those lines are the plan's own metadata, already published in the plan. No sealed file or content was read. From then on, sealed entries are excluded by substring match.

## 3. Reconciling the frozen file counts (a reporting defect, not a membership change)

**What the metadata walk found.** The walk (`r2_inventory.py`, extended-length `\\?\` paths) finds more files than `ROUND2-SELECTION.json` recorded. When the walk counts only files whose path is ≤ 259 characters, it equals the frozen counts exactly (`evidence/manifest/COUNT-RECONCILIATION.json`).

**The cause.** `select_round2.py` walked with `os.walk` / `os.stat` without the extended prefix, and its `except OSError: continue` skipped long paths silently. Example: EP-30549 was frozen at 67 files and 43 PDFs; it now has 2,440 and 1,631, of which 2,371 paths are over 259 characters.

**Other change.** Two files in EP-30549 (one of them a PDF) were modified after the freeze.

**The effect.** The frozen counts undercount long-path projects. Project membership and the cohort split are unaffected.

## 4. The exploration selection (frozen before any prediction)

The file is `evidence/manifest/EXPLORATION-SELECTION.json`, sha256 `4e8190d027444f03a58230357838eb1d0693ebcf9e0d14c236b3a46c1f59db4e`. A superseded draft is kept as `EXPLORATION-SELECTION.superseded-draft1.json`; its quota rule left in-full small projects at 47.

| Rule | Value |
|---|---|
| Seed | `m2-round2-exploration-2026-09-29` |
| Target | 450 distinct documents (the exploration share of the 1,200-document master target) |
| Per-project cap | 90 |
| Per-stratum cap | 45 % of a project's quota |
| Strata | The Round 1 path rules |
| Eligible documents | `.pdf`, plus Word files that the application's `is_transmittal` accepts (imported from `frozen-r12`) |
| Small projects (eligible ≤ 90) | Taken in full: 19144 (55), 22510 (36), 23091 (59), 27421 (59), 28745 (37) |
| Large projects | 40 each (16830, 17428, 23323, 26208), and 44 for 30549 |
| Replacements | Ordered, 4,674 (same project and stratum, in rank order) |
| BOQ name rule | 44 candidates |

## 5. Staging (the approved isolated workflow; originals only read)

The script is `r2_stage.py`, and its output is `evidence/manifest/EXPLORATION-MANIFEST.json`, sha256 `ee9df7b5e3e6f0035beec01643435e46f63d7f59eccfb9102d6633bf2b6f97cd`. Each original is read once (409 OneDrive placeholders hydrated), hashed, deduplicated and copied under `C:/t/r2x/stage`.

**Deduplication** is by content hash, against both this cohort and the exposed hashes (FROZEN-SAMPLE, FROZEN-BOQ-SET, HOLDOUT-SAMPLE, HOLDOUT-BOQ-SET). A duplicate is recorded and never counted. It is replaced only from the same project and stratum, in rank order.

| | |
|---|---|
| **Distinct documents staged** | **415** against the target of 450 |
| Duplicates found | 42 (1 of them duplicates an exposed EP-13777 file) |
| Unreadable | 0 |
| Open errors | 0 |
| **Shortfall** | **35**, all in small projects taken in full: 27421 shop_drawing 14, 19144 approval 8 + reply 2, 23091 scan 5 + submittal 1, 28745 submittal 3, 22510 submittal 1, 27421 submittal 1. The replacement pools were exhausted by duplicates. **Nothing was taken from another project or cohort to fill it.** |
| Per project | 16830 40 · 17428 40 · 19144 45 · 22510 35 · 23091 53 · 23323 40 · 26208 40 · 27421 44 · 28745 34 · 30549 44 |
| Per stratum | submittal 97 · other 69 · shop_drawing 58 · drawing_ifc_input 58 · scan 37 · approval_sample 25 · reply 22 · design_sheet 16 · transmittal_word 16 · calc 9 · spec_compliance 8 |
| Formats | 399 PDF, 13 `.doc`, 3 `.docx` (the Word transmittals were read by Word, read-only, from the staged copies) |
| Other facts | 125 scan-like documents; 11,216 pages; no staged path over 259 characters |
| BOQ | 39 BOQ-name candidates staged. Which of them are real BOQ tables has not yet been established. |

**The master target** is 1,200 documents and 40 BOQ sheets. Only the exposed and exploration share falls in this task. At 415 exploration documents, the exploration cohort cannot reach its share without taking from the sealed cohort, **which will not be done.** The gap is reported in [BLOCKERS-AND-NEXT-GATE.md](BLOCKERS-AND-NEXT-GATE.md).

**Renders.** `r2_render.py` made them from the staged copies only: 441 documents (415 plus the BOQ candidates), 826 pages (pages 1–4, and every page of a BOQ candidate), title-block crops for drawing-size pages, and each page's text layer.

## 6. The small matched batch (frozen before any prediction)

The file is `evidence/manifest/SMALL-BATCH.json`, sha256 `7039daa3f04935a35d9a272076be16510d4eb0a8885651f83f07af51f44d7139`, seed `m2-round2-small-batch-2026-09-29`. It holds **12 documents, one or two per exploration project across the strata**, plus the exposed EP-8430 BOQ sheet (H-06).

The run stage is `C:/t/r2x/small-stage`: byte copies from the stage, each hash-checked (`SMALL-STAGE.json`).
