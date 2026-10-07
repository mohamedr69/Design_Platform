# M3 policy contract — DRAFT

Milestone: **M3 - Ownership, Access & Memory Policy** (unified roadmap, prerequisites M1 and M2).
Date: 7 October 2026. Repository HEAD when written: `b0465ed9ba053b99aba13954e147d3ea0eb20f94` (`git rev-parse HEAD`).
Prepared by ep-scribe from the decision pack; not reviewed by an independent verifier.

Status: **DRAFT: 5 owner decisions recorded (OD-20..OD-24); OD-01..OD-19 remain unanswered except the partial constraint on OD-02/OD-03.** Every clause that depends on one is marked [OD-nn OPEN] and states the roadmap's interim position where the roadmap gives one** (for example "approved as noted" does not count as final until recorded, roadmap section 6). The five decisions (owner session message of 7 October 2026, [Pack section 2a](M3-DECISION-PACK.md)) extend the Project Memory Master Plan and do not replace it. Nothing in this draft is accepted, signed or in force.

## Sources

| Short name | Path | Used for |
|---|---|---|
| Pack | [M3-DECISION-PACK.md](M3-DECISION-PACK.md) (prepared 6 October 2026, HEAD f4d8ca0) | Table A (OD-01..OD-19, questions verbatim), Table B, Table C, Table D, sections 6 and 7 |
| UMR | [docs/UNIFIED_MASTER_ROADMAP.md](../../UNIFIED_MASTER_ROADMAP.md) | M3 entry and gate; sections 3, 4, 5, 6 |
| D-xx / G-xx | [M1-TARGET-OWNERSHIP-DECISIONS.md](../M1/M1-TARGET-OWNERSHIP-DECISIONS.md); [M1-ACCEPTANCE-REPORT.md](../M1/M1-ACCEPTANCE-REPORT.md) line 94 | Accepted decisions D-01..D-15; gap G-04 text |
| Delta | [M1R-DATA-OWNERSHIP-DELTA.md](../M1/refresh-2026-10-06/M1R-DATA-OWNERSHIP-DELTA.md) section 7 | The 17 SETTLED-GAP conflicts and their carried-to milestones |
| PM-M0 | [docs/milestones/project-memory/README.md](../project-memory/README.md) lines 41-55; [PROJECT_MEMORY_GAP_ASSESSMENT.md](../../PROJECT_MEMORY_GAP_ASSESSMENT.md) | Memory plan policy prerequisites |

Line-number basis: "UMR:nnn" is the line at Revision U5 as cited in the Pack. The current file is Revision U6; section 6 rows and the section 3-5 rows cited here are at the same line numbers, and the M3 entry gate is at line 314 (cited by the Pack as 312). The quoted phrases and section names are the stable locators.

How to use: Part A is final text once M3 is accepted. Part B has one slot per owner decision; the scribe fills only the slots. Part C records ratification. Part D lists what M3 does not decide. Part E states the gate and when the contract takes effect.

## Part A — Policy statements in force once M3 is accepted

Clauses P-01 to P-18 restate a row of Pack Table D (D-1..D-18), whose deciding text already exists; P-19 to P-23 record the owner decisions OD-20..OD-24 of 7 October 2026. No option is offered. Where a clause points to an owner decision, the question is in Part B and is not answered here.

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

**P-04.** Isolation is a hard filter: project access, evidence eligibility and revision validity apply before ranking; namespaces stay separate; there are no cross-project memory reads or writes. Which users belong to a project is [OD-19 OPEN].
Decided by: M14 (UMR:462), M21 (UMR:522), M22 (UMR:534); PROJECT_MEMORY_GAP_ASSESSMENT.md:147.
Applies to: M14, M21, M22.
Source row: Pack D-14.

