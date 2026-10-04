# M2 Review 10: stored outputs re-scored under evaluator .9

- **Evaluator:** `m2-pilot-eval-2026-09-29.9` with reader `.5`, imported from the frozen worktree `C:/t/iso/frozen-r10` (`a34d3f8`). The versions were frozen before this scoring.
- **Script:** [`evidence/rescore/rescore9.py`](evidence/rescore/rescore9.py), derived from Review 09's `rescore8.py` by `make_rescore9.py`: the same runs, declared AI contexts and negative controls.
- **Baseline:** each run's evaluator .8 result (`C:/t/iso/work/r9/eval8`). Those files were hashed before and after the run and are unchanged. They are kept, with the earlier .7 and .6 results, as history.
- **The comparison** removes the association metadata carried on judgements (`target`, `association`, `target_revision`, `context_identity`) from both sides, so that the scoring itself is compared.
- **No model call, and no new run.**

## Result

| | Runs | Compared with .8 |
|---|---|---|
| Scored runs | 33 | **Totals identical in all 33.** Documents identical in 31. |
| Matched AI-EV1 | 1 | Totals identical; 3 documents differ only in the **association route** of one decision each |
| Matched AI-EV2 | 1 | Totals identical; 2 documents differ in the same way |
| `r6-det7-pilot-promoted` | — | no stored output, as before |
| Negative controls (wrong variant, wrong profile, undeclared legacy profile) | 4 | unchanged: AI evidence `unavailable`, none scored |

**The five changed documents.** Each carries one decision:

| Run | Document (end) | Page | Decision | Outcome (.8 → .9) | Association (.8 → .9) | Route |
|---|---|---|---|---|---|---|
| matched AI-EV1 | `…Mechanical Floor Plan - Fire Alarm Layout.pdf` | 2 | ANN (held) | `held_correct` → `held_correct` | `current` → `by_target` | `single_component` → `target` |
| matched AI-EV1 | `…ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf` | 2 | rejected (held) | `held_correct` → `held_correct` | `current` → `by_target` | same |
| matched AI-EV1 | `…25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | 1 | ANN (validated) | `correct` → `correct` | `current` → `by_target` | same |
| matched AI-EV2 | `…ICC-DLRC-SPM-SD-MEP-FA-0042-01.pdf` | 2 | rejected (held) | `held_correct` → `held_correct` | `current` → `by_target` | same |
| matched AI-EV2 | `…25H-S202-NCC-SD-MEP-ELE-FA-047_Code B.pdf` | 1 | ANN (held) | `held_correct` → `held_correct` | `current` → `by_target` | same |

**Why these five changed (rule 11).**
- On each page, the AI identity is a `candidate`, not validated, with the same literal as the decision's recorded target.
- Evaluator .8 treated that candidate as the component's current identity (`current`). Evaluator .9 does not accept an association on a non-established anchor, so each decision is associated **only by its own recorded target**.
- That target names the same labelled component, so every outcome, count and total is unchanged.
- The one validated decision among them (EV1, FA-047, ANN `correct`) keeps its credit because its **own recorded target** matches the labelled component, not because of the candidate literal.

## Associations in the stored AI runs

[`ASSOCIATIONS.json`](evidence/rescore/ASSOCIATIONS.json):

| Run | Decisions | Revisions |
|---|---|---|
| matched AI-EV1 | 3 `current`, 3 `by_target` | 18 `not_recorded` |
| matched AI-EV2 | 3 `current`, 2 `by_target` | 15 `not_recorded` |
| Review 06 AI-EV1, eligible | 14 `not_recorded` | 41 `not_recorded` |
| Review 06 AI-EV1, EP-29076 | 10 `not_recorded` | 27 `not_recorded` |
| Review 06 AI-EV2, EP-29076 | 10 `not_recorded` | 39 `not_recorded` |

**No stored fact is held.** Every stored run was a single attempt per document, so every targetless fact's recorded context is its component's current identity. They are `not_recorded` and grouped exactly as before: the supported compatibility behaviour, with no indiscriminate holding of legacy data.

**What the defects touched.** The R10-01 defects are demonstrated by the regression tests and the reviewer's probes. They were **not exercised** by the stored real-model outputs, which contain no mixed-attempt states. The accuracy figures and blockers reported in Reviews 08 and 09 stand unchanged.
