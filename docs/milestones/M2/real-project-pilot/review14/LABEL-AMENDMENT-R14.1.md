# R14-03: the AI source review as a versioned label amendment (`r14.1`)

## Provenance (stated on every unit)

| | |
|---|---|
| Reviewer | Codex, an **independent AI reviewer**. The owner delegated the review of the prepared worklist ("انت راجعها"). |
| What it is not | **Not a human signature. Not blind** to the earlier predictions. |
| Human fields | Empty. No reviewer name was put into a human field. |
| Source | `M2-review-14/AI-SOURCE-REVIEW.json`: 43 units, 23 source findings, 4 H-06 rows, 7 small-batch questions, 5 critical accepts and 4 sample units. All 59 hashes in `REVIEW-MANIFEST.json` were checked. |

**This covers 43 worklist units.** It is not a review of all 415 documents, all 339 packet components or all 194 BOQ rows, and it is not acceptance of M2.

## 1. Binding: document SHA-256 → page → image (all 43 units bound)

**Method 2, regeneration** (`evidence/r14/regen_binding.py`, output `BINDING-REGEN.json`):
- Every evidence image the review used was **regenerated from the hash-verified staged source, with the exact recipe that first produced it**:
  - the finding, OCR, small-batch and critical crop scripts, unchanged, with the output folder redirected;
  - the render recipe;
  - the H-06 row recipe, recovered from the session transcript.
- Each regenerated image was then compared with the reviewer's copy.
- **Result: 48 of 53 image uses are byte-identical.** That binds hash → page → image by construction. It includes pages whose content repeats, such as the identical EP-17428 divider headers, which appearance matching alone cannot tell apart.

**Method 1, appearance matching** (`bind_images.py`, `BINDING.json`):
- This applies to the 5 remaining uses: the Review 07 packet page images, which have no local recipe.
- Each image is compared with the claimed page, re-rendered from the hash-verified copy, using normalized cross-correlation. As a control, the same comparison is made with other pages.

| Unit | Image | Score on the claimed page | Best control |
|---|---|---|---|
| F04/C0261 | `46e16cad3602ed1a-p1.jpg` | 0.995 | −0.004 |
| F05/C0191 | `ea9d1519b8af2f08-p1.jpg` | 0.994 | 0.026 |
| F06/C0193 | `3679b3cbd02b4194-p1.jpg` | 0.984 | 0.199 |
| F11/C0244 | `8f171daed83c545e-p9.jpg` | 0.970 | 0.359 |
| F13/C0283 | `44665c3b5543786e-p1.jpg` | 0.976 | 0.013 |

**Method 1's own history.** Its first run accumulated local variances in 32-bit floats and produced scores above 1. That run is kept as `BINDING.defective-run-1.json` and discarded. The corrected run also leaves 23 crop images below its 0.90 bound, for two reasons: the divider pages repeat, and the multi-scale search is coarse on large drawings. **It is not used to decide any crop; method 2 decides those.**

**Literal cross-check** (`LITERAL-CHECK.json`). Every reviewer literal was checked against the source's text layer.
- **F11/C0226.** The reviewer transcribed `…-GRO-INT9011-01`. The PDF text layer carries `-GRO-INT-` and `9011-01`: the hyphen is printed but hidden by overlapping glyphs in the image. **The label literal `R1029-07-W&A-DWG-TYP-GRO-INT-9011-01` is kept.** The discrepancy is recorded on the unit and not applied.
- **SAMPLE/2.** The AMANA number is drawn as vector graphics, so the text layer cannot confirm it. The image ruling stands.

## 2. The 43 dispositions and what they change

Files are in `evidence/labels/r14/`. The **originals are unchanged byte for byte** (the builder asserts their hashes): GOLDEN-LABELS, the v2 page labels, the holdout labels, HOLDOUT-BOQ-LABELS, and the small-batch proposal labels (`d21a83fd…`). Packet v2 and all earlier packages are also unchanged.

**The amended copies** (`*.amended-r14.1.json`) carry, per unit, a `r14_review` record with the reviewer and provenance. **`AI-REVIEW-AMENDMENT-r14.1.json`** lists, for every unit:
- the original worklist entry;
- the reviewer's observations, status and disposition, and the effect applied;
- the source document and page;
- the image SHA-256 and its binding;
- the literal checks and any remaining uncertainty.

