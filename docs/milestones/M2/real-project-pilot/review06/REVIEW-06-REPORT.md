# M2 Review 06: correction package, AI evidence recovery and verification

**Verdict: CHANGES STILL REQUIRED.**
- M2 is not accepted, and M3 is not started.
- Nothing is promoted, committed or pushed.
- No live setting or service is changed.

## Scope and isolation

| Item | Detail |
|---|---|
| Owner's tree | `2221b43` plus the uncommitted Review 05 Candidate C, **untouched**: no stash, reset, clean, commit or push. Live API and workers not touched. Live DB and symbol library read only (project AI policies). |
| Isolated candidate | `C:/t/iso/ep-platform/backend`, a copy that nothing live watches, with its own sandbox `.env` (AI off, sandbox paths, no key). Scratch baseline commit `c692f1e` = Candidate C, carried explicitly; all 11 frozen hashes verified, and the 48 reviewer tests pass there. |
| Evaluation sandboxes | `C:/t/r6/<tag>`: each has its own database, cache, library and uploads. Inputs are the Review 05 staged copies, read only. |
| Historical evidence preserved | Candidate C, evaluator .3, labels v1/v2, all Review 05 runs, and the four failed holdout projects. The superseded `.7` runs and every crashed or stopped attempt are also kept. |
| Names | Historical Candidates A/B/C are kept apart from the AI experiment variants **AI-EV0-baseline**, **AI-EV1-targeted** and **AI-EV2-broad**. The extraction profiles default/promoted are a separate axis. |

## Package

| Document | Contents |
|---|---|
| [DISPOSITIONS.md](DISPOSITIONS.md) | R6-01 to R6-05 and H-01 to H-06, with source, tests and evidence; defects found and fixed during the round; open defects D-R6-A to D |
| [EVALUATOR.md](EVALUATOR.md) | Evaluator .4 and BOQ evaluator .3: rules, 14 + 3 adversarial tests (each fails on .3), the reviewer's six probes re-run, and every stored output re-scored |
| [CALL-FLOW.md](CALL-FLOW.md) | AS-IS against candidate call flow, the evidence stage, compatibility results |
| [DETERMINISTIC-RESULTS.md](DETERMINISTIC-RESULTS.md) | Candidate `parse .8` against Candidate C, pilot and holdout, both profiles |
| [BOQ-RESULTS.md](BOQ-RESULTS.md) | Deterministic, model-disabled application, real-model application and blind row verification, kept apart |
| [REAL-MODEL-RESULTS.md](REAL-MODEL-RESULTS.md) | Declaration and addenda, the matrix actually run, usage, accuracy, findings, mocked tests listed separately |
| [ROUND2-PLAN.md](ROUND2-PLAN.md) | 34-project selection (14 exposed + 10 exploration + 10 sealed): seeded, metadata only, frozen; shortfalls |
| [REGRESSION.md](REGRESSION.md) | Reviewer set, new tests, full suite; pre-existing failures tracked separately |
| [PROMOTION-ROLLBACK.md](PROMOTION-ROLLBACK.md) | Proposal for the exact isolated candidate |
| `evidence/` | `EVIDENCE-MANIFEST.json` (SHA-256 of every file and of every candidate source file), `candidate.diff`, `candidate_new_files/`, runs, scores, scripts, logs |

## Results in brief

Every project scored here is **exposed data**, so none of this is a generalization claim.

1. **Evaluator (R6-01 to R6-04, closed).** Every stored output was re-scored.
   - Candidate C: 0 → **2 critical** per profile (flagged references used as register keys).
   - Candidates A and B: 31 → 33 and 30 → 35.
   - The reviewer's six probes now give the outcomes the reviewer expected.
   - The complete raw-layer measurement exists for the first time.
2. **Deterministic extraction, candidate `parse .8`:**
   - pilot: critical 2 (unchanged, D-R6-A); raw identity 223 → **244** / 363; raw revision 185 → **195** / 310; register revision 104 → 107 (default) and 108 → 111 (promoted);
   - holdout: register reference 0 → 3 / 5; raw identity 3 → **14** / 20; raw revision 0 → **7** / 13; 0 critical;
   - H-01 partly and H-02, H-04, H-05 closed as raw evidence; H-03 decisions open; H-06 partly.
   - A `.7` regression, 3 wrong OCR register keys, was found and fixed in `.8`, and is disclosed.
