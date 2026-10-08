# M5 real-console validation run (ORCH-046, OD-16 c)

Role ep-implementer, Claude Opus 5.5, high effort. Run 8 October 2026, 02:41-03:21 UTC.
Code: `roadmap/u2` at `37350bc` (contains fcc5ddd and 72f49a5). No application code was edited. No model, provider, `claude` CLI, network or `pip install` was used. Evidence class: **REAL CONSOLE (DWG TrueView 2026 Core Console), not full AutoCAD.**

## 1. Machine, console, profile

| Item | Value |
|---|---|
| Computer name | `LAPTOP-IL4L4UAJ` (Windows 10 Home 10.0.19045) |
| Console | `C:\Program Files\Autodesk\DWG TrueView 2026 - English\accoreconsole.exe`, file version 25.1.164.0.0, banner "AutoCAD Core Engine Console ... (W.164.0.0)", sha256 `fd4b36cf...c41ec9`. No full AutoCAD is installed. |
| Dedicated profile | `/isolate m5cad C:\t\tmp\m5cad\profile` (the console created `Local`, `Roaming`, `Temp` there; 7.2 MB). TEMP for every harness run: `C:\t\tmp\m5cad\tmp`. |
| Outside that profile | Disclosed in `environment.json`: the first usage probe (p0) ran without `/isolate`; 84 zero-byte `accc*` redirect files in `%TEMP%` (deleted); the default `%LOCALAPPDATA%\...\R24\enu` folder's directory timestamp changed during s9 although no file in it changed; no registry key named `m5cad` was found. |
| Isolation | Fresh SQLite `C:/t/tmp/m5cad/db/m5cad.db`, uploads `C:/t/tmp/m5cad/uploads` (project EP-90880, not EP-30880), archive `C:/t/tmp/m5cad/archive` (empty at the end). Scratch at the end: 75 MB. |

## 2. What the TrueView console can do (probes p1-p8, `probes/cmdprobe.json`)

- **No AutoLISP:** every `(` line answers "LISP command is not available."
- **Unknown commands:** `-INSERT`, `INSERT`, `ERASE`, `SAVEAS`, `QSAVE`, `SAVE`, `DXFOUT`, `AUDIT`, `LINE`, `CIRCLE`, `BLOCK`, `PURGE`, `FILEDIA`, `CMDDIA`, and others.
- **Known commands:** `LIST`, `-WBLOCK`, `OPEN`, `-LAYER`, `SETVAR`, `TILEMODE`, `ID`, `ZOOM`, `REGEN`, `XREF`, `PLOT`, `EXPORTPDF`, `PUBLISH`, `CLOSE`, `QUIT`.
- **Script stops at the first error.** At the first unknown command the console stops reading the script and exits with **code 0**.
- **It cannot modify or save a drawing.** `-WBLOCK *` writes an unmodified copy of the whole drawing (p6).
- **It can read a drawing back.** `LIST` of `ALL` reads GC-01: 4,947 selected (158 not in model space), 5,899 listed records with handles, 2,418 block references (p5).
- **Echo.** Each script line is echoed on a line of its own (p8).
- **No writable TEMP.** The console fails with "Failed to redirect stdout" and exit code 1.

So the merged Apply script (all AutoLISP from line 1, `_.FILEDIA`) cannot run on this console. As the card allows, this run proves script execution, marker handling, refusal, cancel and kill paths, the placing functions and read-back of an unchanged file. It does not prove drawing.

## 3. Method

The harness `harness/m5cad.py` runs `service.apply` / `publish` / `sweep_orphans` from a byte copy of the code (`git archive`, LF; `cad.py` `43672b30...`, `verify.py` `449ad1af...`). The copy sits at `C:\t\tmp\m5cad\code\ep platform (m5 copy)\backend`, so the library path has spaces and parentheses. `BOQ_ACCORECONSOLE` and `ACCORECONSOLE_PATH` point at the TrueView console.

Harness interventions:

- `cad._command`, the code's test seam, is wrapped only to **append** `/isolate`.
- s9 wraps `convert.subprocess.run` the same way.
- `readiness` returns ready and `_units` returns 1.0, exactly as the suite's `gc` fixture does. The drawing is in metres (LIST: "Unit conversion 0.0010").

Seeded changes:

- They come from real GC-01 entities read by the console's LIST.
- Approved: **r1**, an add of `HEAT DETECTOR`; **rm**, an erase of `CEILING SPEAKER` 63868; **m1**, the CR interface module with a stored office-PC path.
- Not approved: **p1**, proposed; **s1**, skipped, `6382A`.
- An "earlier made copy" was seeded as a **byte copy of the unchanged GC-01 copy**. It is not an Apply result; it exists only for the "stays downloadable" check.

Deviation: `backend/library` (495 MB) was not copied. The Redesign blocks are in `backend/app/redesign/library`, which was copied with `app/`.

## 4. Results per item (card numbering)

