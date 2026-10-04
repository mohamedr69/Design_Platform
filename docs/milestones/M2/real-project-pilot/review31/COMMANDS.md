# Commands (Review 31)

Python is `C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python`. Set the environment to `PYTHONDONTWRITEBYTECODE=1 PYTHONIOENCODING=utf-8 TEMP=TMP=C:/t/iso/tmp`. None of these commands sends a model request.

| Purpose | Working directory | Command |
|---|---|---|
| Selector tests (4) | `scripts/` | `python -m pytest -q test_selector_core.py -p no:cacheprovider` |
| Stop-rule, state-check and scorer tests (8 + 5 + 13) | `scripts/harness/` | `python -m pytest -q test_stop_rules.py test_state_check.py test_score_bcr.py -p no:cacheprovider` |
| Capture-store tests (21) | `C:/t/iso/cand-r29/backend` (read-only use) | `PYTHONPATH=<package>/scripts/harness AI_ENABLED=false python -m pytest -q <package>/scripts/harness/test_capture_store.py -p no:cacheprovider --rootdir <package>/scripts/harness` |
| Metadata-only selection | the work folder `C:/t/iso/work/r2x/r31` | `python select_fresh_projects_r31.py`, then `python reconcile_r30_picks.py` |
| Feasibility | the work folder | `python feasibility_r31.py` |
| Dry run (needs the frozen four-arm runs and the candidate tree; about 4 min) | the work folder `harness/` | `python dry_run.py <new stamp>`. A stamp is never reused. |
| Binding manifest (written once) and draft declaration v2 | the work folder | `python make_bindings_r31.py`, then `python make_draft_declaration_v2.py` |
| Package check | any | `python scripts/verify_r31_package.py` |

**Rules:**
- The capture-store tests import the candidate's provider types read-only. The candidate tree must stay clean, and the checker verifies that it does.
- Outputs are always written by absolute path, never into a frozen tree.