3. **BOQ, deterministic.** Critical: pilot 5 → **4**, holdout 4 → **3** (quantity passes that agree against the strip now hold the row). A recovery-costly option (C) is measured but not adopted.
4. **Real model**, through the existing `claude-code` provider, on the only projects with a recorded AI policy (29076, 30088, 30784):
   - **690 application requests, 0 failed apart from 1 explicit timeout; cost unknown.**
   - **AI-EV0 (AS-IS) introduced one critical false acceptance:** a transmittal acknowledgment keyed under its listed item. AI-EV1's blind discovery held exactly that case as a conflict.
   - **AI-EV1 and AI-EV2 changed no record** (mirror identical) and **introduced no error** in the evidence layer.

     | Scope | Variant | Identity | Revision | Decision | Requests |
     |---|---|---|---|---|---|
     | EP-29076 | AI-EV1 | +3 | +2 | +0 | 134 |
     | EP-29076 | AI-EV2 | +2 | +1 | +1 | 221 |
     | all 3 projects | AI-EV1 (partial) | 93 → 100 | 68 → 70 | 29 → 30 | 200 |

     **Broader verification did not pay** on this data.
   - **The application's model BOQ path** on four sheets: part 155/156 and quantity 163/163, against the deterministic reader's 113/115 and 121/121. Critical 1 (PT-1S+) against 2.
   - **Blind row verifier `.2`:** parts **50/50** right against OCR 41/50. It caught the PT-1S+ accept and read all 9 reader part errors right, with 0 introduced. Quantity verification is limited by the component-count layout. A stricter policy re-validated on the stored readings is clean (0 missed, 0 false alarms), but it was shaped on this exposed data and remains a candidate.
5. **Round 2:** 34 projects selected and frozen from metadata; 2,933 exploration and 2,517 sealed PDFs available. Nothing new has been read, labelled or run.

## Blockers (why CHANGES STILL REQUIRED)

| # | Blocker | Needs |
|---|---|---|
| B-1 | **Recovery is below 90% on every field** in every configuration. Pilot register: reference 83.5–86.7%, revision 75–77%, decision 37–40%. Raw decision recovery is 36%. | More extraction work; broader AI evidence with a component-role rule (most AI identity readings end as conflicts). |
| B-2 | **Critical false acceptances remain.** 2 per profile on the pilot register (D-R6-A: flagged-incomplete references used as register keys). The **AS-IS AI path adds one more** (AI-EV0). BOQ keeps 4 pilot + 3 holdout deterministic, and 1 on the application's model path. | An owner decision on flagged references as keys; a fix to the submittal reader's own-identity association; the BOQ verifier `.2` / stricter policy frozen and validated. |
| B-3 | **Real-model evidence is narrow.** Only 3 of the 14 exposed projects have a recorded AI policy. H-03 (client/consultant decisions) and H-06 (EP-8430 BOQ) could not be sent to the model. EV2 was run on one project, and EV2 with verifier `.2` not at all. | The owner records `ai_policy` for the projects to be evaluated, or states that unregistered pilot projects may be used. |
| B-4 | **Round 2 cannot be scored.** There are no independent source labels for the 20 new projects, and no **second independent human review**. Gold truth may not be model-generated or approved by a model alone. The exploration cohort is not yet staged; the sealed cohort must stay unread until the freeze. | The owner, or a reviewer the owner appoints, labels and second-reviews. Staging through the approved workflow. |
| B-5 | **Cost controls.** Pricing is not configured (cost unknown). The per-task input-token cap is checked on the reservation, not the actual count: discovery used 16–30k tokens against a declared 6k (D-R6-D). | Pricing or an account cap; enforce actual-token caps before any live use of the evidence stage. |
| B-6 | **Contract change to confirm.** BOQ rows whose 60–90% strip quantity is contradicted by agreeing passes are now held, not accepted. This replaces a Review 02 contract (REGRESSION.md). | Reviewer confirmation. |

## What was deliberately not done

- No live service start, stop or restart.
- No change to the live `.env`, live DB or symbol library.
- No processing of originals.
- No commit or push.
- No consumer or tab migration.
- No AI or OCR in GET handlers.
- No new business statuses, and no discovered observation inserted into a register.
- No sealed data read.
- No tuning on sealed data.
- No mocked response presented as real-model evidence.
