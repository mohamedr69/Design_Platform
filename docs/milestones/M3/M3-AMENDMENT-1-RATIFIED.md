# M3 Amendment 1: final text for ratification

**STATUS: RATIFIED** under owner approval A-30 (clarified by A-31), 8 October 2026. This file holds the ratified text of M3 Amendment 1, produced from candidate v2 (sha256 `8224ef533f4235a56021c61e813dafff08a415995fb69393f630a4b4a2cf2113`, kept unchanged) with the four A-29 choices applied; Parts 1 and 2 are the text appended to the Contract and the Decision Pack; Parts 3 to 6 are drafting records with no force.

Prepared by ep-scribe (Claude Opus 5.5), 8 October 2026, read-only task under A-28; v2 prepared the same day from the independent consistency check; this final text prepared the same day under A-29 item 1. One output file; no git write, no provider request, no live clone or worktree touched.

**Inputs.** `MR/orchestrator/AUTHORITY-REGISTER.md` entries A-25, A-26, A-27, A-28; `MR/reviews/U2-ai-budget-design/M3-AMENDMENT-PACKAGE-V2.md` (base text: clauses, resolution matrix, the 28 ambiguities L-1..L-15, E-1..E-7, I-1..I-6); `M3-AMENDMENT-PROPOSAL.md`; `M3-CONFLICT-CHECK.md`; `OWNER-DECISIONS-AI-BUDGET.md` (RULED, A-25); `DESIGN.md` (ORCH-062); the ratified `G:/dev (2)/dev/ep-platform-merged/roadmap-u2/docs/milestones/M3/M3-POLICY-CONTRACT-DRAFT.md` (the **Contract**, IN FORCE since 7 October 2026) and `M3-DECISION-PACK.md` (the **Pack**). For v2 also: `MR/reviews/U2-ai-budget-design/M3-AMENDMENT-1-CONSISTENCY-CHECK.md` (verdict READY WITH NAMED EDITS: 3 blockers, 11 minor, 11 info) and Authority Register A-22 and A-23. For the final text also: Authority Register A-29 item 1. `MR` = `C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap`.

**How to read this file.**
- **Part 1** is the exact text to append at the very end of the Contract, after the section "Independent review". It runs from the line `BEGIN APPENDED TEXT` to the line `END APPENDED TEXT`; the two marker lines are not part of it.
- **Part 2** is the exact set of reference lines to append to the Pack, each after a named ratified table and outside every ratified cell. No line is added to the Contract outside the Amendments section (A-29 item 1).
- **Parts 3 to 6** are drafting records (disposition of the 28 v2 ambiguities; change log v2 package → candidate v1; change log candidate v1 → candidate v2; change log candidate v2 → final text). They are not appended.
- **Owner choices.** None remains. The four choices left open in candidate v2 are settled by A-29 item 1: "natural" and the Owner-and-`admin` sentence are included in M3-A7.2; item (f) is included in M3-A7.1; the three Contract reference lines and the words "and of this contract" are omitted.
- **Ratification record.** The edits made on ratification under A-30 and A-31 are: the two editorial corrections in M3-A0.1(p) and M3-A7.1(e), the Status, Ratified-by and Date-of-ratification fields, the three Pack reference-line dates, and this wrapper header (lines 3 and 14); no other line changed from the verified final text (sha256 `cb9f8a9dca1864a45f17e80658a983fbcf83b4824a0dffb0bcb5c92ad4a3b243`).
- **Quotation conventions.** Ratified text is quoted exactly from the Contract or the Pack, in double quotes; "..." marks an omission. A-25 to A-29 are cited from the Authority Register, which records each owner message "in substance"; the owner's chat message is the authority.
- **Identifier warning.** "Part B slot B-nn" is an owner-decision slot (OD-nn); "Part C row B-nn" is an ownership-ratification row. Part B slot B-11 (hard delete) and slot B-12 (drawing-review rulings) are unrelated to Part C row B-11 (`AI.usage`) and row B-12 (`AI.budget_limits`).

---

## Part 1. Text to append to the Contract

BEGIN APPENDED TEXT

## Amendments

This section is append-only. Each amendment extends the ratified text it cites. No clause, slot, row or answer above this section is edited; each amendment preserves the previous wording by quotation. The ratified text read together with its amendments is the contract. The rows of `M3-DECISION-PACK.md` are unchanged; reference lines pointing to these amendments are appended after the affected tables of the Pack, never inside a ratified cell.

### M3 Amendment 1

- Version: M3 Amendment 1
- Status: RATIFIED
- Date of final text: 8 October 2026
- Ratified by: Mohamed Elazab (Owner), approval reference A-30
- Date of ratification: 8 October 2026
- Sources: Authority Register A-25 (AI budget rulings D1–D7), A-26 (seven directions), A-27 (conditional approval of direction; wording corrections A1–A9; additional clarifications), A-28 (final clarifications: five rulings), A-29 item 1 (final four choices).
- Clauses: M3-A0 (definitions, hierarchy and precedence), M3-A1 to M3-A9, M3-A10 (deferred items, no authority created), M3-A11 (non-authorization).
- Effect: this amendment takes effect on the Date of ratification recorded above (the Effective Date). It states policy and design requirements only (M3-A11).

#### M3-A0. Definitions, hierarchy and precedence

Extends Part C row B-11 (`AI.usage`), Part C row B-12 (`AI.budget_limits`) and Part B slot B-04; read with P-24 and Part B slot B-19. The previous wording of these items is quoted in M3-A1, M3-A2 and M3-A3.

**M3-A0.1 Terms.** In this amendment each capitalised term below has the meaning given here and no other.

- (a) **Project**: a project of the platform, with the membership of Part B slot B-19.
- (b) **Allowed** and **Blocked**: the two values of the project AI policy of Part B slot B-04 ("The allowed/blocked values stay").
- (c) **Policy Status**: the value of a Project's AI policy under this contract.
- (d) **Stored Value**: the value of a Project's AI policy held in the platform's live data. The Policy Status and the Stored Value differ only where this amendment says so (M3-A2.2, M3-A2.11, M3-A2.13).
- (e) **Provider Boundary**: the point at which Project content would leave the platform for an external AI provider.
- (f) **Request**: one request genuinely dispatched to an external AI provider, whether it succeeds or fails. Each dispatched retry and each dispatched escalation is a separate Request. A cache hit, a NullProvider placeholder, a policy refusal, a budget refusal and a confirmed pre-dispatch failure are not Requests (A-25 D4). Before it is dispatched, the same request is a "proposed request" (not capitalised).
- (g) **Interactive Action**: one chat message, or one standalone compliance action, that does not run inside a background processing job.
- (h) **Job**: one background processing job, for the life of that job, or one Interactive Action. A background processing job may contain several Requests and several documents. Each Interactive Action is one Job (A-28 item 2).
- (i) **Task Group**: a named group of AI tasks, held in the AI platform budget configuration. Each Task Group, and the membership of each task in it, is an explicit, versioned and auditable record. Membership of a task in a Task Group is never inferred from the task's name (A-28 item 2).
- (j) **Per-Document Limit**: the per-document AI limit named in Pack Table B row 12 ("per-job, per-document and per-project-per-day AI limits"), preserved by M3-A0.3.
- (k) **Reservation**: an entry in the Reservation Ledger (M3-A1.5) that holds allowance for one proposed request before it is dispatched.
- (l) **Usage Record**: one record of the AI platform usage record of Part C row B-11, of one of the kinds listed in M3-A1.3.
- (m) **Administrator**: a user who holds the `admin` role.
- (n) **Design Engineer**: a design engineer within the meaning of Part B slots B-08 and B-19.
- (o) **Authorized Design Manager**: as defined in M3-A0.4.
- (p) **Owner**: the platform owner whose rulings are recorded in the Authority Register; at the Effective Date, mohamedr69 (Mohamed Elazab). Owner is not a software role (M3-A6.1).
- (q) **Owner Approval**: an approval given by the Owner and recorded with a verifiable approval reference, the approver's identity, an effective date and the recorded evidence (A-25 D6c).
- (r) **Pending Change**: a proposed change to a Project's AI policy that has not been executed, withdrawn or expired. A change that is approved but not yet executed is a Pending Change.
- (s) **Sensitive Policy Change**: a change listed in M3-A7.1.
- (t) **Precautionary Block**, **Emergency Security Block**, **Existing Allowed Project**, **Unverified Allowed Project**, **Transition Review**: as defined in M3-A2.5, M3-A2.6 and M3-A2.13.
- (u) **Price Basis**: as defined in M3-A1.4.
- (v) **Shadow Threshold**: as defined in M3-A1.6.
- (w) **Company Ceiling**, **Budget Adjustment**, **Budget Override**: as defined in M3-A8.1.
- (x) **Rolling 24-Hour Window**, **Calendar-Month Window**, **Budget Time Zone**: as defined in M3-A9.1 and M3-A9.2.
- (y) **Controlled Security Procedure**: the procedure named in M3-A2.5.
- (z) **Effective Date**: the Date of ratification of this amendment.

