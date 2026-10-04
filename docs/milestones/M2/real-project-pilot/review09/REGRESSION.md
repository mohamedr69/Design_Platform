# M2 Review 09: regression evidence

Every run here is **new**, on the named tree, unless it is marked "submitted" (historical).

## 1. The failures reproduced before any code change

The first thing done, before any source change: `tests/test_m2_review09.py` was written and run on the unchanged `e02a8c1`. Output: [`evidence/prior/before_fix_on_e02a8c1.txt`](evidence/prior/before_fix_on_e02a8c1.txt).
- **Result:** 22 failed and 11 passed.
- **Two adjustments after that run:**
  - The same-identity retry was then made a pure control. It had failed only because the new `association` key was missing, and it now tolerates that absence.
  - The unscored-page metadata test was added later.

## 2. The final Review 09 module: prior candidate vs candidate

`tests/test_m2_review09.py` has 34 tests and SHA-256 `8790988c…`; the same bytes were used in both runs.

| Tree | Result |
|---|---|
| `e02a8c1` (new worktree `C:/t/iso/prior-e02`, only this module added) | **22 failed, 12 passed.** JUnit [`r9__review09_module_on_e02a8c1.xml`](evidence/prior/r9__review09_module_on_e02a8c1.xml); lines [`review09_module_on_e02a8c1.txt`](evidence/prior/review09_module_on_e02a8c1.txt). |
| `689d95e` (`frozen-r9`) | **34 passed** (focused run below) |

- **The module fails on behaviour, not on missing APIs.** Every new key is read with `.get`, and each test's behavioural assertion comes first. On `e02a8c1`:
  - 20 of the 22 fail on a value or state: a replaced identity, revision or decision; recovery credited to another identity; unknown bytes returned as `current`; a heading confirmed despite item evidence; a blind `0` treated as absent.
  - `test_target_and_association_survive_on_unscored_pages_too` fails because the metadata is dropped.
  - The ledger test fails only on the old documentation wording. The behaviour it checks already held at `e02a8c1`.
- **The 12 that pass there are the controls:**
  - a legible negative supersedes;
  - a completed conflict stays explicit;
  - timeout and budget refusal;
  - a same-identity retry;
  - a legacy fact without a target;
  - hash mismatch and exact match;
  - 6 heading cases already correct: blind-only count, string zero, part-only, blank quantity, true heading, illegible.

## 3. The reviewer's probes, before and after

The reviewer's `probes.py` was run with its logic unchanged. It executes the candidate's own function bodies through the AST, with image and call stubs. Only the paths and one stub signature changed: `ai_envelope` now takes the document key. See [`evidence/probes/`](evidence/probes/).

- **Before** (on `frozen-r8`, `e02a8c1`): the output **reproduces the reviewer's `probe-results.json` exactly** (compared after removing CR).
- **After** (on `frozen-r9`):

| Probe | `e02a8c1` | `689d95e` |
|---|---|---|
| `timeout_control` | X-SD-1 kept | X-SD-1 kept |
| `illegible_identity` | page `evidence`, `own:identity: completed`; current identity X-SD-9 `candidate` | page `partial`, `own:identity: unusable:illegible`; X-SD-1 `validated`, ANN `validated` |
| `illegible_negative_decision` | `own:decision: completed`; ANN replaced by `no_decision_marked` | `own:decision: unusable:illegible`; ANN `validated` |
| `missing_source_hash` | `current` | `unknown_source` |
| `wrong_profile_control` | `unavailable` | `unavailable` |
| heading `part_control` | `conflict` | `conflict` |
| heading `source_description_count` | `not_an_item` | `conflict` (count `( 2 )` in the reader's description) |
| heading `numeric_zero` | `not_an_item` | `conflict` |
| heading `string_zero` | `conflict` | `conflict` |
| `changed_identity_evaluator_groups` | one group: X-SD-9 and ANN, both validated, no target | `ai:1:own@X-SD-1`: ANN `held`, target X-SD-1, `held:target_changed`; `ai:1:own`: X-SD-9 |

## 4. Focused and compatibility modules on `689d95e`

All three runs are new, on `C:/t/iso/frozen-r9` at `689d95e`, with no `.env`. The JUnit files are in [`evidence/focused/`](evidence/focused/).

| Run | Modules | Result |
|---|---|---|
| **The reviewer's seven-module set** (the reviewer's `independent-suite.xml`: 115 tests) | `test_m2_eval5` (13), `test_evidence_reader_r7` (36), `test_evidence_reader` (21), `test_ai_ledger` (9), `test_m2_review07_extraction` (6), `test_m2_review07_boq` (3), `test_m2_review08` (27) | **115 passed** |
| **Review 09 module** | `test_m2_review09` (34) | **34 passed** |
| **Compatibility: BOQ, extraction, AI** | `test_design_sheet_extractor` (31, 7 skipped), `test_m2_review05_boq`, `test_m2_review06_boq`, `test_boq_extraction_v2`, `test_boq_verification_v2`, `test_boq_selective_v2`, `test_boq_geometry_v2`, `test_boq_corrections_v2`, `test_ai_assist`, `test_ai_sheet_reader`, `test_submittal_ai`, `test_extraction_pilot`, `test_m2_review06_titleblock`, `test_extraction_m2_review02`, `test_extraction_m2_review03` | **157 passed, 7 skipped** (the same skips as in Reviews 07 and 08) |

The reviewer's run of the seven modules on `e02a8c1` (115 passed) is **submitted, historical** evidence. The run in the first row is new, on the candidate.

## 5. Hermetic full suite on `689d95e`

- **Tree:** `C:/t/iso/frozen-r9`, clean, no `.env`.
- **Command:** `python -B -m pytest tests -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/r9full2`.
- **Output:** JUnit [`evidence/suite/r9__suite_full_frozen_hermetic.xml`](evidence/suite/r9__suite_full_frozen_hermetic.xml) and log `full_frozen_hermetic.log`.
- **Run once,** on the final freeze. A first start on the superseded freeze `ec4f0fc` was stopped at about 20%, and its output was deleted.
- **Result:** **1,662 tests: 1,625 passed, 35 skipped, 2 failed** (18 min 42 s).

| Failure | Status |
|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (migration downgrade, FOREIGN KEY) | **Pre-existing**; the same failure in the Review 07 and Review 08 hermetic runs |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (stale part catalogue) | **Pre-existing**; the same failure in both earlier runs |

**Compared with the Review 08 hermetic run on `e02a8c1`** (1,628 tests, 1,591 passed, 35 skipped, the same 2 failures), the JUnit files differ in exactly one module: `test_m2_review09.py`, +34. Every other module has the same test count. No failure is new, none has gone away, and nothing is masked: the skips are the same 35.

## 6. Assertions changed from an earlier version

1. **`tests/test_m2_eval5.py`.** The fixture rows (`rows()`) now record their bytes: a row `sha256`, and the same `read_sha256` in their flat AI evidence.
   - Before, these synthetic rows carried no source hash at all, and were scored as exact-file evidence only because of the R9-03 defect.
   - Every scoring assertion is unchanged: 13 of 13 pass.
2. **No other existing assertion changed.** The Review 08 module (27 tests) and the Review 07/08 reader, ledger and BOQ modules pass unchanged.
