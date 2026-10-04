# Independent M2 Preparation Review 33: D1, integrity and bindings

**Task:** ORCH-03.1/D1. **Agent:** R33-D1, Claude Opus 5.5 (`claude-opus-5-5`), effort High. **Authority:** A-03.

This is an owner-delegated independent Claude AI review. It is **not** human sign-off. It does not approve or authorize anything. M2 remains CHANGES STILL REQUIRED, and M3 has not started.

- **Run:** 2026-10-03, about 06:50 to 07:00 UTC.
- **Network and models:** no network access and no model or provider request.
- **Git:** no state-changing git command.
- **Package scripts:** run only as copies in `scratchpad/R33-D1/`.

## Outcome

**No blocker and no major finding.**

- **Recomputed and matching:** every binding the task names.
- **Minor findings:** three:
  - D1-03: the `PACKAGE-CHECK.json` reports are unbound.
  - D1-07: the 149 `words.json` locating aids are unbound.
  - D1-17: the packet verifier ran the drafter-folder validate script. This one is UNVERIFIABLE.
- **Info findings:** the remaining fifteen record facts.

| ID | Sev. | Verdict | Claim (short) |
|---|---|---|---|
| D1-01 | info | CONFIRMED | Packet manifest `15c4114d…` and its 110 files |
| D1-02 | info | CONFIRMED | Reviewed manifest `64c03667…` and its 45 files; reviewed labels `00e53e82…` |
| D1-03 | minor | CONFIRMED | `PACKAGE-CHECK.json` is unbound in all three packages |
| D1-04 | info | CONFIRMED | The draft, the 5 packet inputs and the 23 review files are byte-identical copies |
| D1-05 | info | CONFIRMED | The label-review hashes and both RESPONSE*.sha256 files match |
| D1-06 | info | CONFIRMED | Staging: 72 PDFs, 149 renders and 189 crops are all bound |
| D1-07 | minor | CONFIRMED | The 149 `*.words.json` files are not hash-bound |
| D1-08 | info | CONFIRMED | All 1167 evidence references resolve to 324 bound images |
| D1-09 | info | CONFIRMED | Two notes cite unbound scratch enlargements; the evidence fields themselves are bound |
| D1-10 | info | CONFIRMED | OneDrive: 72 of 72 files match on size and mtime (os.stat) |
| D1-11 | info | CONFIRMED | review31 (58 files), the candidate and the baseline are clean; ledger is 483/17 |
| D1-12 | info | CONFIRMED | The ledger `-shm` mtime changed through read-only WAL opens; content unchanged |
| D1-13 | info | CONFIRMED | Response ledger is append-only; both r32 entries are consistent |
| D1-14 | info | CONFIRMED | The labels' agents array omits CRITIC; CRITIC provenance is in CRITIQUE.json |
| D1-15 | info | CONFIRMED | Nothing in the five trees was modified after 06:50Z |
| D1-16 | info | CONFIRMED | No network-capable code in either scripts folder |
| D1-17 | minor | UNVERIFIABLE | The packet verifier runs `validate_drafts_r32.py` from the drafter's folder |
| D1-18 | info | CONFIRMED | Reviewed labels and population rebuild byte-identically; recount is 57/38/38 |

## Method

The scripts are in `C:/Users/moham/AppData/Local/Temp/claude/C--Users-moham-Desktop-dev-dev/453468dd-6650-45fd-93b4-4712a8308d22/scratchpad/R33-D1/`:

| Script | Covers |
|---|---|
| `check1.py` | The three manifests, named hashes, the copies and the review folder |
| `check2.py` / `check2b.py` | Staging bindings and label evidence references |
| `check5.py` | OneDrive os.stat |
| `rebuild.py` | In-memory rebuild of the reviewed labels and population from scratch copies of the package scripts |