**M3-A0.2 Hierarchy.** AI usage control has five levels (A-28 item 2):

- **L0 Project AI Policy Gate**: the project AI policy of Part B slot B-04 as extended by M3-A2. It decides whether a proposed request for a Project may be dispatched at all.
- **L1 Project Budget**: one budget for all AI work of one Project.
- **L2 Task Group Budget**: one budget for one Task Group of one Project. Each Task Group Budget is versioned and named.
- **L3 Job Limit**: the limits of one Job for the life of the Job; for an Interactive Action, the limits of that one action.
- **L4 Request Limit**: the limits of one Request.

The hierarchy Project → Task Group → Job → Request of A-27 is L1 → L2 → L3 → L4, below L0. The server-wide and per-project budget wording of Part C row B-12 and Pack Table B row 12 is extended to these levels.

**M3-A0.3 Per-Document Limit preserved.** The Per-Document Limit is preserved. Where a document is processed, it applies as an additional applicable constraint together with L1 to L4. It is measured at its own scope, the document.

**M3-A0.4 Authorized Design Manager.** An Authorized Design Manager of a Project is a user who, at the time of the act, (a) holds the `design_manager` role and (b) is a member of that Project (Part B slot B-19; P-24). Under P-24, that role together with that membership implies the `engineering_approval` capability for that Project; that capability is the applicable engineering approval capability (A-28 item 4). No new role, no sixth capability and no separate grant is created or required. A user who holds `design_manager` and is not a member of the Project is not an Authorized Design Manager of that Project.

**M3-A0.5 Policy gate first.** L0 is applied before any budget check at any level and before any Reservation is taken (A-27). A proposed request refused at L0 is not dispatched, is recorded as a policy refusal, takes no Reservation and consumes no allowance at any level. Where the Project or its Policy Status cannot be established, the proposed request is not dispatched: L0 fails closed, as the project AI policy of Part B slot B-04 and the ORCH-053 design (central fail-closed project AI-policy enforcement, A-19 item 4) provide and as A-22 decisions 1 and 2 require, subject only to the synthetic operator-evaluation exception of A-22 decision 3. This sentence restates existing rulings and grants nothing.

**M3-A0.6 Most restrictive wins.** Where more than one of L1 to L4 and the Per-Document Limit applies to a proposed request, the most restrictive applicable budget or limit decides (A-27). A value at a lower level never raises, bypasses or replaces the remaining allowance of a higher level; a lower-level value above that remaining allowance has no effect.

**M3-A0.7 Reservations create no allowance.** Reservation accounting operates within the hierarchy of M3-A0.2. A Reservation counts against the allowance of every level it is checked against and creates no additional allowance at any level (A-28 item 2).

#### M3-A1. Budget configuration objects, usage kinds and windows

Extends Part C row B-11 and Part C row B-12; read with Pack Table B rows 11 and 12 and Part B slot B-04. Previous wording preserved: Part C row B-11 "AI.usage | AI platform service (M7, M22); AI platform usage record | None; UMR section 5; M22 (UMR:534) | owner (mohamedr69, Mohamed Elazab) on 2026-10-07"; Part C row B-12 "AI.budget_limits | As B-11; AI platform budget configuration | None; UMR section 5 | owner (mohamedr69, Mohamed Elazab) on 2026-10-07"; Pack Table B row 11 "AI.usage - AiUsage, one row per model call or cache hit; basis of the daily budget"; Pack Table B row 12 "AI.budget_limits - per-job, per-document and per-project-per-day AI limits (server-wide settings)". The ownership cells of both rows are unchanged.

**M3-A1.1 Scope of the ratified rows.** Part C row B-11 covers the Usage Records of M3-A1.3. Part C row B-12 covers the levels L1 to L4, the Per-Document Limit, the Task Group records, the Price Basis and price table (M3-A1.4), the Reservation Ledger (M3-A1.5), the Shadow Threshold (M3-A1.6), the Company Ceiling (M3-A8) and the Budget Time Zone (M3-A9).

**M3-A1.2 Windows.** The Rolling 24-Hour Window applies to the Request counters and the token counters of L1 and L2 (A-25 D2). The Calendar-Month Window is an additional window for L1 and L2 (A-25 D2). L3 Job Limits apply for the life of the Job, L4 Request Limits apply to the single Request, and the Per-Document Limit applies to the document; none of these three is measured in either window (A-27 correction A1). The measures to which the Calendar-Month Window applies, and whether either window applies to cost, are deferred item DI-10.

**M3-A1.3 Usage kinds.** The AI platform usage record of Part C row B-11 records each of the following as a separate kind of Usage Record: (a) Request; (b) cache hit; (c) NullProvider placeholder; (d) policy refusal; (e) budget refusal; (f) confirmed pre-dispatch failure. Of these kinds, only kind (a) counts against the Request allowance; Reservations count under M3-A0.7 and M3-A1.5. Actual reported tokens and cost are accounted separately from the Request count (A-25 D4). The Pack's "one row per model call or cache hit" is read as one Usage Record per event of these kinds. A circuit breaker prevents provider-error retry storms (A-25 D4); this amendment does not set its design.

**M3-A1.4 Price table and Price Basis.** The AI platform budget configuration includes a versioned provider and model price table. The **Price Basis** is the approved basis on which that table prices metered usage. Metered API routes use versioned provider and model pricing supported by reliable billing or pricing evidence. Cost reported for the Claude Code subscription route is an estimated equivalent value, not verified billed expenditure; subscription routes stay under Request and token limits, with no monetary hard stop on notional cost. No monetary enforcement applies without an approved Price Basis (A-25 D1). Approving a Price Basis, and changing it, each require a recorded authorization (A-27) and are Sensitive Policy Changes (M3-A7.1). Who gives that authorization is deferred item DI-9.

**M3-A1.5 Reservation Ledger.** The AI platform budget configuration includes a Reservation Ledger of atomic cross-process Reservations (A-24 item 4). An expired Reservation whose dispatch status is unknown stays counted until it is reconciled. Reconciliation is an audited workflow supported by health and dashboard alerts and operational escalation for stale Reservations. Automatic release is permitted only on reliable evidence that no Request was dispatched. A potentially dispatched Request is never silently released (A-25 D5). The evidence that counts for automatic release and for release in the reconciliation workflow is deferred item DI-14.

**M3-A1.6 Shadow Threshold.** The AI platform budget configuration includes a **Shadow Threshold**: a comparison value only. Would-be refusals against it are recorded without blocking legitimate engineering work. It is not an enforceable budget. The Shadow Threshold ruled in A-25 D7 is not the initial enforceable Project Budget. This amendment does not state its figure (A-27 correction A1: no numbers).

**M3-A1.7 No numbers.** This amendment sets and approves no numerical value at any level and no Per-Document Limit value. Existing job-level safety bounds remain effective. A level without an effective limit is shown explicitly as uncapped at that level; "inherit" never implies protection where none exists (A-25 D3). No L1, L2, reserve or retry value is proposed before at least 30 days of corrected accounting and the reservation system in shadow mode (A-25 D3). An enforceable Project Budget is determined only after corrected accounting, shadow measurement and a separate Owner Approval (A-25 D7). A-23 item 5 provides that the Design Manager or Owner authorizes engineering AI-budget policy values; which of the two approves which value at L2, L3 and L4 and the retry bound is deferred item DI-13.

