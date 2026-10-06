# Independent verification 01 — M1 refresh package

Verifier: ep-verifier role (Opus, read-only), 6 October 2026, on commits e6259de..36144e2 (code at 771001e).

**Verdict: CHANGES REQUIRED.** Structure, census and scope hold; 28 of 34 sampled code citations confirmed, 4 imprecise, 2 not confirmed. Seven documentation changes are required inside this folder, no code:

- C1. Delta §7: classify the 25 ownership conflicts against the accepted decisions D-01..D-15 (SETTLED-GAP / M3-OWNER-DECISION / NEW-PROPOSED).
- C2. Fill a target owner for the 79 CSV rows reading UNKNOWN (orchestrator's rule: inherit D-02/D-03/D-04/D-01/D-14, PROPOSED owner otherwise, M3-OWNER-DECISION where the roadmap reserves it).
- C3. Correct the false claim that `ComplianceStatement.version` is never written: `services/concurrency.py::_bump_version` (63-71) bumps it on every modifying flush; it is a concurrency counter, not an approved version.
- C4. Regenerate the source-hash file to cover files cited by abbreviation (about 212, not 130); fix `review/prepare.py` → `redesign/prepare.py` and `ifc/ai_symbol_review.py` → `ifc/services/ai_symbol_review.py`.
- C5. Settle the AI-policy point from code: `project_policy.allowed` is not consulted on drawing AI paths; compliance assist is gated.
- C6. Acceptance record §1: correct the drift split (100 with drift, 36 line-number only, 6 none, 2 not re-verified) and state which override-writer areas were not re-surveyed.
- C7. Minor line-reference and target fixes (CACHE.result_cache, RC-13, RC-58, WL.sd_required_scope).

`01-criteria.md` is what the verifier wrote down before reading the package; `02-results.md` is its full working record. The orchestrator confirmed the two code findings (C3, C5) directly before assigning the changes.
