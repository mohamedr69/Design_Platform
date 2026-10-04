# Commands (all offline; no model request)

The environment for every Python command is `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`, and no `AI_EVIDENCE_*` variable unless a step sets one. The interpreter is `ep-platform/backend/venv/Scripts/python`. The working folder is `C:/t/iso/work/r2x/r29` unless stated otherwise.

| Step | Command | Result |
|---|---|---|
| Reproduce the defects from the frozen stored outputs | `python repro_dump.py > repro/STORED-EVIDENCE-DUMP.txt` | [repro/](repro/STORED-EVIDENCE-DUMP.txt) |
| Freeze the contracts before code | `logs/CONTRACT-FREEZE.json`, then revisions R1 and R2 | [contracts/](contracts/CONTRACT-FREEZE.json) |
| Isolated candidate tree | `git clone C:/t/iso/cand-ai4 C:/t/iso/cand-r29`, then `git checkout -b r29-candidate 719e8de` and `git config core.autocrlf false` | byte-identical to `cand-ai4` before the patch |
| Apply the change | `python patch/apply_patch.py` (13 counted edits) and `python patch/make_eval6.py` | `evidence_reader.py`; `scripts/m2_eval6.py` |
| Review 29 tests | `python -m pytest -q tests/test_r29_*.py -p no:cacheprovider` (cwd `cand-r29/backend`) | in the focused run |
| Offline replay | `bash rerun_replays_final.sh`, which runs `run_all_replays.sh` (24 replays: 4 arms × {off, IG, CA, DR, PA, ALL}), `analyze_replays.py` and `new_acceptances.py` | [replay/](replay/REPLAY-ANALYSIS.json) |
| One replay | `python replay_arm.py <L1..L4> <off\|IG\|CA\|DR\|PA\|ALL>` | `C:/t/r2x/r29-replay/<arm>-<config>/out/{rows,REPLAY}.json` |
| Flags-off fidelity | `python compare_fidelity.py <arm>` | [replay/FIDELITY-L1.json](replay/FIDELITY-L1.json) |
| Score one set of rows | `python score_replay.py <rows.json> <policy> <arm> <9\|10> <out.json>` | `replay/scores/` |
| Full suite, candidate and baseline | `bash run_full_suites.sh` (candidate `a4ce6a3`, then baseline `3d5607d`) and `bash run_final_suites.sh` (final candidate full suite and focused suites) | [tests/](tests/FAILURE-COMPARISON.json) |
| Failure comparison | `python failure_compare.py logs/FULL-baseline.xml logs/FULL-final-candidate.xml` | [tests/FAILURE-COMPARISON.json](tests/FAILURE-COMPARISON.json) |
| Package and check | `python package_r29.py`, then `python verify_r29_package.py` | [evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json) |