**M3-A1.8 Records.** Budget configuration (values at each level, the Per-Document Limit, Task Group records, the price table and Price Basis, the Shadow Threshold, the Company Ceiling and the Budget Time Zone) is held as versioned, audited records. Each change is a durable event with effective time and recording time (P-15).

#### M3-A2. Authority over a Project's AI policy

Extends Part B slot B-04 (OD-04); read with P-24 and Part B slot B-19. Previous wording preserved: Part B slot B-04 answer "(a) the project AI policy applies to every path that sends project content to an external AI provider: document reading, compliance assist, Drawing Review, Redesign, IFC Symbol AI, the Drawings Assistant and every future AI path. Content-keyed previously generated results may be reused for a blocked project only when the reuse is entirely server-side and sends no blocked-project content to a provider"; conditions "Enforcement on the drawing paths is the M7/M12 server-boundary gap (Delta #25). The allowed/blocked values stay". The Contract contained no clause on who may change a Project's AI policy; this amendment adds one.

**M3-A2.1 Values.** Allowed and Blocked remain the only values. This amendment adds no value and no review state.

**M3-A2.2 Approval of changes.** Every change to a Project's AI policy requires the approval of an Authorized Design Manager of that Project, given before the change is executed (A-25 D6b). The only exceptions are the Precautionary Block (M3-A2.5), the Emergency Security Block (M3-A2.6) and placement in Blocked under Transition Review (M3-A2.13). A change that sets Allowed, or otherwise permits Project content to pass the Provider Boundary, takes effect only with that approval; no other approval replaces it (A-27 correction A2; M3-A3.3). A Stored Value set to Allowed without that approval, including through the Project-Update Authorization Gap (M3-A4.1), does not change the Policy Status.

**M3-A2.3 Proposal.** A Design Engineer who is a member of the Project may propose a change. A proposal is not an approval (A-26 direction 3).

**M3-A2.4 Execution.** An Administrator may execute a change approved under M3-A2.2. An Administrator cannot independently grant external AI permission. Executing a change is not approving it (M3-A7.3).

**M3-A2.5 Precautionary Block.** An authorized project member may request, or apply with immediate effect, a **Precautionary Block** (Blocked) of the Project under a **Controlled Security Procedure** (A-27 correction A2). Each Precautionary Block is audited with the member, the time, the reason, the procedure reference and the previous value. This amendment does not define the Controlled Security Procedure or name the authorized project members (deferred item DI-3). Until the Owner answers deferred item DI-3 by a recorded ruling, this clause cannot be exercised; M3-A2.2 (a change to Blocked approved by an Authorized Design Manager) and M3-A2.6 remain available.

**M3-A2.6 Emergency Security Block.** An Administrator may apply an **Emergency Security Block** (Blocked) to a Project. Applying it gives the Administrator no access to Project content and no engineering authority (Part B slot B-19). An Administrator cannot independently restore Allowed. A restoration follows M3-A2.7; an Administrator may execute it only under M3-A2.4.

**M3-A2.7 Restoration.** Every restoration of Allowed, after a Precautionary Block, an Emergency Security Block, placement in Blocked under Transition Review or any other Blocked state, requires the approval of an Authorized Design Manager of the Project under M3-A2.2. That approval is the engineering authorization required by A-27 correction A2 and A-25 D6b. A restoration is a Sensitive Policy Change (M3-A7.1).

**M3-A2.8 Pending Changes never weaken.** A Pending Change never weakens the existing restriction. While a change toward Allowed is pending, the Project's current Policy Status applies unchanged (A-25 D6b).

**M3-A2.9 Pending-Change lifecycle.** A Pending Change expires 30 days after it is proposed. The person who proposed it may withdraw it at any time before it is executed. Expiry and withdrawal leave the Project's Policy Status and Stored Value unchanged. The change, its expiry or withdrawal, and its full audit history are retained; nothing is deleted (A-27 clarification). Whether other pending changes expire is deferred item DI-7.

**M3-A2.10 Audit.** Every proposal, approval, execution, Precautionary Block, Emergency Security Block, restoration, expiry, withdrawal, Transition Review placement and Transition Review confirmation is versioned and audited with: proposer or requester, approver and approval reference, executor, reason, evidence, previous value, new value, effective time and recording time. Where these records are kept before a dedicated store exists is deferred item DI-17; a change under this clause is executed only when every field of this clause is recorded.

**M3-A2.11 New Projects.** A Project created on or after the Effective Date has the Policy Status Blocked from its creation, until a change approved under M3-A2.2 has been executed for it. A new Project never automatically gains permission to transmit content externally; while approval is pending, deterministic local processing continues (A-26 direction 7; Part B slot B-04 two values).

**M3-A2.12 Enforcement status.** No record, report or statement claims that a Blocked Policy Status is technically enforced for a Project until all relevant provider paths are protected at the Provider Boundary (A-28 item 1; Part B slot B-04 conditions "Enforcement on the drawing paths is the M7/M12 server-boundary gap (Delta #25)").

**M3-A2.13 Transition Review of Existing Allowed Projects (T2).**

- (a) **Existing Allowed Project**: a Project whose Stored Value is Allowed on the Effective Date.
- (b) **Unverified Allowed Project**: an Existing Allowed Project for which no independently verified external-AI authorization is recorded. Holding Allowed does not by itself establish that external transmission was authorized (A-27 clarification). Which records made before the Effective Date count as independently verified external-AI authorization is deferred item DI-1; until the Owner answers it, every Existing Allowed Project is an Unverified Allowed Project.
- (c) **Placement.** From the Effective Date, the Policy Status of each Unverified Allowed Project is Blocked during its **Transition Review**, until an Authorized Design Manager of that Project confirms the permission with sufficient evidence (A-28 item 1).
- (d) **Individual review.** Each Project is reviewed individually. Each review records the evidence relied on, the identity of the Authorized Design Manager, the approval reference, and the effective timestamps of the placement and of any confirmation. Whether a further standard for "sufficient evidence" is set is deferred item DI-2.
- (e) **Outcome.** A confirmation is an approval under M3-A2.2 and a Sensitive Policy Change; the Policy Status is Allowed when the confirmation has been recorded under M3-A2.10 and executed under M3-A2.4 and M3-A7.2. Without a confirmation the Policy Status stays Blocked. This amendment sets no completion date for a Transition Review.
- (f) **Preservation.** The original Stored Value and the complete history of every Existing Allowed Project are preserved. No history is erased or overwritten.
- (g) **No mass update.** Ratification of this amendment changes no Stored Value. No mass update of live Projects is made or authorized. A Stored Value is changed under this clause only under the plan of item (h), after that plan's separate approval.
- (h) **Transition plan.** A separate controlled transition and deployment plan, with safeguards against external transmission during the review, enforced at the Provider Boundary, is prepared and submitted for separate approval. This amendment approves neither that plan nor any deployment.
- (i) **Enforcement.** M3-A2.12 applies: the Blocked Policy Status under this clause is not claimed as technically enforced until all relevant provider paths are protected.

#### M3-A3. The Authorized Design Manager; Owner Approval; delegation

Extends Part B slot B-04 and Part B slot B-09; read with P-24 and Pack section 2b Q-1. Previous wording preserved: P-24 "The `design_manager` role implies the five capabilities only for projects where that user holds project membership.", "A `design_manager` who needs to perform engineering actions on a project must first be a member of it." and "`admin` remains outside engineering authority unless separately granted the appropriate engineering role and membership."; Part B slot B-09 answer "(b) design_manager controls strength-score acceptance and override and may designate one named delegate for an effective period. Complete versioned audit and evidence preserved (previous value, new value, reason, actor, timestamp, evidence, effective version). Overrides authorise no model retraining"; Pack section 2b Q-1 decision "\"Engineering Manager\" maps to the existing `design_manager` role. `admin` does not automatically carry engineering authority. No new `engineering_manager` role is introduced."

**M3-A3.1 Approver.** Every approval under M3-A2.2, M3-A2.7 and M3-A2.13(c) is given by an Authorized Design Manager (M3-A0.4) of the Project concerned.

**M3-A3.2 Capability.** The applicable engineering approval capability is the existing P-24 `engineering_approval` capability, implied for an Authorized Design Manager by role and membership (M3-A0.4; A-28 item 4).

