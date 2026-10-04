# FI-P1 r2: independent review 1 (of CORRECTION-R2.md) and dispositions

**Reviewer.** A fresh-context Opus agent with no part in writing r2. Read-only: code, a `mode=ro` look at the live database, a stat-only folder listing. No model calls.

**Verdict as delivered.**
- **Part A: FAIL.** Stage 0.1 must not be implemented as written.
- **Parts B/C:** mostly resolved, but W-4/W-5 are not sound yet.

**Orchestrator verification.**
- EP-30880's `IFC/Architectural` folder is empty (C).
- Gate Barrier ratio 1.43 (C).
- redesign/service.py:510 and draftsman_assignment.py:103 consume `build()["rows"]` (C).

| # | Sev. | Finding (short) | Disposition (r3 clause) |
|---|---|---|---|
| 1 | critical | `fa_ifc`/SCHED not covered by folder states; EP-30880's only read source would become `stale(folder_missing)` and freeze the snapshot | Accepted: S1, S4.1 F-events, S4.2 tables; T-04, T-05, T-21 |
| 2 | critical | `primary=published` could hide legitimate change for ever; no engineer path out | Accepted: S7 auto-advance A4 retirement, `publish-current`; T-07, T-10, T-11, T-12 |
| 3 | critical | A frozen `build()` output drops later decisions and manual items | Accepted: S7 the snapshot holds evidence; both views built with live decisions; equality by digest; T-13 |
| 4 | major | No GET-time currency check | Accepted: S8.1; T-24 |
| 5 | major | Legacy `coverage.status` would count stale as Received; `return saved` not removed | Accepted: S9; T-03, T-23 |
| 6 | major | Null totals break consumers | Accepted: S8.3 `totals_known`, numbers stay numeric; T-22, T-26 |
| 7 | major | The Stage-0 single-read of duplicates loses AHU/FAHU and orphans decisions | Accepted: S5 information only; T-20 |
| 8 | major | No recovery path for not-synced files | Accepted: S6; T-17, T-18 |
| 9 | major | Redesign/draftsman act on unverified rows silently | Accepted: S10; T-25 |
| 10 | major | Transition table not total, no precedence, swallowed listing errors | Accepted: S4.1 precedence, unsupported/never-scanned rows, `listing_failed`; T-19, T-22 |
| 11 | minor | Seeding and compare-and-set semantics ambiguous | Accepted: S7 one-time seeding in the migration, no `generation` bump; only scan/publish bump; T-14, T-15 |
| 12 | minor | The primary switch was package-level | Accepted: S8.2 row 4, per source |
| 13 | minor | Ignore list | Accepted: S3.4; T-27 |
| 14 | major | W-5 candidates too broad (`fa_ifc`, ACS) | Accepted: S13 W-5 context rule |
| 15 | major | W-5 does not settle the reference case | Accepted: S13 assignment margin (5.16 m, both settle); T-W19 |
| 16 | major | W-5 fallback, identity across drawings, actions per role | Accepted: S13 held fallback, per (floor, role) comparison, actions |
| 17 | major | W-4 equal counts on unaligned floors under-count | Accepted: S13 W-4 alignment per drawing pair; unaligned equal counts held |
| 18 | minor | n = 150 is not enough | Accepted: S13 W-N 210 |
| 19 | minor | Test ids without content, FP1-before-FP3, the budget cap override, the W-BASE commit, an inverted ratio | Accepted: S13 #19 |
| 20 | minor | CASES citations | Accepted: S13 #20 |

**Next.** CORRECTION-R3.md goes to a second, fresh independent review. Stage 0.1 is implemented only if it passes.