All scripts used `backend/venv/Scripts/python.exe` with `PYTHONDONTWRITEBYTECODE=1`. Shell commands were `sha256sum`, `head -c`, `git -C … rev-parse HEAD` and `git -C … status --porcelain`, plus a read-only sqlite URI. Results are saved beside the scripts (`check1.out.json`, `check2.out.json`).

## Findings

### D1-01 (info, CONFIRMED): preparation packet manifest

- **Manifest:** `fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json` has sha256 `15c4114da23e3989b621fed0e43cf9519f9e82e075b972dc2d01f5583f82d0ed`.
- **Listed files:** 110. Every one matches its sha256 and byte count, and none is missing.
- **On disk:** 112 files. The two unlisted files are the manifest itself and `evidence/PACKAGE-CHECK.json` (see D1-03).

The named inputs recompute equal:

| File | sha256 |
|---|---|
| `labels/R32-LABELS-DRAFT-1.json` | `ebd1e24d…a334` |
| `LABEL-CONVENTIONS-R32.md` | `5c09d4d2…e570` (the `.sha256` sidecar records the same value) |
| `FROZEN-SELECTION.json` | `bf71779a…5d21` |
| `SOURCE-MANIFEST.json` | `951e8697…e259` |
| `CROPS.jsonl` | `b1760b64…d1ff` |
| `EVIDENCE-INDEX.json` | `0d0db4f8…08b8` |

### D1-02 (info, CONFIRMED): reviewed package manifest

- **Manifest:** `fresh-cohort-r32-reviewed/evidence/EVIDENCE-MANIFEST.json` has sha256 `64c0366737a5567284c6b862e5addbb0091f7bf98066745f081407a8b3fe31c6`.
- **Listed files:** 45, all matching.
- **On disk:** 47 files. The two unlisted files are the manifest and `PACKAGE-CHECK.json`.
- **Reviewed labels:** `labels/R32-LABELS-REVIEWED-1.json` is `00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779`.
- **Package check:** `PACKAGE-CHECK.json` reports ok, with 18 of 18 checks ok (2026-10-03T06:32:34Z).

### D1-03 (minor, CONFIRMED): PACKAGE-CHECK.json is unbound

No manifest binds `evidence/PACKAGE-CHECK.json`, in any of the three packages, and no response-ledger entry records its hash. Current values:

| Package | `PACKAGE-CHECK.json` sha256 |
|---|---|
| fresh-cohort-r32 | `6be077396b02f232822d0c38328fcf620771495ee52659e790def4f50b43739b` |
| fresh-cohort-r32-reviewed | `7ff3594bbf9956c7f95688ba77b06845ffd2ecc7ef1221d90bb24a04d3a63018` |
| review31 | `301bb0518088f624bc39649675cfc626d99ddb1b6b88a9c95f7dc1b4d9a92b11` |

All three were last modified before the cutoff, and all report ok.

**Required action:** record these hashes in the Review 33 record or the declaration bindings, or disclose that the reports are unbound by design.

### D1-04 (info, CONFIRMED): the reviewed package's copies equal the frozen originals

- **Draft:** `labels/R32-LABELS-DRAFT-1.json` is byte-identical to the original (`ebd1e24d…`).
- **Packet inputs:** all five files in `packet-inputs/` are identical:
  - AUTHORIZATION-2026-10-02.md
  - EVIDENCE-INDEX.json
  - FROZEN-SELECTION.json
  - LABEL-CONVENTIONS-R32.md
  - SOURCE-MANIFEST.json
- **Review folder:** all 23 files of the label-review folder are identical in `review-r32-draft-1/`. The only extra file is `COPY-MANIFEST.json`, which is declared as not part of the source.
- **Copy manifests:** both `COPY-MANIFEST.json` files report `all_equal: true`, with source hashes equal to my recomputation.

### D1-05 (info, CONFIRMED): label review folder hashes

The folder has 23 files. Recomputed hashes:

| File | sha256 |
|---|---|
| REVIEWER-RESPONSE.final.json | `920a21d6…4c5b` |
| REVIEWER-RESPONSE.json | `70f94632…3ff8` |
| CRITIQUE.json | `ad6798dc…7eef` |
| DISPOSITIONS.json | `e8828bec…30a7` |