**M3-A3.3 Owner Approval.** Owner approval authority is documented separately from the software roles (M3-A6.4). An Owner Approval does not replace the approval of an Authorized Design Manager under M3-A2 (A-27 correction A3: "not an automatic substitute"). This amendment provides no means by which an Owner Approval replaces it; whether one is to exist is deferred item DI-4.

**M3-A3.4 Delegation.** The delegation of Part B slot B-09 remains limited to its previously authorized scope, strength-score acceptance and override, and conveys no AI-policy authority (A-27 correction A3; A-28 item 4). An approval under M3-A2 requires an Authorized Design Manager of the Project (A-27 correction A2); a delegate who is not an Authorized Design Manager of the Project cannot give it. This amendment creates no delegation of AI-policy authority.

#### M3-A4. Project-update authorization gap and Interim Technical Restriction

Extends Part B slot B-04; read with Part B slot B-19 and M3-A2. Previous wording preserved (the pattern applied): Part B slot B-19 answer "... the current unrestricted behaviour is a known implementation gap until centralised authorisation lands. Option (c) not used".

**M3-A4.1 Recorded gap.** The existing behaviour in which an Administrator, a Design Manager or a Design Engineer can set a Project's AI policy to Allowed alone, through the general project-update path, with immediate effect and recorded only as a general project update, does not meet M3-A2. It is recorded as a known implementation gap: the **Project-Update Authorization Gap**.

**M3-A4.2 Interim Technical Restriction: written specification only.** An Interim Technical Restriction on that path is prepared as a written specification only (A-28 item 3). The specification is coordinated with ORCH-053, ORCH-059 and ORCH-060. Its preparation adds no code writer and no implementation that overlaps those tasks. No deployment is made. The specification is submitted for separate approval; its implementation and its deployment each require a separate approval. The behaviour the restriction imposes on the path is decided at that separate approval (deferred item DI-16) and meets M3-A2 and M3-A7.

**M3-A4.3 Instructions insufficient.** Operational instructions alone, such as instructions to users not to use that path, do not close or mitigate the Project-Update Authorization Gap (A-27 correction A4).

**M3-A4.4 Duration.** The Project-Update Authorization Gap stays recorded until a technical restriction that meets M3-A2 is in force under a separate approval.

#### M3-A5. Visibility of usage and cost

Extends Part C row B-11; read with Part B slot B-19 and P-24. Previous wording preserved: Part B slot B-19 answer "(b) project membership enforced centrally across project data, documents and sources, jobs, exports, Project Memory, RAG and retrieval, part search and review rulings; design_manager manages engineering project membership; admin remains system and account administration and gains no engineering access merely by being admin; ..."; P-24 "Role determines engineering authority level; project membership determines project access scope".

**M3-A5.1 Project members.** A member of a Project views usage and cost from the Usage Records attributed to that Project (A-25 D6a).

**M3-A5.2 Design Managers.** A user who holds `design_manager` views usage and cost only for the Projects of which that user is an Authorized Design Manager (A-27 correction A5).

**M3-A5.3 Platform-wide operational cost aggregates.** For authorized administrative accounting, platform-wide operational cost aggregates are viewed with project identifiers and job references. They exclude document names, drawing names, Project contents and unrestricted source access (A-27 correction A5). A field that contains a document name or a drawing name, including a job title that contains one, is excluded. Whether a Project's name may appear as a project identifier is deferred item DI-8.

**M3-A5.4 No access by viewing.** Viewing usage or cost under this clause grants no Project membership, no access to Project content and no engineering authority (Part B slot B-19; P-24).

**M3-A5.5 Unattributed records.** A Usage Record that is attributed to no Project is outside M3-A5.1 and M3-A5.2 and appears only in the aggregates of M3-A5.3. The Project to which a cache hit on a shared content-keyed store is attributed is deferred item DI-15.

**M3-A5.6 Estimated cost.** Cost shown for the Claude Code subscription route is labelled as an estimated equivalent value (M3-A1.4).

#### M3-A6. Role mapping; no Owner software role

Extends Pack section 2b Q-1 (Contract Part D3, open question 1); read with Part B slot B-19 and P-24. Previous wording preserved: Contract Part D3 row 1 "ANSWERED 7 October 2026 (Pack section 2b, Q-1): the `design_manager` role; `admin` does not act; no new role."; Part B slot B-19 "admin remains system and account administration and gains no engineering access merely by being admin".

**M3-A6.1 No Owner role.** No Owner software role is created (A-26 direction 2; A-27 correction A6).

**M3-A6.2 Platform-wide view.** The platform-wide operational cost view of M3-A5.3 maps to the existing `admin` role and to no other role.

**M3-A6.3 Design Managers.** For usage and cost, the `design_manager` role is project-scoped only (M3-A5.2) and carries no platform-wide view.

**M3-A6.4 Owner approval authority.** Owner approval authority is separate from the software roles. It is exercised and documented outside the role mapping, by the Owner's rulings recorded in the Authority Register, and confers no software permission, no engineering authority and no Project membership. Within the software, the Owner sees the platform-wide view only through an account that holds `admin`. The A-25 D6a reference to "Admin and Owner" platform-wide access is read through M3-A6.2 and this clause.

#### M3-A7. Separation of approval and execution

Extends Part B slot B-04 and Part C row B-12; read with Part B slots B-05 and B-19, Pack section 2b Q-1 and the Pack's standing conditions. Previous wording preserved: Part B slot B-05 answer "(b) amended: design_manager records and overrides contract value and currency, with a reason. admin may administer the underlying system data but gains no engineering authority from the admin role (question 1); where administrative data entry by admin is technically required it is not an engineering approval or override. Missing values are flagged and never defaulted"; Pack standing conditions "`admin` is system and account administration only and never gains engineering authority or project access from the role (Q-1, OD-05, OD-06, OD-19); every manager override records a reason and a full audit trail (OD-01, OD-05, OD-09, OD-13)".

**M3-A7.1 Sensitive Policy Changes.** Each of the following is a Sensitive Policy Change:

- (a) a change to a Project's AI policy that permits Project content to pass the Provider Boundary, including a restoration (M3-A2.7) and a Transition Review confirmation (M3-A2.13(e)) (A-25 D6b; A-26 directions 3 and 6);
- (b) the approval of a numerical budget value at any level, a Budget Adjustment or a Budget Override (M3-A1.7, M3-A8) (A-25 D6c; A-26 directions 5 and 6);
- (c) the approval of a Company Ceiling (M3-A8) (A-25 D6c; A-27 correction A8);
- (d) the approval of a Price Basis and any change to it (M3-A1.4) (A-25 D1; A-27 clarification);
- (e) a change of the Budget Time Zone (M3-A9.6) (A-27 correction A9 and clarification);
- (f) a change to Blocked approved under M3-A2.2 (A-26 direction 6; A-29 item 1).

**M3-A7.2 Different persons.** Except under the Emergency Exception of M3-A7.4, the approval and the execution of a Sensitive Policy Change are performed by different natural persons and recorded separately (A-27 correction A7; A-29 item 1). One natural person who holds Owner authority and an `admin` account is one person for this clause.

**M3-A7.3 Execution is not approval.** An Administrator who enters or applies an approved value records the verifiable approval reference, the approver's identity, the effective date and the recorded evidence (A-25 D6c). Executing a change is not approving it. Administrative privilege is never treated as engineering approval (A-26 direction 6). The form of a verifiable approval reference for an Owner Approval given outside the software is deferred item DI-18.

**M3-A7.4 Emergency Exception.** One natural person may approve and execute the same Sensitive Policy Change only as an **Emergency Exception**, which requires all of: an explicit recorded Owner authorization; a limited scope; a recorded justification; and a retrospective independent review by a person who neither approved nor executed the change (A-27 correction A7). Whether the Owner authorization is given per instance or may be standing, who performs the review, and within what time, are deferred item DI-6.

**M3-A7.5 No automatic escalation.** No role, account, emergency or exception confers approval or execution authority automatically. There is no automatic privilege escalation (A-27 correction A7).

