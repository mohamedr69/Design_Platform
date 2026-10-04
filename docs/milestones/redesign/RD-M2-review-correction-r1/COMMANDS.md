# Commands and Validation

- Independent package review: all 68 submitted RD-M2 hashes recomputed, 0 mismatches.
- Focused: `pytest tests/test_redesign_apply.py tests/test_redesign.py -q -p no:cacheprovider --basetemp <isolated> --junitxml evidence/focused.xml`
- Focused result: 53 passed, exit 0.
- Full suite: 1,299 passed, 2 failed, 34 skipped, 1 deselected, 0 errors; the two failures match the RD-M2 baseline by test and message.

No model call, API call, live endpoint, database migration, service restart, commit or push was made.

