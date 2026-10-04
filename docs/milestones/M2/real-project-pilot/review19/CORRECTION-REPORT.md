# Review 19 correction: E absence semantics, continuation coverage reporting, actual-crop validation, H-06 (2026-09-30)

## The four conclusions, stated separately

1. **Correction acceptance requested** for R19-01 and R19-02: successor `69ee759`, coverage result version 2.
2. **Extraction accuracy is unresolved.** M2 stays CHANGES STILL REQUIRED. No variant is chosen: the continuation's gain is mostly rotation-correct support, and extra targeted calls show no incremental gain in this sample.
3. **Evidence and label uncertainty is unchanged.** Labels are AI-drafted or AI-reviewed and provisional; no human sign-off is implied. The DJ-295 O/0, DRF handwriting / project association and EML-09 identity uncertainties remain.
4. **H-06 is PENDING** (section 5). The live ledger refused before any dispatch.

No model request was made in this task. No live code, settings, services, database, original documents, labels or earlier packages were changed. The work is in the scratch clone, not the owner's checkout. The ten sealed projects stay unopened.

## 1. Reproduction on the submitted candidate `c216206`

- **Reviewer contracts:** byte copies of `test_review19.py` and `efficiency_probes.py`, run from this package with only the tree path substituted. Result: **2 failed, 6 passed**, exit 1. The probe JSON is **identical** to the reviewer's `INDEPENDENT-E-PROBES.json`. See [repro/on-c216206](repro/on-c216206/).
- **New actual-crop module on `c216206`:** 5 failed, 8 passed ([repro/on-c216206/R19-ACTUAL-CROP-on-c216206.log](repro/on-c216206/R19-ACTUAL-CROP-on-c216206.log)). The raster-stamp test fails, and so do the four rotation tests, only on the decision absence claim; their identity and revision were `completed` at every angle.
- The reviewer's artifacts are untouched; their hashes are in [bindings/SOURCE-BINDINGS.json](bindings/SOURCE-BINDINGS.json).

## 2. R19-01: a crop never establishes absence outside what it inspected

- **Fix in `_absent`:** `absent_by_discovery` only when discovery saw the whole page (not located, or a located area covering ≥ 98% of it). Otherwise every field discovery did not report is `incomplete:located_region_only`. The text-silence rule and its cue pattern are removed.
- **No compensating mechanism:** no request, fallback, status or threshold was added; business routing is unchanged.
- **Identity:** E moves to `.2`. See [CHANGE-MAP.md](CHANGE-MAP.md) and [candidate/c216206-to-69ee759.diff](candidate/c216206-to-69ee759.diff).

**Persisted-stage evidence** (the actual locator and partial crop, coordinate-aware answers, `evidence_stage` → merge → reload → `evidence_for`), in `tests/test_ai_pilot_r19.py`:

| Case | Result |
|---|---|
| Raster "CONSULTANT – CODE B / APPROVED AS NOTED" stamp outside the real crop (text layer silent, ≥ 80 characters) | decision `incomplete:located_region_only`, page partial, **no request spent**; identity validated |
| Control: ordinary A4 text document (whole-page discovery) | decision / revision `absent_by_discovery` (unchanged) |
| Control: wholly scanned A2 sheet (located by local OCR) | decision / revision incomplete; identity read |
| Control: decision words outside the crop | incomplete |
| Control: a genuine decision inside the crop | read, `completed`, ANN validated |
| Control: a failed re-read (decision timeout) | `failed:timeout`; attempt 1's decision stays selected |
| Control: a later crop without the block | incomplete; attempt 1's decision stays selected |

## 3. R19-02: continuation coverage replay, result version 2