**M3-A7.6 Blocks are outside this clause.** A Precautionary Block (M3-A2.5) and an Emergency Security Block (M3-A2.6) are acts of one actor permitted by A-27 correction A2. They, and placement in Blocked under M3-A2.13(c), are not Sensitive Policy Changes. A change to Blocked approved under M3-A2.2 is a Sensitive Policy Change under M3-A7.1(f).

#### M3-A8. Budget Adjustments and Budget Overrides

Extends Part C row B-12; read with Part B slot B-01 (override pattern), Part B slot B-09 (audit standard) and P-15. Previous wording preserved: Part B slot B-01 answer "... explicit per-project override by design_manager only, with a mandatory reason and audit record, where the project's consultant or contractual practice establishes it as final"; Part B slot B-09 "Complete versioned audit and evidence preserved (previous value, new value, reason, actor, timestamp, evidence, effective version)"; P-15 "configuration versions ... are durable events with effective and recording time".

**M3-A8.1 Terms.** A **Company Ceiling** is an Owner-approved upper bound for Budget Adjustments. A **Budget Adjustment** is a time-bound change to an approved budget value of a Project that stays within the Company Ceiling. A **Budget Override** is a time-bound change to an approved budget value of a Project beyond the Company Ceiling. What the Company Ceiling measures is deferred item DI-5.

**M3-A8.2 Within the Company Ceiling.** An Authorized Design Manager of the Project may approve a Budget Adjustment (A-27 correction A8).

**M3-A8.3 Beyond the Company Ceiling.** A Budget Override requires a separate Owner Approval (A-27 correction A8).

**M3-A8.4 No ceiling, no budget yet.** Where no Company Ceiling has been approved and recorded, no change falls within one and M3-A8.2 cannot be exercised. Where no budget value of a Project has been approved (M3-A1.7), there is nothing to adjust or override.

**M3-A8.5 Recording the Company Ceiling.** The Company Ceiling is set by an Owner Approval, entered by an Administrator with the verifiable approval reference, the approver's identity, the effective date and the recorded evidence (A-25 D6c), and held as a versioned, audited record (M3-A1.8).

**M3-A8.6 Time-bound.** Every Budget Adjustment and every Budget Override has an effective start date and an effective end date. When it ends, the value it changed applies again (A-26 direction 5; A-27 correction A8).

**M3-A8.7 Justification and audit.** Every Budget Adjustment and every Budget Override carries a written justification and a full audit history: previous value, new value, reason, actor, approver, approval reference, timestamp, evidence, effective version and effective dates. It never replaces the audit history of the value it changes.

**M3-A8.8 Separation.** The approval and the execution of a Budget Adjustment or a Budget Override follow M3-A7.

**M3-A8.9 No value set.** This clause sets no Company Ceiling and no budget value.

#### M3-A9. Windows and Budget Time Zone

Extends Part C row B-12; read with Pack Table B rows 11 and 12 and P-15. Previous wording preserved: Pack Table B row 11 "... basis of the daily budget"; Pack Table B row 12 "AI.budget_limits - per-job, per-document and per-project-per-day AI limits (server-wide settings)".

**M3-A9.1 Daily.** "Daily", "per day" and "daily budget" in the budget wording mean the **Rolling 24-Hour Window**: the 24 hours ending at the moment of the check (A-25 D2; A-27 correction A9).

**M3-A9.2 Monthly.** The **Calendar-Month Window** is an additional window: a calendar month computed in the **Budget Time Zone**. The Budget Time Zone is Asia/Dubai (+04:00) (A-25 D2; A-27 correction A9).

**M3-A9.3 Storage and retries.** Timestamps are stored in UTC. Monthly boundaries are computed in the Budget Time Zone. Retry accounting follows the same window rules (A-25 D2).

**M3-A9.4 Display.** The exact remaining allowance and the next availability time are displayed (A-25 D2).

**M3-A9.5 No monthly number.** No monthly numeric limit is set or approved.

**M3-A9.6 Changing the Budget Time Zone.** A change of the Budget Time Zone requires a separate policy approval and a recorded authorization (A-27 correction A9 and clarification) and is a Sensitive Policy Change (M3-A7.1). Who gives that approval is deferred item DI-9. Until a change is approved and executed, Asia/Dubai (+04:00) applies.

#### M3-A10. Deferred items (no authority created)

Each item below is a question this amendment does not answer. No permission, approval route, allowance, exemption or ceiling that depends on an answer exists until the Owner answers the question by a recorded ruling. Until then the clause cited applies as written, together with the ratified text it extends.

- **DI-1** (M3-A2.13(b)). Which records made before the Effective Date count as "independently verified external-AI authorization", so that an Existing Allowed Project is not an Unverified Allowed Project?
- **DI-2** (M3-A2.13(d)). Is a standard for "sufficient evidence" in a Transition Review confirmation to be set, beyond the evidence the Authorized Design Manager records?
- **DI-3** (M3-A2.5). What does the Controlled Security Procedure require, and which project members are "authorized project members" who may request or apply a Precautionary Block under it?
- **DI-4** (M3-A3.3). Is there to be any means, such as an explicit recorded act of the Owner, by which an Owner Approval stands in place of an Authorized Design Manager's approval under M3-A2?
- **DI-5** (M3-A8.1). What does the Company Ceiling measure: a maximum for any one Project or an aggregate across Projects, and for which windows and which measures (Requests, tokens, cost)?
- **DI-6** (M3-A7.4). For an Emergency Exception, is the Owner authorization given for each instance or may it be standing for a class of emergencies; who performs the retrospective independent review; and within what time?
- **DI-7** (M3-A2.9). Do pending Budget Adjustments, Budget Overrides, Price Basis approvals or changes, and Budget Time Zone changes also expire after 30 days?
- **DI-8** (M3-A5.3). May a Project's name appear as a project identifier in platform-wide operational cost aggregates, or only its code and numeric identifier?
- **DI-9** (M3-A1.4, M3-A9.6). Who gives the recorded authorization and approval for (a) the first Price Basis, (b) a change to the Price Basis and (c) a change of the Budget Time Zone; and is updating a price under an existing Price Basis, after a provider changes its published price, a change to the Price Basis? (A-23 item 5 concerns engineering AI-budget policy values; whether it covers the Price Basis and the Budget Time Zone is part of this question.)
- **DI-10** (M3-A1.2). To which measures (Requests, tokens, cost) does the Calendar-Month Window apply, and does either window apply to cost?
- **DI-11** (M3-A0.1(i)). Which Task Groups exist, who approves the creation of a Task Group and a change to its membership, and is such a change a Sensitive Policy Change?
- **DI-12** (M3-A0.2). May a Task Group hold a reserved share of the Project Budget (the "reserve" values of A-25 D3), and how does a reserve sit within L1?
- **DI-13** (M3-A1.7). A-23 item 5 provides that "the Design Manager or Owner authorizes engineering AI-budget policy values". For values at L2, L3 and L4 and the retry bound: which of the two approves which value, and for a value not scoped to one Project, which Design Manager?
- **DI-14** (M3-A1.5). What evidence counts as "reliable evidence that no request was dispatched" for automatic release, and what evidence does the audited reconciliation workflow accept to release an expired Reservation?
- **DI-15** (M3-A5.5). To which Project is the Usage Record of a cache hit on a shared content-keyed store attributed: the consuming Project or the Project that created the entry?
- **DI-16** (M3-A4.2). Which behaviour does the Interim Technical Restriction impose on the general project-update path: refusal of every change to Allowed for every role, refusal except for a change approved by an Authorized Design Manager and executed under M3-A2.4 and M3-A7, or conversion of such a change into a Pending Change?
- **DI-17** (M3-A2.10). Where are Pending Changes, approvals, executions, blocks and Transition Review records kept before a dedicated store exists?
- **DI-18** (M3-A7.3). What form does a verifiable approval reference take for an Owner Approval given outside the software: an Authority Register entry number, a dated session-message reference, or both?

#### M3-A11. Non-authorization

This amendment states policy and design requirements only. It authorizes no implementation increment (I1 to I4 or any other); sets or approves no numerical limit, ceiling, threshold or price; authorizes no live policy change and changes no Stored Value; and authorizes no database migration, merge, restart, deployment or live configuration change. The Interim Technical Restriction exists only as a written specification (M3-A4.2), and the transition plan of M3-A2.13(h) is prepared only for separate approval. Existing authorized ORCH work, including ORCH-053, ORCH-059, ORCH-060 and ORCH-064, continues within its existing authorization and is not extended by this amendment.

