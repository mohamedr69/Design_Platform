# M2 Review 12: regression evidence

Each result below is marked as one of:
- **reproduced**: the reviewer's own check, re-executed here with the same result;
- **new**: executed for the first time here, on the named tree;
- **submitted**: historical, not re-run.

**Synthetic and real.**
- **Synthetic:** every test and probe here is synthetic or scripted. The providers are scripted, the evidence dictionaries are synthetic, and no model is called and no project document is opened.
- **Real:** only the re-score uses real-model outputs, and those were stored by Reviews 06 and 07.

## 1. Reproduced before any code change (`frozen-r11`, `a977364`)

| Check | Result |
|---|---|
| `legacy_anchor_probe.py` | **Reproduced** exactly: R12-01A recovers ANN for revision 03 (anchor `revision: null, revision_known: true`); the different-literal control holds; R12-01B recovers the revision |
| `retention_probe.py`, `association_probe.py`, `probes.py` | **Reproduced** exactly |
| `tests/test_m2_review12.py` on the scratch tree at `a977364`, before any source change | **New:** 6 failed, 5 passed ([`before_fix_on_a977364.txt`](evidence/prior/before_fix_on_a977364.txt)) |

## 2. The Review 12 module: `a977364` vs `3d5607d`

`tests/test_m2_review12.py` has 11 tests and SHA-256 `277682e7…`. The same bytes were used in both runs, with the pinned fixture.

| Tree | Result |
|---|---|
| `a977364` (new worktree `C:/t/iso/prior-a97`) | **New: 6 failed, 5 passed; pytest exit code 1.** JUnit [`r12__review12_module_on_a977364.xml`](evidence/prior/r12__review12_module_on_a977364.xml); lines [`review12_module_on_a977364.txt`](evidence/prior/review12_module_on_a977364.txt). |
| `3d5607d` (`frozen-r12`) | **New: 11 passed; exit code 0** (section 4) |

**All 6 failures are behavioural.** Each asserts first the evaluator's judgement or the accessor's association:
- ANN `validated`/`correct` when it was read with revision 02;
- the unrelated-literal case: `current` against `held:revision_changed`;
- shuffled history: `current` / `recovered_clean`;
- a context entry without order: revision recovered;
- an erroneous `.6` anchor: recovered;
- an erroneous `.6` anchor whose history is gone: recovered.

**The 5 that pass there:**
- explicit target and same-context controls;
- duplicate context order: `a977364` held it too. It is a control, not a demonstration;
- flat `legacy` / numbered history / known absence controls. The `revision_status` check tolerates that key's absence there;
- a pruned revision context: `a977364` also treated a full history as indeterminate;
- read-time anchors never rewritten.

## 3. Probes on the frozen successor (`frozen-r12`, new)

| Probe | Result |
|---|---|
| `legacy_anchor_probe.py`: `same_revision_literal_different_targets` | ANN `held` / `held_correct`, decision `held_only`; anchor rev `02`, `revision_status: found` |
| `legacy_anchor_probe.py`: `different_literal_control` | **identical** to the case above |
| `legacy_anchor_probe.py`: `missing_identity_order` | revision `held_unassociated`; decision `missed` |
| `retention_probe.py` | identical to `frozen-r11`: pruning held through read 7, collision held through read 20 |
| `association_probe.py` | identical to `frozen-r11` |
| `probes.py` (R9) | identical to `frozen-r11` |

## 4. Focused modules on `3d5607d` (new)

All three runs are new, on `C:/t/iso/frozen-r12` at `3d5607d`, with no `.env`. They were run one after another, **after** the full suite had finished. The JUnit files are in [`evidence/focused/`](evidence/focused/).

| Run | Modules | Result |
|---|---|---|
| **The reviewer's 188-test set** (its `independent-suite.xml` modules) | `test_m2_review11` (9), `test_m2_review10` (12), `test_m2_review09` (34), `test_m2_review08` (27), `test_m2_eval5` (13), `test_evidence_reader_r7` (36), `test_evidence_reader` (21), `test_ai_ledger` (9), `test_m2_review07_extraction` (6), `test_m2_review07_boq` (3), `test_sync_worker` (18) | **188 passed, exit code 0** |
| **Review 12 module** | `test_m2_review12` (11) | **11 passed, exit code 0** |
| **Changed persistence path and compatibility** | `test_document_processing_v2` (11), `test_design_sheet_extractor` (31, 7 skipped), `test_m2_review05_boq` (11), `test_m2_review06_boq` (3), `test_boq_extraction_v2` (13), `test_boq_verification_v2` (4), `test_ai_assist` (32), `test_ai_sheet_reader` (7), `test_submittal_ai` (9), `test_extraction_pilot` (5), `test_m2_review06_titleblock` (8) | **127 passed, 7 skipped, exit code 0** |

