# M2 Review 18 — targeted AI pilot correction and efficiency-first continuation (2026-09-30)

**Status:** the offline correction and the document continuation are complete. The **H-06 detection control is PENDING**: it is declared, funded and dry-run, but it was not run because EP-8430's rolling window is full. The earliest eligible time is recorded below.

This is not a variant adoption, not M2 acceptance and not a generalization claim. Labels are provisional (AI-drafted, plus a four-page owner-delegated AI source review). No live code, settings, services, database, documents or earlier packages were changed. The ten sealed projects stay unopened.

## 1. What changed, and why (offline, isolated)

The submitted baseline `e5a0a94` was recorded before editing: `evidence_reader.py` sha `ae66397826d1…`, tests `512177a4b98f…`. The successor is commit **`c216206`** in the scratch clone (worktree `C:/t/iso/cand-ai2`). Its only application file is `backend/app/ai/evidence_reader.py`. Files: [CHANGE-MAP.md](CHANGE-MAP.md), [candidate/](candidate/).

With every flag unset, the successor's identities equal the accepted `3d5607d`'s (asserted by the declaration). With G only, it is `e5a0a94`'s G.

| Finding | What was wrong | Fix | Evidence |
|---|---|---|---|
| **R18-01** | A genuine targeted recovery after an empty or illegible primary read stayed `unusable:*`, so it was never selectable. | T `.2`: a field's completion is recomputed from usable evidence. It becomes `completed` only when the targeted reading is legible, carries a value **and reports the field's own role**. The primary and targeted outcomes are kept separately (`own:<f>:primary`, `own:<f>:targeted`; requests `own:<f>`, `own:<f>:targeted`). A wrong-role reading is kept on the observation but excluded from validation. Validation itself is unchanged. | The reviewer probes on the successor ([probes/on-successor](probes/on-successor/TARGETED-PROBES.json)) now read `completed`. Persisted / reloaded / selected tests pass, with the revision target equal to the recovered identity. The negative controls (empty, illegible, timeout, refusal, wrong role) never complete, and the last-good value is kept. A disagreement completes as a **conflict**; an unsupported read completes as a **candidate**; neither ever validates. |
| **R18-02** | A targeted read could follow a failed escalation. | No targeted read after a failed / refused / budget-refused **primary or escalation** request (`not_attempted:after_failure`). Exhaustion is never cleared. | Failed standard escalation: no context read. Budget-refused escalation: the escalation never left the process, `run.exhausted` stays `calls_per_document`. The primary-timeout control is kept. The reviewer's escalation probe now stops after the escalation. |
| **R18-03** | Positional scripted answers were consumed by the extra context read, so later stages never ran. | Tests use `tests/_keyed_provider.py`, which answers by (task, field, tier); an unscripted request fails the test. The R7, R8 and R10 scenarios were rewritten with every original assertion kept, T-specific expectations stated, and the later stages executed. | All three pass with flags off, G and T. In R10 the revision change and the `held:revision_changed` association now run under T. |
| **Scheduling contract** (stated and tested) | An optional read could use budget that a required read needed. | **Required-first, document level:** every triggered page's discovery and required primary reads (identity, revision, decision) run first; only then the optional context reads, identity before revision, while the run is not exhausted and is under the per-document limit. | A 4-call budget test: e5a0a94's order spent the fourth call on the optional read; the successor gives it to the decision and refuses the optional read. A 2-page test: page 2's required reads come before page 1's context read. |

The e5a0a94 test for the wrong-role case was updated to the declared successor contract. Three `e5a0a94` T tests now pin E off because they script whole-page regions.

## 2. Efficiency change E (`AI_EVIDENCE_EFFICIENT=1`, separate flag)

