# Independent Review of RD-M1

The reviewer was a separate read-only agent that did not produce the audit. It wrote only to its own scratch folder, made no git writes, called no endpoints, did not run AutoCAD and made no model calls through the platform. Its round-1 report is reproduced verbatim below. The producer's change log follows it. The producer does not approve the package.

---

## Round 1 — reviewer's report (verbatim)

# Independent review of RD-M1 (Redesign: Freeze, Baseline & Failure Inventory)

**Verdict: CHANGES REQUIRED**

The core of the package holds up. I checked the source and evidence bindings, data safety, the regeneration of the Apply input, the package hashes and the main findings (F001, F002, F003, F017), and they are accurate. The changes needed are bounded documentation fixes, not a re-audit:
- one claim marked "confirmed by data" goes beyond what the data shows (F006 / conclusion 7);
- the wall-index failure has a cause the package did not find;
- two failure classes were missed;
- several evidence line references are wrong.

What I did: I wrote only to `…\scratchpad\rdm1-review\`, and pointed TEMP/TMP there for the venv runs. I ran no git writes, called no HTTP endpoint, ran no AutoCAD and made no model call. I opened the live DB twice, read-only (`mode=ro` + `query_only`, `total_changes` = 0).

---

## 1. Source and evidence bindings: PASS
- **Source and case files.** I recomputed SHA-256 for each file; all match E16, BASELINE-MANIFEST and PACKAGE-CHECK:

  | File | SHA-256 |
  |---|---|
  | `ifc/60de2a377daa.dwg` | `66043c11…ec21` |
  | DXF | `dbe7900f…c14f` |
  | Review PDF | `2dd28b04…2dae` |
  | Wall pickle | `9e5a94c1…6197` |
  | `work-1/redesign.scr` | `e2daf55b…19a0` |
  | `work-1/redesign.dwg` | `66043c11…ec21` (equals the source, so AutoCAD never saved the copy) |
  | CT1, CT2, CR, `modules.json` | match |
- **Database bindings.** In the snapshot, `project_redesign.source_sha256` and `project_drawing_reviews` row 1 `source_sha256` both equal `66043c11…ec21`. `project_ifc_drawings` row 1 `source_sha256` is NULL, as the package states.
- **Snapshot and baseline files.** The snapshot hashes to `b50dfe2b…f8f0` and BASELINE-T0.json to `fc655e60…839b`; both match the manifest.
- **Images.** I checked all 26 render/crop PNGs against E17 and PACKAGE-MANIFEST: 0 mismatches. I also re-rendered all 13 pairs into my own folder with `render_case.py`; they are byte-identical to E17.

## 2. Live-data non-mutation: PASS (adequate)
- **Full re-hash against BASELINE-T0.** I re-hashed every file the baseline lists, not a sample:
  - 740 of 740 git-visible files unchanged;
  - 1,867 of 1,867 upload and library files unchanged;
  - in the outer repo only `worker-g.stderr.log` changed.
  - This covers `redesign/*.py`, `routers/redesign.py`, `test_redesign.py` and the frontend page.
- **Git status.** `git status -uall` compared with `git-status-ep-T0.txt` differs only by 74 new entries, all under `docs/milestones/redesign/RD-M1/`. HEADs `13eb73c` / `e2d8cfd`, gitlink `d3bea8b`, and the 50 M / 58 ?? counts all match.
- **Gap at the start of the audit.** T0 (19:46:01) was taken about 3 minutes after the audit began (about 19:43). I closed this gap independently: no file under `ep-platform` (venv and node_modules excluded) is newer than 19:40 except the live DB, its WAL and the package directories. `.git/index` was touched at 19:43:30, which the package discloses.
- **Live DB unchanged.** My read-only probe shows the live DB equals the snapshot:
  - redesign row `updated_at` 15:28:00.097343;
  - maximum job / activity / ai_usage ids 121 / 972 / 729;
  - identical hashes of the `changes`, `symbols`, `calls`, review `sheets` and `decisions` blobs.
- **Minor wording issue.** The report says "the WAL grew during the audit". The WAL is still 5,730,952 bytes; only its mtime changed.

## 3. Pipeline map completeness: PASS
- **Stages.** CURRENT-PIPELINE.md has 25 numbered stages with all the requested columns. I could not compare them against the original task's wording of the 25 stages; they cover the expected chain.
- **Code references.** I spot-checked about 45 file:line references against the code. All are correct, including:
  - `routers/redesign.py:41-58`, `:70-104`, `:158-169`, `:172-183`;
  - `review/render.py:26-48`, `:59-96`;
  - `review/geometry.py:35-104`;
  - `interfaces/service.py:423`, `:621`;
  - service.py: S:97-119, 178-192, 275-312, 315-359, 394-441, 455-500, 503-597, 600-614, 617-647, 650-664, 667-671, 677-746, 749-821, 824-1060, 1063-1092, 1095-1190, 1134, 1196-1249, 1252-1268, 1282-1301, 1304-1357, 1312-1314, 1376, 1383-1404, 1416-1449;
  - `cad.py:52-140`, `:114-121`, `:143-176`;
  - `walls.py:25-26`, `:151-197`;
  - `ai.py:58-81`;
  - `jobs.py:101-106`, `:351-396`;
  - `runners.py:266-293`;
  - `ProjectRedesignPage.tsx:215`, `:292`, `:461`.
- The only drift is S:385-387, which is actually at 384-386.

## 4. Finding reproducibility
- **F001: confirmed.** In the snapshot, 6 interface changes carry `C:/Users/<PC-A>/OneDrive - <org>/…/library/CTx.dwg`: 5 approved and 1 proposed, all `moved` and `edited`. The other 147 carry the G: path, and `row.symbols` holds G: paths.
  - The `refresh()` stale test (S:1312-1314) finds 0 stale changes, so Apply only re-coordinates.
  - `_merge_interfaces` (606-609) keeps moved or edited modules as they were.
  - `cad.py:117` emits the stored path.
  - In the original script, PC-A paths are on lines 51/60/69/78/87 and G: paths on 96/105.
- **Regeneration: confirmed.** My own script, `repro.py`, regenerated the Apply input. It reads the snapshot directly (not the producer's dump), uses the original wall pickle and the isolated code copy (216 files compared with the repo, 0 mismatches) and runs on the venv interpreter.
  - Result: 11 drawn changes, coordination `seen`/`model` differences = [], regenerated script sha256 `e2daf55b…19a0`, byte-identical to the preserved script.
  - `test_redesign.py` on the copy: 16 passed.
- **F002: confirmed.** `_drawn` (S:667-671) draws review changes in `proposed`; the page labels them "Placed, to approve" (`:292`).
  - Severity nuance: each such change was accepted by an engineer in the review; only its placement or erase target is unapproved. Critical is defensible together with F003.
- **F003: confirmed.** Change `d89599d510abfedf`: REMOVE CS, AI candidate 11, confidence low, note "nearest CS #11 is in lift lobby".
  - The platform set `remove` = handle `5DD10` with `erasable=True`, 107.2 pt × 0.0617 m/pt ≈ 6.62 m from the review point. Status `skipped`.
  - `read_answer` (ai.py:74) and `_place` (S:766) apply no confidence or room check.
- **F005: confirmed, but the package missed a cause.** I rebuilt the wall-index filter from the DXF copy:
  - 92,093 segments kept; their unique set (90,302) is identical to the pickle's;
  - 28,491 segments on raw layer 0 and 9,461 on 06-WALL;
  - the probe segment at x = 714.557 is raw `0` inside `*U442`, with effective layer `…$0$29-PARKING`, which `NOT_WALLS` (PARK) would exclude.
  - **Missed cause:** `walls.build` ignores the DXF entity `invisible` flag (group 60). **4,351 of 92,093 index segments (4.7%) come from invisible entities**, including 6 of the 11 `*U442` segments in the F006 probe.
- **F006: placement confirmed; the "non-plotting" claim is not supported by the package's data.**
  - The modules do sit on that line:
    - CT2 FOR ELECTRIC PUMP at (714.764, 157.090) on face x = 714.557;
    - CT2 FOR ZCV at (714.351, 162.0).
  - Visually, nothing is plotted there in crop R02 A.
  - But E11 records `visible=True` for every segment of the probe it labels "invisible-rect". Layer 29-PARKING is on, not frozen, plots (colour 8), and is not frozen in the FA 101 viewport.
  - The segment under ZCV (y 161.288–162.588) has `invisible=1`. The segment under ELECTRIC PUMP (y 156.288–158.788) has `invisible=0`, so why it does not plot remains unexplained.
- **F013 / F014 / F026 / F029: confirmed from data.** 15 of 31 answers state rotation or facing uncertainty; 8 changes have `ai.symbol==0` but a block inserted (the ids listed); failures split 35 / 10 / 2; `5d2de6f964bab9e3` says "Placed outside".
- **F007: renders consistent.** Renders R01, R04 and R05 agree with the description of B3-SEF-1, -3 and -4. This remains a visual proposal.
- **F017: confirmed.**
  - Job 119 was created 2026-10-02 12:54:19 by user 5 on PC-A.
  - The row's `output_at` is 12:55:35 (`…1654.dwg`, 11 changes).
  - PC-A's sync-worker last heartbeat was 12:55:33, which suggests the DB was copied mid-job.
  - On PC-B, `started_at` is 2026-10-03 15:15:05, `attempts` = 1 and the worker is `ifc:LAPTOP…`, and the E13 log shows "requeued", then a failure 58 s later.
- **F020: confirmed.** 44 rows, all with `run_id` NULL, 11 cache hits; 7 fall outside job 102's window (ids 686-690 and 728-729). No other `fa_redesign_plan` job exists, so their origin is genuinely unknown.
- **F028: confirmed.** 2 `result_cache` keys have 2 rows each.
- **F023: confirmed.** `cad.py:167` checks only that the file exists and its mtime changed.

## 5. Missing failure categories: FAIL (needs additions)
All eight categories A–H are represented, but these significant failures are absent:
1. **G, workflow/persistence: no concurrency control (lost updates).** Confirmed by code, not reproduced.
   - `plan()` rewrites the whole `row.changes` from its start-time list after every answer (S:1175), so an engineer's PATCH made during a Plan (job 102 ran 3.5 min) is overwritten.
   - `adjust` and `set_status` have no status or version guard.
   - Plan and Apply have different dedup keys (`router:74`), so they can run at the same time.
   - `refresh()` commits the row whenever coordination touches anything; that is 25 on GC-01, so every Apply rewrites the row.
   - Suggested severity: Medium–High.
2. **H, Apply: output name has minute resolution.** The name uses a `%Y-%m-%d %H%M` stamp (S:1383-1386), and `cad.py:170` / S:1396 (`open(...,"wb")`) overwrite silently. A second Apply in the same minute replaces the earlier DWG in uploads and in the archive. Jobs 103 and 104 ran 76 s apart. Suggested severity: Low–Medium.
3. **A, extraction: invisible entities (group 60) enter the wall index.** 4.7% of segments; see §4. This should be a secondary cause on F005 or its own finding.
4. **Minor:**
   - `apply()` accepts `check` but never uses it, so a running Apply cannot be cancelled (up to 1,200 s).
   - `_drawn` ignores the `confirm` flag (residual above 1 m). Not triggered on GC-01.

## 6. False or unsupported root-cause claims: FAIL (one overclaim, several reference errors)
- **Overclaim.** Report conclusion 7 says "Confirmed by data and geometry: approved modules are mounted on a non-plotting parking-block line (F006)". The data confirms only that the modules sit on parking-block geometry admitted through raw layer 0. That the line does not plot is visual, and contradicted by E11 `visible=True`. For part of the line the invisible flag explains it; for the segment under ELECTRIC PUMP nothing in the evidence does.
- **Unqualified percentage.** "≈10% of segments are on a wall layer" is by raw layer. The effective layer of the 31% on layer 0 was not determined, so this needs a qualifier.
- **E01 line numbering.** The E01 header says "line numbers below are original line + 1"; the actual offset is +2.
  - Report conclusion 6 and F001 cite "E01 line 51" and "E01 lines 51/60/69/78/87 vs 96/105". Those are original-script numbers; in E01 they are 53/62/71/80/89 vs 98/107.
  - F004's "E01 lines 51-54" is ambiguous.
  - F015 uses +2 correctly.
- **Reproduction paths.** F005's reproduction ("python evidence/scripts/wall_layers.py") does not work as written. `wall_layers.py`, `effective_layer.py` and `render_case.py` resolve the DXF and their output as `HERE/../src` and `HERE/../work`, so they must be copied to ISO/scripts. The runbook only mentions editing constants.
- **Severities and AI labelling.** Other severities are reasonable. AI-visual findings (F006, F007, F009–F011, F029) are correctly labelled as proposals.

## 7. Package hashes: PASS
All 73 PACKAGE-MANIFEST entries match on disk by sha256 and size; the byte total is 8,966,015. The only file on disk not in the manifest is `PACKAGE-MANIFEST.json` itself, which is expected.

## 8. Verdict and conclusions
- **No readiness or approval claims.** The report claims neither production readiness nor human approval, states that all findings are unreviewed, and does not grant RD-M2.
- **The ten conclusions:**
  - 1–6 and 8–10 follow from the evidence. Conclusion 1 ("partly proven") I reproduced independently.
  - Conclusion 7 overstates F006, as described in §6.
- **"Ready for independent review" is justified** as a hand-off state. The package should not be accepted until the required changes below are made.

## Required changes
1. Reword conclusion 7 and F006: "on parking-block geometry admitted via raw layer 0 (effective `29-PARKING`, which `NOT_WALLS` would exclude); not plotted per visual review; partly explained by the DXF invisible flag, otherwise unexplained". Reconcile or annotate E11's `visible=True`.
2. Add the invisible-flag cause to F005 (`walls.py:159-165` does not check `dxf.invisible`; 4,351 of 92,093 segments), or add it as a new A finding.
3. Add a G finding for concurrent writes / lost updates (S:1175, 1146, 1324-1325, 1247; router dedup per kind).
4. Add an H finding for same-minute output-name overwrites (S:1383-1386, 1396; `cad.py:170`).
5. Fix the E01 header offset (+2) and the E01 line citations in report conclusion 6, F001 and F004.
6. Qualify the "≈10% on a wall layer" figure as raw-layer only.
7. Correct the F005 and runbook reproduction instructions for the HERE-relative script paths.

## Non-blocking notes
1. "The WAL grew" should read "the WAL was rewritten (mtime changed; size constant)".
2. The T0 baseline was taken after the audit began. My mtime scan covers that gap, and the data-safety report should say so.
3. The org-name variant (the sibling clone folder's name) appears in RD-M1-REPORT.md:28, GOLDEN-CASE-SELECTION.md:7 and `evidence/scripts/hash_tree.py:77`. The private-name check did not catch the variant. *(Producer note: the folder name is replaced by a placeholder in this copy of the reviewer's text, so the package does not repeat it.)*
4. F002: state that review changes were accepted in the review; it is the AI placement that is unapproved.
5. F017: add the likely reason job 119 was still running in the copied DB — it was copied between the output commit (12:55:35) and the job finishing (PC-A sync heartbeat 12:55:33).
6. Not verified by me:
   - the other three test files (I re-ran only `test_redesign.py`);
   - AutoCAD behaviour after a LISP error (F004);
   - the archive copies (F031);
   - the Desktop deployment.

---

## Producer's change log after round 1

| Review item | Change made |
|---|---|
| Required 1 | Report conclusion 7 and F006 reworded: the modules sit on parking-block geometry admitted via raw layer `0` (effective `29-PARKING`). Not plotting is a *visual* observation, explained by the invisible flag for the ZCV segment only and otherwise unexplained. F006 evidence now states that E11 `visible` reflects layer state only. |
| Required 2 | F005: added the invisible-flag cause (4,351 / 92,093 segments, 3,973 on raw `0`). The producer re-ran the count (`evidence/scripts/invisible_flag.py`, adapted from the reviewer's `invis.py`) and got the same number. |
| Required 3 | New **F032** (High, G): no concurrency control / lost updates. Code verified by the producer. |
| Required 4 | New **F033** (Medium, H): minute-resolution output name with silent overwrite. Code verified. |
| Minor (§5.4) | New **F034** (Low): Apply ignores `check` (cannot be cancelled). New **F035** (Low): `confirm` flag not gating `_drawn`. |
| Required 5 | E01 header now says "+ 2"; report conclusion 6, F001 and F004 cite original line numbers with their E01 equivalents. |
| Required 6 | "≈10%" qualified as by raw layer, in the report and in F005. |
| Required 7 | F005 reproduction and runbook §0/step 6 now say to copy the scripts to `ISO/scripts/`, and list which scripts use absolute constants. |
| Notes 1, 2, 4, 5 | WAL wording fixed; T0-timing note added to DATA-SAFETY-REPORT; F002 and F017 wording added. |
| Note 3 | The folder name is replaced with "sibling clone folder" in the report and Golden Case file, and redacted in packaged scripts; `PACKAGE-CHECK.json` now scans for that pattern too. |
| S:385-387 drift | Corrected in round 2 to "service.py:381-393 comment block". |
| Counts | 35 findings: Critical 2 · High 9 · Medium 18 · Low 6. |

## Round 2 — reviewer's verdict and notes (summary of the reviewer's report)

**Verdict: ACCEPT WITH NOTES.**

| Check | Reviewer result |
|---|---|
| (1) The 7 required changes | All PASS. The round-1 non-blocking notes (WAL wording, T0 timing, F002/F017 wording, folder name) were also addressed. |
| (2) F032–F035 against the code | PASS. All line references are correct and the severities are reasonable; F032 is correctly marked confirmed by code, not reproduced. |
| (3) Conclusion 7 / F006 | PASS: no longer overclaims. |
| (4) No new errors | PASS. 77 manifest entries match on disk (9,018,537 B); 26 image hashes match E17; E01 line 53 is the first PC-A CT2 insert; counts agree (35 = 2/9/18/6); the §5 stage table lists all 35 IDs once. |
| (5) git status / non-mutation | PASS. The only new entries are the 78 package files; a fresh re-hash shows 740/740 code files and 1,867/1,867 upload files unchanged, and only `worker-g.stderr.log` changed in the outer repo; the mtime scan is clean. |

The reviewer's non-blocking notes, and what the producer did:

| Note | Action |
|---|---|
| 1. F017's reason cited the PC-A *sync* worker's heartbeat. Better evidence: the IFC worker running job 119 last heartbeat at 12:55:27 (`current_job_id` 119, `stopped_at` NULL). | F017 reworded; the producer verified it in the snapshot (`background_workers`: heartbeat 2026-10-02 12:55:27.776317, `current_job_id` 119, `stopped_at` NULL). |
| 2. F007 cites `service.py:385-387`; the comment spans about 381–393. | Corrected to `381-393`. |
| 3. Record round 2 here. | This section. |
| 4. The patch scripts write into the package. | The runbook now lists every package-writing script as "do not run". |

No further review round was requested. Round-2 edits were limited to the four notes above; `PACKAGE-CHECK.json` was regenerated afterwards.
