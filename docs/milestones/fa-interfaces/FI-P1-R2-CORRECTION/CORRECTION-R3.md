# FI-P1 r3: Stage 0.1 contract, complete and corrected (review 2 findings resolved)

| | |
|---|---|
| Version | FI-P1 r3 (2026-10-04). It **replaces CORRECTION-R2.md Part A in full** and amends Parts B and C as listed in §9. CASES.md stands, with §9's citation corrections. |
| Why | The independent review of r2 (REVIEW-R2.md) failed Part A on findings 1–13 and found W-4/W-5 unsound (findings 14–17). |
| Verified facts used here (C) | EP-30880's `03- Drawings/IFC/Architectural` exists and is empty; its only saved `read` source is `fa_ifc FIRE ALARM LAYOUT.dwg`. Gate Barrier reference: entry point A 3.10 m from ENTRY and 4.43 m from EXIT; exit point B 1.34 m from EXIT and 5.17 m from ENTRY; the one-to-one assignment costs 4.44 m against 9.60 m swapped, a margin of 5.16 m. |

Clause ids are `S`, tests `T`. Every clause is tested.

---

## S1 Source kinds and the evidence each depends on

| Kind | Where it comes from | Presence is decided by |
|---|---|---|
| `folder` | DWG/DXF under a discipline folder of `03- Drawings/IFC` | the folder listing (S3) |
| `fa_ifc` | the fire-alarm IFC drawings in force (`revisions.in_force`), with their DXF in uploads (service.py:138-144) | **in-force membership and the DXF file**, never the project folder |
| `schedule` | the Excel workbooks under `IFC/Mechanical` (schedules.py:150-159); no hash; re-read every scan | the `IFC/Mechanical` listing |
| `unsupported` | any other file in a discipline folder (PDF, images, Office) except the ignore list (S3.4) | the folder listing |

**Package presence.** A package is present when it has a present `folder`, `schedule` or `unsupported` file. The ARCH package is also present when it has an in-force `fa_ifc` whose DXF exists.

**`source_folder_path` null.**
- The scan endpoint refuses, as today (fa_interfaces.py:56).
- On GET, `evidence.root = "not_configured"`, every `folder`/`schedule`/`unsupported` package gets the badge `No project folder`, and `fa_ifc` is decided as above (T-21).

## S2 Per-source record

```
SourceEntry {
  discipline, kind: folder|fa_ifc|schedule|unsupported, relative_path, filename, size, mtime, sha256|null,
  status: read | stale | failed | unread | removed | superseded | unsupported,
  stale_reason: read_failed | not_synced | folder_missing | ifc_root_missing | listing_failed | null,
  last_known: { result, visual|null, sha256, read_at, scan_version } | null,
  duplicate_of: relative_path | null,          // information only in Stage 0 (S5); counting unchanged
  error|null, removed_at|null, seen_at
}
```

`build()` counts `status == "read"` only (service.py:434, C). A `stale` entry keeps its old reading under `last_known` and is never counted.

## S3 Listing and folder states (stat only)

**S3.1 Root.** One of:
- `not_configured` (null path);
- `unreachable` (not a reachable directory, as `received()` tests today);
- `ifc_root_missing` (reachable, but `03- Drawings/IFC` absent or with no entries);
- `ok`.

**S3.2 Discipline folder.** One of:
- `present` (exists with ≥ 1 entry);
- `absent_or_empty`;
- `listing_failed` (`os.walk(onerror=…)` recorded an error for that folder or below it; today errors are swallowed, service.py:113).

**S3.3 Not synced.** A file whose `st_file_attributes` has `RECALL_ON_DATA_ACCESS` (0x400000) or `OFFLINE` (0x1000) is a cloud-only placeholder.

**S3.4 Ignore list.** These are never listed:
- `desktop.ini`, `Thumbs.db`, `.DS_Store`;
- names starting with `~$`;
- the `_SKIP_FILE` suffixes (`.dwl`, `.dwl2`, `.bak`, `.tmp`, `.sv$`);
- the schedule workbooks, which are listed as `schedule`, not `unsupported`.

## S4 Transitions: precedence and the total table

**S4.1 Precedence** (the first event that applies wins):

`E0 root unreachable/not_configured` > `E6 IFC root missing` > `E5 the entry's discipline folder absent_or_empty` > `EL its folder listing_failed` > `E4 the file is not listed, its folder present` > `E7 a newer revision of the same stem is listed` > `E3 present, cloud-only, and hydration failed` > `E2 present, read failed` > `E1 present, read OK (or carried forward unchanged)`.

