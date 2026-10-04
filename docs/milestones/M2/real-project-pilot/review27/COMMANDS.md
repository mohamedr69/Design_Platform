# Exact commands and exit codes (Review 27 correction)

Interpreter `ep-platform/backend/venv/Scripts/python` (3.12); `PYTHONIOENCODING=utf-8`, `TEMP=TMP=C:/t/iso/tmp`; cwd `C:/t/iso/work/r2x/r27` unless stated. No provider or model request.

| Step | Command | Exit | Result |
|---|---|---|---|
| ROI population | `python roi_population_r27.py` | 0 | 42 in-scope pages, 19 drawing-sized; crop-eligible decision pages D16, D17, D18 |
| Labels r26.2 | `python labels_r26_2.py` | 0 | 4 ruled changes; document-level uncertainty unchanged; manifest `ed3c88e4…` |
| r26.1 → r26.2 diff | inline comparison | 0 | only D05.stage_printed, D17.decision_actor and actor_attribution, D19.decision_literal and decision_normalization; register values identical |
| Declaration v2 | `python declare_final_v2.py` | 0 | `FINAL-DECLARATION.v2.json` `6c0189b3…` |
| v1 → v2 diff | inline comparison | 0 | 39 changed leaf fields (labels, review bindings, `supersedes`, `limit_semantics`, name, time, `harness_dir`, workload note); scope limits and caps identical |
| Re-score under v2 (cwd `C:/t/iso/work/r2x/review25/harness-v4.3`) | `AI_ENABLED=false python score_arms_v4.py --declaration …/r27/FINAL-DECLARATION.v2.json --declaration-sha 6c0189b3… --runs C:/t/r2x/dry-runs/r26-preflight/runs --tags A=r26dry-A,L1=r26dry-L1,L2=r26dry-L2,L3=r26dry-L3,L4=r26dry-L4 --out …/r27/rescore` | 0 | identical recovery, coverage and eligibility to review26 for every arm |
| Bindings | `python bindings_r27.py` | 0 | `bindings/SOURCE-BINDINGS.json` |
| Package and check | `python package_r27.py`; `python verify_r27_package.py` | 0 / 0 | `evidence/PACKAGE-CHECK.json` `ok: true` |
| Response | `python append_response_r27.py e621fa7eb388b01e652bacf8ee78369b306609fff9b7b1412d0f807d1dfa7e62` | 0 | appended to the file as found; prefix byte-identical |

Not run: application or full test suites, because no application or harness file changed. The existing accepted results are reused.
