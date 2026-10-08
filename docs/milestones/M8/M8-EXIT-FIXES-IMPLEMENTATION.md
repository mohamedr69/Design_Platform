# M8 exit fixes: the engineer's decisions (ORCH-044, U2-M8-EXIT-FIXES)

Implementer: ep-implementer (isolated). Authority: A-16 (the engineer's decisions 1-8, 8 October 2026), released
for isolated implementation by A-18 item 5 / A-20 item 8. Branch `task/m8-exit-fixes`, worktree `wt-m8b`, from
`roadmap/u2` at `1708692084f2253fa0eb792910f7c8b685680da7` (contains the M5 merges, the M8 merge, the owner's
platform work and the M6 merge; `config.py` keeps the owner's settings, `prep_wall_layers` and
`attribution_own_originators`). Source commit `77bd211`. Interpreter: the live clone's venv, `python -B`,
ezdxf 1.4.4, `-p no:cacheprovider --basetemp=C:/t/tmp/m8b/bt`. No provider, model, `claude` CLI, network, AutoCAD,
live application, database or `.env`. The Golden DXF was read only; every pickle went to `C:/t/tmp/m8b` (deleted).
Evidence: `docs/milestones/M8/evidence/exit-fixes/` (hashes of the committed bytes in `MANIFEST.json`).

A passing suite is evidence, not acceptance. The decision sheet file itself still reads "OPEN": it was not edited
here; the register entry A-16 is the authority.

## Decision -> change -> test -> before/after -> GC-01 effect

| # | Decision (A-16) | Change | Test | Before -> after | GC-01 effect |
|---|---|---|---|---|---|
| 1 | B: default deny of block names `T\.FRAM\|TITLE\|FRAME\|BORDER\|SHEET` in the INSERT chain, walls and boundaries, overridable; DIM_TEXT inherited onto a wall layer too | `layers.FrameRule` (block's own name, xref prefix off; any block of the chain; DIM_TEXT class = `ANNOTATION_BLOCKS` `DIM\|TEXT` on layer-"0" content only); `settings.prep_frame_blocks` right after `prep_wall_layers`; `walls.build(deny_blocks=, annotation_blocks=)`, `coverage.build_columns(...)` same; reason `title_frame` (after visibility, before deny/allow); `report.title_frame_blocks`; rules in both fingerprints | f8 (frame on 06-WALL via CCSD, BORDER with explicit A-WALL lines, X-REF_ DIM_TEXT); override test; setting-position test; GC-01 golden | f8: kept 769 m -> 244 m; bounds 769 -> 244 m | walls: **72 T.FRAM segments, 7,733.5 m** and **4 DIM_TEXT segments, 13.9 m** leave the kept set: **16,645 / 32,625.0 m -> 16,569 / 24,877.6 m**. Also reclassified (not kept before either): 288 `47-GRID` segments in T.FRAM, 302 `DIM_TEXT$0$UNITS TYPES TAG` (deny_listed -> title_frame). No other GC-01 block adds a `title_frame` segment (the drawing also defines `X-REF_TITLE BLOCK A1…`, `…$0$Frame`, `…$0$Frame Post` and two `title block a1` blocks, which the rule matches by name; none contributes a shown segment of 0.3 m or more to either index). Boundaries: see below |
| 2 | B: off / no-plot INSERT hides only inherited "0" content; frozen hides all | `layers.walk`: `HIDES_ALL` = invisible, frozen, viewport-frozen; inherited content's own reason gets `insert_` | f3 and f6 updated (cited in the tests); f11 | f3: B0 on an off layer keeps its explicit A-WALL line (was `insert_layer_off`); its "0" line `insert_layer_off` (was `layer_off`); B0 on a frozen layer: both `insert_layer_frozen`. f6: frozen xref's "0" lines `insert_layer_frozen` (was `layer_frozen`) | 0 (kept unchanged; `X-REF_PLOT$0$A-NORTH` stays `layer_frozen` 342: explicit layer) |
| 3 | A + C: keep 200 m; `$INSUNITS` -> metres before threshold and report; unknown unit held | `layers.drawing_units` (INSUNITS table 1-24; 0/missing = unknown; `$MEASUREMENT`/`$LUNITS` read and reported); `walls.build` converts every length (min length, threshold, report); report `units` (unit, factor, source); `Walls.held` = `units_unknown`, `sparse` True, `near()` empty; `coverage.build_columns` converts bounds and column size, holds both when unknown; `prepare.rooms`/`gate` say "not measured, units unknown" | u1 metres, u2 mm, u3 inches, u4 unitless; header/table test | mm drawing: 301,600 "m" never sparse, 0.4 m column missed -> 301.6 m, column found; unitless: measured as metres -> held | unit m, factor 1.0 (`$INSUNITS` 6; `$MEASUREMENT` 0, `$LUNITS` 2 reported): numbers unchanged by this decision |
| 4 | C: MLINE not read; `mline_unsupported`; gate not measured | walk counts MLINE on wall layers (shown, not framed): count, reference-line length, hidden; `Walls.held` = `mline_unsupported` when sparse; `prepare.rooms` holds the room even with named boundaries; `prepare.index_state` -> coordination `wall_index`; `gate` reason | f9 | f9: silent "sparse" -> report 3 MLINE / 30.0 m; gate `needs_engineer` with the reason | 0 MLINE |
| 5 | B: TAG in `NOT_BOUNDS` | `coverage.NOT_BOUNDS` | regex test; GC-01 golden | | `X-REF_ TAG$0$49-DOOR-TAG` 501.8 m (1,869 segments) out of the boundaries |
| 6 | A: rotation term in `fit`; viewport passed | `review/geometry.py`: `fit(page, texts, view)` with `rot_deg` = -twist (ezdxf: paper = R(twist)·model), `to_model`, new `to_page`, `sheet_view` (handle, twist, centre, scale, frozen layers; mixed twists -> not tied), `fit_sheets` passes it and stores `view`; `redesign/service.py`: `_page` via `to_page`, `_index_viewport`, `_walls(sheets=)` at the six call sites | synthetic twisted page (None without the term, exact with it); f12 end to end (page drawn from the DXF through ezdxf's viewport matrix, tied by `fit_sheets`, every text within 0.5 m); untwisted fit identical; `_walls` builds for the viewport | f12: not tied -> tied, residual < 0.5 m | all 20 sheets twist 0: fit before/after **identical on 20/20** (pages drawn from each sheet's viewport; the plotted PDF is under the live uploads and was not read). Index for FA 101's viewport (frozen 18-DIM, BUILDING): kept identical (16,569) |
| 7 | arcs candidates; meshes not read, reported | `layers.is_mesh`; `report.mesh_not_read` (polyface, polygon_mesh, on wall layers); bounds report too | f10 | silent drop -> counted | 0 meshes |
| 8 | A: allow-list regex stays | none | pin test | | none |

## Boundary index (GC-01, deduplicated)

Base (ORCH-036 record) 40,426.7 m; ORCH-036 M8 43,456.6 m; now **35,221.3 m** (338 columns, hidden: invisible 6,838,
title_frame 76). Attribution: frame rule **7,733.5 m** (72 segments: 36 horizontal x 119.83 m = 4,314.1 m and
36 vertical x 94.98 m = 3,419.4 m), TAG 501.8 m. The card expected 39,142 m (from ORCH-042's 4,314 m): ORCH-042
counted only the horizontal edges. The new total is 5,205.4 m below the base, honestly reported.

## ORCH-042 conditions

- U2M8V-04: `f11_bounds_hidden` (300 m shown; a frozen, an invisible and an inserted-on-frozen line): raw-layer rule
  400 m, index 300 m, hidden `{insert_layer_frozen 1, invisible 1, layer_frozen 1}`.
- U2M8V-02: `.gitattributes` `backend/tests/fixtures_m8/*.dxf -text`; fixtures written LF; `MANIFEST.json` records
  the blob id and the sha256 of the committed bytes; `scripts/check_manifest.py` recomputes it from a commit and from
  a checkout (as is and LF-normalised) and also reads the ORCH-036 manifest.
- U2M8V-03: `make_fixtures.py` writes CLASSES in a fixed order and LF line ends: 8 runs (PYTHONHASHSEED 4, 7, 10, 0,
  1, 12345, 99, unset) identical, 16/16 files equal to the committed blobs (`fixtures-determinism.json`); f1-f7
  bytes unchanged.
- Report corrections in `M8-WALL-INDEX-IMPLEMENTATION.md` (T.FRAM total; boundary attribution; build times) and a
  section "Engineer decisions applied (A-16)".

## Runs

- Targeted (`targeted.xml`, `targeted.log`): walls_layers, exit_fixes, redesign, drawing_prep, redesign_apply,
  prep_readiness, drawing_review (review/geometry), fa_interfaces: **159 passed**, 0 failed, both golden tests ran.
  The 13 ORCH-036 tests: 3 updated (f3, f6: decision 2; saved-index versions 2->3 and 3->4), each cited.
- Full suite once (`full-suite.xml`, `full-suite.log`; 2026-10-08T11:52:30Z, 3,609 s): **1,999 tests, 1,963
  passed, 1 failed, 35 skipped**. Against the latest `roadmap/u2` result (M6 merge-and-conditions, 1,981 / 1,945 /
  1 / 35): no newly failing, none removed, no skip change, 18 new (this card's file); the one failure is the same
  test with the same message in both (`test_proposed_materials::…part_catalogue…`, pre-existing). Against the M4
  baseline (1,819 / 1,782 / 2 / 35): no newly failing; the same `test_proposed_materials` failure; `test_persistence`
  passes as it did in ORCH-036/042 (test source and environment, U2M8V-08); 180 tests only in the new run.
  (`full-suite-vs-roadmap-u2-latest.json`, `full-suite-vs-m4-baseline.json`).

## Ambiguities (literal option implemented; for the engineer)

1. "DIM_TEXT-class" read as blocks named `DIM|TEXT`, inherited content only (module constant, per-build override,
   not a setting). Using the whole NOT_WALLS list on block names would be broader.
2. `title_frame` precedes deny/allow, so 590 GC-01 segments already deny-listed are now counted `title_frame`.
3. Units: `$MEASUREMENT`/`$LUNITS` are reported, never used to infer a unit (GC-01 is metres with `$MEASUREMENT` 0);
   architectural/engineering `$LUNITS` (inches by AutoCAD convention) is not inferred. Unknown unit also holds the
   columns/boundaries index (no columns claimed).
4. Only lengths are converted; index coordinates stay in drawing units. Placement constants (1.5 m back, 0.6 m wall,
   0.2 m room grid, 6.3 m radius) still assume metre coordinates: a known non-metre drawing is measured in the index
   but not in placement.
5. MLINE + sparse holds the room even where named boundaries would close it (literal "not measured").
6. One wall index per drawing: a viewport is passed only when every sheet with a view freezes the same layers
   (GC-01: 3 sheets freeze two layers, 17 none -> model-space index; measured equal for FA 101).
7. The fit's viewport is read inside `fit_sheets` (where the DXF is opened), not handed from `review/service.py`;
   `FIT_VERSION` stays 1, so stored fits are not recomputed: rotated sheets need a re-review or a version bump
   (owner).

## Open points

- F-07 (wall snapping on a sparse index): handled only where the unit is unknown (`Walls.near` empty); a sparse,
  known-unit index still feeds snapping.
- The redesign's page directions (`_VECTORS`) and page-aligned boxes assume an untwisted view.
- Per-sheet wall index; per-project allow/frame store; later M8 stages; real-AutoCAD confirmation.