**`fa_ifc` uses its own events instead of E4–E6/EL:**
- `F1` in force, DXF present, read OK;
- `F2` in force, DXF present, read failed;
- `F3` in force, DXF missing;
- `F4` no longer in force, a newer one in force;
- `F5` not in force and nothing replaces it.

**S4.2 Total table** for `folder` entries:

| Previous ↓ \ event → | E0 | E6 | E5 | EL | E4 | E7 | E3 | E2 | E1 |
|---|---|---|---|---|---|---|---|---|---|
| (new file) | — | — | — | — | — | `superseded` | `unread`(not_synced) | `failed` | `read` |
| `read` | no change; job fails | `stale(ifc_root_missing)` | `stale(folder_missing)` | `stale(listing_failed)` | `removed` (last_known kept) | `superseded` | `stale(not_synced)` | `stale(read_failed)` | `read` |
| `stale(any)` | no change | `stale(ifc_root_missing)` | `stale(folder_missing)` | `stale(listing_failed)` | `removed` | `superseded` | `stale(not_synced)` | `stale(read_failed)` | `read` |
| `failed`, `unread` | no change | `stale(ifc_root_missing)`, last_known null | `stale(folder_missing)`, null | `stale(listing_failed)`, null | `removed` | `superseded` | `unread`(not_synced) | `failed` | `read` |
| `removed` | no change | stays `removed` | stays | stays | stays | `superseded` | `unread`(not_synced) | `failed` | `read` (file returned) |
| `superseded` | no change | `stale(ifc_root_missing)` | `stale(folder_missing)` | `stale(listing_failed)` | `removed` | stays `superseded` | `unread`/`stale(not_synced)` | `failed`/`stale(read_failed)` | `read` (the newer revision is gone) |

`unsupported` entries:

| Previous \ event | E0 | E6/E5/EL | E4 | listed |
|---|---|---|---|---|
| `unsupported` | no change | stays `unsupported`, marked `present=false` | `removed` | `unsupported` |

`fa_ifc` entries:

| Previous \ event | F1 | F2 | F3 | F4 | F5 |
|---|---|---|---|---|---|
| any | `read` | `stale(read_failed)` if it had a reading, else `failed` | `stale(read_failed)` ("DXF not on this PC") | `superseded` | `removed` |

`schedule` entries follow the `folder` table, with E5 meaning `IFC/Mechanical` absent_or_empty. They are references: a `read` schedule feeds the plan-against-schedule checks, and nothing else counts them.

**Engineer action.** `POST …/fa-interfaces/sources/confirm-removed {relative_paths[]}` (creator roles) turns `stale(folder_missing|ifc_root_missing|listing_failed)` into `removed`.

## S5 Duplicates in Stage 0: information only

Every path is still read, as today: a sha already converted reuses the cached DXF, so this is cheap. When two `read` entries share a sha, the second gets `duplicate_of` the first, **for display only**. Counting and row ids are unchanged, so no decision is orphaned. Reading once with the union of keys comes with W-DUP (Stage 1).

## S6 Hydration of cloud-only files

- **Default `FA_READ_CLOUD_ONLY_FILES=true`:** a cloud-only file is opened like any other, which makes OneDrive download it. Success means E1/E2 as usual. An `OSError` while it is a placeholder is E3, `stale(not_synced)` (or `unread`, not_synced, if it was never read). Every scan tries again.
- **`false`:** placeholders are not opened. They go straight to E3, and the page offers **"Download and read"**, which starts a scan with hydration allowed for that project.

## S7 The published snapshot holds evidence, not output

**Migration.** Add to `project_fa_interfaces`:
- `published` JSON null
- `published_at` DateTime null
- `published_basis` String(24) null (`complete_scan | engineer_accepted | seeded`)
- `published_by_id` int null
- `published_reason` Text null
- `generation` Integer not null, default 0

**Snapshot.**

```
{ sources: [SourceEntry with status read], sources_digest, job_id|null }
```

- `sources_digest` = sha256 over the sorted `(kind, discipline, relative_path, sha256, scan_version, visual.version, visual.status)` of those entries.
- **Views.** The published view is `build_from(snapshot.sources, live decisions, live manual, live floors)`. The current view is `build_from(current sources, live decisions, live manual, live floors)`. Decisions and manual items made at any time therefore apply to both views. That covers review-2 #3.

