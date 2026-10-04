"""RD-M1 findings: one source for FAILURE-INVENTORY.csv and FAILURE-INVENTORY.md."""
import csv
import io
import os
import sys

SRC = "66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21"
S = "backend/app/redesign/service.py"
UNREV = "UNREVIEWED - awaiting independent RD-M1 review"
NOTEST = "none"

F = []


def f(**k):
    base = dict(golden_case="GC-01", source_sha256=SRC, reviewer_status=UNREV, secondary="", sheet="-", floor="-",
                room="-", coords="-", images="-", existing_tests=NOTEST)
    base.update(k)
    F.append(base)


f(id="RD-M1-F001", primary="H. CAD Apply - missing dependency", secondary="G. Workflow - stale/absolute path persisted",
  severity="High", sheet="FA 101", floor="3RD BASEMENT", room="Pump Room",
  coords="first failing insert: model (714.565, 157.0897) rot 270 (CT2 FOR ELECTRIC PUMP)",
  images="crops/GC01-R02-pumproom-drawn-B-plan.png",
  expected="Apply loads the CT1/CT2/CR library blocks from the library folder of the code that is running and saves the redesigned copy.",
  actual="Jobs 119 and 121 failed: AutoCAD 'CT2.dwg: Can't find file in search path ... *Invalid* ; error: Function cancelled'; no DWG produced. CT2.dwg exists in the running copy's library.",
  evidence="Original script line 51 (= E01 line 53) inserts \"CT2=<PC-A user profile>/OneDrive - <org>/Desktop/dev/ep-platform/backend/app/redesign/library/CT2.dwg\"; that path does not exist on PC-B. E05: exactly 6 interface changes carry the PC-A path, all moved=True & edited=True; 5 are approved (drawn). 145+2 others carry the G: path. E02 jobs 119/121 error; E13 worker log; E16: work-1/redesign.dwg sha256 = source sha256 (never saved).",
  reproduction="Offline: open evidence/E05-library-paths.json; filter status=approved -> 5 entries with a PC-A library path; the first drawn (script order) is if:e9335f7e336e:CT21. Compare with original script lines 51/60/69/78/87 (PC-A path) vs 96/105 (G path) = E01 lines 53/62/71/80/89 vs 98/107.",
  stage="20/21 CAD script generation / block-library dependency loading", cause_status="CONFIRMED (code + preserved script + DB)",
  cause="_module_symbols stores an absolute resolved library path in each change (service.py:435). plan() keeps engineer-moved/edited changes verbatim (service.py:1134) and _merge_interfaces keeps moved/edited modules' old insert (service.py:600-614). refresh() at Apply only re-places interface changes whose library key is MISSING, not unreachable (service.py:1312-1314). script_lines emits the stored path (cad.py:114-117). The DB and uploads were copied from PC-A to PC-B.",
  confidence="High", deterministic="Yes - every Apply on any PC where the stored PC-A path is absent",
  code="service.py:435, 600-614, 1134, 1312-1314; cad.py:114-121", existing_tests="test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted (does not cover stale/missing paths)",
  milestone="RD-M2 (proposed)")

f(id="RD-M1-F002", primary="G. Workflow - wrong status", secondary="H. generated result differs from plan; AI unapproved output drawn",
  severity="Critical", images="-",
  expected="Only changes an engineer approved are made on the redesigned DWG (the page labels review changes in status 'proposed' as 'Placed, to approve').",
  actual="_drawn() makes every review-sourced change in status 'proposed' as well as approved ones. The change itself was accepted by an engineer in the Drawings Review; what is unapproved is the AI's placement / symbol / erase target; only interface modules wait for approval. UI line 292 labels the proposed count 'Placed, to approve'.",
  evidence="service.py:667-671; ProjectRedesignPage.tsx:292 and :461 ('drawn once approved' shown only for interface modules). Current state: 0 review changes are proposed (4 approved, 27 skipped - E03), so the CURRENT Apply set is not affected; earlier Apply outputs (jobs 103-118, E02) cannot be checked because applied DWGs were not rendered in RD-M1.",
  reproduction="Read service.py:667-671; test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved asserts the same rule for modules only.",
  stage="18/19 approval state -> Apply job input", cause_status="CONFIRMED (code)",
  cause="Design choice in _drawn(); the UI wording implies approval is required.", confidence="High", deterministic="Yes",
  code="service.py:667-671, 1377; frontend/src/pages/ProjectRedesignPage.tsx:292", existing_tests="test_interface_modules_are_the_samples_blocks_as_big_on_paper_and_drawn_only_once_approved (asserts module rule; no test that unapproved review changes are excluded)",
  milestone="RD-M2 (proposed)")