**Before the freeze,** the same 188-test set plus the new module was run on the working tree (not the frozen candidate). It first found 2 BOQ-verifier failures caused by the `_brief` shadowing (DISPOSITIONS.md), then passed 199/199 after the rename. Those pre-freeze runs are development checks. The reported results are the three runs above, on the frozen candidate.

The reviewer's run of the 188-test set on `a977364` (188 passed, exit 0) is **submitted, historical** evidence.

## 5. Planned full suite on `3d5607d` (new, run once)

**The run.**
- **Candidate:** `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`, tree `C:/t/iso/frozen-r12/backend` (clean, no `.env`).
- **Command:** `TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp python -B -m pytest tests -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/r12full --junitxml=…`. pytest's own exit code was written by `echo $?` immediately afterwards.
- **Timing:** started 2026-09-29 20:48:50 +04:00, finished 21:11:27 (22 min 25 s). Nothing else was run alongside it.
- **Evidence:** [`RUN.txt`](evidence/suite/RUN.txt), [`pytest_exit_code.txt`](evidence/suite/pytest_exit_code.txt), [`full_frozen_hermetic.log`](evidence/suite/full_frozen_hermetic.log) and [`r12__suite_full_frozen_hermetic.xml`](evidence/suite/r12__suite_full_frozen_hermetic.xml).

**The result:**

| | |
|---|---|
| pytest exit code | **1** (captured) |
| tests | 1,694 |
| passed | **1,657** |
| failed | **2** |
| skipped | **35** |
| errors | **0** |
| collection errors | none: no `ERROR` or `INTERNALERROR` lines in the log |

**Every failure, compared by test identity and message** with the Review 11 (`a977364`) and Review 10 (`a34d3f8`) runs ([`suite_analysis/comparison.json`](evidence/suite_analysis/comparison.json)):

| Test | Review 10 | Review 11 | Review 12 |
|---|---|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` | failed: `IntegrityError: FOREIGN KEY constraint failed` | same | **same identity and message**: pre-existing |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` | failed: `AssertionError: assert {'3-SDDC2', …} <= {…}` | same | **same identity and message**: pre-existing |
| `test_sync_worker.py::test_two_worker_processes_cannot_both_claim` | passed (4.6 s) | **failed: `TimeoutExpired`** (60.8 s) | **passed (4.8 s)** |

**Counts.** 1,694 against 1,683. The only module difference is `test_m2_review12` (+11), and the 35 skips are identical.

**The Review 11 timeout.** It stays a failure of the submitted Review 11 run, its cause **unconfirmed**. This run passing does not establish that cause and does not retroactively turn that run into a pass.

## 6. The preceding run (Review 11, historical)

**The submitted Review 11 run on `a977364`** is **submitted** evidence and stays in its package:
- **The result:** 1,683 tests, 1,645 passed, 3 failed, 35 skipped, 0 errors.
- **The failures:** two pre-existing (the same identity and message as Review 10), and one new: `test_sync_worker.py::test_two_worker_processes_cannot_both_claim`, `subprocess.TimeoutExpired`.
- **The exit code:** pytest's own exit code for that run was **not captured**, and none is inferred here.

**The corrected statement about that timeout:**
- **Not reproduced in focused checks,** and **its root cause is unconfirmed.** The isolated re-runs and the observed slowdown are supporting evidence only; they do not prove it cannot be a regression.
- **The submitted full suite did not pass;** it had 3 failures.
- **It stays in history** whatever this run shows.

## 6b. The pinned fixtures

Kept intact:
- `tests/fixtures/evidence_reader_r10.py` (`a34d3f8`) and the earlier fixtures, unchanged;
- `tests/fixtures/evidence_reader_r11.py`, added and byte-identical to `a977364`.

## 7. Assertions changed from an earlier version

**None.** No existing test was modified. The only files added are `test_m2_review12.py` and the pinned fixture `evidence_reader_r11.py`.
