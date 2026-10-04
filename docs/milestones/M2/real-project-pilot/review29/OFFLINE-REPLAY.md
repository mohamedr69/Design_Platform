# Offline replay of the four-arm outputs (diagnostic)

**Not fresh accuracy.** The corpus is the four-arm sample, which is already exposed. Labels r26.2 are frozen and unchanged. No model request was made. The replay changes no frozen output, label or score.

## Method

`scripts/replay_arm.py` re-executes one arm's evidence stage with the **final candidate `a8aaced`**:
1. **Sandbox:** a new copy of the frozen A base (`final-A`) in a throw-away sandbox.
2. **Configuration:** the arm's declared switch set plus one Review 29 configuration (off, IG, CA, DR, PA or ALL).
3. **Provider:** `ReplayProvider` answers only requests whose exact fingerprint was recorded in that arm's `io.jsonl`. The fingerprint covers the task, tier, prompt text and image hashes.
4. **Refusals:** a request the original run refused before dispatch is refused again, with the same reason. It is matched by document, task and page from the stored attempt log.
5. **Unrecorded requests:** any request that was never recorded fails as `unrecorded`. An answer is never invented.
6. **Wall clock:** the replay is not held to the real 120-second job limit. A slow replay machine therefore adds no refusals of its own, while the original time-budget refusals still come from the record.

`scripts/score_replay.py` scores rows in the evaluator's own tree, AI disabled:
- **.9** is the frozen experiment's evaluator and reader association code, in `frozen-r12`.
- **.10** is Review 29's per-fact association evaluator, in `cand-r29`.
- **Eligibility:** binds the attempt policy of that run.

`scripts/analyze_replays.py` compares each configuration with the **flags-off replay**, the old policy under identical replay conditions, under the same evaluator. `scripts/new_acceptances.py` lists every fact a configuration *newly validates*. `scripts/decision_absence.py` separates verified absences from wrong ones.

All 24 replays were run on `a8aaced` (`replay/logs/REPLAY-CANDIDATE-HEAD.txt`), with 0 model requests.

## 1. Flags-off fidelity: the replay reproduces the frozen runs

| Arm | Documents identical to the frozen stored rows | Frozen .9 facts reproduced |
|---|---|---|
| L1 | 27 / 27 | yes |
| L2 | 27 / 27 | yes |
| L3 | 25 / 27 | yes |
| L4 | 25 / 27 | yes |

The comparison covers attempts, page fields, requests, the call log and merged observations, ignoring wall-clock fields. The four remaining differences are the original runs' deadline effect. In those runs the job's time ran out, so a local OCR of a read region was skipped and the reason reads "no source text". The replay had time for the OCR. That changes only a reason string, and one support source on a read already stopped by the budget. No state or scored fact changes.

**Flags-off compatibility, shown three ways:**
- **Identities:** with all four switches off, the identity strings are those of `719e8de`, for both the accepted and the frozen arm identities.
- **Behaviour:** the replay above reproduces the frozen behaviour.
- **Source:** every unchanged file is byte-identical to `719e8de`.

## 2. No new false acceptance

`replay/NEW-ACCEPTANCES.json` lists every fact a configuration validates that the old policy did not validate with the same value. Across 4 arms, 5 configurations and 2 evaluators:

| | Count |
|---|---|
| **Newly validated wrong facts** (wrong, fp, accepted on conflict, wrong unassociated) | **0** |
| Newly validated correct facts | D04 identity `17` and D04 decision `ANN` (resolved), under CA and ALL in L3 and L4; D09 identity (resolved), under CA and ALL in L3 |

`analyze_replays.py` also reports newly *critical* facts under each evaluator. Under .10 there are none in any arm or configuration. Under .9 there is one: L1 with IG alone, D26 page 3 revision. It is not a new acceptance. The reader validated that footer revision in the old policy too, and .9 credited it only by inheriting page 1's record through the page-3 identity, which IG now holds. Under .10 it is a false positive in both policies, and under ALL, PA holds it, so there are 0 critical facts.

