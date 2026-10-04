# M2 Review 07: evaluator .5 / .6 (R7-01)

## What was wrong with .4 at the raw and evidence layers

The reviewer's findings are reproduced here as tests that must fail on `.4`:

- **A wrong validated AI identity was scored as a missed read.**
- **Validated facts on a labelled no-record page were not scored.**
- **A correct raw value masked a wrong AI revision or decision.**
- **Two identities on one page overwrote each other.** The result depended on their order.

## Evaluator .6

`scripts/m2_eval5.py`, `m2-pilot-eval-2026-09-29.6`.

- `.5` is the first version of this file. Its outputs are kept in `evidence/eval5_superseded/`.
- `.6` is a post-freeze amendment, committed as `1455f8b` before any matched-run result was read (see PROVENANCE-AND-FREEZE).
- `.4` (`scripts/m2_eval4.py`) is unchanged and still supplies the truth states, the expected records and the register layer.

The design follows.

1. **Facts, not pages.** Every emission unit is a *group* of facts. A unit is:
   - a register record;
   - a deterministic observation (title block, transmittal and each of its listed records, cover, drawing sheet, form fields, decision candidates);
   - an AI component reading.

   A fact is `{field, value, state}`, with its page, component key, reader and provenance. Nothing is merged or overwritten.
2. **States:**

   | State | Meaning |
   |---|---|
   | `accepted` | a register value (an automatic acceptance) |
   | `validated` | an AI value the validation policy accepted (an automatic acceptance) |
   | `observed` | a deterministic source observation: raw evidence, not an acceptance |
   | `held` | a flagged reference, an untrusted OCR number, an AI candidate or conflict, a decision candidate, or a record the application holds as pending evidence |

3. **Explicit association.** A group is associated with a truth component in this order:
   1. by an asserted identity on its page (exact or suffix);
   2. else as a **cross-page copy** of the document's own identity (also on a no-record page, as `.4` does);
   3. else, on a page with a single component, by that component. **An asserted identity that doesn't match it is `wrong`, never "missed".**
   4. else **`unassociated`**. The asserted identity is a wrong identity of no component (critical), and the group's other facts are `association_unknown`: counted, never scored right or wrong.

   On a labelled no-record page, anything asserted that isn't a cross-page copy is a false positive. Facts on unlabelled or unvalidated pages are counted as `unscored_page`.
4. **Two measures.**
   - **Accepted-output precision** is counted over *distinct* asserted facts: component, field and normalised value. A redundant identical copy counts once (`redundant`). Every distinct wrong value is an error, whatever else is correct. It is also broken down by state (`precision_by_state`).
   - **Deduplicated source-fact recovery** is counted per truth component and field:

     | Outcome | Meaning |
     |---|---|
     | `recovered_clean` | a correct value is asserted, and no wrong one |
     | `recovered_mixed` | correct and wrong values are both asserted; the wrong one is also a precision error |
     | `wrong_only` | only wrong values are asserted |
     | `held_only` | a correct value exists only as held evidence (evidence credit, not acceptance credit) |
     | `missed` | nothing correct was read |
     | `tn` / `fp` | on negative truth |
     | `accepted_on_conflict` / `conflict_held` / `conflict_missing` | on conflict truth |

5. **Critical versus observed errors.**
   - `critical` counts wrong **automatic acceptances** only: `accepted` or `validated` facts that are `wrong`, `fp`, `wrong_unassociated` or `accepted_on_conflict`.
   - A wrong deterministic **observation** is listed separately in `observed_errors`. It is never hidden and never called an acceptance.
   - `introduced_ai_errors` lists every asserted AI fact that is wrong. This replaces `.4`'s "introduced only where the raw verdict was clean".
6. **Register view.** A record the application holds as pending evidence (the review 07 guard, `extracted.pending_evidence`) is no register emission and holds all its facts in the raw layer. Rows read before the guard carry no such list and are scored as they were.
7. **AI envelope.** Only the **current, non-stale** AI envelope is scored: the review 07 lifecycle shape, or the review 06 flat shape. Stale evidence (changed bytes or profile) is not current.
8. **Order does not matter.** Every permutation gives the same result (tested).

## Tests: `tests/test_m2_eval5.py`, 13 tests

| # | Test | What it shows |
|---|---|---|
| 1–4 | The reviewer's four evaluator probes | Each asserts that `.4` hides the defect and `.5`/`.6` counts it: the wrong identity, the no-record-page facts, the masking, and the order-dependent overwrite |
| 5 | Permutation invariance | over mixed layers |
| 6 | Redundant copies | inflate neither recovery nor precision |
| 7 | Several components on a page | unknown association stays explicit (`wrong_unassociated` identity, `association_unknown` decision) |
| 8 | Held facts | earn evidence credit only |
| 9 | A known wrong identity on a single-component page | is wrong, and judges the group's other facts |
| 10 | Conflict truth and unscored pages | — |
| 11 | Stale retained AI evidence | is not scored as current |
| 12 | A pending-evidence record | is no register emission, and is held raw evidence |
| 13 | A cross-page copy on a no-record page | associates, while an invented identity there is a false positive |

