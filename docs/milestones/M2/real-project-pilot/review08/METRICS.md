# M2 Review 08: metrics under frozen labels, with unresolved truth kept visible

- **Evaluator:** `m2-pilot-eval-2026-09-29.7`.
- **Labels:** Golden v2 as frozen, page labels v2, holdout labels as frozen.
- **No new model run.** Every figure comes from outputs already stored by Reviews 05–07.
- **Files:** [`evidence/metrics/METRICS-R8.json`](evidence/metrics/METRICS-R8.json) (script `metrics_r8.py`) and [`evidence/eval7/`](evidence/eval7/SUMMARY.json) (script `rescore7.py`).

## 1. Evaluator .7 reproduces .6 when each run's own context is declared

Each stored run was scored with the AI context its manifest declares:

| Runs | Declared context |
|---|---|
| Review 06 AI-EV1 and AI-EV2 | default profile and their variant; their flat envelopes store no profile, so `accept_unknown_profile` is declared |
| Matched AI-EV1 and AI-EV2 | `default\|EV1` and `default\|EV2` |
| AI-EV0 and every deterministic run | no AI stage |

Result: **all 33 scored runs give the same totals as evaluator .6.**
- 28 are identical in full once the two fields .7 adds are removed: the declared context, and each document's AI evidence state.
- The other 5 are the AI runs. Their documents are equal as unordered judgements; the order changed because fields are now stored per field. See [`ORDER-ONLY-CHECK.json`](evidence/eval7/ORDER-ONLY-CHECK.json).
- One further run, `r6-det7-pilot-promoted`, has no stored output, as in Review 07.

**Negative controls.** In each of these the AI evidence is `unavailable`, so it contributes nothing:

| Control | Scored as |
|---|---|
| Review 06 EV1 rows, legacy profile not declared | EV1 |
| Review 06 EV1 rows | EV2 |
| Matched EV1 rows | EV2 |
| Matched EV1 rows | `promoted` |

## 2. Automatic acceptance and raw observation, kept apart

These are evidence-layer judgements:

| Term | Meaning |
|---|---|
| **auto** | accepted by the parser or validated by the verifier, i.e. what would reach the register |
| **observed** | a raw reading that was never accepted |
| **held** | kept out of the register for review; neither a success nor an error |

Two views, both declared:
- **frozen:** scored against the labels as frozen;
- **unresolved excluded:** judgements on the 10 pages of the 8 *decide* groups of the [findings index](human-review-packet-v2/FINDINGS-INDEX.md) are removed from the denominators. They are listed below as unresolved truth.

The 5 *confirm* groups stay counted in both views: their labels are not disputed. **Neither view calls a pending dispute an AI success or a confirmed error.**

| Run (context) | Field | Auto precision, frozen | Auto, unresolved excluded (unresolved) | Observed precision, frozen | Observed, unresolved excluded (unresolved) | Held correct / wrong | Recovery (readable) |
|---|---|---|---|---|---|---|---|
| Frozen deterministic, pilot (r7-det9, default) | identity | 142/142 = 1.000 | 1.000 (1) | 0.913 (19 errors) | 0.938 (7) | 9 / 13 | 0.672 (363) |
| | revision | 105/105 = 1.000 | 1.000 (0) | 0.989 (2) | 1.000 (2) | 2 / 0 | 0.710 (310) |
| | decision | 26/26 = 1.000 | 1.000 (0) | n/a (0 observed) | n/a | 13 / 0 | 0.325 (80) |
| Frozen deterministic, holdout (r7-det9, default) | identity | 3/3 = 1.000 | 1.000 (0) | 0.875 (2) | 1.000 (2) | 0 / 0 | 0.700 (20) |
| | revision | 2/2 = 1.000 | 1.000 (0) | 1.000 (0) | 1.000 (0) | 0 / 0 | 0.538 (13) |
| Matched, model-disabled (det9, 12 documents) | identity | 12/12 = 1.000 | 1.000 (0) | 0.833 (1) | 1.000 (1) | 0 / 1 | 0.875 (16) |
| | revision | 10/10 = 1.000 | 1.000 (0) | 0.889 (1) | 1.000 (1) | 0 / 0 | 0.813 (16) |
| | decision | 6/6 = 1.000 | 1.000 (0) | n/a | n/a | 3 / 0 | 0.667 (9) |
| Matched, AI-EV1 (default\|EV1) | identity | 18/19 = 0.947 | 1.000 (1) | 0.833 (1) | 1.000 (1) | 7 / 3 | 0.875 (16) |
| | revision | 21/22 = 0.955 | 1.000 (1) | 0.889 (1) | 1.000 (1) | 3 / 0 | 0.813 (16) |
| | decision | 9/9 = 1.000 | 1.000 (0) | n/a | n/a | 6 / 0 | 0.778 (9) |
| Matched, AI-EV2 (default\|EV2) | identity | 17/18 = 0.944 | 1.000 (1) | 0.833 (1) | 1.000 (1) | 4 / 4 | 0.875 (16) |
| | revision | 17/17 = 1.000 | 1.000 (0) | 0.889 (1) | 1.000 (1) | 4 / 0 | 0.813 (16) |
| | decision | 7/7 = 1.000 | 1.000 (0) | n/a | n/a | 7 / 0 | 0.667 (9) |
| Review 06 AI-EV1, eligible projects (default\|EV1, legacy profile declared) | identity | 84/89 = 0.944 | 0.954 (2) | 0.707 (17) | 0.714 (2) | 19 / 18 | 0.711 (142) |
| | revision | 70/70 = 1.000 | 1.000 (1) | 0.983 (1) | 1.000 (1) | 10 / 0 | 0.792 (120) |
| | decision | 34/35 = 0.971 | 1.000 (1) | n/a | n/a | 17 / 0 | 0.744 (43) |

