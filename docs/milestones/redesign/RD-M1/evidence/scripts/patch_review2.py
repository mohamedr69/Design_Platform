"""Apply independent-review round 2 notes (producer edits). Writes into the package: do not re-run."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = sys.argv[1]


def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (os.path.basename(path), a[:80])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s)


patch(os.path.join(HERE, "findings.py"), [
    ("Likely reason it was still running in the copy: the DB was copied between the Apply's output commit "
     "(12:55:35) and the job finishing (PC-A sync worker last heartbeat 12:55:33 - independent review).",
     "Likely reason it was still running in the copy: the PC-A IFC worker running job 119 last heartbeat at 12:55:27 UTC "
     "(background_workers: current_job_id 119, stopped_at NULL); the output was committed at 12:55:35 and the job row was never "
     "finished before the DB was copied (independent review round 2, verified by the producer in the snapshot)."),
    ("(service.py:385-387 comment)", "(service.py:381-393 comment block)"),
])

patch(os.path.join(PKG, "REPRODUCTION-RUNBOOK.md"), [
    ("`invisible_flag.py` holds an absolute DXF path.",
     "`invisible_flag.py` holds an absolute DXF path. **Do not run** `build_evidence.py`, `findings.py`, `package_check.py`, "
     "`patch_findings_review1.py`, `patch_docs_review1.py` or `patch_review2.py` against the package: they are the producer's "
     "package-writing tools, kept as provenance."),
])

patch(os.path.join(PKG, "INDEPENDENT-REVIEW.md"), [
    ("| S:385-387 drift | The F007 cause text cites the comment loosely (\"service.py:385-387 comment\"); the comment runs 381-393. Left as is, noted here. |",
     "| S:385-387 drift | Corrected in round 2 to \"service.py:381-393 comment block\". |"),
    ("## Round 2\n\nRecorded below after the re-review.\n",
     """## Round 2 — reviewer's verdict and notes (summary of the reviewer's report)

**Verdict: ACCEPT WITH NOTES.**

| Check | Reviewer result |
|---|---|
| (1) The 7 required changes | All PASS. The round-1 non-blocking notes (WAL wording, T0 timing, F002/F017 wording, folder name) were also addressed. |
| (2) F032–F035 against the code | PASS. All line references are correct and the severities are reasonable; F032 is correctly marked confirmed by code, not reproduced. |
| (3) Conclusion 7 / F006 | PASS: no longer overclaims. |
| (4) No new errors | PASS. 77 manifest entries match on disk (9,018,537 B); 26 image hashes match E17; E01 line 53 is the first PC-A CT2 insert; counts agree (35 = 2/9/18/6); the §5 stage table lists all 35 IDs once. |
| (5) git status / non-mutation | PASS. The only new entries are the 78 package files; a fresh re-hash shows 740/740 code files and 1,867/1,867 upload files unchanged, and only `worker-g.stderr.log` changed in the outer repo; the mtime scan is clean. |

The reviewer's non-blocking notes, and what the producer did:

| Note | Action |
|---|---|
| 1. F017's reason cited the PC-A *sync* worker's heartbeat. Better evidence: the IFC worker running job 119 last heartbeat at 12:55:27 (`current_job_id` 119, `stopped_at` NULL). | F017 reworded; the producer verified it in the snapshot (`background_workers`: heartbeat 2026-10-02 12:55:27.776317, `current_job_id` 119, `stopped_at` NULL). |
| 2. F007 cites `service.py:385-387`; the comment spans about 381–393. | Corrected to `381-393`. |
| 3. Record round 2 here. | This section. |
| 4. The patch scripts write into the package. | The runbook now lists every package-writing script as "do not run". |

No further review round was requested. Round-2 edits were limited to the four notes above; `PACKAGE-CHECK.json` was regenerated afterwards.
"""),
])

patch(os.path.join(PKG, "RD-M1-REPORT.md"), [
    ("Its report is reproduced verbatim in `INDEPENDENT-REVIEW.md`, followed by the producer's change log. The producer does not approve this package; acceptance rests with the re-review.",
     "Its report is reproduced verbatim in `INDEPENDENT-REVIEW.md`, followed by the producer's change log. **Round 2** (same reviewer) "
     "returned **ACCEPT WITH NOTES**: all 7 required changes PASS, F032–F035 verified against code, no new errors, and git status and "
     "non-mutation re-verified. Its 4 non-blocking notes were applied (see `INDEPENDENT-REVIEW.md`). The producer does not approve this package."),
])
print("round-2 notes applied")