## Re-scores of every stored output under .6

Nothing is overwritten. Outputs are in `evidence/eval6/*.json`, with `.5` in `eval5_superseded/`.

Recovery and precision are shown for the raw layer, then the evidence layer (raw plus AI). Recovery counts clean plus mixed recoveries of readable facts; precision is over distinct accepted and observed facts.

The **real-model** rows are exposed exploration data on the eligible projects (EV1 is partial outside EP-29076). The `replay` rows re-validate the stored real-model readings under policy `.2`, with no new calls (VALIDATOR-AND-LIFECYCLE).

| Run | Register critical | Accepted critical: raw / evidence / AI | Wrong raw observations | AI-introduced | Identity rec / prec, raw → evidence | Revision rec / prec, raw → evidence | Decision rec / prec, raw → evidence |
|---|---|---|---|---|---|---|---|
| r5-candidateA-default | 33 | 30 / 30 / 0 | 9 | 0 | 0.344 / 0.801 → 0.344 / 0.801 | 0.197 / 0.884 → 0.197 / 0.884 | 0.312 / 1.000 → 0.312 / 1.000 |
| r5-candidateB-default | 35 | 31 / 31 / 0 | 9 | 0 | 0.399 / 0.838 → 0.399 / 0.838 | 0.232 / 0.857 → 0.232 / 0.857 | 0.312 / 1.000 → 0.312 / 1.000 |
| r5-candC0-default | 13 | 11 / 11 / 0 | 20 | 0 | 0.598 / 0.897 → 0.598 / 0.897 | 0.626 / 0.970 → 0.626 / 0.970 | 0.325 / 1.000 → 0.325 / 1.000 |
| r5-candC1-default | 3 | 1 / 1 / 0 | 9 | 0 | 0.609 / 0.957 → 0.609 / 0.957 | 0.652 / 1.000 → 0.652 / 1.000 | 0.325 / 1.000 → 0.325 / 1.000 |
| r5-candidateC-default | 2 | 0 / 0 / 0 | 9 | 0 | 0.614 / 0.961 → 0.614 / 0.961 | 0.655 / 1.000 → 0.655 / 1.000 | 0.325 / 1.000 → 0.325 / 1.000 |
| r6-det7-pilot-default | 5 | 3 / 3 / 0 | 37 | 0 | 0.680 / 0.876 → 0.680 / 0.876 | 0.716 / 0.991 → 0.716 / 0.991 | 0.325 / 1.000 → 0.325 / 1.000 |
| r6-det8-pilot-default | 2 | 0 / 0 / 0 | 21 | 0 | 0.672 / 0.928 → 0.672 / 0.928 | 0.716 / 0.991 → 0.716 / 0.991 | 0.325 / 1.000 → 0.325 / 1.000 |
| r7-det9-pilot-default | 0 | 0 / 0 / 0 | 21 | 0 | 0.672 / 0.928 → 0.672 / 0.928 | 0.710 / 0.991 → 0.710 / 0.991 | 0.325 / 1.000 → 0.325 / 1.000 |
| r5-candidateC-promoted | 2 | 0 / 0 / 0 | 9 | 0 | 0.614 / 0.961 → 0.614 / 0.961 | 0.655 / 1.000 → 0.655 / 1.000 | 0.362 / 1.000 → 0.362 / 1.000 |
| r6-det8-pilot-promoted | 2 | 0 / 0 / 0 | 21 | 0 | 0.672 / 0.928 → 0.672 / 0.928 | 0.716 / 0.991 → 0.716 / 0.991 | 0.362 / 1.000 → 0.362 / 1.000 |
| r7-det9-pilot-promoted | 0 | 0 / 0 / 0 | 21 | 0 | 0.672 / 0.928 → 0.672 / 0.928 | 0.710 / 0.991 → 0.710 / 0.991 | 0.362 / 1.000 → 0.362 / 1.000 |
| r5-holdout-default | 0 | 0 / 0 / 0 | 0 | 0 | 0.150 / 1.000 → 0.150 / 1.000 | 0.000 / n/a → 0.000 / n/a | 0.000 / n/a → 0.000 / n/a |
| r6-det7-holdout-default | 0 | 0 / 0 / 0 | 2 | 0 | 0.700 / 0.875 → 0.700 / 0.875 | 0.538 / 1.000 → 0.538 / 1.000 | 0.000 / n/a → 0.000 / n/a |
| r6-det8-holdout-default | 0 | 0 / 0 / 0 | 2 | 0 | 0.700 / 0.875 → 0.700 / 0.875 | 0.538 / 1.000 → 0.538 / 1.000 | 0.000 / n/a → 0.000 / n/a |
| r7-det9-holdout-default | 0 | 0 / 0 / 0 | 2 | 0 | 0.700 / 0.875 → 0.700 / 0.875 | 0.538 / 1.000 → 0.538 / 1.000 | 0.000 / n/a → 0.000 / n/a |
| r7-det9-holdout-promoted | 0 | 0 / 0 / 0 | 2 | 0 | 0.700 / 0.875 → 0.700 / 0.875 | 0.538 / 1.000 → 0.538 / 1.000 | 0.000 / n/a → 0.000 / n/a |
| r6-det7-eligible-default | 3 | 3 / 3 / 0 | 18 | 0 | 0.662 / 0.847 → 0.662 / 0.847 | 0.742 / 0.989 → 0.742 / 0.989 | 0.581 / 1.000 → 0.581 / 1.000 |
| r6-ai-ev0-eligible-default | 4 | 4 / 4 / 0 | 18 | 0 | 0.662 / 0.839 → 0.662 / 0.839 | 0.742 / 0.989 → 0.742 / 0.989 | 0.605 / 1.000 → 0.605 / 1.000 |
| r6-ai-ev1-eligible-default | 4 | 4 / 6 / 2 | 18 | 2 | 0.662 / 0.839 → 0.711 / 0.842 | 0.742 / 0.989 → 0.792 / 0.990 | 0.605 / 1.000 → 0.744 / 0.970 |
| r7-replay-ev1-eligible | 4 | 4 / 5 / 1 | 18 | 1 | 0.662 / 0.839 → 0.697 / 0.839 | 0.742 / 0.989 → 0.758 / 0.989 | 0.605 / 1.000 → 0.744 / 1.000 |
| r6-ai-ev0-ep29076-default | 4 | 4 / 4 / 0 | 15 | 0 | 0.566 / 0.652 → 0.566 / 0.652 | 0.604 / 1.000 → 0.604 / 1.000 | 0.125 / 1.000 → 0.125 / 1.000 |
| r6-ai-ev1-ep29076-default | 4 | 4 / 5 / 1 | 15 | 1 | 0.566 / 0.652 → 0.623 / 0.673 | 0.604 / 1.000 → 0.729 / 1.000 | 0.125 / 1.000 → 0.750 / 0.857 |
| r6-ai-ev2-ep29076-default | 4 | 4 / 5 / 1 | 15 | 1 | 0.566 / 0.652 → 0.604 / 0.667 | 0.604 / 1.000 → 0.688 / 1.000 | 0.125 / 1.000 → 0.375 / 0.750 |
| r7-replay-ev1-ep29076 | 4 | 4 / 4 / 0 | 15 | 0 | 0.566 / 0.652 → 0.604 / 0.667 | 0.604 / 1.000 → 0.625 / 1.000 | 0.125 / 1.000 → 0.750 / 1.000 |
| r7-replay-ev2-ep29076 | 4 | 4 / 4 / 0 | 15 | 0 | 0.566 / 0.652 → 0.604 / 0.667 | 0.604 / 1.000 → 0.604 / 1.000 | 0.125 / 1.000 → 0.375 / 1.000 |