The sidecar files agree with these hashes:

- `RESPONSE.sha256` reads `70f94632884af028f31d66f76557807801cf00fcca37251a2ade25c9de3a3ff8 *REVIEWER-RESPONSE.json`.
- `RESPONSE.final.sha256` reads `920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b *REVIEWER-RESPONSE.final.json`.

### D1-06 (info, CONFIRMED): staging bindings

**Staged PDFs (72):**
- Every PDF hashes to its SOURCE-MANIFEST `staged_sha256`.
- `source_sha256 == staged_sha256` for all 72.
- For every file, size equals `bytes`, which equals `selected_size`. State is `staged` and `source_unchanged` is true.
- `files/` holds exactly these 72 files.

**Renders (149):**
- `png_sha256` and `txt_sha256` match RENDERS.json.
- Each staged hash matches SOURCE-MANIFEST.
- Each PNG's pixel size, read by PIL, equals the recorded `png_px`.
- EVIDENCE-INDEX lists the same 149 renders, with equal hashes and equal text-layer hashes.

**Crops (189):**
- All 189 entries in CROPS.jsonl are unique, present and hash-equal, and their staged hashes match.
- EVIDENCE-INDEX lists the same 189 crops.
- `crops/` holds no unbound file.

**Cross-bindings:**
- RENDERS.json `source_manifest_sha256` equals `951e8697…e259`.
- SOURCE-MANIFEST `selection_sha256` equals the FROZEN-SELECTION hash.
- The 72 entries in the FROZEN-SELECTION pool agree with SOURCE-MANIFEST on `ep`, `relative_path`, size and mtime.
- Staging holds 708 files in total: 72 PDFs, 447 render-folder files (149 × png, txt and words.json) and 189 crops.

**Render geometry:** the long side is 1800 px on all 149 renders. The short side ranges from 1172 to 1391 px, and only 9 renders are exactly 1272×1800. Each size matches its recorded `png_px`.

### D1-07 (minor, CONFIRMED): words.json files are unbound

The 149 `renders/F###-pN.words.json` files are not hash-bound anywhere. RENDERS.json and EVIDENCE-INDEX record only the PNG and `.txt` hashes.

- **What they are:** `render_r32.py` writes them as locating aids.
- **Use in the review:** batch B7 lists `F043-p1.words.json` among the files it opened (an empty list, for a scanned page).
- **Effect:** they are not label evidence, so no label depends on them.

**Required action:** disclose this, or bind the files in a later evidence index.

### D1-08 (info, CONFIRMED): every reviewed-label evidence path is bound

`R32-LABELS-REVIEWED-1.json` has 1167 `evidence` and `evidence_checked` values:

- 1145 are exact paths or names. These include `render F###-pN.png` forms and rotated `-r90`/`-r270` crops.
- 7 are image names inside prose.
- 15 are convention-ruling prose with no path.

Every image reference resolves to one of 324 distinct bound images (144 renders and 180 crops), and each re-hashes equal to EVIDENCE-INDEX. There are 0 unbound references and 0 directory mismatches.

- **Full-text scan:** 1163 image-name occurrences, 324 distinct, 0 unbound.
- **Draft:** 295 references to 193 bound images, 0 unbound.

### D1-09 (info, CONFIRMED): notes cite unbound reviewer scratch images

Two review notes copied into the reviewed labels cite reviewer scratch enlargements:

- F010 decision: `z_F010_box.png`
- F022 revision: `z_F022_tb.png`

`REVIEWER-RESPONSE.final.json` also lists further `reviewer_working_images` under the session scratchpad (`r32rev-B1`, `r32rev-B3` and `r32rev-B7`).

- **Declared status:** each is declared a derivative of a bound render or crop, "not evidence".
- **Evidence fields:** the evidence fields of these rows cite only bound images.
- **Existence check:** the two cited files exist. I checked this with `os.path.exists` only and did not open them.