f(id="RD-M1-F003", primary="F. AI behaviour - unsupported answer accepted", secondary="B. wrong action/target; C. wrong room",
  severity="Critical", sheet="FA 105", floor="1ST PODIUM", room="ELECTRICAL ROOM -> erase target in LIFT LOBBY",
  coords="review point page (655.0, 669.6); erase target handle 5DD10 page (761.45, 656.6), model (1309.45, 155.68); ~107 pt = ~6.6 m apart",
  images="crops/GC01-R06-remove-cross-room-A-source.png; crops/GC01-R06-remove-cross-room-B-plan.png",
  expected="REMOVE 'ceiling mounted speaker (CS) from electrical room' erases a CS in that room, or fails/asks when none is there.",
  actual="Model answered candidate 11 with confidence low and note 'Electrical room has only smoke detector #1 and light #2; nearest CS #11 is in lift lobby.' The platform accepted it and set remove = Ceiling Speaker handle 5DD10, erasable=True. Engineer skipped it.",
  evidence="E06 change d89599d510abfedf (ai, remove, candidates); crop R06 shows the red X on the lift-lobby CS, not in the electrical room.",
  reproduction="evidence/E06-review-changes.json -> id d89599d510abfedf; ai.candidate=11, remove.handle=5DD10; candidates[10].page.",
  stage="12/13 AI placement proposal -> deterministic conversion", cause_status="CONFIRMED (code + stored answer)",
  cause="read_answer keeps any in-range candidate regardless of confidence or note (ai.py:58-81, line 74); _place sets remove from the candidate with no room-membership check (service.py:762-766). Combined with F002, an unskipped low-confidence REMOVE in status proposed would be erased on Apply.",
  confidence="High", deterministic="Yes for the stored answer (model answer itself is not deterministic)",
  code="ai.py:58-81; service.py:749-766, 667-671", existing_tests="test_the_answer_is_kept_only_where_it_is_well_formed (format only)",
  milestone="RD-M2 (drawn-set gate) + later AI-validation milestone (proposed)")

f(id="RD-M1-F004", primary="H. CAD Apply - invalid script on error", secondary="H. generated result differs from plan; original-content-in-copy deletion risk",
  severity="High", images="-",
  expected="A failed insert stops the script (or is detected) before any other entity is touched.",
  actual="Each insert is followed unconditionally by (setq ep_f (cdr (assoc 41 (entget (entlast))))) and (entdel (entlast)). If an -INSERT fails, (entlast) is the previously created entity - a marker label, or, if the first insert of the script fails, the last entity of the original drawing - and it is deleted from the copy. AutoCAD script processing may continue after a LISP error.",
  evidence="cad.py:118-121; original script lines 51-54 (= E01 lines 53-56). In job 121 the copy was not saved (E16 work-1/redesign.dwg hash = source), so no corrupted output exists; the continuation behaviour after the error was not reproduced.",
  reproduction="Static: read cad.py:118-121 and E01. Dynamic reproduction requires running AutoCAD on an isolated copy - NOT done in RD-M1 (see DATA-SAFETY-REPORT).",
  stage="20/22 CAD script generation / AutoCAD execution", cause_status="CONFIRMED (code); consequence SUSPECTED (not reproduced)",
  cause="No success check between the measuring insert and entdel.", confidence="Medium", deterministic="Yes (given an insert failure)",
  code="cad.py:118-122", existing_tests="test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change (text of script only)",
  milestone="RD-M2 (proposed)")

