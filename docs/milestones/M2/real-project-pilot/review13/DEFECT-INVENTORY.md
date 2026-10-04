# Round 2: the source-backed failure inventory, and the change decision (deliverable 2)

**Where the figures come from.** They are counted from the accepted Review 12 re-score (evaluator `.9` over reader `.7` outputs, `C:/t/iso/work/r12/eval9-reader7`). Nothing was re-read for this inventory.

Every clear, applicable labelled fact that the evidence layer did not recover cleanly is put in exactly one category (`failure_inventory.py`; first match wins):
- **disputed label:** the page belongs to one of the 8 DECIDE groups of packet v2;
- **correct but withheld;**
- **failed reading:** the document's execution was bounded or failed;
- **wrong association:** readings exist on the page, attached to another component or to none;
- **missed discovery:** no reading of that field on the page;
- **literal misread** and **association swap.**

Evidence: `evidence/failure-inventory/FAILURE-INVENTORY.json` and `MISSED-DISCOVERY-BREAKDOWN.json`.

## 1. Inventory, by run

### Deterministic baseline, pilot (reader `.9`, no model)

| Field | Denominator | Recovered clean | Missed discovery | Wrong association | Failed reading | Withheld (correct) | Literal misread | Disputed |
|---|---|---|---|---|---|---|---|---|
| identity | 363 | 237 | **76** | 12 | 11 | 9 | 6 + 7 (the 7 alongside a correct reading) | 5 |
| revision | 310 | 220 | **84** | 0 | 3 | 2 | 0 | 1 |
| decision | 80 | 26 | **46** | 0 | 2 | 3 | 0 | 3 |

This run has **0** critical false accepts.

### Other exposed runs

| Run | Result |
|---|---|
| Deterministic baseline, holdout | identity 14/20 · revision 7/13 · decision 0/4 clean; 0 critical |
| Matched, model-disabled (16 / 16 / 9 components) | identity 14 · revision 13 · decision 6 clean; 0 critical |
| Matched, AI-EV1 | identity 14 · revision 13 · decision 7 clean; withheld-correct 1 / 2 / 2; **2 critical** |
| Matched, AI-EV2 | identity 14 · revision 13 · decision 6 clean; **1 critical** |

**The matched runs' critical errors are all the F09 dispute.** EP-30784 `BBY006_1.PDF` page 3 carries another project's supplier cover (`EP-30627/SS/EML/ 1293`, rev `00`). The label has no component on that page, and that labelling is exactly what F09 asks a person to decide. **These errors stay critical until F09 is settled.** They are not re-counted here.

## 2. What the inventory says about each blocker

| Blocker | What the evidence shows |
|---|---|
| **B-1 recovery** | Missed discovery dominates: 76 / 84 / 46 of the deterministic gaps. **72 of the 76 identity misses are page-1 document-level labels, 51 of them on pages with a text layer.** Example: EP-30784 `EM-101` has `EM-101` in the text layer next to `DRAWING NO.`, yet the deterministic reader produced no identity for it. That is a parser gap. On the matched set, the AI evidence stage closes most of that gap: identity misses fall from 1 to 0, and decision clean rises from 6 to 7 under EV1. The remainder is withheld-correct (held ≠ recovered). |
| **B-2 identity precision** | The only critical false accepts in the exposed runs are the F09 page. **No other wrong identity was automatically accepted.** Precision cannot be claimed beyond that, because five DECIDE groups (F01, F07, F10, F12, F13) are identity-role disputes with no settled truth. |
| **B-5 variant selection** | The existing matched evidence (12 documents) does not separate EV1 from EV2. Both are 14/16 on identity. EV1 has one more clean decision; EV2 has one fewer critical error. The difference is a single disputed page. **This round's small batch adds exploration evidence (METRICS.md), but no variant can be selected while truth is unconfirmed.** |
| **B-6 H-06 BOQ** | AI off, on `frozen-r12`: EP-8430 has 20 accepted rows, 17/20 quantities correct, and **3 critical wrong accepted quantities**: `PRS-CSNKP` "Numeric Keypad", "CD Changer" and "Printer", each printed `1` and read `4` (`evidence/boq/holdout-A-r12.json`). The crops (`worklist/h06`) confirm the printed `1`, pending a person's confirmation. The other holdout sheets hold every row. The row verifier (EV1 / EV2) is measured on this sheet in this round (METRICS.md §3). |

## 3. Change decision: no reader or parser change in this round

**No application change was made.**

1. **The evidence does point at a targeted fix.** Page-1 document-level identities that are present in the text layer next to a printed label (`DRAWING NO.`, `Document No.`, `Submittal No.`) are missed by the deterministic reader.
2. **It was not made now, for three reasons:**
   - **The truth it would be tuned on is unconfirmed.** Every exploration label is an AI proposal, and the exposed identity-role disputes are open. Tuning a parser rule against unreviewed truth is the pattern the policy forbids.
   - **The A/B/C comparison needs a fixed candidate.** A parser change would require a new freeze, a full-suite run and a re-run of every track, and the small-batch evidence it would rest on was only just arriving.
   - **A no-guess fix needs examples beyond the exposed pilot.** The fix is a label-anchored identity read with a boundary rule. It must not pick up referenced drawings, as F05, F06 and F11 already show. Writing it without guessing needs reviewed examples from the exploration set.
3. **What a change would be once truth is settled:**
   - **Parser:** read the value in the same table cell, or to the right of, a printed identity label on page 1 (`DRAWING NO.`, `DOC. NO.`, `Document No.`, `Sheet No.`, `Ref.`, `Qtn. Ref.`, `AASS Ref.`). Exclude `Ref:` lines that list priced or referenced drawings, and form-template control blocks (`Document Reference … Revision Number …`). Keep it observation-only (held) until a person has reviewed it.
   - **Tests:** the exposed misses (EM-101 and others) as positives; F05, F06, F11 and the DRF template block as negatives.
   - **BOQ H-06:** the verifier's blind quantity read is measured here first. If it catches the three rows, the change needed is a policy change (accepting only after verification), not a reader change.

Protections are unchanged:
- no loss;
- identity and revision association;
- cache and profile versioning;
- bounded history;
- manual override.

New facts from this round live only in the isolated sandboxes. There is no business-row promotion, automatic deletion, role replacement or tab-time processing.
