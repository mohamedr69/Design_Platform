# Dry run of the B / C / R / P contract (R31-05): no model request

**Command:** `python scripts/harness/dry_run.py t3`. The report is [dry-run/DRY-RUN-REPORT.json](dry-run/DRY-RUN-REPORT.json) (sha256 `ac60194c…3a63`), and the scorer output is [dry-run/SCORE-BCR.json](dry-run/SCORE-BCR.json).

**Sample:** the already-staged four-arm sample, with its frozen r26.2 labels. No new document was opened or rendered.

**Safety:**
- **Live providers blocked:** every live provider class (API, OpenAI, Claude Code CLI) was replaced by one that raises, and no attempt was recorded.
- **No CLI on the path:** the subprocesses ran with a PATH that does not contain the CLI.
- **Ledger unchanged:** 483 entries and 17 scopes before and after.

## Lanes

| Lane | What ran | Provider beneath the capture store |
|---|---|---|
| B | the frozen final-A run, accepted path with the evidence reader off (4 requests in the four-arm ledger) | none, already run |
| C | candidate `a8aaced`, L3 switch set plus IG, CA, DR and PA, on a fresh copy of B | replay of the frozen L3 captures. An unrecorded request fails as `unrecorded` and is never invented. L3's pre-dispatch refusals are reproduced as recorded. |
| R | the same candidate with the L3 switch set, on a fresh copy of B | lane R of the same store, served C's capture by content key |
| P | the seeded 15% probe of C's answered dispatches | the same replay |

## Results of the contract checks

1. **Population gate first.**
   - **Counts:** identity 16, revision 16, decision **6**, from resolved, independently reviewed r26.2 documents.
   - **Outcome:** **PREPARATION BLOCKED**, because no extension exists for this frozen sample. **A live run would stop here without any dispatch.**
   - Everything below ran in **exercise mode only**, and the scorer marks its output "not a result".
2. **C-from-B state check:** passed for C, R and the resume sandbox.
   - B's file hash equals the hash recorded after the four-arm run, `2161297e…41b6`.
   - The logical content is equal.
   - There is no C-policy evidence and no evidence cache row.
3. **Capture store:**

   | Measure | Count |
   |---|---|
   | Lane C rows | 76 (63 answered; 13 failed: 3 recorded L3 timeouts and 10 unrecorded) |
   | Lane P rows | 9 |
   | Duplicate bound keys | 0 |
   | R requests served from C's capture | **66** of 66 (R dispatched nothing of its own) |
   | R answers served to C | 0 |
   | B or C served from P | 0 |
4. **Transparency:** the evidence observations of C and of R are **identical, document for document,** to the Review 29 replays of the same candidate (`L3-ALL` and `L3-off`). The capture-store layer changes no answer.
5. **Probe:** 9 of the 63 answered C dispatches were re-sent in lane P. All 9 agree, which is expected because the dry run's inner provider is a replay. Live disagreement rates come only from a live run.
6. **Resume drill:**
   - **Setup:** C was run again over a copy of the capture with one dispatch reset to RESERVED, as if the process died after sending it.
   - **Result:** **0** dispatches to the inner provider. The reserved request was served once as `interrupted_charged` and never re-sent. There were 74 same-fingerprint serves, and the row count stayed at 85.
7. **Stop controller:** no lane stopped, and the comparison stayed PENDING. There was no critical acceptance in any lane, and the 3 recorded timeouts were not consecutive. The scenarios that *do* stop are covered by `tests/harness-pure.xml` (stop rules).
8. **Scorer:** `score_bcr.evaluate` ran end to end with caps B 240 and C 240. For comparison, the check with B 16 and C 240 returns "not applicable: unequal caps (R31-03)".

## What the exercise figures are not

`SCORE-BCR.json` contains exercise figures:
- requests B 4, C 80;
- decision coverage B 0, C 7, R 9.

They are **not results**:
- the population gate refused dispatch;
- the labels are exploration-project labels, with templates exposed;
- C made 10 requests the frozen L3 run never recorded, so its decision coverage is understated.

They show that every stage executes and every gate is computed. They say nothing about the candidate's accuracy.
