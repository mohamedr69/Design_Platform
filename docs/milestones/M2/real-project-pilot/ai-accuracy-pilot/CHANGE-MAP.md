# Change map — AI accuracy pilot candidate

Candidate commit `e5a0a94` on scratch branch `ai-pilot-2026-09-30`. Its parent is the accepted `3d5607d`. It lives in the scratch clone `C:/t/iso/ep-platform` (worktree `C:/t/iso/cand-ai`), not in the owner's repository. Nothing in the live application, services, settings, database or documents was changed.

| File | Change |
|---|---|
| `backend/app/ai/evidence_reader.py` | +135 / −2 lines, flag-gated |
| `backend/tests/test_ai_pilot_2026_09_30.py` | new, 24 tests |

When neither flag is set, the module behaves exactly like the accepted one:
- the version strings are unchanged;
- every new branch is behind `GUARD_ENABLED` or `TARGETED_ENABLED`.

## Call path inspected before the change

`evidence_stage` → `read_document` → `_read_page`:
- **discovery**: `discover_page`;
- **per field**: blind `read_identity` / `read_revision` / `read_decision`;
- **escalation**: when triggered;
- **validation**: `validate_value` / `validate_decision`;
- **then**: observations → `merge_evidence` (the envelope) → `evidence_for` (the shadow view by context).

Consumers see the `ai_evidence` envelope only. `EXTRACTION_PROMOTE_OBSERVATIONS` stays false, so nothing is promoted into business rows, `ProjectDocument.role`, submittal status or BOQ corrections.

## Why each change is needed (from the stored accepted-EV1 evidence of the earlier small batch, r2x-small-B)

S (the accepted EV1 run on the earlier small batch) held correct identities for three reasons.

| Cause | Examples | Changed function |
|---|---|---|
| **No region support.** `region_texts` clips `page.get_text` with the displayed (rotated) rectangle, so rotated sheets read the wrong area. | FAS-09, rotation 270: the display clip gives `''`, while the derotated clip holds `FAS-09`. | T-a |
| **Scans with no text layer.** | DRF 3105 | T-a |
| **Blind read incomplete.** Discovery gave no region, so the blind read never happened. | EP-23091 | T-b |
| **Bare revision token accepted as an identity.** | `Rev.0` | G |

## The changes

| Layer | Function | G | T |
|---|---|---|---|
| validation | `validate_value` | A value that is *wholly* a revision token (`Rev.0`, `REV 01`, `Rev A`, `R1`) in the identity field becomes `candidate` with `guard: bare_revision_token`. It is never validated and never becomes the component identity (revision target). | — |
| observation | `_read_page` (after the field loop) | The guarded token is kept as a raw revision observation: component `revtok`, role `revision_token`, state `observed_reference`, **no target**. | — |
| evidence (support) | `region_texts_v2` (new; replaces `region_texts` only when T is on) | — | The clip goes through `page.derotation_matrix`, so rotated sheets read the right area. If the region has no text layer, the fallback is local Tesseract OCR of the region (`_local_ocr`, the application's own OCR configuration, psm 6, 300 dpi), recorded as source `ocr_local`. |
| discovery / evidence (read) | `_targeted_read` (new), called from `_read_page` | — | One independent context read, task `read_field_context`. **When:** an own identity or revision was proposed (by discovery or the deterministic reader) and not validated. **Never:** after a failed or budget-refused request, or after a guard hold. **Input:** a wider crop (pad 1.5), or the whole page (long side 2400) when no region exists. **Prompt:** asks for the field only; it contains no proposed value, label, file name or expected answer. **Answer:** literal value, printed label, role (own identity / own revision / referenced identity / template or form code / date / other), region, legibility. |
| validation (unchanged rule) | `validate_value` | — | The targeted reading joins the readings, and the **unchanged** rule decides: every legible reading agrees, the literal is supported in the region's source text, and there is no deterministic conflict. A targeted role other than the field's own role downgrades a validation to `candidate`. |
| budget | `EvidenceRun.call` (unchanged) | — | Every targeted read is an ordinary request under the same per-document budget, ledger and caps. It is counted and logged as `own:<field>:targeted`. |

**Not changed:**
- the thresholds and the decision policy (legend, consultant/client mark);
- `merge_evidence`, `evidence_for`, and the no-loss / last-good / attempt-anchor semantics;
- BOQ row verification;
- business consumers;
- the evaluator and the r16.1 matcher.

## Harness-only additions (outside the application)

- **`boq_queue.py`**: the BOQ-T risk-ordered row queue and `verify_queue`. It reuses the accepted r16.1 `DocAllowance` / `DurableBudget` unchanged.
- **`pilot_*.py`**: runners adapted from the Round 2 runners, adding:
  - per-arm ledger scopes;
  - per-arm project shares;
  - model input/output capture;
  - the stop tripwire;
  - a dry mode.