END APPENDED TEXT

---

## Part 2. Reference lines to append (Pack only)

Each line below is added only on ratification. Each is placed after the named ratified table, separated from the table and from the following text by one blank line. No ratified cell, row, heading or paragraph is edited.

**Pack (`M3-DECISION-PACK.md`), after the Table A answer sheet table (section 2, before the paragraph "Dependencies among decisions"):**

> Amendment references (M3 Amendment 1, appended date of ratification: 8 October 2026; the rows above are unchanged): OD-04 → M3-A0, M3-A1, M3-A2, M3-A3, M3-A4; OD-09 → M3-A3, M3-A8; OD-19 → M3-A2, M3-A4, M3-A5, M3-A6, M3-A7. Text: M3-POLICY-CONTRACT-DRAFT.md, section "Amendments".

**Pack, after the section 2b table (before the paragraph "Standing conditions the owner attached across the answers"):**

> Amendment references (M3 Amendment 1, appended date of ratification: 8 October 2026; the rows above are unchanged): Q-1 → M3-A3, M3-A6, M3-A7; Q-6 → M3-A0.4, M3-A3; R-1 → M3-A0.4, M3-A3. Text: M3-POLICY-CONTRACT-DRAFT.md, section "Amendments".

**Pack, after the Table B table (section 3, before the paragraph "Two observations the ratifier should see"):**

> Amendment references (M3 Amendment 1, appended date of ratification: 8 October 2026; the rows above are unchanged): row 11 (AI.usage) → M3-A0, M3-A1, M3-A5, M3-A9; row 12 (AI.budget_limits) → M3-A0, M3-A1, M3-A8, M3-A9. Text: M3-POLICY-CONTRACT-DRAFT.md, section "Amendments".


No other line is added. No reference line is added to the Contract: the ratified Contract body is preserved, and the Amendments section at its end is the only addition (A-29 item 1).

---

## Part 3. Disposition of the 28 v2 ambiguities (drafting record; not appended)

"Settled" names the ruling or ratified text that answers the item; "Deferred" names the M3-A10 item. "Plain reading" marks a wording choice that grants no authority and that the owner may correct at ratification.

| v2 item | Disposition | Where |
|---|---|---|
| L-1 applicable engineering approval capability | Settled by A-28 item 4: P-24 `engineering_approval`, implied by role and membership; no new role, capability or grant | M3-A0.4, M3-A3.2 |
| L-2 "authorized project member" for a precautionary block | Deferred DI-3; clause not exercisable until the procedure is recorded | M3-A2.5 |
| L-3 "not an automatic substitute" | A-27 A2 and A3 applied: Owner Approval never replaces Authorized Design Manager approval; any other means deferred DI-4 | M3-A3.3 |
| L-4 recording and measure of the Company Ceiling | Recording settled by A-25 D6c; measure deferred DI-5 | M3-A8.1, M3-A8.5 |
| L-5 emergency exception details | "Independent" given its plain reading (neither approver nor executor); the rest deferred DI-6 | M3-A7.4 |
| L-6 blocks and the two-person rule | Precautionary and emergency blocks settled by A-27 A2 (immediate, single-actor blocks). An ordinary change to Blocked approved under M3-A2.2 is a Sensitive Policy Change, settled by A-29 item 1 (M3-A7.1(f); A-26 direction 6) | M3-A7.1, M3-A7.6 |
| L-7 one person with Owner authority and `admin` | Plain reading of A-27 A7 "different persons ... normally": natural persons, and the Emergency Exception is the only departure from "normally"; settled by A-29 item 1 (different natural persons; one natural person using both identities is one person) | M3-A7.2 |
| L-8 delegation of AI-policy authority | Settled by A-27 A2 (approval only by an Authorized Design Manager) and A-28 item 4 (B-09 limited to its scope) | M3-A3.4 |
| L-9 30-day expiry | Plain reading: runs from proposal; "pending" ends only at execution, withdrawal or expiry. Other change types deferred DI-7 | M3-A0.1(r), M3-A2.9 |
| L-10 content of identifiers and references | A-27 A5 exclusion governs any field containing a document or drawing name; project names deferred DI-8 | M3-A5.3 |
| L-11 how the Owner sees platform-wide data | Settled by A-27 A6 (view maps to `admin` only) | M3-A6.2, M3-A6.4 |
| L-12 shadow figure | Settled by A-27 A1 "no ... numbers": figure not stated | M3-A1.6 |
| L-13 non-precautionary change to Blocked | Settled by A-25 D6b ("project ai_policy changes require authorized Design Manager approval") | M3-A2.2 |
| L-14 price basis and time-zone authorization | Deferred DI-9 | M3-A1.4, M3-A9.6 |
| L-15 placement of references | Settled by A-27 and A-28 item 5 (append-only, after tables, no ratified cell touched); Pack lines only, no Contract lines, settled by A-29 item 1 | Part 2 |
| E-1 state during transition review | Settled by A-28 item 1 (T2) with its conditions; pre-existing verification records DI-1; evidence standard DI-2 | M3-A2.13 |
| E-2 counters for the windows | Rolling window on Requests and tokens at L1 and L2 settled by A-25 D2 and A-27 A1; month measures and cost deferred DI-10 | M3-A1.2 |
| E-3 level definitions | Settled by A-28 item 2 (L0–L4, Job, per-document limit, Task Group membership); Task Group list and approver DI-11; reserves DI-12 | M3-A0 |
| E-4 evidence for release | A-25 D5 applied (counted until reconciled); evidence standard deferred DI-14 | M3-A1.5 |
| E-5 attribution of usage | Unattributed records: literal reading of A-25 D6a; shared cache-hit attribution deferred DI-15 | M3-A5.5 |
| E-6 initial value of a new Project | Settled by Part B slot B-04 (two values) and A-26 direction 7 | M3-A2.11 |
| E-7 engineering authorization for restoration | Settled by A-25 D6b and A-27 A2 (Authorized Design Manager approval) | M3-A2.7 |
| I-1 what "prepare" authorizes | Settled by A-28 item 3 (written specification only, coordinated, no deployment); behaviour deferred DI-16 | M3-A4.2 |
| I-2 controlled security procedure | Deferred DI-3 | M3-A2.5 |
| I-3 provider-boundary enforcement | Settled by A-28 item 1 (no enforcement claim; separate transition and deployment plan) | M3-A2.12, M3-A2.13(h) |
| I-4 records before a store exists | Deferred DI-17; no execution without the full record | M3-A2.10 |
| I-5 form of the approval reference | Deferred DI-18 | M3-A7.3 |
| I-6 staffing of the two-person rule | A-27 A7 applied as written; staffing is an operational consequence, not a clause | M3-A7.2 |

Count: 28 items. Fully settled by a ruling or ratified text: 12 (L-1, L-6, L-7, L-8, L-11, L-12, L-13, L-15, E-6, E-7, I-3, I-6; L-6 and L-7 by A-29 item 1). Settled in part with a remainder deferred: 11 (L-3, L-4, L-5, L-9, L-10, E-1, E-2, E-3, E-4, E-5, I-1). Wholly deferred: 5 (L-2, L-14, I-2, I-4, I-5). Deferred items in M3-A10: 18; DI-13 (approvers of L2–L4 values) arises from A-25 D3 and was not a v2 item; in candidate v2 it is narrowed by A-23 item 5.

---

## Part 4. Change log, v2 package → ratification candidate v1 (drafting record; not appended)

This log is kept as written for candidate v1. Rows superseded in candidate v2 are marked; Part 5 gives the v2 edits.

