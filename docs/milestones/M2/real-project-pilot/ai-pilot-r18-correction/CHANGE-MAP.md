# Change map: successor `c216206` (from the submitted `e5a0a94`)

The successor lives in the scratch clone `C:/t/iso/ep-platform`, worktree `C:/t/iso/cand-ai2`, branch `ai-pilot-r18-2026-09-30`. It is not in the owner's repository. The full diff is in [candidate/e5a0a94-to-c216206.diff](candidate/e5a0a94-to-c216206.diff); the commit patch is in [candidate/](candidate/).

Only `backend/app/ai/evidence_reader.py` changes in the application; the rest are tests.

## Behaviour by flag

| Flags | Behaviour |
|---|---|
| none | accepted `3d5607d` (identities asserted equal) |
| G | `e5a0a94` G: `validate_value` guard + the `revtok` raw observation; the discovery / absence helpers are no-ops |
| T (requires G), `.2` | new `_read_page_required` + `_finish_page` (`_read_page` delegates to them; `read_document` runs every page's required reads, then the optional reads) |
| E (independent) | `_discover` / `locate_title_block` / `_absent` / `_norm_to_page`, the timeout + floor in `EvidenceRun.call`, `_ocr_timeout` bounding `_local_ocr` / `region_texts_v2` |

Details of T `.2`:
- **Completion:** recomputed from a usable targeted reading (legible, has a value, own role).
- **Separate outcomes:** `own:<f>:primary` / `own:<f>:targeted`.
- **Wrong role:** the reading is kept on the observation but excluded from validation.
- **Gate:** no targeted read after a failed / refused / budget-refused primary or escalation request.
- **No-region reads:** the context clip is E's located area when there is one.

## Identities

| Arm | Reader | Policy | Added prompt |
|---|---|---|---|
| G | `…29.7` (unchanged) | `+guard-rev-token-2026-09-30.1` | none |
| T `.2` | `+targeted-2026-09-30.2` | `+region-support-2026-09-30.1+targeted-completion-2026-09-30.2` | `read_field_context` (text unchanged, `.1`) |
| E | `+located-discovery-2026-09-30.1` | `+located-discovery-2026-09-30.1` | `discover_region` `discover-region-2026-09-30.1` |

## Pre-freeze patches

All scripts are kept.

| Patch | Change | Found by |
|---|---|---|
| `patch_successor.py` | the main change | – |
| `patch_successor_2.py` | an absence is verified whenever discovery saw the whole page | running the existing modules under E with a whole-sheet locator |
| `patch_successor_3.py` | a label box only with a number label; scans OCR both title-block edges | the offline locator evaluation |

## Tests

| File | What it is |
|---|---|
| `tests/_keyed_provider.py` | the keyed provider |
| `tests/_e_frame_shim.py` | the frame shim for the E run of the existing modules |
| `tests/test_ai_pilot_r18.py` | 30 new tests: R18-01/02, scheduling, E, and the guard replay with positive controls |
| `test_evidence_reader_r7.py`, `test_m2_review08.py`, `test_m2_review10.py` | the three repaired scenarios (keyed answers; assertions kept) |
| `test_ai_pilot_2026_09_30.py` | the wrong-role expectation updated to the successor contract; E pinned off in its T helper |

## Unchanged

- thresholds;
- `validate_value` / `validate_decision`;
- `merge_evidence` / `evidence_for`;
- BOQ verification and the BOQ-T queue;
- evaluator `.9`;
- the r16.1 matcher / replay;
- business consumers.
