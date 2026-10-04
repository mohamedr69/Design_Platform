# M2 Real-Project Acceptance Pilot -- plan and execution record

Date: 2026-09-28. Executed by Claude (Fable 5.1) under the owner's pilot instructions
(`M2-real-project-pilot/M2-REAL-PROJECT-PILOT-CLAUDE-INSTRUCTIONS.md`) after Independent M2 Review 04.
Nothing in this folder is an approval: the verdict in `ACCEPTANCE.md` is a candidate verdict for the
independent reviewer and the owner.

## 0. Candidate freeze and source identity

| item | value |
|---|---|
| reviewed commit | `2221b4327c7dd140994cc2c98e89229431b34899` (`Publish M2 extraction and document sync updates`, 2026-09-28 13:39 +0400) |
| dirty tree at the freeze (candidate A) | `document_sync.py`, `document_processing.py`, `repair_extraction.py`, `test_extraction_m2_review02.py`, `test_extraction_m2_review03.py` (the R4-01 closure), plus the live operational files `backend/ep_platform.db` and `backend/library/symbols/symbol_library.json` (not pilot artifacts) |
| candidate A | parser `parse-2026-09-28.4`, evidence `evidence-2026-09-28.2`, index `index-2026-09-24.4`, design-sheet reader `2026-09-28.1`; source hashes in `outputs/REPRODUCIBILITY.json` |
| candidate B | candidate A plus the four bounded reader fixes P-01..P-04 (`DEFECTS.md`), parser `parse-2026-09-28.5`; source hashes in `RUN-MANIFEST.json` |
| profiles | `default` (`EXTRACTION_PROMOTE_OBSERVATIONS=false`) and `promoted` (`true`), each into its own sandbox database |
| budgets | `PAGE_SCAN_LIMIT` 12, `REPLY_SEARCH_LIMIT` 12, `OCR_PAGE_LIMIT` 12, `OCR_TIMEOUT_S` 25; sheet render 300 dpi |
| OCR | Tesseract 5.4.0 (`C:\Program Files\Tesseract-OCR\tesseract.exe`); `SYNC_FILE_WORKERS=0` in the sandbox (the live setting is 3) |
| model | `AI_ENABLED=false` throughout: every model-requiring branch is reported as not exercised, never as passed |
| Python / platform / dependencies | in `outputs/REPRODUCIBILITY.json` |

R4-01 was closed before the freeze (`../M2-REVIEW-RESPONSE.md`, Review 04 section); the eight reviewer probes
were rerun on the frozen code (`outputs/probe_r4/`).

## 1. Inventory