- **Located discovery:** for a drawing sheet (the application's test: long side > 1300 pt), the first request reads the title-block area, never the full sheet.
  - The area comes from the application's number/revision label patterns in its title-block zone. The sources are the text layer, else cached OCR, else bounded local OCR of the application's strip, and for scans also the other edge.
  - A label box is used only when a *number* label exists; otherwise the strip.
  - The crop is at most 1568 px on its long side, and regions are mapped back to the page.
- **Located absence is not verified absence:** it is recorded as `incomplete:located_region_only`, except where discovery saw the whole page, or the page's text carries no decision-block words.
- **Deadline propagation:** each request's timeout is `min(300 s, the job's remaining time)`; no request starts with less than 20 s left. Local OCR gets `min(30 s, remaining − 20 s)`.
- **Cancellation limit:** the CLI adapter kills its direct child process at the timeout. A wrapper's grandchild may outlive it, and a killed request's usage is unknown (charged at its estimate).
- Non-drawing pages (A4 / A3) are discovered as before. DJ-295 is A3, so only the deadline applies to it.

**Offline, independent evaluation** (no model calls): [locator/LOCATOR-EVAL.json](locator/LOCATOR-EVAL.json). The first version is kept as `LOCATOR-EVAL.before-patch3.json`.

- On 9 drawing sheets, the located area contains the labelled identity on 8.
- The TEL-00 scan cannot be checked by local OCR. Its right-edge strip contains the region where S's discovery found the identity.
- The median gain in discovery resolution is 1.56× pixels per point.
- A pre-freeze fix, generic and found on this evaluation: number labels are required for a label box, and scans try both title-block edges.

## 3. Tests (successor `c216206`)

| Run | Result |
|---|---|
| 15 focused AI / evidence modules, flags off / G / T | **246 / 246 / 246 passed** |
| Same modules, T+E with the whole-sheet frame shim (`tests/_e_frame_shim.py`) | 246 passed |
| Same modules, T+E **without** the shim | 227 passed, **19 failed** |
| r16.1 harness (allowance / overlay / association / join) | 66 passed |
| BOQ queue | 8 passed |
| Full backend suite, flags off | **1711 passed, 2 failed, 35 skipped** (1681 + the 30 new tests). The 2 failures are the known baseline failures below. |

The 19 failures without the shim are all existing persisted-stage tests that script discovery regions in the whole page's frame on an A2 drawing sheet. With the shim, the located area is the whole sheet and nothing else changes, and all 246 pass. This is frame dependence of the scripts, not an E defect.

The e5a0a94 flags-off full suite had 2 baseline failures, which reproduce on `3d5607d`:
- `test_ep_archive_models::…lookup_index` (FOREIGN KEY);
- `test_proposed_materials::…completes_it` (extra catalogue items).

JUnit, logs and exit codes are in [tests/](tests/).

## 4. Guard (G): offline replay of the confirmed case

[guard/GUARD-REPLAY.json](guard/GUARD-REPLAY.json) is an **offline** replay with no model call. It uses the captured readings of the accepted EV1 run's confirmed critical acceptance (review 13, EP-17428 `FA MS/Rev.01/1-7.pdf`, page 4, `Rev.0` next to "Submittal No.") and the region text recomputed from the hash-checked staged source.

- Guard off: **validated** (the acceptance is reproduced).
- Guard on: **candidate, `bare_revision_token`**.
- 11 short-identifier controls stay validated: FAS-09, 3105, P10781, AR-101, 2836, E, EML-09, 819-TL-101, ELEC-B16-EM-101, EP-23091 R1 and a `-R3`-suffixed number.

The live pilot and the continuation never triggered the guard. This demonstrates the guard on the real captured case; it does not measure a live-document benefit.

## 5. Labels: v2 and a separate replay

- **v2 labels:** `ai-pilot-labels-2026-09-30.2`, in [labels-v2/](labels-v2/). They add only the Review 18 source review, with its sha, page and render hashes. The review is an owner-delegated AI review, not human and not blind, and covers four pages only.
  - Reply to Comments: the U+00B7 separator is resolved as printed; revision 00 confirmed.
  - P10781 confirmed.
  - DJ-295: revision 00 confirmed; the O/0 question stays **open**.
  - DRF: the handwriting stays **uncertain**. Its project association is now **unresolved**: it prints EP-18101 and nothing is inherited from the EP-19144 folder. The footer "Revision Number 03" is template metadata.
  - All 12 documents are exposed from now on. v1 is kept unchanged.
- **Separate offline replay:** [rescore/RESCORE-v1-v2.json](rescore/RESCORE-v1-v2.json). No score changes. The only change is that Reply to Comments becomes a resolved label, so the pilot's two G→T gains on it now sit on a resolved label.
  - The identity gain is region support (rotation), not a new model read.
  - The revision gain came via the targeted read.
  - P10781 is an AI-layer confirmation of a fact the deterministic path had already accepted.

## 6. Continuation: live, frozen before any request

**Declaration and budget:**
- [declaration/CONT-DECLARATION.json](declaration/CONT-DECLARATION.json), sha `7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3`, frozen 13:23 UTC.
- The residual of the original 150 was reconciled immediately before: 72 settled, 8 breaker refusals (never sent), **78 left**.
- Subcaps: H-06 BOQ-S 12 + BOQ-T 12 (reserved first), A 4, S 21, T2 29.
- The closed pilot T scope stays closed.

**Sample:** [CONTINUATION-SAMPLE.json](sample/CONTINUATION-SAMPLE.json).
- 4 **exposed** large-sheet controls whose S discovery ran out of time or timed out in the pilot: BH2031, TEL-00, 74028, DJ-295.
- 3 **new** drawing sheets, never predicted before, labelled beforehand from their text layer and renders:
  - EP-27421 `EML-09` (medium confidence: no "Drawing No" label);
  - EP-26208 `ELEC-B16-EM-101`;
  - EP-16830 `819-TL-101`.

**Arms:**
- **S:** accepted `3d5607d`, EV1.
- **T2:** `c216206`, G+T+E.
- Each arm started from a copy of a common A base, with its own caches and sandbox; nothing from the pilot's G or T evidence was loaded.

**Requests (ledger):** A 1, S 15, T2 16, so **32 used, 46 left, of which 24 are reserved for H-06**. Cost is unknown. Every settled request's total input, including cached input, stayed ≤ 55,102, under the 70,000 breaker.

### All 7 planned documents (evaluator .9, unchanged)

| Arm | Identity recovered / held / missed | Revision recovered / held / missed | Precision (identity, revision) | Critical (resolved / unresolved) |
|---|---|---|---|---|
| A | 2 / 0 / 5 | 3 / 0 / 4 | 2/2, 3/3 | 0 / 0 |
| S | 2 / 3 / 2 | 3 / 3 / 1 | 2/2, 3/3 | 0 / 0 |
| T2 | **5 / 0 / 2** | **5 / 0 / 2** | 5/5, 5/5 | 0 / 0 |

In all three arms the decision field is tn 6 with 1 missed: the TEL-00 consultant decision was not read by any arm.

### Matched completed subset

The subset is the documents complete in both S and T2: BH2031, EML-09, ELEC-B16, 819-TL-101.

| Arm | Identity | Revision |
|---|---|---|
| S | 1 recovered, 3 held | 2 recovered, 2 held |
| T2 | **4 recovered** | **4 recovered** |

### Coverage per document

| Document | S | T2 |
|---|---|---|
| BH2031 (control) | complete: discovery 39 s (the pilot's S took 266 s) | complete: located discovery 36 s, 14.6k tokens against S's 27.6k; one context read (identity) |
| DJ-295 (control, A3) | discovery 190 s, then the elapsed budget stopped the reads | discovery **killed at 119.8 s** by the deadline timeout (`failed:timeout`, usage unknown) |
| TEL-00 (control, scan) | discovery 180 s, then the elapsed budget stopped the reads | located discovery **19.9 s**, but the located strip (from the cached OCR) was the bottom edge, and the identity sits on the right, so identity and revision are `incomplete:located_region_only`. An honest incomplete, not a false negative. |
| 74028 (control, A0) | complete: discovery 57 s this time (the pilot's S: 95 s, then budget) | located discovery **timed out at 114 s** (the deadline) |
| EML-09 (new) | complete, identity held | complete, validated |
| ELEC-B16 (new) | discovery gave no regions (`incomplete:no_region`) | located discovery gave regions; validated |
| 819-TL-101 (new) | complete, identity held | complete, validated; discovery 28 s / 8.0k tokens against 41 s / 27.8k |

**Discovery input tokens** (total including cached):
- S full page: mean about 30.7k over 7 requests.
- T2 located: mean about 13.9k over 5 completed requests; 2 timed out.

**Latency** is mixed and dominated by model variance: the same S sheet varied 39 s to 266 s between runs.

### Where the S→T2 gains come from

The sources are [results/CONT-DELTAS.json](results/CONT-DELTAS.json) and [support/SUPPORT-REPLAY.json](support/SUPPORT-REPLAY.json), an **offline** replay of S's own captured readings with only the region text recomputed by the rotation-correct support.

- **819-TL-101 identity and revision, EML-09 identity** (all on 270°-rotated pages): S's own readings **validate** once the rotation-correct text is used. These gains are the **deterministic support fix**, not new model reads. The same replay also validates the pilot's Reply to Comments (identity and revision) and P10781.
- **ELEC-B16 identity and revision:** S's full-page discovery named both values but gave no region (`incomplete:no_region`), so nothing was read. T2's located discovery gave regions, and the blind reads validated with rotation-correct support. These gains come from **E plus support**.
- **EML-09 revision:** S's discovery read `0` against the blind `00`, a disagreement correctly held as a conflict (**model variability**). T2's readings agreed on `00`.
- **Targeted context reads:** one request in total (BH2031 identity), with no score change.
- **Losses:** 74028's AI-layer revision and DJ-295's held revision are lost in T2 **because of the deadline-bound timeouts**. These are bounded failures instead of 190–300 s reads.

**Model variability versus deterministic effects:** the support fix (and the guard) are deterministic and replayable, and the offline replays show it. Discovery latency, turn count, token count and whether discovery finds a region all vary between runs of the same code (for example BH2031's S discovery: 266 s in the pilot, 39 s here).

## 7. H-06 detection control: PENDING, not waived

The runner, arms, allowance and scoring are declared, dry-run end to end, and funded (24 reserved).

- **Blocked refusal:** at 13:47 UTC the runner refused before any request: "EP-8430 rolling-24-hour allowance cannot fit this arm now (60/60 used)" ([logs](logs/run-h06-S-blocked-check.log)).
- **Earliest eligible window:** from the real rolling counter, EP-8430's 60 calls expire between 18:52:31 and 19:00:02 UTC on 2026-09-30.
  - One 12-request arm fits from **18:53:57 UTC**.
  - Both arms (24 requests) fit from **18:55:21 UTC**.
- **Evaluation-only targets:** the r16.1 replay with the r14.1 amended labels and the verified geometry identifies three wrong accepted rows (L1, L9, L19: emitted quantity 4 where 1 is printed) and the control L17 (2 = 2). These appear only in scoring, never in a prompt, queue or selection.
- **Finding from the dry run** (the queue is deterministic, independent of answers): the frozen BOQ-T risk queue puts every held row first. H-06 has more held rows than the 12-request cap, so **BOQ-T would reach none of the accepted wrong rows**. The EV1 selection's seeded audit reaches accepted rows. Changing the queue now would tune it with knowledge of H-06's rows, which is not allowed, so the queue is unchanged. A successor queue design needs its own declaration.

## 8. Recommendation and what needs independent review

**Still diagnostic, and not safe to generalize.**

- **Promising, deterministic:** rotation-correct region support. It is replayable offline, explains most observed gains in both the pilot and the continuation, and made no false acceptance.
- **Mixed:** E. It uses fewer tokens and gives regions where full-page discovery gave none, but it is not reliably faster; two deadline timeouts and a wrong-edge strip on a scan cost coverage.
- **Unmeasured:** the targeted read added one request and no score change. The guard's real-document benefit is shown only by offline replay.
- **Safety:** zero false acceptances on a small provisional sample is not a safety result.

Please review:

1. The completion rule (own role required; a disagreement completes as a conflict; an unsupported read as a candidate).
2. The required-first contract, and whether document level is the right scope.
3. E's located-absence outcome and its cost to coverage.
4. The frame-shim argument for the 19 T+E script failures.
5. The TEL-00 cached-OCR strip choice (the alternate-edge search applies only to fresh local OCR).
6. The BOQ-T queue finding.
7. Whether to run H-06 at the recorded window under this declaration, or waive it.

M2 remains **CHANGES STILL REQUIRED**.