**Seeding.**
- One time only, in the Alembic data migration: if a row has ≥ 1 `read` source, `published` is set from those entries with basis `seeded`. `generation` is not bumped.
- Projects created later start with `published = null`. There is no seeding at read time.

**Who bumps `generation`.** Only a scan commit and `publish-current`. Decisions and manual items do not.
- The compare-and-set is `UPDATE … SET …, generation = generation + 1 WHERE id = :id AND generation = :seen`.
- The loser's job fails with "the schedule changed while it was being read; read again".

**Auto-advance after a scan.** The snapshot is replaced by the scan's `read` entries (basis `complete_scan`) only when all of these hold:
- A1: root `ok`;
- A2: no discipline folder `listing_failed`;
- A3: no present supported entry is `failed`, `unread` or `stale`;
- A4: every source in the current snapshot is now either `read`, or **retired**: `removed` (E4, F5 or confirmed), or `superseded` by a `read` revision.

A legitimately removed package, or a DWG replaced by PDFs only, satisfies A4 through retirement. The view may become smaller than before; that is the drawings' truth, not a sync failure.

**Engineer path out.** `POST …/fa-interfaces/publish-current {reason}` (creator roles):
- requires root `ok` and no `listing_failed`;
- sets the snapshot from the current `read` entries, basis `engineer_accepted`, with by/at/reason;
- bumps `generation`;
- is activity-logged.

It covers a permanently failing file, and anything else the auto-advance rule will not take.

## S8 GET-time currency and the primary view

**S8.1 Currency at read time.** The view is computed afresh on every GET. Nothing is written.

A `read` entry is **current now** only if one of these holds:
- (`folder`/`schedule`) its file is listed now, with the same `(size, mtime)` as when it was read, and the root is `ok`;
- (`fa_ifc`) it is still in force and its DXF exists.

Otherwise it is shown as `stale (changed since the last read: missing | modified | ifc_root_missing | unreachable)`. Such an entry is not counted as current and appears in the "Last known, not current" section.

A **cloud-only placeholder with unchanged `(size, mtime)` stays current.** Its content was hash-verified when read, and dehydration changes availability, not content. The page marks it "cloud-only" (T-24).

**S8.2 Primary view.** `published` is the view built from the snapshot. `current` is the view built from entries current now.

| # | Condition (first match) | `view_state` | `primary` |
|---|---|---|---|
| 1 | root `not_configured` or `unreachable` | `unverified` | `published` if a snapshot exists, else `none` |
| 2 | root `ifc_root_missing` | `unverified` | `published` if a snapshot exists, else `none` |
| 3 | never scanned (no sources) | `not_read` | `none` |
| 4 | a snapshot exists, and **any source in it is neither current now nor retired** | `provisional` | `published` |
| 5 | any present supported entry is not current now (`failed`, `unread`, `stale`) | `provisional` | `current` |
| 6 | a snapshot exists and the current digest differs from it | `provisional` | `current` (the page offers "Publish") |
| 7 | otherwise | `current` | `current` |

`primary = none` gives empty rows, the title "Not yet read completely", and `totals_known: false`.