f(id="RD-M1-F005", primary="A. Source and extraction - wrong layer interpretation", secondary="C. not on wall (downstream)",
  severity="High", sheet="all 17 plan sheets (one wall index per drawing)", images="renders/GC01-R01-sheet-FA101-B-plan.png (orange = wall index)",
  expected="The wall index contains wall faces only.",
  actual="Of 92,093 indexed segments only 9,461 (~10%, by RAW layer; the effective layer of the 28,491 raw-layer-'0' segments was not determined in bulk) are on an explicit wall layer (06-WALL); 4,351 (4.7%) come from entities with the DXF invisible flag (group 60) set, 3,973 of them on raw layer '0' (found by the independent reviewer, re-run by the producer: evidence/scripts/invisible_flag.py); and cabinets (02-CAB 17,776), glass, lifts, hidden lines (21-HIDDEN), ramps, fixtures, car stoppers, wall tiles and a frozen layer (X-REF_PLOT$0$A-NORTH, 342) are included. Probe at the 'wall' used by two approved modules: layer '0' inside anonymous block *U442 whose effective layer is X-REF_ FILE ALL FLOORS PLANS$0$29-PARKING - a layer the NOT_WALLS filter would exclude by name.",
  evidence="E10 (wall-index layers), E11 (effective layers of probe segments); walls.py:25-26,164.",
  reproduction="Copy evidence/scripts/*.py to ISO/scripts (they resolve the DXF as ISO/src/EP-30880/source.dxf and write to ISO/work, relative to their own folder), copy the source DXF there, then run wall_layers.py, effective_layer.py and invisible_flag.py (REPRODUCTION-RUNBOOK section 1 and step 6).",
  stage="8 wall extraction and caching", cause_status="CONFIRMED (code + DXF attribution)",
  cause="walls.build filters on the decomposed entity's raw layer (walls.py:164); recursive_decompose keeps '0' for block content instead of the INSERT's layer; layer on/frozen/plot state, viewport freeze and the entity invisible flag (walls.py:159-170 never reads dxf.invisible) are not considered; the filter is a deny-list.",
  confidence="High", deterministic="Yes", code="walls.py:25-27, 151-187",
  existing_tests="test_a_module_goes_on_the_nearest_real_wall_turned_to_it_past_an_equipment_outline (synthetic Walls only)",
  milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F006", primary="C. Placement - not on wall / outside room", secondary="E. clash with architectural element",
  severity="High", sheet="FA 101", floor="3RD BASEMENT", room="Pump Room / parking bay",
  coords="CT2 FOR ELECTRIC PUMP seen model (714.763, 157.090) approx.; CT2 FOR ZCV seen (714.351, 162.0)",
  images="crops/GC01-R02-pumproom-drawn-A-source.png; crops/GC01-R02-pumproom-drawn-B-plan.png",
  expected="A wall-mounted module is fixed on a real wall face of the room its equipment is in.",
  actual="Two APPROVED modules (drawn by Apply) are mounted on parking-block geometry admitted through raw layer '0' (effective layer 29-PARKING, which NOT_WALLS would exclude) - F005: CT2 FOR ELECTRIC PUMP stands in the pump room floor ~1.3 m inside the room's west wall; CT2 FOR ZCV stands outside the pump room, between parking bays. AI-proposed visual finding, corroborated by the wall-index geometry.",
  evidence="E07 (if:e9335f7e336e:CT21 moved=True on_wall=True; if:d6137c203008:CT21 approved on_wall=True); crop R02 A vs B (no line plotted there - visual); E11 probe 'invisible-rect-left-edge'. Note: E11 'visible' reflects LAYER state only (on/frozen/plot); it does not read the entity invisible flag or viewport freeze. The segment under CT2 FOR ZCV (y 161.288-162.588) has invisible=1; the segment under CT2 FOR ELECTRIC PUMP (y 156.288-158.788) has invisible=0, so why it does not plot is UNEXPLAINED (independent review).",
  reproduction="Render crop R02 (REPRODUCTION-RUNBOOK step 5) and compare A/B; the orange segment the modules sit on has no plotted line in A.",
  stage="13/14 deterministic placement (module wall snap) + coordination", cause_status="CONFIRMED: modules sit on parking-block geometry (data + code). Not plotting: PROPOSED (visual), explained by the invisible flag for the ZCV segment only. Engineering judgement: PROPOSED (AI)",
  cause="_nearest_wall / _place_module snap to the nearest indexed face (service.py:455-500) which here is parking-block geometry.",
  confidence="High (geometry) / Medium (engineering judgement)", deterministic="Yes", code="service.py:455-500; walls.py:151-187",
  milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F007", primary="E. Coordination - wrong cross-discipline transformation", secondary="C. outside room/building",
  severity="High", sheet="FA 101 (also other sheets - not enumerated)", floor="3RD BASEMENT", room="outside PLOT LIMIT",
  coords="see E07 anchor_model of CR B3-SEF-1, B3-SEF-3, B3-SEF-4",
  images="renders/GC01-R01-sheet-FA101-B-plan.png; crops/GC01-R04-FA101-left-edge-B-plan.png; crops/GC01-R05-FA101-right-edge-B-plan.png",
  expected="An interface module is placed beside its equipment inside the building.",
  actual="On FA 101, proposed modules CR B3-SEF-1 and CR B3-SEF-3 are placed outside the PLOT LIMIT boundary wall and CR B3-SEF-4 against the sheet frame line beside the legend; their anchors (red rings) are themselves outside the building. Status proposed (not drawn unless approved). AI-proposed visual finding.",
  evidence="Renders R01/R04/R05; E07 anchors; interfaces/service.py:621 uses the trade drawing's own model point; redesign/service.py:527-529 maps it straight onto this drawing's sheets.",
  reproduction="Render R01 and R04/R05; read E07 for the three modules.",
  stage="9/10 interface schedule ingestion -> module identification/anchoring", cause_status="SUSPECTED (shared-coordinates assumption not verified; no registration check exists - confirmed by code)",
  cause="The trades' drawings are assumed to share the FA drawing's coordinates (service.py:381-393 comment block); no transform or plausibility check. Alternative: the trade label read is not at the fan's location.",
  confidence="Medium", deterministic="Yes", code="interfaces/service.py:618-621; redesign/service.py:503-560",
  existing_tests="test_a_typical_plans_floors_get_one_module_each_item_stacked_and_the_unplaceable_listed (synthetic)", milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F008", primary="E. Coordination - model incomplete", secondary="E. symbol-text, note, door/window, other discipline; D. ceiling coordination",
  severity="High", images="crops/GC01-R02-pumproom-drawn-B-plan.png; crops/GC01-R11-roof-left-cluster-B-plan.png; crops/GC01-R06-remove-cross-room-B-plan.png",
  expected="New symbols and notes are kept clear of existing text, notes, doors and swings, windows, equipment, other disciplines and existing devices.",
  actual="coordinate() checks only (a) new placed symbols/notes against each other and (b) existing device symbols that happen to be in some change's candidate list (the 15 nearest within 8 m), each as a fixed 0.25 m square. Existing text, notes, door swings, windows, equipment, ceilings and other disciplines are not inputs.",
  evidence="service.py:880-1060 (existing set 899-905; clear() 920-936; EXISTING_RADIUS_M 825).",
  reproduction="Read code; instances F009-F011.", stage="14 coordination", cause_status="CONFIRMED (code)",
  cause="Coordination inputs limited by design.", confidence="High", deterministic="Yes", code="service.py:824-1060",
  existing_tests="test_coordination_is_always_done_the_engineers_moves_and_the_modules_notes_included; test_two_devices_at_one_wall_share_it_side_by_side_without_passing_its_corner",
  milestone="RD-M4 coordination (proposed)")

