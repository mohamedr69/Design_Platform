# M2 Review 06: evaluator corrections (R6-01 to R6-04) and BOQ evaluator .3

## Versions and freeze

| Evaluator | Version | Status |
|---|---|---|
| Document evaluator .3 | `scripts/m2_pilot_eval.py` | Unchanged. Kept as history and reused for its literal and identity helpers only. |
| **Document evaluator .4** | `m2-pilot-eval-2026-09-29.4`, `scripts/m2_eval4.py` | New. |
| **BOQ evaluator .3** | `m2-boq-eval-2026-09-29.3`, `scripts/m2_boq_eval.py` | Adds absence and unscorable truth states. |

Both were frozen before any AI-variant run: `evidence/FREEZE-evaluators.json`, frozen 2026-09-28T23:21:30, holds the SHA-256 of both evaluators, their tests and the reused .3 module. Nothing was changed after the AI or real-model results were seen.

## Field-accounting rules (evaluator .4)

These rules are frozen with `tests/test_m2_eval4.py`.

1. **Denominators come from truth alone.** Each field is `readable`, `negative`, `conflict` or `unscorable`, decided from the labels. A document that has no execution row, or a failed or partial one, keeps its readable fields in the recovery denominator. Its outcome is reported under `execution` as `not_run`, `failed`, `partial` or `complete` (R6-03).
2. **Every emitted record is associated and judged** (R6-01). Association tries these in order:
   - same page and same identity;
   - otherwise, the page has exactly one expected component (the association is clear even with unknown identity);
   - otherwise, the same identity on another page (a cross-page copy).

   For each field, all accepted values are pooled. Any wrong accepted value makes the field `wrong`, and critical, even beside a correct one. A correct value earns recovery once. Results do not depend on record order. Exact redundant copies are counted as `redundant_copies`; differing copies as `conflicting_emission_sets`.
3. **Conflict truth** (R6-02):
   - An accepted decision on conflict truth is `accepted_on_conflict`: accepted, wrong and critical.
   - A held conflict is `conflict_held`; a bare UR is `conflict_missing`.
   - A revision projected without the `revision_conflict` flag where the REV cell and the revision history disagree is `conflict_resolved_silently`, which is critical.
4. **Explicit absence labels.**
   - Decisions: `UR`, `n/a`, `absent`, `none`, `no decision`, `not applicable` and `na` all mean no consultant decision. An accepted decision on one of them is a false positive.
   - Revisions: `absent`, `n/a` and `not applicable` are negatives, and stay negative when the whole record is missing (R6-03).
5. **Flagged references.** A reference the reader flags as incomplete or uncertain is still the register key, so it counts as accepted at the register layer. The flag is reported separately as `flagged_reference`. Evaluator .3 counted such references as held.
6. **Four layers, kept apart** (R6-04):
   - **register**: emitted records;
   - **raw**: records plus every observation shape, through `adapt_observation`: `title_block.number` and `revision`, the transmittal's own number and its records, `cover_untracked`, `drawing_sheet`, `decision_unpromoted`, `consultant_comments`, `form_identity`, and the evidence and own-identity shapes;
   - **projection**: the business revision;
   - **evidence**: raw plus the AI reader's `ai_evidence`.

   In the evidence layer, `validated` counts as accepted evidence; it is wrong or critical like any other value. `candidate` and `conflict` count as held. Errors the model introduced are listed in `evidence_introduced_errors`. A register-ineligible truth record is never counted as missing from the register.

## Tests: `tests/test_m2_eval4.py`, 14 tests

Each test is paired with the evaluator .3 behaviour that it fails on.

| # | Case | .4 result | .3 result on the same input |
|---|---|---|---|
| 1 | A conflicting duplicate before or after a correct record, in either order | decision and revision `wrong`, 2 critical, 1 conflicting set | 0 critical, 100% precision |
| 2 | A redundant exact copy | tp 1, readable 1, no critical, 1 redundant copy | — |
| 3 | A wrong copy on another page | associated across pages, `decision: wrong` | ignored |
| 4 | An approval on conflict truth | `accepted_on_conflict`, critical | `conflict_missing`, not accepted |
| 5 | A silently resolved revision conflict | `conflict_resolved_silently`, critical | not scored |
| 6 | The other component on the same page | judged against its own truth | — |
| 7 | Not-run, failed and partial documents | denominators kept, outcome reported | the document dropped out |
| 8 | An absent revision on a missing record | `tn`, not `missed` | `missed` |
| 9 | Decision-absence labels | `fp` on an accepted decision | `unscorable` |
| 10 | Unknown identity, one component on the page | the decision error is found | the page is `unvalidated` |
| 11 | Ambiguous association (several components) | stays `unscorable` | — |
| 12 | Title-block and transmittal observations | identity tp 2, revision `wrong` 1 | tp 1, missed 1, no revision judged |
| 13 | Flagged references | accepted at the register layer, `flagged_reference` shown | held |
| 14 | `ai_evidence` states | validated counts, candidate is held, introduced errors listed | — |

`tests/test_m2_boq_eval3.py` has 3 tests covering BOQ absence and unscorable truth.

