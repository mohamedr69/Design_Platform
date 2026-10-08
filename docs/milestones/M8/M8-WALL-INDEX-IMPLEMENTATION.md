# M8 wall index: implementation report (ORCH-036, U2-M8-WALL-INDEX)

Implementer: ep-implementer (isolated). Branch `task/m8-wall-index`, worktree `wt-m8`, from `roadmap/u2` at
`5270773a469e31f5cad0b7d7a170e168a1d918ba` (code equal to 668f92f: only docs differ). Source commit `3317b88`.
Interpreter: the live clone's venv, `python -B`, ezdxf 1.4.4, `--basetemp=C:/t/tmp/m8/bt`. No provider, no
network, no AutoCAD, no live application, worker or migration. GC-01 DXF read only; every pickle went to
`C:/t/tmp/m8`. Evidence: `docs/milestones/M8/evidence/wall-index/` (hashes in `MANIFEST.json`).

A passing suite is evidence, not acceptance.

## Requirement -> change -> test -> result

| # | Requirement (card) | Change | Test | Result |
|---|---|---|---|---|
| 1 | Effective layer, nested INSERTs | `backend/app/redesign/layers.py` (new): `effective_layer`, `walk` (layer "0" takes its INSERT's effective layer, recursively), `local_name` (xref prefix). Port of RD-M1 `effective_layer.py` (left untouched). | f2, f3, f6; GC-01 E11 probes | pass; 22/22 E11 probe segments resolve to E11's effective layer |
| 2 | Block transforms | `app/ifc/dxf/geometry.py: chain_matrix` (the `m @ parent` composition), used by the walker and now by `interfaces/geometry.py` (behaviour identical); depth cap 16, self-insert guard, MINSERT expanded | f2 (by-hand affine maths incl. base point, rotation, 0.5 scale, mirror; and equality with ezdxf `recursive_decompose`) | pass; all interfaces suites pass unchanged |
| 3 | Visibility + reasons | `LayerTable.hidden` (frozen, off, no-plot, DEFPOINTS), entity `invisible`, INSERT chain (`insert_*` reasons), viewport frozen list (`viewport_info`, VIEWPORT `frozen_layers`); reasons recorded per segment (`detail=True`) and counted per layer | f3, f4, f5 | pass |
| 4 | Allow-list setting + override; deny-list second; same rules for columns/bounds | `prep_wall_layers` beside `prep_column_layers` in `config.py`; `walls.build(..., allow=, deny=, viewport=)`; `coverage.build_columns` walks with the same rules (effective layer's own name, hidden skipped) | f1, f6, f7; f3/f6 columns and bounds | pass |
| 5 | Composition report; sparse/empty = not measured | report stored in the pickle and on `Walls.report`; `Walls.sparse` (< 200 m kept, `MIN_WALLS_M`); `coverage.room_at` returns None for a sparse built index; `prepare.rooms/propose` name a "missing"/"sparse" index in the not-measured issue | sparse test (same lines by hand close the room; built sparse index -> not measured) | pass |
| 6 | Cache | `walls.VERSION` 1 -> 2; `fingerprint(allow, deny, viewport)` in `path_for`; `load` refuses a v1 bare pickle or another version; `coverage.VERSION` 2 -> 3 with its rules in `columns_path` | cache test | pass |
| 7 | Preserve | `Walls(cells, report=None)`, tuples, `near/faces_behind/face_behind/thick/face_span` untouched; `service.py` not edited (its `path_for`/`build` calls get the setting by default) | 30 tests of `test_redesign.py` + `test_drawing_prep.py` | 30/30 pass unchanged |

Allow-list default: `prep_wall_layers = ^(?!.*(?:TILE|FINISH)).*(?:WALL|PARTITION|CURTAIN|GLASS|GLAZ|SILL)`,
case-insensitive, matched (as `NOT_WALLS`) on the layer's own name: `X-REF_ FILE ALL FLOORS PLANS$0$06-WALL` -> `06-WALL`.

## Fixtures (`backend/tests/fixtures_m8/`, written byte-identically twice by `make_fixtures.py`)

| Fixture | Asserted |
|---|---|
| f1 simple sheet | 9 kept (inner 4, outer polyline 4, a wide polyline as its centre line); stub below_min_length 1; A-FURN deny_listed 4; A-EQPM and model "0" not_allow_listed; exact A-WALL report row; sparse |
| f2 nested | 6 lines + LOOP line at by-hand coordinates; 3 arcs on their circles (r 10, 5, 10); A-EQPM 22 and 08-COLUMN 4 not_allow_listed; 06-WALL 55 kept all via INSERT; self_inserts 1, depth_capped 1; `thick` holds through the chain; equals ezdxf's explosion |
| f3 states | kept 3; layer_off/frozen/no_plot, DEFPOINTS no_plot, B0 on a frozen layer (layer_frozen + insert_layer_frozen), B0 on an off layer (layer_off + insert_layer_off); columns: the off-layer column dropped |
| f4 invisible | invisible 1, insert_invisible 1, kept 2 |
| f5 twisted viewport | A-PARTITION viewport_frozen only for the 30 deg viewport; coordinates identical with and without the viewport; report carries twist 30 and frozen list; bad handle -> ValueError |
| f6 bound xref | layer "0" in `X-ARCH$0$BAS4- SERV` -> `X-ARCH$0$06-WALL`; `X-FIRE ALARM$0$06-WALL` kept (deny words only in the prefix); PARKING deny_listed; A-NORTH frozen; bounds 248 m (raw-layer rule: 8 m, below 200 m, no bounds) |
| f7 deny list | false negatives 02-CAB, 21-HIDDEN, 41-ELE-5, -Ext, 55-RAMP, 23-WALL-TILES now not_allow_listed; false positives A-WALL-WING, STOREROOM-PARTITION, CARGO-WALL stay deny_listed under NOT_WALLS and are kept with a word-bounded per-build deny; per-build allow `WALL|HIDDEN` |

## Golden GC-01 (`60de2a377daa.dxf`, read only; `gc01-composition.json`, `gc01-vs-rd-m1.json`)

- v1 (E10): 92,093 segments kept. ezdxf `recursive_decompose` with the v1 rule reproduces 92,093 exactly. M8: **16,645
  kept, 32,625 m** (06-WALL xref 10,567; 11-GLASS-1 3,636; 10-SILL 1,176; 31-PARAPET-WALL 535; 12-GLASS-2 402;
  S-RETAINING-WALL 234; top-level 06-WALL 95). Not sparse. Build 31 s without detail.
- Out now: raw "0" (E10 28,491), resolved by inheritance to 17-FIXTURE 5,268, 32-RAILING 4,368, 29-PARKING 6,464
  (deny_listed or invisible), furniture 4,760, -XREF 2,574, 49-DOOR-TAG 1,221... (only 31-PARAPET-WALL 435 and
  06-WALL stay); 02-CAB 17,776, -Ext/Ext,
  41-ELE-5, 21-HIDDEN, 08-COLUMN, 55-RAMP, 17-FIXTURE, A-STOPPER, 23-WALL-TILES (not_allow_listed); the frozen
  `X-REF_PLOT$0$A-NORTH` (342, layer_frozen, as E10 flagged); invisible 11,431 + insert_invisible 11,692 (under the v1
  rule the invisible count is exactly F005's 4,351).
- 06-WALL xref rises 9,461 -> 10,567 (layer-"0" content inheriting it, E11's `BAS4- SERV` case); 11-GLASS-1 falls
  3,948 -> 3,636 (312 invisible).
- E11: all 22 probe segments match E11's effective layer; the "invisible rectangle" lines are 29-PARKING
  (deny_listed or invisible), no longer walls.
- The v1 rule re-applied to the M8 walk gives 94,008, not 92,093: (a) v1's explosion turned 180 LEADER segments
  (5 leaders x 18 inserts of `X-REF_PLOT`) into lines, M8 reads only line primitives; (b) wide polylines: v1's
  `make_primitive` indexed the outline of a polyline's width (a zigzag), M8 its centre line (layers "0", -Ext, Ext,
  33-PLOT).
- New false positive found: 72 segments of the title-frame block `T.FRAM` are drawn on "0" and
  inserted on the CCSD file's own layer `06-WALL`, so they inherit a wall layer and are kept. AutoCAD shows them on
  06-WALL too; no rule here removes them. Engineer/owner decision (block-name deny or per-project list).
  **Correction (ORCH-044, from ORCH-042 U2M8V-01):** the 72 segments total **7,733.5 m** (23.7 % of the 32,625 m
  kept), not "119.8 m": 119.83 m is one horizontal edge (36 such edges, plus 36 vertical edges of 94.98 m).
  Same class, smaller: 4 segments (13.9 m) of `X-REF_ DIM_TEXT`'s layer-"0" content on 06-WALL.
- Named-boundary index: base 40,427 m -> M8 43,457 m (deduplicated), 338 columns both, build 73.1 s -> 13.6 s (the
  run's own `gc01-vs-rd-m1.json`; "87 s -> 17 s" earlier in this report was wrong, U2M8V-08).
  **Correction (ORCH-044):** the whole rise is title-frame lines and more: the T.FRAM segments are boundaries too,
  **72 segments, 7,733.5 m** after deduplication (36 horizontal edges of 119.83 m = 4,314.1 m, which ORCH-042
  counted, and 36 vertical edges of 94.98 m = 3,419.4 m, which it did not). Without them this index held
  **35,723.1 m**, 4,703.7 m less than the base, not more. The M8 walk itself (effective layer, visibility) lowered
  the boundaries; the frame lines alone made the total look higher. Measured by ORCH-044
  (`evidence/exit-fixes/gc01-exit-fixes.json`, `bounds.attribution_dedup_m`).
  `X-REF_ TAG$0$49-DOOR-TAG` (502 m) still counts as a boundary because the unchanged `BOUND_LAYERS` matches DOOR
  and `NOT_BOUNDS` lacks TAG: pre-existing, left for a later M8 stage.

## Rotated view (F021)

The twisted-viewport fixture proves the index stays in model coordinates and honours the viewport's frozen layers;
the report records the twist. Not changed: the plot-to-model fit (`review/geometry.py fit`) still has no rotation
term, and nothing in redesign reads `Window.twist`. F021 remains open.

## Decisions to review

1. ORCH-036 item 3 rule applied: an INSERT on an off or no-plot layer hides its whole content. AutoCAD hides only
   the inherited ("0") content in that case (frozen hides all). Stricter here; one-line change if the owner prefers
   AutoCAD's rule.
2. Filters match the layer's own name (xref prefix stripped), so `X-FIRE ALARM$0$06-WALL` is a wall and an
   xref name like `BAS 3-2-1 - COL` no longer makes every layer in it a column layer.
3. TILE/FINISH excluded inside the default allow-list (GC-01 `23-WALL-TILES`).
4. Arcs added to the wall kinds; polyface/polygon meshes no longer read as lines.
5. Sparse threshold 200 m of kept wall (as `MIN_BOUNDS_M`); a sparse index never measures coverage.

## Runs

- Targeted (`targeted.xml`, `targeted.log`): new file + test_redesign, test_drawing_prep, test_fa_interfaces,
  test_fa_cases, test_fa_evidence, test_fa_review_fixes, test_ifc_boq, test_render_bounds: **211 passed, 1 skipped**
  (pre-existing: no DWG converter), 337 s.
- Full suite (`full-suite.xml`, `full-suite.log`, `full-suite-vs-baseline.json`): **1796 passed, 1 failed, 35 skipped** (1832), 1936 s, 2026-10-07T21:34:39Z-22:07:09Z. Baseline (M4 windows run2): 1782 passed, 2 failed, 35 skipped (1819). Differences by name and message: newly failing none; failing in both with the same message `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it`; baseline failure now passing `test_persistence::test_a_data_root_gathers_the_database_uploads_backups_and_caches` (it asserts the default data root is None, so it depends on the shell environment -- most likely a data-root variable set in the baseline shell; this change does not touch persistence); 13 new tests (this file); no skip changes; none removed.

## Engineer decisions applied (A-16)

The engineer's decision sheet (`M8-ENGINEER-DECISIONS-2026-10-08.md`, answered by the owner on 8 October 2026,
register A-16) was implemented by ORCH-044 on `task/m8-exit-fixes` (worktree `wt-m8b`, from `roadmap/u2` at
`1708692`). Full detail, numbers and runs: `M8-EXIT-FIXES-IMPLEMENTATION.md`.

| # | Decision | Change | Test |
|---|---|---|---|
| 1 | B: default-deny `T\.FRAM\|TITLE\|FRAME\|BORDER\|SHEET` block names in the INSERT chain; DIM_TEXT-class inherited content too | `layers.FrameRule`, `settings.prep_frame_blocks` (beside `prep_wall_layers`), `walls.build(deny_blocks=, annotation_blocks=)`, `coverage.build_columns` same; reason `title_frame` | f8; GC-01 golden |
| 2 | B: AutoCAD rule (off / no-plot hides inherited "0" content only; frozen hides all) | `layers.walk` | f3, f6 (updated, cited), f11 |
| 3 | A + C: 200 m kept; `$INSUNITS` -> metres before the threshold and the report; unknown unit held | `layers.drawing_units`, `walls.build`, `Walls.held`, `coverage.build_columns`, `prepare.rooms/gate` | u1..u4 |
| 4 | C: MLINE not read; `mline_unsupported` in the report and the gate | `walls.build`, `Walls.held`, `prepare.rooms/index_state/gate` | f9 |
| 5 | B: TAG in `NOT_BOUNDS` | `coverage.NOT_BOUNDS` | regex test; GC-01 golden |
| 6 | A: rotation term in the plot-to-model tie; viewport passed | `review/geometry.py fit/to_model/to_page/sheet_view/fit_sheets`; `service._page`, `service._index_viewport`, `service._walls(sheets=)` | f12 end to end; synthetic pages |
| 7 | arcs candidates; meshes not read, counted (`mesh_not_read`) | `walls.build`, `coverage.build_columns`, `layers.is_mesh` | f10 |
| 8 | A: allow-list regex unchanged | none | pin test |

## Limitations

- No per-project allow-list store (only the `allow`/`deny` arguments); no database field.
- Placement, coordination, label anchoring and the interface fallback chain untouched (later M8 stages); nothing
  anchors equipment to labels.
- Real AutoCAD not exercised: fixtures are ezdxf-built; layer/VPLAYER semantics follow the DXF reference.
- `service.py` builds the model-space index only; nothing passes `viewport` yet.
- GC-01 exists only on the owner's machine; elsewhere the Golden test skips.
