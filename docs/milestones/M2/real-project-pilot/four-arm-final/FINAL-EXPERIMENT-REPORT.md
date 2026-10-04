# M2 four-arm accuracy experiment: final report (2026-10-01)

**Declaration:** `6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1` ([declaration](declaration/FINAL-DECLARATION.v2.json)), executed under the owner's written authorization ([authorization](authorization/AUTHORIZATION-2026-10-01.md), sha256 `2e700c3e…`).
**Bindings:** baseline `3d5607d`, candidate `719e8de`, harness v4.3, labels r26.2, evaluator .9, scorer v4. All were re-checked before every dispatch and after the run ([post-run bindings](run/POST-RUN-BINDINGS.json)).

**No default variant is selected or deployed.** M2 remains **CHANGES STILL REQUIRED**. This package is submitted for independent review and is not self-approved.

## Outcome in brief

- All five arms ran to the end. A, L2, L3 and L4 completed. **L1 was budget-stopped** when one page-discovery request used 70,264 actual input tokens, above the 70,000 per-request threshold. Its breaker refused every later request, so 4 projects and part of a fifth were never read.
- **No arm accepted a wrong value on a resolved label.** Two arms accepted a wrong value on a label that is on the predeclared uncertainty list:
  - L2 accepted revision "00" on D26 page 2, read from the running footer.
  - L4 accepted the heading "2.4 Accessories" as D03's identity. A targeted read introduced it.
  
  Neither was a terminal stop under the declared rule.
- **Every predeclared comparison is INCONCLUSIVE.** Too few matched facts exist for decisions (2 to 4 resolved documents), and the identity and revision intervals include zero. Nothing is supported and nothing is contradicted. See [ARM-COMPARISON.md](ARM-COMPARISON.md).
- **Targeted reads show no evidence of benefit.** The X gate fails in both pairs. In L3 and L4 the targeted reads often found the correct value: D04 "17", D06 the full number, D12 "…_MAIN". Each time the reader's conflict rule kept the first, wrong value as a held candidate. In L4 one targeted read produced the D03 false accept.
- **Consultant decisions outside the title block were not recovered.** No arm read a decision on the crop-eligible pages D16, D17 or D18. The ROI arms located two of them but did not read them. The ROI decision gate passes for L1 → L2, where L1's breaker confounds it. It fails by the predeclared rule for L3 → L4.

## Requests and usage

Full detail: [USAGE-AND-BUDGET.json](USAGE-AND-BUDGET.json). Cost is unknown.

| Scope | Dispatched / cap | Provider-reported input (cached) / output | Estimated charge for timeouts with unknown usage | Ledger total input / output | Breaker |
|---|---|---|---|---|---|
| A | 4 / 8 | 46,729 (21,559) / 5,519 | none | 46,729 / 5,519 | clear |
| L1 | 34 / 160 | 430,943 (277,813) / 56,708 | 3: 109,259 / 28,091 | 540,202 / 84,799 | **open** (request 287) |
| L2 | 64 / 160 | 648,129 (409,162) / 85,097 | 2: 22,786 / 1,600 | 670,915 / 86,697 | clear |
| L3 | 66 / 180 | 711,471 (438,103) / 104,982 | 3: 136,632 / 32,610 | 848,103 / 137,592 | clear |
| L4 | 66 / 180 | 634,893 (387,305) / 100,950 | 2: 23,669 / 1,600 | 658,562 / 102,550 | clear |
| **Total** | **234 / 688** | **2,472,165 (1,533,942) / 353,256** | **10: 292,346 / 63,901** | **2,764,511 / 417,157** | |

- **Refusals before dispatch:** No request was refused by the rolling counter or the durable allowance. The ledger refused 10 requests in L1, all after its breaker opened. Reader calls ending with a budget outcome numbered 15 in L1, combining the breaker and the per-document time budget. In L2, L3 and L4 they numbered 4, 12 and 8, all from the per-document time budget. Refused calls are not sent requests.
- **Models:** Every response was from claude-sonnet-5. The "sonnet" rows are timeouts, where no model was reported. No escalation to the standard model occurred.
- **Original 150-request experiment:** It is unchanged at 128 settled requests. No undeclared scope exists, and nothing is in flight.

