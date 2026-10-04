# M2 source-review packet: for the human reviewer

**Status: prepared, not reviewed.** No item in this packet has been checked by a person yet. Nothing here is a human signature.

## Who reviews

The reviewer is the owner, or a person the owner appoints. Their name goes in `human_reviewer` on every row they settle.

The labels offered here were drafted by an AI model in earlier rounds. The acceptance policy does not allow a model to be the owner of Golden truth, so an AI draft is never taken as a human answer.

## What you are shown and what you are not

| Item | What it is |
|---|---|
| `pages/*.jpg` | Each page rendered at 110 dpi directly from the staged copy of the original file. |
| `proposed_*` columns | The current Golden label, AI-drafted, for you to confirm or correct. |
| Not shown | Any prediction by the platform's reader or by the AI verifier. You label the source, not a prediction. |

Source hashes are in `PACKET-MANIFEST.json` under `source_sha256`. A Word transmittal, or a file that would not render, says "open the original": use the file itself.

## What to review (the agreed scope)

`COMPONENT-ITEMS.csv` has 339 items, out of 555 labelled components:

| Scope | Items | Covers |
|---|---|---|
| **decision label** | 212 | every component with a consultant or client decision, or on a form, reply, review or transmittal |
| **critical disagreement / adjudicated case** | 87 | every page where a platform reading and the label disagree critically, including the adjudicated cases in `../ADJUDICATIONS.md` |
| **ambiguous or low-confidence label** | 71 | labels marked medium or low confidence, or unknown, illegible or ambiguous |
| **frozen 20% sample** | 54 | of the remaining components, seeded `m2-review07-packet-2026-09-29` |

`BOQ-ITEMS.csv` has 194 items, out of 933 labelled BOQ rows:

| Scope | Items |
|---|---|
| critical disagreement | 29 |
| ambiguous part or row | 6 |
| frozen 20% sample of the other equipment rows | 159 |

An item can carry several scopes.

## How to fill a row

1. Read the page, or the file, yourself. Write what the source shows in the `human_*` columns:
   - the page's **own** identity, exactly as printed;
   - its **printed** revision;
   - the consultant or client **decision** (only if marked) and **who** marked it;
   - for a BOQ row, the part number exactly as printed (every `+`, `/`, `-`) and the quantity with its decimal point, sign or unit.
2. Record what is not a clear value:
   - `absent`: the source has no such fact;
   - `illegible`;
   - `ambiguous`: two or more own identities, or an unclear mark;
   - `conflict`: the source contradicts itself.

   Do not guess. `human_uncertainty` takes a short reason.
3. A page that prints **two** identities that are both its own (for example a consultant's and a contractor's transmittal number, or a permit number beside a request reference) is written as both, separated by ` | `, and marked `ambiguous`.
4. Add your name and the date.

## What happens with your answers

- Settled rows replace the AI-drafted labels in a new, versioned label set (labels v3). The earlier sets stay as history.
- A row left blank or marked ambiguous stays **unresolved truth**. It is kept out of acceptance denominators and reported as a coverage gap. It is never counted as a platform success or failure.
- A second person is not required for this scope. If one reviews, their disagreements are kept in `human_notes` and resolved together.
