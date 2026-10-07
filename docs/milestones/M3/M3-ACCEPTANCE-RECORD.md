# M3 — acceptance record

Milestone: **M3 — Ownership, Access & Memory Policy** (unified roadmap, prerequisites M1 and M2).
Date: 7 October 2026. Repository: `G:\dev (2)\dev\ep-platform-merged\ep-platform`, branch `claude/upbeat-lovelace-sa9j3w` at commit **0568623** (working tree carrying the M3 records of this day, uncommitted at the time of writing). Documentation and owner-authorised read-only inspection only: no application code, test, migration, configuration or evidence folder was changed for M3; the live database was opened read-only once and nothing was written to it.

Prepared by the orchestrator from the owner's decisions of 7 October 2026 and the two independent reviews of the same day. **Owner acceptance: ACCEPTED by Mohamed Elazab (owner, mohamedr69) on 2026-10-07** (section 9).

Task statement, as the roadmap's section 14 requires:

| Element | Value |
|---|---|
| Milestone | M3 |
| Bounded scope | Record the ownership, access and memory policy contract: every owner decision the roadmap reserves for M3 (Pack Table A, OD-01..OD-19), the five memory decisions received on 7 October 2026 (OD-20..OD-24), the ratification of the M1 refresh's proposed and inherited owners (29 rows), the policy statements that need no owner choice (Table D), and what M3 leaves to later milestones. |
| Snapshot changed | None in code. Records under `docs/milestones/M3/`: [M3-DECISION-PACK.md](M3-DECISION-PACK.md), [M3-POLICY-CONTRACT-DRAFT.md](M3-POLICY-CONTRACT-DRAFT.md), [M3-M1-DELTA-RATIFICATION-2026-10-07.md](M3-M1-DELTA-RATIFICATION-2026-10-07.md), [M3-INSPECTIONS-2026-10-07.md](M3-INSPECTIONS-2026-10-07.md), this record. |
| Completion gate (roadmap M3 entry, verbatim) | "Align with refreshed M1: fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse. Recorded contract accepted before authoritative memory writes." |
| Evidence destination | `docs/milestones/M3/` and the session log `docs/SESSION-LOG-2026-10-07-windows.md` (rows 15-19). |

## 1. Gate subject → decision → record → remaining gap

