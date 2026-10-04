# M2 Review 09: the evidence contract (read usability, association, source identity, item presence)

This is the contract implemented by:
- `evidence-reader-2026-09-29.4` and `evidence-policy-2026-09-29.4` (`backend/app/ai/evidence_reader.py`);
- evaluator `m2-pilot-eval-2026-09-29.8` (`backend/scripts/m2_eval5.py`);
- candidate `689d95e`.

Review 08's field-level lifecycle and context selection are unchanged, except where stated below.

## 1. A returned response is not a usable read (R9-01)

**Two outcomes are recorded for every required read.**
- **The request** (`coverage.pages[].requests`): `ok`, `failed:<kind>`, `budget` or `not_attempted`.
- **The field** (`coverage.pages[].fields`):

| Field outcome | When | Supersedes last-good evidence? |
|---|---|---|
| `completed` | **Identity or revision:** a legible blind reading that carries a value (the small read, or an EV2 escalation). **Decision block:** a legible blind reading. | **Yes.** This includes a completed, legible negative (a legible block with nothing marked, read that way both times) and a completed reading that conflicts, which stays an explicit `conflict`. A completed read that came back only `unreadable` supersedes nothing (Review 08). |
| `unusable:illegible` | The request returned, but the blind answer is `legible=false`. | No |
| `unusable:empty` | The request returned a legible answer with no value, for an identity or a revision. There is no verified absence of an identity or a revision. | No |
| `absent_by_discovery`, `incomplete:no_region`, `failed:<kind>`, `budget`, `not_attempted` | As in Review 08 | No |

**The discovery reading never completes a field on its own.**
- **What discovery alone yields.** Its value can only be a `candidate`, never a verified value.
- **Negatives.** A negative from discovery alone (`no_decision_marked`, `not_a_decision`) whose blind read was not usable is recorded as `unverified`, never as a verified absence.
- **An unusable read of a field that already has evidence changes nothing current.** The field keeps its last-good evidence, with its original provenance and target. The unusable reading is kept with the attempt, in `attempts[].unapplied`: field, value, state, read outcome and target.
- **An unusable read of a field with no evidence yet** is stored as `incomplete`. It is listed in `evidence_for(...)["incomplete"]` and never counted as verified.
- **A later usable read replaces it** under the Review 08 rule, and the replaced evidence moves to the field's history.

**Page outcome.** A page is `evidence` only when every required read is `completed` or `absent_by_discovery`. An unusable read makes the page `partial`.

## 2. A retained fact keeps its association (R9-02)

**What each dependent fact records.** A dependent fact of the page's own component is a revision or a decision.
- **Decision:** `target`, the identity it was validated against (the component's own identity read in the same attempt, or the deterministic identity), and `target_revision`, the revision read in the same attempt when that read completed.
- **Revision:** `target`, the component identity it was read for. Review 06 evidence recorded no targets, and Review 07/08 revisions recorded none either.

**`evidence_for` labels each such fact with its `association`** against the component as it is read now. The current identity and revision are the field's value when that field is `completed` (or `legacy`) and carries a value.

| `association.status` | When | Evaluator .8 |
|---|---|---|
| `current` | The target is the component's current identity, and for a decision the revision, when both are known, is the same. | Judged with its component, as before |
| `held:target_changed` | The component now reads another identity. | Its own group, associated **only by its target**, state `held`. It is never accepted or recovered for the new identity, and it stays visible (`held_correct`, `held_wrong` or `held_unassociated`). |
| `held:revision_changed` | A decision read with a known revision the component no longer carries. | As above |
| `by_target` | There is no usable current identity on the component. | Its own group, associated only by its target, keeping its state. It is never associated with the page's other component. |
| `not_recorded` | The fact never recorded a target. | Grouped as before. No target is invented. |

- **Stored facts are never rewritten.** The association is computed at selection; the stored observation and its provenance are unchanged.
- **Judgements carry the metadata.** Evaluator .8 carries `target` and `association` into every judgement of the fact, on scored and unscored pages alike.
- **A target that matches nothing** gives `association_unknown` (asserted) or `held_unassociated` (held), both visible in the judged list.
- **Referenced identities** (`refN` components) stay references. They never anchor an own-component association.

## 3. Unknown bytes are not exact-file evidence (R9-03)

`evidence_for(ai, sha256=, profile=, variant=, policies=, accept_unknown_profile=, historical_source=)` decides source identity **per field**, by the `read_sha256` in the field's own provenance:

| State | Meaning |
|---|---|
| `current` | Fields read from exactly the requested bytes. `withheld` lists the fields of the same envelope that are not: `unknown_source` or `stale`. |
| `stale` | The envelope, or all of its fields, was read from other bytes. |
| `unknown_source` | The evidence records no source hash. It is not exact-file evidence, and it is not returned as current. |
| `source_required` | The request names no source hash. |
| `pending`, `unavailable` | As in Review 08 |

- **The legacy-profile declaration says nothing about bytes.** `accept_unknown_profile` still only allows an unknown legacy **profile**. Flat evidence without `read_sha256` is `unknown_source` even when that profile is declared.
- **Retained fields are never relabelled.** A partial or failed later attempt adds its own fields with its own hash; each field keeps its own source. For an envelope that recorded no hash, the envelope-level `read_sha256` becomes the bytes it was last read from. Selection still goes by each field's own provenance.
- **Historical compatibility is a separate, explicit mode.** `historical_source={"manifest": <run manifest>, "sha256": <the hash it binds this document to>}` lets fields with **no** recorded hash count as read from the manifest's bytes, and only when those are the requested bytes. A known mismatch never counts. The result is `mode: "historical"`, and each such observation carries `source_binding: "historical:<manifest>"`.
  - Operational callers never pass it; `evidence_stage` and the API do not.
  - Evaluator .8 passes it only from a declared `ai_context.historical_source` `{manifest, sha256_by_doc}`.
  - **No stored run needed it.** Every stored AI envelope records the hash of the bytes it read, and it matches.

## 4. A heading is confirmed only without item evidence (R9-04)

- **What the validator receives.** The normal verifier (`verify_boq_rows`) passes the reader's part, quantity **and description** to `validate_boq_row`, as read and without rewriting.
- **Item evidence against a heading answer is any of:**
  - a part, on either side;
  - a **present** quantity, on either side;
  - a `( n )` count in either description, the reader's included.
- **Presence is explicit** (`quantity_present`). Numeric `0` and `"0"` are present; only `None` and blank text are absent. The same rule now applies in the item comparison, so a blind `0` is a quantity, not an absence.

| Heading answer | Outcome |
|---|---|
| Illegible | `unverified` |
| With any item evidence | `conflict`, `row_type: disputed` (held), with every piece of evidence named in the reason |
| Neither side has item evidence | `not_an_item`, `row_type: heading_confirmed` |

- **The literals are kept.** The verdict includes the reader's literals (`reader`) and the blind literals (`blind`). No line is removed, and no catalogue number or quantity is inferred.
- **Limit.** A description count is used as item evidence against a heading answer, and, as since Review 07, as the blind reading's own quantity. It is not used as the reader's quantity in the item comparison. That would be a new parsing rule, outside this correction.

## 5. Ledger (R8-03, accepted): wording only

The module documentation now states the behaviour as it is (`ai-ledger-2026-09-29.2`, unchanged):
- **After an amendment, a handle that is already open** reads the saved, amended policy at its next reservation or settlement.
- **A handle opened afterwards** that explicitly supplies the old, now conflicting limits is refused (`LedgerConfigMismatch`).

No claim is made that the Review 07 run of 120 requests overspent.