| Status (count) | Units | Effect in `r14.1` |
|---|---|---|
| LABEL_CORRECTION (6) | F02, F04, F05, F06, F08, F13 | F02 p3: decision `ANN` (LACASA Code B), for the printed sheet `25H-AAEM-SD-ELEC-FA-B1-003A` rev 03 only. F04: `LPOD-1856000229`, with purchase request `LPRR-1856000239` recorded as a separate role. F05: `EP-19977-R3` (R3 from the printed suffix). F06: `EP-19977-R4-BD`; its revision is **held** (the review does not rule on it). F08 p1: the cover `EP-26369/SS/FA/101` rev 01 as a source component, register **off**. F13 p1: the Bosch letter `BSS/AE/ALARABIA/170315-047` as a correspondence component, register off, no approval. |
| ROLE_SPLIT (7) | F01, F07 ×3, F12, SB u3, SB u7 | Typed identities. F01: the permit `B2312982` is its own identity; the footer `REQ-2387569-2` is a request reference. F07: the mail number `TAVC-TRANSMIT-…` is the transmittal's own number; `K&A-WTRAN-…` is a linked reference. F12: the review form's own identity is `CRS-DOC-02006`; `CDS-DOC-01943` is the submitted reference; the MS number is the reviewed document; **the decision is not re-ruled.** SB u3: template fields confirmed as template. SB u7: the full cover literal is kept. |
| CONFLICT_HELD (1) | F09 | Page 3 becomes a component with its printed literal `EP-30627/SS/EML/ 1293` rev 00, as a **source fact**. The EP-30784 header and the EP-30627 number conflict, so the project and business association is **held** and the register is off. |
| PARTIAL_HELD (2) | F10, SB u5 | F10: reference `ambiguous` (unscorable); the candidate is kept and not used as a key. SB u5: part `+SL23I` / `+SL231` ambiguous; quantity 10 kept. |
| ROLE_HELD (2) | SB u6, CRIT/5 | `P06/TRANS/R1` is recorded as footer / control-code evidence, **held**, not an identity. |
| ASSOCIATION_HELD (2) | CRIT/1, CRIT/4 | The divider `Rev.0` is recorded as a **supported revision observation with no target**. It earns no register recovery. |
| CONFIRMED_READER_ERROR (1) | CRIT/2 | `Rev.0` is not an identity. The literal is kept as revision evidence. |
| LABEL_SCOPE_CORRECTION (1) | CRIT/3 | Page 2 of the calculation: revision `00` is a **supported raw observation**. Linking it to the page-1 cover is a **proposal, not accepted**, and it gets no register credit. |
| CONFIRMED (21) | F03, F11 ×9, H-06 ×4, SB u1, u2, u4, SAMPLE ×4 | Nothing changes, except that the review is recorded. SB u1 also adds the divider's revision observation with no target. H-06 is confirmed as quantities 1, 1, 1 and control 2; the two `PRS-CSNKP` rows stay distinct, and blank part cells stay blank. |

**The only schema addition is `supported_observations`** on small-batch pages. Evaluator `.9` does not read it, and it stays unchanged. **Overlay `r2x-overlay-2026-09-30.1`** (`evidence/r14/overlay.py`) types each critical fact against these observations and against the target the stored AI evidence actually recorded:
- a correct literal with no supported target stays **critical**, retyped;
- a supported literal of another role accepted as an identity stays **critical** (a role error);
- a held footer accepted as an identity stays **critical** (role not established);
- only a recorded target that equals the association proposal would count as a held association. **No such case occurs.**

The overlay has 7 targeted tests: every branch, plus the stored B and C outputs.

## 3. Re-scoring the stored outputs with the original and the amended labels (separately named)

This is evaluator `.9` under each run's declared context (`evidence/r14/rescore/`, `RESCORE-SUMMARY.json`, `RESCORE-DELTAS.json`). Recovered means clean plus mixed.

| Run | Labels | Critical | Identity | Revision | Decision |
|---|---|---|---|---|---|
| det9 pilot | original | 0 | 244/363 | 220/310 | 26/80 |
| det9 pilot | amended r14.1 | 0 | 247/364 | 222/311 | 26/81 |
| det9 holdout | original | 0 | 14/20 | 7/13 | 0/4 |
| det9 holdout | amended r14.1 | 0 | 15/21 | 7/13 | 0/4 |
| matched model-disabled | original / amended | 0 / 0 | 14/16 → 15/17 | 13/16 → 14/17 | 6/9 → 6/9 |
| matched AI-EV0 | original / amended | 0 / 0 | 14/16 → 15/17 | 13/16 → 14/17 | 6/9 → 6/9 |
| matched AI-EV1 | original / amended | **2 → 0** | 14/16 → 15/17 | 13/16 → 14/17 | 7/9 → 7/9 |
| matched AI-EV2 | original / amended | **1 → 0** | 14/16 → 15/17 | 13/16 → 14/17 | 6/9 → 6/9 |
| small batch det / A | original / amended | 0 / 0 | 4/8 | 1/5 | 0/0 |
| small batch B (EV1) | original / amended + overlay | 3 / **3** | 4/8 | 1/5 | 0/0 |
| small batch C (EV2) | original / amended + overlay | 2 / **2** | 4/8 | 1/5 | 0/0 |

**Reading the deltas** (`RESCORE-DELTAS.json`, per document):
- **Matched EV1 and EV2.** Their only criticals were the F09 page. Under `r14.1` that page is a component whose printed number the AI read correctly, so the criticals leave the evidence layer. **This is not register or business credit:** the component is register-off, and its project association stays held.
- **Pilot.**
  - F04 and F08 now recover.
  - F05, F06 and the three F07 transmittals now score the reader's older readings as **wrong** (`wrong_only`). Those readings were observed or held, never accepted, so they are not critical.
  - F01's permit number is `missed` by the deterministic reader.
  - F02 p3's decision is `missed`.
  - F10 becomes unscorable.
- **Holdout.**
  - F12 CRS-DOC-02006 is `wrong_only`: the reader had taken the reviewed MS number.
  - F13's letter reference is recovered.
- **Small batch.** No document changes under evaluator `.9`. The overlay **retypes** the criticals and removes none of them:

| Profile | Correct literal, accepted without a supported target | Role error (`Rev.0` accepted as identity) | Role not established (held footer accepted as identity) |
|---|---|---|---|
| B | 2 (DCH p2 `00`, EP-17428 p3 `0`) | 1 | – |
| C | 1 (EP-17428 p2 `Rev.0`) | – | 1 (`P06/TRANS/R1`) |

All five had a recorded target `null`. So revision `00` on the calculation's history page is a **supported raw observation**. Its acceptance, which attached it to an unidentified page-2 component, remains an acceptance error.

**These figures are diagnostics** on AI-drafted and AI-reviewed truth. They are not human-adjudicated, and they are not accuracy acceptance.
