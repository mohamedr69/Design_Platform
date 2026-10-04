# M2 Review 08: regression evidence

Every run here is **new**, on the exact candidate, unless it is marked "submitted" (historical).

## 1. The Review 08 module fails on the prior candidate and passes on this one

`tests/test_m2_review08.py` has 27 tests, byte-identical in both runs (SHA-256 `74578fe9…`).

**On the prior candidate, 24 fail and 3 pass.** The run used a worktree at `1455f8b` (`C:/t/iso/prior-1455`) with only the module and its two pinned fixtures added. See [`evidence/prior/`](evidence/prior/review08_module_on_1455f8b.txt).

- **The module fails on behaviour, not on missing names.** Where 1455f8b has no such API, thin adapters call what its consumers actually called: `current_evidence(ai)`, `evaluate(...)` without a context, and `result.get("row_type")`.
- **Failures:**

| Test | Fails at 1455f8b because |
|---|---|
| blind identity timeout | `KeyError: 'own:decision'`: the validated decision was gone after the timeout |
| reviewer's timeout probe | the page outcome was `evidence`, not `partial` |
| budget attempt without field outcomes | `[('identity', 'X-SD-NEW')]`: a candidate replaced the validated identity and decision |
| revision timeout, decision refused by budget | "the timed-out read replaces nothing" |
| two components | "the own component failed and keeps its evidence" |
| resume | "the replaced value is kept with its own provenance" |
| completed negative vs absence vs failure | `KeyError: 'own:decision'` |
| field only from an unsuccessful read | `'completed' == 'incomplete'`: a candidate was stored as complete |
| failed profile switch, both directions | `'current' == 'pending'`: the other profile was returned as current |
| the prior accessor with no context | it returned the default profile's evidence |
| budget-stopped variant switch | `'current' == 'pending'` |
| unknown legacy profile | `'current' == 'unavailable'` |
| evaluator context | "the promoted run is scored with the default profile's evidence" |
| reviewer's ledger case | `DID NOT RAISE`: the second reservation was allowed |
| another OS process | the process with different limits succeeded |
| simultaneous workers | "one policy wins the creation; every handle that opened agrees with it" |
| input, output and time caps | `DID NOT RAISE`: a looser handle was accepted |
| amendment | `amend_limits` does not exist (no audited amendment path) |
| heading cases (×5) | `validated` for a part-only heading, a counted heading and an illegible heading; `validated`, not `not_an_item`, for a clean heading. The quantity-only heading was already `conflict` at 1455f8b; it fails there only because no row type is recorded. |

- **The 3 that pass there:**
  - `test_restart_after_reservations_a_timeout_and_settlement`: ledger .1 already recovered in-flight rows at restart. It is kept as a compatibility check.
  - `test_before_a_heading_answer_validated_a_part_only_row`: it asserts the old behaviour on the pinned fixture.
  - `test_part_and_quantity_stay_separate_for_absent_and_unreadable_quantities`: Review 07 behaviour, kept.

**On `e02a8c1`: 27 of 27 pass.**

**Stability.** The concurrency tests (simultaneous workers, another process, restart) were repeated 15 times on the candidate, with 0 failures.

## 2. The reviewer's probes

[`evidence/probes/probes_r8.py`](evidence/probes/probes_r8.py) runs the reviewer's `probes.py` scenarios with the same inputs on the pinned 1455f8b code and on the candidate. Adaptations were needed only where the candidate's API changed: the stub run keeps a call log as the real run does, and evidence is requested for a context. Output: [`probe-results-r8.json`](evidence/probes/probe-results-r8.json).

| Probe | 1455f8b | Candidate |
|---|---|---|
| `failed_profile_switch` | `promoted` requested, `default` returned as current | `pending`, no observations |
| `blind_timeout_replaces_good_page` | page `evidence`; after the merge only a discovery-only identity candidate remains | page `partial` (`own:identity: failed:timeout`, decision `absent_by_discovery`); after the merge the validated identity and decision are both kept |
| `budget_envelope_does_not_guard_page_overwrite` | `X-SD-NEW` candidate replaced the page | the validated identity and decision are kept |
| `heading_validated_without_verified_fields` | `validated` | `conflict`, `row_type: disputed` |
| `scope_reopened_with_looser_limit` | handle opened; second request would be dispatched; totals 2 requests | `LedgerConfigMismatch` on open; a handle without limits gets `requests=1` and is refused; totals 1 request |