f(id="RD-M1-F009", primary="E. Coordination - symbol-text overlap", severity="Medium", sheet="FA 101", floor="3RD BASEMENT", room="Pump Room",
  images="crops/GC01-R02-pumproom-drawn-B-plan.png",
  expected="Approved heat detector and IP-rated emergency light clear of the room label.",
  actual="Approved changes 3ddaa99cd7374341 (heat detector, engineer-moved) and 45efbfb70918a4f0 (E WP, engineer-moved) sit on/against the 'PUMP ROOM' label. AI-proposed visual finding.",
  evidence="Crop R02; E06 insert.seen for both.", reproduction="Render R02.", stage="14 coordination", cause_status="CONFIRMED cause class (F008); instance PROPOSED (visual)",
  cause="Text not a coordination input (F008).", confidence="Medium", deterministic="Yes", code="service.py:880-1060", milestone="RD-M4 coordination (proposed)")

f(id="RD-M1-F010", primary="E. Coordination - note overlap", secondary="E. clash with equipment",
  severity="Medium", sheet="FA 101", floor="3RD BASEMENT", room="Pump Room",
  images="crops/GC01-R02-pumproom-drawn-B-plan.png (pink = note footprint)",
  expected="Module notes ('FOR ...') readable and clear of equipment and other annotation.",
  actual="Approved module notes run ~3.0-3.9 m across the pump room (e.g. 'FOR DIESEL PUMP' 15 chars x 0.306 m x 0.85) over the pump area and dashed lines; the ZCV note runs into a parking bay. AI-proposed visual finding; footprint computed from service._note/_footprint.",
  evidence="Crop R02; note height in E07 / code service.py:830-873.", reproduction="Render R02.", stage="14 coordination", cause_status="CONFIRMED cause class (F008); instance PROPOSED (visual)",
  cause="Notes are only checked against other new placements.", confidence="Medium", deterministic="Yes", code="service.py:830-873", milestone="RD-M4 coordination (proposed)")

f(id="RD-M1-F011", primary="C. Placement - in door swing / on opening", secondary="E. note overlap",
  severity="Medium", sheet="FA 117; FA 105", floor="ROOF; 1ST PODIUM", room="Roof pump room door; electrical room door",
  images="crops/GC01-R11-roof-left-cluster-B-plan.png; crops/GC01-R06-remove-cross-room-B-plan.png",
  expected="No module or note on a door, its swing or its tag.",
  actual="Proposed module CR for SD on FA 117 sits on the pump-room door symbol and its door tag; on FA 105 a proposed CR SD module's note runs through the electrical-room door swing and tag. Status proposed (not drawn unless approved). AI-proposed visual finding.",
  evidence="Crops R11, R06.", reproduction="Render R06/R11.", stage="13/14 placement/coordination", cause_status="CONFIRMED cause class (F008: doors excluded); instance PROPOSED (visual)",
  cause="Door/window layers are excluded from the wall index and not otherwise modelled.", confidence="Medium", deterministic="Yes",
  code="walls.py:25-26; service.py:880-1060", milestone="RD-M4 coordination (proposed)")

f(id="RD-M1-F012", primary="E. Coordination - unresolved clash not reported", severity="Medium",
  expected="A symbol that cannot be cleared is flagged to the engineer.",
  actual="When slide, side-by-side and next-wall fail (and for non-module wall devices the free search is skipped), the change is appended to the fixed set unchanged with no flag (service.py:1044-1059).",
  evidence="Code.", reproduction="Read service.py:1013-1060.", stage="14 coordination", cause_status="CONFIRMED (code)",
  cause="No 'unresolved' state.", confidence="High", deterministic="Yes", code="service.py:1013-1060", milestone="RD-M4 coordination (proposed)")

f(id="RD-M1-F013", primary="F. AI behaviour - unsupported orientation", secondary="C. wrong orientation",
  severity="Medium", sheet="multiple", images="crops/GC01-R09-lift-lobby-FTJ-B-plan.png",
  expected="Wall devices are oriented from verified geometry; uncertain orientation is held for the engineer.",
  actual="15 of 31 review-change answers state that the rotation/facing convention is uncertain or assumed; the platform still converts the stated facing into a rotation and marks the change proposed.",
  evidence="E06 notes (ids listed in E04/E06); service.py:195-202, 146-162.", reproduction="grep 'rotation' in E06 notes.",
  stage="12/13 AI proposal -> conversion", cause_status="CONFIRMED (stored answers + code)", cause="Facing inferred from block geometry heuristics; AI uncertainty not gating.",
  confidence="High", deterministic="Yes for stored answers", code="service.py:146-202; ai.py:15-40", milestone="AI-validation milestone (proposed)")

f(id="RD-M1-F014", primary="F. AI behaviour - ignored evidence / answer overridden", secondary="B. wrong symbol mapping",
  severity="Medium", expected="AI and platform agree on the inserted symbol; overrides are visible.",
  actual="8 answers say the emergency light / directional sign is 'not in the symbol list' (symbol 0) although the current list has Emergency Light and Directional Emergency Sign; the platform then inserts E / E WP / EXT-2D through PREFERRED regardless (not shown as an override).",
  evidence="E06 ids 45efbfb70918a4f0, 13059eaeb6b87480, 0cdfb503e512c2c7, d6b299d789d905ed, bd092a68454cc62a, 72f22f76271b87b8, 34f8317dbedb40bb, e637aa4a101d2ae0; service.py:209-230, 770-773.",
  reproduction="E06: ai.symbol==0 and insert.block set.", stage="12/13", cause_status="SUSPECTED (whether the list sent at plan time contained these symbols is not stored)",
  cause="Symbols list not persisted per call; PREFERRED override silent.", confidence="Medium", deterministic="Yes for stored answers",
  code="service.py:209-230, 770-773, 1082-1083", milestone="AI-validation milestone (proposed)")

