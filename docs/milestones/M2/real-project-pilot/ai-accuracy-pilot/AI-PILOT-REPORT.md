# M2 targeted AI accuracy pilot — report (2026-09-30)

**Status:** diagnostic pilot on AI-drafted, **provisional** labels. It is not M2 acceptance, not a generalization claim and not a variant adoption. No production, M3 or sealed-project work was done; the ten sealed projects stay unopened.

**Recommendation:** **INCONCLUSIVE**. There is a small promising signal, no safety regression and no evidence of a general gain. See section 7.

## 1. What was run

The question: can targeted AI recover supported identities, revisions and consultant decisions that are currently missed or held, without new false accepted facts or wrong associations?

| Arm | What it is | Tree | Ledger scope (cap) | Requests sent |
|---|---|---|---|---|
| A | Common base: the accepted application path with AI on and the evidence reader off | `3d5607d` | `…-A` (12) | 2 |
| S | Accepted EV1 evidence policy, unchanged | `3d5607d` | `…-S` (36) | 18 (one of them a 300 s provider timeout) |
| G | S plus the bare-revision-token guard | `e5a0a94`, `AI_EVIDENCE_GUARD=1` | `…-G` (36) | 26 |
| T | G plus targeted verification (region support + independent context read) | `e5a0a94`, both flags | `…-T` (42) | 9 sent, then **8 refused by the scope's token breaker** |
| BOQ-S | Accepted EV1 row selection, r16.1 harness | `3d5607d` | `…-BOQ-S` (12) | 5 |
| BOQ-T | Declared risk-ordered row queue, r16.1 allowance | `3d5607d` | `…-BOQ-T` (12) | 12 |

**Totals:**
- 72 requests settled out of the experiment's 150; 8 were refused and never sent.
- The earlier scope `r2x-small-2026-09-29` is untouched (113 entries).
- Cost is **unknown**: no valid price is configured.
- Tokens are the CLI's reported actuals, and they are estimates for the breaker. Per arm: A 35,615 in / 2,685 out; S 294,497 / 44,509 (one request with unknown usage, charged at its estimate); G 390,869 / 47,873; T 140,666 / 9,087; BOQ-S 27,556 / 2,653; BOQ-T 69,699 / 4,780.
- Actual model on every completed response: `claude-sonnet-5`.

**Sources and controls:**
- **Sample:** 12 documents from 5 exploration projects (16830, 17428, 19144, 23323, 30549), frozen with hashes before labelling: [PILOT-SAMPLE.json](sample/PILOT-SAMPLE.json). There was no availability shortfall.
- **Labels:** written before any prediction, with the uncertainty and exposure register: [labels/](labels/).
- **BOQ sheet:** EP-22510 FA Design, labelled before prediction.

**Declaration and freeze:**
- **Declaration:** [PILOT-DECLARATION.json](declaration/PILOT-DECLARATION.json), sha256 `6218bb8f9bd97f0a55419929385729449d45299e95843f7a43a43f24a13b71cd`. It was frozen at 06:34 UTC, before the first pilot request.
- **Frozen before requests:** code identities; the owner permission (reused, not requested again); arms and caps; per-arm project shares; stop rules; cache mode.
- **Dry run:** a scripted-provider dry run of every runner came first.

**The EP-8430 H-06 BOQ control was declared but not run.** Its project's rolling-24-hour allowance was full (60/60 from 2026-09-29 18:52–19:00 UTC). Any request before about 2026-09-30 19:00 UTC would have breached the 60/project/day rule. Its stored earlier replays remain the history.

## 2. Candidate and tests

The only application file changed is `app/ai/evidence_reader.py`, and every change is flag-gated. See [CHANGE-MAP.md](CHANGE-MAP.md) and [candidate/](candidate/).

**Candidate full suite, flags off:** 1681 passed, 2 failed, 35 skipped. Both failures reproduce on the accepted `3d5607d` ([tests/ACCEPTED-two-failures.log](tests/ACCEPTED-two-failures.log)), so they pre-date this candidate:
- `test_ep_archive_models`: a FOREIGN KEY failure;
- `test_proposed_materials`: extra catalogue items.

**Focused AI/evidence modules (14):**

| Configuration | Result |
|---|---|
| Flags off | 216 passed |
| G | 216 passed |
| T | 213 passed, 3 failed |

The 3 T failures are expected scripted-sequence differences. The extra targeted request is appended, or it consumes the next scripted answer:
- `test_evidence_reader_r7::test_escalation_keeps_the_earlier_disagreement`: one more `blind_context` reading.
- `test_m2_review08::…revision_times_out…`: revision `completed` / decision `budget`, instead of `failed:timeout`.
- `test_m2_review10::…known_revision_constraint…`: decision `candidate` instead of `validated`, which is more conservative.

