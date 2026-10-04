# Tests and regressions

All runs were offline, with scripted providers and no model request. Interpreter `ep-platform/backend/venv`, no `AI_EVIDENCE_*` variable set unless a test sets one, `-p no:cacheprovider`. The candidate tree was clean before and after every run (`tests/FINAL-candidate-status-*.txt`).

## Review 29 tests (92, all pass on `a8aaced`)

| File | Tests | Covers |
|---|---|---|
| `test_r29_identity_guard.py` | 40 | 18 positive controls for short and unusual real identifiers; 12 negative controls (headings, clause titles, page counters, generic labels, revision tokens); section number under its label; running footer on A4 but not on a drawing sheet; two-label lift and no lift without source text; reference role from label, discovery or targeted role; a model role claim never lifts; revision token never lifted; IG off equals `validate_value`; the **D03 shape end to end**, reproducing with IG off and held with region and no targeted read with IG on; C1 revision 2, a conflict not guarded |
| `test_r29_adjudication.py` | 20 | **D04 shape** resolves; order and recency invariance (6 permutations); one model reading never wins; an own-labelled competitor keeps the conflict; **D12 shape** truncation; no source text means no resolution; **D06 shape**, two own-labelled numbering systems held; a source-bound deterministic reading blocks; revision needs a page identity; **split-text regression**, the revision-0 false acceptance kept as a test; the D04 shape through the reader under CA off, CA, CA + IG and CA + IG + PA |
| `test_r29_decision_region.py` | 14 | **D16 shape**, a scanned stamp read instead of absent and reproducing the defect with DR off; **D18 shape**, a failed read is a failure; signal without region goes to the locator, and a failed locator is unknown; a scan with no signal is unknown after an empty locator; a no-decision control letter keeps its verified absence; **D17 shape**, a written code read twice through the legend at 0°, 90° and 270°; a single read is not corroborated; conflicting marks give conflict; a receipt stamp is no decision; ROI discovery gives no decision and the locator finds the stamp; request bound; DR off unchanged |
| `test_r29_association.py` | 6 | **D26 shape**: .9 alternates (held on a no-record page against held correct) while .10 does not; PA holds a targetless footer revision through merge and `evidence_for`; page-1 revision keeps its credit; no page identity means held unassociated with no credit; `association_of` never reattaches a PA hold; .10 equals .9 except for cross-page dependents |
| `test_r29_persistence.py` | 12 | Flags off are the accepted identities and the frozen L3 identity is unchanged; each switch adds only its own suffix; combined identity; no scheduling is ever implied, even through T; configurations never share cached answers; a repeat reuses only its own cache and is idempotent; a failed decision read is retried and the last good evidence kept; profile and variant keep their own envelopes |

## Existing suites on the final candidate (`a8aaced`, flags off)

| Run | Result |
|---|---|
| Focused: 50 modules covering extraction, BOQ, AI evidence, processing jobs, M2 reviews 05 to 12, evaluators and pilot arms, plus R29 (`tests/FOCUSED-MODULES.txt`) | **652 passed, 10 skipped, 0 failed** (`tests/FOCUSED-final.*`). The 10 skips are pre-existing in the design-sheet and DRF extractors. |
| Full backend suite | **2 failed, 1,824 passed, 35 skipped** (`tests/FULL-final-candidate.*`) |

## Baseline comparison (accepted `3d5607d`)

| Run | Result |
|---|---|
| Accepted baseline, full suite, clean re-run | **2 failed, 1,657 passed, 35 skipped** (`tests/FULL-baseline-rerun.*`); baseline tree clean before and after |
| Failure comparison | **Identical by test name and by message** (`tests/FAILURE-COMPARISON.json`): `test_ep_archive_models::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` (FOREIGN KEY on DROP TABLE users) and `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (three part numbers missing from the catalogue). These are the same two failures recorded on `3d5607d` in Review 21. |

**Messages.** The raw message text of the second failure lists the same three part numbers in a different order, because Python randomises set ordering per process. The comparison therefore keys on the exception type and the sorted quoted items, and records both results (`same_messages: true`, `same_messages_raw: false`).

**The first baseline run is disclosed, not used** (`tests/FULL-baseline.*`, `tests/FAILURE-COMPARISON-stalled-baseline.json`). It ran overnight, and three tests stalled for about 7,200 seconds each. Two failed after the stall: a 401 from an expired session and a `KeyError`. Both pass in the clean re-run, which changed no code. The candidate's earlier run on `a4ce6a3` (`tests/FULL-candidate.*`) also had only the same two failures.

**Housekeeping.** My first manual scorer test wrote one score file into the baseline tree (`frozen-r12/backend/scores/`), through a relative path after the scorer changed directory. I found it through the untracked-files check after the stalled run and removed it, and the tree is clean. The scorer is always called with absolute output paths now.

## Regressions found during the work and how they were handled

1. **Revision 0 of C2** validated split-text truncations (D12, and D19, which is resolved) in the offline replay. The contract was revised and re-frozen (revision 1), and a regression test was added.
2. **IG with CA:** guarding a conflict's provisional value suppressed the targeted read. C1 revision 2 was frozen and a test added.
3. **Replay artefacts**, corrected in the method and not in the candidate:
   - original budget refusals were matched by cache key, which does not survive a switch change, so they are now matched by document, task and page;
   - the replay was exposed to the real 120-second job limit under load, so that limit is lifted in the replay sandbox only.

   All final replays ran after both fixes.

## Verdict

Every offline criterion is met, and failures are proven identical to the accepted baseline:
- the Review 29 and focused suites pass;
- the full-suite failures are identical to the baseline's;
- flags-off compatibility holds;
- there are 0 newly validated wrong facts;
- the package check passes (`evidence/PACKAGE-CHECK.json`).

**READY FOR INDEPENDENT CORRECTION REVIEW.**

This does not claim improved general accuracy, select a default, start the fresh run, approve M2 or start M3. M2 remains **CHANGES STILL REQUIRED**.
