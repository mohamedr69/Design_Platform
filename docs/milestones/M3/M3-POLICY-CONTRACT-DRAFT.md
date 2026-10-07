# M3 policy contract — DRAFT

Milestone: **M3 - Ownership, Access & Memory Policy** (unified roadmap, prerequisites M1 and M2).
Date: 7 October 2026. Repository HEAD when written: `b0465ed9ba053b99aba13954e147d3ea0eb20f94` (`git rev-parse HEAD`).
Prepared by ep-scribe from the decision pack; filled by the orchestrator from the owner's answers of 7 October 2026; independently reviewed twice on 7 October 2026 (see Independent review at the end).

Status: **DRAFT, all slots filled: 5 owner decisions recorded (OD-20..OD-24) and all 19 Part B slots filled from the owner's answers of 7 October 2026 (afternoon; Pack sections 2 and 2b). Part C ratified by the owner 7 October 2026 (29 rows; C-5 store owner flagged). Independent review 7 October 2026: CHANGES REQUIRED; the three substantive items were decided by the owner the same evening (S1 in P-24, S2 in P-25, S3 in Part C row C-5) and the clerical findings resolved; second independent review 7 October 2026 (evening): ACCEPT WITH NOTES, notes resolved. ACCEPTED by the owner (Mohamed Elazab, mohamedr69) on 7 October 2026, [M3-ACCEPTANCE-RECORD.md](M3-ACCEPTANCE-RECORD.md): IN FORCE from that acceptance.** Every clause that depended on an owner decision now points to its Part B slot; the roadmap's interim positions stay in the Part B question table for the record (for example "approved as noted" does not count as final until recorded, roadmap section 6). The five decisions (owner session message of 7 October 2026, [Pack section 2a](M3-DECISION-PACK.md)) extend the Project Memory Master Plan and do not replace it. Accepted by the owner on 7 October 2026 (acceptance record); in force from that date.

## Sources

| Short name | Path | Used for |
|---|---|---|
| Pack | [M3-DECISION-PACK.md](M3-DECISION-PACK.md) (prepared 6 October 2026, HEAD f4d8ca0) | Table A (OD-01..OD-19, questions verbatim), Table B, Table C, Table D, sections 6 and 7 |
| UMR | [docs/UNIFIED_MASTER_ROADMAP.md](../../UNIFIED_MASTER_ROADMAP.md) | M3 entry and gate; sections 3, 4, 5, 6 |
| D-xx / G-xx | [M1-TARGET-OWNERSHIP-DECISIONS.md](../M1/M1-TARGET-OWNERSHIP-DECISIONS.md); [M1-ACCEPTANCE-REPORT.md](../M1/M1-ACCEPTANCE-REPORT.md) line 94 | Accepted decisions D-01..D-15; gap G-04 text |
| Delta | [M1R-DATA-OWNERSHIP-DELTA.md](../M1/refresh-2026-10-06/M1R-DATA-OWNERSHIP-DELTA.md) section 7 | The 17 SETTLED-GAP conflicts and their carried-to milestones |
| PM-M0 | [docs/milestones/project-memory/README.md](../project-memory/README.md) lines 41-55; [PROJECT_MEMORY_GAP_ASSESSMENT.md](../../PROJECT_MEMORY_GAP_ASSESSMENT.md) | Memory plan policy prerequisites |

Line-number basis: "UMR:nnn" is the line at Revision U5 as cited in the Pack. The current file is Revision U8; the section 3-5 rows cited here are at the same line numbers, section 6 rows after UMR:218 read 1 higher (the U8 OD-14 row), and the M3 entry gate is at line 320 (cited by the Pack as 312; 314 is now the M3 heading). The quoted phrases and section names are the stable locators.

How to use: Part A is final text once M3 is accepted. Part B has one slot per owner decision; the scribe fills only the slots. Part C records ratification. Part D lists what M3 does not decide. Part E states the gate and when the contract takes effect.

## Part A — Policy statements in force once M3 is accepted

Clauses P-01 to P-18 restate a row of Pack Table D (D-1..D-18), whose deciding text already exists; P-19 to P-23 record the owner decisions OD-20..OD-24 of 7 October 2026; P-24 records the owner's answer to Pack open question 6 (afternoon) and the S1 resolution (evening); P-25 records the S2 resolution (evening). No option is offered. Where a clause points to an owner decision, the question is in Part B and is not answered here.

### A1. Ownership and canonical owners

**P-01.** Existing domain owners stay canonical. Memory adds typed facts and event/evidence links and creates no independently editable duplicate store; source observations, classification, attribution, domain status, approved values and AI-proposed memories stay distinct.
Decided by: UMR section 6 "Memory versus domain truth" (UMR:209); UMR section 4 (UMR:142). The accepted fact owners are D-01..D-15; the open owners are in Parts B and C.
Applies to: M14, M15, M16 and every memory consumer after M3 (the cited text names no narrower list).
Source row: Pack D-12.

**P-02.** Every domain keeps its own engineer override with actor, time, source and history, and automatic reprocessing never replaces a confirmed value without a recorded conflict.
Decided by: accepted M1 decision D-15 ([M1-TARGET-OWNERSHIP-DECISIONS.md](../M1/M1-TARGET-OWNERSHIP-DECISIONS.md), SETTLED with gaps G-01..G-04). Closing the gaps is not done by this clause (Part D).
Applies to: M4 (gap closure per Delta section 7), M7, and every writer of a domain fact.
Source row: Pack D-13.

**P-03.** Workload facts (contract value and currency, capacity with effective periods, ownership shares, required-deliverable scope, stream applicability) are domain records under M7, not spreadsheet inputs of the workload page. Who records and overrides each is a Part B slot (OD-05 to OD-09).
Decided by: UMR section 6 "Workload facts have owners" (UMR:205).
Applies to: M7, M28.
Source row: Pack D-16.

### A2. Isolation and access

**P-04.** Isolation is a hard filter: project access, evidence eligibility and revision validity apply before ranking; namespaces stay separate; there are no cross-project memory reads or writes, with one narrowly scoped exception: the controlled promotion engine of P-25, which must not expose one project's memory directly to another project's retrieval context. Which users belong to a project is decided 7 October 2026 (Part B slot B-19).
Decided by: M14 (UMR:462), M21 (UMR:522), M22 (UMR:534); PROJECT_MEMORY_GAP_ASSESSMENT.md:147; the exception by the owner's resolution R-2 of 7 October 2026 (evening), clause P-25.
Applies to: M14, M21, M22.
Source row: Pack D-14.

