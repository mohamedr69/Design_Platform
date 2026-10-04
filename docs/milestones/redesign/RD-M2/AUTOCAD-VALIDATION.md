# Isolated AutoCAD Validation (owner decision 3, then the owner's authorisation of a second session)

**Result: PASS on candidate v2.** With the real AutoCAD 2027 Core Console on isolated copies:
- **A:** GC-01's 11 approved changes were made. AutoCAD printed one standalone OK marker. The output was read back and reconciled (11/11 inserts, no unexpected erasure) and published only inside the isolated output, with the source unchanged.
- **B:** a missing block saved and published nothing.
- **C:** a synthetic approved erase of one model-space symbol was verified by AutoCAD and by the read-back (exactly that handle gone).

The output differs from the source only as expected (section 3).

Session 1 (candidate v1) had found a log-parsing defect that refused a correct result. Session 2 is the re-validation of the fix.

## 1. Sessions and isolation

| | Session 1 | Session 2 |
|---|---|---|
| Authorisation | owner decision 3 ("one validation run") | owner's additional bounded session for v2, after a clean regression |
| When (UTC+4) | 2026-10-03 22:26:46 → 22:27:17 | 22:51:09 → 22:52:50 (A, B); 22:54:45 → 22:56:14 (C) |
| Candidate | **v1**, manifest sha256 `eb34898b…` | **v2**, manifest sha256 `5345c1e7998a40c821ed830e736e163cf3bb261b1dcd350bc7b67fe2d3a48a21`, re-hashed by the harness **before execution**: 381/381 backend files, 0 mismatch |
| Code location | `ISO/iso/code (2)/backend` | `ISO/iso2/{main,erase}/code (2)/backend` (paths with a space and parentheses, like `G:\dev (2)\…`) |
| Database | a copy of the RD-M1 snapshot | a **fresh** copy of the RD-M1 snapshot per root (sha256 `b50dfe2b…` verified). Session 1's copy was not reused, because its scenario B had injected a change into it |
| Drawings | copies of GC-01 DWG `66043c11…` / DXF `dbe7900f…` | the same, freshly copied per root |
| Output | `ISO/iso/uploads` (`UPLOADS_ROOT`) | `ISO/iso2/main/uploads`, `ISO/iso2/erase/uploads` |
| Not used | live DB, live uploads, project archive, running services, any API | same |
| Core Console processes | 2 (A, B) | 7 (A: Apply, source read-back, output read-back; B: Apply; C: Apply, source read-back, output read-back) |

Both sessions were rehearsed first with a stand-in for AutoCAD. The session-2 rehearsal caught the reuse of session 1's modified DB copy before any AutoCAD process ran.

## 2. Session 2 results (candidate v2)

| Check | A: 11 approved GC-01 changes | B: missing block first | C: synthetic approved erase (disposable copy) |
|---|---|---|---|
| Drawn set | 11 (4 review, 7 modules; 5 carry the office-PC stored path) | 12 (the missing-block change first) | 1 approved REMOVE of `5DD10` (`CEILING SPEAKER` at 1309.2, 155.93; a top-level model-space INSERT confirmed in the source DXF); every other change set to skipped **in the disposable copy only** |
| Library references in the script | `ISO/iso2/main/code (2)/…/library/{CR,CT1,CT2}.dwg`; no stored path | same | none needed |
| AutoCAD | all insert checks passed; `QSAVE` → `T`; exit 0; 62.6 s including both read-backs | `; error: Function cancelled` at the first insert, after which the script stopped; exit 0; 12.9 s | `ep_erase "5DD10" "CEILING SPEAKER" 1309.2 155.93 0.01` passed (INSERT, block, model space, within 0.01); `QSAVE` → `T`; exit 0; 60.2 s |
| Standalone markers | `EP-RD-OK:9dfc88469bf21d3b:11:0` (the echoed quoted copy is ignored by v2) | none | `EP-RD-OK:b591d5bde2853178:0:1` |
| Product verification (`verify.verify`) | **ok**, no problems | refused: completion marker missing; copy same as source; not read back | **ok**, no problems |
| Read-back reconciliation (source and output both converted by the same Core Console) | 11/11 inserts found at their points; `not_erased` [], `unexpected_erasures` [], `inserts_missing` [], `unexpected_inserts` [] | not attempted | `erased_as_expected` [`5DD10`]; everything else empty |
| Added entities vs expected | INSERT 11, CIRCLE 11, TEXT 18 = expected (11 markers, 11 labels, 7 module notes) | none | CIRCLE 1, TEXT 1 = expected |
| Saved work copy | published, then deleted from the run folder | `redesign.dwg` = source (`66043c11…`): **not saved** | published, then deleted |
| Published | `EP-30880/redesign/FIRE ALARM LAYOUT R0 - Redesign 20261003-185212-462213Z d1 s66043c11fab9 j0-658da456fa.dwg`, sha256 `32b90f64…`, inside `ISO/iso2/main/uploads` (checked), differs from source | **nothing** (`output_status = failed` in the DB copy) | `…20261003-185546-312016Z d1 s66043c11fab9 j0-da71d13bc8.dwg`, sha256 `e2be681f…`, inside `ISO/iso2/erase/uploads` |
| Stored `output_path` | relative (`EP-30880/redesign/…`), `output_relative` = None (no archive) | unchanged (failed) | relative |
| Source DWG copy before/after | `66043c11…` / `66043c11…` | same | same |
| Live source DWG before/after | `66043c11…` / `66043c11…` | same | same |

