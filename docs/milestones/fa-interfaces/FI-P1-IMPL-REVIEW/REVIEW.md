# FI-P1 implementation — independent correction review

Branch `fi-p1/implementation` @ `80b9603`, worktree `G:\dev (2)\dev\ep-platform-fi-impl`.
Read-only review by two fresh reviewers (code/tests; source drawings) plus a
cost check. No merge, no live DB write, no live migration, no service
restart, no model call.

## Verdict: CHANGES REQUIRED

One blocker (F1) breaks the binding contract C2 / W-PUB-2 on the acceptance
path. Reproduced on HEAD by scripted probes (provider stand-in, no model).

## Findings

| id | sev | where | scenario | covered by tests |
|---|---|---|---|---|
| F1 | BLOCKER | `workflow.py:402-406`, `accept` `:570-597` | `decide_publication` only examines agent reports with `status == "read"`; a present drawing that failed / is unread / stale / not synced is `not_attempted` and ignored. `accept()` lacks the empty-set / listing-failed / not-synced refusals of `_advance` and `publish_current`. Probe 1: FF drawing corrupt -> `complete_candidate` -> accept 200 -> snapshot holds only HVAC. Probe 2: every drawing fails -> `complete_candidate` -> accept 200 -> published snapshot with **0 sources**. Only the orchestrator's recommendation stands in the way. | none |
| F2 | MAJOR | `scan.py:129`, `service.py:299`, `:958-972` | The fire-alarm IFC drawing is read as ARCH, and ARCH yields gate connection points; contract S13 W-5 says no gate points from `fa_ifc`. Probe: two settled CR gate rows sourced from FIRE ALARM LAYOUT.dwg. | none |
| F3 | MAJOR | `service.py:1304-1322`, `fa_interfaces.py:268-283` | A governed gate conflict leaves both `verification` and `settled`; reopen and re-govern answer 404, so a wrong govern cannot be undone. | govern only |
| F4 | MAJOR | `workflow.py:411-412` | Only FP2's recommendation is used: an FP1 `do_not_publish`, coverage disputes and rework requests do not lower the run. Probe: FP1 do_not_publish + every source disputed -> still `complete_candidate`. | FP2-lowers only |
| F13 | MAJOR (cost) | `visual.wanted` `visual.py:88-92` | Damper labels on non-plan sheets are looked at although `_assemble` never counts them (`service.py:946-951`). EP-30880 SM-119 "SCHEMATIC RISER DIAGRAM": 268 labels, 54 of 132 Opus requests per full run (41 %), no effect on any count. | none |
| F5 | MINOR | `workflow.py:552-567` | `retry_review` on an accepted run resets it to `complete_candidate`; a second accept succeeds. | none |
| F6 | MINOR | `workflow.py:292-308` | A malformed Fable item (string in `coverage_assessment`) raises AttributeError; the run ends `failed` (fails closed, but a crash). | none |
| F7 | MINOR | `service.py:1189-1206` | W-4 alignment is decided per drawing pair, not per floor; union falls back to the label point when no symbol. | hand-built entries |
| F8 | MINOR | `fa_interfaces.py:151-163` | Retry review runs inside the HTTP request (up to 2x(packages+1) calls x 900 s); daily counter not atomic; stored `review_inputs` unused. | partly |
| F9 | MINOR | `provider.py` `models_used` | Substitution check passes when `modelUsage` is absent or lists only Haiku. | none |
| F10 | MINOR | `fa_interfaces.py:65-102`, `workflow.py:358` | Scan/run mutual exclusion check-then-enqueue can race (CAS still protects data); `accept` does not re-check open conflicts; review budget uses `calls_today_before=0`. | — |
| F11 | MINOR | `workflow.py:285-310` | `missing_or_suspect` package/issue not checked against the input; links/markup in Fable text not withheld. | partly |
| F12 | MINOR (safe side) | `service.py:1311-1322` | Contract rule "equal totals counted once from the role-bearing drawing" not implemented; EP-30880 GB stays held until governed. | — |