| # | Item | Verdict | Evidence |
|---|---|---|---|
| 1 | Approved inserts/erases reconcile; proposed not drawn | **NOT PROVABLE WITH THIS CONSOLE** (reconciliation). The proposed-not-drawn part is **PROVEN at script level**. | `runs/j1-*/redesign.scr`: lines for r1, rm, m1; no p1, s1 or `6382A`; `ep_erase "63868" "CEILING SPEAKER" 2950.5865 144.3098`. The console executed none of it. |
| 2 | Missing block / script error / marker / incomplete script publish nothing | **PROVEN** for: missing library file (s2: refused before any console start, "the CR module's file is missing", no run folder, nothing published); a real script error (s1: the console stopped at `_.FILEDIA`, exit 0; verify gave "completion marker is missing; same as the source"; status `failed`); marker absence read correctly; incomplete script fails. **NOT PROVABLE:** a missing block inside the drawing (LISP `ep_new_insert`), the count check before QSAVE, and the marker's presence. | `results/s1-*.json`, `s2-*.json`, `runs/j1-*/autocad.log`, `verification.json` |
| 3 | Saved output valid DWG; earlier output stays downloadable | Valid saved DWG: **NOT PROVABLE** (no save). Earlier copy downloadable: **PROVEN** after s1-s4 (`view.output.available` true, `last_output` unchanged) and s5/s5b (row `output_path`/`output_at` unchanged); file sha unchanged at the end. Publishing it was refused with 422 "Only a copy Apply made and verified..." (s7). The console-only fact that its own `-WBLOCK *` file reopens and lists equal by type, layer and point (p6/p7; handles renumbered) involves no platform code. | `results/s1..s7`, `probes/p6-p7-compare.json` |
| 4 | Library paths with spaces resolve at script time | Script-time resolution **PROVEN**: the script carries `"CR=C:/t/tmp/m5cad/code/ep platform (m5 copy)/backend/app/redesign/library/CR.dwg"`; the stored `someone-else/OneDrive - Org` path is absent. A real `-INSERT` with it is **NOT PROVABLE**. The console does accept a quoted path with spaces and parentheses at a file prompt (p6). | `runs/j1-*/redesign.scr`, `probes/p6.log` |
| 5 | Cancel/kill publishes nothing, no final-named output, `.part` swept | **PROVEN** for cancel (s3): the console PID 13716 was killed by the code while it loaded the drawing, the status is `cancelled`, there is no new output and no `.part`. **PROVEN** for an external console kill (s4): exit 1, `failed`. Worker hard kill (s5, s5b): nothing published, **finding F1**. **NOT EXERCISED:** a `.part` in `redesign/publishing/`, because no verified copy can reach staging. The sweep (s6) moved and removed nothing, and it skipped the project while the killed jobs were active. | `results/s3..s6` |
| 6 | Source byte-unchanged | **PROVEN**: sha256 `66043c11fab9eaf5a1768ba24ed924821baecec3b6726ee70f6c529300ceec21` before (02:41:36Z) and after (03:21:29Z), and before and after every scenario. All 5 run copies equal it. | `environment.json`, `results/*.json` |
| 7 | Hard link / rename per volume | **PROVEN** on this PC's local NTFS volumes (s8): same volume C: uses a hard link (`_finalize` and `_into_archive`, nlink 2). Second volume G: `os.link` gives WinError 17, so `_into_archive` falls back to an exclusive copy (nlink 1, sha equal). Each name, once taken, is refused on the second attempt with the file unchanged. `_finalize` across volumes raises WinError 17; Apply never does this, because it finalises inside its own folder. A OneDrive-synced archive was not tested. | `results/s8-volumes.json` |

Delivery-record item 6 also names "timeout". The 20-minute timeout was not exercised; it uses the same kill path as cancel.

## 5. Findings (no code changed)

- **F1 (Low).** A hard-killed worker does not kill its Core Console. The console outlived the killed interpreter by about 10 s here, until its script ended. The row stays `making` and the job `running` until recovery. With full AutoCAD the orphan would go on to QSAVE the run-folder copy, which would never be published. Option for the owner: a Windows job object with kill-on-close.
- **F2 (Info).** A script line that literally is a marker is echoed as its own line, and `parse_log` counts it (p8). The code's script contains no literal joined marker (0 occurrences), so the run-time `strcat` design is necessary and holds.
- **F3 (Info).** The code's command line has no `/isolate`; production would use the default console profile.
- **F4 (Info).** The read-back converter refuses cleanly on this console: `ConversionError` at `FILEDIA` (s9). `find_converter` labels any configured path "AutoCAD Core Console"; its own search never picks TrueView.

## 6. Needs full AutoCAD

The following still need full AutoCAD:

- exact insert/erase reconciliation;
- the in-drawing missing-block and LISP-error refusals;
- the count check before QSAVE;
- a real `EP-RD-OK` marker;
- a saved, reopened output;
- `-INSERT` from a library path with spaces;
- `.part` staging during a real publication;
- the timeout kill;
- hard links on the real (synced) archive volume.

**M5 condition C1 stays open.**
