# Change map: successor `69ee759` (from the reviewed `c216206`)

The successor is in the scratch clone `C:/t/iso/ep-platform`, worktree `C:/t/iso/cand-ai3`, branch `ai-pilot-r19-2026-09-30`. It is not the owner's checkout. The full diff is in [candidate/c216206-to-69ee759.diff](candidate/c216206-to-69ee759.diff).

## Application: `backend/app/ai/evidence_reader.py` (+9 / −10, E only)

| Before (`c216206`) | After (`69ee759`) |
|---|---|
| `_absent`: on a located crop, a decision was `absent_by_discovery` when the page text had ≥ 80 characters and no decision-block cue | `_absent`: `absent_by_discovery` only when discovery saw the whole page (not located, or a located area covering the whole page); every other field on a located crop is `incomplete:located_region_only` |
| `_DECISION_BLOCK_CUES` pattern | removed (unused) |
| E identity `+located-discovery-2026-09-30.1` | `+located-discovery-2026-09-30.2` (policy and reader), because the absence semantics changed |

**Unchanged:**
- G, T `.2`, the locator and its crop, the deadline and timeouts;
- thresholds, validation, merge / selection, the evaluator, the BOQ runner and queue;
- business routing, roles, categories and statuses;
- no migration.

With flags off the identities equal accepted `3d5607d`'s.

## Tests

| File | Change |
|---|---|
| `tests/test_ai_pilot_r19.py` (new, 13 tests) | Every test uses the **actual** locator and crop, with coordinate-aware scripted answers, through the persisted `evidence_stage` path (merge → reload → `evidence_for`). |
| `tests/_e_crop_coords.py` (new) | A plugin that runs the existing modules on the actual crop. It adapts only the scripted discovery frame: a page-frame region at least half inside the crop is mapped into it, otherwise the field is not visible. It logs every field it drops. |
| `tests/test_ai_pilot_r18.py` | One expectation corrected: `test_located_discovery_maps_its_regions_back_to_the_page` now expects `incomplete:located_region_only` for a decision the crop never showed (R19-01), instead of `absent_by_discovery`. |

What `test_ai_pilot_r19.py` covers:
- the raster stamp outside the crop;
- controls: an ordinary whole-page text document, a wholly scanned sheet, decision words outside the crop, a genuine decision read inside the crop, and a failed re-read with good-decision retention;
- rotation 0 / 90 / 180 / 270, own-field coordinates and source support;
- a missing ROI, where the context read is on the crop and not the sheet;
- discovery and blind timeouts with last-good retention;
- crop absence not superseding a completed revision.

The whole-page shim (`tests/_e_frame_shim.py`) is unchanged and remains **compatibility-only** evidence.

## Reporting (outside the application)

| File | Change |
|---|---|
| `score_cont_v2.py` | Coverage replay, result version `cont-coverage-2026-09-30.v2`. It replaces the v1 `stop_of` / `matched_completed` reporting; the stored attempts are not altered. |
| `h06_preflight.py` | Read-only live check before any H-06 dispatch. |