- **Script:** [scripts/score_cont_v2.py](scripts/score_cont_v2.py), result version `cont-coverage-2026-09-30.v2`, in [results-v2/](results-v2/).
- **Stored data:** attempts, rows and usage are read only; their hashes are recorded.
- **Required fields:** the set is explicit (identity, revision, decision). Optional keys never count toward it.
- **Field outcome classes:** `completed_read` and `discovery_absent` are kept apart; the others are `located_incomplete`, `no_region`, `unusable`, `failed`, `budget` and `not_attempted`.
- **Transport:** `stop_of` now returns only a transport state (`no_transport_stop` / `transport_stop:…`), never "complete".
- **R19-01 column:** a separate column re-reads stored `absent_by_discovery` values that were recorded on a located crop.

**Headline, all 7 planned documents** (evaluator .9 recovery, asserted equal to v1):

| Arm | Identity | Revision | Decision |
|---|---|---|---|
| S | 2 recovered, 3 held, 2 missed | 3 recovered, 3 held, 1 missed | tn 6, missed 1 |
| T2 | 5 recovered, 2 missed | 5 recovered, 2 missed | tn 6, missed 1 |

**Field coverage, all planned:**

| Arm | Identity | Revision | Decision |
|---|---|---|---|
| S | 4 completed read, 2 budget, 1 no region | same as identity | 7 discovery absent (whole-page discovery, valid under the accepted contract; S's discovery missed TEL-00's labelled consultant decision) |
| T2 | 4 completed read, 2 not attempted (timeouts), 1 located incomplete | same as identity | 2 located incomplete + 3 discovery absent + 2 not attempted; **under R19-01: 5 located incomplete + 2 not attempted** |

**Subgroups** (never the headline; with document IDs in the files):
- **`no_transport_stop_subgroup`** (v1's "matched completed", renamed; a transport comparison, not fully read documents): BH2031, EML-09, ELEC-B16, 819-TL-101.
- **All required fields usable in both arms:** **1** (819-TL-101); under R19-01: **0**. BH2031, EML-09 and ELEC-B16 leave v1's completed claim ([V1-TO-V2-DELTAS.json](results-v2/V1-TO-V2-DELTAS.json)).
- **Identity read in both arms:** 3 (BH2031, EML-09, 819-TL-101). S: 1 recovered, 2 held; T2: 3 recovered.
- **Revision read in both arms:** the same 3. S: 2 recovered, 1 held; T2: 3 recovered.
- **Decision read in both arms:** 0.

**Reviewer contracts on the successor** with the v2 scorer / metrics: **8 passed**, exit 0 ([repro/on-successor-frozen](repro/on-successor-frozen/)).

## 4. Validating the actual E path

Two plugins were used to run the existing modules on E:

- **`tests/_e_frame_shim.py`** (whole page as the crop): compatibility-only evidence.
- **`tests/_e_crop_coords.py`** (new): keeps the **real locator and partial crop**. It adapts only the scripted discovery frame: a page-frame box at least half inside the crop is clipped and mapped into it; otherwise the field is not visible. It logs every dropped field.

**Test results on the frozen `69ee759`** (16 modules, 259 tests; JUnit / logs / exit codes in [tests/](tests/)):

| Run | Result | Explanation |
|---|---|---|
| flags off | **259 passed**, exit 0 | – |
| T | **259 passed**, exit 0 | – |
| T+E, actual crop (adapter) | 237 passed, **22 failed**, exit 1 | Every failure classified from the adapter's own log ([tests/CROP-FAILURE-CLASSIFICATION.json](tests/CROP-FAILURE-CLASSIFICATION.json)); see below |
| T+E, whole-page shim (compatibility only) | 247 passed, 12 failed, exit 1 | All 12 are the new actual-crop module, whose tests reject a whole-page "crop" by design; the other 15 modules pass |
| T+E, raw (no adapter, no shim) | 240 passed, 19 failed, exit 1 | The same 19 tests, by id, as the disclosed `c216206` run |
| r16.1 harness | 66 passed | – |
| BOQ queue | 8 passed | – |
| Full backend suite, flags off (final frozen `69ee759`) | **1724 passed, 2 failed, 35 skipped**, exit 1 | 1711 + the 13 new tests. The 2 failures are the same tests with the same messages as on `c216206` (`test_ep_archive_models::…lookup_index` FOREIGN KEY; `test_proposed_materials::…completes_it`), and both also fail on the accepted `3d5607d` ([tests/FULL-SUITE-KNOWN-FAILURES-COMPARISON.json](tests/FULL-SUITE-KNOWN-FAILURES-COMPARISON.json)). Run once; not looped. |

The 22 actual-crop failures break down as:
- **20:** the fixture's decision block (all 20) and, in one, also its revision are printed **outside the real crop** (the decision at the page's top-left). A located discovery cannot see them, so the decision is never read and is recorded incomplete. That is the crop contract.
- **2** (`test_resumed_work_keeps_what_was_read_and_reads_the_rest`, `test_a_later_resume_completes_the_missing_work_with_its_own_provenance`): nothing lay outside the crop. Only the final page-outcome assertion fails: `partial` instead of `evidence` / `complete`, because a located page's decision is now unknown (R19-01). Every earlier assertion passed.
- **Locator finding (not widened):** the R10 fixture prints its revision inline as `REV 02 03`, which the application's pattern does not treat as a revision label. The ±12% box around the number label therefore clips that cell (44% visible).