None of the three is a new acceptance.

**Other tests:**
- The 24 new candidate tests are in the focused set.
- BOQ queue tests: 8 passed.

## 3. Results — documents (evaluator .9, unchanged; provisional labels)

**Pooled over all 12 documents** (evidence layer; recovery = recovered_clean / readable):

| Arm | Identity recovered / held / missed | Revision recovered / held / missed | Decision | Critical false accepts |
|---|---|---|---|---|
| A | 5 / 0 / 5 | 5 / 0 / 3 (tn 2) | tn 9, missed 1 | 0 |
| S | 5 / 3 / 2 | 5 / 1 / 2 (tn 2) | tn 9, missed 1 | 0 |
| G | 6 / 1 / 3 | 6 / 1 / 1 (tn 2) | tn 9, missed 1 | 0 |
| T | 6 / 0 / 4 | 6 / 0 / 2 (tn 2) | tn 9, missed 1 | 0 |

Accepted precision was 1.0 wherever anything was asserted. **Pooled rows are not a G→T comparison**, because T was stopped after 9 requests (section 5).

**Matched coverage:** the 4 documents that S, G and T all processed to completion (EP-16830 ×3, EP-19144 TEL-02). Source: [PILOT-MATCHED.json](results/PILOT-MATCHED.json).

| Field | S | G | T |
|---|---|---|---|
| Identity (3 readable) | 2 recovered, 1 held | 2 recovered, 1 missed | **3 recovered** |
| Revision (2 readable, 1 tn) | 1 recovered, 1 held | 1 recovered, 1 held | **2 recovered** |
| Decision (3 tn) | 3 tn | 3 tn | 3 tn |
| No-record control (Content 14) | no false positive | no false positive | no false positive |

**Per case, G→T on matched documents** (routes from the stored readings; [PILOT-DELTAS.json](results/PILOT-DELTAS.json)):

1. **EP-16830 Reply to Comments, revision `00`.** Held → validated. Route: **targeted context read** (`discovery` + `blind_small` + `blind_context` agree; text-layer support). This is a reply document; the contractor's "Comply" is not treated as a decision, and the decision field stays tn.
2. **EP-16830 Reply to Comments, identity `Caf6NGC/KA/PQ·MEP-002`.** Missed or held → validated. Route: **region support** (the rotation-correct text layer), with no targeted read. **The label is on the uncertainty register**: the U+00B7 separator. T kept the middle dot literally. G's blind reading gave `-` and was correctly held as a conflict.
3. **EP-16830 Authorization, identity `P10781`** (a scan letter; resolved label). The evidence layer is unchanged: the fact was already accepted deterministically. In the **AI layer** it went from held (S and G: "no source text for the read region") to validated. Route: **targeted context read + local OCR support**.

So the AI-attributable gains on resolved labels come to 1 revision (held → accepted) and 1 AI-layer identity confirmation. All three cases come from **two documents of one project**.

**S→G (the guard):** the guard **never fired**. No bare revision token was read as an identity in this sample (0 guard holds, 0 `revision_token` observations in G or T). All three S→G deltas are therefore **run-to-run model/latency variance**, not the guard:
- AR-101: the blind read succeeded in G;
- DJ-295: discovery timed out (300 s) in S;
- EP-16830 identity: a different blind reading.

The guard's value on real data is **untested** in this sample; only its unit and positive-control tests support it.

**Business rows:** the hashes of `project_submittals`, `project_shop_drawings`, `project_actions` and `project_documents.role` are identical in A, S, G and T. No business-row, BOQ-correction, submittal-status or role change was made.

## 4. Results — BOQ (r16.1 replay, unchanged; separate from document metrics)

- **Sheet:** EP-22510 FA Design.
- **Reader output (AI off):** 18 emitted rows (14 accepted lines, 4 held issues) against 15 labelled line rows. The labelled rows all match; 3 emitted rows have no line truth: the panel heading line, the `12V8A` part-only battery row and a duplicate `TP606` issue. [PILOT-BOQ-RESULTS.json](results/PILOT-BOQ-RESULTS.json).

| | BOQ-S (EV1 selection) | BOQ-T (risk queue) |
|---|---|---|
| Requests | 5 | 12 (cap) |
| Rows reached | 4 held + 1 audit (`27193-11`) | 4 held + 3 risk (SIGA-IB, 12V8A, panel line) + 5 audit |
| Confirmed correct accepted rows | 1 | 6 |
| Held rows, blind right / wrong | 2 / 1 | 2 / 1 |
| Rows flagged (conflict) | 0 | 1: the panel line (reader part blank, blind `IO1000-`) |
| Wrong accepted rows caught | 0 | 0 (none exists among matched accepted rows) |
| Not reached | 13 of 18 | 6 of 18: SIGA-PD, SIGA-SB, SIGA-278, SIGA-CR, TP434, 27193-11 |
| At BOQ-S's 5 requests (T prefix) | — | Same outcome counts as BOQ-S |

