# FI-P1 — VALIDATION: correctness definitions, deterministic checks, reviewer protocol, metrics, cases, gates

Labels: C = confirmed, A = assumption, EXAMPLE = illustrative. Verified EP-30880 facts cite research B/D.

## 1. Correctness definitions (SPEC §4 "define before evaluation")

A published physical item is **correct** when all hold: (a) its `symbol_candidate_id` is a real symbol of an
accepted class for its `key` (right entity); (b) right layout/page and floor key(s); (c) `equipment_anchor` lies
inside `equipment_bounds` of that symbol or within the per-type tolerance below; (d) its labels are uniquely
associated (runner-up ratio ≥ 1.5, EXAMPLE) or the association is engineer-confirmed; (e) no other published item
shares the symbol id. A label-only item (no symbol) is never "correct physical"; it is `label_without_symbol`.

Per-type tolerances (all EXAMPLE, B §6; scale context: EP-30880 viewports 121.8×97 m, ≈1:150 on A1 (A), 10 m window
at 1400 px ≈ 7 mm/px, ±3 % pointing ≈ ±0.3 m):

| Equipment | Physical anchor | Location tolerance | Association reach |
|---|---|---|---|
| Dampers MD/MSD/SMD/MFSD | symbol bbox centre on duct | inside bbox or ≤0.15 m; distinct dampers = distinct symbol ids, else ≥0.3 m | ≤ max(1.0 m, 5× text height); observed 0.26–0.46 m (verified) |
| Fans SEF/JF/PEF/SPF | fan symbol centre | inside bbox or ≤0.5 m | tag ≤2 m or leader |
| Valves ZCV/ACV/OS&Y | valve symbol on pipe | ≤0.3 m | ≤1.5 m; riser valve = schematic |
| Pumps | pump symbols in pump-room polygon | room level | qty from symbols; schematic names evidence only; never default 3 (`_pump_room_pumps`, C) |
| Panels GCP/ACP | panel symbol | ≤0.5 m or room level | ≤1.5 m |
| Lifts | shaft polygon / machine room | room level, once per lift | label inside shaft |
| Doors (decoy class) | door block / opening | ≤0.5 m | door tag → nearest door block ≤1.5 m |

No single global distance threshold is used anywhere in validation or evaluation.

## 2. Deterministic checks (run on every Observation before any model review)

1. `frame_ok`: units known (`metre` not null) and point inside the layout's viewport window(s).
2. `class_allowed`: `key` wanted for the discipline by `matrix.rules_for` (C) and symbol class compatible.
3. `symbol_present`: physical instance has `symbol_candidate_id`; else state `label_without_symbol`, held.
4. `point_in_bounds`: `equipment_anchor` within bounds/tolerance (§1); free points `unsnapped` → held.
5. `sheet_floor_consistent`: `containing_sheets` size 1 or `ambiguous_sheet` → held; floor basis recorded.
6. `xref_door_tag`: label from architect xref (`xref_origin`) or with numeric sibling ATTRIB in a DOOR TAG block →
   damper keys rejected unless a duct-layer symbol candidate is associated (the "SD 04" case, verified B §2).
7. `duplicate_symbol`: two observations with one symbol id → merged (labels[]) **only when the labels are
   compatible** (same tag identity, or untagged with the same text and leader/same-block evidence to that symbol);
   otherwise a held ConflictSet with all members — an auto-merge would reproduce the two-MSD failure whenever one
   symbol candidate is missed.
8. `region_role`: labels in `schedule|legend|title_block` regions → `legend_entry|schedule_entry`, never physical.
9. `typical_support`: multiplier > 1 only with `sheet.multiplier` from title (sheets.py:393-395, C) and floors in snapshot.
10. `reference_fresh`: `reference_version` == snapshot; else `stale` → revalidate.
11. `decision_preserved`: an engineer decision keyed to this observation's sha-independent `decision_key`
    (CONTRACTS §0) is applied when the source sha is unchanged; across a revision it is carried forward as
    `needs_reconfirm` and not applied; if the observation changed materially (symbol id or floor) the decision is
    kept with `stale: true` and reason — never overridden.
12. `model_used`: `used_model` from the response equals the requested id; otherwise `model_substituted` → held.

