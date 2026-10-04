# The next extraction change: a revision literal accepted as an identity (design only, not implemented)

This task repairs evaluation. **The accepted application reader is not changed here**, and nothing below is implemented or tuned. The change becomes the first item of the next bounded task (AI accuracy improvement), to be done under a frozen contract with the `r14.1` labels.

## The confirmed defect

**Where.** EP-17428 `FA MS/Rev.01/1-7.pdf`, page 4 (profile B, EV1).

**What happened.** The divider header prints `Submittal No.:` followed only by `Rev.0`. The evidence reader's discovery returned `Rev.0` as the page's own identity, and the policy **validated** it. The accepted value's recorded target was `null`.

**The ruling.** The AI source review confirms a reader error (CRIT/2): `Rev.0` is a revision literal, and the page prints no identity. The same header yields a real revision observation (`Rev.0` → `0`), which must be kept as revision evidence with no target.

## The proposed rule (narrow)

**Refuse** to accept an identity when **both** of these hold:
1. The **whole** accepted value is a revision token: `^(REV|R)\.?\s*[0-9A-Z]{1,3}$` (case-insensitive), for example `Rev.0`, `REV 01`, `R1`.
2. The value was read from the region of a printed revision label, or from an identity field that prints nothing but that token.

When refused:
- the value is re-routed as a **revision observation** of the same page;
- its association stays held unless the page has a supported identity target;
- the raw token and its region are kept as provenance.

Refused means held, not deleted.

**Not banned** (explicit non-goals):
- identifiers that merely contain `Rev` or `R<digit>`;
- footer or control codes in general;
- project-number references;
- any identity whose literal also carries other characters.

## Controls for its tests (next task)

| Case | Expected |
|---|---|
| EP-17428 p4 `Rev.0` read as the identity (stored B output) | Refused as an identity; kept as a revision observation; no register credit |
| EP-17428 p1–p3 `Rev.0` read as the revision | Unchanged: supported revision literal, held, no target |
| **Positive:** `EP-23091 R1` (Qtn. Ref.) | Accepted as an identity, with the full literal kept; any split into the base number plus R1 is a declared normalization |
| **Positive:** `DCH-M-MHT-CAL-IFC-ELE-0001-00` | Accepted with its full literal; a trailing `-00` is **not** assumed to be a revision in general |
| **Positive:** `25H-S202-NCC-SD-MEP-ELE-FA-003-R3`, `EP-19977-R3`, `EP-19977-R4-BD` | Accepted identities containing revision text |
| **Positive:** `REQ-2387569-2`, `P06/TRANS/R1` | Not affected by this rule (the footer code stays a held role question, handled separately) |
| A title block whose revision cell reads `R1` next to a real drawing number | The drawing number is the identity; `R1` is the revision; nothing is refused |

**Other fixes** (page-1 identity discovery, the held footer role, association targets) use the corrected labels and a frozen contract. None uses a prompt tuned on the sealed cohort.