## 3. Focused and compatibility modules on `e02a8c1`

All three runs are new, on `C:/t/iso/frozen-r8` at `e02a8c1`, with no `.env`. The JUnit files are in [`evidence/focused/`](evidence/focused/).

| Run | Modules | Result |
|---|---|---|
| **The reviewer's module set** (the same six modules as `independent-suite.xml`) | `test_m2_eval5` (13), `test_evidence_reader_r7` (36), `test_evidence_reader` (21), `test_ai_ledger` (9), `test_m2_review07_extraction` (6), `test_m2_review07_boq` (3) | **88 passed** |
| **Review 08 module** | `test_m2_review08` (27) | **27 passed** |
| **Compatibility: BOQ, extraction, AI** | `test_design_sheet_extractor` (31, 7 skipped), `test_m2_review05_boq` (11), `test_m2_review06_boq` (3), `test_boq_extraction_v2` (13), `test_boq_verification_v2` (4), `test_boq_selective_v2` (7), `test_boq_geometry_v2` (10), `test_boq_corrections_v2` (1), `test_ai_assist` (32), `test_ai_sheet_reader` (7), `test_submittal_ai` (9), `test_extraction_pilot` (5), `test_m2_review06_titleblock` (8), `test_extraction_m2_review02` (16), `test_extraction_m2_review03` (7) | **157 passed, 7 skipped** (the same design-sheet skips as Review 07) |

The reviewer's own run of those six modules on `1455f8b` (`independent-suite.xml`, 88 passed) is **submitted, historical** evidence. The run in the first row is new, on the candidate.

## 4. Hermetic full suite on `e02a8c1`

- **Tree:** `C:/t/iso/frozen-r8` at `e02a8c1`, clean, **no `.env`**. `tests/conftest.py` points the database, library, cache and uploads at temporary folders and turns AI off.
- **Command:** `python -B -m pytest tests -q -p no:cacheprovider --basetemp=<temp>` from `frozen-r8/backend`.
- **Output:** JUnit [`evidence/suite/r8__suite_full_frozen_hermetic.xml`](evidence/suite/r8__suite_full_frozen_hermetic.xml) and log `full_frozen_hermetic.log`.
- **Result:** **1,628 tests: 1,591 passed, 35 skipped, 2 failed** (19 min 7 s).

| Failure | Status |
|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (migration downgrade, FOREIGN KEY on `DROP TABLE users`) | **Pre-existing** (Review 05: pre-M1); the same failure as Review 07 |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (stale part catalogue) | **Pre-existing**; the same failure as Review 07 |

The count differs from Review 07's 1,600 in exactly two modules, per the two JUnit files:
- `test_m2_review08.py`: +27, the new module;
- `test_m2_eval5.py`: 12 → 13. The Review 07 full run was at `c9a1a14`, and the `1455f8b` amendment added that test.

The 35 skips are unchanged.

**Submitted, historical, not re-run here:** the Review 07 hermetic run on `c9a1a14` gave 1,600 tests: 1,563 passed, 35 skipped, 2 failed. Both failures were pre-existing. Section 4 accounts for the difference in test count.

## 5. Assertions changed from an earlier version

These are listed for the reviewer. All are API or data-shape migrations for R8-01/R8-02; no expected behaviour was weakened.

1. **`test_evidence_reader_r7.py`, lifecycle section.**
   - It reads through `evidence_for(...)` instead of `current_evidence(ai)`, and uses provenance per field instead of per page.
   - A failed switch now gives `pending` for the requested context. It previously returned the other context's envelope.
   - The legacy-profile test now requires the caller's declaration.
   - The synthetic attempts record field outcomes.
2. **`test_evidence_reader.py::test_stage_is_off_by_default_and_writes_only_its_own_key`.**
   - It reads `evidence_for(..., profile="default", variant="EV1")["envelope"]`.
   - The scripted answers are reordered to discovery then blind read, because only one page has a trigger. The assertions are unchanged.
3. **`test_ai_ledger.py`.**
   - It reads the stage result through `evidence_for`.
   - An attempt's page entry is now `{"outcome", "fields"}`, not a bare string.
4. **`test_m2_eval5.py`.** Its AI rows are flat Review 06 envelopes, so the module declares that legacy context (`profile: None, variant: None`) through a local `evaluate` wrapper. The expected numbers are unchanged.