**Required action:** none for integrity. Disclose this in Review 33.

### D1-10 (info, CONFIRMED): OneDrive originals

For each file, the path was built as `\\?\` + `PROJECT-VERIFICATION.results[ep].folder` + `relative_path`. Files were never opened.

- **Result:** all 72 files match on size and mtime. The largest mtime delta is 0.0 s, so all 72 are exact.
- **Folder agreement:** the PROJECT-VERIFICATION folders equal FROZEN-SELECTION `project_folders` for the six cohort projects.
- **First attempt:** it failed with stat errors because a shell heredoc stripped the backslashes from the long-path prefix. I rebuilt the prefix with `chr(92)`. No file was opened in either attempt.

### D1-11 (info, CONFIRMED): frozen state

- **review31:** the manifest is `d5fe1649…c460`, and all 58 listed files match. The only unlisted files are the manifest and PACKAGE-CHECK.
  - `DRAFT-DECLARATION.v2.json` is `19720ad9…8b5d`.
  - `dry-run/LABELS-NORMALISED.json` was hashed as a manifest member only. Its rows were not parsed or displayed.
- **Candidate:** `C:/t/iso/cand-r29` HEAD is `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d`. `status --porcelain` prints 0 lines; the only ignored files are `__pycache__`.
- **Baseline:** `C:/t/iso/frozen-r12` HEAD is `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`, with 0 lines from `status --porcelain`.
- **AI ledger:** read through `file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro` with `uri=True`.
  - entries 483, scopes 17, limit_amendments 0, sqlite_sequence 483;
  - newest entry 2026-10-01T18:17:43Z (scope `m2-four-arm-final-2026-10-01-L4`), which is before 2026-10-02.

### D1-12 (info, CONFIRMED): ledger -shm mtime after the cutoff

| File | Size | mtime |
|---|---|---|
| `r2x-ledger.sqlite` | 110592 bytes | 2026-10-01T18:17:50Z |
| `-wal` | 0 bytes | 2026-10-01T18:26:41Z |
| `-shm` | 32768 bytes | 2026-10-03T06:53:10Z |

The `-shm` mtime falls after the cutoff. Read-only WAL connections, including this review's own, touch that file. The counts are unchanged, so this is not a content change.

### D1-13 (info, CONFIRMED): response ledger is append-only and consistent

**Hashes:**

| Range | sha256 |
|---|---|
| Whole file (160093 bytes) | `f0a4ffacba2c7765133475352e939a8149e119f7eb1efef73c2faec77774c65b` |
| First 156880 bytes | `6e296c28160b138d140d6c6dd275e1cd41e0a19827b24136b76dbabbf33fa0d4` |
| First 153812 bytes | `afddd562d2bb153c6092765de31022e12c66906b49b4f03507a0183179202ab4` |

The 153812-byte prefix equals the prefix that entry 1 claims, `afddd562…`.

- **Entry 1** (heading at byte 153813, the r32 packet) matches the packet:
  - manifest `15c4114d…`, 110 files;
  - 72 staged files, 149 renders, 189 crops;
  - pool 40/20/12, with 12 per project;
  - FROZEN-SELECTION, SOURCE-MANIFEST, conventions and draft hashes;
  - projection 62/39/39 of 70 distinct;
  - two byte-identical pairs, F038=F052 and F067=F070, which I recomputed.

  Entry 1 calls the reviewer "Codex". AUTHORITY-REGISTER A-03 explicitly amends that naming.
- **Entry 2** (heading at byte 156881, the reviewed package) matches the package:
  - manifest `64c03667…`, 45 files; PACKAGE-CHECK 18/18;
  - reviewed labels `00e53e82…`; rulings 432/210/56;
  - status counts 128/14/2, 123/20/1 and 131/13;
  - gate 57/38/38, with F069 (identity) and F019 (revision) excluded; upper bound 57/39/38;
  - documents 72/70/68; the aliases; ledger 483/17.

### D1-14 (info, CONFIRMED): CRITIC is missing from the agents array

The reviewed labels' `agents` array is copied from the final response (`apply_rulings_r32.py` line 418). It lists 9 agents: B1 to B7, CONSOLIDATE and DISPOSE. It does not list R32REV-CRITIC.

The labels' status text and response-ledger entry 2 do name CRITIC. CRITIC's identity (ORCH-01A.4, opus-5-5, high) is recorded in the `critic` field of CRITIQUE.json, which is hash-bound.

### D1-15 (info, CONFIRMED): no modification after 06:50Z

I walked each tree with `os.stat` at about 06:55Z, checking mtime and ctime on both files and directories. No tree has any file or directory changed after the cutoff:

| Tree | Files | Newest |
|---|---|---|
| fresh-cohort-r32 | 112 | 2026-10-02T20:06:25Z |
| M2-label-review-r32-draft-1 | 23 | 2026-10-03T06:12:39Z |
| fresh-cohort-r32-reviewed | 47 | 2026-10-03T06:32:34Z |
| C:/t/r2x/r32-stage | 708 | 2026-10-02T20:00:27Z |
| review31 | 60 | 2026-10-02T18:25:29Z |

### D1-16 (info, CONFIRMED): no network-capable code

I grepped both script folders for requests, urllib, http, socket, anthropic, openai, subprocess, claude, httpx, aiohttp, curl and wget, and took an import census. No network-capable code was found.

- **Imports:** standard library, plus pymupdf, PIL, pytest, sqlite3 and local modules.
- **Grep hits, none of them network code:**
  - the word "requests" in a docstring (`lib/arex.py`);
  - a `model_requests` key (`assemble_draft_r32.py`);
  - `http:` in a markdown-link filter.
- **subprocess:** used only in `verify_r32_packet.py`, for `git -C … rev-parse HEAD` / `status --porcelain` and for one Python run (see D1-17). Nothing calls claude.

### D1-17 (minor, UNVERIFIABLE): the packet verifier runs a script outside the package

`verify_r32_packet.py` line 58 runs `C:/t/iso/work/r2x/r32/validate_drafts_r32.py`, which is in the drafter's folder, not the packaged copy `fresh-cohort-r32/scripts/validate_drafts_r32.py`.

- **Effect:** the packet's "Validation: 0 problems" result cannot be reproduced from the package alone.
- **Why UNVERIFIABLE:** checking whether the two scripts are identical would require opening the forbidden folder.

**Required action:** re-run the validation from the packaged copy (in scratch), or record the executed script's hash, and disclose the result.

### D1-18 (info, CONFIRMED): rebuild and recount

The rebuild used scratch copies of the package scripts. `apply_rulings_r32.py` hashes to `8e3d0bbc…f252`, which equals the labels' `generator.sha256`.

- **Reviewed labels:** `build_reviewed(...)`, run on the package's own copies of the draft, the final response and the dispositions with the stored meta, serialises to `00e53e82…9779`. This is byte-identical to the stored file.
- **Population:** `count_population(...)` output is byte-identical to `FIELD-POPULATION.json`.
- **Independent recount:** my own recount code gives identity 57, revision 38 and decision 38.
  - Excluded as unresolved: identity [F069] and revision [F019].
  - Aliases: F031→F001, F052→F038, F059→F046 and F070→F067.
  - F069's identity is `unresolved` for scoring and has `carries_fact` "no". The upper-bound rule therefore leaves identity at 57.
- **Tests:** the packaged tests, run in scratch, pass 21 of 21 (15 + 6), matching `tests/*.xml`.

## Files opened

The machine-readable list is `D1-findings.json` → `files_opened`.

- **Not opened:** the drafter's and the implementer's folders, any arm output or replay, the label rows of r26.2 or LABELS-NORMALISED, any OneDrive file (stat only), and any database other than the AI ledger (read-only).
