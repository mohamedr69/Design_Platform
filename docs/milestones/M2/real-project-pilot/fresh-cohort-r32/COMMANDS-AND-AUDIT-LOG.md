# Commands and audit log (cohort preparation, initial pool)

**Environment:**
- Python: `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`, with `PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1`.
- Work folder: `C:/t/iso/work/r2x/r32`. Staging: `C:/t/r2x/r32-stage`.
- Model or provider requests: **0**.

| # | When (UTC) | Command | Result |
|---|---|---|---|
| 1 | 2026-10-02 ~18:40 | read-only hash check, written to `PRE-AUTHORIZATION-HASH-CHECK.json` | all frozen hashes match |
| 2 | 2026-10-02 18:55 | owner authorization, recorded verbatim in `AUTHORIZATION-2026-10-02.md` | "I authorize this" |
| 3 | after 2 | `verify_projects_r32.py` (Review 31 `selector_core` and `used_sets`, unchanged) | 10 of 10 pass; cohort = the 6 primaries |
| 4 | after 3 | `select_pool_r32.py`: first attempt stopped on a path longer than 260 characters; fixed with the `\\?\` prefix, then run | `FROZEN-SELECTION.json` `bf71779a…` (written once, after the fix) |
| 5 | after 4 | `stage_r32.py pool` | 72 staged, 0 failed; `SOURCE-MANIFEST.json` `951e8697…` |
| 6 | after 5 | `render_r32.py pool` | 149 pages, 0 unsupported; `RENDERS.json` |
| 7 | after 6 | `crop_r32.py`: first test crop failed (wrong clip space, nothing written); fixed to displayed coordinates | 189 crops logged in `CROPS.jsonl` |
| 8 | before the first label | `LABEL-CONVENTIONS-R32.md` frozen | `5c09d4d2…` |
| 9 | labelling | 72 drafts written in `drafts/F###.json` (the `lib/` helpers write recurring layouts from values read by the drafter) | 72 drafts |
| 10 | after 9 | `validate_drafts_r32.py` | 0 problems |
| 11 | after 10 | `assemble_draft_r32.py` | `labels/R32-LABELS-DRAFT-1.json` `ebd1e24d…` (immutable); projection written |
| 12 | after 11 | `make_review_packet_r32.py` | worklists, questions, response template, evidence index |
| 13 | after 12 | `package_r32.py`, then `verify_r32_packet.py` | packet folder and checker result |

**Notes:**
- **Crop orientation:** some crops of rotated sheets were first taken at 270° and came out upside down. They were re-taken at 90°, and both are kept in `CROPS.jsonl`. Drafts cite the readable ones.
- **Duplicates found during staging:** F038 = F052 and F067 = F070. Convention 1, frozen before labelling, counts each pair once.
- **Live application database:** `ep-platform/backend/ep_platform.db` keeps changing because the owner's running uvicorn server writes to it. No step here wrote to it; `used_sets` opens databases read-only.
