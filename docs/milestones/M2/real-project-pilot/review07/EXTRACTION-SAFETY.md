# M2 Review 07, section E: extraction safety within existing ownership

Frozen candidate `c9a1a14`: `parse-2026-09-29.9`, `listed-item-2026-09-29.1`, sheet extractor `2026-09-29.2`. No approval status is changed, and no business policy is invented.

## 1. Incomplete / uncertain register keys (B-2)

### Future ingestion guard

Files: `app/services/document_sync.py`, via `mirror_from`, `hold_uncertain_references`, `uncertain_reference_cases` and `log_records`.

- **The row mirror** (reference, revision, status) is taken from the first record whose reference is **not** flagged `reference_incomplete` or `reference_uncertain`.
- If every record is flagged, the mirror **keeps what it had**. It is not renamed, cleared or moved to the uncertain value.
- The flagged readings are stored as `extracted.pending_evidence`, each under a **stable internal key**, `doc:{document id}:p{page}:r{record}`, never under the uncertain reference.
- **`log_records`** is the single path to every register builder: the drawings log, the submittal map, project home and the logs page. It does not hand a flagged record to them, so no business row is created, merged or reconciled under that value.
- **An existing business row already filed under exactly that reference** (a shop-drawing record or a submittal) is **preserved**. Its record still reaches the builders, so nothing is deleted, renamed or falsely marked "source missing". It is listed for the owner to adjudicate (`uncertain_reference_cases`).
- Engineer-confirmed rows are never touched.

### Tests: `tests/test_m2_review07_extraction.py`

- the mirror is not set from a flagged reference, an existing mirror is kept, a settled record beside it still sets it, and pending evidence has a stable key;
- `log_records` holds a flagged reference, unless a submittal already carries it; the case list marks `existing_business_row`;
- an engineer-confirmed drawing under an uncertain key is left alone;
- generic incomplete references (`X-SD`, `-0012`, `AB-`) never become business keys.

### Dry-run impact

`evidence/GUARD-DRY-RUN-{default,promoted}.json`, read only: `.8` (no guard) against `.9` (guard), the same staged pilot sources, both profiles.

| | Default | Promoted |
|---|---|---|
| Shop-drawing / submittal rows added, removed or renamed | **none** | **none** |
| Document mirrors changed | 1: `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020-01_CODE C.pdf`, from the cut key `V-EL-MTG-PJW-ZZZ` (R1) to the document's own settled record `R1029-CSM-CO-ELV-EL-MTG-PJW-ZZZ-ZZZ-1020` (R0) | same |
| Cases held as pending evidence | `A23-EFE-MAT-E-00033 … - B.pdf` page 4, `A23-EFECO-MAT-E`; MTG-1020 page 1, `V-EL-MTG-PJW-ZZZ`. **Neither has an existing business row** under the uncertain key. | same |
| Register critical (evaluator .6) | 2 → **0** | 2 → **0** |
| Cost | two correct printed revisions no longer reach the register (107 → 105) | 111 → 109 |

**Existing live data.** Read only, never written: the four projects registered in the live database (30784, 30880, 29076, 30088) hold **no** record with an incomplete or uncertain reference (`evidence/LIVE-READONLY-UNCERTAIN-REFERENCE-CASES.json`). There is therefore no live case for the owner to adjudicate now. The exposed pilot cases exist only in the sandboxes.

## 2. Transmittal versus listed submittal

- **The defect** (application path, AI-EV0): on `EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf`, a scanned acknowledgement of transmittal `TR/0127/26`, the form reader's reference `25H-S202-NCC-MAS-MEP-ELE-005-R3` (a listed item) became the row's register identity and a log record.
- **The fix** (`listed_by_transmittal`, `apply_form_reading`): when the page is a transmittal and the form reader's reference is one of the items that transmittal lists, it is not taken as the row's identity. The listed item's literal matches the reference, or is its start cut at a line break (at least 12 characters). Only the observation's own item table decides this; no file or folder name is used.
  - The row is **not filed** under the listed item, and **no log record** is made of it.
  - The reading stays on the row (`extracted.form`), and the relationship is kept as `extracted.submission`: `{relationship: "transmits", listed_item, listed_item_literal, transmittal_reference, transmittal_raw_reference, transmittal_reference_unread, date, basis, policy}`.
- **The same rule on the two other business paths the listed item took:**
  - the submittal map (`submittal_reader.check`): the reading draws no submittal, and a warning names the relationship;
  - the register's filed-in-the-folder listing (`routers/submittal._filed_in_the_folder`).
- **Regression test, on the normal application path** (`test_a_transmittals_listed_submittal_is_not_filed_as_its_identity`):
  - a scanned acknowledgement (image only, in a submittal folder) is classified `submittal_form` exactly like the real one;
  - OCR runs; the scripted form reader returns the listed item; the `sync-documents` job and processing run inline;
  - the row is not filed under the listed item, there is no form record, and the relationship is kept with `TR/0127/26`;
  - `/logs` carries no material submittal for it;
  - **a second sync keeps the reading and the relationship** (no loss).

  The existing form tests (`test_document_sync`, `test_submittal`) still pass.

## 3. BOQ: disagreement and component counts

- **B-6, hold on contradiction** (accepted by the reviewer): kept, with the strip literal, the alternatives, the region and the reason. Neither quantity is chosen. The Review 06 regression tests are kept (`test_m2_review06_boq.py`, and the changed Review 02 assertion).
- **Counts printed in a description** (`( 2 ) Dual Input Module`) are now a **separately located source fact** (`_inline_count`, sheet extractor `2026-09-29.2`):
  - the row's `quantity_parse` records `source: description_count`, the description literal and the cell literal;
  - where the quantity cell holds a *different* value, neither is taken and the row is held with both literals.

  Tests are in `tests/test_m2_review07_boq.py`.
- **The verifier keeps `part` and `quantity` distinct.**
  - `part_verified_quantity_unverified` never becomes `validated`.
  - An empty quantity cell is not proof of absence: the blind description's "( n )" is read as a located count.
- **Protection from removal.** A sheet that is not read, or is read incompletely, removes no BOQ line. The model-disabled application path still refuses with "BOQ is unchanged", and the re-read job kept 82/82 and 84/84 items (Review 06 run, unchanged path).
- **The stored-reading policy candidate** from Review 06 stays a candidate. It was shaped on exposed data, and it is not frozen as accepted behaviour until it has been tested on fresh sheets.
