# Evidence: ORCH-053 AI policy remediation

Interpreter `ep-platform/backend/venv/Scripts/python.exe -B -m pytest -p no:cacheprovider --basetemp=C:/t/tmp/sec/...`, TMP under `C:/t/tmp/sec` (deleted after). No provider request, no `claude` process, no network (the harness blocks and counts all three: 0, 0, 0 for application-built requests).

| File | What |
|---|---|
| `full-suite-before.*` | base 94af35a, untouched: 1926 tests, 1890 passed, 1 failed (`test_proposed_materials` part catalogue, pre-existing), 35 skipped; identical by name and outcome to ORCH-047 (`C:/t/tmp/owner-work/merged-full.xml`) |
| `full-suite-after.*` | the branch before the last test fix: 1959 tests, 1920 passed, 4 failed, 35 skipped. Three were `test_render_bounds` unit tests calling `visual.check(None, ...)` with no database (now fail closed); fixed in the test (the stand-in project is allowed), see `render-bounds-after-fix.xml` (10 passed). Net: 1959 / 1923 / 1 (the same pre-existing failure) / 35 |
| `full-suite-final.*` | the committed branch 8a47d7c: 1959 tests, 1923 passed, 1 failed (the same pre-existing failure), 35 skipped |
| `full-suite-compare.json`, `full-suite-compare-final.json` | by-name comparison ORCH-047 vs before vs after / final: no test changed state; 33 new, all passing |
| `merge-check.txt` | dry-run merge against the moved `roadmap/u2`: clean |
| `forced-blocked-harness.json` | the ORCH-051 harness (`tests/ai_policy_harness.py`), every project forced `blocked`, 301 tests of 19 AI-path modules: content-free counts |
| `harness-*.txt` | the child runs' failing test names (expected in forced-blocked mode: the tests assert answers that are now refused) |
| `static-guard-on-base.log` | `tests/test_ai_policy_guard.py` on the base code: 4 of 6 fail (no central gate; ungated sends in `pipeline.ask`, `ai_symbol_review._call`, `drawing_ai_review._ask`; no entry-point gates) |

Forced-blocked harness (application-built requests / inputs given to scripted providers / real dispatches of app requests):

- before (base code): 403 requests (335 image parts) on blocked projects, 49 scripted-provider inputs, 0 real; by task: drawing review 90, FA orchestrator 188, FA visual 68, FA findings 29, preparation 6, IFC symbol 21, compliance `answer_clauses` 1.
- after (branch): 0 / 0 / 0 across all 301 tests.
- control (branch, nothing forced): 469 requests, 110 inputs, 0 real: the harness sees sends, so the zero is not blindness. The control's 11 failures are provider unit tests whose fake transports the harness blocks by design.