## 3. "Differs only as expected": every entity present in both read-backs, attribute by attribute

The harness compared all 4,807 (A) and 4,806 (C) model-space entities common to the source read-back and the output read-back. This is beyond the product's own handle reconciliation.

| Difference | A | C | Explanation |
|---|---|---|---|
| INSERTs whose block name changed | 43 | 43 | **all** anonymous dynamic-block references (`*U1059 → *U940` and so on). The referenced block content is identical (hashed without names or handles), and every other attribute is equal. AutoCAD renumbers anonymous blocks when it saves; the drawing is unchanged |
| Other attribute changes | 1 | 1 | ELLIPSE `5F6E3`: extrusion `(0, 0, -0.9999999999999998)` → `(0, 0, -1.0)`, a floating-point normalisation on save (Δ ≈ 2e-16) |
| Anything else | 0 | 0 | |

Evidence: `evidence/autocad/session2-v2-*/name-change-analysis.json`. The product's `verify.reconcile` does not yet compare attributes; this was harness-only evidence (`NEXT-MILESTONE-HANDOFF.md`).

## 4. Session 1 (candidate v1), for the record

- **A:** all 11 inserts verified, `QSAVE` → `T`, the copy saved. v1's `parse_log` counted the printed marker and its echoed quoted copy as two completion markers, so it **refused a correct result** and published nothing.
- **B:** as in session 2.
- The defect was fixed in v2 (whole-line markers). Session 2 proves the fix with the real AutoCAD.

## 5. Facts about this AutoCAD build (both sessions)

- After a LISP `(command …)` error, the Core Console **stops reading the script** and exits with code 0. The RD-M1 F004 continuation hazard does not occur in this build; the guards remain as defence in depth, and success is never inferred from the exit code.
- A printed marker is echoed again as a quoted string. Markers are therefore accepted only as whole lines.
- `_.QUIT` / `_Y` answers "Really want to discard all changes to drawing?", so it **discards**.
- AutoCAD writes `redesign.bak` and `ErrorReports/…/cer.log` into the run folder (its working directory).

## 6. Temporary files (session 2)

| | |
|---|---|
| New in `%TEMP%` during A/B | `ACAS{F575A04A…}.ac$`, `UNDO{B2A2AD9D…}.ac$`: **deleted** (AutoCAD-named, created within the session window, not locked). `5e314ad3-….tmp`, `accc63322`, `{F544EFFF-…}`: left (cannot be proven to be only this session's) |
| New during C | `UNDO{8E74B4BA…}.ac$`: conclusively this session's but **locked** by another process at the end and on one retry, so left. `659312c9-….tmp`, `acd9ad14b54.tmp`: left |
| Changed (existing) entries | `atil.…tmp`, `ogs`, an existing `.tmp`, the session's own scratch folder: not touched |
| From session 1 | its AutoCAD temp files were not deleted ("existing" by the time of session 2) and are listed in its record |
| Run folders | kept as evidence in the isolated area; scripts, full logs and `verification.json` are copied (redacted) into `evidence/autocad/` |
