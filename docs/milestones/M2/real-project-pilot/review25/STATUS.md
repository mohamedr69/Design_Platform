# Status after the Review 25 correction task (2026-10-01)

Submission readiness is reported separately from milestone acceptance. Nothing here is self-approval.

1. **R24-01 remains corrected.** The original before- and after-stop-file probe was rerun on the frozen successor. Both cases resume with exit 4, 0 new requests and `stopped`, and 3 regressions passed. The runner is byte-identical to v4.2.
2. **R25-01 is corrected and ready for independent review.** Contradictory neutral results (`budget`, `cache_hit` or `none` with a failure outcome) now make the journal indeterminate. Resume then exits 5 with zero requests, writes no stop, leaves the saved state unchanged and records the refusal with its reason. Valid neutral results stay neutral, and all existing v4.2 journals load unchanged.
3. **Fresh tests on the frozen successor:**
   - submitted 62-test set: 62 passed (pytest exit 0);
   - R25 regressions: 32 passed (exit 0);
   - reviewer's neutral probe: 6 passed on v4.3, after 3 failed / 3 passed on v4.2;
   - original R24 provider probe: 3 passed.
   No application suite was run; no application file changed.
4. **No new accuracy evidence.** These are synthetic harness tests. Labels, extraction accuracy and the default variant remain unresolved.
5. **Budget:** no model call, no new model budget, no live run, and no new live scope. H-06 is complete at the recorded 128/150 original requests. **The 688-request proposal remains unapproved.**
6. **M2 remains CHANGES STILL REQUIRED.** No M3 and no default is adopted.
