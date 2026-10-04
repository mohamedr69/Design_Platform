# Next Milestone Handoff (from RD-M2)

**RD-M3 is not started and not authorised by RD-M2.**

## 1. Integrating the RD-M2 candidate (owner's step, after independent review)

The candidate (v2.1) exists only as an isolated copy and `evidence/rdm2-candidate.patch` (sha256 in `PACKAGE-MANIFEST.json`). It was not applied to the live tree, because the :8001 API hot-reloads `backend/app`. To integrate:

1. Wait for an accepting independent RD-M2 review.
2. Choose a quiet moment. Applying the patch reloads the G-drive API automatically; the IFC worker has no hot reload and must be restarted to pick up the new Apply.
3. Make sure no Apply or Plan job is queued or running (`fa_redesign_apply`, `fa_redesign_plan`).
4. Apply the patch to `ep-platform` (`git apply --check` first; the target files are untracked, so check the file hashes against `evidence/candidate-files.json → base_sha256_of_changed` before and `changed_sha256` after).
5. Restart the IFC worker.
6. The frontend change takes effect with Vite's hot reload.

No migration is needed. Existing rows keep working: legacy absolute `output_path` values are rebased at read time, and stored `insert.library` values are ignored for execution.

Expected first effects on GC-01:
- the 11 approved changes can be made (`AUTOCAD-VALIDATION.md`);
- `GET output.dwg` serves the existing `…1654.dwg` from this PC's uploads, via the rebased legacy path;
- the next Apply writes a new, uniquely named file under `uploads/EP-30880/redesign/` and nothing into the project archive.

## 2. Still open after RD-M2

| Finding | Status |
|---|---|
| F003 cause: AI answers accepted regardless of confidence/notes | Open (only its route to the drawing is closed) |
| F005/F006: wall index from raw layers, invisible and non-wall geometry | Open |
| F007, F026: interface anchors / typical plans | Open |
| F008–F012: coordination obstacles; unresolved clashes not flagged | Open |
| F013, F014, F028, F029: AI orientation, symbol-list overrides, variation, wrong room | Open |
| F018–F020, F025: provenance, GET writes, naming | Open |
| F021, F022: rotation, containment | Open |
| F027: rules not re-checked | Open |
| F031: archive publication | Disabled (decision 2); a controlled promotion is not designed yet (section 4) |
| F032 outside Apply: Plan/PATCH lost updates | Open |
| F024: leftovers | Partly: each Apply has its own run folder (kept by design as evidence); a retention policy is not defined |
| `ep_erase` | Verified with the real AutoCAD on a synthetic approved erase (session 2, control C); a *wrong-target* erase is tested only as script text and in unit tests |
| Output verification of existing entities' attributes | Not in the product (harness-only evidence in session 2); a check that tolerates `*U` renumbering and float normalisation is proposed |

## 3. Proposed next bounded milestone (proposal only)

**RD-M3 — "Wall geometry the drawing actually shows"** (F005, F006; groundwork for F022):
- build the wall index from **effective** layers (block content on layer `0` takes the INSERT's layer);
- skip entities with the invisible flag, and layers that are off, frozen or no-plot (including viewport freeze);
- replace the deny-list with an allow-list of wall layers, configurable per project;
- report the index's layer make-up;
- re-place GC-01's approved modules **offline** and show, on renders, that none sits on non-plotting or parking geometry.

It would not change coordination rules, the AI, or Apply.

Prerequisite: at least two more Golden Cases (one simple single-sheet drawing, one with a rotated view), registered and reviewed by the owner, because GC-01 alone cannot show that an allow-list generalises.

## 4. Future controlled promotion to the project archive (design note only; not implemented)

When the owner allows it:
- promote a **verified** platform output into `03- Drawings/Redesign/`, behind a flag that is off by default;
- use exclusive create (no overwrite), the same unique name, and record the archive-relative path and the promotion actor and time;
- refuse promotion when the output's snapshot is no longer current;
- never write to the archive during Apply itself.
