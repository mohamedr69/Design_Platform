# Next Milestone Handoff (from RD-M1)

**RD-M2 is not authorised by RD-M1.** This is a proposal for the owner and the independent reviewer. Nothing below has been started.

## Proposed RD-M2 — "Apply fails closed and makes only what was approved"

One bounded task, limited to stages 18–25 of `CURRENT-PIPELINE.md`. No change to placement, coordination, the wall index, the review or any AI prompt.

### In scope

| # | Change | Fixes | Acceptance test (offline, GC-01 snapshot, no model, no live DB) |
|---|---|---|---|
| 1 | Resolve each interface module's library file **at script time** from the running code's `app/redesign/library/<CODE>.dwg` (by `interface.code`), never from the stored absolute `insert.library`; refuse with a clear error if the file is missing | F001 | Regenerating the GC-01 Apply script (as `reproduce_apply_input.py` does) yields no path outside the running library folder; all 7 module inserts reference the same existing folder |
| 2 | Make the script fail closed: no `entlast`/`entdel` unless the measuring insert actually created a new INSERT of the expected block; on failure stop before `QSAVE` and report which change failed | F004 | Script text test with a deliberately missing block: the script contains a guard before every `entdel`, and an abort path that skips `QSAVE` |
| 3 | Verify the output: after AutoCAD, check (in the log or a read-back) that each expected insert/erase happened and nothing else was erased; keep the AutoCAD log with the job | F023 | Unit test on a recorded log; AutoCAD run only under item 6 |
| 4 | Drawn-set gate: draw only `approved` changes (owner decision A), and make the page wording match | F002, F003 (exposure) | Regenerated GC-01 script with one review change set to `proposed` contains no insert/erase for it |
| 5 | Apply job idempotency and portability: do not re-run an Apply whose row already shows a newer `output_at` than the job's `created_at`; store `output_path` relative to the uploads root | F016, F017 | Unit tests on `recover_stale` + a synthetic row; GET `/output.dwg` resolves a relative path |
| 5b | Unique output names (no same-minute overwrite in uploads or archive); Apply honours cancel; `confirm`-flagged inserts not drawn until confirmed | F033, F034, F035 | Unit tests on name generation, the `check` callback and `_drawn` |
| 6 | One AutoCAD run of the GC-01 Apply on an isolated copy, **only if the owner authorises** AutoCAD writing outside the isolated folder (user-profile temp/`ErrorReports`, registry) | evidence for 1–3 | Output DWG saved in the isolated folder; source sha256 unchanged; output read back |

### Out of scope for RD-M2

Wall index (F005/F006), interface anchoring (F007, F026), coordination model (F008–F012), room containment (F022), geometry fit (F021), AI answer validation (F013, F014, F028, F029), provenance, read-side writes and concurrency (F018–F020, F032), engineering rules (F027), the archive write (F031) unless decision B says otherwise.

### Owner decisions needed before RD-M2 starts

- **A.** Should review-sourced changes require explicit approval before they are drawn (today they are drawn while `proposed`)?
- **B.** May Apply keep writing the redesigned DWG into the project archive folder (`03- Drawings/Redesign`)? The platform's own config says the archive is read-only.
- **C.** Is an AutoCAD run on an isolated copy authorised (item 6), given that `accoreconsole` writes to the user profile?
- **D.** What to do with the 6 stored changes that carry PC-A library paths (repair in data, or leave as history and resolve at script time only)? RD-M1 changed nothing.

### Inputs RD-M2 should reuse

- DB snapshot sha256 `b50dfe2b14ae381158cb47778651f8ce9bcf3dbed985e7b3af81a0821a8df8f0` (kept outside the repo).
- Preserved failing script sha256 `e2daf55bfe7edf4f9d0f93d0c646135b5eb4c9119bfd7b3af37e854ef9d019a0` and `evidence/E18-reproduce-apply-input.json` (byte-identical regeneration).
- Golden sub-cases GC-01a, GC-01d, GC-01j (`GOLDEN-CASE-SELECTION.md`).

## Later milestones suggested by the inventory (unordered, not authorised)

- **Geometry:** wall index from effective layers with visibility, allow-list of wall layers; room/building containment; registration check for trade-drawing anchors; rotated sheets. Needs more Golden Cases first.
- **Coordination:** existing text, notes, doors/swings, windows, equipment and other disciplines as obstacles; report unresolved clashes.
- **AI answer validation:** confidence/notes gate REMOVE/REPLACE targets and orientation; record the symbol list sent; record overrides.
- **Workflow provenance:** per-decision who/when; no writes from GET; AI calls linked to jobs.
