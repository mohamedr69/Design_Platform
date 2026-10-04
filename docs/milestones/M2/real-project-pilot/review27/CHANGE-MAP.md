# Change map — Review 27 correction

No application, harness, ledger, scorer or stop-policy file changed. Everything new sits in `C:/t/iso/work/r2x/r27/` and this package. The superseded artifacts are untouched: review26, declaration v1 `aec4d4df…`, labels r26.1 (manifest `b29d93d1…`) and the R21 skeletons.

| New file | From | Purpose |
|---|---|---|
| `labels-r26.2/R26.2-*.json`, `LABEL-MANIFEST.r26.2.json` | r26.1 + the reviewer's rulings (`labels_r26_2.py`) | the frozen label version with independent AI source-review provenance |
| `labels-r26.2/R26.2-CHANGES.json` | — | field-level diff r26.1 → r26.2 with each ruling |
| `declaration/FINAL-DECLARATION.v2.json` | `declare_final_v2.py` (derived from review26's `declare_final.py`) | rebinds labels r26.2 and the review artifacts; adds `ledger.limit_semantics` and `supersedes`; scopes, limits and caps identical to v1 |
| `evidence/ROI-POPULATION.json` | `roi_population_r27.py` | the frozen drawing-sheet predicate on every in-scope page |
| `evidence/RESCORE-DELTA.json`, `evidence/rescore/` | the frozen v4 scorer on the review26 preflight runs with declaration v2 | the rebinding changes no scored value |
| BUDGET-PROPOSAL, DECISION-CARD, OWNER-CLAIMS-DIFF, LABELS-SUMMARY, RUNBOOK, CORRECTION-REPORT, COMMANDS | review26 documents corrected | R27-01 and R27-02 |
| `scripts/` | — | `labels_r26_2.py`, `declare_final_v2.py`, `roi_population_r27.py`, `bindings_r27.py`, `package_r27.py`, `verify_r27_package.py`, `append_response_r27.py` |
