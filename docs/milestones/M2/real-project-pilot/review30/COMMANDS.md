# Commands (Review 30): offline, with no model request and no document content

Interpreter: `ep-platform/backend/venv/Scripts/python`. Working folder: `C:/t/iso/work/r2x/r30`.

| Step | Command | Result |
|---|---|---|
| Projects referenced by M1 and M2 (exclusion list) | inline scan of `docs/milestones/**` and both backend test trees for `EP-nnnn` | [cohort/M2-USED-PROJECTS.json](cohort/M2-USED-PROJECTS.json) |
| Fresh-project candidates, metadata only | `python select_fresh_projects.py` | [cohort/FRESH-PROJECT-CANDIDATES.json](cohort/FRESH-PROJECT-CANDIDATES.json) |
| r26.2 field prevalence | inline count over the frozen r26.2 labels | [field-population/R26-FIELD-RATES.json](field-population/R26-FIELD-RATES.json) |
| Feasibility | `python feasibility.py` | [field-population/FIELD-POPULATION.json](field-population/FIELD-POPULATION.json) |
| Draft declaration | `python make_draft_declaration.py` | [DRAFT-DECLARATION.json](DRAFT-DECLARATION.json) |
| Checker tests | `python -m pytest -q test_r30_checks.py -p no:cacheprovider --junitxml=CHECKER-TESTS.xml` | [tests/CHECKER-TESTS.xml](tests/CHECKER-TESTS.xml) |
| Package and check | `python package_r30.py`, then `python verify_r30_package.py` | [evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json) |
