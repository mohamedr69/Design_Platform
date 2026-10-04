# M2 Review 06: AS-IS and candidate call flow

The AS-IS column describes the reviewed Review 05 Candidate C tree: owner HEAD `2221b43` plus the uncommitted changes, which are carried unchanged into the isolated baseline commit `c692f1e`. The candidate column describes the isolated copy at `C:/t/iso/ep-platform/backend`.

Line references point to the isolated copy.

## 1. Document reading (sync-documents job, then processing)

| Step | AS-IS (Candidate C, parser `.6`) | Candidate (parser `.8`) |
|---|---|---|
| Entry | `sync-documents` job, then `document_processing.run`. Nothing runs from a GET handler. | Unchanged. |
| Deterministic read | `document_sync.extract`, then `document_control.read_pdf_full`, then `parse_page` for each page. | Unchanged. |
| Page gate | A page yields records only if its text matches the register grammar (`required`), or has consultant-reply wording. | Same, but a page whose title block gives its **own** number (`title_block.read_page`) passes as well ([document_control.py:1272](../../../../../backend/app/services/document_control.py)). This is where AGC-DF-MEP-SD-PAS sheets (H-01) now become records. |
| Title block | Text layer only. The number label accepts DRAWING/DWG. The REV cell must be on the number's row. | Labels DRG/DOCUMENT/DOC are added. A stacked sub-label row (`ORIGINAL SIZE`) is skipped. The nearest REV cell is used within 25% of the page height. If the text layer gives no number, the title-block strip is OCRed; the lines are cached in `page_cache`, variant `tb-ocr-1`. **An OCR number becomes the sheet's number, and so a register key, only when it is one clean identity-shaped token with no O/I/L against a digit** (`titleblock-3`, `ocr_number`). Otherwise the literal and the candidate stay in the observation (`number_literal`, `number_candidate`) with the reason. This was added after the `.7` pilot run showed 3 wrong register keys (`XY) LAC-653-…`). Regions are recorded. |
| Evidence the grammar cannot carry | Nothing. A page without a record left no trace, except the Review 05 untracked-sheet observation. | `page_evidence`: every transmittal becomes an observation (`transmittals.observe`: own TR number, date, to/attn, subject, project id, listed items, receipt evidence). On the first 4 pages that gave no record, labelled form fields become a `form_identity` observation: the literal identity with its label, revision, date, stated purpose and region. Word transmittals are observed the same way. |
| Output | `extracted.records` / `observations` / `coverage` on the row, plus the register mirror columns. | Same keys. The observation kinds `transmittal` (with items and receipt) and `form_identity` are added. No new business status, role or category. |
| Application AI (AS-IS path) | A form with role submittal and no stored reading is deferred to the AI stage. `submittal_reader.read_form_or_raise` (`read_submittal_form`, prompt `submittal-2026-09-17.1`, at most 2 pages) runs, then `apply_form_reading`. | **Unchanged. This is AI-EV0.** |
| New AI evidence stage | None. | `evidence_reader.evidence_stage` runs **after** the AI stage, on the PDFs read in this run. It is **off by default** and is on only when `AI_EVIDENCE_VARIANT` is EV1 or EV2 (see §3). It passes through the same gate as other AI reading (`submittal_reader.available`: AI enabled, the project's `ai_policy`, provider ready, task not switched off). It writes only `extracted["ai_evidence"]`. |

## 2. BOQ / Design Sheet

| Step | AS-IS | Candidate |
|---|---|---|
| Application path | `POST /projects/{id}/boq/ensure`, then (with the model) the `boq-read` job, then `sheet_reader.read_design_sheet` (`read-sheet-2026-09-16.1`, `verify-rows-2026-09-27.1`). With the model disabled, the sheet is recorded as **not read**. There is no deterministic fallback. | Unchanged. The deterministic `design_sheet_extractor` is still not an application path; it is evaluated as its own track. |
| Deterministic reader | Version `2026-09-28.2`. The part-number cross-check (`_confirm_catalog`) runs only when the strip confidence is below 90. A 60–90% strip quantity stands even when independent passes agree on another value (only a cut digit holds it). | Version `2026-09-29.1`. **Two or more agreeing independent passes against the strip quantity, none backing it, hold the row for review with both readings** (`HOLD_ON_PASS_DISAGREEMENT`, H-06). The part gate is its own knob, `CONFIRM_CATALOG_BELOW`, default 90 (unchanged); 101 was measured as an option (BOQ-RESULTS). |
| AI row verification | None. The model path settles rows with its own second readings. | `evidence_reader.verify_boq_rows` is an experiment function and is not wired into the application. It is a blind crop of each row across the table. EV1 reads every held row plus the frozen 20% audit of accepted rows; EV2 reads every row. Readings are compared afterwards by `validate_boq_row`. |

## 3. The evidence stage (candidate only)

1. **Triggers** (`triggers()`), for each page up to 4 pages per document:
   - `form_or_title_block_without_identity`
   - `identity_without_revision`
   - `decision_block_unread`: two or more printed options, and no decision was read
   - `flagged_by_reader`
   - `unexplained_empty_document`
   - `audit_confident_output`: EV1, the frozen 20% sample, seeded by `audit-2026-09-29` + content hash + page
   - `broad_verification`: EV2, every page with a critical fact

   A page with no trigger records `no_trigger`, which is a coverage entry, not a negative.
2. **Discovery** (`discover_page`): the whole page, downscaled to a long side of 1600 px. The model is **not** given any existing record, regex match or file name. It returns the page kind, its own identity, revision and decision block (literal value, label, region on a 0–1000 scale), and the other numbers it saw with their roles.
3. **Blind reads** (`read_identity`, `read_revision`, `read_decision`): a 300 dpi crop around the region. The deterministic reader's own geometry comes first (`titleblock-2` regions, `form_identity` region); discovery's region is used otherwise. The prompt text is fixed per task and never contains a proposed value; `test_blind_reads_never_carry_a_proposed_value` checks this.
4. **Validation** (`evidence-policy-2026-09-29.1`):

   | State | Condition |
   |---|---|
   | `validated` | A legible blind read whose literal is found in the page's text layer or cached OCR, and which no other reading contradicts. |
   | `candidate` | Read, but without source support, or read by discovery only. Model agreement alone is never enough. |
   | `conflict` | The readings disagree, or they disagree with the deterministic value. Neither side is preferred. |
   | `unreadable` | No legible reading. |

   A decision is `validated` only when a printed option is explicitly marked, by the consultant or client, and the blind read agrees with discovery.
5. **Escalation** (EV2 only): at most 2 readings **per document** go to the standard tier (configured alias `opus`; the model returned was `claude-opus-5`), for a `conflict` or `candidate` result. This matches `AI_MAX_ESCALATIONS_PER_DOCUMENT`.
6. **Output**:
   - `extracted["ai_evidence"]` holds `{version, policy, variant, read_sha256, observations, coverage, calls}`.
   - Each call writes an `AiUsage` row with task `evidence:<task>`, the model returned, tokens, latency, outcome and `escalated`.
   - An unknown price is logged as cost `None` in the run log, never as 0.
   - A failure, timeout or budget stop is recorded as such, and nothing is cached from it.
7. **Cache identity**: scope `evidence` + document hash + fingerprint of the exact parts sent + task + {variant, profile, policy, tier} + reader version + prompt version + schema + model. EV1 and EV2 never share an answer. `fresh=True` bypasses the cache for experiments.

## 4. Compatibility results

| Contract | Evidence |
|---|---|
| Records, business status, revision projection and engineer values are untouched by AI | `test_records_and_observations_are_never_modified`, `test_stage_is_off_by_default_and_writes_only_its_own_key`, and the real-model runs (register mirror columns identical between AI-EV0 and EV1/EV2; see RESULTS). |
| No AI or OCR in GET handlers | `test_no_get_handler_reaches_the_evidence_reader` (no router imports the module). The OCR title-block fallback runs inside `read_pdf_full` in the processing job and is page-cached. |
| Default off | `ai_evidence_variant: str = "off"` ([config.py](../../../../../backend/app/core/config.py)). `configured_variant()` returns `off` for any unknown value. |
| Project AI policy honoured | The stage returns `not_run` with the reason when `submittal_reader.available` refuses. |
| Role, legacy categories, sample-register behaviour | The reviewer's 28-module set and the full suite (REGRESSION.md). The Word transmittal branch still returns `read_transmittal` records; `observe` only adds an observation. |