**Revision 0 of C2 failed this check.** C2 is frozen in `contracts/CONTRACT-FREEZE.json`. In an earlier replay it validated two truncations, D12 page 1 and D19 page 2, D19 being resolved. The text layer splits those long numbers, so the source text supported the truncated literal and counted as a second support. Revision 1 (`contracts/CONTRACT-FREEZE-R1.json`) requires two model readings, and the replays above use it. The regression is kept as a test (`test_split_text_regression_…`).

## 3. Critical acceptances, old against new policy (.10)

| Arm | Old (flags off) | ALL (combined) |
|---|---|---|
| L1 | D26 p3 revision (uncertain label; credited by .9 inheritance, a false positive under .10) | none |
| L2 | D26 p2 revision (uncertain) | none |
| L3 | none | none |
| L4 | D03 p1 identity "2.4 Accessories" (uncertain) | none |

## 4. What changed, by switch (.10; full lists in `replay/REPLAY-ANALYSIS.json`)

- **IG:** It holds D03's heading in L4 and D26's page-3 running-footer identity in L1. Nothing else changes in any arm.
- **CA (revision 1):** In L3 and L4, D04's identity resolves to "17" and is validated correct, and its ANN decision then becomes validated correct because its target is now established. In L3, D09's identity is validated correct. D06 and D12 stay held. Nothing changes in L1 or L2, which have no targeted read.
- **DR:** These replays cannot show DR's gains. Every new request is unrecorded: 5 to 6 `read_decision` and 4 to 14 `locate_decision` per arm. What they do show is the absence rule:

| Arm | Wrong decision absences, off → DR | Verified absences, off → DR |
|---|---|---|
| L1 | 1 (D16) → 0 | 9 → 4 |
| L2 | 0 → 0 | 9 → 2 |
| L3 | 1 (D18) → 0 | 16 → 9 |
| L4 | 0 → 0 | 8 → 2 |

  Fewer verified absences is the fail-closed cost of C3.6. In the ROI arms, decision reads that came from title-block discovery (C3.1) are no longer used, so L2's completed decision reads fall from 6 to 4. In a live run the locator would be called, so here they are unknown.

- **PA:** Dependent facts on a page with no identity established on that page become held without association, which earns no credit. The cost is real:

| Arm | Revision clean recovery under ALL against off (.10) | Held-correct revisions or decisions that become unassociated |
|---|---|---|
| L1 | 11 → 10 (D04 p1) | revisions of D15, D16 and D17; D04's decision |
| L2 | 14 → 12 (D04 p1, D26 p1) | revision of D22 p2; D04's decision |
| L3 | 13 → 13 | revisions of D15, D18 and D26 p1 (and D17's held-wrong revision) |
| L4 | 13 → 13 | D22 p2, D26 p1 |

  It removes the D26 page-2 false positive in L2.

## 5. Combined configuration (ALL) against flags off, evaluator .10

| Arm | Identity clean | Revision clean | Decision clean | Accepted precision, id / rev / dec | Critical |
|---|---|---|---|---|---|
| L1 | 14 → 14 | 11 → 10 | 0 → 0 | 14/14, 11/13 → 14/14, 10/11 | 1 → 0 |
| L2 | 20 → 20 | 14 → 12 | 1 → 1 | 20/20, 14/16, 1/1 → 20/20, 12/13, 1/1 | 1 → 0 |
| L3 | 19 → 20 | 13 → 13 | 1 → 2 | 19/19, 13/14, 1/1 → 20/20, 13/14, 2/2 | 0 → 0 |
| L4 | 23 → 24 | 13 → 13 | 1 → 2 | 23/24, 13/14, 1/1 → 24/24, 13/14, 2/2 | 1 → 0 |

The remaining wrong revision in every arm is D15's deterministic title-block reading, which is not an AI fact.

These are changes on an **exposed** corpus, so they are diagnostic only and are not evidence of general accuracy. The fresh test is in [FRESH-VALIDATION-PLAN.md](FRESH-VALIDATION-PLAN.md).

## 6. Evaluator .10 alone, on the frozen stored rows

| Arm | Facts whose .10 outcome differs from .9 |
|---|---|
| L1 | D26 p3 revision: validated "00", correct by inheritance → false positive (uncertain label) |
| L2 | none |
| L3 | none |
| L4 | D26 p2 revision: held "00", held correct by inheritance → held on a no-record page |

The frozen experiment's scores are unchanged. These rows describe the evaluator change only.
