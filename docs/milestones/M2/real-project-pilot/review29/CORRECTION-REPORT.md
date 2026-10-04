# Review 29 correction: a bounded offline accuracy candidate

**Candidate.** The candidate is `C:/t/iso/cand-r29`, commit **`a8aaced`**, parent `719e8de`. It is isolated, and it contains no model call, live run, production change, migration or label change.

**Frozen evidence.** `four-arm-final/` is preserved byte for byte, and the package check re-verifies its manifest and every file in it.

## What was built

There are four changes, each behind its own switch and identity. None implies another, and CA, DR and PA refuse to start without the required-first scheduling set explicitly. With all four off, the identities and behaviour are those of `719e8de`. Contracts: [CONTRACTS.md](CONTRACTS.md). Files and functions: [CHANGE-MAP.md](CHANGE-MAP.md).

| Defect (four-arm) | Switch | Change |
|---|---|---|
| D03: a section heading was validated as identity, in L4 by a targeted read | IG | Headings, clause titles, page counters, generic labels, revision tokens, running headers and footers on non-drawing pages, and values with a reference role are held, with their region and readings. Only two own-labelled, source-bound readings lift a class. A model's role claim never does. |
| D04, D06, D12: a correct later read was held behind a wrong first value | CA | A written evidence-ordering contract. A literal wins only with two agreeing model readings, an own-role label, source binding and every competitor disqualified by a role contradiction or by not being printed. Order, recency, labels and length are never used. |
| D16 to D18: decision stamps outside the title block were absent or unread | DR | A bounded decision-region path: discovery's decision signal, decision vocabulary in the text layer, or one whole-page locator, with at most 3 reads per page. Acceptance needs two agreeing readings, a printed legend, a consultant or client actor and the page's own target. A crop that missed a possible region is **unknown, never absent**. |
| D26: the same observation alternated between no-record, false positive and held correct | PA, plus evaluator .10 | A dependent fact binds only to an identity established on its own page, and without one it is held with no target. Evaluator `.10` (`m2_eval6`) decides association per fact, so dependent facts never cross pages. Evaluator `.9` is unchanged. |

**Two contract revisions, both frozen before their code change and both reported.**
- **C2 revision 1:** the offline replay showed that the first E4 validated split-text truncations, D12 and D19 (D19 resolved). Two model readings are now required.
- **C1 revision 2:** in the combined configuration, guarding a conflict's provisional value suppressed the targeted read that CA needs. The guard now applies to the final single-literal verdict only.

## Results (all offline)

| Check | Result |
|---|---|
| Reproduction before implementation | All four defects reproduced from the frozen stored outputs ([repro/](repro/STORED-EVIDENCE-DUMP.txt)). D06 was confirmed as a design risk: two own-labelled numbering systems that evidence cannot rank. |
| Review 29 tests (92) | pass |
| Focused suites: extraction, BOQ, AI evidence, processing jobs, M2 reviews, R29 (662 tests) | 652 passed, 10 skipped, 0 failed on `a8aaced` |
| Full backend suite on `a8aaced` | 2 failed, 1,824 passed, 35 skipped. Both failures are long-known and are compared with the accepted baseline in [TESTS-AND-REGRESSIONS.md](TESTS-AND-REGRESSIONS.md). |
| Flags-off fidelity, 4 arms × 27 documents | L1 and L2 identical; L3 and L4 25 of 27, the difference being original-run OCR timing only; frozen .9 facts reproduced in every arm |
| Newly validated wrong facts, 4 arms × 5 configurations × 2 evaluators | **0** |
| Critical acceptances, combined configuration against flags off (.10) | L1 1 → 0, L2 1 → 0, L4 1 → 0 |
| Wrong decision absences with DR | 2 → 0 |
| Correct newly validated facts | D04 identity and decision (resolved), D09 identity (resolved), exposed corpus only |
| Costs | PA holds some correct revisions on pages without an established identity, so revision clean recovery falls by 1 to 2 in L1 and L2. DR lowers verified absences, which is fail-closed. DR's decision gains cannot be measured offline because its reads were never recorded. |

Details: [OFFLINE-REPLAY.md](OFFLINE-REPLAY.md) and [TESTS-AND-REGRESSIONS.md](TESTS-AND-REGRESSIONS.md).

## Acceptance criteria

| Criterion | Status |
|---|---|
| No structural heading or bare revision token is accepted as identity | Met: tests, plus the D03 shape end to end |
| A stronger later read resolves a conflict only under the written contract | Met: D04 resolves; D06, D12 and split text stay held; order-invariant |
| Off-title-block decisions are reachable without weakening acceptance | Met as built and unit-tested with scripted answers. Not measurable offline, and left to the fresh validation. |
| Page and target association is deterministic and fail-closed | Met: reader PA plus evaluator .10; the D26 shape scores identically however the other facts are emitted |
| No new false acceptance in offline regressions | Met: 0 newly validated wrong facts |
| Flags-off compatibility | Met: identities, replay fidelity and byte-identical untouched files |
| Tests and package checks pass, apart from failures proven identical to the baseline | See [TESTS-AND-REGRESSIONS.md](TESTS-AND-REGRESSIONS.md) and `evidence/PACKAGE-CHECK.json` |

## Fresh validation

The fresh validation is planned but **not run**: [FRESH-VALIDATION-PLAN.md](FRESH-VALIDATION-PLAN.md).
- 20 unseen, non-sealed documents.
- Labels independently reviewed and frozen before any prediction.
- The accepted baseline against the combined candidate only.
- At most 128 requests.
- Running it needs the owner's authorization.

## Status, stated separately

| Item | Status |
|---|---|
| Correction readiness | See the verdict at the end of [TESTS-AND-REGRESSIONS.md](TESTS-AND-REGRESSIONS.md) |
| Historical experiment | `four-arm-final/` is accepted as reproducible evidence and preserved byte for byte |
| Accuracy | No improved general accuracy is claimed. The replay is diagnostic on an exposed corpus, and the fresh validation has not run. |
| Labels | r26.1 and r26.2 are unchanged. No label was changed after seeing predictions. |
| Default selection | None |
| M2 | **CHANGES STILL REQUIRED.** M3 has not started. |
