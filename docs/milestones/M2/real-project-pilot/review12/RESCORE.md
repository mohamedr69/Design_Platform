# M2 Review 12: re-score of the 33 stored runs

- **Reader and evaluator:** reader `.7` with evaluator `.9` (unchanged), imported from the frozen worktree `C:/t/iso/frozen-r12` (`3d5607d`).
- **Script:** [`evidence/rescore/rescore_r12.py`](evidence/rescore/rescore_r12.py), derived from Review 11's `rescore_r11.py` by `make_rescore_r12.py`, with the same runs, declared AI contexts and negative controls.
- **Baseline:** the Review 11 results (reader `.6`, `C:/t/iso/work/r11/eval9-reader6`). Those files were hashed before and after the run and are unchanged.
- **No model call.**

## Result

- **All 33 scored runs are identical to Review 11,** and the 4 negative controls are unchanged. `r6-det7-pilot-promoted` still has no stored output.
- **The association counts in the AI runs are identical too** ([`ASSOCIATIONS.json`](evidence/rescore/ASSOCIATIONS.json)):
  - matched EV1: 3 decisions `current`, 3 `by_target`, 18 revisions `not_recorded`;
  - matched EV2: 3 `current`, 2 `by_target`, 15 `not_recorded`;
  - Review 06 runs: all `not_recorded`.

## What this does and does not show

- **The stored runs are single-attempt.** Every stored run was one attempt per document, with reliable, unique order. Reconstruction therefore selects the same (only) entry either way, and nothing changes.
- **It does not validate repeated-processing safety.** Stored single-attempt results say nothing about safety across repeated processing. That is what the synthetic persisted tests and the reviewer's probes cover.
- **No accuracy figure is claimed or changed.**