Retired is defined as in S7 A4. Row 4 works **per source** (review-2 #12): losing any one source that fed the published view switches the primary view to `published`.

**S8.3 Payload.** Existing keys keep their shape and carry the **primary** view: `rows, verification, settled, rejected, manual, floor_summary, type_summary, totals, conflicts, excluded_found, floors, coverage, matrix`. Added keys:

```
view_state, primary,
totals_known: bool,                       // false when primary = none; numbers stay numeric (0s), never null
published_at, published_basis, published_by, published_reason,
current_summary: { totals, rows: int } | null,     // null when root not ok
last_known: [ { package, relative_path, reason, last_known_at, counts_by_key } ],
decisions_not_applied: { package: int },  // decisions whose source is not current now
evidence: { root, read_current, stale, failed, unread, removed, superseded, unsupported, cloud_only, listing_failed[] }
```

## S9 Coverage: legacy fields and ordered badges

**`received()` changes.**
- The `return saved` fallback (service.py:1018-1019) is removed.
- On a root that is not `ok`, every package gets badge 1 or 2, and its saved entries are listed under `last_known` only.

Ordered badges, first match wins:

| # | Badge |
|---|---|
| 1 | `Unreachable` (root unreachable) or `No project folder` (not configured) |
| 2 | `Not synced` (IFC root missing) |
| 3 | `Missing, last known kept` (no present file; stale entries exist) |
| 4 | `Missing` |
| 5 | `Received, not read` (a present supported file is not current now) |
| 6 | `Received, not readable (PDF)` (only unsupported present) |
| 7 | `Received` |

**Legacy field.** `coverage[].status = "available"` **exactly** for badges 5–7 (`received = true`), and `"missing"` otherwise. The UI's "Drawings Received" KPI (InterfacesTab.tsx:72) therefore never counts stale evidence (T-23). A `badge` field is added.

## S10 Consumers and exports

**Exports.** xlsx and pdf export the primary view.
- The header carries `view_state`, `primary` and the published date/basis.
- Stale entries appear only in a separate "Last known, not current" sheet/section.
- When `totals_known` is false, totals print as "—".

**Redesign** (`_interface_changes`, redesign/service.py:503ff).
- If `view_state != "current"`, every interface change is created with `verified: false` and the note "Interface schedule not verified now (<view_state>): placed from <primary> reading of <date>".
- Such changes are never pre-approved. The engineer approves each one.
- With `primary = none`, no interface changes are created and the plan notes why.

**Draftsman check** (`_interfaces`, draftsman_assignment.py:100-107).
- `view_state == "current"`: as today.
- `provisional`: passes, with the note "provisional: n source(s) not verified now".
- `unverified` or `not_read`: does not pass, with the reason.

**UI.**
- The KPI cards show "—" when `totals_known` is false.
- A banner states `view_state` and `primary`.
- A "Last known, not current" section is shown, plus the "Publish current" and "Confirm removed" actions for creators.

## S11 Scan

1. Compute S3. A root that is `unreachable` or `not_configured` makes the job **fail**, with nothing written. `ifc_root_missing` completes: the transitions are applied and the snapshot is unchanged.
2. List, then hydrate, hash and read per S4 and S6. Unchanged `read` entries carry forward.
3. Visual look as today (Stage 0.3).
4. A **single commit** writes `sources`, the auto-advance decision and the `generation` compare-and-set. A cancel or interrupt before the commit leaves the row untouched.
5. `decisions` and `manual` are never written by a scan.

## S12 Tests (Stage 0.1)

| Id | Given → when → then |
|---|---|
| T-01 | FF read (in the snapshot) → reread fails → FF `stale(read_failed)`, last_known kept; current excludes FF; primary `published` (row 4); FF badge `Received, not read`; `decisions` unchanged |
| T-02 | SM read → SM folder renamed → SM `stale(folder_missing)`; badge `Missing, last known kept`; `received=false`; primary `published` |
| T-03 | All read → root unreachable → job fails; row unchanged (`generation` too); GET: `view_state=unverified`, primary `published`, every badge `Unreachable`, `status != available` everywhere, `current_summary=null` |
| T-04 | All read → `IFC` folder missing (unsynced) → job completes; `folder`/`schedule` entries `stale(ifc_root_missing)`; **`fa_ifc` stays `read`**; primary `published`; the primary rows are not empty |
| T-05 | **EP-30880 shape:** empty `Architectural` folder, one in-force `fa_ifc` read, SM/HVAC read → ARCH badge `Received`; fa_ifc `read`; the snapshot can auto-advance |
| T-06 | T-01 → reread OK, same sha → FF `read`; snapshot auto-advances; `view_state=current` |
| T-07 | R1 read → R1 deleted, R2 filed → R2 `read`, R1 `removed`; counted once; auto-advance (R1 retired) |
| T-08 | R1 and R2 both present → R1 `superseded` |
| T-09 | T-08 → R2 deleted → R1 `read` |
| T-10 | GB DWG replaced by a PDF → DWG `removed`, PDF `unsupported`; badge `Received, not readable (PDF)`; auto-advance (retired) |
| T-11 | `stale(folder_missing)` → engineer confirms removal → `removed`; the next complete scan auto-advances |
| T-12 | A permanently failing file → `publish-current` with a reason → snapshot = current read set; basis `engineer_accepted`; by/at/reason stored; `generation` +1 |
| T-13 | Primary `published` → engineer resolves a verification item → the resolution appears in the primary view (live decisions) |
| T-14 | Migration on a row with read sources → snapshot seeded, basis `seeded`, `generation` 0; a row without read sources stays null |
| T-15 | Two scans race → the second fails "changed while being read"; `generation` +1 once |
| T-16 | A scan cancelled mid-way → row and snapshot untouched |
| T-17 | A cloud-only file, read before, hydration raises → `stale(not_synced)`; next scan, hydration OK → `read` |
| T-18 | `FA_READ_CLOUD_ONLY_FILES=false` → placeholder not opened (asserted) → `stale(not_synced)`; "Download and read" scan → read |
| T-19 | `os.walk` error under SM → SM entries `stale(listing_failed)`; no auto-advance |
| T-20 | Same bytes in SM and HVAC → both read; the second has `duplicate_of`; counts and row ids equal to today's |
| T-21 | `source_folder_path` null → GET: badges `No project folder`; fa_ifc as S1; scan endpoint refuses |
| T-22 | Never-scanned project → `view_state=not_read`, `primary=none`, rows `[]`, `totals_known=false` |
| T-23 | Stale entries present → `coverage[].status == "available"` only for badges 5–7; UI KPI counts match |
| T-24 | After a scan, a read file is modified on disk → GET shows it `stale (modified)`, excluded from current; a dehydrated unchanged file stays current, marked cloud-only |
| T-25 | `view_state != current` → redesign interface changes `verified=false`, not pre-approved; draftsman check per S10 |
| T-26 | Exports for `published`/`provisional`/`none` → header and "—" totals; the stale sheet is separate |
| T-27 | Ignore list → `desktop.ini`, `~$x.dwg` and `.dwl` are never listed |
| T-28 | Existing `test_fa_interfaces`, redesign and draftsman tests pass (adapted only where they assert the removed fallback) |

---

## S13 Amendments to r2 Parts B and C (review-2 findings 14–20)

**W-5 Gate barriers (review-2 #14–16).**
- **Candidate connection points** are taken only from `folder` drawings of the **GB** package, or of ACS/ARCH folder drawings when within 5 m (EXAMPLE) of a gate-barrier label, a `LOOP`-layer polyline, or a barrier block on a plan sheet. Never from `fa_ifc`.
- **Settlement by assignment margin.** Roles are assigned to points one-to-one at minimum total distance (each ≤ 6 m, EXAMPLE).
  - Settled by rule when (second-best total − best total) ≥ 1.0 m (EXAMPLE) and the assignment is unique.
  - Reference case: margin 5.16 m, so **both barriers settle**. Expected outcome: two CR lines, `entry` (close entrance barrier, the additional module) and `exit` (open exit barrier) (T-W19).
- **Fallback.** A GB drawing with gate-barrier labels but no connection point gives a **held** verification group. It earns no accepted credit; today it is one counted line.
- **Across drawings.** Counts are compared per (floor, role). Role-less points (e.g. the shop drawing's) are compared on the floor total only. Equal totals are counted once, from the role-bearing drawing. Unequal totals form a held ConflictSet.

**W-4 Alignment (review-2 #17).**
- Alignment is verified **per drawing pair** from all coinciding same-key, same-text labels across floors: ≥ 3 coincidences within 0.5 m, with residual ≤ 0.2 m (EXAMPLE).
- It applies to every floor whose sheet viewports are identical in both drawings, including floors with fewer than 3 dampers.
- An unaligned floor with equal counts is **held** unless every position is compatible. Equal counts alone are never credited.

**W-N (review-2 #18).** G-ACC needs |A| ≥ 210 pooled on exhaustive layouts (206/210 gives a Wilson lower bound of 0.952). Critical strata are reported, with a point estimate ≥ 0.98 required.

**Review-2 #19.**
- FP1 re-runs for reworked packages **before FP3**.
- Orchestrator calls use their own `Limits` with `max_input_tokens_per_task = FA_ORCHESTRATOR_MAX_INPUT_TOKENS`, overriding the 6,000 default (budget.py:86-87).
- W-BASE names commit `e983b4b`.
- W-3 settles an association when runner-up/best ≥ 1.5.
- T-W tests are written as given/when/then in the Stage 1–6 test files before each stage starts (the stage gate).

**Review-2 #20 (CASES citations).**
- detect.py:120 also matches BOOM, PARKING, VEHICLE, ENTRANCE and EXIT before BARRIER, and BARRIER GATE. The analysis is unchanged, because none of those phrases occur in the GB drawings' plan text except as shown.
- The visual.py lines cited were in the live checkout (worktree: about lines 203-206).
