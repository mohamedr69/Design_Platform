# Independent verification 01 — M2 refresh package

Verifier: ep-verifier role (Opus, read-only), 6 October 2026, on commit 285857c (code at 771001e).

**Verdict: CHANGES REQUIRED.** Nothing in the package treats a historical finding as fixed; structural checks pass; every sampled classification (16 of 35) and candidate (11 of 22) holds against the code; the verifier re-ran the seven suites on a `git archive 771001e backend` copy and obtained 116 passed in 158.90 s with test ids identical to the committed JUnit file. Three record defects were required to be fixed:

- C1. `evidence/M2R-SOURCE-HASHES.json` claimed to cover every cited file but missed seven cited in the records' own cells (core/config.py, compliance/assist.py, services/jobs.py, ai/provider.py, ai/project_policy.py, services/project_deletion.py, tests/test_sync_worker.py) and three S7-cited files (models.py, tests/conftest.py, tests/test_worker_runtime.py). Fixed: all ten added, file_count 93, note reworded, test-output hashes added.
- C2. The acceptance record said the test log was in evidence; `redesign-suites.log` was gitignored and uncommitted. Fixed: force-added, wording corrected.
- C3. §2 pointed at section 6 for the verdict; it is section 5. Fixed.

Notes applied: N1 (F027 scope caveat), N2 (F028 basis reworded), N3 (line offsets F002 1550→1551, F008 947-950→952, C10/S08 walls.py 23-24→25-26), N4 (file-delta scope stated over S7's 54 files and over the full manifest), N5 (M11 secondary owner on F017, F032), N6 (compliance baseline stated outside this refresh's scope). N7 needed no change.

The verifier's working notes are the other files in this folder; its full report is `REPORT.md`.