## 3. Reviewer protocol (fresh-context Opus; SPEC §9)

Trigger: **every** model-proposed physical/association observation that is not settled by a deterministic geometric
rule (`settled_by_rule ∈ {same_block, leader_unique_candidate}` — the label sits inside the symbol's own block, or a
leader arrowhead lands inside exactly one candidate's bounds); self-reported confidence never decides who escapes
review, it only orders the queue (low first). Observations settled by rule are sampled (EXAMPLE 10 %) for drift.
Reviewer calls are counted in the agent's request allowance (PERFORMANCE §3). Procedure: (1) build a packet = crop (labels and candidate symbols
numbered, extractor's verdict **withheld**) + legend excerpt + matrix class list; (2) one schema-constrained call
(`ReviewerReading`, CONTRACTS §9) asking for the reviewer's own reading; (3) Python compares symbol id / class /
count; (4) agree → `validated` (by `reviewer_agreement`); disagree or abstain → `held` with both readings preserved.
Limits of this check, stated: separate contexts reduce leakage; they do not create independent human truth or
remove correlated same-family (same model) errors. Confidence strings are never an acceptance criterion.

## 4. Metrics (SPEC §12)

What the existing figures measure today (C, D §1): "98 %" is only the `table_layout` gate in `ai/evaluation.py:62`
(min 50 cases, min precision 0.98, 0 false validations) over resolved `ExtractionIssue` cases — BOQ cell reading, never
run against a live provider; "90 % recovery" appears nowhere in code or docs (closest: LLM_ASSISTANCE_PLAN.md §13,
no percentage promised). They are therefore **reused as owner targets and as the gate pattern**, with the
definitions below making the populations explicit.

Unit: ground-truth equipment instance **GTE** = one physical interfaced item (source sha, layout, key, physical
anchor/symbol handle, floor keys, tag|none, revision, disposition `interface|not_interface` for decoys). Predicted
record **PR** = published schedule line or held item. Matching: Hungarian assignment per (key, layout) on physical
distance within the §1 tolerance for the type (not a global τ); tagged items may match by tag identity.

| Metric | Definition (fields/population) | Target |
|---|---|---|
| Accepted precision | correct PRs / **published (not held)** PRs; correct = key, floor, tag identity and location all right | ≥ 0.98 |
| Physical recall ("recovery") | GTEs matched by published **or held** PR / all GTEs with disposition interface, on exhaustively annotated layouts only; accepted-only recall reported beside it | ≥ 0.90 |
| Tag / floor / revision accuracy | matched pairs: tag identity equal; floor-key set equal (typical expansion included); revision in force equal | reported |
| Location correctness | matched pairs: `equipment_anchor` within type tolerance of GT physical anchor and ≠ label point unless GT says so; median and p95 distance | reported |
| Association correctness | GT label→symbol links reproduced (same label, same symbol) | reported |
| Duplicate rate | PRs matched to an already-matched GTE + cross-file double counts / published PRs | 0 |
| Omission rate | 1 − recall, split never-detected vs held-not-published | reported |
| Critical false acceptances | published PR wrong in any field for safety-critical keys (dampers, fans, pumps) | **0 unresolved** |
| Coverage | layouts with terminal `inspected` / layouts in manifest; GTEs on uncovered layouts reported "unmeasured", never misses | reported |
| Decoy rejection | GT `not_interface` not published / decoys | reported |
| Cost & latency | requests, tokens, elapsed per agent/run (needs the extended `ai_usage` with job/agent id, CONTRACTS §13) | reported |

Grouping: by (prompt_version, model_id, effort, scan_version, task_version), stratified by key and discipline;
Wilson 95 % intervals; with fewer than ~150 GTEs per stratum a 98 % claim cannot be demonstrated (A). Concurrency
settings are compared on throughput; accuracy per setting is reported separately and is not evidence for speed.

## 5. Evaluation cases (SPEC §12) — what exists, what is needed

| # | Case | Exists today (C, D §1) | Needed | Pass criterion |
|---|---|---|---|---|
| 1 | Two adjacent MSDs (EP-30880 B3 pump room, labels 5741C/5741E, symbols 5741B/5741D — verified B) | synthetic test `tests/test_fa_interfaces.py:443` with mocked answers; real DXF in cache | GT record with both symbol handles | 2 items, 2 distinct symbol ids |
| 2 | Text far from symbol (leader) | none | annotate on SMOKE LAYOUT; LEADER/MLEADER fixture | association via leader arrowhead |
| 3 | Multiple labels, one symbol | none | fixture | 1 item, labels[]=2 |
| 4 | Unlabelled equipment | none (text-only scan → recall ≈ 0 structurally, A) | fixture with symbol, no text | `symbol_without_label` proposed, reviewer-validated |
| 5 | Rotated/scaled/nested CAD | none (RD-M1 F021 same gap) | synthetic DXF with rotated INSERT, scaled xref, depth ≥3 | anchors within tolerance |
| 6 | Cross-file coordinate differences | partly (RD-M1 GC-01f) | two files, one shifted frame | no cross-file comparison without `Alignment.verified` |
| 7 | Schedules & schematics | partly (`_schedule_checks`, riser conflicts) | fixture | schedule rows never counted; schematic refs = evidence |
| 8 | Typical floors | partly (RD-M1 GC-01g) | tagged item on typical sheet | multiplied per title, `_once` defect (B §4) fixed |
| 9 | Unreadable/missing pages | synthetic only | corrupt DXF; missing xref; layout without viewport | `PageOutcome=unread/unsupported`, never empty |
| 10 | Interrupted/resumed | real incident 142/144 | kill mid-drawing test | resume reuses checkpoints; no duplicates; no loss |
| 11 | Fresh unseen drawings | none | ≥1 second project/consultant held out, never used for prompt tuning | metrics reported separately |
| 12 | Decoys ("SD 04" door tag verified, room tags, smoke detectors) | synthetic only | GT `not_interface` records | decoy rejection |
| 13 | Pathological render (ASE-TILE hatch, SM-104 window — verified incident) | none | offline reproduction under `RENDER_TIMEOUT_S` | window `unread:render_timeout` within timeout; job cancellable |

## 6. Ground truth (D §1 proposal, adopted)

JSONL per source at `backend/evaluations/interfaces/<ep>/<sha24>.jsonl` (outside git like `cases/`):
`{gt_id, source_sha256, filename, revision, layout, floor_keys[], key, disposition, tag|null, physical:{x,y,handle|null,
block|null}, labels:[{x,y,handle,text}], typical_of|null, annotator, at, method: dwg_click|crop_review, notes}` plus a
per-drawing scope record `{layouts_annotated[], exhaustive: bool}`. Recall is computed only on exhaustive drawings.
The 158 existing decisions are **seed candidates**, not GT: line-level positives, bulk-confirmed (A), no omissions,
no physical coordinates, and 49 keyed to unmatchable anchors (C, D). Effort EXAMPLE/A: SMOKE + FIRE FIGHTING layouts
exhaustive ≈ 150–250 GTEs + 20–40 decoys ≈ 1–2 engineer-days with a click-to-annotate UI.

## 7. Acceptance gates

| Gate | Applies to | Criterion |
|---|---|---|
| G0 safety | Stage 0 merges | kill-mid-scan and unreachable-project-root tests keep prior readings; absent discipline folder does not abort; R1 removed + R2 added counted once; SM-104 render bounded; readiness false → no render; a substituted model is never logged as the requested one |
| G1 regression | every stage | `tests/test_fa_interfaces.py`, `test_redesign.py`, `test_draftsman_assignment.py` pass or their changes are listed with reasons (RD-M2 REGRESSION.md pattern, C) |
| G2 case gates | Stages 3–6 | cases 1–10, 12, 13 pass on fixtures |
| G3 accuracy | before replacing the current path | on exhaustive GT: accepted precision ≥ 0.98 with min cases per gate pattern, physical recall ≥ 0.90 (published+held), 0 unresolved critical false acceptances, duplicate rate 0; results on case 11 reported |
| G4 comparison | same | current vs proposed on identical frozen manifest, same PC, same model/effort, caches cleared; all §4 metrics + elapsed/requests/tokens; limitations stated |

Nothing here claims an accuracy or speed improvement; the gates define how one would be demonstrated.