f(id="RD-M1-F015", primary="B. Device understanding - wrong symbol mapping", severity="Medium", sheet="FA 101", room="Pump Room",
  expected="Weatherproof MCP inserted from a plan symbol block.",
  actual="Approved change 34d7690b0446388c inserts block 'XREF - title block a1 15-06-2022$0$BREAK GLASS WP' (a bound title-block xref block) at scale 0.001; _symbols excludes '|' xref blocks but not bound '$0$' blocks.",
  evidence="original script line 35 (E01 line 37); E06; symbols list in E04.", reproduction="E06 -> 34d7690b0446388c insert.block.",
  stage="7/10 existing symbol discovery -> symbol choice", cause_status="CONFIRMED (data); visual result UNVERIFIED (applied output not rendered)",
  cause="service.py:282 filter.", confidence="Medium", deterministic="Yes", code="service.py:275-312", milestone="RD-M3/RD-M5 (proposed)")

f(id="RD-M1-F016", primary="G. Workflow - absolute paths persisted", secondary="H. output not retrievable",
  severity="Medium", expected="Stored references are portable (relative to the platform's roots).",
  actual="project_redesign.output_path is a PC-A absolute path; GET /output.dwg checks Path(row.output_path).is_file() and returns 404 on PC-B although GC01 redesign/...1654.dwg exists here. Library paths (F001) are the same pattern.",
  evidence="E03 output_path; routers/redesign.py:172-183; E16 lists the 1654.dwg file.", reproduction="E03 + E16.",
  stage="24 output registration", cause_status="CONFIRMED (code + data)", cause="str(platform_copy) stored (service.py:1401).",
  confidence="High", deterministic="Yes", code="service.py:1386, 1401; routers/redesign.py:172-183", milestone="RD-M2 (proposed)")

f(id="RD-M1-F017", primary="G. Workflow - failed retry / duplicate execution", secondary="H. output saved twice risk",
  severity="Medium", expected="A job whose work already completed is not run again; a job carried in a copied DB does not start by itself on another PC.",
  actual="Job 119 (Apply, created 2026-10-02 12:54:19 UTC on PC-A) had already made 'FIRE ALARM LAYOUT R0 - Redesign 2026-10-02 1654.dwg' (row output_at 12:55:35, output_changes 11) but was still 'running' in the copied DB; PC-B's IFC worker requeued and re-ran it at 2026-10-03 15:15:05 UTC with no user action (attempts=1), and it failed (F001). Likely reason it was still running in the copy: the PC-A IFC worker running job 119 last heartbeat at 12:55:27 UTC (background_workers: current_job_id 119, stopped_at NULL); the output was committed at 12:55:35 and the job row was never finished before the DB was copied (independent review round 2, verified by the producer in the snapshot).",
  evidence="E02 jobs 118/119; E03 output_*; E13 'Job 119 was left running by a worker that stopped: requeued'; jobs.py:351-396.",
  reproduction="E02 + E03 + E13.", stage="25 error handling and retry", cause_status="CONFIRMED (log + DB)",
  cause="recover_stale requeues by heartbeat age only; no idempotency/host check.", confidence="High", deterministic="Yes",
  code="services/jobs.py:101-106, 351-396", existing_tests="test_ifc_worker_and_ai (requeue behaviour; not cross-host)", milestone="RD-M2 (proposed)")