### How to read the changes

- **Register layer.** `det9`, the final candidate with the incomplete-reference guard, has **0 register critical in both profiles.** Candidate C and `.8` had 2: the flagged `A23-EFECO-MAT-E` and `V-EL-MTG-PJW-ZZZ`. The cost is two correct revisions, which no longer reach the register (revision 107 → 105 default).
- **Wrong deterministic observations** are new visibility, not new behaviour:
  - Candidate C: 9;
  - `.8` and `.9`: 21, the added observation shapes (labelled form fields, OCR title blocks) plus the pre-existing drawing-sheet observations;
  - holdout: 2.

  All were adjudicated against the source (ADJUDICATIONS.md). Many are label disputes or label gaps; the rest are real raw-observation errors, which are held evidence and never register keys.
- **AI.** Review 06 said "zero introduced errors", and that statement is **withdrawn**. Under `.6` the stored AI-EV1 run has 2 introduced errors across the eligible projects, and AI-EV2 has 1 on EP-29076. Both were adjudicated against the source:
  - the building permit prints its permit number `B2312982` as well as the request reference `REQ-2387569` used by the label (two own identities);
  - page 3 of `FA-003-R03 - Code B` carries a signed consultant "CODE B APPROVED AS NOTED" stamp that the label says is not there.

  Both are **disputed truth, not confirmed AI false acceptances**, and both are in the human-review packet. Under the policy `.2` replay:
  - EP-29076 has 0 introduced errors for both variants;
  - the eligible set has 1, the permit case, which is still validated because the permit number is printed in the read region;
  - policy `.2` holds the Code B stamp as a candidate (discovery did not corroborate the mark).

  No AI error count is asserted as final until the human review settles these labels.
