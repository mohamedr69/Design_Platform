# Label conventions R32 (frozen before any label is drafted)

**Labels:** `r32-labels-draft-1`, for the fresh M2 cohort pool `FROZEN-SELECTION.json` (sha256 `bf71779a…5d21`).

**Prediction-blind:**
- No prediction, application output, register, extracted record, earlier label or model-run evidence exists for these documents, or is consulted.
- A file name or folder name is **never** evidence.
- No model or provider request is made.

## 1. Unit and scope

- **Unit:** each staged document (`F###`). Pages 1–4, the reader scope, are labelled page by page. Later pages are counted, not labelled.
- **Duplicates:** byte-identical staged files (F038 = F052, F067 = F070) are labelled once, on the lower id. The other carries `duplicate_of`, and each pair **counts once** in every field population.

## 2. Fields and states

Each in-scope page has three fields: `identity`, `revision` and `decision`. Each field has exactly one state:

| State | Meaning |
|---|---|
| `present` | a value of this field's semantic role is **visible on this page** and legible. The literal and its semantic role are recorded. |
| `absent` | no value of this role is printed on this page. For `decision`, `absent_kind` is `blank_decision_area` (a review or status area exists and is unmarked, exported as `UR`) or `no_decision_area` (exported as `n/a`). |
| `illegible` | the field's place is visible (a cell, stamp or mark), but its value cannot be read with certainty |
| `ambiguous` | a value is readable, but which role it has, or which of several candidates is the field, cannot be established from the page |
| `unsupported` | the page cannot be assessed: no usable render, a blank or unreadable scan, or a non-document image |

- **Value uncertainty** is carried by the state (`illegible`, `ambiguous`).
- **Association uncertainty** is recorded **separately**: `association` is `resolved` (the value belongs to this page's own document) or `uncertain` (for example, a stamp on a package cover whose scope is unclear, or one decision for several listed drawings), with a note.

## 3. Identity

- **What counts:** the page's **own** document number as printed: drawing number, document or submittal number, transmittal or letter reference, or certificate number, with its printed label.
- **Other numbers:** project codes, plot, job and BOQ numbers, form or template numbers, referenced drawings and catalogue codes go to `other_identities`, with roles. They are never the identity.
- **Literal:** the literal is kept **as printed**, including punctuation, hyphens, slashes, leading zeros and internal spaces. Only line breaks inside one value are joined with a single space.
- **Split cells:** when the number is printed in separate cells (for example a project cell and a serial cell), the cell labelled as the drawing or document number is the identity, and the split is noted.
- **Several candidates:** when two candidate own numbers appear and neither is marked as the document's own, the state is `ambiguous`.

## 4. Revision

- **Primary source:** the page's own current revision, from its revision cell or title-block `REV` field, as printed (for example `0`, `00`, `01`, `A`, `R1`).
- **Table only:** when only a revision-history table is printed, the latest entry is recorded, with `semantic_role: "latest revision-table entry"`.
- **Embedded only:** when the revision appears only inside the printed document number (for example a `-R00` suffix), it is recorded with `semantic_role: "suffix of the printed document number"` and `association: uncertain`.
- **No sources:** no revision cell, table or suffix means `absent`.

## 5. Decision

- **What counts:** the review decision of the **reviewing party**, the consultant or an authority (for example Civil Defence or DEWA), on the document this page belongs to. It may appear as a stamp, a ticked option, a code letter with its legend, or a handwritten statement visible on the page. `actor` and `actor_state` (`resolved` or `inferred`) are recorded.
- **Not decisions:** contractor internal stamps ("checked", "for submission"), receipt or "received" stamps and approval-workflow boxes left blank are not decisions.
- **Literal and class:** `literal` is the printed or written decision text, and `class` is one of `approved`, `approved as noted` (approved with comments, code B, no objection with comments), `revise and resubmit` (code C, resubmit), `rejected` (code D, not approved), or `other`, with a note.
- **Location:** `in_title_block` or `outside_title_block`.
- **Page level:** a package decision printed only on the cover is **not** copied to enclosed sheets whose own status area is empty. Those sheets are `absent` with `blank_decision_area`, as in the earlier label sets.

## 6. Evidence

- **Location:** every `present`, `illegible` or `ambiguous` field has a region in fractions of the displayed page (0 to 1, origin top-left).
- **Visual confirmation:** a crop (`CROPS.jsonl`, recipe CROP-R32-1, bound to the staged sha256) or the full render (`RENDERS.json`, recipe RENDER-R32-1) shows the value. The text layer is used only to locate a region. A value is recorded only after it is seen.
- **Text-layer mismatch:** where the text layer and the visible rendering differ, the visible rendering wins, and the difference is noted.

## 7. Document resolution (draft proposal; the independent review rules)

- **Draft confidence:** `high` when every in-scope page field is `present` or `absent` and every present value's association is resolved. Otherwise it is `medium`, with the open items listed in `unresolved`.
- **Counting rule (after review only):** a document **carries** a field when, after review, at least one in-scope page has that field `present` with association `resolved` and the document is resolved. Draft counts are never gate counts.

## 8. Provenance

- **Authorship:** drafts are AI-authored (Claude Opus 5.5 coding assistant, this session) and **not human-signed**.
- **Review:** the independent review is the owner-delegated Codex reviewer. It is an AI review, not human sign-off. The drafter does not review its own draft a second time and call that independent.