**P-05.** Reusable global knowledge is a separate governed namespace. A project correction or decision does not become a company-wide fact merely by being saved or reviewed in a project. The promotion rule and promoter are [OD-02 OPEN].
Decided by: UMR section 4 (UMR:140); PM-M0 acceptance (README:54-55).
Applies to: M7, M19, M21, M23, M26, M27, M31 (the Pack's "Blocks" list for OD-02).
Source row: Pack D-10.

**P-06.** Historical approved answers are wording guidance only (Task One tier 8) and never evidence. The knowledge base's verified responses are tier 7. Project-local decisions stay project-local. A retrieval result carries originating project, reviewer and date. Statement approval promotes wording, not facts.
Decided by: UMR section 6 "Historical answers and global knowledge" (UMR:202); Task One.md:60-73. The same sentence appears among the decisions UMR:314 lists for owner recording, so the owner is asked to confirm it at OD-02; until then this clause is the roadmap's stated position. Today's code does the opposite (RC-33).
Applies to: M19, M26, M27.
Source row: Pack D-11.

### A3. Evidence and authority

**P-07.** Unknown is never complete. An unread page, missing proof, undiscovered scope or missing input is reported as such, never as compliant, approved, complete or zero load. For memory answers this reads as "insufficient evidence" (UMR:691).
Decided by: UMR section 6 (UMR:198); Task Two.md:89-101, 343.
Applies to: M6, M10, M12, M26, M28 (the roadmap rows that apply the principle) and memory answers.
Source row: Pack D-6.

**P-08.** Engineer decisions outrank automation. A correction to an inference does not silently supersede an approved external requirement; the conflict is retained and the appropriate confirmation process is used. Who confirms is [OD-18 OPEN].
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
Applies to: M7 and M15 (effective time, UMR:472); the cited text names no other milestone.
Source row: Pack D-3.

**P-12.** There is one canonical consultant decision vocabulary: approved, approved as noted, revise and resubmit / not approved, rejected, clarification requested, superseded, reply not on file. M7 defines it for shop drawing revisions, material submittal revisions and compliance clauses. Whether "approved as noted" is final for workload is [OD-01 OPEN]; the vocabulary itself is not an owner choice.
Decided by: UMR section 6 "One consultant decision vocabulary" (UMR:199).
Applies to: M7, M26, M27, M28.
Source row: Pack D-17.

### A5. Artifact reuse

**P-13.** Default semantic and context outputs are project-scoped. Content-keyed stores that today are shared by default are listed in the artifact capability map section 4 (K-01..K-09) and section 6.2 ("Project-scoped default ... missing").
Decided by: UMR section 5 (UMR:161); UMR:91 ("contextual outputs keyed by project and dependency versions", M7 / M22).
Applies to: M7, M22.
Source row: Pack D-1.

**P-14.** Pure byte-derived artifacts may be shared across projects only under an explicit access-safe content-reuse contract. Shared bytes do not share project approval, attribution or corrections. The contract itself is M7's (UMR:150-162); this clause sets the rule, and the access and retention terms the contract must satisfy (K-03, K-09 name M3). The AI policy that bounds reuse is [OD-04 OPEN].
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

These clauses record the owner decisions of 7 October 2026 (Pack section 2a). They extend the Project Memory Master Plan; project isolation, evidence-backed memory, revision awareness, auditability and shared memory across agents are unchanged.

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

**P-22.** Repeated validated knowledge may be promoted from project memory into global knowledge under the promotion logic being designed. The global record stays linked to the projects and evidence it was learned from. Provenance is never lost in promotion. This does not change P-05 and P-06: global knowledge is a separate governed namespace and approved answers remain wording guidance, never evidence. Who may promote and the retirement rule remain [OD-02 OPEN].
Decided by: owner decision OD-23, 7 October 2026.
Applies to: M3 global promotion rule, M19, M23, M31, M27.
Source row: Pack section 2a, OD-23.

**P-23.** Each learned global rule or pattern is traceable to all contributing project memories and evidence, so that "which projects taught the system this rule, and on what evidence?" can be answered.
Decided by: owner decision OD-24, 7 October 2026.
Applies to: M21, M23, M31, M25.
Source row: Pack section 2a, OD-24. Related: P-04 (no cross-project memory reads or writes) is unchanged; how a global record's links to project memories are read under project isolation is not stated by the decision; evidence not supplied.

## Part B — Clauses awaiting the owner

One slot per owner decision. The question is copied from Pack Table A. "Interim position" is what the roadmap itself says; it is not a decision. The Pack's options, current code facts and dependencies are in [Table A](M3-DECISION-PACK.md) and are not repeated. Every slot is filled by the scribe from the owner's signed answer sheet (Pack section 2), with the person, role and date.

Owner decisions OD-20..OD-24 have no Part B slot because they were received as decisions, not as open questions; they are Part A clauses P-19..P-23.

Dependencies: OD-03, OD-12 and OD-13 depend on the rule chosen in OD-02; OD-18 option (c) depends on OD-19; OD-10 and OD-11 interact with OD-15; OD-05 to OD-09 cannot be filed until Pack open question 1 (who is "the engineering manager") is answered.

| Clause | Question (verbatim from the Pack) | State | Interim position in the roadmap | Blocks |
|---|---|---|---|---|
| **B-01** [OD-01 OPEN] | Does a consultant decision of "approved as noted" count as final approval when engineering workload is calculated? | [OPEN] | Not final until recorded (UMR:200). M7 stores whatever is chosen as versioned, auditable configuration; M28 applies it and shows the mapping in every drill-down. Home and the Drawings summary count it as approved today and M28 must not reuse them. | M7, M28, M29 |
| **B-02** [OD-02 OPEN; partly constrained by OD-23, OD-24] | Under what rule, and by whom, may a project-level answer or correction become reusable company guidance in the governed global namespace? | [OPEN, partly constrained 7 October 2026] | Content is fixed by P-05 and P-06 (wording guidance only, tier 8, never evidence, carrying originating project, reviewer and date). Partly decided 7 October 2026 (P-22, P-23): promoted items must carry full provenance to every contributing project memory and evidence item (OD-23, OD-24) and promotion applies to repeated validated knowledge. Still open: who may promote (options a-c) and the retirement rule (f/g). | M7, M19, M21, M23, M26, M27, M31 |
| **B-03** [OD-03 OPEN; constrained by OD-23, OD-24] | How are the learned answers already stored treated until they are reviewed? | [OPEN, constrained 7 October 2026] | Direction only: existing learned rows are "ungoverned until reviewed" (UMR:85, UMR:202; RC-33). The treatment is not stated. OD-23 and OD-24 (P-22, P-23) constrain any option: existing rows cannot be promoted without provenance. | M7, M26, M27 |
| **B-04** [OD-04 OPEN] | What does the project AI/provider policy bound (which content and which AI paths), and must it be enforced on the drawing AI paths? | [OPEN] | None stated beyond the M3 entry's wording "the project AI/provider policy that bounds what compliance evidence may be transmitted". | M7, M12, M22, M26, M27 |
| **B-05** [OD-05 OPEN] | Which role may record a project's contract value and currency, and which may override the value, its currency conversion or its source? | [OPEN] | None. Task Two names the engineering manager (Task Two.md:146-173 lists the fields to keep). | M7, M28 |
| **B-06** [OD-06 OPEN] | Which role may record employee capacity (and department) with effective periods, and which may change them? | [OPEN] | None. Effective-dated history is required (Task Two.md:133). | M7, M18, M28 |
| **B-07** [OD-07 OPEN] | Which role may assign project ownership shares and responsibility roles, record an additive-support exception, and decide whether draftsman assignments count toward workload? | [OPEN] | None. | M7, M18, M28 |
| **B-08** [OD-08 OPEN] | Which role may record that a deliverable stream (Shop Drawings or Material Submittals) is required, not required or disputed for a project? | [OPEN] | None. P-07 applies: a stream with no confirmed scope is not complete. | M7, M28 |
| **B-09** [OD-09 OPEN] | Which role may accept or override a proposed Project Strength Score? | [OPEN] | P-09 and UMR:506: the manager's recorded override outranks a proposed score, with the previous value retained. Who is the manager is not stated. | M28, M29, M19, M18 |
| **B-10** [OD-10 OPEN] | Which lifecycle states may a project hold (archived, cancelled, on hold), who may set and reverse them, and what does each state allow? | [OPEN] | An archived or cancelled project keeps its engineering history and drops out of active workload without deletion (UMR:314; PM-M0 README:54-55). The states, setters and state rules are not stated. | M7, M14, M28 |
| **B-11** [OD-11 OPEN] | What does a hard delete remove or keep, who may run it, and how long are backups kept? | [OPEN] | Normal project removal preserves engineering history (PM-M0 README:54-55); content-keyed rows shared across projects are no longer removed by the first asker (UMR:91 direction, rule is M7's); "define any exceptional purge policy separately" (PROJECT_MEMORY_GAP_ASSESSMENT.md:83). | M7, M14, M18 |
| **B-12** [OD-12 OPEN] | Is a drawing-review ruling company-wide or project-local, and who may create and delete one? | [OPEN] | None (UMR:92, RC-14 name the question). | M12, M22, M7, M3 access |
| **B-13** [OD-13 OPEN] | Is the IFC symbol library company-wide reference data or project-scoped, and who may verify, unverify or delete a symbol that other projects use? | [OPEN] | None (UMR:92, RC-14 name the question). | M7, M12, M10, M22 |
| **B-14** [OD-14 OPEN] | Handoff A: must review-sourced drawing changes be explicitly approved before they are drawn? | [OPEN; decided by code at owner commit bb5871d, pending the owner's recorded confirmation — see Pack §2 answer sheet] | M5 states that only approved changes are eligible (UMR:347) and M12 that engineers approve before Apply (UMR:444). The M2 acceptance record says this is not yet recorded as a decision. Owner commit bb5871d changed `_drawn` (backend/app/redesign/service.py:695) to draw approved changes only, which is option (a); the clause below is not filled, since the owner's confirmation is not yet on record. | M5, M12 |
| **B-15** [OD-15 OPEN] | Handoff B: may Apply keep writing the redesigned DWG into the project archive folder (03- Drawings/Redesign)? | [OPEN] | Direction: "archive publication is a separate controlled action" (UMR:352). Not recorded as a decision. | M5 |
| **B-16** [OD-16 OPEN] | Handoff C: is one AutoCAD run of Apply on an isolated copy authorised, given that accoreconsole writes to the user profile? | [OPEN] | None. The roadmap grants no live-validation authorisation (UMR:5); real-AutoCAD claims stay separate (UMR:219-220). | M5 exit evidence, M13 |
| **B-17** [OD-17 OPEN] | Handoff D: what is done with the stored changes that carry PC-A library paths? | [OPEN] | None. | M5 |
| **B-18** [OD-18 OPEN] | Which role or designated person may confirm a critical project-memory fact, and what evidence must support that confirmation? | [OPEN] | P-10: no model confidence or pin can grant authority (UMR:686). M16 requires "acceptable evidence/authority" (UMR:478), which is not defined. | M14, M16, M17, M19, M23, M31 |
| **B-19** [OD-19 OPEN] | Is access to a project restricted to named people, or does any user with a permitted role keep access to every project? | [OPEN] | UMR:86 names the M3 and M7 access contract ("enforce allowed-project access for data, sources and jobs"); the Pack does not treat this as a recorded choice. | M7, M14, M21, M22, M30 |

Answer slots, to be filled by the scribe when the owner answers (Pack section 2 answer sheet is the source):

| Clause | Option chosen (letters or amended text) | Decided by (name, role) | Date | Conditions | Deferred to (named milestone, if deferred) |
|---|---|---|---|---|---|
| B-01 |  |  |  |  |  |
| B-02 | Partly decided: promoted items carry full provenance (OD-23, OD-24); promotion applies to repeated validated knowledge. Promoter and retirement rule not filed | owner (mohamedr69), session message of 7 October 2026 (partial) | 7 October 2026 | Constraint only | not deferred |
| B-03 | Not decided; any option limited: existing rows cannot be promoted without provenance (OD-23, OD-24) | (constraint only) | 7 October 2026 |  |  |
| B-04 |  |  |  |  |  |
| B-05 |  |  |  |  |  |
| B-06 |  |  |  |  |  |
| B-07 |  |  |  |  |  |
| B-08 |  |  |  |  |  |
| B-09 |  |  |  |  |  |
| B-10 |  |  |  |  |  |
| B-11 |  |  |  |  |  |
| B-12 |  |  |  |  |  |
| B-13 |  |  |  |  |  |
| B-14 |  |  |  |  |  |
| B-15 |  |  |  |  |  |
| B-16 |  |  |  |  |  |
| B-17 |  |  |  |  |  |
| B-18 |  |  |  |  |  |
| B-19 |  |  |  |  |  |

## Part C — Ownership ratification

Unmarked. "Decision extended" is as written in the Pack. Row text and code citations are in Pack Tables B and C and are not repeated. Ratifying a row does not settle any OD named in the Pack's "Related OD" column.

### C1. PROPOSED owners (Pack Table B: 18 + 4 + 1)

| # | Field or fact | Proposed owner | Decision extended | Ratified by: ____ on ____ |
|---|---|---|---|---|
| B-1 | SBQ.result (shop-drawing BOQ) | BOQ Processor, shop-drawing lineage separate from Design Sheet BOQ; M7 to confirm; engineer-edit layer proposed | D-09 (covers ProjectBoqItem only) | ____ on ____ |
| B-2 | SBQ.source (IFC drawings the shop BOQ was made from) | Same as B-1; separate last-editor field proposed | D-09 (as B-1) | ____ on ____ |
| B-3 | JOB.row (BackgroundJob) | M7 shared processing registry, as the job record | None of D-01..D-15; UMR section 5 | ____ on ____ |
| B-4 | JOB.queue_claim | As B-3; M7 idempotency key per stage and input fingerprint | None; UMR section 5 | ____ on ____ |
| B-5 | JOB.worker | As B-3 | None; UMR section 5 | ____ on ____ |
| B-6 | JOB.process_split | As B-3; M7 stage records | None; UMR section 5; D-02 owns the registry rows | ____ on ____ |
| B-7 | CACHE.page_ocr | M7 shared processing registry / AI platform service; registered text/OCR stage artifact | None; UMR section 5 | ____ on ____ |
| B-8 | CACHE.page_box | As B-7; registered stage artifact | None; UMR section 5 | ____ on ____ |
| B-9 | CACHE.pdf_memo (LEGACY) | As B-7; retires with the legacy whole-folder scan | None; UMR section 5 | ____ on ____ |
| B-10 | CACHE.result_cache | As B-7; under the M7 content-reuse contract | None; UMR section 5 and UMR:91 | ____ on ____ |
| B-11 | AI.usage | AI platform service (M7, M22); AI platform usage record | None; UMR section 5; M22 (UMR:534) | ____ on ____ |
| B-12 | AI.budget_limits | As B-11; AI platform budget configuration | None; UMR section 5 | ____ on ____ |
| B-13 | AI.reading_store | As B-7; registered model-reading artifact under the M7 content-reuse contract | None; UMR section 5 | ____ on ____ |
| B-14 | USR.account | Platform registry / auth service; access policy is an owner decision (OD-19, OD-06) | None; roadmap M3 project access | ____ on ____ |
| B-15 | USR.role_access | As B-14 (OD-19, OD-18) | None; UMR:86 | ____ on ____ |
| B-16 | USR.login_state | As B-14 (OD-19) | None | ____ on ____ |
| B-17 | USR.session | As B-14 (OD-19) | None | ____ on ____ |
| B-18 | USR.activity_event | As B-14; use as the "mine" source falls under project access (OD-19, OD-11) | None | ____ on ____ |
| B-19 | Delta #16 FA interface publication | Interface processor over the M7 registry; engineer publication is its protected override (OD-18) | None; D-15 override rule applies | ____ on ____ |
| B-20 | Delta #18 fire-alarm IFC DXF parsed three ways | M7 shared processing registry, one CAD-conversion and DXF-parse stage | None; UMR section 5 | ____ on ____ |
| B-21 | Delta #19 "IFC drawings counted" | IFC domain publishes one in-force and answers-complete flag (OD-13) | None (D-09 names IFC counts a comparison source) | ____ on ____ |
| B-22 | Delta #22 canonical manufacturer name | Knowledge Processor keeps one manufacturer normaliser; M26 reads it | D-12 | ____ on ____ |
| B-23 | Delta S-2 draftsman names across projects | Platform registry / auth service holds the people list (OD-19, OD-07) | D-04 for the assignment record | ____ on ____ |

Rows B-1..B-18 are the 18 PROPOSED owner cells; B-19..B-22 are the four NEW-PROPOSED conflicts; B-23 is S-2. Which other cells containing the word PROPOSED M3 ratifies is Pack open question 2.

### C2. Inherited owners that go beyond a decision's literal wording (Pack Table C)

| # | Fact group | Decision inherited | Stretch (one line) | Confirmed by: ____ on ____ / re-assigned to: ____ |
|---|---|---|---|---|
| C-1 | DRV.review_run, sheets, floor_geometry, finding, decision, rules | D-04 | Review record is a different table from the shop-drawing register | ____ on ____ |
| C-2 | DRV.fls_files | D-02 (discovery) with D-04 (consumer) | Files found by folder walk, not ProjectDocument rows | ____ on ____ |
| C-3 | DRV.ruling | D-04 for the owner; scope is OD-12 | Confirming the owner does not settle scope | ____ on ____ |
| C-4 | PREP.plan_run, change, symbols, run, output, walls_index, columns_index | D-04 | Preparation results, not register rows; index files name a second owner | ____ on ____ |
| C-5 | DFT.items, skipped_ready, draftsman, log | D-04 | Same table as WL.draftsman_assignment, which names "M7 assignment record" (Pack open question 10) | ____ on ____ |
| C-6 | ARC.root, folder, project_path_rebind | D-01 with D-02 | Archive folder inventory is not a Project; rebind rewrites the Project row with no event | ____ on ____ |

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

### D3. The 12 open questions of Pack section 7

| # | Question | Who or what decides it |
|---|---|---|
| 1 | Who is "the engineering manager" (named person, role mapping, whether `admin` may act)? | Owner. Blocks filing OD-05..OD-09 and P-09. |
| 2 | Which PROPOSED cells does M3 ratify (18 + 4 + 1 versus the 121 cells containing the word)? | Owner. |
| 3 | How are delta cells recorded as SETTLED by reference (dated erratum or separate ratification file)? | Owner, with the orchestrator for the M1 delta record. |
| 4 | Do G-01..G-04 and the 16 M3-tagged weakness rows belong to M3? Who owns the guard code? | Owner; M4 and M7 named as candidates in the sources. |
| 5 | What is "critical" memory (the fact classes)? | Owner. No milestone is named in the sources. Needed to answer OD-18 fully. |
| 6 | Are Task One's five separate permissions (drafting, evidence review, engineering approval, export, repair; Task One.md:145) part of the M3 contract? | Owner. The roadmap assigns no milestone. |
| 7 | State of the data (stored learned answers, rulings, ai/carried-over symbols, projects by status, PC-A-path changes): no database was opened. | Not assigned; needs a read of the active database authorised by the owner. |
| 8 | Whether `require_role` scopes an engineer to a discipline's projects (UNK U-23); whether viewer and draftsman GETs that write fall in M3 or M10. | Owner before OD-19 is answered; M10 is the candidate for the GET writes. |
| 9 | Production values (AI switches, `ai_policy`, default admin password, secret_key/cookie_secure) differ from code defaults? | Owner; UNKNOWN in the M1 refresh. |
| 10 | Two target owners for ProjectDraftsmanAssignment (D-04 and M7 assignment record). | Owner (Part C row C-5). |
| 11 | Method note: the Pack's scribe ran two read-only git commands beyond the brief. | No decision needed; recorded in the Pack. |
| 12 | Roadmap changed during Pack preparation; re-check Table D and the Table A "reserved by" column. | Orchestrator. This draft re-read the M3 entry and the section 6 rows at Revision U6; both match the Pack's quotations. |

## Part E — Acceptance

**Gate (roadmap M3 entry, verbatim):** "Align with refreshed M1: fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse. Recorded contract accepted before authoritative memory writes."

**Evidence the M3 record will carry (Pack section 6):**

1. The signed decision table: the Pack's Table A answer sheet completed with option, deciding person and role, date and conditions, one row per OD. Status: evidence not supplied for OD-01..OD-19. Decisions OD-20..OD-24 are recorded in Pack section 2a from the owner's session message of 7 October 2026; OD-02 and OD-03 carry only a partial constraint.
2. The ratified owner list: Pack Tables B and C with each row marked ratify or amend (and the amended owner), signed by the owner. Status: evidence not supplied (Part C is unmarked).
3. The policy text: this contract, covering fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse, with the Table D statements and the five owner decisions (Part A) and the Table A answers (Part B). Status: draft.
4. The M1 delta cells updated from PROPOSED to SETTLED by reference, one record line per Part C row and per M3-OWNER-DECISION cell (DRV.ruling, PRJL.* 4, USR.* 5, conflicts 9, 10, 17, 25, S-1), naming the ratifying decision and its date. How the delta files are touched is Pack open question 3. Status: evidence not supplied.
5. A statement of what M3 did not decide (Part D). Status: draft.

No test, code change, migration or live action is part of M3's evidence; the milestone is a recorded contract.

**Count of decided clauses.** Part A holds 23 clauses: 18 restate decided roadmap or accepted-decision text (P-01..P-18) and 5 record owner decisions of 7 October 2026 (P-19..P-23). Part B holds 19 slots: 0 filled, 2 partly constrained (B-02, B-03), 17 open. P-22 still depends on the open part of OD-02 (promoter and retirement rule).

**Effect.** This contract takes effect only when every Part B slot is filled with the owner's signed answer or is explicitly deferred by the owner with a named milestone. Until then Part A states the roadmap's decided text, Part B states only the roadmap's interim positions, and "approved as noted" does not count as final for workload (UMR:200). The status wording in the roadmap and README changes only on a verifier verdict.

## Independent review

Not performed. Evidence not supplied.