**Notes:**
- `held_blind_wrong` (IO1000R-2): the blind reading read no quantity cell. The verifier used the `( 1 )` description count, but the replay compares the cell value.
- `12V8A` was validated through its `( 2 )` description count, which is accepted policy. It is labelled part-only, so the replay reports it as an extra row.
- **Neither arm verified the full sheet.** This sheet contains no wrong accepted quantity, so it cannot show whether T's order detects more errors. The fair reading: T spends its 12-request cap on uncertain rows first, and matches BOQ-S at equal request count.

## 5. Coverage, stops and what limited the experiment

| Cause | Where |
|---|---|
| **T token breaker** (declared stop) | T's discovery of FA-105 (EP-17428) reported **81,625 input tokens over 8 CLI turns**, above the declared 70,000 per-request limit. The ledger closed the T scope, and the next 8 requests were refused and never sent. The same page used 26,556 tokens (5 turns) in S and 28,243 (5 turns) in G. The breaker counts the CLI's accumulated cached context, which varies with the number of turns; T's own targeted reads used 6–8k tokens. Per the rules, nothing was raised, reset or re-scoped. T therefore covers EP-16830 fully and FA-105 up to discovery; **7 documents were not attempted by T** (recorded as budget, never as negatives). |
| **120 s per-document job budget** | Full-page discovery on large drawings took 95–266 s. S: 4 documents budget-stopped after discovery (BH2031, TEL-00, DRF, 74028). G: 1 (74028). **This, not model reading, is the dominant bottleneck for large sheets**, and T cannot address it: it never reads after a budget stop. |
| **Provider timeout** | S: 1 (DJ-295 discovery, 300 s; usage unknown, charged at its estimate). |
| **Cross-track day limit / shares** | No refusal. The per-arm shares frozen after A were 19 / 15 / 19 / 19 / 17. |
| **Three-consecutive-failure stop, critical tripwire** | Not triggered; 0 critical acceptances on resolved or unresolved labels in every arm. |

Per-document and per-field coverage for every arm is in [PILOT-MATCHED.json](results/PILOT-MATCHED.json) (`coverage`) and [PILOT-METRICS.json](results/PILOT-METRICS.json) (`coverage`, `breakdowns` by project, stratum and label status).

## 6. What this shows and what it does not

**Shows:**
- On the documents T could process, the targeted route recovered a held revision and confirmed a scan identity by local OCR. The rotation-correct support recovered an identity whose literal punctuation T preserved. There was no false acceptance, no wrong association, and no change on the no-record control.
- The candidate kept every accepted boundary: thresholds, the decision policy, the no-loss envelope and business rows.

**Does not show:**
- a general G→T gain: the matched set is 4 documents, the gains come from 2 documents of one project, and one of them is on an uncertain label;
- any effect of the guard on real data: it never fired;
- BOQ error-detection benefit: no wrong accepted row existed.

**Main blocker found:** large-sheet discovery latency against the 120 s job budget, and CLI turn-count variance against the per-request token breaker. Both are properties of the provider path; neither is a reading-accuracy defect.

## 7. Recommendation and independent-review requests

**INCONCLUSIVE.** It is not unsafe: 0 critical acceptances and business rows unchanged. There is a promising signal for the targeted/local-OCR route on letters, forms and rotated text. The evidence is insufficient because T's scope closed after 9 requests.

Please review independently:

1. **Candidate `e5a0a94`:** the guard definition and its positive controls, `region_texts_v2`, and the `_targeted_read` blindness (the prompt carries no value). Also the validated-role downgrade and the no-read-after-failure/budget rule.
2. **The 3 T-only focused-test differences:** are they acceptable sequence effects?
3. **The breaker stop:** do you agree that stopping T was required? Should a successor declare the per-request breaker on uncached input, or run T's discovery reuse from G's captured reading? The latter needs a provenance contract that this pilot did not have.
4. **Whether the 120 s job budget should stay binding** for full-page discovery of A0 sheets. That is a product decision; it was not changed here.
5. **The provisional labels,** especially the uncertainty items (DJ-295 O/0, the EP-16830 U+00B7 separator, the handwritten DRF `2836`).
6. **H-06:** run the declared BOQ control after 2026-09-30 19:00 UTC within its 60/day allowance, or waive it.

A successor run is **not** scheduled implicitly; it would need a new declaration.
