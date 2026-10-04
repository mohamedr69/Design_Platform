# FI-P1 r3: independent review 2 (of CORRECTION-R3.md) and the binding conditions

**Reviewer.** A fresh-context Opus agent, read-only, no model calls. It checked r3 against the code at `bbf35be`.

**Verdict as delivered: PASS WITH CONDITIONS.** Conditions C1–C8 are binding. If any one is not adopted, the verdict is FAIL.

**Disposition: all conditions adopted.** The minor findings N9–N13 and the S13 residuals are also adopted. The text below **amends CORRECTION-R3.md** and is part of the Stage 0.1 contract. The implementation and its tests follow it, and the stage report maps every condition to its test.

## Status of REVIEW-R2 findings 1–13 (reviewer's assessment)

- **Resolved:** 1 (with N7), 3, 5 (with N7), 6, 7, 13.
- **Partially resolved:** 2 (N1, N9), 4 (N3, N6), 8 (N6, plus the dedup of "Download and read"), 9 (N4, N8), 10 (N3; `present=false`; a folder's own listing failure), 11 (N5; `server_default`; legacy mapping), 12 (needs N3).

Each is closed by the conditions below.

## Binding conditions (amendments to r3)

**C1: E4 never retires by itself (N1).**
- E4 (a file not listed while its discipline folder is present) gives `stale(missing)`: not counted and not retired.
- It becomes `removed` only when (i) the engineer confirms it, or (ii) a same-stem successor in the same package is `read` in the same scan. The R1→R2 case (T-07) still auto-advances.
- A discipline folder is `present` only if it lists ≥ 1 **non-ignored file** anywhere beneath it. Empty subfolders do not count.
- A directory carrying `FILE_ATTRIBUTE_RECALL_ON_OPEN` (0x40000) or `OFFLINE` (0x1000), or whose own listing raises, makes every entry beneath it `stale(listing_failed)`.
- T-10 (a DWG replaced by a PDF) now needs the engineer's confirmation of the DWG's removal before auto-advance.
- **Tests:** subfolder deleted → `stale(missing)`, no auto-advance, primary `published`; 0x40000 directory → `listing_failed`; R1→R2 auto-advances.

**C2: never an empty published or primary view from missing evidence (N1, N2).**
- Auto-advance never publishes an empty read set.
- It never drops a package's last read source unless that source was confirmed removed or replaced by a read successor.
- With **no snapshot**, and any present supported entry not current now, `primary = none` and `totals_known = false`.
- A first scan that reads nothing (e.g. PDFs only, or every file `not_synced`) publishes nothing.
- **Test:** all entries `unread(not_synced)`, no snapshot → rows `[]`, `totals_known = false`, `published` null.

**C3: "current now", exactly (N3).**
- A source is **current now** iff `sources` holds an entry with the same (kind, discipline, relative_path, sha256), stored `status = read`, **and** (`folder`/`schedule`) a live listing entry with that stored entry's exact (size, mtime), **or** (`fa_ifc`) it is still in force and its DXF exists.
- E7 (superseded) **retires** an older revision only when the newer one is `read`. If the newer one is unread or failed, the older one is `superseded`, not counted and not retired, so S8.2 row 4 gives `primary = published`.
- **Test:** R2 newer and unread → R1 not current, primary `published`.

**C4: redesign approvals are preserved (N4).**
- When `view_state != current` or `primary = none`, the redesign does **not** regenerate its interface changes. Existing interface changes (approved, moved, edited) are kept byte-for-byte, and the plan records the note "Interface schedule not verified now (<state>): interface changes kept as they were".
- Interface changes created while `view_state = current` carry `verified: true`.
- **Test** in test_redesign: approved interface change, then the schedule becomes provisional, then the redesign plans again → the change is unchanged.

**C5: one compare-and-set for every writer of the evidence (N5, N9).**
- `confirm-removed` and `publish-current` use the `generation` compare-and-set and bump it. The scan reads `generation` at start and commits only if it is unchanged, so a confirmation made during a scan makes the scan fail with "changed while being read", and nothing is lost.
- `confirm-removed` accepts only `stale(folder_missing|missing)` entries. Sync states (`listing_failed`, `ifc_root_missing`, `not_synced`) cannot be confirmed away.
- `publish-current` takes `expected_sources_digest`, which must equal the digest of the current read set shown on the page.
- It refuses an empty set, or a set where a present supported entry is `not_synced`, unless `override: true` (with a reason).
- It is allowed under root `ok`, and under `ifc_root_missing` with a reason (N9: a project whose only evidence is its fire-alarm IFC).
- **Test:** confirm during a scan → the scan fails and the confirmation stands.

**C6: one placeholder rule for scan and GET (N6).**
- A `read` entry whose live (size, mtime) is unchanged is **carried forward without opening the file**, cloud-only or not (marked `cloud_only` when the attribute is set). The GET rule is the same.
- Only new or changed placeholder files are opened (`FA_READ_CLOUD_ONLY_FILES = true`) or left `not_synced` (`false`).
- The carry-forward no longer re-hashes unchanged files. Identity is by (size, mtime) as listed, plus the stored sha.
- **Test:** a fully dehydrated, unchanged project rescans to `current` without opening a file.

**C7: the draftsman check passes only with `primary = current` (N8).** With `primary = published` it does not pass ("last published, not verified now").

**C8: ARCH badge, legacy `read`, schedules in the digest (N7, N10).**
- Under a root that is not `ok`, the ARCH package with a current `fa_ifc` gets the badge `Received (fire alarm IFC only)`, `status = available`, `received = true`. The folder part is reported as unknown.
- `coverage[].read` is true only when ≥ 1 of the package's sources is current now.
- Schedule workbooks are hashed (sha256) when read, and the digest includes `sha256` and `schedule_version`.

## Adopted minor items

- **N9:** see C5.
- **N11:** exact (size, mtime) equality is kept, and the carry-forward refreshes size/mtime from the listing.
- **N12:**
  - The published view is built only for S8.2 rows 1, 2 and 4.
  - The first GET may create the project's empty row (the existing behaviour).
  - S2 includes the top-level `result`, `read_at`, `visual` and `cloud_only` fields.
  - `generation` has `server_default = 0`.
  - Legacy entries map as is: `read`/`failed`/`superseded` keep their meaning and the new fields default to null.
- **N13:** S8.2 row 6 shows a "Publish current" banner.
- **"Download and read":** uses its own job parameter (`hydrate: true`). It shares the scan's dedup key, so while a normal scan runs the page says so and offers it again after.

## S13 residuals (for Stages 4–6, not Stage 0.1)

- **W-5:**
  - A single point with both role labels nearby is held.
  - Duplicate same-role labels collapse to that role's nearest label.
  - Note-only labels (`NETWORK`, `DATA POINT`, `CAT6`, `CONTROL PANEL`) never establish gate-barrier context.
- **W-4:** "compatible positions" means within the key's type tolerance (W-3).
- **W-N:** keep a minimum of n ≥ 30 per critical stratum, alongside the pooled n ≥ 210.
