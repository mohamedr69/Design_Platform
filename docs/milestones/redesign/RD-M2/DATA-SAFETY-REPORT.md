# Data Safety Report (RD-M2)

**Verdict: VERIFIED.** The task changed no live code, drawing, upload, database row or archive file. Machine-checked results are in `PACKAGE-CHECK.json`; this file explains what each check covers.

**The live platform was in use during RD-M2.** Between 17:27 and 19:05 UTC, user 5 signed in through the browser on the G-drive platform and created jobs 122–138 on the owner's running IFC worker:
- 16 Applies: 2 failed with RD-M1's CT2 error, then 14 succeeded with the *old* code's minute-stamp names;
- 1 Plan;
- accepted 156 review findings.

The live DB and uploads therefore changed. The checks below attribute every such change to that activity, and show that none is the candidate's or this audit's. This audit never signed in to the live API.

| Property | How it was ensured | Check in `PACKAGE-CHECK.json` |
|---|---|---|
| Live application code unchanged | All work happened in isolated copies; no file under the live `backend/` or `frontend/` was written. T0 (`RDM2-T0`) and a final re-hash (`RDM2-T1`) of every git-visible file in `ep-platform` match. The only new files are under `docs/milestones/redesign/RD-M2/` | `no_application_file_changes_in_live_tree` |
| Running services unaffected | No edit under the watched `backend/app`, so the :8001 `--reload` API never reloaded. Ports 8000, 8001, 5173, 5174 and 5175 are owned by the same PIDs as at the start | `running_services_unchanged` |
| Source drawings and library | GC-01's source DWG `66043c11…` and every `ifc/`, `review/`, `interfaces/` and library file are unchanged between T0 and T1, before and after both AutoCAD sessions | `source_drawings_and_library_unchanged`, `gc01_source_dwg_unchanged` |
| Other live uploads | 14 files were added, **all** exactly the outputs named by the owner's succeeded jobs 124–138. 3 files changed in `redesign/work-1/`, the running old code's shared work folder used by those jobs. No file with the candidate's naming, and no `runs/` or `source-readback-` path, exists in the live uploads | `live_uploads_changed_only_by_owner_activity` |
| Live database | Never opened for writing: tests used an in-memory DB, and the AutoCAD sessions used copies of the RD-M1 snapshot. Read-only probes (`mode=ro` + `query_only`, `total_changes` 0) show that every job since RD-M1 (122–138) has `created_by` user 5 and ran on the live IFC worker, and every activity row (973–995) has a user. The live Redesign row contains none of the candidate's markers (`rdm2-missing-block`, `rdm2-erase-control`, `confirmed`, `requires_confirmation`). AI usage is unchanged at 729 | `live_db_changed_only_by_owner_activity` |
| Project archive | The candidate has no archive write. The isolated roots contain no `03- Drawings` path. Each validation `output_relative` is `None` | `no_archive_path_in_isolated_run` |
| AutoCAD confined to copies | `cad.run` copies the source into a new run folder (`exist_ok=False`) and refuses to work when the copy's path equals the source's. Source and drawings were copies under `ISO`. Live and isolated source hashes are unchanged across both sessions | `AUTOCAD-VALIDATION.md` |
| RD-M1 package | Not modified: 78/78 manifest entries re-hashed, no extra files | `rd_m1_package_unchanged` |
| Candidate identity | v2.1 files equal to the frozen manifest; the patch in `evidence/` equals the frozen patch | `candidate_unchanged_since_freeze`, `candidate_patch_bound` |
| No private names | User-profile paths, host names, the project's name, the organisation name and the office user's name are redacted from every copied evidence file, then checked by a scan that reads those names from data at run time | `no_private_names_in_package` |
| No secrets | `.env` files were not read in RD-M2. No API key or password is in any evidence file | (scan) |

## Writes outside the repository (all in the session scratch area)

- `ISO/base`, `ISO/cand`: code copies.
- `ISO/tscheck`: frontend source copies plus **junctions** to the live `node_modules`, used read-only by `tsc`. The two first, malformed junctions were removed with `rmdir`, which removes only the link. The live `node_modules/.tmp` was hash-identical afterwards.
- `ISO/iso`, `ISO/iso2/{main,erase}`, `ISO/iso-dry`, `ISO/iso2-dry`: DB snapshot copies, drawing copies, run folders and published validation outputs.
- Python/pytest temporary folders under `%TEMP%`.
- AutoCAD temporary files under `%TEMP%` (see `AUTOCAD-VALIDATION.md` §6). Two were deleted (conclusively session 2's, unlocked). The rest were left: either uncertain, or locked by another process.

## Not done

No live endpoint call. No live Plan, Apply, Sync, Repair or Reprocess. No service start, stop or reconfiguration. No migration. No commit or push. The patch was not applied to the live tree. RD-M3 was not started.