## Accuracy and coverage (whole sample, all denominators retained)

The denominators are 27 planned documents and 42 in-scope pages. The pages hold 30 identity facts, 30 revision facts and 7 consultant-decision facts. The 54 pages beyond the reader scope and the Word control D27 stay in the denominators.

The **evaluator recovery** column comes from the frozen evaluator's evidence totals. It combines the deterministic and AI layers, so it is not AI-only. All other columns count the AI reader's own emissions. Full detail: [ACCURACY-AND-COVERAGE.json](ACCURACY-AND-COVERAGE.json).

| Arm | Field | Evaluator recovery (clean) | Accepted precision | Field read completed | Verified absence | Wrong absence | Accepted correct / wrong | Held correct / wrong / on no-record |
|---|---|---|---|---|---|---|---|---|
| A | identity / revision / decision | 13 / 10 / 0 | 13/13, 10/11, none | n/a | n/a | n/a | n/a | n/a |
| L1 | identity | 14 | 14/14 | 8 | 1 | 0 | 2 / 0 | 7 / 4 / 1 |
| L1 | revision | 12 | 12/13 | 5 | 1 | 2 | 2 / 0 | 3 / 0 / 1 |
| L1 | decision | 0 | none | 1 | 9 | 1 (D16) | 0 / 0 | 1 / 0 / 0 |
| L2 | identity | 20 | 20/20 | 15 | 1 | 0 | 9 / 0 | 5 / 4 / 4 |
| L2 | revision | 14 | 14/16 | 12 | 2 | 2 | 8 / 1 | 2 / 0 / 2 |
| L2 | decision | 1 | 1/1 | 6 | 9 | 0 | 1 / 0 | 1 / 0 / 0 |
| L3 | identity | 19 | 19/19 | 16 | 2 | 0 | 6 / 0 | 9 / 4 / 3 |
| L3 | revision | 13 | 13/14 | 10 | 2 | 3 | 5 / 0 | 4 / 1 / 3 |
| L3 | decision | 1 | 1/1 | 5 | 16 | 1 (D18) | 1 / 0 | 1 / 0 / 0 |
| L4 | identity | 23 | 23/24 | 19 | 1 | 0 | 11 / 1 | 3 / 6 / 1 |
| L4 | revision | 13 | 13/14 | 12 | 2 | 3 | 6 / 0 | 5 / 0 / 1 |
| L4 | decision | 1 | 1/1 | 3 | 8 | 0 | 1 / 0 | 1 / 0 / 0 |

- **Revision wrong in every arm:** The one wrong revision shared by all arms, A included, is the deterministic title-block reading of D15 ("00" against R1). It is not an AI error.
- **L2's second wrong revision:** It is the D26 page-2 critical acceptance.
- **Required-complete documents:**

| Arm | Required-complete documents |
|---|---|
| L1 | 4 |
| L2 | 4 |
| L3 | 11 |
| L4 | 5 |

- **Remaining populations:**
  - **Unsupported:** 1 document in every arm.
  - **Incomplete:** 22 documents in L1, 22 in L2, 15 in L3 and 21 in L4.
  - **Budget page-fields:** 18 in L1, 8 in L2, 12 in L3 and 16 in L4.
  - **Not-attempted page-fields:** 33 in L1, 12 in L2, 15 in L3 and 9 in L4.
- **A completed read is not a recovery.** A "verified absence" is only an absence where the frozen truth has no fact. Absences on pages that carry a fact are counted as wrong absences: D16 in L1 and D18 in L3.

## Critical acceptances and held facts

Full detail: [CRITICAL-AND-HELD-EVIDENCE.json](CRITICAL-AND-HELD-EVIDENCE.json).