## Required verifications (task 1)

| item | result |
|---|---|
| a. both MSD drawings discovered and accounted for | PASS at unit level: every SM/HVAC drawing gets an agent; old winner rule gone; union only when aligned, else held. No end-to-end test with SMOKE + VENTILATION together. Real-data copy: both drawings read, 107 damper rows with stand-in answers, B3 = 2 rows on symbols `5741B`, `5741D`. |
| b. symbol vs tag coordinates | PASS: row anchor is the symbol or none, never the label; shared / architectural / no-symbol labels held. Tests genuine (one near-tautological assertion in `test_fa_cases.py:203`). |
| c. ENTRY/EXIT as two CR interfaces | PASS with F2, F3: roles assigned from connection points with a 1 m margin, not hard-coded; repeated notes merge; govern validated (drawing must be in the conflict, reason required). |
| d. stale-evidence exclusion (C1-C8) | PASS on scan / GET / publish-current (T-01..T-27); **FAIL on run acceptance (F1)**. |
| e. Fable failure handling | Mostly PASS: unavailable / unsupported / substituted / failed / budget leave the review not completed and the run provisional; exact model + effort passed. F4, F6, F9. |
| f. acceptance safeguards | **FAIL (F1)**; digest 409, CAS, retry bound, changed-drawing refusal, viewer 403 work. F5. |

## Tests (task 2)

- Focused: 98 passed (provider_honesty 17, render_bounds 10, fa_evidence 37, fa_cases 9, fa_interfaces 13, fa_workflow 12). Frontend `tsc` exit 0.
- Full suite on HEAD (implementer, nothing concurrent): 2 failed, 1355 passed, 35 skipped. Reviewer's run: 3 failed + 1 error; the extra two were `OSError: [Errno 28] No space left on device` / `database or disk is full` (C: at ~100 %), both pass alone.
- The two remaining failures match the baseline `21a2dc5` by name and message:
  - `test_ep_archive_models::test_directory_upgrade_preserves_existing_project_and_adds_lookup_index` — `IntegrityError: FOREIGN KEY constraint failed [DROP TABLE users]`
  - `test_proposed_materials::test_the_part_catalogue_knows_every_number_on_file_for_a_brand_and_completes_it` — AssertionError, extra `3-SSDC2`, `3-SDDC2`, `SIGA-OSD-FCN`
- The earlier 11 extra failures (document_sync, drawing_log, drawing_review, drawings_module, drf_extractor) did not reproduce; consistent with the disk-full condition.

## EP-30880 Gate Barrier conflict (task 3) — stays HELD

| | IFC layout | Shop drawing |
|---|---|---|
| file | `03- Drawings/IFC/Electrical/GB/BINGHATTI TITANIA GATEBARRIER SYSTEM LAYOUT.dwg` (2,916,568 B, sha `eda8dd8d…`) | `03- Drawings/IFC/Electrical/GB/Shop Drawings-Titania rev01.dwg` (5,766,111 B, sha `a7fb4efa…`) |
| revision | title block REV 00, empty revision table, no DWG NO; saved 2026-04-27; PDF print 2026-04-29; "PRELIMINARY SUBMISSION"; model-space title says "BINGHATTI **VINTAGE**" (copy error) | REV 01; revision table 00 24-06-2026, 01 20-07-2026 "SHOP DRAWING GATE.BARRIER"; DWG NO MAJ002-GME-SDW-EL-GB-ZZZ-BGF-010000; on architecture "ISSUED FOR CONSTRUCTION R1 01-05-2026"; status still "PRELIMINARY SUBMISSION" |
| GF barriers | **2**, central island at grid A4, ~14 m N of B1: entry cabinet (1162.99–1163.29, 178.69–179.28), arm W over "PARKING ENT."; exit cabinet (1163.49–1163.78, 178.69–179.28), arm E over "PARKING EXIT." | **4**: driveway pair between A8–A9 (D-S housing 1192.56–1192.96, 175.49–175.89; D-N block at 1194.96, 175.69) and ramp-head pair at B1 between A5–A6 (R-W 1174.46–1174.86, 165.19–165.59; R-E block at 1174.78, 163.49) |
| FA evidence | 2 notes "DRY CONTACT BY THIRD PARTY (2 Core) FIRE ALARM CABLE", leaders to (1163.161, 179.277) and (1163.635, 178.687) | 4 "FIRE ALARM CABLE" notes, joined by polylines (not LEADERs): (1190.57, 175.95), (1195.76, 175.76), (1174.72, 162.55), (1172.33, 166.59) |
| settled by the code | 2 of 2 (role margin 5.18 m) | 1 of 4 (R-W "ENTRY"); 3 held "no lane role label near it" |

