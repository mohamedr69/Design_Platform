# M8 wall index: engineer decision sheet (A-14 item 8)

Date: 8 October 2026. Role: ep-scribe. Status: **OPEN. No decision below has been made.** The owner ruled (authority A-14 item 8) that these wall-index decisions need an engineer; the AI identifies and surfaces them and does not decide them. Every "current" rule is a **temporary default, engineer decision pending**.

How to answer: tick one box per item and sign the last line of the item. Where an item has "Other", write the rule in the space.

## Where the numbers come from

All numbers are copied from the files below. This sheet adds no new measurement. Where an input does not give a number, the item says so.

| Short name | File |
|---|---|
| Verification | `MR/reviews/U2-M8-verify/INDEPENDENT-VERIFICATION.md` and `FINDINGS.json` (U2M8V-01..11), ORCH-042 |
| Implementation | `docs/milestones/M8/M8-WALL-INDEX-IMPLEMENTATION.md` (ORCH-036) |
| Composition | `docs/milestones/M8/evidence/wall-index/gc01-composition.json` |
| Compare | `docs/milestones/M8/evidence/wall-index/gc01-vs-rd-m1.json` |
| Delivery record | `docs/milestones/M8/M8-DELIVERY-RECORD-2026-10-08.md` |
| Survey | `MR/orchestrator/surveys/U2-M8-WALL-INDEX-SURVEY.md` |
| Roadmap | `docs/UNIFIED_MASTER_ROADMAP.md`, section 8, M8 (line 408 onward) |
| M3 | `docs/milestones/M3/M3-POLICY-CONTRACT-DRAFT.md` |

`MR` = `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap`.