| Gate subject | Settled by | Record | Remaining gap (downstream, not M3's) |
|---|---|---|---|
| Fact ownership | P-01..P-03; Part C 29 rows ratified (C-5 re-assigned to the M7 assignment record by R-3; B-23 flagged as superseded by it); D1 the 17 SETTLED-GAP conflicts; Q-2 scope rule; Q-4 guards | Contract Part C, D1, D2; ratification record sections A-D | Guard implementation of G-01..G-04 and the 16 M3-tagged weaknesses belongs to M4 and M7 |
| Project access | OD-19 (b) central membership administered by `design_manager`; Q-1 engineering manager = `design_manager`, `admin` no engineering authority; P-24 capabilities with R-1 (role = authority level, membership = access scope, capabilities = actions) | Contract P-04, P-24, B-19; inspection section 2 (no scoping exists today, U-23 answered) | Membership table, central lookup, backfill with the design engineer of record: M7 and M14 |
| Critical confirmer | OD-18 (c) amended: per-project confirmer or `design_manager`; policy auto-confirmation on sufficiently authoritative verified evidence; AI confidence never authoritative; baseline critical classes, centrally configurable | Contract P-08, P-10, B-18 | The trust policy's versioned definition: M16 (D4-1) |
| Archive retention | OD-10 (c)(e)(h) states and setter; OD-11 (b)(e) no ordinary destruction of history, backups with retention; OD-15 (a) Apply never publishes to the archive | Contract B-10, B-11, B-15, P-15; ratification record PRJL rows | States, reopen path, archive-publication action: M7, M5 |
| Global promotion | OD-02 completed (automatic on configured criteria or manual by `design_manager`/confirmer, never the author alone; provenance; retirement on withdrawal); OD-03 (d); OD-12 (c); OD-13 (a) with sub-rules; OD-23, OD-24; P-25 (R-2 controls: the engine is the only authorised cross-project reader, disabled until the roadmap's promotion gates pass, criteria owned and versioned by `design_manager`, symbol library a governed exception with no AI-only entry) | Contract P-05, P-06, P-22, P-23, P-25, B-02, B-03, B-12, B-13 | Promotion engine, criteria, tests: M19, M21, M22, M23, M31; D4-3, D4-7 |
| Scoped revisions | OD-20 (P-19), P-11, P-12 with OD-01 (c) restricted | Contract A4, B-01 | Versioned approval-mapping configuration: M7; aggregates corrected: M28 inputs (RC-37) |
| Artifact reuse | P-13, P-14; OD-04 (a) every provider path honours the project policy, server-side-only reuse for a blocked project; Part C rows B-7..B-13 | Contract A5, B-04 | Enforcement on the drawing AI paths: M7, M12 (Delta #25) |

## 2. Exit gate assessment (orchestrator's reading; the verifier's verdicts are in section 6)

Every one of the seven subjects has a recorded decision with a deciding person, role and date, and a clause in the contract. The contract's Part B has 19 of 19 slots filled, Part C 29 of 29 rows ratified, Part D lists what M3 does not decide with an owner or a later decision for each (D1 17 rows, D2, D3 12 rows, D4 7 rows). The second independent review found no substantive conflict and all seven subjects settled. The gate's second sentence, "recorded contract accepted", is the owner's act and is pending (section 9). No authoritative memory write exists yet in the platform, so the ordering the gate requires is kept.

## 3. Snapshot and versions

Roadmap: `docs/UNIFIED_MASTER_ROADMAP.md` Revision U8 (its M3 status text and section 6 rows on OD-14 to OD-17 and the promoter predate these decisions and are to be updated at the next revision; the contract says that wording changes only on a verifier verdict, which now exists). Pack prepared at f4d8ca0; contract drafted at b0465ed; filled and reviewed at 0568623 plus the day's working tree. M1 refresh files: unmodified (verified by both reviews with `git status` and `git diff`).

## 4. Tests

None. M3 is a recorded contract; no test, code change, migration or live action is part of its evidence. The read-only inspections ran SQLite in `mode=ro` and static scans of the routers; results are in the inspection record.

## 5. How the work was done

1. The owner answered Pack open question 1 and all 19 Table A rows in the orchestrating session of 7 October 2026 (afternoon), one at a time for question 1, OD-19, OD-18 and OD-01, then the remaining rows together, each from a recommended option with its consequence stated; amendments are the decision. Filed in the Pack answer sheet and section 2b, and in the contract's Part B.
2. The owner then ratified all 29 Part C rows, scoped ratification to those rows, chose a separate dated ratification record, assigned guard implementation to M4 and M7, added the five Task One capability classes as capabilities, set the draftsman-assignment authority, and authorised three read-only inspections (Pack Q-2..Q-10).
3. First independent review (verifier role, read-only): CHANGES REQUIRED. The owner decided the three substantive findings the same evening (Pack R-1..R-3); the orchestrator resolved the clerical findings without new policy.
4. Second independent review: ACCEPT WITH NOTES. The fourteen clerical notes were resolved by the orchestrator without new policy; the one attribution question the verifier raised (the plan's "explicit promotion" sentence) is answered in P-25 from the orchestrator's own conflict statement to the owner, which named that sentence.
5. This record was then written. Nothing was committed by the session; committing is the owner's.

## 6. Independent review disposition

| Pass | Verdict | Substantive findings | Disposition |
|---|---|---|---|
| 1 (7 October 2026, afternoon; agent ac10212288563b782, Claude Opus, ep-verifier instructions) | CHANGES REQUIRED | S1 P-24 beyond the owner's words and role versus capability open; S2 automatic promotion unreconciled with isolation, PM-M0, the roadmap's test gate, criteria ownership and OD-13; S3 C-5 store owner | Owner decisions R-1, R-2, R-3 (Pack 2b); applied in P-24, P-25, Part C C-5. Twelve clerical findings resolved. |
| 2 (7 October 2026, evening; agent ad58cf1b5076c8368, same role and model) | ACCEPT WITH NOTES | none; S1-S3 recorded faithfully, no policy beyond the owner's words, seven subjects settled | Fourteen clerical notes resolved (status lines, P-04 wording "directly", stale pre-R-3 text, P-25 moved to its own section A10 with the A8 and P-23 notes updated, D4-7 added, Effect clause, line bases, Pack headers, inspection wording, attributions, D4-1 phrase, slot heading). |

Note on the verifier role: the clone's `.claude/agents` roster was not loaded in this session (started from the parent folder), so each pass ran as a general-purpose agent given the ep-verifier instructions verbatim, read-only, on the Opus model the roster prescribes.

## 7. Owner decisions still required

None for M3's gate. Items the reviews found undecided are each assigned (contract Part D4): the trust-policy threshold (M16), the "materially stronger" test (M19), the read-back of global links under isolation (M14, M21, M22), the candidate read while automatic promotion is disabled (M23, M31); D4-4, D4-5 and D4-6 were decided by R-3, R-2 and R-1.

Outside M3's gate, for the owner:
- Security: the seeded admin password setting is at its public code default (inspection section 3). The owner treats this as a separate security action outside the M3 gate; no value is recorded anywhere.
- The roadmap's next revision (U9) to carry the M3 decisions and this record's status; the owner's commit of the M3 records and of the unrelated uncommitted work in the tree.

## 8. Downstream implementation obligations recorded by M3 (not unresolved policy)

| Obligation | Milestone |
|---|---|
| Central project membership, lookup and backfill; capability table and check; audited membership changes | M7, M14 |
| Guards for G-01..G-04 and the 16 M3-tagged weaknesses | M4, M7 (by subsystem) |
| The eight groups of state-changing GET handlers (inspection section 2.2) moved to processors or explicit commands | M10 with M7 |
| Project AI policy enforced on every provider path, including the drawing paths and the Drawings Assistant | M7, M12 |
| Lifecycle states, archive-publication action, deletion and backup contract, shared-row protection | M7, M5 |
| Versioned approval-mapping configuration; Home and Drawings aggregates corrected or relabelled | M7, M28 |
| Promotion engine, criteria, provenance, tests; symbol-library version, access class and exception | M19, M21, M22, M23, M31, M12, M7 |
| Trust policy for critical-fact auto-confirmation; critical-class configuration | M16, M14 |

## 9. Acceptance

Readiness: both reviews are on record, no substantive finding is open, every gate subject is settled. **Accepted by the owner on 7 October 2026**; the contract is in force from that acceptance (contract Part E, Effect). The owner also accepted, as recorded under R-1, that a `design_manager` can add themselves to a project, audited.

| Element | Status |
|---|---|
| Contract accepted by the owner | ACCEPTED — Mohamed Elazab (owner, mohamedr69), 2026-10-07, by session message relayed by the orchestrator |
| Status wording in the roadmap and README | Roadmap revision U9 prepared on this record (uncommitted, for the owner's review) |
| Downstream implementation | Not started; M4 closure and M5 remain the next implementation tasks (roadmap section 14) |
