# M2 Review 09: stored outputs re-scored under evaluator .8

- **Evaluator:** `m2-pilot-eval-2026-09-29.8`, imported from the frozen worktree `C:/t/iso/frozen-r9` (`689d95e`). The versions were frozen before this scoring.
- **Script:** [`evidence/rescore/rescore8.py`](evidence/rescore/rescore8.py). It is derived from Review 08's `rescore7.py` by `make_rescore8.py`: the same runs, the same declared AI contexts and the same negative controls.
- **Baseline:** each run's evaluator .7 result (`C:/t/iso/work/r8/eval7`). Those files were hashed before and after the run and are unchanged.
- **No model call, and no new run.**

## Result: no historical score changes

| Group | Runs | Compared with .7 |
|---|---|---|
| Runs with no AI stage: the deterministic runs of Reviews 05–07, the Review 06 AI-EV0 runs, and the matched model-disabled and AI-EV0 runs | 28 | identical |
| AI runs: Review 06 AI-EV1 (eligible and EP-29076), AI-EV2 (EP-29076); matched AI-EV1 and AI-EV2 | 5 | identical |
| **All scored runs** | **33** | **identical** once the two keys .8 adds to judgements (`target`, `association`) are set aside |
| `r6-det7-pilot-promoted` | — | no stored output, as in Reviews 07 and 08 |

The negative controls are unchanged. The AI evidence is `unavailable` in each, and none is scored:
- the Review 06 EV1 rows without the legacy-profile declaration;
- the same rows scored as EV2;
- the matched EV1 rows scored as EV2;
- the matched EV1 rows scored as `promoted`.

Summary: [`evidence/rescore/SUMMARY.json`](evidence/rescore/SUMMARY.json); log `eval8_run.log`.

## What .8 adds, and why nothing moved

Every AI decision and revision judgement now states its association ([`ASSOCIATIONS.json`](evidence/rescore/ASSOCIATIONS.json)):

| Run | Decisions | Revisions |
|---|---|---|
| matched AI-EV1 | 6 `current` | 18 `not_recorded` |
| matched AI-EV2 | 5 `current` | 15 `not_recorded` |
| Review 06 AI-EV1, eligible | 14 `not_recorded` | 41 `not_recorded` |
| Review 06 AI-EV1, EP-29076 | 10 `not_recorded` | 27 `not_recorded` |
| Review 06 AI-EV2, EP-29076 | 10 `not_recorded` | 39 `not_recorded` |

- **Every stored run was a single attempt per document.** No fact was retained across a changed identity or revision, so no `held:*` or `by_target` association occurs, and the grouping is what it was.
- **The Review 06 reader recorded no targets, and no reader before .4 recorded a revision target.** Those facts are `not_recorded`: grouped as before, with nothing invented.
- **Source identity (R9-03) changes nothing here.** Every stored AI envelope records the hash of the bytes it read, and it matches the row. The historical-binding mode was not needed and was not used.

So the R9-02 and R9-03 defects are real, and demonstrated by the regression tests and the reviewer's probes. They were **not exercised** by the stored real-model outputs. The Review 08 metrics stand as reported: frozen-label views, pending disputes and blockers are unchanged.

## BOQ heading policy (R9-04): stored readings replayed

**What the stored readings allow.**
- The stored Review 06 BOQ verifier results (`C:/t/r6/boq-ev1`, `boq-ev1b`) keep each blind reading's part, quantity and description, but not its heading flag or legibility.
- Only readings whose recorded reason names a heading can therefore be replayed without guessing: one row, stored in both runs.

**The replay.**
- Script: [`evidence/replay/replay_boq_headings.py`](evidence/replay/replay_boq_headings.py), result: [`replay-boq-headings.json`](evidence/replay/replay-boq-headings.json).
- It uses the prior policy (`frozen-r8`) and the candidate's (`frozen-r9`).
- Result: `conflict`, `disputed` under both. The reader carried an OCR-garbled part and quantity, so there is no change.

No other stored BOQ result can be re-validated honestly without the missing flags, and none is claimed.