| # | Edit | Source |
|---|---|---|
| 1 | Label "M3 Amendment 1 (proposed v2)" → "M3 Amendment 1"; status → "RATIFICATION CANDIDATE, not ratified"; separate "Date of ratification" line; A-28 added to the sources; Effective Date defined as the date of ratification | A-28 item 5; task brief |
| 2 | v2 preamble 1.2 (non-binding restatement) removed; replaced by the binding clause M3-A0 (definitions, hierarchy, precedence) | A-27 clarification; A-28 item 2 |
| 3 | Hierarchy restated as L0 Project AI Policy Gate, L1 Project Budget, L2 versioned named Task Group Budgets, L3 Job Limits, L4 Request Limits, mapped to Project → Task Group → Job → Request | A-28 item 2 (resolves v2 E-3 mapping, question 13) |
| 4 | "Job" defined as a background job or one Interactive Action (chat message or standalone compliance action); jobs may contain several Requests and documents | A-28 item 2 |
| 5 | "Request" defined (dispatched, success or failure; retries and escalations separate; five non-request kinds) | A-25 D4 |
| 6 | Task Group membership explicit, versioned, auditable, never inferred from task names | A-28 item 2 |
| 7 | Per-Document Limit preserved as an additional applicable constraint (new M3-A0.3) and included in most-restrictive-wins and in Records | A-28 item 2; Pack Table B row 12 |
| 8 | Reservations create no allowance (new M3-A0.7) | A-28 item 2 |
| 9 | Policy gate narrowed to the Project AI Policy Gate (v2 "and every other policy gate" removed); a gate refusal takes no Reservation | A-28 item 2; A-27 |
| 10 | "Authorized Design Manager" redefined: role + membership, with P-24 `engineering_approval` implied; no new role, capability or grant; v2 M3-A3.1(c) replaced | A-28 item 4 (resolves L-1) |
| 11 | Defined terms introduced and capitalised throughout (Policy Status, Stored Value, Provider Boundary, Pending Change, Owner, Owner Approval, Sensitive Policy Change and others) | A-28 item 5 (unambiguous wording) |
| 12 | M3-A1.1 states the full scope read into Part C rows B-11 and B-12 (adds Per-Document Limit, Task Group records, Company Ceiling, Budget Time Zone, consistent with v2 M3-A1.10) | A-27 correction A1 |
| 13 | Windows: rolling 24 h on Request and token counters at L1 and L2; month additional at L1 and L2; L3, L4 and per-document limits at own scopes; month measures and cost deferred | A-25 D2; A-27 correction A1 (E-2; DI-10) |
| 14 | Price Basis defined; its approval and change are Sensitive Policy Changes; approver deferred | A-25 D1; A-27 clarification (L-14; DI-9) |
| 15 | Reservation release: evidence standard deferred; unknown expired Reservations stay counted | A-25 D5 (E-4; DI-14) |
| 16 | No numbers: enforceable Project Budget needs separate Owner Approval; approver of L2–L4 values and retry bound deferred; Per-Document Limit value not set | A-25 D3, D7 (DI-13) |
| 17 | M3-A2.2 now covers every AI-policy change (v2 covered only changes toward Allowed), with the three listed exceptions | A-25 D6b (resolves L-13) |
| 18 | v2 M3-A2.2/A2.3 merged; Owner-substitute question moved to M3-A3.3 with DI-4 | A-27 corrections A2, A3 (L-3) |
| 19 | Precautionary Block: not exercisable until the Controlled Security Procedure is recorded; procedure and authorized members deferred; other block routes stated as available | A-27 correction A2 (L-2, I-2; DI-3) |
| 20 | Restoration: covers placement under Transition Review; "engineering authorization" identified as Authorized Design Manager approval; marked Sensitive Policy Change | A-25 D6b; A-27 correction A2 (E-7) |
| 21 | Pending Change defined (approved-not-executed included); expiry runs from proposal; withdrawal by the proposer; other change types deferred | A-27 clarification (L-9; DI-7) |
| 22 | Audit list extended to Transition Review placement and confirmation; record-location deferred; no execution without the full record | A-27 correction A2; A-28 item 1 (I-4; DI-17) |
| 23 | New Projects: Policy Status Blocked from creation | Part B slot B-04 two values; A-26 direction 7 (E-6) |
| 24 | New M3-A2.12: no claim of technical enforcement of Blocked until all relevant provider paths are protected | A-28 item 1; Part B slot B-04 conditions |
| 25 | v2 bracketed choice T1/T2/T3 replaced by T2 with all A-28 conditions: individual review, evidence, approval identity, effective timestamps, preservation, no mass update, separate transition and deployment plan, no enforcement claim; Policy Status / Stored Value distinction added | A-28 item 1 (resolves E-1, I-3, question 8; DI-1, DI-2) |
| 26 | Delegation: B-09 limited to its previously authorized scope; a non-Authorized-Design-Manager delegate cannot approve | A-28 item 4; A-27 corrections A2, A3 (L-8) |
| 27 | Interim Technical Restriction: written specification only; coordinated with ORCH-053, ORCH-059, ORCH-060; no added code writer or overlapping implementation; no deployment; implementation and deployment each need separate approval; behaviour deferred | A-28 item 3 (I-1; DI-16) |
| 28 | Design Manager visibility restated as "Projects of which that user is an Authorized Design Manager" (v2 "subject to membership and approved scope") | A-27 correction A5; A-28 item 4 |
| 29 | Platform-wide aggregates: exclusion governs fields containing document or drawing names; project names deferred | A-27 correction A5 (L-10; DI-8) |
| 30 | Unattributed Usage Records visible only in aggregates; shared cache-hit attribution deferred | A-25 D6a literal reading (E-5; DI-15) |
| 31 | Owner sees the platform-wide view in the software only through an `admin` account | A-27 correction A6 (L-11) |
| 32 | "Normally" removed: different natural persons except under the Emergency Exception; Owner-plus-admin is one person | A-27 correction A7 (L-7, I-6). Superseded in v2: a plain reading, not settled; marked as an owner choice (Part 5, m-1) |
| 33 | Sensitive Policy Change list annotated with sources; (b) restated as approvals of numerical values, Budget Adjustments and Budget Overrides; Transition Review confirmation added to (a) | A-25 D1, D6b, D6c; A-26 directions 3, 5, 6; A-27 corrections A7–A9 (L-6) |
| 34 | Emergency Exception: "independent" reviewer = neither approver nor executor; per-instance or standing, reviewer and timing deferred | A-27 correction A7 (L-5; DI-6) |
| 35 | Blocks outside the two-person rule now cite A-27 A2; ordinary change to Blocked and Transition Review placement added | A-27 correction A2 (L-6) |
| 36 | Company Ceiling, Budget Adjustment and Budget Override defined; ceiling recorded under D6c; measure deferred; A8.2 inoperative until a ceiling and a budget exist | A-27 correction A8; A-25 D3, D6c (L-4; DI-5) |
| 37 | Rolling 24-Hour Window defined as the 24 hours ending at the check; Budget Time Zone change approver deferred | A-25 D2; A-27 correction A9 (L-14; DI-9) |
| 38 | New M3-A10 "Deferred items (no authority created)" with 18 exact questions and the rule that no dependent permission exists before an answer | A-28 item 5 |
| 39 | v2 section 5 closing statement replaced by the appended clause M3-A11 "Non-authorization" (no increment, numbers, live policy change, Stored Value change, migration, merge, restart, deployment or live configuration change; existing ORCH work unchanged) | A-25; A-28 Boundaries |
| 40 | Pack reference lines kept from v2, OD-04 and Table B lines extended to M3-A0/M3-A1, and Q-6 and R-1 added to the section 2b line; exact placement named (before the following paragraph) | A-27 clarification; A-28 items 4 and 5 (L-15) |
| 41 | Contract reference lines added after the Part B answer-slots table, Part C table C1 and Part D3 table (v2 had none); no pointer in ratified non-table text | A-28 item 5 ("approved append-only references"); task brief (L-15) |
| 42 | v2 derivation notes, trace table, resolution matrix and section 4 ambiguity list removed from the appended text; their outcome is recorded in Part 3 | A-28 item 5 (clean text) |
| 43 | Wording: no "should"; "may" used only as a permission; one meaning per sentence | Task brief; A-28 item 5 |
| 44 | A-25 D4 circuit breaker not restated (unchanged from v2; it remains an A-25 design requirement) | A-27 correction A1 (lists the objects to include). Superseded in v2: restated in M3-A1.3 (Part 5, m-8) |

---

## Part 5. Change log, candidate v1 → candidate v2 (drafting record; not appended)