The legacy tests were **not edited**: their behavioural assertions stand, and the changed expectations are explained per test.

**Substantive E finding:** on drawing sheets, located discovery never reads a decision printed outside the title-block area. After R19-01 this is reported honestly as incomplete, but it is a **coverage cost** of E. It applies to the legacy fixtures' top-left decision block and to any stamp outside the title block.

**Narrow expectation corrections:**
- `test_ai_pilot_r18.py::test_located_discovery_maps_its_regions_back_to_the_page`: `absent_by_discovery` → `incomplete:located_region_only`, for a decision a crop never showed (R19-01).
- The three repaired legacy scenarios pass with flags off and T. Under T+E, two of them (R8, R10) are among the 20 decision-outside-crop cases above.
- The submitted 30-test R18 module passes with flags off, T and T+E after the one correction.

**Reviewer's rotation controls** (actual locator, 0/90/180/270): pass, within the 8 contracts.

## 5. H-06: PENDING (live refusal saved, nothing dispatched)

- **Unchanged frozen binding:** declaration `7b2513b2…`, runner `cont_boq.py` (hash equal to the declaration's), the accepted `3d5607d` BOQ reader, queue, r16.1 harness, sheet / extraction / labels.
- **Preflight** ([h06/](h06/)):
  - the durable ledger shows 104/150 settled, 0 open reservations and the H-06 scopes unused;
  - the exclusive H-06 allowance store has never been opened (both arms have their full 12);
  - the sandboxes are free.
- **Rolling EP-8430 count:** **60/60 used** at the last check (**2026-09-30 15:26:47 UTC**; an earlier check at 14:49:52 UTC gave the same). The frozen runner was invoked right after and **refused before any request**: "EP-8430 rolling-24-hour allowance cannot fit this arm now (60/60 used)". The log is saved. No H-06 ledger entry or allowance store exists.
- **Eligibility from the live counter at that check:** one 12-request arm from **2026-09-30 18:53:56 UTC**, both arms (24) from **18:55:20 UTC**. This is a statement of the counter, not an authorization. The next run must re-run the preflight.
- **Queue finding (unchanged):** the frozen BOQ-T queue puts held rows first and cannot reach H-06's three wrong accepted rows within 12 requests. It is not re-ordered.

## 6. Next step (proposal only)

[PROSPECTIVE-EXPERIMENT-PROPOSAL.md](PROSPECTIVE-EXPERIMENT-PROPOSAL.md) proposes isolating the rotation fix, ROI discovery and extra targeted calls at equal budgets, with labels frozen before predictions. It is not executed; no residual request is spent.
