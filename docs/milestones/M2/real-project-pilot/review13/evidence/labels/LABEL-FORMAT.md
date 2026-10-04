# Round 2 exploration: source label format (AI-drafted proposals)

**Status of every label here:**
- These are **AI-drafted proposals** (Claude), transcribed from the staged source renders and text layer **before any candidate prediction** for the document was produced or viewed.
- They are **not** human truth and not a sign-off. Human review is required for:
  - all decisions;
  - all critical disagreements;
  - all ambiguous identity, revision and part cases;
  - the predeclared independent sample (the Round 2 plan: a seeded 20% of the rest).
- **Provisional only.** Until that review is done, any metric computed from these labels is provisional and cannot support accuracy acceptance, final variant selection or sealed evaluation.

## Shape

The shape is compatible with page labels v2, so evaluator `.9` reads it unchanged. There is one entry per document, keyed by `doc_key`:

```json
{
  "doc": "EP-xxxxx/<relative path>",
  "sha256": "<staged content hash>",
  "scope_pages": [1, 2, 3, 4],
  "records": [
    {
      "page": 1,
      "component": "cover | sheet | form | reply | transmittal | letter | quotation | spec | calc | ...",
      "category": "drawings | submittals | correspondence | commercial | ...",
      "reference": "<the component's own identity for evaluation, exact literal>",
      "printed_revision": "<exact literal, or null>",
      "decision": "approved | ANN | rejected | UR | null",
      "decision_actor": "consultant | client | authority | contractor | null",
      "decision_target": "<the identity the decision is for>",
      "decision_evidence": "<where / how it is marked>",
      "identities": [
        {"literal": "...", "printed_label": "...", "role": "own_document | own_document_alternate | permit | request | reviewed_document | listed_item | referenced_document | project_or_contract | other", "own_for_evaluation": true}
      ],
      "states": {"identity": "clear | absent | unreadable | ambiguous", "revision": "...", "decision": "..."},
      "register": true,
      "confidence": "high | medium | low"
    }
  ],
  "no_record_pages": {"<page>": "<why: absent / out of scope / continuation sheet ...>"},
  "unvalidated_pages": ["<pages outside the reading scope>"],
  "unresolved": ["<what a human must decide on this document>"]
}
```

## What the states mean

| State | Meaning | Scored as |
|---|---|---|
| **clear** | The literal is legible and its role is settled | Scored |
| **absent** | The source genuinely carries no such fact on that page | A known negative |
| **unreadable** | The fact is present but cannot be read from the source | Excluded from denominators, reported |
| **ambiguous** | An unresolved fact or association | Excluded from denominators until a human decides it, and listed in `unresolved` |
| **out of scope** | Pages beyond the reading scope | Listed in `unvalidated_pages`, never scored |

**Identity roles.** Printed identifiers keep their role: own document, a listed or transmitted item, a reviewed document, a referenced drawing, a permit or request, a project or contract number. Two legible identifiers with clear roles are **not** ambiguous.

**BOQ rows.** Labels keep the literal part number and quantity, and the row type (item | heading | part_only | note | unreadable). A `( n )` count in the description is recorded **separately** from the quantity-column value.