What the table shows:

- **Register.** Critical count is 0 for the frozen deterministic candidate and the matched runs. It is 4 for the Review 06 AI-EV1 run. Those 4 are the same `reference: wrong` items as in its model-disabled baseline AI-EV0: deterministic, from the Review 06 application, which predates the Review 07 guard.
- **Matched AI runs.** Their only automatic acceptances that the frozen labels count as wrong are the **F09** dispute: the cover on page 3 of `BBY006_1.PDF`, which carries another project's number (EP-30627/SS/EML/ 1293).
  - EV1 validated its identity and revision, which are the 2 "introduced AI errors".
  - EV2 validated its identity (1).
  - Whether that page belongs to the document is exactly what F09 asks a person to decide. These are pending, not AI errors and not AI successes.
- **Review 06 AI-EV1.** Its pending disputes are F01 (permit vs request number), F02 (page-3 Code B decision) and F09. Its other automatic-acceptance errors (4 of identity) are real under the frozen labels and stay counted in both views.
- **Raw observations.** The frozen deterministic pilot has 19 wrong or false identity observations. 7 are on *decide* pages (F07 ×3, F08, F09, F10). The remaining 12 include the confirm-only groups (F03, F04, F05, F06 and F11), which the Review 07 adjudication found to be raw-observation errors under undisputed labels. Raw observations are never accepted, so none of them reaches the register.

## 3. Pending disputes, by group (frozen labels)

| Group | Run | Field | Read | Frozen label | State | Frozen outcome |
|---|---|---|---|---|---|---|
| F07 ×3 | r7-det9 pilot | identity | K&A-WTRAN-017671 / -000913 / -020525 | TAVC-TRANSMIT-… | observed | wrong |
| F08 | r7-det9 pilot | identity, revision | EP-26369/SS/FA/101, 01 | (no component) | observed | fp |
| F09 | r7-det9 pilot, matched det9 / EV1 / EV2, r6 EV1 | identity, revision | EP-30627/SS/EML/ 1293, 00 | (no component) | observed; **validated** in EV1 (both) and EV2 (identity) | fp |
| F10 | r7-det9 pilot | identity | 10789-CSCEC-OUT-L0 | L0749 | observed | wrong |
| F12 | r7-det9 holdout | identity | ICDS-DOC-01943 | D15015-0200S-FS-EL-MS-0022 | observed | wrong |
| F13 | r7-det9 holdout | identity | BSS/AE/ALARABIA/170315-047 | (no component) | observed | fp |
| F01 | r6 AI-EV1 | identity | B2312982 | REQ-2387569 | **validated** | wrong |
| F02 | r6 AI-EV1 | decision; identity | ANN; 25H-AAEM-SD-EL | (no decision on p3); 25H-AAEM-SD-ELEC-FA-B1-003A | **validated**; held | fp; held_wrong |

Until the owner or an appointed reviewer settles these groups (labels v3), both views stay reported. A settled group moves into the frozen view with its human answer.

## 4. M2 accuracy remains blocked

Nothing in this review changes accuracy. These are correction-only changes: lifecycle, context, ledger and heading policy.

- **Recovery is below the 90% target** on every run and field above (B-1). The frozen deterministic pilot reaches identity 0.672, revision 0.710 and decision 0.325.
- **Human truth (B-3) is not available.** The packet is prepared but not reviewed, and the reviewer appointment is pending.
- **Project-model permission (B-4) remains as recorded.** It covers 29076, 30088 and 30784 only.