f(id="RD-M1-F018", primary="G. Workflow - missing provenance (engineer decisions)", severity="Medium",
  expected="Each approve/skip/move/pick records who and when.",
  actual="Change records have no decided_by/decided_at; activity_events records only plan/drawing/interfaces starts (E14); the PATCH endpoints record nothing.",
  evidence="E03 change_keys_present; E14; routers/redesign.py:116-142.", reproduction="E03/E14.", stage="15 manual engineer changes",
  cause_status="CONFIRMED (code + data)", cause="Not implemented.", confidence="High", deterministic="Yes",
  code="service.py:650-664, 1196-1249; routers/redesign.py:116-142", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F019", primary="G. Workflow - unsafe read-side effect", severity="Medium",
  expected="GET endpoints do not write.",
  actual="GET /projects/{id}/redesign/{did} -> view() calls state() (inserts a row when none), review.build() (may run _fit and commit) and db.commit(); GET image/output call state().",
  evidence="service.py:70-77, 1416-1426; review/service.py:398-401; routers/redesign.py:63-66, 163, 176.", reproduction="Read code.",
  stage="17 preview rendering / page load", cause_status="CONFIRMED (code)", cause="Lazy creation on read.", confidence="High", deterministic="Yes",
  code="service.py:70-77, 1416-1426", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F020", primary="G. Workflow - missing provenance (AI calls)", severity="Low",
  expected="Every model call is linked to the job that made it.",
  actual="All 44 fa_drawing_redesign ai_usage rows have run_id NULL; 7 rows (ids 686-690 at 09:49-09:50 and 728-729 at 10:05 UTC, 2026-10-02) fall outside Plan job 102's run window - their origin is not recorded.",
  evidence="E09; E02 job 102.", reproduction="E09.", stage="12 AI proposal", cause_status="CONFIRMED (data); origin of the 7 calls UNKNOWN",
  cause="assist.call_task not given a run id here.", confidence="High", deterministic="n/a", code="service.py:1063-1092", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F021", primary="A. Source and extraction - wrong rotation (unsupported)", secondary="A. scale/origin error carried",
  severity="Medium", expected="Plot-to-model tie supports rotated/twisted views and flags its error on every added symbol.",
  actual="geometry.fit is X = a*x + bx, Y = -a*y + by (no rotation term). On GC-01 median residuals are 0.0-0.55 m (FA 104 0.55, FA 112 0.37, FA 117 0.36); CONFIRM_ABOVE_M = 1.0 so none is flagged.",
  evidence="review/geometry.py:35-76; E15.", reproduction="E15.", stage="5 sheet detection / geometry tie", cause_status="CONFIRMED (code); rotated-drawing failure NOT REPRODUCED (no rotated case available)",
  cause="Fit model.", confidence="High", deterministic="Yes", code="review/geometry.py:35-78; service.py:63", milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F022", primary="C. Placement - outside room (no containment model)", secondary="A. missing architectural geometry",
  severity="High", expected="Placement is checked against the room/building it must be in.",
  actual="No room or building polygon is used: each sheet's 'plan' box is the whole drawing frame [48,34,2057,1650] on all 17 sheets; room membership rests on the model's answer only. Modules outside the PLOT LIMIT (F007) and the AI's 'placed outside' answer (F029) pass unflagged.",
  evidence="E15 plan_box_pt; service.py:527-536, 749-821.", reproduction="E15.", stage="6 room and geometry discovery", cause_status="CONFIRMED (code + data)",
  cause="Not implemented.", confidence="High", deterministic="Yes", code="service.py:503-560, 749-821", milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F023", primary="H. CAD Apply - output not verified", secondary="H. generated result differs from plan",
  severity="High", expected="After AutoCAD runs, the output is checked against the plan (inserted blocks/handles/markers present, erased handles gone, nothing else removed).",
  actual="Only 'file exists and mtime changed' is checked (cad.py:167); the AutoCAD log is discarded on success. A partially executed script (F004) would be saved and filed as made.",
  evidence="cad.py:143-176.", reproduction="Read code.", stage="23 output verification", cause_status="CONFIRMED (code)",
  cause="Not implemented.", confidence="High", deterministic="Yes", code="cad.py:143-176", milestone="RD-M2 (proposed)")

f(id="RD-M1-F024", primary="H. CAD Apply - leftovers", severity="Low",
  expected="Work folders cleaned; failure artefacts kept deliberately and bounded.",
  actual="work-1 keeps redesign.dwg/redesign.scr after failure (useful evidence) and an AutoCAD ErrorReports folder that the cleanup loop cannot remove (unlink on a directory); review/plot-66043c11fab9 and plot-8eea8dd66621 keep DWG copies from earlier failed plots.",
  evidence="E16 file list.", reproduction="E16.", stage="22 AutoCAD execution", cause_status="CONFIRMED (filesystem + code)",
  cause="cad.py:171-175; render.py cleanup only on success.", confidence="High", deterministic="Yes", code="cad.py:171-175; review/render.py:84-96",
  milestone="RD-M2 (proposed)")

f(id="RD-M1-F025", primary="G. Workflow - inconsistent floor naming", severity="Low",
  expected="One floor name per sheet across change records.",
  actual="Changes on the same sheet carry different floor strings (e.g. page 16 'ROOF' x29 vs 'Roof' x22; page 3 'GROUND FLOOR' vs 'Ground Floor'; FA 114 changes carry 'Level 18'..'Level 22').",
  evidence="E04 sheets_of_changes.", reproduction="E04.", stage="9/16", cause_status="CONFIRMED (data)",
  cause="Failed interface changes use the schedule's floor; placed ones the sheet's (service.py:546-547 vs 565).", confidence="High", deterministic="Yes",
  code="service.py:543-568", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F026", primary="D. Coverage - incomplete placement of required modules", secondary="A. wrong floor (typical plan mapping)",
  severity="Medium", expected="Every scheduled module is placed or explicitly assigned to a plan.",
  actual="47 of 200 interface modules are 'failed' (draw by hand): 35 no drawn position, 2 no plan for Top Roof, 10 typical-plan mismatches (e.g. 'shows it on a plan that covers Level 18, but this drawing's plan there is TYPICAL 23R...'), the last suggesting the trade's typical plan sits where this drawing has a different typical plan.",
  evidence="E04 failed_errors; E07.", reproduction="E04.", stage="9/10 interface ingestion", cause_status="CONFIRMED (data); typical-plan cause SUSPECTED",
  cause="Shared-coordinates assumption across typical plans (see F007).", confidence="Medium", deterministic="Yes", code="service.py:503-560",
  existing_tests="test_a_typical_plans_floors_get_one_module_each_item_stacked_and_the_unplaceable_listed", milestone="RD-M3 geometry (proposed)")

