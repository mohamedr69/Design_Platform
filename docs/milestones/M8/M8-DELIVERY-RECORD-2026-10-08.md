# M8 Deterministic Geometry, Placement & Coordination, first bounded task (wall index): delivery and acceptance record

Prepared 8 October 2026 by ep-scribe, per `docs/UNIFIED_MASTER_ROADMAP.md` section 13. Branch `roadmap/u2`.

**Status:** M8 (wall index, first bounded task): implemented / partial; independently verified PASS WITH CONDITIONS; not accepted (title-frame deny rule, owner/engineer decisions on the off-layer INSERT rule, sparse threshold and units, MLINE, F021 rotation term, later M8 stages and real-AutoCAD confirmation outstanding)

This record states only what its inputs contain. It grants no acceptance and no deployment. Only the first bounded task of M8 (the wall-index paragraph, UMR section 8) is covered; the later M8 stages are not started.

## 1. Inputs (sha256)

| File | sha256 |
|---|---|
| `docs/UNIFIED_MASTER_ROADMAP.md` section 8 M8, sections 3 and 13 | read at HEAD (no hash taken) |
| `docs/milestones/M3/M3-POLICY-CONTRACT-DRAFT.md` (P-07, P-17, Part C row C-4) | read at HEAD (no hash taken) |
| `docs/milestones/M8/M8-WALL-INDEX-IMPLEMENTATION.md` | `3b066074a24930ca32d98d053e856bc1886b6fbc9d0e06ae9194e110c7b9163c` (equals the manifest's `report`) |
| `docs/milestones/M8/evidence/wall-index/MANIFEST.json` | not hashed by the scribe; it lists 28 hashes (section 4) |
| `.../orchestrator/surveys/U2-M8-WALL-INDEX-SURVEY.md` | `98e9e7966cdcbaa3eb50e0c92ae68e4b04692e2d1a299d9f9cc6ba0d828ea97a` |
| `.../reviews/U2-M8-verify/INDEPENDENT-VERIFICATION.md` (ORCH-042) | `ba03fdd40080c3cfbfded1f9b9d0c0b9bceb599b4f9ee6e738453f780b7668ed` |
| `.../reviews/U2-M8-verify/FINDINGS.json` | `1f8c5f6a2dd5f6c391123a97f062e0d59881db8e4b3dc0bc58631ee2e0e8a8f4` |

Folder prefix: `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/` (`orchestrator/surveys/`, `reviews/U2-M8-verify/`).

## 2. Governing text

- Roadmap section 8 M8 paragraph: effective layer inheritance, block transforms, visibility/off/frozen/no-plot handling including viewport state, configurable wall-layer allow-lists and layer composition reporting; validate a simple sheet and a rotated view as well as the exposed Golden drawing.
- Roadmap M8 exit: no placement justified by invisible/non-wall geometry; accepted cases have valid transforms, containment and clearance; known failures improve without new critical clashes. Unresolved geometry remains held.
- Section 3 finding: the active wall builder used raw-layer deny-list filtering; wall and column indexes are cached pickles keyed by source hash and a `VERSION` constant (RC-06).
- M3 P-07 (unknown is never complete) and P-17 (geometry checks are authoritative). Part C row C-4: PREP walls_index and columns_index are preparation results, owned under D-04 (owner mohamedr69, confirmed as inherited 2026-10-07).

## 3. Requirement, implementation, gap, action, evidence

| Requirement | Current implementation (ORCH-036) | Remaining gap | Action | Acceptance evidence |
|---|---|---|---|---|
| Effective layer, nested INSERTs | `backend/app/redesign/layers.py` (new): layer "0" takes its INSERT's effective layer, recursively; xref prefix stripped | none recorded for the walker | none | Tests f2, f3, f6; GC-01: 22/22 E11 probe segments match (reproduced by ORCH-042) |
| Block transforms | `chain_matrix` in `app/ifc/dxf/geometry.py`, shared with `interfaces/geometry.py`; depth cap 16, self-insert guard, MINSERT expanded | none recorded | none | f2 by-hand affine maths; `symbols_near` output byte-identical to base on 7 fixtures (ORCH-042) |
| Visibility: off, frozen, no-plot, DEFPOINTS, entity invisible, viewport frozen list | `LayerTable.hidden`, entity `invisible`, `insert_*` reasons, VIEWPORT `frozen_layers` | Off/no-plot INSERT hides all its content (stricter than AutoCAD, which hides only the inherited "0" content); `service.py` passes no viewport | Owner/engineer decision on the off-layer INSERT rule; viewport hand-off from `service.py` | f3, f4, f5; 0 GC-01 segments affected by the stricter rule (U2M8V-06) |
| Configurable wall-layer allow-list, deny-list second, same rules for columns and bounds | `prep_wall_layers` in `core/config.py`; `walls.build(..., allow=, deny=, viewport=)`; `coverage.build_columns` uses the same walk | No per-project allow-list store | Later M8 stage | f1, f6, f7 |
| Composition report; sparse/empty = not measured | Report in the pickle and on `Walls.report`; `Walls.sparse` (under 200 m kept); `room_at` returns None for a sparse index; issue "sparse/missing ... not measured" | Sparse threshold value and unit assumption (metres) | Engineer decision (U2M8V-10) | sparse test; P-07 behaviour confirmed by ORCH-042 |
| Cache | `walls.VERSION` 1 to 2; rule fingerprint in the file name; old pickle refused; `coverage.VERSION` 2 to 3 | none | none | cache test; mutation killed (ORCH-042) |
| Rotated view | Twisted (30 deg) viewport fixture: index stays in model coordinates, viewport frozen layers honoured, twist reported | `review/geometry.py fit` has no rotation term; nothing in redesign reads `Window.twist`; F021 open | Add the rotation term to the plot-to-model tie | f5; U2M8V-07. Exit condition only partly covered |
| Title-frame and non-wall blocks | None | T.FRAM frame lines kept as walls and as boundaries (U2M8V-01, Medium) | Default deny for title/frame/border blocks, configurable, applied to walls and boundaries, with a fixture; exact rule is an owner/engineer decision | Open. ORCH-044 issued, not yet run |
| Exit: no placement justified by invisible/non-wall geometry | Invisible and hidden geometry removed from the index | Title-frame lines still count; later M8 stages (doors, ceilings, obstacles, containment, rotation, spacing, coverage, post-change clash checks) not started | See section 8 | Open |
| Preserve existing behaviour | `Walls` tuples and methods unchanged; `service.py` not edited | none | none | `test_redesign.py` and `test_drawing_prep.py` (30 tests) pass unchanged |

## 4. Exact code and artifact snapshot

- Branch `task/m8-wall-index`, worktree `wt-m8`, based on `roadmap/u2` at `5270773a469e31f5cad0b7d7a170e168a1d918ba` (backend equal to `668f92f`; only docs differ).
- Commits: source `3317b8814f96949eafd3fa89e3be3045df51b149`; evidence `f7e3f621fb9fc906deeaa8a31ccb125a8498d63f`; logs `4165a435fd42687e296435c5cc1e3566bc2cbd85` (head verified by ORCH-042; adds the run logs the manifest lists, as `*.log` is git-ignored).
- Environment: Python 3.12.10, ezdxf 1.4.4, Windows-10-10.0.19045-SP0, the live clone's venv with `python -B`; no provider, no network, no AutoCAD, no live application. Run window 2026-10-07T20:51:47Z to 22:10:32Z.
- Golden input (read-only): `G:\dev (2)\dev\ep-platform-merged\data\uploads\EP-30880\ifc\60de2a377daa.dxf`, sha256 `dbe7900f21033b2a9c5d3379c93cbf56250735143f8a424559b09a9d4ee5c14f`. Present only on the owner's machine.
- Changed source (sha256 of the Windows autocrlf checkout, per the manifest):

| File | sha256 |
|---|---|
| `backend/app/core/config.py` | `bbc33eaf935e6f8a39d82fd6d9ce5af7a43765a6d220c9de9b313e683991f127` |
| `backend/app/ifc/dxf/geometry.py` | `b28496ae36f14751f014aa03d3f05834a42054b1817801b09a2c9f278b469fe0` |
| `backend/app/interfaces/geometry.py` | `aca8eea13796c37e946b2cc2453e5837e269b745b2cdbf51762e4f6b9194cff1` |
| `backend/app/redesign/coverage.py` | `07b835380fd6a76a0243eb08e6605724edc3d660010e35b9609abbfc2baa8b36` |
| `backend/app/redesign/layers.py` | `854e32d69b55225401ba20ffb1e6a71f0ac323d44820dcf64faba53ea5801e2a` |
| `backend/app/redesign/prepare.py` | `95a922a4229615c23c917828ec192224bbe2d7dd3e99b4fb43f4a77638403000` |
| `backend/app/redesign/walls.py` | `44cabb4b69ae1f48d9a749a350e1f2607b8b229c2182315da5fc1490d6d7f302` |
| `backend/tests/test_redesign_walls_layers.py` | `3829b74b444950cd05475049920b66fbaf806e4927f056d7f872ad7db33072f9` |
| `backend/tests/fixtures_m8/make_fixtures.py` | `269c8b26508c5a9d332d420aeb852d82b607da8ccf91dfb0222a76d899bd746b` |
| `backend/tests/fixtures_m8/f1_simple.dxf` | `5edb0da66f0ffabb87ba3e1f44322d4364a67442c09bb026b4cb0031eb139cc0` |
| `.../f2_nested.dxf` | `90ac76080fee436e9135db7cd4e73c1f579de714b0c2a7c0f6f3dd1ef6e6d229` |
| `.../f3_states.dxf` | `87c2705d98ae367f96dd71a7883cd9e9b465efc9a13596454b9f3aa6aaeca2ef` |
| `.../f4_invisible.dxf` | `958798ca387720fce224b66559b79432f2cee2d730f8309e1c863ec7e43a4099` |
| `.../f5_viewport.dxf` | `2c7939c95ee887c7684800a0ff39f79cb47aa665c41d1dbdcdbd54dbcd2606b2` |
| `.../f6_xref.dxf` | `83099f422d312d60cefc55ef0352ba03a35dd5ea15dc76811b038d283e63eb80` |
| `.../f7_denylist.dxf` | `1b62e86065f2bacb050298c0bd7dffb2d57a3b57422c83b4630ffe79314474c4` |

- Evidence hashes (full list in `MANIFEST.json`): `full-suite.xml` `6ff67797047cd1e0f096b12408cb167ca50523b55d3657345f997cbce0cf8f97`; `full-suite.log` `ea5f74a17c745d7ff61008843e419b99459305cf4c0bd80716cf76db53031cd2`; `full-suite-vs-baseline.json` `4f678c4041c0f38b71168c08de4a8b001a746669d3d3bf3a8f8a05c5ad29c715`; `targeted.xml` `bc615abd31e00ec79ff54b7bb70d37b014e55289e0d384c87ae6b0c5b7d7e03b`; `targeted.log` `77b0bc9fd5a17548485bce3a023f8c4cc25b8f21f034e1429c96728bff04382e`; `gc01-composition.json` `307eb50c52418a2aa08eacff95c00b82896d144236ebdfbcfb5549ece4039789`; `gc01-vs-rd-m1.json` `fe108cbe8b8a91961c320a574eaa25d18e52c4f1fe53d143cd97cb1b6b5b1396`; `gc01-run.log` `0e25e6558ba37a6739133d6e4246c8c1e836f16ce0599384be9ae1b5d06d7169`.
- Hash caveat (U2M8V-02, Low): 10 of the 28 manifest hashes (`config.py`, `ifc/dxf/geometry.py`, `interfaces/geometry.py` and the seven fixture DXFs) are CRLF hashes from the autocrlf checkout; each equals its LF blob converted LF to CRLF. The 18 others equal the committed blobs. A checkout with autocrlf false, or on Linux, will not reproduce those 10.
- Model, profile, schema and policy versions: none apply (no model call). Cache versions: walls `VERSION` 2, columns `VERSION` 3; allow-list default `prep_wall_layers = ^(?!.*(?:TILE|FINISH)).*(?:WALL|PARTITION|CURTAIN|GLASS|GLAZ|SILL)`, case-insensitive, matched on the layer's own name.

## 5. Tests and results

A passing suite is evidence, not acceptance. The three kinds of evidence are kept apart.

### 5a. Functional / mocked (synthetic ezdxf fixtures; no AutoCAD)

| Run | Result |
|---|---|
| New file `tests/test_redesign_walls_layers.py` (13 new tests) on fixtures f1..f7 | Pass (report) |
| Targeted set (new file, `test_redesign`, `test_drawing_prep`, `test_fa_interfaces`, `test_fa_cases`, `test_fa_evidence`, `test_fa_review_fixes`, `test_ifc_boq`, `test_render_bounds`), implementer | 211 passed, 1 skipped (no DWG converter), 337 s |
| Full suite, implementer, 2026-10-07T21:34:39Z to 22:07:09Z | 1,796 passed, 1 failed, 35 skipped (1,832 collected), 1,936 s |
| Baseline (M4 windows run2) | 1,782 passed, 2 failed, 35 skipped (1,819) |
| Against baseline, by name and message | No new failures; 13 new tests; 0 removed; no skip changes. The failure in both: `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` (same message). `test_persistence::test_a_data_root_gathers_the_database_uploads_backups_and_caches` failed in the baseline and passes now. |
| ORCH-042 targeted rerun from a byte copy | 212 tests, 211 passed, 1 skipped; the GC-01 golden test ran (50.8 s) |
| ORCH-042 full suite from a byte copy | 1,832 tests, 1,796 passed, 1 failed, 35 skipped, 2,521 s; outcomes identical to the implementer's `full-suite.xml` for every test |
| ORCH-042 mutations (viewport-frozen check off; invisible flag dropped; fingerprint removed from the cache key; old pickle accepted; self-insert guard off; no layer-0 inheritance; columns/bounds ignore visibility) | All killed; after restore, byte-identical and green |
| ORCH-042 dry merge into `roadmap/u2` (scratch clone): walls_layers, redesign, drawing_prep, redesign_apply, prep_readiness | 106 passed, 0 failed |

Persistence explanation (U2M8V-08): the implementer's report says the baseline persistence failure was "most likely a data-root variable set in the baseline shell". ORCH-042 records the documented cause as the baseline run collecting the pre-repair test source (before d47fa70, which added `_env_file=None`) with the live `backend/.env` setting DATA_ROOT (`docs/milestones/M4/evidence/tests-2026-10-07-windows-run2/ADDENDUM-persistence-at-5da743d.md`). It is not M8 code. This record adopts the ORCH-042 account.

### 5b. Deterministic Golden GC-01 (owner's DXF, read only; no AutoCAD)

| Item | Result |
|---|---|
| v1 base code (5270773 `walls.build`, run as-is by ORCH-042) | 92,093 segments (unique 90,302); raw layer "0" 28,491; invisible flag 4,351 (equals E10/F005) |
| M8 | 16,645 kept, 32,624.974 m (report: 32,625 m); not sparse. Excluded: invisible 11,431; insert_invisible 11,692; `X-REF_PLOT$0$A-NORTH` layer_frozen 342; 02-CAB 17,776 (not_allow_listed) |
| Raw "0" lines resolve to | 17-FIXTURE 5,268; 32-RAILING 4,368; 29-PARKING 3,271 deny_listed plus 3,193 invisible; and so on |
| E11 probes | 22/22 match (report and ORCH-042) |
| Named-boundary index | base 40,426.718 m; M8 43,456.556 m; 338/338 columns |
| ORCH-042 per-layer report | 145 layers; totals, walk and rules equal to the committed `gc01-composition.json` |
| Deviations from v1 rated by ORCH-042 | LEADER segments not read (180 in v1): correct, no effect on the kept set; wide polylines read as centre lines: correct, GC-01 unaffected |

Build times: the report gives the boundary build as 87 s to 17 s, but its own `gc01-vs-rd-m1.json` and `gc01-run.log` say 73.1 s to 13.6 s (ORCH-042 under load: 131.0 s to 32.8 s; the direction holds) (U2M8V-08).

### 5c. Real AutoCAD

None. No real-AutoCAD run exists for M8. Fixtures are ezdxf-built; layer and VPLAYER semantics follow the DXF reference and were not exercised in AutoCAD.

## 6. Corrections to the implementation report (recorded here; the report itself is not edited)

Both come from ORCH-042 (U2M8V-01) and apply to `docs/milestones/M8/M8-WALL-INDEX-IMPLEMENTATION.md`:

1. **T.FRAM length.** The report says "72 segments (119.8 m lines)". 119.83 m is the length of each frame edge, not the total. The 72 segments total 7,733.5 m, 23.7 % of the 32,625 m kept. All are LINEs on layer 0 inside `CCSD > X-REF_ FILE ALL FLOORS PLANS$0$T.FRAM`, inheriting 06-WALL. Also 4 DIM_TEXT segments (13.9 m) on 06-WALL.
2. **Boundary-index gain.** The report presents 40,427 m to 43,457 m. The whole increase is frame lines: 36 distinct 119.83 m horizontal frame edges, 4,314.1 m, are boundaries under M8 and none were in the base. Without them M8 holds 39,142 m, 1,284 m less than the base. Because `room_at` prefers the bounds index, a room touching a frame edge can be closed by a title frame, which conflicts with the M8 exit.

## 7. Independent review disposition

ORCH-042 (ep-verifier, Claude Opus 5.5, fresh and read-only; 8 October 2026): **PASS WITH CONDITIONS**. Counts: Blocker 0, Major 0, Medium 1, Low 4, Info 6. Fit to merge into `roadmap/u2`: yes. U2M8V-01 must be closed before the M8 exit, not before the merge.

| ID | Severity | Subject | Disposition |
|---|---|---|---|
| U2M8V-01 | Medium | T.FRAM title-frame false positive larger than reported; reaches the boundary index | Open condition for the M8 exit; deny rule pending decision; ORCH-044 |
| U2M8V-02 | Low | 10 manifest hashes are autocrlf (CRLF) hashes | Open; record blob ids or mark the fixture DXFs `-text` |
| U2M8V-03 | Low | Fixture script byte-identical only for some PYTHONHASHSEED values (0,1,2,3,5,6,8,9,11,12,13 give the committed bytes; 4,7,10 swap two CLASSES entries; geometry identical) | Open; run with PYTHONHASHSEED=0 or compare semantically |
| U2M8V-04 | Low | No test discriminates visibility in the boundary index (the f6 assertion is vacuous) | Open; add a hidden 06-WALL boundary to f6 or f3 |
| U2M8V-05 | Low | MLINE walls no longer read (GC-01: 0 MLINE) | Open; engineer decision |
| U2M8V-06 | Info | Off/no-plot INSERT hides all its content | Owner/engineer decision |
| U2M8V-07 | Info | F021: no rotation term in `fit`; rotated-view exit partly covered | Open |
| U2M8V-08 | Info | Build-time figure and persistence explanation in the report | Corrected in section 5 |
| U2M8V-09 | Info | Merge conflicts only in `.gitattributes` | Resolved at merge (section 9) |
| U2M8V-10 | Info | Sparse threshold and report lengths assume metre units | Engineer decision with the threshold |
| U2M8V-11 | Info | One verifier `git merge-tree` wrote unreferenced loose objects to the shared object store of `ep-platform/.git` | Disclosed; harmless, garbage-collectable |

ORCH-042 ratings of the judgement calls: TILE/FINISH exclusion, polyface/mesh no longer read, and the column regex on the layer's own name are correct; arcs as wall candidates and NOT_WALLS on the layer's own name are acceptable; the off-layer INSERT rule is acceptable now but needs a decision; the 200 m sparse threshold is acceptable but needs a decision on value and units.

Not independent: the M8 survey (the card's source) and the implementation report are inputs, not reviews.

## 8. Decisions and work still required

Owner/engineer decisions:
1. The title/frame/border block deny rule (ORCH-042 suggests a configurable default such as `T\.FRAM|TITLE|FRAME|BORDER|SHEET` applied to the wall and boundary indexes; the exact rule is theirs to approve).
2. The off-layer INSERT rule: keep the stricter rule (hide all content) or adopt AutoCAD's (hide inherited "0" content only for off/no-plot; one-line change per the report).
3. The sparse threshold value (200 m) and the drawing-unit assumption.
4. Whether MLINE walls are expected in the firm's drawings.

Work remaining (not decisions):
- ORCH-044 exit-fixes task: issued, not yet run.
- F021: rotation term in the plot-to-model tie; pass the viewport from `service.py`.
- Per-project allow-list store (none exists; only the `allow`/`deny` arguments).
- Pre-existing `X-REF_ TAG$0$49-DOOR-TAG` boundary (502 m): `BOUND_LAYERS` matches DOOR and `NOT_BOUNDS` lacks TAG.
- Later M8 stages: doors, ceilings, obstacles, containment, rotation, spacing, coverage, post-change clash checks; reuse interface physical-symbol associations; do not anchor equipment to labels.
- Real-AutoCAD confirmation of the visibility semantics.
- Fixes for U2M8V-02..04.

## 9. Integration status, retention, rollback, limitations

- **Integration:** merged into `roadmap/u2` as merge commit `f95a3f412f6a04fc2801737cf8a58a12fa6a7db0` on 2026-10-08 (parents `50b55e57f3701cc68cc767a571f2047fe34acf5c` and `4165a435fd42687e296435c5cc1e3566bc2cbd85`). The `.gitattributes` conflict was resolved by keeping both evidence blocks (M5 and M8). At the time of writing `roadmap/u2` was at `fd6ae22` (session log). **Not merged into the platform branch. Not accepted.**
- **Retention:** report and evidence are under `docs/milestones/M8/` (13 tracked files). Branch `task/m8-wall-index` and worktree `wt-m8` remain. Verification outputs sit in the folder prefix of section 1; ORCH-042 scratch was under `C:/t/tmp/m8v`. GC-01 DXF stays on the owner's machine and was only read; pickles went to `C:/t/tmp/m8` and `C:/t/tmp/m8v/gc`.
- **Rollback:** revert merge `f95a3f4` on `roadmap/u2` (`git revert -m 1 f95a3f4`); the platform branch holds no M8 code. Old v1 pickles are refused by the new loader and are rebuilt on use; no migration or database field was added, so no data rollback is needed.
- **Known limitations:** synthetic fixtures only; no real-AutoCAD run; the Golden test skips off the owner's machine; `service.py` builds the model-space index only and passes no viewport; no per-project allow-list store; placement, coordination, label anchoring and the interface fallback chain untouched; title-frame lines are still kept (U2M8V-01); MLINE not read; the sparse threshold assumes metres.
