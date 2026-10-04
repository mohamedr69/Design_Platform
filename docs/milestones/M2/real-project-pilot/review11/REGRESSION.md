# M2 Review 11: regression evidence

Each result below is marked as one of:
- **reproduced**: the reviewer's own check, re-executed here with the same result;
- **new**: executed for the first time here, on the named tree;
- **submitted**: historical, not re-run.

**Synthetic and real.**
- **Synthetic:** every test and probe in this package is synthetic or scripted. The providers are `RecordingProvider` or `LedgerProvider` answers, or synthetic evidence dictionaries; no model is called and no project document is opened.
- **Real:** only the re-score (§5) uses real-model outputs, and those were stored by earlier rounds (Reviews 06 and 07). No model was called in this round.

## 1. Reproduced before any code change (`frozen-r10`, `a34d3f8`)

| Check | Result |
|---|---|
| `retention_probe.py` | **Reproduced** exactly: pruning accepts ANN at read 6; the collision recovers at read 15 |
| `association_probe.py` | **Reproduced** exactly |
| `probes.py` (earlier R9 probes) | **Reproduced** exactly |
| `tests/test_m2_review11.py` on the scratch tree at `a34d3f8`, before any source change | **New:** 5 failed, 4 passed ([`before_fix_on_a34d3f8.txt`](evidence/prior/before_fix_on_a34d3f8.txt)) |

## 2. The Review 11 module: `a34d3f8` vs `a977364`

`tests/test_m2_review11.py` has 9 tests and SHA-256 `9190999a…`; the same bytes were used in both runs, with the pinned fixture.

| Tree | Result |
|---|---|
| `a34d3f8` (new worktree `C:/t/iso/prior-a34`) | **New: 5 failed, 4 passed.** JUnit [`r11__review11_module_on_a34d3f8.xml`](evidence/prior/r11__review11_module_on_a34d3f8.xml); lines [`review11_module_on_a34d3f8.txt`](evidence/prior/review11_module_on_a34d3f8.txt). |
| `a977364` (`frozen-r11`) | **New: 9 passed** (section 3) |

**All 5 failures are behavioural.** Every new key is read with `.get`, and each test's first assertion is the evaluator's judgement or the stored attempt numbers.
- accepted after re-read 5, the pruning sequence;
- recovered for X-SD-9 at actual read 15, the collision sequence;
- attempt numbers repeating `13, 13, 13, 13`;
- a stored collided row recovered;
- improved at step 8 of the retention cycles with failed and budget-stopped attempts.

**The 4 that pass there:**
- explicit `target_revision` held past the history limit (control);
- same-context retries (control);
- genuine re-read (control);
- missing attempt order. `a34d3f8` already held that row, so it is kept as a control and **not** claimed as a demonstration.

## 3. Focused modules on `a977364` (new)

All three runs are new, on `C:/t/iso/frozen-r11` at `a977364`, with no `.env`. The JUnit files are in [`evidence/focused/`](evidence/focused/).

| Run | Modules | Result |
|---|---|---|
| **The reviewer's nine-module set** (161 tests before additions) | `test_m2_eval5` (13), `test_evidence_reader_r7` (36), `test_evidence_reader` (21), `test_ai_ledger` (9), `test_m2_review07_extraction` (6), `test_m2_review07_boq` (3), `test_m2_review08` (27), `test_m2_review09` (34), `test_m2_review10` (12) | **161 passed** |
| **Review 11 module** | `test_m2_review11` (9) | **9 passed** |
| **Changed persistence path and compatibility** | `test_document_processing_v2` (11: the processing job that runs the evidence stage), `test_design_sheet_extractor` (31, 7 skipped), `test_m2_review05_boq` (11), `test_m2_review06_boq` (3), `test_boq_extraction_v2` (13), `test_boq_verification_v2` (4), `test_ai_assist` (32), `test_ai_sheet_reader` (7), `test_submittal_ai` (9), `test_extraction_pilot` (5), `test_m2_review06_titleblock` (8) | **127 passed, 7 skipped** (the same design-sheet skips as before) |

**The accepted work is still intact:**
- the Review 09 module (illegible reads, source hash, BOQ item presence, ledger wording);
- the Review 10 module (R10-01A/B);
- the reviewer's earlier and association probes (identical before and after; see SEQUENCES.md).

The reviewer's run of the nine modules on `a34d3f8` (161 passed) is **submitted, historical** evidence. The run in the first row is new, on the candidate.

## 4. Hermetic full suite on `a977364` (new, run once)

- **Tree:** `C:/t/iso/frozen-r11`, clean, no `.env`.
- **Command:** `python -B -m pytest tests -q -p no:cacheprovider --basetemp=C:/t/iso/tmp/r11full`.
- **Output:** JUnit [`evidence/suite/r11__suite_full_frozen_hermetic.xml`](evidence/suite/r11__suite_full_frozen_hermetic.xml) and the log.
- **Result:** **The run completed:** 1,683 tests, **1,645 passed, 3 failed, 35 skipped, 0 errors**, no collection errors. It took 43 min 23 s, against about 19 min for the Review 08, 09 and 10 runs. The JUnit start timestamp is 2026-09-29 19:19:10 (+04:00), and the log and JUnit were written at 20:02.

