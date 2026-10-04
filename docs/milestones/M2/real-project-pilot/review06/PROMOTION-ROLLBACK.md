# M2 Review 06: promotion and rollback proposal for the exact isolated candidate

**This is a proposal only.**
- Nothing is promoted, committed or pushed.
- No live setting or service is changed.
- M2 stays **CHANGES STILL REQUIRED**, and M3 is not started.

The owner's working tree (HEAD `2221b43` plus the uncommitted Candidate C) is untouched.

## The candidate

| Item | Identity |
|---|---|
| Isolated copy | `C:/t/iso/ep-platform/backend`, a scratch repository, branch `iso-baseline` |
| Baseline commit | `c692f1e2cf20ad92ff2414ab7a433fc9102ad406`: Candidate C, carried from the owner's tree, with all 11 frozen hashes verified |
| Candidate change | `evidence/candidate.diff` (tracked files) plus `evidence/candidate_new_files/`. SHA-256 of every changed file is in `evidence/EVIDENCE-MANIFEST.json` → `candidate.changed_files_sha256` |
| Parser | `parse-2026-09-29.8` |
| Title block | `titleblock-3` |
| Labelled fields | `fields-2026-09-29.1` |
| Transmittal observe | `transmittal-observe-2026-09-29.1` |
| Sheet extractor | `2026-09-29.1` |
| Evidence reader | `evidence-reader-2026-09-29.1` / `evidence-policy-2026-09-29.1`, **off by default** |
| Evaluators (not application code) | document .4, BOQ .3 |

### Files changed against Candidate C

| File | Change |
|---|---|
| `app/services/title_block.py` | DRG/DOC labels, sub-label rows, nearest REV, OCR fallback with `ocr_number` trust, regions |
| `app/services/document_control.py` | `.8`; OCR title-block lines through `page_cache`; page gate on the own title-block number; `page_evidence` |
| `app/services/labelled_fields.py` | new: `form_identity` observations |
| `app/services/transmittals.py` | `observe`, `looks_like_transmittal_form` (additive) |
| `app/services/document_sync.py` | the Word transmittal is also observed |
| `app/services/design_sheet_extractor.py` | `2026-09-29.1`: `HOLD_ON_PASS_DISAGREEMENT`; `CONFIRM_CATALOG_BELOW` knob (default unchanged) |
| `app/ai/evidence_reader.py` | new |
| `app/services/document_processing.py` | evidence stage hook, only when `AI_EVIDENCE_VARIANT` is not `off` |
| `app/core/config.py` | `ai_evidence_variant = "off"` |

## Promotion proposal

These are staged steps, each needing the owner's or reviewer's decision. None is done here.

1. **Deterministic part: parse `.8`, `titleblock-3`, fields, transmittal observe, sheet extractor `2026-09-29.1`.**
   - **Effect:** the parser version changes, so every row is read again on its next processing. That re-read is the existing mechanism; there is no migration. Retained provenance and the no-loss re-read keep the last good reading until the new one is complete.
   - **Recommended precondition:** an independent re-review of this package, then a decision on D-R6-A (flagged references as register keys).
   - **Behavioural changes an owner should know:**
     - AGC-style shop drawings with vector title blocks now become register records.
     - Transmittal and `form_identity` observations appear in `extracted`, without any new register rows.
     - Some BOQ quantities that used to be accepted are now held for review when the independent passes contradict the strip. That holds, for example, a printed 48 that the passes read as 86, which Review 02 had accepted.
2. **Evidence reader.** It stays **off** (`AI_EVIDENCE_VARIANT=off`). EV1 or EV2 is not proposed for live use until:
   - (a) the evaluator shows no introduced critical error on a broader exploration cohort;
   - (b) the per-call token cap is enforced on actual usage (D-R6-D);
   - (c) a cost basis exists, or the owner accepts unknown cost;
   - (d) the project AI policies for the target projects are recorded.

   Even when on, it writes only `extracted["ai_evidence"]`. No consumer reads it yet, and migrating consumers is explicitly out of scope.
3. **Round 2 sealed validation** after the freeze (ROUND2-PLAN), with independent labels and a second review.

## Rollback

| Part | Rollback | Data effect |
|---|---|---|
| Evidence reader | `AI_EVIDENCE_VARIANT=off`, which is the default. | The stage stops. Existing `extracted["ai_evidence"]` entries are dropped on the row's next re-read; no consumer depends on them. `AiUsage` rows with task `evidence:*` stay as history. |
| Parser `.8` → Candidate C `.6` | Restore the Candidate C source (the baseline commit `c692f1e` holds it exactly). | The version change causes a re-read under `.6`. The observations `form_identity` and `transmittal` (with items) disappear, and AGC records made from OCR title blocks are no longer emitted. Engineer overrides and business statuses are not touched by either direction. |
| Sheet extractor `2026-09-29.1` → `2026-09-28.2` | Restore the file, or set `HOLD_ON_PASS_DISAGREEMENT=False`. | The BOQ from the deterministic reader is not an application path (the application BOQ path is the model's `sheet_reader`). There is no stored-data effect. |
| Evaluators | Evaluation scripts only. | None. |

**Verified in this round:**
- The stage writes only its own key (`test_stage_is_off_by_default_and_writes_only_its_own_key`).
- The records and register mirror columns are identical between AI-EV0 and AI-EV1/EV2 on the real runs (REAL-MODEL-RESULTS, "mirror identical").

**Not verified:** a live rollback rehearsal. Live services are out of scope.