**P-05.** Reusable global knowledge is a separate governed namespace. A project correction or decision does not become a company-wide fact merely by being saved or reviewed in a project. The promotion rule and promoter are decided 7 October 2026 (Part B slot B-02) under the controls of P-25.
Decided by: UMR section 4 (UMR:140); PM-M0 acceptance (README:54-55).
Applies to: M7, M19, M21, M23, M26, M27, M31 (the Pack's "Blocks" list for OD-02).
Source row: Pack D-10.

**P-06.** Historical approved answers are wording guidance only (Task One tier 8) and never evidence. The knowledge base's verified responses are tier 7. Project-local decisions stay project-local. A retrieval result carries originating project, reviewer and date. Statement approval promotes wording, not facts.
Decided by: UMR section 6 "Historical answers and global knowledge" (UMR:202); Task One.md:60-73. The same sentence appears among the decisions UMR:314 lists for owner recording, and the owner confirmed it at OD-02 on 7 October 2026 (Part B slot B-02). Today's code does the opposite (RC-33).
Applies to: M19, M26, M27.
Source row: Pack D-11.

### A3. Evidence and authority

**P-07.** Unknown is never complete. An unread page, missing proof, undiscovered scope or missing input is reported as such, never as compliant, approved, complete or zero load. For memory answers this reads as "insufficient evidence" (UMR:691).
Decided by: UMR section 6 (UMR:198); Task Two.md:89-101, 343.
Applies to: M6, M10, M12, M26, M28 (the roadmap rows that apply the principle) and memory answers.
Source row: Pack D-6.

**P-08.** Engineer decisions outrank automation. A correction to an inference does not silently supersede an approved external requirement; the conflict is retained and the appropriate confirmation process is used. Who confirms is decided 7 October 2026 (Part B slot B-18).
Decided by: UMR section 6 "Critical authority" (UMR:215); PROJECT_MEMORY_GAP_ASSESSMENT.md:146.
Applies to: M14, M16, M17, M19, M23, M31.
Source row: Pack D-7.

**P-09.** Authority precedence: a consultant's recorded decision outranks an inferred status; an engineer's approved assessment outranks an AI draft; the engineering manager's recorded override outranks a proposed strength score, with the previous value retained; a superseded specification revision or datasheet makes evidence ineligible without deleting it. Who counts as "the engineering manager" is Pack open question 1 (Part D).
Decided by: M19 (UMR:506).
Applies to: M19, M28, M29.
Source row: Pack D-8.

**P-10.** A critical inference is never auto-confirmed; unsupported AI approval stays unconfirmed. No model confidence or pin grants authority.
Decided by: M23 (UMR:542); UMR:686.
Applies to: M23, M31, and any memory write.
Source row: Pack D-9.

### A4. Revisions and time

**P-11.** Latest uploaded, latest issued and latest approved are different states, kept by document, system or entity lineage, not as one project R-number. Effective time and recording time are both stored. Acceptance example: Eaton R0 / Edwards R1, default valid-current query and explicit R0 query (UMR:684).
Decided by: UMR section 6 "Revision semantics" (UMR:216); PROJECT_MEMORY_GAP_ASSESSMENT.md:144-145.
Applies to: M7 and M15 (effective time, UMR:470 at U5); the cited text names no other milestone.
Source row: Pack D-3.

**P-12.** There is one canonical consultant decision vocabulary: approved, approved as noted, revise and resubmit / not approved, rejected, clarification requested, superseded, reply not on file. M7 defines it for shop drawing revisions, material submittal revisions and compliance clauses. Whether "approved as noted" is final for workload is decided 7 October 2026 (Part B slot B-01); the vocabulary itself is not an owner choice.
Decided by: UMR section 6 "One consultant decision vocabulary" (UMR:199).
Applies to: M7, M26, M27, M28.
Source row: Pack D-17.

### A5. Artifact reuse

**P-13.** Default semantic and context outputs are project-scoped. Content-keyed stores that today are shared by default are listed in the artifact capability map section 4 (K-01..K-09) and section 6.2 ("Project-scoped default ... missing").
Decided by: UMR section 5 (UMR:161); UMR:91 ("contextual outputs keyed by project and dependency versions", M7 / M22).
Applies to: M7, M22.
Source row: Pack D-1.

**P-14.** Pure byte-derived artifacts may be shared across projects only under an explicit access-safe content-reuse contract. Shared bytes do not share project approval, attribution or corrections. The contract itself is M7's (UMR:150-162); this clause sets the rule, and the access and retention terms the contract must satisfy (K-03, K-09 name M3). The AI policy that bounds reuse is decided 7 October 2026 (Part B slot B-04).
Decided by: UMR section 5 (UMR:161).
Applies to: M7, M22.
Source row: Pack D-2.

### A6. Events and ephemera

**P-15.** UI change notifications are ephemeral and stay separate from durable engineering history. Consultant decisions, capacity and share changes, strength overrides, configuration versions and task-result events are durable events with effective and recording time. ProjectChange rows are pruned after 30 days and are not audit (UMR:87).
Decided by: UMR section 3 table (UMR:87); M18 (UMR:496).
Applies to: M18, M28.
Source row: Pack D-15.

**P-16.** An Active Task Context is workflow state, not memory. It is isolated to its project and selection, may expire, and never becomes a project fact by being saved. Only the M31 promotion step moves confirmed facts into memory. Per-job payloads and per-request selections are not an explicit task context.
Decided by: UMR section 6 (UMR:222); M30 (UMR:572); M31 (UMR:574).
Applies to: M30, M31.
Source row: Pack D-4.

### A7. AI and automation

**P-17.** Validators, the workload formula and geometry checks are authoritative. AI may split, locate, extract bounded facts, compare, explain, draft and propose, but cannot override a failed check, approve itself, write approved records or replace a formula. This applies to memory writes.
Decided by: UMR section 6 "Deterministic authority over AI" (UMR:197); UMR:686.
Applies to: M8, M26, M28, and every memory write (the roadmap's named authorities).
Source row: Pack D-5.

**P-18.** There is no continuous retraining. Overrides and reviews become labeled examples under M19/M23 governance; model improvement needs a separately curated, evaluated dataset.
Decided by: UMR section 6 "No continuous retraining" (UMR:206); Task Two.md:201.
Applies to: M19, M23, M27, M29.
Source row: Pack D-18.

### A8. Memory history, conflicts and promotion

These clauses record the owner decisions of 7 October 2026 (Pack section 2a). They extend the Project Memory Master Plan; evidence-backed memory, revision awareness, auditability and shared memory across agents are unchanged, and project isolation is unchanged except for the one narrowly scoped exception of P-25 (the controlled promotion engine, owner resolution of 7 October 2026 evening).

**P-19.** Historical and superseded memories stay available to the AI when relevant. Normal engineering decisions use the latest valid authoritative state. Historical memory is context and audit history, not the default decision source.
Decided by: owner decision OD-20, 7 October 2026.
Applies to: M19, M20, M22.
Source row: Pack section 2a, OD-20. Related: P-09 (a superseded revision makes evidence ineligible without deleting it) and P-11 (scoped revisions).

**P-20.** When an engineer resolves a conflict, the resolution is stored as durable memory with a structured rationale, not free text only. At minimum it holds: selected value; rejected or overridden value(s); reason or rationale; supporting evidence; authority basis; engineer or user; timestamp; applicable revision or scope.
Decided by: owner decision OD-21, 7 October 2026.
Applies to: M18, M19.
Source row: Pack section 2a, OD-21. Related: P-02 and P-08 (conflicts are retained, not silently replaced).

**P-21.** If the same conflict appears again, the previous resolution is applied automatically and the engineer is not asked to resolve the same issue repeatedly. The resolution is reopened only when materially stronger or higher-authority evidence appears, or when the applicable project scope or revision changes enough to invalidate it.
Decided by: owner decision OD-22, 7 October 2026.
Applies to: M19, M23, M31.
Source row: Pack section 2a, OD-22. What counts as "materially stronger" evidence is not defined by the decision; evidence not supplied.

**P-22.** Repeated validated knowledge may be promoted from project memory into global knowledge under the promotion rule of Part B slot B-02. The global record stays linked to the projects and evidence it was learned from. Provenance is never lost in promotion. This does not change P-05 and P-06: global knowledge is a separate governed namespace and approved answers remain wording guidance, never evidence. Who may promote and the retirement rule are decided in Part B slot B-02 (7 October 2026); the reconciliation of automatic promotion with isolation (P-04) and with the plan's promotion conditions is P-25 (owner resolution of 7 October 2026, evening).
Decided by: owner decision OD-23, 7 October 2026.
Applies to: M3 global promotion rule, M19, M23, M31, M27.
Source row: Pack section 2a, OD-23.

**P-23.** Each learned global rule or pattern is traceable to all contributing project memories and evidence, so that "which projects taught the system this rule, and on what evidence?" can be answered.
Decided by: owner decision OD-24, 7 October 2026.
Applies to: M21, M23, M31, M25.
Source row: Pack section 2a, OD-24. Related: P-04 now carries the P-25 exception (the controlled promotion engine is the only authorised cross-project reader); how a global record's links to project memories are read back under project isolation is not stated by the decision (Part D4, row D4-3).

### A9. Capability classes (owner decision of 7 October 2026, afternoon)

**P-24.** Task One's five separate permissions are added to this contract as capabilities, not new user roles: `drafting`, `evidence_review`, `engineering_approval`, `export` and `repair`. Their authorisation must still respect project membership (OD-19) and the engineering-authority rules already decided (Q-1: `design_manager` is the engineering manager; `admin` carries no engineering authority by itself). Resolution of 7 October 2026 (evening, verifier finding S1): The `design_manager` role implies the five capabilities only for projects where that user holds project membership. `design_manager` may administer project membership centrally, but that administrative authority does not itself grant access to project engineering content. Role determines engineering authority level; project membership determines project access scope; capabilities determine the permitted actions within an accessible project. A `design_manager` who needs to perform engineering actions on a project must first be a member of it. Membership changes are audited. `admin` remains outside engineering authority unless separately granted the appropriate engineering role and membership. (Orchestrator's milestone assignment from Q-6's "Binds: M7", not an owner sentence: M7 defines the capability table and the check at the domain boundary, after membership (OD-19).)
Decided by: owner (mohamedr69, Mohamed Elazab), session message of 7 October 2026 (afternoon), answer to Pack open question 6; the resolution paragraph by the same owner, session message of 7 October 2026 (evening), R-1.
Applies to: M7 (capability table and check), M14 (membership), M26, M27 (Task One's consumers).
Source row: Task One.md:145; Pack section 7 question 6.

### A10. Promotion engine and the isolation exception (owner resolution of 7 October 2026, evening)

**P-25.** Automatic promotion is kept. The controlled promotion engine is the only policy-authorised cross-project reader for this purpose: a narrowly scoped exception to project-memory isolation that must not expose one project's memory directly to another project's retrieval context. Automatic promotion may activate only after the cross-project promotion tests and gates the roadmap requires pass; until then it stays disabled and eligible knowledge may be promoted manually under OD-02. `design_manager` owns and versions the promotion criteria: repetition threshold, independence of contributing projects, minimum trust and evidence requirements, applicability and generalisation rules, conflict handling, and retirement or re-review conditions. Every promoted global item retains full provenance to its contributing projects and evidence (OD-23, OD-24); project-specific requirements continue to override global knowledge within their own project. The IFC symbol library (OD-13) is a governed exception: verified symbols may enter the company-wide library through the symbol-verification workflow without the general knowledge-promotion workflow, but retain verification authority, version, provenance and audit history; AI confidence alone never qualifies a symbol for that exception.
Decided by: owner (mohamedr69, Mohamed Elazab), session message of 7 October 2026 (evening, resolution of the verifier's findings).
Applies to: M12, M14, M19, M21, M22, M23, M31 (R-2's binds); M7 (symbol library version and access class) and M27 (tier-8 content) added as the orchestrator's milestone assignments.
Source row: Part B slots B-02 and B-13; P-04, P-05, P-22, P-23; verifier finding S2. The orchestrator put the plan's "cross-project reuse requires explicit promotion" (docs/milestones/project-memory/README.md:55) to the owner as part of the S2 conflict; R-2 is the owner's answer to it: automatic promotion under these controls, with manual promotion under OD-02 until the gates pass.

## Part B — Clauses awaiting the owner

One slot per owner decision. The question is copied from Pack Table A. "Interim position" is what the roadmap itself says; it is not a decision. The Pack's options, current code facts and dependencies are in [Table A](M3-DECISION-PACK.md) and are not repeated. Every slot is filled by the scribe from the owner's signed answer sheet (Pack section 2), with the person, role and date.

Owner decisions OD-20..OD-24 have no Part B slot because they were received as decisions, not as open questions; they are Part A clauses P-19..P-23.

Dependencies: OD-03, OD-12 and OD-13 depend on the rule chosen in OD-02; OD-18 option (c) depends on OD-19; OD-10 and OD-11 interact with OD-15; OD-05 to OD-09 needed Pack open question 1 (who is "the engineering manager"), answered 7 October 2026 (Pack section 2b, Q-1).

| Clause | Question (verbatim from the Pack) | State | Interim position in the roadmap | Blocks |
|---|---|---|---|---|
| **B-01** [OD-01 DECIDED 7 October 2026] | Does a consultant decision of "approved as noted" count as final approval when engineering workload is calculated? | [DECIDED 7 October 2026; see the answer slot below] | Not final until recorded (UMR:200). M7 stores whatever is chosen as versioned, auditable configuration; M28 applies it and shows the mapping in every drill-down. Home and the Drawings summary count it as approved today and M28 must not reuse them. | M7, M28, M29 |
| **B-02** [OD-02 DECIDED 7 October 2026] | Under what rule, and by whom, may a project-level answer or correction become reusable company guidance in the governed global namespace? | [DECIDED 7 October 2026; see the answer slot below] | Content is fixed by P-05 and P-06 (wording guidance only, tier 8, never evidence, carrying originating project, reviewer and date). Partly decided 7 October 2026 (P-22, P-23): promoted items must carry full provenance to every contributing project memory and evidence item (OD-23, OD-24) and promotion applies to repeated validated knowledge. The promoter and the retirement rule were decided the same afternoon (answer slot B-02). | M7, M19, M21, M23, M26, M27, M31 |
| **B-03** [OD-03 DECIDED 7 October 2026] | How are the learned answers already stored treated until they are reviewed? | [DECIDED 7 October 2026; see the answer slot below] | Direction only: existing learned rows are "ungoverned until reviewed" (UMR:85, UMR:202; RC-33). The treatment is not stated. OD-23 and OD-24 (P-22, P-23) constrain any option: existing rows cannot be promoted without provenance. | M7, M26, M27 |
| **B-04** [OD-04 DECIDED 7 October 2026] | What does the project AI/provider policy bound (which content and which AI paths), and must it be enforced on the drawing AI paths? | [DECIDED 7 October 2026; see the answer slot below] | None stated beyond the M3 entry's wording "the project AI/provider policy that bounds what compliance evidence may be transmitted". | M7, M12, M22, M26, M27 |
| **B-05** [OD-05 DECIDED 7 October 2026] | Which role may record a project's contract value and currency, and which may override the value, its currency conversion or its source? | [DECIDED 7 October 2026; see the answer slot below] | None. Task Two names the engineering manager (Task Two.md:146-173 lists the fields to keep). | M7, M28 |
| **B-06** [OD-06 DECIDED 7 October 2026] | Which role may record employee capacity (and department) with effective periods, and which may change them? | [DECIDED 7 October 2026; see the answer slot below] | None. Effective-dated history is required (Task Two.md:133). | M7, M18, M28 |
| **B-07** [OD-07 DECIDED 7 October 2026] | Which role may assign project ownership shares and responsibility roles, record an additive-support exception, and decide whether draftsman assignments count toward workload? | [DECIDED 7 October 2026; see the answer slot below] | None. | M7, M18, M28 |
| **B-08** [OD-08 DECIDED 7 October 2026] | Which role may record that a deliverable stream (Shop Drawings or Material Submittals) is required, not required or disputed for a project? | [DECIDED 7 October 2026; see the answer slot below] | None. P-07 applies: a stream with no confirmed scope is not complete. | M7, M28 |
| **B-09** [OD-09 DECIDED 7 October 2026] | Which role may accept or override a proposed Project Strength Score? | [DECIDED 7 October 2026; see the answer slot below] | P-09 and UMR:506: the manager's recorded override outranks a proposed score, with the previous value retained. Who is the manager is not stated. | M28, M29, M19, M18 |
| **B-10** [OD-10 DECIDED 7 October 2026] | Which lifecycle states may a project hold (archived, cancelled, on hold), who may set and reverse them, and what does each state allow? | [DECIDED 7 October 2026; see the answer slot below] | An archived or cancelled project keeps its engineering history and drops out of active workload without deletion (UMR:314; PM-M0 README:54-55). The states, setters and state rules are not stated. | M7, M14, M28 |
| **B-11** [OD-11 DECIDED 7 October 2026] | What does a hard delete remove or keep, who may run it, and how long are backups kept? | [DECIDED 7 October 2026; see the answer slot below] | Normal project removal preserves engineering history (PM-M0 README:54-55); content-keyed rows shared across projects are no longer removed by the first asker (UMR:91 direction, rule is M7's); "define any exceptional purge policy separately" (PROJECT_MEMORY_GAP_ASSESSMENT.md:83). | M7, M14, M18 |
| **B-12** [OD-12 DECIDED 7 October 2026] | Is a drawing-review ruling company-wide or project-local, and who may create and delete one? | [DECIDED 7 October 2026; see the answer slot below] | None (UMR:92, RC-14 name the question). | M12, M22, M7, M3 access |
| **B-13** [OD-13 DECIDED 7 October 2026] | Is the IFC symbol library company-wide reference data or project-scoped, and who may verify, unverify or delete a symbol that other projects use? | [DECIDED 7 October 2026; see the answer slot below] | None (UMR:92, RC-14 name the question). | M7, M12, M10, M22 |
| **B-14** [OD-14 DECIDED 7 October 2026] | Handoff A: must review-sourced drawing changes be explicitly approved before they are drawn? | [DECIDED 7 October 2026; see the answer slot below] | M5 states that only approved changes are eligible (UMR:347) and M12 that engineers approve before Apply (UMR:444). The M2 acceptance record says this is not yet recorded as a decision. Owner commit bb5871d changed `_drawn` (backend/app/redesign/service.py:695) to draw approved changes only, which is option (a); the owner confirmed option (a) on 7 October 2026 (answer slot B-14). | M5, M12 |
| **B-15** [OD-15 DECIDED 7 October 2026] | Handoff B: may Apply keep writing the redesigned DWG into the project archive folder (03- Drawings/Redesign)? | [DECIDED 7 October 2026; see the answer slot below] | Direction: "archive publication is a separate controlled action" (UMR:352). Not recorded as a decision. | M5 |
| **B-16** [OD-16 DECIDED 7 October 2026] | Handoff C: is one AutoCAD run of Apply on an isolated copy authorised, given that accoreconsole writes to the user profile? | [DECIDED 7 October 2026; see the answer slot below] | None. The roadmap grants no live-validation authorisation (UMR:5); real-AutoCAD claims stay separate (UMR:219-220). | M5 exit evidence, M13 |
| **B-17** [OD-17 DECIDED 7 October 2026] | Handoff D: what is done with the stored changes that carry PC-A library paths? | [DECIDED 7 October 2026; see the answer slot below] | None. | M5 |
| **B-18** [OD-18 DECIDED 7 October 2026] | Which role or designated person may confirm a critical project-memory fact, and what evidence must support that confirmation? | [DECIDED 7 October 2026; see the answer slot below] | P-10: no model confidence or pin can grant authority (UMR:686). M16 requires "acceptable evidence/authority" (UMR:478), which is not defined. | M14, M16, M17, M19, M23, M31 |
| **B-19** [OD-19 DECIDED 7 October 2026] | Is access to a project restricted to named people, or does any user with a permitted role keep access to every project? | [DECIDED 7 October 2026; see the answer slot below] | UMR:86 names the M3 and M7 access contract ("enforce allowed-project access for data, sources and jobs"); the Pack does not treat this as a recorded choice. | M7, M14, M21, M22, M30 |

Answer slots, filled from the Pack section 2 answer sheet (7 October 2026):

| Clause | Option chosen (letters or amended text) | Decided by (name, role) | Date | Conditions | Deferred to (named milestone, if deferred) |
|---|---|---|---|---|---|
| B-01 | (c) restricted: company-wide default, Approved as Noted is NOT final for workload or completion; stored by M7 as versioned, auditable policy configuration; explicit per-project override by design_manager only, with a mandatory reason and audit record, where the project's consultant or contractual practice establishes it as final | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Every workload calculation and drill-down exposes which approval mapping applied. Until a stream can reliably distinguish its approval states (including the Material Submittal reply-code issue) finality is not inferred and the affected calculation is marked provisional. Existing Home and Drawings aggregates that treat Approved as Noted as unconditionally approved are corrected or relabelled (RC-37) | not deferred |
| B-02 | Promoter: promotion to global knowledge may be AUTOMATIC once the configured cross-project repetition, validation, trust and provenance criteria are satisfied (no manual promoter action is always required); design_manager or the project's designated confirmer (OD-18) may also promote eligible knowledge manually; never the row's own author acting alone. Carried: (e) provenance to every contributing project memory and evidence item, applicability conditions, project-specific details removed. Retirement: (g) withdrawal or invalidation of the originating authoritative evidence triggers re-review or retirement, never silent deletion of the global knowledge | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Supersedes the partial constraint of the morning; OD-23 and OD-24 unchanged. P-06 (wording guidance, never evidence) confirmed. Controls of the same evening (verifier finding S2): see P-25 | not deferred |
| B-03 | (d) existing learned answers stay active only within their originating project; excluded from cross-project reuse until they qualify for promotion under OD-02; nothing is deleted | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Keeps today's within-project autofill (Task One baseline items 5 and 7 untouched) | not deferred |
| B-04 | (a) the project AI policy applies to every path that sends project content to an external AI provider: document reading, compliance assist, Drawing Review, Redesign, IFC Symbol AI, the Drawings Assistant and every future AI path. Content-keyed previously generated results may be reused for a blocked project only when the reuse is entirely server-side and sends no blocked-project content to a provider | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Enforcement on the drawing paths is the M7/M12 server-boundary gap (Delta #25). The allowed/blocked values stay | not deferred |
| B-05 | (b) amended: design_manager records and overrides contract value and currency, with a reason. admin may administer the underlying system data but gains no engineering authority from the admin role (question 1); where administrative data entry by admin is technically required it is not an engineering approval or override. Missing values are flagged and never defaulted | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | No estimation-register link (D-13 stands). Task Two.md:161-171 field set applies | not deferred |
| B-06 | (b) plus (c): design_manager records effective-dated capacity; admin records account and department administration; employees view their own capacity read-only. Missing or zero capacity is explicitly flagged and never read as unlimited | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Effective-dated history retained; changes are durable events (M18) | not deferred |
| B-07 | (b) for shares: the primary owner may propose ownership shares, design_manager finalises; shares total 1.00 unless a justified explicit exception is recorded, finalisation blocked otherwise. (c) for draftsmen: outside the workload formula for now | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Ownership changes carry effective dates. (d) may be adopted later without a model change | not deferred |
| B-08 | (b) plus (c): design engineers, and document or register extraction through M7's register, may propose stream applicability; design_manager confirms. Unconfirmed applicability is UNKNOWN, not complete; disputed applicability keeps calculations provisional | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 |  | not deferred |
| B-09 | (b) design_manager controls strength-score acceptance and override and may designate one named delegate for an effective period. Complete versioned audit and evidence preserved (previous value, new value, reason, actor, timestamp, evidence, effective version). Overrides authorise no model retraining | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 |  | not deferred |
| B-10 | (c) states archived, cancelled and on hold; (e) lifecycle changes and reversals by design_manager; (h) archived projects are read-only for ordinary work but accept controlled corrections and formally reopened deliverables | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | A handed-over project with unresolved approvals remains represented correctly in workload, never treated as automatically complete | not deferred |
| B-11 | (b) plus (e): hard delete only before a project has ever become active; otherwise archive under OD-10; exceptional purge is separately governed; backups follow the project's retention. Ordinary actions never destroy engineering history. Shared or content-keyed records are never deleted because one originating project is removed | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | The content-keyed rule is M7's to write (UMR:91) | not deferred |
| B-12 | (c) drawing-review rulings are project-local by default; company-wide reuse only through the OD-02 promotion mechanism; existing rulings remain local until qualified or promoted | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Ends the cross-project prompt feed and re-ask (review/service.py:176, 296-300, 750-753) | not deferred |
| B-13 | (a) with the sub-rules: the IFC Symbol Library is company-wide, versioned reference data with controlled access; design_manager or a designated qualified project member verifies symbols; AI output, including confidence 0.97 or more, remains a proposal until engineer verification; a machine carry-over never inherits engineer authority; unverification of an engineer-confirmed symbol requires confirmation, a reason and audit record, and a tombstone or history preservation | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | M12 reworks the auto-accept (ai_symbol_review.py:328-350) and reprocess (ifc/reprocess.py:60-80) paths. Governed exception to the promotion workflow per P-25 (7 October 2026, evening) | not deferred |
| B-14 | (a) approved-only drawing, CONFIRMED as already implemented by owner commit bb5871d | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Tests re-pinned at e4fa306; confirmation now on record | not deferred |
| B-15 | (a) Apply writes only to the platform-controlled working or output copy; publication into the official project archive is a separate explicit engineer action using a unique non-overwriting filename | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Other flows that write into the archive (PRJL.archive_writes) are listed for the same treatment under M7 | not deferred |
| B-16 | (c) authorised with the stated limits: one named machine, an isolated copy of GC-01, a dedicated AutoCAD profile, the source hash verified unchanged afterwards, the output retained as evidence only. The authorisation does not extend beyond that test | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Machine name to be recorded in the M5 evidence when the run is scheduled | not deferred |
| B-17 | (b) the six stored changes are preserved unchanged as history; current block and library paths are resolved at script execution time from the active library; no migration of those historical records | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 |  | not deferred |
| B-18 | (c) amended: a per-project confirmer selected from the project's authorised members by design_manager, with design_manager also able to confirm. Human confirmation is NOT mandatory where the fact is directly and unambiguously established by sufficiently authoritative verified evidence under the trust policy: such facts may be auto-confirmed by policy. Ambiguous, inferred, conflicting, incomplete or below-threshold evidence requires confirmation by the designated project confirmer or design_manager. A model confidence score, AI verdict or pin alone never makes a critical fact authoritative. Critical facts retain their supporting evidence and full audit trail. Initial critical-fact classes: project identity and consultant, system scope and approved brands, floor registry, revision in force, approval decisions, facts consumed by engineering calculations; the classification is centrally configurable. No project needs a named human confirmer before evidence-backed critical facts can be auto-confirmed | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Answers Pack open question 5 (critical classes). The trust policy that defines 'sufficiently authoritative' is a versioned definition M16 must write | not deferred |
| B-19 | (b) project membership enforced centrally across project data, documents and sources, jobs, exports, Project Memory, RAG and retrieval, part search and review rulings; design_manager manages engineering project membership; admin remains system and account administration and gains no engineering access merely by being admin; existing projects backfilled with the Design Engineer of Record as the initial member; the current unrestricted behaviour is a known implementation gap until centralised authorisation lands. Option (c) not used | owner (mohamedr69, Mohamed Elazab), session messages of 7 October 2026 (afternoon, filed by the orchestrator) | 7 October 2026 | Decided without waiting on open question 8 (U-23); the membership rule applies regardless | not deferred |

## Part C — Ownership ratification

Ratified 7 October 2026 by the owner (mohamedr69, Mohamed Elazab): all 29 rows as proposed, with the rule that a filed Part B decision prevails over any row that contradicts it and such a row is flagged in its cell, never silently ratified (one row re-assigned by the owner: C-5, store owner moved to the M7 assignment and access domain on 7 October 2026 evening; B-23 flagged as superseded by the same resolution; C-3 carries a remark that its stretch note is superseded by OD-12, which is not a conflict). Scope rule (open question 2): M3 ratifies only these 29 rows; the 103 other delta cells that merely contain the word PROPOSED stay proposed unless an already-ratified policy or OD governs them; wording alone is never owner approval. "Decision extended" is as written in the Pack. Row text and code citations are in Pack Tables B and C and are not repeated. Ratifying a row does not settle any OD named in the Pack's "Related OD" column.

### C1. PROPOSED owners (Pack Table B: 18 + 4 + 1)

| # | Field or fact | Proposed owner | Decision extended | Ratified by: ____ on ____ |
|---|---|---|---|---|
| B-1 | SBQ.result (shop-drawing BOQ) | BOQ Processor, shop-drawing lineage separate from Design Sheet BOQ; M7 to confirm; engineer-edit layer proposed | D-09 (covers ProjectBoqItem only) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-2 | SBQ.source (IFC drawings the shop BOQ was made from) | Same as B-1; separate last-editor field proposed | D-09 (as B-1) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-3 | JOB.row (BackgroundJob) | M7 shared processing registry, as the job record | None of D-01..D-15; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-4 | JOB.queue_claim | As B-3; M7 idempotency key per stage and input fingerprint | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-5 | JOB.worker | As B-3 | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-6 | JOB.process_split | As B-3; M7 stage records | None; UMR section 5; D-02 owns the registry rows | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-7 | CACHE.page_ocr | M7 shared processing registry / AI platform service; registered text/OCR stage artifact | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-8 | CACHE.page_box | As B-7; registered stage artifact | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-9 | CACHE.pdf_memo (LEGACY) | As B-7; retires with the legacy whole-folder scan | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-10 | CACHE.result_cache | As B-7; under the M7 content-reuse contract | None; UMR section 5 and UMR:91 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-11 | AI.usage | AI platform service (M7, M22); AI platform usage record | None; UMR section 5; M22 (UMR:534) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-12 | AI.budget_limits | As B-11; AI platform budget configuration | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-13 | AI.reading_store | As B-7; registered model-reading artifact under the M7 content-reuse contract | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-14 | USR.account | Platform registry / auth service; access policy is an owner decision (OD-19, OD-06) | None; roadmap M3 project access | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; access policy now DECIDED (OD-19 membership, OD-06 department by admin as account administration) |
| B-15 | USR.role_access | As B-14 (OD-19, OD-18) | None; UMR:86 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; OD-19 and OD-18 DECIDED, no conflict |
| B-16 | USR.login_state | As B-14 (OD-19) | None | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; OD-19 DECIDED |
| B-17 | USR.session | As B-14 (OD-19) | None | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; OD-19 DECIDED |
| B-18 | USR.activity_event | As B-14; use as the "mine" source falls under project access (OD-19, OD-11) | None | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; OD-19 and OD-11 DECIDED |
| B-19 | Delta #16 FA interface publication | Interface processor over the M7 registry; engineer publication is its protected override (OD-18) | None; D-15 override rule applies | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; the engineer publication override stands as a human confirmation under OD-18 (never AI) |
| B-20 | Delta #18 fire-alarm IFC DXF parsed three ways | M7 shared processing registry, one CAD-conversion and DXF-parse stage | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-21 | Delta #19 "IFC drawings counted" | IFC domain publishes one in-force and answers-complete flag (OD-13) | None (D-09 names IFC counts a comparison source) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified; OD-13 DECIDED (the symbol library); the in-force flag stays the IFC domain's, as proposed |
| B-22 | Delta #22 canonical manufacturer name | Knowledge Processor keeps one manufacturer normaliser; M26 reads it | D-12 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 |
| B-23 | Delta S-2 draftsman names across projects | Platform registry / auth service holds the people list (OD-19, OD-07) | D-04 for the assignment record (superseded by R-3: the M7 assignment record) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07; ratified for the people list; FLAGGED under the header rule: the assignment record's owner is the M7 assignment and access domain (R-3, row C-5), not D-04; OD-19 and OD-07 DECIDED |

Rows B-1..B-18 are the 18 PROPOSED owner cells; B-19..B-22 are the four NEW-PROPOSED conflicts; B-23 is S-2. Which other cells containing the word PROPOSED M3 ratifies is Pack open question 2.

### C2. Inherited owners that go beyond a decision's literal wording (Pack Table C)

| # | Fact group | Decision inherited | Stretch (one line) | Confirmed by: ____ on ____ / re-assigned to: ____ |
|---|---|---|---|---|
| C-1 | DRV.review_run, sheets, floor_geometry, finding, decision, rules | D-04 | Review record is a different table from the shop-drawing register | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (confirmed as inherited) |
| C-2 | DRV.fls_files | D-02 (discovery) with D-04 (consumer) | Files found by folder walk, not ProjectDocument rows | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (confirmed as inherited) |
| C-3 | DRV.ruling | D-04 for the owner; scope is OD-12 | Confirming the owner does not settle scope | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (confirmed as inherited); ratified for the owner (D-04); scope now DECIDED by OD-12 (project-local, promotion via OD-02): the stretch note is superseded, not a conflict |
| C-4 | PREP.plan_run, change, symbols, run, output, walls_index, columns_index | D-04 | Preparation results, not register rows; index files name a second owner | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (confirmed as inherited) |
| C-5 | DFT.items, skipped_ready, draftsman, log | D-04, re-assigned to the M7 assignment record (7 October 2026, evening) | Same table as WL.draftsman_assignment, which names "M7 assignment record" (Pack open question 10) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (re-assigned, R-3); authority per the owner's answer to open question 10: operational owner of a draftsman assignment is the design engineer / primary project owner; design_manager may review, change or override; admin gains no engineering ownership. Store owner DECIDED 7 October 2026 (evening, verifier finding S3): RE-ASSIGNED to the M7 project assignment and access domain. The canonical draftsman-assignment record belongs to the M7 project assignment and access domain, not the drawing processor. Drawing pages and drawing-processing services are consumers of that record: they may display and use assignments but maintain no separate authoritative copy. The primary project owner / design engineer operates the assignment; `design_manager` reviews, changes or overrides it (Q-10); all changes are audited. |
| C-6 | ARC.root, folder, project_path_rebind | D-01 with D-02 | Archive folder inventory is not a Project; rebind rewrites the Project row with no event | owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (confirmed as inherited) |

## Part D — What M3 does not decide

### D1. The 17 SETTLED-GAP conflicts

The owner of each is already settled by an accepted decision; today's code has more than one writer or an unprotected override. Source: Delta section 7 (kind SETTLED-GAP, items 1-8, 11-15, 20, 21, 23, 24). Carry-over is as the Delta states it; items 2, 5 and 12 are named under two milestones there.

| Id | Fact (Delta short name) | Carried to |
|---|---|---|
| 1 | Floor identity | M4 |
| 2 | Floor registry rows and floor aliases | M4, M10 |
| 3 | Drawing status | M10 |
| 4 | Engineer-confirmed drawing revision against reconcile | M4 |
| 5 | Who triggers shop drawing reconcile and project action reconcile | M7, M10 |
| 6 | Material submittal register status, revision and reply code | M4 |
| 7 | Material submittal status shown to readers (overlays) | M10 |
| 8 | Consultant reply wording and reply code on a material submittal | M7 |
| 11 | State of one compliance clause answer | M26 |
| 12 | Specification discovery and verdict | M10, M26 |
| 13 | Project.source_folder_path | M7 |
| 14 | ProjectDocument identity, role, state and row projection | M7 |
| 15 | Floor schedule quantity overlay and line material | M4 |
| 20 | Part to datasheet lookup and PartDatasheetLink writers | M7 |
| 21 | Part current figures used by the battery calculation | M4 |
| 23 | Open-work lists | M10 |
| 24 | Draftsman package PDFs | M5 |

The Delta's own by-milestone lists are M4 (1, 2, 4, 6, 15, 21), M5 (24), M7 (5, 8, 13, 14, 20), M10 (2, 3, 5, 7, 12, 23) and M26 (11, 12). The four M3-OWNER-DECISION conflicts (9, 10, 17, 25) are answered by OD-01, OD-02/OD-03, OD-13 and OD-04. The four NEW-PROPOSED conflicts (16, 18, 19, 22) are Part C rows B-19..B-22.

### D2. Gaps G-01..G-04

| Gap | Statement | Owner as recorded |
|---|---|---|
| G-01 | `sync_register` overwrites engineer submittal status | M3/M4 per the decisions file; the roadmap carries it at M4 (Delta #6) |
| G-02 | No classification confirmation endpoint | M3/M4 per the decisions file; milestone not further named |
| G-03 | No sample override record | M3/M4 per the decisions file; milestone not further named |
| G-04 | Automatic current fill re-sets a host part to no-load even after an engineer rejected the no-load setting (`fill_battery_currents@319`, line 355) | "to be confirmed as intended or fixed in M4" ([M1-ACCEPTANCE-REPORT.md](../M1/M1-ACCEPTANCE-REPORT.md) line 94) |

Whether M3 or M7 owns the guard code is Pack open question 4.

Owner decision of 7 October 2026 (afternoon, Pack open question 4): M3 owns the policy requirement and the acceptance constraint for G-01..G-04 and the 16 M3-tagged weakness rows; the guard implementation belongs to the milestone that owns the affected subsystem (M4 or M7 as the roadmap maps them) and is not duplicated inside M3. The M3 acceptance record lists them as downstream implementation obligations.

### D3. The 12 open questions of Pack section 7

| # | Question | Who or what decides it |
|---|---|---|
| 1 | Who is "the engineering manager" (named person, role mapping, whether `admin` may act)? | ANSWERED 7 October 2026 (Pack section 2b, Q-1): the `design_manager` role; `admin` does not act; no new role. |
| 2 | Which PROPOSED cells does M3 ratify (18 + 4 + 1 versus the 121 cells containing the word)? | ANSWERED 7 October 2026: only the 29 Part C rows; the 103 other cells stay proposed unless an already-ratified policy or OD governs them (Part C header). |
| 3 | How are delta cells recorded as SETTLED by reference (dated erratum or separate ratification file)? | ANSWERED 7 October 2026: a separate dated ratification record, [M3-M1-DELTA-RATIFICATION-2026-10-07.md](M3-M1-DELTA-RATIFICATION-2026-10-07.md), naming the exact cells and source decisions; the M1 files are not rewritten. |
| 4 | Do G-01..G-04 and the 16 M3-tagged weakness rows belong to M3? Who owns the guard code? | ANSWERED 7 October 2026: M3 owns the policy requirement and acceptance constraint; the guard implementation belongs to the milestone owning the subsystem (M4 or M7 as the roadmap maps them); M3 acceptance records them as downstream implementation obligations, not unresolved M3 policy (Part D2). |
| 5 | What is "critical" memory (the fact classes)? | ANSWERED 7 October 2026 within OD-18: the baseline classes listed there, centrally configurable; the trust policy for auto-confirmation is M16's to write. |
| 6 | Are Task One's five separate permissions (drafting, evidence review, engineering approval, export, repair; Task One.md:145) part of the M3 contract? | ANSWERED 7 October 2026: yes, as capabilities, not roles (clause P-24). |
| 7 | State of the data (stored learned answers, rulings, ai/carried-over symbols, projects by status, PC-A-path changes): no database was opened. | ANSWERED 7 October 2026: owner-authorised read-only inspection, [M3-INSPECTIONS-2026-10-07.md](M3-INSPECTIONS-2026-10-07.md) section 1 (Q-7). |
| 8 | Whether `require_role` scopes an engineer to a discipline's projects (UNK U-23); whether viewer and draftsman GETs that write fall in M3 or M10. | ANSWERED 7 October 2026: U-23 is answered by inspection (no project or discipline scoping for design roles) and the state-changing GETs are listed and assigned to M10 with M7, [M3-INSPECTIONS-2026-10-07.md](M3-INSPECTIONS-2026-10-07.md) section 2 (Q-8); OD-19 (b) governs access regardless. |
| 9 | Production values (AI switches, `ai_policy`, default admin password, secret_key/cookie_secure) differ from code defaults? | ANSWERED 7 October 2026 as classes (default / overridden / missing), [M3-INSPECTIONS-2026-10-07.md](M3-INSPECTIONS-2026-10-07.md) section 3 (Q-9); one security item for the owner (the seeded admin password key at its code default). |
| 10 | Two target owners for ProjectDraftsmanAssignment (D-04 and M7 assignment record). | ANSWERED 7 October 2026 for authority: design engineer / primary owner operates the assignment, design_manager may review, change or override, admin has no engineering ownership (Part C row C-5). The store owner was re-assigned to the M7 assignment and access domain the same evening (R-3; Part C row C-5). |
| 11 | Method note: the Pack's scribe ran two read-only git commands beyond the brief. | No decision needed; recorded in the Pack. |
| 12 | Roadmap changed during Pack preparation; re-check Table D and the Table A "reserved by" column. | Orchestrator. Re-read at Revision U6 and again at U8 (7 October 2026, verifier): the M3 entry gate text is unchanged and the Table D source rows still match; section 6 rows after UMR:218 moved by one line. |

### D4. Items the independent review of 7 October 2026 found undecided, with their owner or their later decision

| # | Item | Where it arises | Owner of the decision |
|---|---|---|---|
| D4-1 | The trust policy that defines "sufficiently authoritative verified evidence" for policy auto-confirmation of a critical fact, and its threshold | B-18 (OD-18 amended) | M16 writes it as a versioned definition (B-18 conditions) |
| D4-2 | The "materially stronger or higher-authority evidence" test that reopens a resolved conflict | P-21 (OD-22) | M19 (roadmap section 6, OD-22 row) |
| D4-3 | How global links are read back under project isolation | P-23 (OD-24), P-04 | M14, M21, M22 |
| D4-4 | The store owner of ProjectDraftsmanAssignment | Part C row C-5 | DECIDED 7 October 2026 (evening): the M7 assignment and access domain; drawing pages and services are consumers (Part C row C-5) |
| D4-5 | Automatic global promotion: how the cross-project repetition check is reconciled with P-04 isolation, with PM-M0's "explicit promotion", with the roadmap's "no broad automatic promotion until tests pass" condition, who defines and versions the promotion criteria, and how a project member's symbol verification entering the company-wide library (OD-13) relates to P-05 and OD-24 provenance | B-02 (OD-02), B-13 (OD-13), P-05, P-22, P-23 | DECIDED 7 October 2026 (evening): clause P-25 |
| D4-7 | Whether the promotion engine's cross-project candidate read may run while automatic promotion is disabled, to support manual promotion of eligible knowledge under OD-02 | P-25 | M23 and M31 (roadmap UMR:550, 590) |
| D4-6 | Whether `design_manager`'s role-based authorities (B-05, B-06, B-09, B-10, B-13, B-18) imply the `engineering_approval` capability, and whether the role must hold membership or a grant on each project to use them | P-24, Q-1, OD-19 | DECIDED 7 October 2026 (evening): clause P-24, resolution paragraph |

## Part E — Acceptance

**Gate (roadmap M3 entry, verbatim):** "Align with refreshed M1: fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse. Recorded contract accepted before authoritative memory writes."

**Evidence the M3 record will carry (Pack section 6):**

1. The signed decision table: the Pack's Table A answer sheet completed with option, deciding person and role, date and conditions, one row per OD. Status: all 19 rows filled from the owner's session messages of 7 October 2026 (afternoon), relayed by the orchestrator; OD-20..OD-24 in Pack section 2a; open questions 1-4, 6 and 10, the three inspection authorisations and the resolutions of the first review's substantive findings in section 2b (Q-1..Q-10, R-1..R-3). Evidence form: the owner's session messages relayed by the orchestrator, no separate signature. The owner accepted this record on 7 October 2026 (M3-ACCEPTANCE-RECORD.md section 9).
2. The ratified owner list: Pack Tables B and C with each row marked ratify or amend (and the amended owner), signed by the owner. Status: all 29 rows ratified 7 October 2026 by the owner (Part C); one row re-assigned by the owner's resolution R-3 (C-5) and one flagged as superseded by it (B-23); by session message relayed by the orchestrator.
3. The policy text: this contract, covering fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse, with the Table D statements, the five owner decisions and the capability classes (Part A) and the Table A answers (Part B). Status: complete draft awaiting the independent review.
4. The M1 delta cells updated from PROPOSED to SETTLED by reference, one record line per Part C row and per M3-OWNER-DECISION cell (DRV.ruling, PRJL.* 4, USR.* 5, conflicts 9, 10, 17, 25, S-1), naming the ratifying decision and its date. Recorded as the separate dated record [M3-M1-DELTA-RATIFICATION-2026-10-07.md](M3-M1-DELTA-RATIFICATION-2026-10-07.md) (Pack Q-3); the M1 files are untouched. Status: supplied 7 October 2026.
5. A statement of what M3 did not decide (Part D). Status: draft.

No test, code change, migration or live action is part of M3's evidence; the milestone is a recorded contract.

**Count of decided clauses.** Part A holds 25 clauses: 18 restate decided roadmap or accepted-decision text (P-01..P-18), 5 record owner decisions of 7 October 2026 (P-19..P-23), 1 records the owner's answer to open question 6 with the S1 resolution (P-24) and 1 records the S2 resolution (P-25). Part B holds 19 slots: 19 filled (7 October 2026, afternoon), 0 open, 0 deferred. P-22's promoter and retirement rule are now B-02.

**Effect.** This contract takes effect only when every Part B slot is filled with the owner's recorded answer (signed, or a session message relayed by the orchestrator and filed with its date) or is explicitly deferred by the owner with a named milestone, the independent review has no substantive finding open, and the owner accepts the record. Until then nothing in it is in force: the decisions are recorded, not applied, and in particular "approved as noted" is not final for workload (B-01) until M7 stores the configuration. The status wording in the roadmap and README changes only on a verifier verdict.

## Independent review

Two read-only passes by the verifier role (general-purpose agent with the ep-verifier instructions, Claude Opus) on 7 October 2026, each reported in the session log (docs/SESSION-LOG-2026-10-07-windows.md rows 17 and 19):

1. First pass (afternoon): **CHANGES REQUIRED**. Three substantive findings (S1 role versus capability for `design_manager`; S2 automatic promotion against isolation and the plan's promotion conditions; S3 the store owner of ProjectDraftsmanAssignment) and twelve clerical findings. The owner decided S1-S3 the same evening (Pack section 2b, R-1..R-3); the clerical findings were resolved by the orchestrator.
2. Second pass (evening): **ACCEPT WITH NOTES**. S1-S3 recorded faithfully with no policy beyond the owner's words; all seven gate subjects settled; fourteen clerical notes, resolved by the orchestrator before the acceptance record was written. The owner's acceptance of the record (Part E, last step) is outside the verdict.

Second-pass status line (verbatim): "ACCEPT WITH NOTES. The three owner resolutions (S1, S2, S3) are recorded faithfully, they add no policy of substance beyond the owner's words, and no substantive conflict remains. All seven gate subjects are settled."
