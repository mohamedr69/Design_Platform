# M2 source-review packet v2: for the human reviewer

**Status: prepared, not reviewed.** No item in this packet has been checked by a person, and nothing here is a human signature. An AI model prepared the proposals and the index. That is not approval.

This is the successor of `../../review07/human-review-packet/` (v1). v1 is kept unchanged as history. v2 contains the same items and the same agreed scope. It changes three things:

1. **Identities are recorded one per row.** Each row gives the literal, its printed label and its role. v1 asked for two own identities to be joined with ` | ` and marked `ambiguous`; v2 does not.
2. **"Ambiguous" is narrower.** It now means only that a fact or an association is still open. A page that legibly prints two identifiers is not, by itself, ambiguous.
3. **The findings index.** [FINDINGS-INDEX.md](FINDINGS-INDEX.md) groups the 13 Review 07 source findings and links each one to its rows and page images. Eight groups need a decision.

## Who reviews

The reviewer is the owner, or a person the owner appoints. That appointment is still open. The reviewer writes their name in `human_reviewer` on every row they settle. No name is filled in for you.

## Files

| File | What it is |
|---|---|
| `COMPONENT-ITEMS-v2.csv` | 339 component items (as in v1), one per page component. The `finding_group` column names the index group the item belongs to, if any. |
| `IDENTITIES-v2.csv` | 359 identity rows: every identity proposed for an item, one per row. 20 items have more than one. A proposal's free-form note (its source, its confidence, a cut cell) is kept whole in `proposal_note`; it is never a printed label. |
| `BOQ-ITEMS-v2.csv` | 194 BOQ rows (as in v1), with a row type and separate part and quantity status. |
| `FINDINGS-INDEX.md` / `.json` | The 13 Review 07 source findings, linked to items and pages. |
| `PACKET-SCHEMA-v2.json` | Every column, and the values it takes. |
| `PACKET-MANIFEST-v2.json` | Counts, file hashes, and the hashes of the v1 files this version succeeds. |
| page images | Kept in the v1 packet (`../../review07/human-review-packet/pages/`) and linked from every row. Each was rendered from the staged copy of the original; the source hashes are in the v1 manifest. |

As in v1, you are shown the AI-drafted label to confirm or correct. You are not shown any platform or AI reading. You label the source, not a prediction.

## Filling a component item

**1. The identities (`IDENTITIES-v2.csv`).** For each identifier printed on the page that matters to this component, make one row:

- `human_literal`: exactly as printed, character for character;
- `human_printed_label`: the label printed beside it, such as "Drawing No", "Permit Number", "Mail number", "Ref";
- `human_role`: one of the following:

| Role | Meaning |
|---|---|
| `own_document` | this document's own number |
| `own_document_alternate` | another party's number for the same document, such as the contractor's number next to the consultant's |
| `permit` | a permit number |
| `request` | a request or application reference |
| `reviewed_document` | the document this form or reply reviews |
| `transmitted_item` / `listed_item` | an item a transmittal sends or lists |
| `referenced_document` | a drawing or document the page cites |
| `project_or_contract` | a project or contract number |
| `other` | none of the above |

- `human_own_for_evaluation`: `yes` for the one identity the register should be evaluated on, `no` for every other row, and `unresolved` if the source does not settle it;
- `human_status`, one of:

| Status | When |
|---|---|
| `settled` | the literal and its role are clear |
| `illegible` | the literal cannot be read |
| `unresolved_fact` | the literal itself is uncertain |
| `unresolved_association` | it is unclear which component the identity belongs to |

Correct any proposed row that is wrong, and add rows for identities that were missed. Leave a row blank if it does not matter to this component.

Two legible identifiers with clear roles are **settled**, not ambiguous. A permit number next to a request reference is one example; a consultant's mail number next to a contractor's reference is another. Say which one is evaluated.

**2. The item (`COMPONENT-ITEMS-v2.csv`):**

- `human_identity_status`:
  - `settled`;
  - `unresolved_fact` or `unresolved_association`, when the identity rows leave something open;
  - `absent`, when the page has no component;
  - `illegible`;
  - `conflict`, when the source contradicts itself.
- `human_own_identity_for_evaluation`: the literal you marked `yes`, or blank.
- `human_printed_revision` and `human_revision_status`.
- `human_decision`, `human_decision_actor` and `human_decision_status`. A decision counts only if it is marked; the status is `settled`, `absent`, `illegible`, `conflict` or `unresolved_fact`.
- `human_association_status`: `settled`, or `unresolved_association` when it is unclear whether this page belongs to the document. Finding F09 is an example: a cover carrying another project's number.
- `human_uncertainty`: a short reason, whenever a status is not `settled`.
- `human_reviewer`, `human_date`, `human_notes`.

Do not guess. When the source leaves a fact open, record `unresolved_*` with a reason.

## Filling a BOQ row (`BOQ-ITEMS-v2.csv`)

- `human_row_type`, one of:

| Row type | Meaning |
|---|---|
| `item` | a priced or quantified line |
| `heading` | a section title; it has no part or quantity |
| `part_only` | a part is printed and no quantity is |
| `note` | a note line |
| `unreadable` | the row cannot be read |

  A heading row that prints a part, a quantity or a "( n )" count is not a heading: record what is printed.
- `human_part_number`: exactly as printed, keeping every `+`, `/` and `-`. `human_part_status` is `settled`, `absent`, `illegible` or `conflict`.
- `human_quantity`: with its decimal point, sign or unit. `human_quantity_source` is `column`, `description_count` or `absent`. `human_quantity_status` is as for the part.

## Start with the findings index

[FINDINGS-INDEX.md](FINDINGS-INDEX.md) lists the 13 Review 07 source findings:

- **8 groups (10 items) need a decision:** F01, F02, F07, F08, F09, F10, F12 and F13;
- **5 groups (13 items) need only a confirmation of the label literal:** F03, F04, F05, F06 and F11.

One correction is recorded there. Review 07 filed finding 10 under EP-29076; the file is in EP-26082. The Review 07 table itself is not edited.

## What happens with your answers

- Settled rows become a new, versioned label set, labels v3. The AI-drafted sets v1 and v2 stay as history.
- Any field left blank, or marked `unresolved_*`, stays **unresolved truth**. It is kept out of acceptance denominators and reported as a coverage gap, and it is never counted as a platform success or failure.
- The evaluator reads the identity marked `yes` for the register. The other settled identities are kept with their roles, so that a reading of one of them is scored as a correct reading of an identity with that role, not as a wrong own identity.
- A second reviewer is not required for this scope. If one does review, their disagreements go in `human_notes` and are resolved together.