The ten folders the reviewer selected (`M2-real-project-pilot/pilot_selection.json`) were walked again with
extended paths (`\\?\`), read-only, deduplicated by normalised path, recording size, mtime, attributes,
OneDrive placeholder state (`FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS`) and path length; nothing was hydrated by
the walk. Result: 42,574 files, 24,311 PDFs, 0 metadata errors (`PROJECT-INVENTORY.json`, per-folder lists
under `inventory/`, gzipped; the clone record dumps and snapshots under `outputs/clone_default/` likewise). Differences from the reviewer's 42,576: two entries under EP-26082 no longer exist and one
EP-29076 entry changed size between the two walks (OneDrive activity, recorded, not corrected).

Project identity is the folder's EP number. Printed EP references inside documents are labelled separately
(`printed_project` in `GOLDEN-LABELS.json`) and never used to file a document.

## 2. Isolation

- Sandbox roots `C:\t\pilot\{db,cache,library,uploads,out}` and the staged trees `C:\t\pilot\stage\EP-<n>\...`
  are set through the environment before any application import; every runner asserts the settings point there.
- Originals under OneDrive were only read (hashing, staging, the regression-clone repair). Sampled placeholders
  were hydrated one file at a time by the read itself (289 of 380 sampled files; 10 of 15 BOQ sheets); no
  folder was made available offline and no bulk download happened. The two regression-control folders hold
  6.7 GB of PDFs, mostly placeholders, so their clone repair was limited to the sampled rows.
- The live database was cloned with the SQLite backup API from a read-only connection (WAL-consistent) into
  `C:\t\pilot\db\clone_default.db`; the ordinary sync job, the extract-only repair tool and the sync again
  (reconciliation included) ran on the clone only, with business snapshots before, between and after.
- No live API or worker was used, started or stopped; no live migration, repair or reset was made.
  A live backend (API + 3 workers) started outside this session kept running untouched.

## 3. Sample

`FROZEN-SAMPLE.json`, drawn on 2026-09-28T11:52Z with seed 20260928 before any extraction:

| | count |
|---|---|
| eligible files under the sync contract (`.pdf`, or `.doc/.docx` in a transmittal folder) | 24,358 across the ten folders |
| drawn | 380 (quota per project: 40/40/55/50/32/55/2/60/40/6) |
| distinct content | 376 (4 duplicate-content pairs kept, labelled as such) |
| by cohort | regression 80, exploration 192, holdout 108 |
| by stratum (path rule) | shop_drawing 81, drawing_ifc_input 90, other 50, reply 34, scan 31, submittal 22, approval_sample 18, spec_compliance 18, design_sheet 17, transmittal_word 10, calc 9 |
| scan-like (no text layer on the first pages) | 67 |
| Word transmittals | 10 |
| unreadable | 1 (EP-26082 ... `2024.09.04 - MEP-SHD-EL-0008-Rev.01-...Status-C.pdf`: a 0-byte original) |
| pages (sum) | 6,369 |

The stratum is a path rule (recorded in the file), not the document's kind: the kind was labelled afterwards
from the page itself and the strata are reported as drawn. The two very small folders (EP-27474: 2 files,
EP-14119: 6 eligible files) are included whole. A template-copy cap of 45 % per stratum was applied.

BOQ / design-sheet set (`FROZEN-BOQ-SET.json`): the 15 Design Sheet / BOQ PDFs found by name in the
projects' Commercial or Scan folders (9 projects; EP-13777 has none by that name), frozen with hashes and
page counts before any read, all rows labelled (778 rows).

## 4. Truth

`GOLDEN-LABELS.json`, one record per sampled document, labelled by Claude from renders of the staged
originals made with pymupdf (contact sheets of page 1 with its cue bands; title-block strips for
drawing-sized sheets; every page of the BOQ set at 110 dpi; the Word transmittals from Word's own text).
No reader output was consulted while labelling. Fields: kind, reference, revision, date, title, system,
floor, originator, decision, decision candidates (every mark seen), printed project, components,
confidence (high / medium / low), labeller notes. Non-values are distinct: `absent`, `illegible`, `unknown`,
`n/a` (the field does not apply), `unlabelled`. A contractor reply, a receipt signature or an internal form
approval is never a consultant decision; a document with no consultant decision applying is `n/a`.
No countersignature is claimed. The EP-30784 BOQ rows reuse the existing golden fixture
(`backend/tests/fixtures/boq_ep30784_golden_v1.json`), owner countersignature pending.

## 5. Runs

1. Candidate A, default profile, all ten projects through `POST /projects` + `sync-documents` (inline) with
   the processing job the sync queues, cold OCR cache. Then the promoted profile into its own database
   (warm OCR cache, since the cache is keyed by content).
2. Persistence scenarios on real sampled copies (`outputs/SCENARIOS2-*.json`), both profiles.
3. Regression-control clone workflow (`outputs/clone_default/`).
4. BOQ path with the model disabled (`outputs/BOQ-RUN-default.json`).
5. Scoring of candidate A on all cohorts (`outputs/candidateA/`), the holdout included: the holdout was
   scored once on the frozen candidate before any fix.
6. Four defects demonstrated on the regression / exploration cohorts fixed with bounded regression tests
   (`backend/tests/test_extraction_pilot.py`), candidate B frozen, both profiles rerun and scored on the same
   labels (`outputs/candidateB/`). No label was changed after scoring began. The holdout's exposure is
   stated in `ACCEPTANCE.md`.

Targets fixed before scoring (not changed afterwards): >= 98 % precision among auto-accepted critical fields
(reference, revision, decision); >= 90 % correct automatic recovery of clearly readable applicable critical
fields; no unresolved critical false acceptance, evidence loss, cross-profile or cross-parser reuse, or
engineer-override regression.

## 6. What this pilot is not

A sampled run of 380 documents (plus 15 sheets) over ten folders holding 24,311 PDFs. It is not a validation of
any whole project, not a live backfill, and not a claim over the 1,028 candidate folders of the archive.
