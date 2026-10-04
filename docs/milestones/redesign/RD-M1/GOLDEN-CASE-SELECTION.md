# Golden Case Selection (RD-M1)

## What was available

The audit snapshot of the G-drive copy's database (see `DATA-SAFETY-REPORT.md`) holds **one** Redesign record: `project_redesign` id 1 = project 5 (EP-30880), IFC drawing 1 (`FIRE ALARM LAYOUT.dwg`, R0). The only other Drawings Review row (project 1, drawing 11) is `idle` with no sheets and no Redesign. No other project has Redesign data, so **every Golden Case below is a slice of one drawing**. No new processing was run to fill gaps.

Not opened: the Desktop copy's database (a separate running deployment on :8000), the sibling clone folder in the outer repo, and the project archive (not reachable from this PC: "Project archive path is not reachable" in the sync worker log). All 10 projects in the snapshot are `status=active`, `ai_policy=allowed`; none is marked sealed.

## GC-01 — the primary case

| Item | Identity |
|---|---|
| Source DWG | GC01:`ifc/60de2a377daa.dwg`, sha256 `66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21`, 4,380,643 B (= review `source_sha256` = redesign `source_sha256`) |
| Extraction (DXF) | GC01:`ifc/60de2a377daa.dxf`, sha256 `dbe7900f21033b2a…` (full hash in `evidence/E16-source-binding.json`) |
| Sheets | 17 plan sheets FA 101–FA 117 (`evidence/E15-sheet-geometry.json`) |
| Review plot | GC01:`review/66043c11fab9eaf5a1768ba2.pdf`, sha256 `2dd28b0480adcd2b…`, 20 pages |
| Symbols | 21 symbol types (`evidence/E04-changes-analysis.json` → `symbols`), 1,546 `ifc_symbols` rows DB-wide |
| Wall index | GC01:`redesign/walls-1-66043c11fab9eaf5-v1.pkl`, sha256 `9e5a94c17fa2573f…` |
| Interface schedule | `project_fa_interfaces` id for project 5; 6 trade DXFs under GC01:`interfaces/` (hashes in E16) |
| Planned changes | 231 (31 review-sourced, 200 interface modules) — `evidence/E03`, `E06`, `E07` |
| Engineer decisions | 11 approved, 27 skipped, 146 proposed, 47 failed |
| Preview images | reconstructed offline: `renders/`, `crops/` |
| Apply input | `evidence/E01-apply-script-job121.redacted.scr` (original sha256 `e2daf55bfe7edf4f…`) |
| AutoCAD log | tail only (the full log is not kept on failure): `evidence/E13`, job error in `E02` |
| Outputs | 17 earlier applied DWGs (jobs 103–118 + job 119's PC-A run), hashes in E16; job 119 and 121 failed outputs: none (work copy unchanged) |

## Sub-cases (all within GC-01)

| ID | Covers (requested category) | Changes / evidence | Images |
|---|---|---|---|
| GC-01a | Interface modules CT1, CT2, CR; multiple devices at one wall; previous Apply failure; missing dependency | 7 approved modules on FA 101 pump room; jobs 119/121; F001 | crops/GC01-R02*, R03* |
| GC-01b | Wall-mounted devices on non-wall geometry; ambiguous geometry | CT2 ELECTRIC PUMP, CT2 ZCV; F005/F006; AI note "Pump room's bottom edge is unclear" | crops/GC01-R02* |
| GC-01c | Ceiling-mounted devices; symbol–text overlap | heat detector 3ddaa99cd7374341, E WP 45efbfb70918a4f0 (approved, engineer-moved) | crops/GC01-R02* |
| GC-01d | Wrong target in another room (REMOVE) | d89599d510abfedf (skipped) — F003 | crops/GC01-R06* |
| GC-01e | Wrong room / outside named room; dense symbols & notes | FA 108 swimming-pool pump room (9 review changes, all skipped) — F029 | crops/GC01-R07* |
| GC-01f | Drawing with external-discipline information; wrong cross-discipline transformation | FA 101 modules B3-SEF-1/3/4 outside PLOT LIMIT — F007 | renders/GC01-R01*, crops/R04*, R05* |
| GC-01g | Multi-sheet; typical plans; wrong floor mapping | FA 111/114/115 modules, 10 typical-plan mismatches — F026 | renders/GC01-R12* |
| GC-01h | Dense modules, doors | FA 117 roof (29 proposed modules) — F011 | renders/GC01-R10*, crops/R11* |
| GC-01i | Wall devices beside doors; orientation uncertainty | fire lift lobby phone jacks (FA 102 etc.) — F013 | crops/GC01-R09* |
| GC-01j | Previous Apply success | job 118 → `…Redesign 2026-10-02 1625.dwg` (sha256 `4a512056e70b64e6…`) and 15 earlier outputs | hashes only (DWG not renderable without AutoCAD/ODA) |
| GC-01k | AI repeated answers | 3ddaa99cd7374341, 1561933977450e28 — F028 | – |

## Requested categories not available

| Category | Status |
|---|---|
| Simple single-sheet drawing | **Missing** — only one 17-sheet drawing exists |
| Rotated or transformed drawing | **Missing** — all GC-01 sheets fit without rotation (residual ≤ 0.55 m); code has no rotation term (F021) |
| PDF or IFC (non-DWG) source | **Missing** |
| Doors and windows as modelled objects | Only visual (doors on plot); no data to test against |
| Second project / second consultant's CAD standards | **Missing** |
| Successful Apply output that can be inspected | Outputs exist but could not be rendered (no ODA converter; AutoCAD not run) |

## Sufficiency verdict

- **Sufficient for RD-M2 as proposed in `NEXT-MILESTONE-HANDOFF.md`** (Apply dependency resolution, drawn-set safety, output verification): GC-01a, GC-01d, GC-01j and the preserved script give a deterministic failing input and expected outputs.
- **Insufficient for any geometry, coordination or AI-quality milestone**: one drawing, one consultant's layering, no rotated sheet, no inspectable applied output. At least two more drawings (one rotated, one simple single-sheet) should be registered and reviewed by the owner before those milestones.