- Same coordinate frame (24/31 landmarks, 21 mm; grid bubbles identical). The points are **different gates, not a superset**: the shop's newer architecture no longer shows the A4 barriers or their labels.
- Corroboration: ACS and FA IFC (older background) draw the two A4 barriers, no connection points. The approved load schedule PDF (`Electrical/Load Schedule/E-148497-APPROVED SCHD.pdf`, 05.04.2026) lists "GATE BARRIER IN" and "GATE BARRIER OUT" — 2 barriers.
- **Recommendation (advisory; not chosen):** keep held and ask the consultant/site to confirm (a) whether the A4 barriers were removed in architecture R1, (b) the shop drawing's approval state in `03- Drawings/SD Reference No/Shop Drawing Reference Number - Titania.xlsx` (cloud-only, not opened), (c) whether the electrical design went from 2 to 4 barrier circuits. If a choice is forced, shop rev01 is the more likely current intent (newer, on R1), confidence ~55–60 %; even then 3 of its 4 points stay held for lane role. The true total may be 2, 4 or 6.

## Limitations on the actual drawings (task 4)

- **PDFs — affects this case.** `SM/SD/` holds three GME smoke-management shop drawings (B1; GF to roof, 16 pages, legend lists MOTORIZED SMOKE FIRE DAMPER; B3/B2), Rev 00 21-07-2026, newer than SMOKE LAYOUT.dwg and only in PDF: the SM schedule may miss newer damper evidence. The FLS folder (DCD life-safety set) and the load schedule are not scanned. GB and ACS PDFs are prints of the read DWGs (no new evidence).
- **Loose-line symbols — small effect on dampers, none on the gate count.** Damper plan labels with no block symbol: SM 2 (SM-109 / SM-110 "SMD", 6-piece loose group 0.33 m away), HVAC 0; both held, never counted. 266 riser-diagram labels have loose geometry but diagrams are not counted. Gate counts come from FA notes; the layout's barriers and 2 of the shop's 4 are loose polylines, so their physical location relies on the leader target.
- **CLI — blocks any real validation today.** `.env`: `AI_PROVIDER=claude-code`; `AI_CLAUDE_CLI` points to `C:\Users\ramadan.mohamed\AppData\Local\ep-platform\claude-2.1.286\claude.exe`, which does not exist on this PC. The `claude` on PATH is 2.1.263 < `CLI_MIN_VERSION` 2.1.280 for claude-opus-5-5, so Opus is refused before any call (every run would be provisional, fails safe). Fable has no recorded minimum and is unverified. Model settings use defaults: claude-opus-5-5 / high, claude-fable-5-1 / high.
- Cloud-only: none of the read drawings; AutoCAD lock files for FF and HVAC (dated 2026-10-02) show those DWGs were open in AutoCAD.

## Environment notes

- C: has ~0.5 GB free; it caused the reviewer's two disk-full test failures. About 2.3 GB of it is this session's scratch DB copies (removable).
- The reviewer's baseline sparse worktree set `extensions.worktreeConfig = true` in the shared `G:/dev (2)/dev/ep-platform/.git/config` (harmless; removal was blocked by permissions). Undo: `git -C "G:/dev (2)/dev/ep-platform" config --unset extensions.worktreeConfig`.