### The reviewer's six probes, re-run against .4

Source: `independent_checks.py`. Output: `evidence/reviewer_probes_eval4.txt`.

| Probe | Reviewer's expectation | .4 |
|---|---|---|
| conflicting_duplicate | the wrong approved decision and R9 are counted | `revision: wrong` and `decision: wrong` are critical |
| accepted_approval_on_conflict | a critical false acceptance | `decision: accepted_on_conflict` is critical |
| missing_execution_row | readable fields kept | reference, revision and decision each `missed` 1 of `readable` 1; execution `not_run` |
| known_decision_unknown_reference | the decision error remains | `decision: wrong` is critical; reference `unscorable` |
| absent_decision | fp, or an explicit contract | `decision_truth('absent')` is `negative`; with an approval it is `decision: fp`, critical |
| absent_revision_missing_record | not a readable missed revision | revision `tn` |

## Re-scores of every stored output

The prior reports are not overwritten. Outputs are in `evidence/eval4/*.json`. The .3 figures come from Review 05 `eval/`.

Cells show tp / accepted / readable.

| Run | Profile | Critical .3 | **Critical .4** | .4 critical kinds | Reference .4 (.3) | Revision .4 (.3) | Decision .4 (.3) | Execution |
|---|---|---|---|---|---|---|---|---|
| Candidate A | default | 31 | **33** | reference wrong 25, revision wrong 8 | 94/119/156 (94/117/156) | 57/65/134 (57/65/142) | 25/25/70 (25/25/70) | complete 343, bounded 36, failed 1 |
| Candidate A | promoted | 31 | **33** | same | 101/126/158 (101/124/158) | 61/69/136 (61/69/141) | 28/28/72 (28/28/72) | same |
| Candidate B | default | 30 | **35** | reference wrong 21, revision wrong 10, reference fp 2, revision fp 2 | 114/137/160 (114/134/160) | 68/80/138 (68/78/144) | 25/25/71 | same |
| Candidate B | promoted | 30 | **35** | same | 121/144/162 (121/141/162) | 72/84/140 (72/82/143) | 28/28/73 | same |
| C0 | default | 9 | **13** | revision wrong 4, reference wrong 5, reference fp 2, revision fp 2 | 125/132/162 (125/130/162) | 97/103/140 (97/101/147) | 26/26/71 | same |
| C0 | promoted | 9 | **13** | same | 132/139/164 | 101/107/142 | 29/29/73 | same |
| C1 | default | 1 | **3** | reference wrong 3 | 135/138/164 | 103/103/142 (103/103/149) | 26/26/71 | same |
| C1 | promoted | 1 | **3** | same | 142/145/166 | 107/107/144 | 29/29/73 | same |
| **Candidate C** | default | **0** | **2** | reference wrong 2 | 137/139/164 (137/137/164) | 104/104/142 (104/104/149) | 26/26/71 | same |
| **Candidate C** | promoted | **0** | **2** | same | 144/146/166 | 108/108/144 | 29/29/73 | same |
| R5 holdout | both | 0 | 0 | — | 0/0/5 (0/0/9) | 0/0/5 (0/0/9) | 0/0/0 | complete 26, bounded 2 |

**The Candidate C zero-critical figure is no longer cited.** Under .4, Candidate C has **2 critical errors in each profile**. Both are references that the reader flagged but that the register files under the cut key:
- `A23-EFECO-MAT-E` on A23 page 4;
- `V-EL-MTG-PJW-ZZZ` on MTG-1020 page 1.

Revision readable denominators fell, for example Candidate C default 149 → 142. That is because absent revisions on missing records are now negatives. The holdout register readable count fell from 9 to 5, because the labels mark the Word material transmittals `register: false`.

Candidate C raw layer under .4 (default profile):

| Field | Recovered / readable |
|---|---|
| identity | 223 / 363 |
| revision | 185 / 310 |
| decision | 29 / 80 |

These are the first complete raw-layer figures.

## BOQ evaluator .3: same classes of mistake, checked on the BOQ path

- **Duplicates.** BOQ pairing is already one-to-one per labelled row. An extra emitted row is `extra held` or `extra accepted`, never merged into a correct one. No change was needed.
- **Absence truth.** A truth literal of `-`, `n/a`, `absent`, `none` or `not applicable` is now a negative. An accepted value on it is `fp`; before, it was `wrong`. Unscorable words (`?`, `illegible`, `unknown`, `unclear`) are now `unscorable`; before, they were `missed`. A missing truth row counts as missed, tn or unscorable, by its state.
- **Effect.**

  | Set | Critical .2 → .3 | Part / quantity figures (.2 → .3) |
  |---|---|---|
  | Baseline | 55 → 55 | quantity 30 wrong → 15 wrong + 15 fp; part tn 15 → 49; part missed 247 → 232 |
  | After corrections (labels v2) | 5 → 5 | part tn 18 → 52; quantity tn 0 → 15 |
  | Holdout | 4 → 4 | part tn 8 → 13 |

  No critical count changed; the classification is now correct.