- **Exit code.** pytest's own exit code was **not captured**. The run's wrapper command ended with `tail`, whose exit status (0) is what was recorded, and it is not pytest's. The log's final summary line reports 3 failures, which under pytest's documented convention means a non-zero exit (1). The run was not repeated merely to capture the code.
- **The run itself was neither restarted nor duplicated,** and the candidate was not changed while it ran.

**Every failure, compared with the Review 10 frozen run (`a34d3f8`) by test identity and failure message** ([`investigation/failure-comparison.json`](evidence/investigation/failure-comparison.json)):

| Failure | Review 10 run | Review 11 run | Disposition |
|---|---|---|---|
| `test_ep_archive_models.py::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` | failed: `IntegrityError: FOREIGN KEY constraint failed` | failed: **same identity, same message** | Pre-existing (also failed in Reviews 07–10) |
| `test_proposed_materials.py::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` | failed: `AssertionError: assert {'3-SDDC2', …} <= {…}` | failed: **same identity, same message** | Pre-existing (also failed in Reviews 07–10) |
| `test_sync_worker.py::test_two_worker_processes_cannot_both_claim` | **passed** (4.6 s) | **failed: `subprocess.TimeoutExpired`** (60.8 s) | **New in this run; investigated below. Not a correction regression, on the evidence below.** |

**Test counts.** 1,683 against 1,674. The difference is exactly `test_m2_review11.py` (+9); every other module has the same count, and the 35 skips are unchanged.

### Investigation of the new failure

**What the failure is.** The test starts two real Python processes. Each imports `app.database` and `app.services.jobs` and claims a job at the same instant, and the test waits at most 60 s for them. In this run a child process did not finish within 60 s (`TimeoutExpired` inside `communicate(timeout=60)`). No assertion about the claim result was reached.

**Evidence:**
1. **The candidate's changes are not on this path.** `a34d3f8..a977364` changes only `backend/app/ai/evidence_reader.py` and two test files. Importing the child processes' modules (`app.database`, `app.services.jobs`) on `frozen-r11` **does not load `app.ai.evidence_reader`** (checked: not in `sys.modules`). The import alone took 11.9 s at the time of the check.
2. **It passes in isolation on both candidates.** Run alone three times on `frozen-r11`, it passed 3/3 (5.65, 5.27, 5.37 s). On `frozen-r10` it also passed 3/3 (5.51, 5.16, 5.35 s). The whole `test_sync_worker.py` module passes 18/18 on both trees. See [`investigation/isolated_runs.txt`](evidence/investigation/isolated_runs.txt) and the JUnit files.
3. **Its timing across full runs.** In the Review 08, 09 and 10 full runs it took 4.6 s each time, and those suites took 18.7–19.1 min. In this run it took 60.8 s, and the whole suite took 43.3 min (2.3× slower). The slowdown was machine-wide, not confined to this test ([`investigation/prior_full_suite_times.txt`](evidence/investigation/prior_full_suite_times.txt)).
4. **The cause of that slowdown was not established.** The focused runs started during the suite had finished by 19:36; the test began at about 19:58, so they do **not** explain it. The owner's own services (uvicorn and the workers) run on this machine. Process creation here is known to be slow on some days: one isolated pytest start took 54 s of wall time against 13–16 s for the others.

**Disposition.**
- **Recorded as a failure of the frozen `a977364` run,** and it stays that way. It is not re-labelled as pre-existing, and nothing is masked.
- **On the evidence above, it is an environmental timeout, not a regression of this correction.** The changed code is not imported on its path, and the test passes identically on the candidate and the baseline when run alone.
- **Limitation:** no second full-suite run was made to show a full run without it.

## 5. Re-score of the stored outputs (new)

**The setup.**
- **The evaluator's code did not change** (`.9`), but its AI evidence comes from reader `.6`.
- **Every stored output was re-scored** from `frozen-r11` with the same declared contexts and negative controls as in Review 10 (script [`evidence/rescore/rescore_r11.py`](evidence/rescore/rescore_r11.py), derived by `make_rescore10.py`).
- **Each run was compared with its Review 10 result** (reader `.5`), whose files were hashed before and after and are unchanged.

**Result.**
- **All 33 scored runs are identical**, and the 4 negative controls are unchanged. The association counts in the AI runs are also identical to Review 10 ([`ASSOCIATIONS.json`](evidence/rescore/ASSOCIATIONS.json)):
  - matched EV1: 3 decisions `current`, 3 `by_target`, 18 revisions `not_recorded`;
  - matched EV2: 3 `current`, 2 `by_target`, 15 `not_recorded`;
  - Review 06 runs: all `not_recorded`.
- **Why nothing changed.** Every stored run is a single attempt per document, with reliably ordered, unique attempt numbers. So reconstruction yields the same context as before, and no fact is held for lost or ambiguous history.
- **What R11-01 therefore is.** A defect of repeated processing. This package claims neither an effect on the historical scores nor a production defect.

## 6. Assertions changed from an earlier version

**None.** No existing test was modified. The only files added are `test_m2_review11.py` and the pinned fixture `tests/fixtures/evidence_reader_r10.py`.