Source of every edit: `MR/reviews/U2-ai-budget-design/M3-AMENDMENT-1-CONSISTENCY-CHECK.md` (check id in column 2). Only edits that restore fidelity to the rulings, or remove authority that candidate v1 created by drafting, are applied. Nothing new is created. Candidate v1 is unchanged.

| # | Check id | Edit | Authority |
|---|---|---|---|
| 1 | B-1 | M3-A2.6: "An Administrator cannot restore Allowed." → "An Administrator cannot independently restore Allowed. A restoration follows M3-A2.7; an Administrator may execute it only under M3-A2.4." | A-27 correction A2 ("cannot independently restore Allowed"); A-26 direction 3 |
| 2 | B-2 | M3-A1.7: the 30-day corrected-accounting and shadow-mode precondition restored for L1, L2, reserve and retry values; the enforceable Project Budget sentence kept with A-25 D7 | A-25 D3 ("before proposing L1, L2, reserve and retry values"); A-25 D7 |
| 3 | B-3 | M3-A0.1(d): M3-A2.2 added to the cross-references. M3-A2.2: sentence added that a Stored Value set to Allowed without approval, including through the Project-Update Authorization Gap, does not change the Policy Status | A-25 D6b; A-27 correction A2 |
| 4 | m-1 | M3-A7.2: "natural" and the Owner-and-`admin` sentence put in owner-choice brackets. Part 3 row L-7 relabelled as a plain reading; Part 4 row 32 marked superseded | A-27 correction A7; A-28 item 5 |
| 5 | m-2 | Converted into an explicit owner choice: M3-A7.1 item (f) "a change to Blocked approved under M3-A2.2" in owner-choice brackets; the exemption removed from M3-A7.6 and replaced by a sentence tying it to item (f). Part 3 row L-6 updated. The check's option (b) alone was not used: M3-A0.1(s) makes the M3-A7.1 list exhaustive, so deleting the words would have left the exemption in effect | A-26 direction 6; A-27 correction A2 |
| 6 | m-3 | M3-A0.1(f): "proposed request" sentence added; "Request" → "proposed request" in M3-A0.1(k), M3-A0.2 L0, M3-A0.5 and M3-A0.6; M3-A1.3: "Of these kinds, only kind (a) counts against the Request allowance; Reservations count under M3-A0.7 and M3-A1.5." | A-25 D4, D5; A-28 item 5 |
| 7 | m-4 | M3-A0.1(i): "of one Project" removed from the Task Group definition; DI-11 left open | A-28 item 2 |
| 8 | m-5 | M3-A1.7 cites A-23 item 5; DI-13 narrowed to the remaining question; DI-9 notes A-23 item 5 | A-23 item 5 |
| 9 | m-6 | M3-A4.2: "meets M3-A2" → "meets M3-A2 and M3-A7"; DI-16 option that conflicted with M3-A7 replaced by "refusal except for a change approved by an Authorized Design Manager and executed under M3-A2.4 and M3-A7" | A-27 correction A7; A-26 direction 6 |
| 10 | m-7 | M3-A2.13(e): Policy Status becomes Allowed only when the confirmation is recorded under M3-A2.10 and executed under M3-A2.4 and M3-A7.2 | A-26 direction 6; A-28 item 1 |
| 11 | m-8 | M3-A1.3: circuit-breaker sentence added; Part 4 row 44 marked superseded | A-25 D4 |
| 12 | m-9 | M3-A2.13(h): "enforced at the Provider Boundary" added | A-27 clarification 1; A-28 item 1 |
| 13 | m-10 | Pack Table A line: "OD-01 → M3-A8" and "OD-05 → M3-A7" removed. Contract Part B line: "B-01 → M3-A8" and "B-05 → M3-A7" removed. M3-A7 header: "Extends Part B slot B-04 and Part C row B-12; read with Part B slots B-05 and B-19, ...". The three Contract reference lines placed in one owner-choice block; the Amendments preamble words "and of this contract" bracketed to match. Q-6 and R-1 Pack lines kept | A-27 clarification 5; A-28 item 5 |
| 14 | m-11 | M3-A0.5: fail-closed sentence added for a Project or Policy Status that cannot be established, by reference to Part B slot B-04 and the ORCH-053 design, with the A-22 decision 3 exception; states that it grants nothing | Part B slot B-04; A-19 item 4 (ORCH-053 "central fail-closed project AI-policy enforcement"); A-22 decisions 1 to 3 |
| 15 | i-8 | Typographic: the Part 2 anchor for the D3 line now names the full heading "D4. Items the independent review of 7 October 2026 found undecided, with their owner or their later decision" | Contract heading text |
| 16 | (status) | Status "RATIFICATION CANDIDATE v2, not ratified"; "Ratified by" and "Date of ratification" left blank; header, inputs and how-to-read updated (owner-choice bullet; rule for resolving brackets on ratification); Part 3 count; Part 4 heading | A-28 item 5; coordinator instruction |

**Not applied, and why.**
- **i-1 to i-7, i-9 to i-11 (info):** left unchanged, as instructed; none is typographic. This includes i-7 ("at the date of this candidate" in M3-A0.1(p)), which is a wording change, and i-11 (terms defined inside clauses but missing from the M3-A0.1 index), which is clerical. i-4 (restoration after an Emergency Security Block needs no closure of the security matter) stays an observation for the owner; no deferred item was added.
- **m-2 option (b) as worded:** not used alone, for the reason in row 5.
- **m-10 "(read with)" relabelling:** removal was chosen instead, because it adds nothing.

**Deferred items.** All 18 remain genuine gaps and are kept. DI-13 is narrowed, and DI-9 and DI-16 are amended (rows 8 and 9). None is removed and none is added.

---

## Part 6. Change log, candidate v2 → final text (drafting record; not appended)

Authority for every edit: Authority Register A-29 item 1 (owner ruling of 8 October 2026, "M3 Amendment 1, final four choices"). Candidate v1 and candidate v2 are unchanged. No clause other than those listed is edited, and all 18 deferred items (DI-1 to DI-18) are kept as in candidate v2.

| # | Edit | Authority |
|---|---|---|
| 1 | M3-A7.2: owner choice 1 settled, "natural" included: "different natural persons" | A-29 item 1 |
| 2 | M3-A7.2: owner choice 2 settled, sentence included: "One natural person who holds Owner authority and an `admin` account is one person for this clause." | A-29 item 1 ("one natural person using both identities is one person") |
| 3 | M3-A7.1(f): owner choice 3 settled, item included: "(f) a change to Blocked approved under M3-A2.2". M3-A7.6 now reads that such a change "is a Sensitive Policy Change under M3-A7.1(f)". The Precautionary Block and Emergency Security Block exceptions in M3-A7.6 are unchanged; placement in Blocked under M3-A2.13(c) stays outside M3-A7.1 as in candidate v2 | A-29 item 1 ("preserving the specified Precautionary Block and Emergency Security Block exceptions") |
| 4 | Part 2: owner choice 4 settled, the three Contract reference lines and their owner-choice block omitted; Part 2 heading "(Pack only)"; closing sentence states that no Contract line is added | A-29 item 1 ("Part 2 omits the three Contract reference lines"; "the ratified Contract body preserved") |
| 5 | Amendments preamble: the words "and of this contract" omitted | A-29 item 1 ("and-of-this-contract wording") |
| 6 | Status lines: "FINAL TEXT FOR RATIFICATION, not ratified"; "Ratified by" and "Date of ratification" left blank; "Date of candidate" → "Date of final text"; A-29 item 1 added to the sources | A-29 item 1 (not marked RATIFIED before the owner's explicit approval after the verification report) |
| 7 | Bracket removal: the bracketed placeholder "date of ratification" in the three Pack reference lines → "date of ratification: ______", and the Markdown link around `M3-DECISION-PACK.md` in the Amendments preamble → the file name in code format, so that no square bracket remains in the file | A-29 item 1 ("fully resolved final text ... (no brackets)") |
| 8 | Header, inputs, how-to-read (no owner choice remains; ratification edits), Part 3 rows L-6, L-7, L-15 and the count line updated to record the A-29 settlement | A-29 item 1 |

Pending under A-29 item 1: a fresh independent consistency check on this exact rendered text, then the owner's explicit approval. Nothing here ratifies the amendment or authorizes any implementation, numerical limit, live policy change, migration, merge, restart or deployment.