| Arm | Critical acceptance | Label status | How |
|---|---|---|---|
| L2 | D26 p2 revision "00" | uncertain (confidence medium, on the list) | validated from the running-footer text, region [428, 741, 533, 752] pt |
| L4 | D03 p1 identity "2.4 Accessories" | uncertain (confidence medium, on the list) | validated after a targeted read (reason: unexplained empty document) |

No critical acceptance landed on a resolved label in any arm. The runner tripwire, which is scoped to resolved labels, never fired.

## Adoption gates

Full detail: [ADOPTION-GATES.json](ADOPTION-GATES.json) and [ARM-COMPARISON.md](ARM-COMPARISON.md).

| Gate | L1 | L2 | L3 | L4 |
|---|---|---|---|---|
| No critical accepted value on resolved truth | pass | pass | pass | pass |
| No critical acceptance at all | yes | **no** (D26) | yes | **no** (D03) |
| Decision coverage does not regress | baseline for L2 | passes against L1 (confounded by L1's breaker) | baseline for L4 | **fails by the predeclared rule** against L3, and is equal on strict completed reads |
| X gate: 1 correct fact per 8 extra requests, no new false accept, interval above zero | n/a | n/a | **fails** (0 net facts for 32 extra requests) | **fails** (0 net facts for 2 extra requests; new false accept D03) |
| Incomplete and unsupported items retained in denominators | yes | yes | yes | yes |
| Matched population sufficient | no | no | no | no |

**No default.** No arm meets the gates. No difference is supported, and the only nonzero paired difference, D22 revision for L3 → L4, comes from one project. A default may not rest on coverage or request count alone.

## Limitations

- **L1 breaker:** L1 stopped after 34 requests, so every comparison with L1 is confounded by coverage imbalance.
- **Run-to-run variation:** The same model and inputs gave different first readings. Examples are "DJ-295/296/298-…" for D09, "BSB/B18" for D01, "FA-101-106/FA-101-10" for D04, and different D26 footer forms. This happened in 5 to 6 of 36 to 73 common first readings, even where the arms differ only in targeted reads.
- **Sample size:** 26 PDFs and 7 decision facts can show only large effects. The decision population for ROI is 3 crop-eligible pages, all in one project.
- **Label provenance:** Labels r26.2 rest on an independent AI review delegated by the owner. That review is not human and not blind.
- **D26 page-2 scoring:** The frozen evaluator scored the same value "00" three different ways across arms, because its page association differed. The scores are kept as frozen. See [POST-RUN-ADJUDICATION.md](POST-RUN-ADJUDICATION.md).

## What is in this package

- **Per-arm reports:** [L2](arms/L2/L2-REPORT.md), [L3](arms/L3/L3-REPORT.md) and [L4](arms/L4/L4-REPORT.md). The L1 figures are in [the L1 machine report](arms/L1/REPORT-L1-FULL.json) and in this report.
- **Frozen per-arm evidence:** `arms/<arm>/` holds each run's outputs, provider journal, request log, rows, usage, ledger rows, rolling-counter calls, interim scoring and sandbox database, plus its own manifest.
- **Targeted calls:** [L3](targeted/TARGETED-L3.json) and [L4](targeted/TARGETED-L4.json).
- **Final offline scoring:** [ARMS-METRICS.v4.json](final-score/ARMS-METRICS.v4.json) and the per-arm evaluator outputs. The scorer exited 0 with AI disabled and a throw-away database.
- **Run log, preflights and post-run bindings:** under `run/`.
- **Scripts:** under `scripts/`.
- **Manifest and package check:** [the manifest](evidence/EVIDENCE-MANIFEST.json) and [the package check](evidence/PACKAGE-CHECK.json). The check re-runs the frozen scorer and the analysis offline and requires identical results.

## Status, stated separately

1. **Experiment:** Executed under the approved declaration, with 234 of the 688 requests used.
2. **Extraction accuracy:** Measured, but the comparisons are inconclusive.
3. **Default:** None selected.
4. **Production:** No production change.
5. **M3:** Not started.
6. **M2:** CHANGES STILL REQUIRED.
7. **Review:** Submitted for independent review, not self-approved.