f(id="RD-M1-F027", primary="D. Coverage and engineering rules - not re-checked", severity="Medium",
  expected="After placement/moves, coverage/spacing rules the review applied are re-checked.",
  actual="The redesign performs no coverage or spacing check after placing or moving devices (e.g. the engineer-moved heat detector); rules exist only in the review stage.",
  evidence="Code search: no coverage computation in app/redesign.", reproduction="Read app/redesign/*.py.", stage="13-15", cause_status="CONFIRMED (code)",
  cause="Not implemented.", confidence="High", deterministic="Yes", code="app/redesign/service.py", milestone="later engineering-rules milestone (proposed)")

f(id="RD-M1-F028", primary="F. AI behaviour - inconsistent repeated answer", severity="Low",
  expected="Repeated questions about the same change give the same answer, or variation is recorded.",
  actual="2 of 31 changes have two cached answers: 3ddaa99cd7374341 point moved (0.515,0.513)->(0.504,0.547) of a 16 m box (~0.6 m); 1561933977450e28 symbol 36 'Sounder Strobe WP' -> 44 'Wall mounted sounder'. Evidence fingerprints differed, so this is not pure model nondeterminism.",
  evidence="E08.", reproduction="python evidence/scripts/ai_variation.py.", stage="12", cause_status="CONFIRMED (cache data)", cause="Input change + model variation (not separable from stored data).",
  confidence="Medium", deterministic="No", code="compliance/assist.py:246-283", milestone="AI-validation milestone (proposed)")

f(id="RD-M1-F029", primary="C. Placement - wrong room", secondary="F. AI unsupported placement",
  severity="Medium", sheet="FA 108", floor="4TH PODIUM", room="SWIMMING POOL / pump room", images="crops/GC01-R07-pool-pumproom-B-plan.png",
  expected="Device placed in the room the change names.",
  actual="Change 5d2de6f964bab9e3 (sounder strobe WP, low confidence): model note 'Ring and 7 are parking side; named room is pump room. Placed outside, beside door.' Accepted as proposed; engineer skipped.",
  evidence="E06; crop R07.", reproduction="E06.", stage="12/13", cause_status="CONFIRMED (stored answer); no containment check (F022)",
  cause="F022.", confidence="High", deterministic="Yes for stored answer", code="ai.py:58-81; service.py:749-821", milestone="RD-M3 / AI-validation (proposed)")

f(id="RD-M1-F030", primary="G. Workflow - plan modified at Apply", secondary="H. generated result differs from reviewed plan",
  severity="Medium", expected="Apply makes exactly the plan the engineer last saw.",
  actual="apply() calls refresh(), which re-places stale changes and re-runs coordination, and commits the result (service.py:1376, 1304-1357) before generating the script; positions can change between review and Apply without the engineer seeing them.",
  evidence="Code.", reproduction="Read code.", stage="19/20", cause_status="CONFIRMED (code)", cause="Design.", confidence="High", deterministic="Yes",
  code="service.py:1304-1357, 1376", milestone="RD-M2 (proposed)")

f(id="RD-M1-F031", primary="H. CAD Apply - output saved to project archive", severity="Medium",
  expected="Consistent with config: 'Never the archive itself -- the platform reads the archive, it does not write to it.'",
  actual="apply() writes the redesigned DWG into <project source folder>/03- Drawings/Redesign/ (the synced archive) in addition to uploads; 17 such files are recorded as filed (E02 results). Not re-verified in the archive (archive not reachable from PC-B).",
  evidence="service.py:1389-1400; core/config.py:149-150; E02 'filed'.", reproduction="Read code + E02.", stage="24 output registration",
  cause_status="CONFIRMED (code + job results)", cause="Policy conflict.", confidence="High", deterministic="Yes", code="service.py:1389-1400",
  milestone="RD-M2 (proposed) - owner decision")

f(id="RD-M1-F032", primary="G. Workflow - manual decision overwritten (no concurrency control)", secondary="G. stale plan",
  severity="High", expected="An engineer's approve/skip/move made while a Plan or Apply runs is never lost; concurrent writers are detected.",
  actual="plan() writes the whole row.changes from its start-time list after every model answer (service.py:1175; also 1146, 1181), so a PATCH made during a Plan (job 102 ran 3.5 min) is overwritten. adjust()/set_status() have no status or version guard (service.py:662, 1247). Plan and Apply have different dedup keys (routers/redesign.py:74, key = kind:project:drawing), so both can run at once. refresh() inside Apply commits the row whenever coordination touches anything (service.py:1324-1325; 25 touches on GC-01).",
  evidence="Code; reported by the independent reviewer, verified by the producer against service.py:1173-1176 and routers/redesign.py:72-76.",
  reproduction="Read code. Not reproduced (would need concurrent live requests).", stage="15/16/19 engineer changes, plan persistence, Apply",
  cause_status="CONFIRMED (code); NOT REPRODUCED", cause="Whole-row JSON rewrite without optimistic locking.", confidence="High",
  deterministic="Timing-dependent", code="service.py:1146, 1175, 1181, 1247, 1324-1325; routers/redesign.py:70-90", milestone="RD-M6 workflow (proposed)")