Subject drawing: Golden Case GC-01 (the owner's DXF for EP-30880, sha256 `dbe7900f…`). Results are deterministic and come from the DXF only; real AutoCAD was not run (Verification, "Separate statements").

**The two clauses that apply to every item** (M3, `M3-POLICY-CONTRACT-DRAFT.md`):
- **P-07** (line 63): "Unknown is never complete." Missing input is reported as such, never as compliant or complete.
- **P-17** (line 121): validators and geometry checks are authoritative; AI may only propose and cannot override a failed check.

**The roadmap M8 exit** (Roadmap, M8): "no placement justified by invisible/non-wall geometry; accepted cases have valid transforms, containment and clearance; known failures improve without new critical clashes. Unresolved geometry remains held."

**GC-01 headline for the current rules** (Composition `report.totals`): 1,338,010 segments walked; **16,645 kept, 32,624.974 m**; not sparse. Excluded: below_min_length 1,195,138; deny_listed 34,865; insert_invisible 11,692; invisible 11,431; layer_frozen 342; not_allow_listed 67,897. Boundary index: base 40,426.718 m, now 43,456.556 m (deduplicated); 338 columns in both (Compare `columns_index`).

---

## 1. Title, frame and border geometry: which words and which names count

**Question in plain words.** The title block of the sheet is drawn as lines on layer "0" inside a block that was placed on a wall layer, so the lines inherit "wall" and are counted as walls and as room boundaries. Which block names and layer names should be treated as title, frame or border and thrown out, before a room is closed or a wall is measured?

**Current (temporary default, engineer decision pending).** No title/frame rule exists. The default deny word list (`GRID|AXIS|DIM|TEXT|NAME|ANNO|TAG|FURN|CAR|PARK|SYMBOL|FIRE|ALARM|SPK|SPEAKER|LIGHT|\bEM\b|-EM|EXIT|SIGN|DOOR|WIN|TITLE|LEVEL|ROOM|HATCH|ARROW|STAIR`, Composition `rules.deny`) is matched on the layer's own name only, and the frame block's name is not tested at all (Verification U2M8V-01).

**Options.**
- [ ] A. No change. Title-frame lines stay in both indexes.
- [ ] B. Default deny on block names in the INSERT chain, as suggested by the verifier: `T\.FRAM|TITLE|FRAME|BORDER|SHEET` (Verification and Delivery record section 8, item 1 suggest `T\.FRAM|TITLE|FRAME|BORDER|SHEET`; ORCH-044 fix 1 also names `TBLK`). Applied to the wall index and the boundary index, overridable per build.
- [ ] C. B plus layer names (for example any layer whose own name contains TITLE, FRAME, BORDER or SHEET).
- [ ] D. Other word list / other names: ______________________________________________

Also decide: does DIM_TEXT-class content inherited onto a wall layer (4 segments, 13.9 m on 06-WALL) go to the same deny? [ ] yes  [ ] no

**GC-01 impact (numbers).**
- Wall index, `T.FRAM` block (inherits 06-WALL): **72 segments, 7,733.5 m**, which is 23.7 % of the 32,625 m kept (Verification U2M8V-01). Each frame edge is 119.83 m long; the Implementation report's "119.8 m" is one edge, not the total.
- Boundary index (the one `room_at` prefers): **36 distinct frame edges, 4,314.1 m**, against 0 in the base code. Without them the boundary total is 39,142 m, which is 1,284 m less than the base 40,427 m. The reported rise from 40,427 m to 43,457 m is entirely frame lines (Verification, rating of T.FRAM).
- `DIM_TEXT`: 4 segments, 13.9 m on 06-WALL (Verification U2M8V-01).
- If B or C is chosen, the expected kept wall total is 32,625 m minus 7,733.5 m and minus the DIM_TEXT length if ticked; the exact new totals are for ORCH-044 to recompute, not stated in the inputs.
- Not stated in the inputs: which other GC-01 blocks the words TITLE, FRAME, BORDER or SHEET would also catch. ORCH-044 fix 1 is told to list them.

**What the roadmap / M3 says.** Roadmap M8 exit: no placement justified by "invisible/non-wall geometry". Verification: a room touching a frame edge can be closed by a title frame, which conflicts with that exit. P-17: the geometry check is authoritative, so it must not be fed non-wall lines. The verifier rated it Medium and an open condition for the M8 exit, not for the merge.

Decision / signature / date: ______________________________________________

---

## 2. An INSERT placed on an off or no-plot layer: hide everything, or only what it inherits

**Question in plain words.** A block (INSERT) sits on a layer that is switched off or set not to plot. Do we hide every line inside the block, or only the lines inside it that are drawn on layer "0" (which take the block's layer)? AutoCAD hides only the inherited layer-"0" content for an off layer; a frozen layer hides everything.

**Options.**
- [ ] A. Hide all content of the INSERT (current: **temporary default, engineer decision pending**). Follows ORCH-036 item 3 literally.
- [ ] B. AutoCAD rule: hide only the inherited ("0") content for off and no-plot layers; frozen still hides all. The Implementation report calls this a one-line change.
- [ ] C. Other: ______________________________________________

**GC-01 impact (numbers).** Zero. The composition has no `insert_layer_off` and no `insert_layer_no_plot` segments in its totals (Verification U2M8V-06). The excluded reasons that do occur are `insert_invisible` 11,692 and `layer_frozen` 342; they do not depend on this choice. The effect of option B on other drawings is not measured in any input.

**What the roadmap / M3 says.** P-07: the stricter rule errs toward fewer walls, so toward "not measured". P-17: geometry checks should reflect what is plotted (Verification U2M8V-06, rated "acceptable now; owner/engineer decision for the final rule"). Real AutoCAD semantics were not exercised; the fixtures are synthetic.

Decision / signature / date: ______________________________________________

---

## 3. The sparse threshold (200 m) and its units

**Question in plain words.** If the index keeps less than a set length of wall, the drawing is treated as "wall index sparse, not measured" and no room is closed from it. Is 200 m the right value, and are drawing units to be taken as metres?

**Options.**
- [ ] A. Keep 200 m (current: **temporary default, engineer decision pending**; `MIN_WALLS_M` in `backend/app/redesign/walls.py:43`; same value as `MIN_BOUNDS_M`).
- [ ] B. Other value: ________ m
- [ ] C. Units: [ ] keep "drawing units are metres" (pre-existing assumption)  [ ] read the drawing's unit setting and convert  [ ] hold the drawing as "not measured" when units are not metres  [ ] other: ____________

**GC-01 impact (numbers).** GC-01 keeps 32,624.974 m, so any threshold up to that value leaves it "not sparse" (Composition `sparse: false`). The threshold changes no GC-01 result at 200 m. On a millimetre drawing the length would be counted in millimetres and a drawing would never be "sparse" (Verification U2M8V-10; the assumption also governs the existing 0.3 minimum length and 200 m minimum bounds). No input says how many project drawings are in non-metre units.

**What the roadmap / M3 says.** P-07: a sparse or empty index must read "not measured", never complete (the code does this, Verification check 2). The value and the units are not set by any roadmap or M3 clause; the verifier asks for an engineer decision (Verification, judgement-call table).

Decision / signature / date: ______________________________________________

---

## 4. MLINE walls: read them as walls, or report "not measured" with a reason

**Question in plain words.** Some drawers draw a wall as a multiline (MLINE). The old reader exploded MLINEs into lines; the new one does not read them. Do the firm's drawings use MLINE walls?

**Options.**
- [ ] A. Do not read MLINE; leave as is (current: **temporary default, engineer decision pending**). A drawing whose walls are MLINEs would build a sparse index and report "not measured", without a specific reason.
- [ ] B. Read MLINE walls as wall candidates on allow-listed layers (expand through `virtual_entities`), with a fixture.
- [ ] C. Do not read MLINE but report "not measured" with a specific reason `mline_unsupported` and a fixture that proves the reason is shown.
- [ ] D. Other: ______________________________________________

**GC-01 impact (numbers).** None. GC-01 has **0 MLINE** entities. For comparison, it has 115 LEADERs (none on an allow-listed layer) and 6 ACAD_TABLE entities on allow-listed layers (not walls). The 180 LEADER segments v1 exploded had no effect on the kept set (Verification U2M8V-05). The share of firm drawings that use MLINE is not in any input.

**What the roadmap / M3 says.** Roadmap M8 names no MLINE rule. P-07: option C is safe (unknown is reported as unknown); option A is safe but gives a less specific reason. Verification rates it Low and asks for this engineer decision.

Decision / signature / date: ______________________________________________

---

## 5. The pre-existing 49-DOOR-TAG boundary (about 502 m)

**Question in plain words.** The layer `X-REF_ TAG$0$49-DOOR-TAG` holds door-tag symbols. Because the boundary list matches the word DOOR and the exclusion list has no TAG, these tag lines count as room boundaries. Should tag layers be excluded from boundaries?

**Options.**
- [ ] A. Leave as is (current: **temporary default, engineer decision pending**). This is pre-existing, from the unchanged `BOUND_LAYERS` / `NOT_BOUNDS` (Implementation, Golden GC-01).
- [ ] B. Add TAG to the boundary exclusion list (`NOT_BOUNDS`).
- [ ] C. Exclude door layers from boundaries altogether, or only tag-class names: ______________________________________________
- [ ] D. Other: ______________________________________________

**GC-01 impact (numbers).** Boundary index: `X-REF_ TAG$0$49-DOOR-TAG` contributes **501.757 m** (Compare, `columns_index.m8.bounds_layers`, before deduplication; the composition's undeduplicated boundary total is 44,190.664 m). The same layer is already excluded from the wall index: 7,053 segments, 653.478 m walked, 0 kept (1,221 deny_listed, 5,832 below minimum length). In the same boundary list, door layers also contribute `14-DOOR` 8.177 m, `…$0$14-DOOR` 2,639.815 m, `…$0$DOOR` 23.792 m and `X-REF_LANDSCAPE$0$14-DOOR` 1.333 m; this sheet asks about the TAG layer only. The effect of option B on room closure in GC-01 is not measured.

**What the roadmap / M3 says.** Roadmap M8 exit: no placement justified by non-wall geometry. P-17: boundaries are authoritative inputs to room closure, so tag symbols should not be among them. The Delivery record (section 8) leaves it to a later M8 stage; ORCH-044 lists it among the "owner/engineer decisions" only.

Decision / signature / date: ______________________________________________

---

## 6. F021: a rotation term in the plot-to-model tie (rotated views)

**Question in plain words.** A sheet view can be rotated (twisted). The step that ties a point on the plotted sheet to a point in the model has no rotation term, so on a rotated view a placement can land in the wrong place. Add the rotation, and when?

**Options.**
- [ ] A. Add a rotation term to `review/geometry.py fit` (and pass the viewport from `service.py`) as part of M8, before the M8 exit.
- [ ] B. Keep as is for M8 and hold any rotated view as "not measured" until it is done.
- [ ] C. Defer to a later milestone: ______________________________________________
- [ ] D. Other: ______________________________________________

Current (**temporary default, engineer decision pending**): no rotation term, `fit` is X = a·x + bx, Y = −a·y + by (`backend/app/review/geometry.py:35-38`); `service.py` passes no viewport; the twist is only recorded in the report (Verification U2M8V-07).

**GC-01 impact (numbers).** The survey records that all GC-01 sheets fit without rotation, residual up to 0.55 m (Survey, "Rotated view"; F021). So GC-01 itself does not exercise the gap. The only rotated-view evidence is the synthetic 30 degree viewport fixture f5, which proves the index stays in model coordinates and honours the viewport's frozen layers; it does not test the plot-to-model tie.

**What the roadmap / M3 says.** Roadmap M8 asks to "validate a simple sheet and a rotated view as well as the exposed Golden drawing". Verification: the rotated-view exit condition is "only partly covered" and F021 stays open.

Decision / signature / date: ______________________________________________

---

## 7. Arcs as wall candidates; polyface and polygon meshes not read

**Question in plain words.** (a) Should arcs count as wall candidates (curved walls)? (b) The old reader turned polyface and polygon meshes into lines; the new one ignores them. Confirm or change.

**Options.**
- (a) Arcs: [ ] confirm: arcs are wall candidates (current: **temporary default, engineer decision pending**)  [ ] arcs are not wall candidates  [ ] other: ____________
- (b) Meshes: [ ] confirm: meshes are not read (current: **temporary default, engineer decision pending**)  [ ] read meshes as lines  [ ] other: ____________

**GC-01 impact (numbers).** The walk saw 52,823 ARC, 117,433 LINE, 101,974 LWPOLYLINE and 34 POLYLINE primitives (Composition `walk.kinds`). The inputs do not state how many of the kept 16,645 segments are arcs, nor how many mesh entities exist in GC-01, so the effect of either choice on the GC-01 totals is **not stated in the inputs**. Door swings stay denied by the DOOR word whatever is ticked (Verification judgement-call table).

**What the roadmap / M3 says.** Roadmap M8 asks for curved walls; the exit excludes "non-wall geometry". Verification rated both calls acceptable and correct respectively. Not a P-07 or P-17 matter beyond that.

Decision / signature / date: ______________________________________________

---

## 8. TILE and FINISH excluded inside the allow-list

**Question in plain words.** The allow-list accepts any layer with WALL, PARTITION, CURTAIN, GLASS, GLAZ or SILL in its name. The default removes names containing TILE or FINISH (such as `23-WALL-TILES`) even though they contain WALL. Confirm?

**Options.**
- [ ] A. Confirm: TILE and FINISH are excluded (current: **temporary default, engineer decision pending**; allow rule `^(?!.*(?:TILE|FINISH)).*(?:WALL|PARTITION|CURTAIN|GLASS|GLAZ|SILL)`).
- [ ] B. Include them (wall finishes count as walls).
- [ ] C. Change the word list: ______________________________________________

**GC-01 impact (numbers).** `X-REF_ FILE ALL FLOORS PLANS$0$23-WALL-TILES`: 1,999 segments, 1,086.331 m walked; 1,193 not_allow_listed, 806 below minimum length, 0 kept. `…$0$22-FINISH` (`X-REF_LANDSCAPE`): 10,349 segments, 569.752 m, 0 kept. Under option B the first layer's 1,193 segments would become candidates again; the resulting kept length is not stated in the inputs.

**What the roadmap / M3 says.** Roadmap M8 exit: "non-wall geometry" must not justify placement. Verification: correct (judgement-call table).

Decision / signature / date: ______________________________________________

---

## Closing table: which ORCH-044 item each decision unblocks

ORCH-044 is `MR/orchestrator/tasks/ORCH-044-TASK.md` (U2-M8-EXIT-FIXES; fixes 1..6). Status: issued, not yet run (Delivery record section 8).

| Decision | ORCH-044 item it unblocks | Note |
|---|---|---|
| 1. Title/frame/border words | Fix 1 (U2M8V-01, Medium: default deny, reason `title_frame`, fixture f8, GC-01 recompute). It also gates the report correction in fix 6 (T.FRAM total and boundary attribution are corrections of fact; the word list is the decision). | The only Medium finding. ORCH-044 says to keep the default conservative until decided. |
| 2. Off-layer INSERT rule | Fix 6 ("Owner/engineer decisions" section lists it). No code fix in ORCH-044. If B is ticked, a one-line rule change plus a test is a new item not in ORCH-044. | Zero GC-01 effect. |
| 3. Sparse threshold and units | Fix 6 (listed only). No code fix in ORCH-044. | Per-project store stage would hold the value (Verification U2M8V-10). |
| 4. MLINE | Fix 5 (U2M8V-05): read MLINE (option B) or surface `mline_unsupported` (option C). | Option A needs no change. |
| 5. 49-DOOR-TAG boundary | Fix 6 (listed only). No code fix in ORCH-044; a later M8 stage. | 501.757 m of boundary. |
| 6. F021 rotation term | None. ORCH-044 does not include F021; it is separate M8 work (Delivery record section 8). It blocks the M8 exit rotated-view condition, not ORCH-044. | |
| 7. Arcs / meshes | None. Confirmation only; no ORCH-044 item. | |
| 8. TILE / FINISH | None. Confirmation only; no ORCH-044 item. | |

Items in ORCH-044 that need no decision: fixes 2 (boundary visibility test, U2M8V-04), 3 (manifest hashes, U2M8V-02) and 4 (fixture determinism, U2M8V-03).
