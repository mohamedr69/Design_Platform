# M2 Review 10: regression evidence

Each result below is marked as one of:
- **reproduced**: the reviewer's own check, re-executed here with the same result;
- **new**: executed for the first time here, on the named tree;
- **submitted**: historical, not re-run.

## 1. Reproduced before any code change

| Check | Tree | Result |
|---|---|---|
| The reviewer's `association_probe.py` (output folder only changed) | `frozen-r9` (`689d95e`) | **Reproduced:** the output equals their `association-probe-results.json` exactly (compared after removing CR). Both R10-01 cases recover falsely; both controls hold. |
| The reviewer's `probes.py` from the Review 10 folder (root and output only changed) | `frozen-r9` | **Reproduced:** equals their `probe-results.json` exactly |
| `tests/test_m2_review10.py`, first version | the scratch tree at `689d95e`, before any source change | **New:** 7 failed, 5 passed ([`before_fix_on_689d95e.txt`](evidence/prior/before_fix_on_689d95e.txt)) |

## 2. The Review 10 module: `689d95e` vs `a34d3f8`

`tests/test_m2_review10.py` has 12 tests and SHA-256 `dfb36277…`; the same bytes were used in both runs.

| Tree | Result |
|---|---|
| `689d95e` (new worktree `C:/t/iso/prior-689`; only this module added) | **New: 7 failed, 5 passed.** JUnit [`r10__review10_module_on_689d95e.xml`](evidence/prior/r10__review10_module_on_689d95e.xml); lines [`review10_module_on_689d95e.txt`](evidence/prior/review10_module_on_689d95e.txt). |
| `a34d3f8` (`frozen-r10`) | **New: 12 passed** (section 4) |

**All 7 failures are behavioural, and none is a missing name.** Every new key is read with `.get`, and each test's first assertion is the evaluator's judgement.
- **Six fail because a retained fact is judged `validated` / `correct`** for the wrong component, with recovery `recovered_clean`: the Review 08 revision, the Review 07 decision, the targetless decision after a revision change, the fact read before any identity, the stage-built revision constraint, and the reviewer's synthetic revision case.
- **One fails because a candidate anchor yields `current`** where `by_target` is required.

**The 5 that pass there are the controls:** unrelated revision, same-context retry, unchanged legacy scoring, a reread establishing the association, and an explicit compatible target.

## 3. Probes on the frozen successor (new)

| Probe case | `frozen-r9` (reproduced) | `frozen-r10` (new) |
|---|---|---|
| `legacy_unchanged_control` | ANN `validated` `correct`; decision `recovered_clean` | unchanged |
| `legacy_changed_identity` | ANN `validated` `correct` (`not_recorded`); `recovered_clean` for X-SD-9 | ANN `held` `held_unassociated` (`held:context_changed`); decision `missed` |
| `recorded_target_control` | ANN `held_unassociated` (`held:target_changed`) | unchanged |
| `review08_revision_without_target` | revision 02 `validated` `correct`; `recovered_clean` for X-SD-9 | revision 02 `held` `held_unassociated` (`held:context_changed`); revision `missed` |
| `known_revision_without_identity` | ANN `validated` `correct` (`by_target`); `recovered_clean` | ANN `held` `held_correct` (`held:revision_changed`); decision `held_only`; revision 03 `recovered_clean` |

**The earlier independent probes** (`probes.py`: illegible reads, missing hash, heading and zero, explicit changed target) give **identical** results on `frozen-r9` and `frozen-r10`. The accepted R9-01, R9-03 and R9-04 behaviour is unchanged.

Files: [`evidence/probes/`](evidence/probes/).

## 4. Focused modules on `a34d3f8` (new)

All three runs are new, on `C:/t/iso/frozen-r10` at `a34d3f8`, with no `.env`. The JUnit files are in [`evidence/focused/`](evidence/focused/).

| Run | Modules | Result |
|---|---|---|
| **The reviewer's eight-module set** (149 tests before additions) | `test_m2_eval5`, `test_evidence_reader_r7`, `test_evidence_reader`, `test_ai_ledger`, `test_m2_review07_extraction`, `test_m2_review07_boq`, `test_m2_review08`, `test_m2_review09` | **149 passed** |
| **Review 10 module** | `test_m2_review10` (12) | **12 passed** |
| **Affected paths: BOQ, extraction and AI** | `test_design_sheet_extractor` (7 skipped), `test_m2_review05_boq`, `test_m2_review06_boq`, `test_boq_extraction_v2`, `test_boq_verification_v2`, `test_ai_assist`, `test_ai_sheet_reader`, `test_submittal_ai`, `test_extraction_pilot`, `test_m2_review06_titleblock` | **116 passed, 7 skipped** (the same design-sheet skips as before) |

The reviewer's run of the eight modules on `689d95e` (149 passed) is **submitted, historical** evidence. The run in the first row is new, on the candidate.

## 5. Hermetic full suite on `a34d3f8` (new, run once)

- **Tree:** `C:/t/iso/frozen-r10`, clean, no `.env`.
- **Command:** `python -B -m pytest tests -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/r10full`.
- **Output:** JUnit [`evidence/suite/r10__suite_full_frozen_hermetic.xml`](evidence/suite/r10__suite_full_frozen_hermetic.xml) and the log.
- **Result:** **1,674 tests: 1,637 passed, 35 skipped, 2 failed** (18 min 42 s).

| Failure | Status |
|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` | **Pre-existing**; the same failure in the Review 07, 08 and 09 hermetic runs |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` | **Pre-existing**; the same failure in those runs |

**Compared with the Review 09 hermetic run on `689d95e`** (1,662 tests: 1,625 passed, 35 skipped, the same 2 failures), the JUnit files differ in exactly one module: `test_m2_review10.py`, +12. Every other module has the same test count. No failure is new, none has gone away, the 35 skips are unchanged, and nothing is masked. The Review 09 full-suite result is **submitted** evidence; this run is **new**.

## 6. Assertions changed from an earlier version

**None.** No existing test was modified. The Review 08 module (27 tests), the Review 09 module (34 tests) and the other six modules pass unchanged. The only test file added is `test_m2_review10.py`.