f(id="RD-M1-F033", primary="H. CAD Apply - output overwritten (minute-resolution name)", secondary="H. output saved to wrong location",
  severity="Medium", expected="Every Apply output has a unique name; nothing is overwritten silently.",
  actual="The output name uses the stamp %Y-%m-%d %H%M (service.py:1383-1385); shutil.copyfile (cad.py:170) and open(..., wb) into the archive (service.py:1396) overwrite silently, so two Applies in the same minute replace the earlier DWG in uploads and in the archive. Jobs 103 and 104 ran 76 s apart (different minutes).",
  evidence="Code; E02 timings. Reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="24 output registration", cause_status="CONFIRMED (code); NOT REPRODUCED", cause="Name collision.", confidence="High",
  deterministic="Timing-dependent", code="service.py:1383-1396; cad.py:169-170", milestone="RD-M2 (proposed)")

f(id="RD-M1-F034", primary="G. Workflow - Apply cannot be cancelled", severity="Low",
  expected="A running Apply honours the job's cancel request.",
  actual="apply() accepts check= but never calls it; the AutoCAD run can take up to 1,200 s (cad.py:34).",
  evidence="service.py:1360-1410 (no use of check); reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="22/25", cause_status="CONFIRMED (code)", cause="Not implemented.", confidence="High", deterministic="Yes",
  code="service.py:1360-1410; cad.py:34, 159-161", milestone="RD-M2 (proposed)")

f(id="RD-M1-F035", primary="G. Workflow - confirm flag not gating", secondary="A. scale/origin error carried", severity="Low",
  expected="An added symbol flagged confirm (plot error above 1 m) is not drawn until confirmed.",
  actual="view() computes confirm (residual > CONFIRM_ABOVE_M) for display only; _drawn() ignores it. Not triggered on GC-01 (max residual 0.55 m).",
  evidence="service.py:1433-1434 vs 667-671; reported by the independent reviewer, verified by the producer.", reproduction="Read code.",
  stage="18", cause_status="CONFIRMED (code)", cause="Display-only flag.", confidence="High", deterministic="Yes",
  code="service.py:63, 667-671, 1433-1434", milestone="RD-M2 (proposed)")

COLS = ["id", "golden_case", "primary", "secondary", "severity", "source_sha256", "sheet", "floor", "room", "coords", "images",
        "expected", "actual", "evidence", "reproduction", "stage", "cause", "cause_status", "confidence", "deterministic", "code",
        "existing_tests", "milestone", "reviewer_status"]
HEAD = ["finding_id", "golden_case_id", "category_primary", "categories_secondary", "severity", "source_sha256", "sheet", "floor",
        "room_or_area", "drawing_coordinates", "screenshots_crops", "expected_behavior", "actual_behavior", "evidence",
        "reproduction_steps", "pipeline_stage", "suspected_cause", "cause_status", "confidence", "deterministic",
        "affected_files_functions", "existing_test_coverage", "recommended_milestone", "reviewer_status"]


def main(pkg):
    with open(os.path.join(pkg, "FAILURE-INVENTORY.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEAD)
        for x in F:
            w.writerow([x.get(c, "") for c in COLS])
    from collections import Counter
    sev = Counter(x["severity"] for x in F)
    out = io.StringIO()
    out.write("# RD-M1 Failure Inventory\n\n")
    out.write("Golden Case GC-01 (project 5 / IFC drawing 1 / project_redesign 1; source DWG sha256 `" + SRC + "`).\n\n")
    out.write("Generated from the same source as `FAILURE-INVENTORY.csv` (35 findings). Every finding is **UNREVIEWED**: "
              "nothing here is human engineering approval. Findings marked *PROPOSED (visual)* come from Claude's review of rendered "
              "copies and are corroborated only as far as the *cause_status* says.\n\n")
    out.write(f"Severity counts: Critical {sev['Critical']}, High {sev['High']}, Medium {sev['Medium']}, Low {sev['Low']}.\n\n")
    out.write("| ID | Sev | Primary category | Stage | Cause status | Deterministic |\n|---|---|---|---|---|---|\n")
    for x in F:
        out.write(f"| {x['id']} | {x['severity']} | {x['primary']} | {x['stage']} | {x['cause_status']} | {x['deterministic']} |\n")
    for x in F:
        out.write(f"\n## {x['id']} - {x['primary']} ({x['severity']})\n\n")
        for label, key in (("Secondary", "secondary"), ("Sheet / floor / room", None), ("Coordinates", "coords"),
                           ("Images", "images"), ("Expected", "expected"), ("Actual", "actual"), ("Evidence", "evidence"),
                           ("Reproduction", "reproduction"), ("Pipeline stage", "stage"), ("Suspected cause", "cause"),
                           ("Cause status", "cause_status"), ("Confidence", "confidence"), ("Deterministic", "deterministic"),
                           ("Code", "code"), ("Existing tests", "existing_tests"), ("Recommended milestone", "milestone"),
                           ("Reviewer status", "reviewer_status")):
            val = f"{x['sheet']} / {x['floor']} / {x['room']}" if key is None else x.get(key, "")
            if val and val != "-":
                out.write(f"- **{label}:** {val}\n")
    open(os.path.join(pkg, "FAILURE-INVENTORY.md"), "w", encoding="utf-8", newline="\n").write(out.getvalue())
    print(len(F), dict(sev))


if __name__ == "__main__":
    main(sys.argv[1])
