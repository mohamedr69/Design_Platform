# Unified Engineering Platform Master Roadmap

Revision U8 — 7 October 2026
Scope: one integrated delivery roadmap, M1–M31, covering the platform, drawing redesign, project memory, compliance evidence and engineering workload.  
Status: consolidated implementation plan and evidence-based code assessment. Revision U8 records that owner commit bb5871d (on `merge/candidate`) changed `_drawn` in backend/app/redesign/service.py so that Apply draws **approved** review changes only, which is RD-M1 handoff decision A and M3 decision pack OD-14 option (a) implemented in code — decided by code, pending the owner's recorded confirmation in the M3 answer sheet (docs/milestones/M3/M3-DECISION-PACK.md); that the M2 refresh of 6 October 2026 found RD-M1 finding F002 "STILL OPEN" at its surveyed commit 771001e, which is the pre-bb5871d behavior and stands for that snapshot; and that the first Windows full-suite run is recorded separately when its evidence lands, not claimed here. Revision U7 records five owner decisions on memory history, conflict resolution and global promotion (OD-20..OD-24, 7 October 2026; docs/milestones/M3/M3-DECISION-PACK.md §2a) in section 6 and in M19, M20, M22, M23 and M31, and the M4 test-suite repairs. Revision U6 recorded the M2 refresh (section 8, M2): the 35 RD-M1 findings classified against the current code, 22 new candidate findings in the preparation/coverage/agents code, and the test coverage map. Revision U5 recorded the M1 refresh (section 8, M1) and carries the 65 corrections of its [M1 refresh corrections register](milestones/M1/refresh-2026-10-06/M1R-ROADMAP-CORRECTIONS.md) into sections 3, 6 and 8; statements below that the refresh corrected are marked (RC-nn). Revision U4 incorporates the Project Memory Master Plan v1.1 (Active Task Context / Workflow State, Task Result Feedback & Memory Promotion, and the memory roadmap renumbered M1–M14) as M30 and M31 and amends M18, M22, M23, M24, M25 and section 10. Revision U3 brought the two workflow requirement specifications (Task One, Task Two) into the sequence as M26–M29, maps their phases, and recorded the decisions that make them consistent with each other and with the earlier plans. No milestone acceptance, live validation authorization or deployment is granted by publishing this document.

## 1. Purpose and source precedence

This is one execution roadmap numbered M1–M31. Milestone numbers are stable identifiers; the default delivery order follows the prerequisite graph in section 7, which M26–M29 join by their prerequisites rather than at the end. All milestone references in the plan use this unified numbering. Original IDs appear only in the historical cross-reference appendix and unchanged source/evidence titles and paths; they are not separate execution tracks. Shared infrastructure is built once.

Source plans, preserved byte-for-byte in this project:

- [Platform-Master-Roadmap-M1-M7.pdf](roadmap-sources/Platform-Master-Roadmap-M1-M7.pdf): core data ownership, extraction, classification, central processing, backfill, consumer migration and stabilization.
- [Redesign-Accuracy-Roadmap-RD-M1-M5.pdf](roadmap-sources/Redesign-Accuracy-Roadmap-RD-M1-M5.pdf): baseline, safe Apply, deterministic geometry, staged AI/visual review and real-project validation.
- [Engineering_AI_Project_Memory_Master_Plan_v1.1.pdf](roadmap-sources/Engineering_AI_Project_Memory_Master_Plan_v1.1.pdf): persistent project facts, decisions, evidence, history, summaries, retrieval and shared agent context, plus (new in v1.1) an explicit, ephemeral Active Task Context for every button-driven platform action, task-result feedback into memory, and the memory roadmap renumbered M1–M14. This is the governing memory plan from Revision U4.
- [Engineering_AI_Project_Memory_Master_Plan.pdf](roadmap-sources/Engineering_AI_Project_Memory_Master_Plan.pdf): version 1.0 of the same plan, superseded for memory scope by v1.1 and retained unchanged as the basis of the PM-M0–PM-M12 mapping that Revisions U2 and U3 used (appendix).

Workflow requirement specifications, kept unchanged at the repository root and governed by this roadmap (hashes recorded in [SOURCE-MANIFEST.json](roadmap-sources/SOURCE-MANIFEST.json)):

- [Task One — Compliance Statement Improvement Requirements](../Task%20One.md) (sha256 `6d02bcc97b57280f4ff1348ea82188db4dd921abddbf8aae7b41613bcacc0438`): a nine-state, evidence-grounded compliance assessment with a page ledger, atomic requirements, exact-model evidence, deterministic verification, consultant-first retrieval, citations, a consultant outcome loop and a frozen evaluation cohort.
- [Task Two — Explainable Engineering Team Workload and Overload](../Task%20Two.md) (sha256 `fe92c18307f8509c8fa778d5b2bfb3bb098b28a3613917f0d23a0a781ccc8879`): a deterministic, versioned workload calculation per employee from required Shop Drawing and Material Submittal approval progress, cost band, strength score and ownership share, with a manager dashboard, redistribution scenarios and calibration.

Both tasks are delivered through the unified sequence as M26–M29 (section 8). Their internal “Phase 0–7” numbering is a sub-structure of those milestones, mapped in the appendix; it is not a separate execution track. Each task's requirements stand, but where a task's text and a milestone gate or another task differ, section 6 records the governing decision and the task is read with it.

The original maintained [MASTER-ROADMAP.md](<C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/MASTER-ROADMAP.md>) and [AI-ACCURACY-POLICY.md](<C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/AI-ACCURACY-POLICY.md>) were located through the M4 closure package and consulted. They contain additional scope that the short planning PDFs summarize.

Explicit owner decisions and approved, applicable amendments retain precedence. Existing frozen validation declarations, labels, budgets and review packages remain evidence for their own named snapshots. This consolidation does not reinterpret their authorization or weaken their acceptance criteria. Where closure needs an owner decision, it is recorded as remaining work.

The earlier [memory-only roadmap](milestones/project-memory/README.md) and [gap assessment](PROJECT_MEMORY_GAP_ASSESSMENT.md) are retained as prior planning records. This document governs consolidated sequencing and current status. In particular, RAG follows M11 and PostgreSQL migration is planned at M11 after ownership/workflows stabilize.

## 2. What was checked and how status is stated

The assessment used an isolated copy of 551 application, test, migration and frontend source/configuration files, captured at Git HEAD **831c198ad94224671aa4830d3d601d80634d0590**, including seven working-tree changes recorded at capture. The project was being edited/committed during the review, so the captured file hashes define the assessed code, not HEAD alone.

[Source snapshot and hashes](roadmap-evidence/2026-10-06/source-snapshot.json), [working-tree status](roadmap-evidence/2026-10-06/git-status-before.txt), and [candidate integration comparison](roadmap-evidence/2026-10-06/candidate-integration-check.json) identify that snapshot. Test results and post-review source drift are recorded in section 11.

Status terms:

- **Accepted historical snapshot**: an existing report explicitly records acceptance; it is not renewed acceptance of today's installation.
- **Implemented / partial**: executable code is present, but full milestone gates are unproven.
- **Candidate only**: fixes/evidence exist outside the active implementation.
- **Missing dedicated implementation**: reusable infrastructure exists, but the named capability was not found.
- **Not accepted**: required validation/integration/independent acceptance remains open.

Source comments, screens, test names and historical passing suites do not by themselves establish end-to-end acceptance. No single platform completion percentage is used.

## 3. Current position and material findings

### Core platform

**M1 is historically accepted for its reviewed snapshot. M4 remains CHANGES STILL REQUIRED. M6, M7, M9, M10 and M11 are not formally complete.**

Existing active code provides file discovery, background document processing, hash reuse, classification metadata, domain registers, BOQ, calculations, interfaces, drawing review/preparation, job recovery and audit/activity records. Classification metadata is written only when `document_classification_v2` is on (off by default) and no business tab reads it (RC-01). The processing registry is not one registry but five unrelated stores with their own keys: project_documents, document_readings, document_classifications, background_jobs, and the page and result caches (RC-36).

The latest [historical M2 closure decision](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-CLOSURE-DECISION-2026-10-06.md>) and [17-gate acceptance matrix](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-ACCEPTANCE-MATRIX.md>) say that fresh validation, BOQ evidence, expanded sealed evaluation, accepted-tree integration and final acceptance remain open. Verification 42 accepted the **experiment preparation**, not M4 accuracy. The older declaration summary still says verification pending; the later closure and verification disposition supersede that status.

The active source retains `parse-2026-10-05.5` and `titleblock-2`; the reviewed candidate's `app/ai/evidence_reader.py`, `app/ai/ledger.py` and candidate-only corrections are not automatically present merely because their reports are in docs. The integration comparison verifies the named files are absent; the closure report provides the wider candidate-lineage analysis. Treat candidate promotion as a controlled port with compatibility evidence. A change to either constant queues no re-read; only `INDEX_VERSION` does, and the parser-version repair script is the manual path (RC-02, RC-35, RC-38).

### Drawings, interfaces and redesign

**The tabs and several advanced drawing functions exist, but M5 safety acceptance and M8/M12 correctness are not established for the active code.**

- M2's packaged independent review ends with **ACCEPT WITH NOTES** after its initial corrections. That is historical audit acceptance.
- M5's packaged independent review requests correction of the approval/publication race. A correction report says **READY FOR INDEPENDENT CORRECTION REVIEW**. An accepting final correction disposition was not found in the packaged files inspected.
- Active [redesign _drawn](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/service.py:695>) permits some `proposed` review changes; active [Apply](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/service.py:1479>) copies output into the project archive when a source folder exists. This does not meet the M5 approved-only/no-implicit-publication target. Apply draws whatever the stored change list holds, including `proposed` changes whose review decision was later reversed, and never reads the stored preparation gate, which is not recomputed after engineer edits (RC-05). At owner commit bb5871d (merge/candidate), `_drawn` (service.py:695, line unchanged by that commit) draws **approved** changes only — OD-14 option (a), decided by code, pending the owner's confirmation; the statement above describes the code at commit 771001e, the M2 refresh's surveyed snapshot.
- Active Apply does not implement the candidate's verified read-back/publication transaction. Its service hash differs from the correction manifest, and `tests/test_redesign_apply.py` is absent.
- Active [wall builder](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/walls.py:151>) still uses raw-layer deny-list filtering without the planned effective-layer visibility/allow-list contract. New room coverage code cannot compensate for an untrusted wall index. Wall and column indexes are cached pickle files keyed by the review's source hash and a `VERSION` constant; a rules change needs a version bump to take effect (RC-06).
- Placement, coordination, coverage and floor-review code now exist in [drawing preparation](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/prepare.py:133>). The plan stores a preparation gate, but Apply does not enforce that stored gate. The preparation floor reviewer at [_ask_review](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/prepare.py:650>) receives structured text; this alone is not the separate visual review of rendered proposals required by M12. Review and preparation GETs create their rows, fit DXF/PDF geometry once and commit; plots, model calls, placement and AutoCAD run only in jobs. GET /draftsman and GET /shop-boq also create their rows on first read (RC-10).
- [interface geometry](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/interfaces/geometry.py:188>) already associates labels with physical symbol candidates and holds ambiguity. Preserve and reuse that work; do not assume all remaining placement and cross-discipline coordination requirements are satisfied.

The FA interface schedule and IFC quantities are recomputed on every read from unversioned inputs (the interface matrix, word-detection and floor rules carry no version in the digest; the symbol library is company-wide and unversioned); there is no stored projection for either (RC-13). The same FA IFC drawing is parsed and converted separately by the IFC extract, the interface scan and the review geometry (RC-03).

These are code findings. No real DWG was generated or published during this roadmap assessment.

### Project memory and shared reuse

The dedicated memory model/service/API/UI, ProjectContextBuilder, controlled summaries and project vector-RAG pipeline are still absent in the inspected active code. Existing structured domain records, corrections, events, AI budgets and caches are reusable foundations.

Shared extraction already exists in parts: [document processing](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/document_processing.py:139>) skips unchanged content, interface scanning carries forward valid prior results, and the interface finding review can reuse rendered pictures. The implementation is not yet a universal cross-tab processing registry. Document processing's skip rule is exact: hash equal, state not processing, no error, extraction present, index version current, no incomplete attempt, parser and profile current (RC-04). These reuses are inside each tab (RC-03).

Additional gaps:

| Finding | Current evidence | Required owner milestone |
|---|---|---|
| Cross-project compliance learning | [learning.index_for](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/compliance/learning.py:139>) filters by system, not project. Approval records every answered row as a learned answer, reviewed or not; learned answers apply as response and proposed technical status and are never retired (RC-15, RC-33). | M7 knowledge boundary + M3/M19: project-local by default; reviewed global promotion; existing learned rows treated as ungoverned until promoted. |
| Project listing is not access isolation | [project access policy](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/routers/projects.py:425>) explicitly allows broader project opening; “mine” is a list preference. | M3 and M7 access contract: enforce allowed-project access for data, sources and jobs. Jobs, parts search and review rulings are further cross-project paths (RC-16). |
| UI change notifications expire | [prune_changes](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_state.py:58>) removes changes older than 30 days, at the end of a sync or processing run of that project, never on a timer; the rows are a UI feed, not audit (RC-17). | M7 durable events / M18: keep ephemeral UI notifications separate from engineering history. |
| Project deletion removes history | [delete_project](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_deletion.py:64>) removes domain records, audit/correction rows, review rulings and submittal history; it deletes content-shared DocumentReading and ResultCache rows by the first-asker project_id, and removes only the `ifc` upload folder, leaving other uploads orphaned (RC-18). | M7 / M3: ordinary archive/deactivation and retained engineering evidence. |
| Registry still has a 2,000-file ceiling | [file enumeration](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/document_sync.py:53>) counts PDFs anywhere plus Word documents under Transmittal folders and raises at the 2,001st; the sync job fails and a project over the limit receives no index update at all (RC-19). | M9: bounded/resumable complete discovery, including 5,000/10,000-file cases. |
| Read requests still perform work | The M1 refresh audited all 149 GET handler definitions (151 runtime routes): 67 do read-time work (folder scans 39, parsing 39, writes 40, reconciliation 22); none calls a model or enqueues a job. The drawings catch-up reconcile runs from eight GETs including Project Home's `/state` and writes shop drawing, floor and issue rows; GET /fa-interfaces and its exports create the project row, walk the IFC folder tree and write floor-alias rows; the floor schedule GET lists the design folder, hashes every candidate workbook, parses changed ones and commits. The worst producers by cost and impact are the drawings reconcile, the datasheet-library refresh (16 GETs, every battery calculation included) and the compliance recheck, which withdraws approvals on a plain GET (RC-07 to RC-12; [read-side-effect record](milestones/M1/refresh-2026-10-06/M1R-READ-SIDE-EFFECTS.md)). | M10: background production and stored read models; no ordinary-read extraction or business mutation. |
| Shared content cache is not memory isolation | [cache reuse](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/cache.py:62>) keys on scope, document hash, evidence fingerprint, task, context and the parser/prompt/schema/model/policy versions, with no project; `put` never refreshes `created_at`, so an entry past its 90-day TTL is a permanent miss; DocumentReading is deleted by the first-asker project (RC-20). | M7 artifact contract / M22: contextual outputs keyed by project and dependency versions. |
| Company-wide review rulings and symbol library | ReviewRuling rows are returned in every project's review payload and fed into every project's model prompt; the IFC symbol library is shared and unversioned, one verify/unverify re-counts every project, and `unverify` deletes engineer-confirmed symbols globally (RC-14). | M3 access and promotion; M7 artifact contract; M22 context. |

### Compliance statements and engineering workload

These findings were taken on the branch tree at Revision U3 (section 11). They establish the regression baseline that Task One's “verified current behavior” and Task Two's Phase 0 ask for, and they are why the two tasks cannot be built as stand-alone features without contradicting the earlier plans.

**Compliance (Task One).** The existing workflow matches Task One's baseline list: clause-by-clause handling, deterministic autofill from the knowledge base, AI drafts, engineer approval before export, and approved answers becoming learned examples. Two baseline items carry corrections: knowledge and learned drafts are autofilled and do not block approval (item 5), and approval records every answered row as a learned answer, reviewed or not (item 7) (RC-21). What is missing is the evidence layer:

- The response vocabulary in [statements.py](../backend/app/compliance/statements.py) is the consultant-facing wording (Comply, Noted, Complied with remark, Not applicable, By others, Deviation, Clarification required). A five-value advisory technical status that includes `insufficient_evidence` exists in knowledge/policy.py; it is not evidence-gated and does not fail closed. The nine-state model is new (RC-22).
- [spec_text.py](../backend/app/compliance/spec_text.py) reads a page range and reports a `pages_read` count. A per-page ledger does exist for project documents in the processing registry, but compliance never uses it and specifications must first enter the registry; the ledger lacks unsupported and unattempted states (RC-23).
- The AI assist prompts in [assist.py](../backend/app/compliance/assist.py) instruct the model not to invent products, values, approvals or certificates. That is an instruction, not a deterministic validator; no numeric, unit, standard, certificate, approval or revision check runs before a positive answer. Structural checks do run: vocabulary and id filtering of AI answers, and manufacturer, model and scope checks on knowledge answers; none of them is a numeric, unit, standard, certificate, approval or revision validator (RC-24).
- The datasheet library exists (DatasheetDocument, PartDatasheetLink, the Datasheet Engine page; BrandSupplier is a supplier contact table, not datasheet content) but is not supplied to compliance drafting beyond a prompt sentence, confirming Task One's baseline item 8. DatasheetDocument has no runtime writer, only an import script (RC-25).
- AiUsage records task, model, tokens, cost, latency and outcome; prompt version, model, source, BOQ and scope hashes sit in ComplianceAudit; budget-stopped and switched-off calls leave no AiUsage row (RC-26). ComplianceStatement carries `version`, which has no writer, and `approved_fingerprint`, which is a hash only: an immutable approved version does not exist yet (RC-27).
- Learned answers are indexed by system across projects ([learning.index_for](../backend/app/compliance/learning.py), table above). Task One's retrieval order permits historical answers only as wording guidance; the roadmap's project-local default and governed promotion (M3) apply to that namespace.
- The knowledge base (KnowledgeResponse, KnowledgeMapping, KnowledgeMappingReview with verified/rejected review states) is the reusable foundation for Task One's “verified organizational knowledge” tier. A verified mapping certifies the pairing of clause and answer, not a product's compliance; equivalence validation has no writer (RC-28).

**Workload (Task Two).** No workload, capacity, assignment-share or scenario code exists, and the Project Team navigation entry is marked not available yet. The inputs Task Two depends on are only partly owned:

| Task Two input | Current evidence | Owner milestone |
|---|---|---|
| Employees and roles | Users with discipline roles and `design_manager`; no department, capacity or effective periods. | M1 refresh (facts), M3 (who may set capacity), M28 |
| Project assignment and ownership share | One `design_engineer_id` per project, set at creation with no reassignment route; draftsman assignment by name and e-mail, not by user. No shares or effective dates (RC-29). | M1 refresh, M7 domain record, M28 |
| Contract value and currency | No field on Project. EstimationProject is a separate register that design accounts cannot read. | M1 refresh, M3 ownership decision, M28 |
| Required Shop Drawings | `required_drawings` and DrawingRequirementState record the contractor's inputs asked for, not the shop drawings we owe, so they give no denominator; M7 creates the scope register. Revisions carry `under_review`, `approved`, `approved_as_noted`, `not_approved`, `reply_not_found` (RC-30). | M7 required-deliverable register |
| Required Material Submittals | No required-submittal register found. Submittals carry SubmittalStatus (`not_submitted`, `under_review`, `approved`, `rejected`) and a reply code A/B/C/D; “approved as noted” is reply code B here but a status on shop drawings, and an engineer cannot enter reply code B or C by hand (RC-30). | M7 required-deliverable register and one consultant decision vocabulary |
| Approval history for calibration | ProjectSubmittalStatusChange, ShopDrawingEvent and ProjectSubmittalEvent keep histories; submittal history is deleted with the submittal; ProjectChange is pruned after 30 days when a project's documents are processed (RC-31). | M18 durable events |
| Project archive and cancellation | ProjectStatus exists; deletion removes history (table above). | M3 / M7 archive retention |

These are code findings. Neither task's feature was built or evaluated during this revision.

## 4. One target architecture

```text
Project files / uploads / OneDrive
    -> complete project document registry + immutable content versions
    -> background extraction/OCR/CAD conversion and geometry artifacts
    -> content-supported classification and scope attribution
    -> central domain processors + persisted source relationships
    -> canonical domain records + engineer-confirmed overlays
       |-> domain APIs -> every tab, including Drawings and Interfaces
       |-> durable engineering events, evidence and project memory
       |-> dependency engine -> only affected outputs become stale
    -> explicit Active Task Context per platform action (ephemeral; M30)
    -> after M11: project-filtered RAG + ProjectContextBuilder
    -> task-specific AI or deterministic engineering calculation
    -> proposals / review / authorized confirmation -> retained history
```

Reusable global knowledge is a separate governed namespace. Project corrections and decisions cannot become company-wide facts merely by being saved or reviewed in a project.

Preserve the distinctions between source observations, classification, attribution, domain business status, approved engineering values, and AI-proposed memories. The document registry, central artifact storage and domain tables remain authoritative owners; memory provides governed context over them.

## 5. Mandatory cross-tab reuse contract

**If a drawing version has already been successfully processed for a required capability, another tab consumes that persisted result. Opening another tab does not repeat the same extraction.**

“Processed” must be tracked by capability and version, not one Boolean. A file can have complete text extraction but incomplete geometry or interface interpretation.

### Shared processing registry and artifacts — owned by M7

For each project/document version, persist:

- Immutable content hash and source identity; page/component/sheet IDs, revision lineage and provenance.
- Stage/capability: text/OCR, CAD conversion, sheet mapping, physical equipment, geometry, interface observations, quantities, classification, visual evidence and domain projection.
- Reader/parser/schema/profile/rules versions, relevant configuration fingerprint and dependency versions.
- Status: pending, running, complete, partial, failed, cancelled, stale or explicitly not applicable; coverage, held items and failure reasons.
- Saved output artifact IDs, producing job, timestamps and last-good result with honest freshness.
- One idempotency key per stage/input fingerprint, with concurrent-job deduplication.

Default semantic/context outputs are project-scoped. Pure byte-derived artifacts can be shared only under an explicit access-safe content-reuse contract; shared bytes do not share project approval, attribution or corrections.

### Example across tabs

| Action | What should happen |
|---|---|
| A drawing is first ingested | Background processing stores source observations, sheet/coordinate mapping, equipment and available geometry. |
| Open Drawings | Read stored identity, revisions, scope, review state and evidence. |
| Open Interfaces | Reuse equipment, physical anchors, floors and evidence. Read an existing compatible interface projection, or display its missing/stale status. |
| User requests missing interface analysis | Run only missing interface interpretation/projection against the stored artifacts; do not repeat completed OCR/conversion/device extraction. |
| Open BOQ/IFC | Consume the applicable stored quantities and approved mappings, keeping IFC and Design Sheet BOQ lineage separate. |
| Open calculations | Read stored inputs/results; source or parameter mutations queue only affected recalculations. |
| Open memory or ask an agent | Retrieve applicable facts/corrections/evidence, not the entire drawing again. |
| Open Compliance | Read the stored page ledger, atomic requirements, evidence bundles and assessment states for the current specification version; a missing stage is shown as missing, not re-extracted on read. |
| Open Engineering Workload | Read the stored calculation snapshot built from the canonical deliverable registers; a changed approval queues one recalculation, the page does not recompute. |
| User requests Fresh reread | Explicitly invalidate/re-run the selected stages, with reason, budget and retained prior history. |

Reprocessing is justified by changed content, a missing/incomplete artifact, an incompatible processing/profile change, changed relevant dependencies, or an explicit fresh-read request. A renamed/moved identical file changes its location/context; reuse its pure extraction when compatible while reevaluating contextual classification/relationships. A parser change requires an explicit compatibility decision, not automatic reprocessing of every project.

Viewing/downloading source evidence may serve the original bytes or precomputed images. That is not permission for ordinary page-load handlers to parse, run OCR, call models or mutate business truth.

### Required integration proof — M7, M10, M11, M24 and M25

At M10–M11, exercise every implemented consumer using M7 artifacts. Repeat the same proof with Project Memory at M24–M25 when that consumer exists; its later delivery does not block earlier consumer acceptance.

Process a synthetic drawing once, reset extraction/OCR/model counters, then open Drawings → Interfaces → BOQ → Calculations → Logs → Home → Project Memory, and, once M26–M29 exist, Compliance → Engineering Workload. For the completed compatible stages, require **zero additional extraction/OCR/model calls**, unchanged artifact IDs, unchanged business records and consistent quantities/locations. Repeat with concurrent tabs, worker restart, renamed identical content, one changed revision and one incomplete stage. Only the affected/missing stage may run when an authorized processing action/event schedules it.

M8 and M12 reuse these geometry/evidence contracts. M21 indexes the stored extraction; it does not introduce a second PDF-reading pipeline. M26's page ledger and atomic-requirement extraction run as M7 stages over the same registry, and M28 reads the M7 deliverable registers; neither introduces its own reader or its own register.

## 6. Consistency decisions across the plans and tasks

| Topic | Consolidated decision |
|---|---|
| Milestone naming | One canonical M1–M31 sequence. Numbers are stable identifiers and are not renumbered when work is added; delivery order follows prerequisites (section 7). Historical IDs are mapped in the appendix; source PDFs and acceptance reports retain their original names. |
| Task phase numbering | Task One and Task Two each number their own Phases 0–7. Those phases are stages inside M26–M29 (appendix table) and are reported under the milestone, never as “Phase 3” alone. A phase may start when its milestone's prerequisites are met; integration and release wait for the milestone gate. |
| Workflows build on shared infrastructure | Task One's retrieval, evidence verification and “structured memory” and Task Two's facts, evidence and history are consumers of M7, M11, M16, M18, M19, M21 and M22. No compliance-only retrieval index, context builder, evidence store, event log or deliverable register is built; a workflow that needs one before its owner milestone exists waits or delivers only the parts that do not need it. |
| Deterministic authority over AI | Both tasks and the redesign plan say the same thing; it is one platform rule. Deterministic validators (M26), the workload formula (M28) and geometry checks (M8) are authoritative. AI may split, locate, extract bounded facts, compare, explain, draft and propose; it cannot override a failed check, approve itself, write to approved records or replace a formula. |
| Unknown is never complete | Task One's fail-closed states and Task Two's `UNKNOWN`/provisional rule are one principle, also used by M6 UNKNOWN, M10 honest states and M12 held proposals: an unread page, missing proof, undiscovered scope or missing input is reported as such, never as compliant, approved, complete or zero load. |
| One consultant decision vocabulary | Shop drawing revisions (`approved_as_noted` status) and material submittals (reply code B) record the same consultant decision differently. M7 defines one canonical decision set (approved, approved as noted, revise and resubmit / not approved, rejected, clarification requested, superseded, reply not on file) at submission and, for compliance statements, clause level. Task One's closed-loop outcomes and Task Two's approval percentages read this one model. |
| “Approved as noted” and finality | Whether “approved as noted” counts as final approval for workload is a company policy, not a code default. M3 records the decision; M7 stores it as versioned, auditable configuration; M28 applies it and shows the mapping in every drill-down. Until recorded, it does not count as final. Home and the Drawings summary currently count approved-as-noted as approved; M28 must not reuse those aggregates, and the submittal numerator needs the reply-code migration first (RC-32, RC-37). |
| Assessment state versus exported response | Task One's nine assessment states are internal and authoritative. The company's response wording exported to the consultant (Comply, Noted, Complied with remark, Not applicable, By others, Deviation, Clarification required) is derived from them through a recorded mapping; a response cannot read Comply unless the state is `COMPLIES_EVIDENCED` with eligible citations. Existing exports and approval gates remain the regression baseline. |
| Historical answers and global knowledge | Approved answers from other projects are wording guidance only (Task One tier 8) and never evidence. They live in the governed global namespace of section 4 under M3's promotion rule: statement approval promotes wording, not facts, and the retrieval result carries the originating project, reviewer and date. The knowledge base's verified responses are tier 7, project-local decisions stay project-local. Today approval promotes every answered row, reviewed or not; M3's promotion rule treats existing learned rows as ungoverned until reviewed (RC-33). |
| Accuracy gate rule | Task One's acceptance (98% accepted-compliance precision, 90% recovery, zero unresolved critical false positives) uses the same frozen-cohort rules as M4: declared denominators, at least 12 independently reviewed matched cases per evaluated field or population, otherwise `NOT ESTABLISHED`; AI-drafted labels are provisional. One scorer convention serves M4, M13, M27 and M25. |
| Evidence contract once | Task One's evidence item (source hash, page/region, original and normalized value, method/version, freshness, confidence, reviewer decision) is the M7 typed evidence primitive that M16 also consumes. Task Two's strength reasons and contract-value sources cite the same primitive. |
| Workload facts have owners | Contract value and currency, employee capacity with effective periods, assignment ownership shares, required-deliverable scope and stream applicability are new facts added to the M1 ownership matrix; M3 names who may record and override each (the engineering manager for capacity, shares, strength overrides and applicability). They are domain records under M7, not spreadsheet inputs of the workload page. |
| No continuous retraining | Task One (compliance labels) and Task Two (strength overrides) both forbid continuous retraining. Overrides and reviews become labeled examples held by M19/M23 governance; any later model improvement needs a separately curated, evaluated dataset and the M25 acceptance route. Fine-tuning stays a post-foundation extension. |
| Staged rollout and flags | Both tasks release behind a feature flag with rollback. The platform has no flag mechanism today; M26 introduces one per-project, server-enforced flag convention that M27, M28 and M29 reuse. While a flag is off, the existing approved workflow stays authoritative, exactly as Task One's definition of done states. |
| Project Team tab | Section 9 previously placed Team outside milestone scope. Task Two makes the engineering workload view the first delivered content of that tab (M28/M29). O&M, Reports and Settings remain outside scope. |
| Memory versus domain truth | Existing domain owners stay canonical. Add typed facts/projections and event/evidence links; avoid independently editable duplicate BOQ, drawing or approval stores. |
| “Read once” responsibility | Central artifact production belongs to M7; consumer conversion to M10; reliability and invalidation to M11. Memory consumes the results. |
| AI sequencing | AI extraction/verification belongs to M4 and classification assistance to M6. Project RAG and new optional agent expansion follow M11. Existing drawing-agent code still needs drawing-workflow acceptance. |
| PostgreSQL timing | Design compatible schemas early. Rehearse and schedule migration at M11 after ownership/workflows stabilize; require a proven PostgreSQL path before production memory rollout. |
| Manual memory timing | Align schema, evidence and durable-event contracts with M7. Deliver manual memory through the unified sequence after the core is stable; do not wait for embeddings to preserve history. |
| Memory automation order | Implement durable events and conflict/revision rules before M23 automatic memory capture. The unified milestone sequence places these prerequisites before automation. |
| Critical authority | Engineer decisions outrank automation. A correction to inference does not silently supersede an approved external requirement; retain conflict and use the appropriate confirmation process. |
| Revision semantics | Distinguish latest uploaded, latest issued and latest approved by document/system/entity lineage. Store effective time and recording time. |
| Geometry and symbols | Use visible physical equipment and verified coordinate transforms; labels identify equipment but do not establish its position. Schedules corroborate instead of duplicating physical items. |
| Drawing validation | Safer candidate Apply must be reviewed, ported and retested against current preparation code. Existing coordination/coverage code receives gap tests; it is not discarded or automatically accepted. |
| Apply draws approved changes only (OD-14) | Approved-only drawn set per RD-M1 decision A / OD-14 option (a); implemented by owner commit bb5871d (`_drawn`, backend/app/redesign/service.py:695), pending the owner's recorded confirmation in the M3 answer sheet (docs/milestones/M3/M3-DECISION-PACK.md). The two tests that pinned the old rule were replaced on the branch (commit e4fa306). M5 still owns the preparation-gate enforcement, archive write and read-back items; OD-15..OD-17 remain open. |
| Quality evidence | Functional tests, real-model accuracy, real AutoCAD behavior, independent AI review and engineer/human sign-off remain separate claims. |
| Budgets and sources | Reuse existing valid permissions only within their exact scope. This roadmap creates no experimental allowance, default-model selection, backfill or live cutover. |
| Future extensions | Full knowledge graphs, fine-tuning, advanced proactive alerts, change-impact analysis and handover packages remain post-foundation extensions. Global-promotion control and basic stale-dependency propagation are required earlier. |
| Active task context versus memory (plan v1.1) | Every button-driven AI action starts from an explicit Active Task Context (project, task type, system, revision, floor/zone, selected entities and files, attachments, user inputs, current step, temporary outputs). It is workflow state, not memory: it is isolated to its project and selection, may expire, and never becomes a project fact by being saved. Only M31's promotion step moves confirmed facts, decisions, approvals, corrections, meaningful events and validated lessons into Project Memory. The ProjectContextBuilder (M22) takes task context as its first input. Existing per-job payloads and per-request selections (BackgroundJob rows, the scoped drawing review) are the nearest current behavior and are not an explicit task context. |
| Memory plan renumbering (v1.0 → v1.1) | The v1.1 plan renumbers its milestones M1–M14. The unified numbers do not change: v1.1 M5 (Active Task Context & Workflow State) is M30 and v1.1 M13 (Task Result Feedback & Memory Promotion) is M31; the other twelve keep their U2 unified numbers. The appendix carries both mappings. v1.1's production acceptance gate (no broad automatic promotion until isolation, revision, evidence, task-context, correction, RAG-filter and insufficient-evidence tests pass) is adopted as an M23 and M31 exit condition. |
| Historical versus current memory (OD-20) | Historical and superseded memories stay available to the AI when relevant, as context and audit history. Normal engineering decisions use the latest valid authoritative state; history is never the default decision source. M19 keeps superseded values queryable, M20 summaries and M22 context mark them as history, and retrieval ranks the current authoritative state first. |
| Structured conflict resolution (OD-21) | An engineer's resolution of a conflict is durable memory with a structured rationale, not free text alone: selected value, rejected or overridden value(s), reason, supporting evidence, authority basis, engineer, timestamp, and the applicable revision and scope. M18 records it as an event and M19 as the authoritative resolution. |
| Recurring conflicts (OD-22) | When the same conflict (same scoped fact identity, same competing sources, same revision and scope) appears again, the stored resolution is applied automatically and the engineer is not asked again; the application is recorded as an event citing the original resolution. It is reopened only when materially stronger or higher-authority evidence appears, or when the applicable scope or revision changes enough to invalidate the previous resolution. M19 defines the identity and reopening tests; M23 and M31 may propose but never widen them. |
| Promotion with provenance (OD-23) | Repeated validated project knowledge may be promoted into the governed global namespace under the M3 promotion rule (promoter still to be decided, OD-02). The promoted record keeps its links to every contributing project memory and evidence item; promotion never drops provenance. Applies to learned compliance answers (M27), review rulings, the symbol library and memory candidates (M23, M31). |
| Global knowledge provenance (OD-24) | Every learned global rule or pattern is traceable to all contributing project memories and evidence, so that “which projects taught the system this rule, and on what evidence?” is answerable. M21 indexes global items with their provenance; M25 measures provenance coverage. |

## 7. Single delivery sequence — M1–M31

Use this sequence for planning, issue titles, progress reporting and completion records. The prerequisite column names technical dependencies. Earlier work remains credited to its assessed snapshot. Adding milestones neither resets completed work nor declares an incomplete milestone accepted.

Default delivery order (numbers are identifiers, not positions):

```text
M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 → M9 → M10 → M11
  → { M12 → M13 }  ∥  { M26, M28 }  ∥  { M14 → M15 → M16 → M17 → M30 }
  → M18 → M19 → M20 → M21 → M22 → M23 → M31
  → { M27, M29 } → M24 → M25
```

Braces hold work that may proceed in parallel once its own prerequisites are met. M26 and M28 start after M11 alongside the drawing and memory tracks; M30 (active task context) follows the memory foundation and precedes the context builder; M31 (task-result promotion) follows automatic capture; M27 and M29 follow the shared retrieval/context and event milestones; M24 and M25 close after every workflow consumer exists.

Design and isolated preparation may overlap where prerequisites allow, but integration and release must satisfy the stated gates. Shared event/evidence contracts start at M7; their complete memory features are delivered later. Quality instrumentation starts with the foundation and closes at M25.

| Milestone | Scope | Current assessed status | Prerequisites |
|---|---|---|---|
| M1 | Data Requirements, Ownership & Current-State Map | accepted historical snapshot (27 September 2026); refreshed for the current code on 6 October 2026, independent verification ACCEPT WITH NOTES; 18 proposed owners and 4 owner decisions await M3. | Baseline; no earlier milestone |
| M2 | Baseline & Error Inventory | historical independent review ACCEPT WITH NOTES (RD-M1, 3 October 2026); refreshed for the current code on 6 October 2026, independent verification ACCEPT WITH NOTES; 32 of 35 findings still open, 22 new candidates, RD-M1 handoff decisions A–D open for M3/M5. | M1 |
| M3 | Ownership, Access & Memory Policy | Prior assessment exists; boundary decisions incomplete. | M1, M2 |
| M4 | Extraction Reliability | partial active implementation; reviewed candidate work exists separately; not accepted. | M1, M2, M3 |
| M5 | Safe Apply & AutoCAD Block Library | candidate and race correction exist; final correction acceptance and active integration unverified/not present in inspected code. | M2, M3, M4 |
| M6 | Central Document Classification & Attribution | Classification V2 code/inspector foundations present; not formally accepted. | M4 |
| M7 | Central Processing, Relationships & Domain Records | document worker, domain records and some dependencies exist as five unrelated stores; unified contract is incomplete (RC-36). | M3, M4, M5, M6 |
| M8 | Deterministic Geometry, Placement & Coordination | geometry/coverage components present; critical wall-index foundation remains missing. | M5, M7 |
| M9 | Historical Backfill, Registry Completeness & Validation | repair/backfill tooling exists; complete migrated-project validation is not demonstrated. | M6, M7 |
| M10 | Database-Driven Tab Migration | many DB-backed views exist; residual read-time production prevents full acceptance. | M7, M8, M9 |
| M11 | Stabilization, Dependency Engine & Legacy Cleanup | jobs, deduplication, heartbeats, recovery, fingerprints and metrics exist; final unified stabilization is incomplete. | M7, M9, M10 |
| M12 | Multi-Stage AI & Visual Review | placement/coordination/floor-review and preparation UI code present; complete rendered-review/repair acceptance missing. | M8, M11 |
| M13 | Real-Project Accuracy Validation & Release | no completed fresh multi-project acceptance found. | M5, M8, M11, M12 |
| M14 | Project Memory Database & Service Foundation | No dedicated memory schema/service. | M3, M7, M11 |
| M15 | Structured Project Facts | Partial in existing domain tables. | M14 |
| M16 | Memory Evidence & Source Traceability | Partial domain provenance. | M14, M15 |
| M17 | Project Memory Tab & Manual Review | Missing dedicated page. | M15, M16 |
| M18 | Durable Engineering Events & Timeline | Partial domain histories and ephemeral changes. | M7, M14, M16, M17 |
| M19 | Conflicts, Corrections & Revision Authority | Partial domain supersession. | M15, M16, M18 |
| M20 | Versioned Project Summaries | Current-state dashboard only. | M18, M19 |
| M21 | Project-Scoped RAG | Dedicated chunk/vector retrieval missing. | M11, M16, M19, M20 |
| M22 | Shared Project Context Builder | Task-specific strings and budgets only. | M15, M19, M20, M21, M30 |
| M23 | Controlled Automatic Memory Capture | Domain proposals exist; general memory capture missing. | M18, M19, M22, M30 |
| M24 | Memory Integration Across Engineering Workflows | Multiple AI workflows; common memory contract missing. | M10, M13, M17, M22, M23, M27, M29, M30, M31 |
| M25 | End-to-End Quality, Operations & Acceptance | AI usage metrics only. | M11, M13, M24 |
| M26 | Compliance Evidence, Requirements & Deterministic Verification | Clause handling, autofill, approval and export exist; an advisory five-value technical status exists but is not evidence-gated; no page ledger use, evidence items, immutable approved version or validators; compliance GETs write and scan today (RC-22, RC-27, RC-34). | M3, M4, M6, M7, M11 |
| M27 | Compliance Retrieval, Drafting, Outcomes & Release | Prompt-level guidance and cross-project learned answers only. | M18, M19, M21, M22, M23, M26 |
| M28 | Engineering Workload Engine & Dashboard | No workload, capacity, share or snapshot code; inputs partly owned (section 3); Home and Drawings aggregates count approved-as-noted as approved and must not be reused (RC-37). | M1, M3, M7, M9, M11 |
| M29 | Workload Scenarios, Strength Proposals, Calibration & Release | Missing. | M15, M16, M18, M22, M28 |
| M30 | Active Task Context & Workflow State | Missing dedicated implementation; per-job payloads and per-request selections only. | M3, M7, M14 |
| M31 | Task Result Feedback & Memory Promotion | Missing. | M18, M19, M22, M23, M30 |

The current extraction closure belongs to **M4** and safe Apply closure to **M5**. Their historical evidence retains the source-plan identifiers; use the appendix when reading those reports. Task One is M26 and M27; Task Two is M28 and M29; their phase mapping is in the appendix. Memory plan v1.1's new milestones are M30 and M31; its renumbering is in the appendix. Owners and dates remain to be assigned against actual capacity and validation scope.

## 8. Milestone details — M1–M31

### M1 — Data Requirements, Ownership & Current-State Map

**Prerequisites:** Baseline; no earlier milestone.

**Status:** accepted historical snapshot (27 September 2026); refreshed for the current code on 6 October 2026, independent verification ACCEPT WITH NOTES; 18 proposed owners and 4 owner decisions await M3.

**Refresh of 6 October 2026:** [docs/milestones/M1/refresh-2026-10-06/](milestones/M1/refresh-2026-10-06/M1R-ACCEPTANCE-RECORD.md). 173 new field rows in the accepted 22-column schema; 108 drift entries on accepted rows; all 149 GET handlers classified (67 with read-time work, no model calls); 73 override writers with 54 recorded weaknesses; 38 processing stages mapped against the section 5 contract; 25 ownership conflicts recorded for M3; 65 roadmap/package corrections; 57 unknowns. Static reading at commit 771001e; no code run, no database opened. Independent verification: first pass CHANGES REQUIRED (seven documentation corrections, applied), second pass **ACCEPT WITH NOTES** (static reading only; S1–S4 citations not mechanically span-checked). Records: [verification-01](milestones/M1/refresh-2026-10-06/evidence/verification-01/README.md), [verification-02](milestones/M1/refresh-2026-10-06/evidence/verification-02/REPORT.md).

Reuse the existing 155-field ownership inventory and consumer map. Add current interface scans/reviews, drawing preparation/coverage, source artifacts, project memory and every new producer introduced since that snapshot. Identify all GET-side work and manual-override writers.

Add the facts Task One and Task Two introduce, each with an owner, producer and override writer: compliance assessment state, atomic requirement, evidence item and consultant decision; contract value and currency; employee capacity and effective period; assignment ownership share; required Shop Drawing and Material Submittal scope and stream applicability. Record where each is held today (section 3) and that the estimation register is not the design projects' contract-value owner.

**Deliver:** refreshed field/producer/persistence/consumer/freshness/override matrix; shared artifact capability map; protected behavior list; traceable changes from the accepted M1 snapshot.

**Exit:** every critical fact/artifact has exactly one authoritative owner, producer and consumer contract; no unresolved conflict over whether the tab, processor or memory service owns it. Do not redo the accepted audit wholesale.

### M2 — Baseline & Error Inventory

**Prerequisites:** M1.

**Status:** historical independent review ACCEPT WITH NOTES (RD-M1, 3 October 2026); refreshed for the current code on 6 October 2026, independent verification ACCEPT WITH NOTES; 32 of 35 findings still open, 22 new candidates, RD-M1 handoff decisions A–D open for M3/M5.

Retain the 35-finding inventory and frozen Golden evidence. Add a delta inventory for current preparation/coverage/agents and interface changes; distinguish fixed, still open, superseded by verified behavior and not yet reproduced.

**Refresh of 6 October 2026:** [docs/milestones/redesign/RD-M1-refresh-2026-10-06/](milestones/redesign/RD-M1-refresh-2026-10-06/M2R-ACCEPTANCE-RECORD.md). All 35 RD-M1 findings classified against the current code: 0 fixed, 32 still open, 1 superseded by tests (F027, detector coverage only), 2 not reproducible without the Golden drawing; both Critical and all nine High findings still open, owned by M5 (14), M8 (14), M12 (3), M7 (2), M10 (1), M18 (1). No RD-M2 candidate correction is in the active tree and the candidate patch no longer applies. The code added since RD-M1 (preparation, coverage, agents, markup, scoped review) adds 18 pipeline stages and 22 unreviewed, code-confirmed candidate findings (Critical 1: the stored preparation gate is never read by Apply; High 8, among them `proposed` review changes drawn without approval, the agents-off fallback erasing the nearest symbol of any name, the structured-text floor review standing in for visual review, `ai_policy` unconsulted on every drawing AI path, company-wide review rulings matching without the device). Tests: 116 passed over seven suites (RD-M1 ran 78 over four; the same four now give 81); 12 of 43 stages have no test and none reaches `apply()`. Golden Case GC-01 is not reproducible in the repository; the record names the RD-M1 evidence file that pins each missing input. The accepted RD-M1 package re-verifies against its manifest. Independent verification: first pass CHANGES REQUIRED (three record defects, applied), second pass **ACCEPT WITH NOTES** (static reading plus one independently reproduced test run; GC-01 instance findings need the owner's machine). Records: [verification-01](milestones/redesign/RD-M1-refresh-2026-10-06/evidence/verification-01/README.md), [verification-02](milestones/redesign/RD-M1-refresh-2026-10-06/evidence/verification-02/REPORT.md). The candidate finding "`proposed` review changes drawn without approval" and RD-M1 F002 describe the code at the surveyed commit 771001e; at owner commit bb5871d the `_drawn` rule is approved-only (OD-14 option (a), decided by code, pending the owner's confirmation), and the re-verification of that finding against the current code belongs to M5.

**Exit for the refreshed baseline:** a reviewer can trace current findings to source/input/output hashes and reproduce bounded cases. Do not treat historical findings as automatically fixed by new UI or AI code.

### M3 — Ownership, Access & Memory Policy

**Prerequisites:** M1, M2.

**Status:** Prior assessment exists; boundary decisions incomplete. OD-14 (handoff A: must review-sourced drawing changes be explicitly approved before they are drawn) is decided by code at owner commit bb5871d, pending the owner's confirmation.

**Deliverable and acceptance gate:** Align with refreshed M1: fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse. Recorded contract accepted before authoritative memory writes.

Also record, as owner decisions this roadmap cannot take: whether “approved as noted” is final approval for workload (section 6); that approved compliance answers from other projects are wording guidance in the global namespace and never evidence; the project AI/provider policy that bounds what compliance evidence may be transmitted; who may record and override contract value, capacity, ownership shares, stream applicability and strength scores (Task Two names the engineering manager); and that an archived or cancelled project keeps its engineering history and drops out of active workload without deletion.

### M4 — Extraction Reliability

**Prerequisites:** M1, M2, M3.

**Status:** partial active implementation; reviewed candidate work exists separately; not accepted.

Preserve existing source-bound native/OCR/AI extraction, BOQ row provenance, last-good readings, partial progress and targeted verification. Close the complete 17-gate matrix, not only the 24-document R32 experiment.

Required closure work:
1. Resolve named residual extraction/BOQ/decision-association defects or obtain explicit recorded scope amendments.
2. Complete applicable fresh validation with frozen code, labels, models, request/token/time bounds and exact denominators.
3. Retain dates/sections, BOQ part-number/quantity/same-row evaluation and expanded sealed pilot scope. The recorded target is 30 projects / 1,200 distinct-content documents / 40 sheets, subject to documented availability and applicable amendments.
4. Resolve the label-review requirement outside the run-specific AI-reviewed reference-set amendment.
5. Select/promote an eligible profile only through its separate decision process; prepare the exact version and rollback proposal.
6. Port accepted candidate changes onto an isolated copy of the current merged tree, preserving current interfaces/preparation behavior; run compatibility and final independent acceptance on the chosen acceptance tree.

**Exit:** governing field thresholds and critical false-accept gates pass; source/row/page loss is explicitly accounted; fresh/generalization evidence and integration are accepted. The policy's critical-error objectives are not replaced by the simpler 98% headline. Report the exact cohort, field, population gate and amended rule in each result.

The frozen R32 field gates include at least 98% accepted precision, at least 90% correct recovery and at least 12 matched cases per evaluated field. Preserve its negative-control and association gates as well. The broader policy targets zero observed adjudicated critical false accepts and requires no unresolved critical false acceptance; passing a percentage alone does not override that requirement. R32 scores identity, revision and decision, so its success would not close dates/sections or BOQ evidence.

**Evidence:** [current closure](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-CLOSURE-DECISION-2026-10-06.md>) and the linked acceptance matrix. Verification 42's zero-request rehearsal establishes preparation behavior only.

M4 closes extraction of project documents, Design Sheets and BOQ. It does not close specification-clause extraction for compliance; that cohort, with the same gate rules, is M27's. M26 reuses M4's accepted readers and page accounting rather than adding a reader.

### M5 — Safe Apply & AutoCAD Block Library

**Prerequisites:** M2, M3, M4.

**Status:** candidate and race correction exist; final correction acceptance and active integration unverified/not present in inspected code.

Complete the correction review, port onto current preparation logic in isolation and explicitly enforce:
- Only approved changes with current source/approval snapshots are eligible; uncertain placement needs its specified engineer confirmation.
- Resolve CT1/CT2/CR against the current installation library.
- Fail on incomplete scripts; require standalone completion markers, saved-output validation and insert/erase read-back.
- Hold conflicting/failed preparation results; enforce gates at the server boundary.
- Unique exclusive outputs, cancellation, retry/idempotency and atomic publication/finalization; clean up a newly created output if final commit fails.
- Preserve source drawings; archive publication is a separate controlled action.

**Exit:** approved inserts/erases reconcile exactly; missing blocks, script errors, stale approvals and commit failure publish nothing. Reproduce the concurrent publication test. Reuse old real-AutoCAD evidence only where the relevant CAD-facing code is unchanged; otherwise validate the changed behavior on isolated drawings.

### M6 — Central Document Classification & Attribution

**Prerequisites:** M4.

**Status:** Classification V2 code/inspector foundations present; not formally accepted.

Retain SUPPORTED/HINT/AMBIGUOUS/UNKNOWN and independent freshness, component evidence and versioned context. Add/verify drawing attribution states OUR_SCOPE, LIKELY_OUR_SCOPE, RELATED_EXTERNAL, REFERENCE_ONLY and UNKNOWN with conflict handling, lineage and originator evidence.

Use stored extraction first, bounded AI where justified and a declared audit of confidently supported results. Keep initial routing hints separate from final content-supported classification to avoid an extraction/classification dependency cycle.

**Exit:** shadow evaluation reports per-type precision/recall, mixed-component recall, system/scope accuracy, false-supported and false-OUR_SCOPE rates. Classification changes no approval or engineer-confirmed business state.

### M7 — Central Processing, Relationships & Domain Records

**Prerequisites:** M3, M4, M5, M6.

**Status:** document worker, domain records and some dependencies exist as five unrelated stores (project_documents, document_readings, document_classifications, background_jobs, page/result caches), each with its own keys; unified contract is incomplete (RC-36).

Implement the shared registry/artifact contract in section 5. Add central orchestration over domain-specific DRF, drawing, interface, submittal, BOQ, calculation and knowledge processors. Persist document/page/component → drawing revision/submittal cycle/comment/reply/decision relationships with provenance and freshness.

Keep raw observations and proposed values separate from effective engineer-confirmed values. Write audit/event/outbox records in the same transaction. Define typed facts and source adapters for future memory. Add project access, archive retention and controlled global promotion at the domain boundary.

For the workflow milestones, M7 also owns: the typed evidence item (section 6) that M16, M26 and M29 consume; the one consultant decision vocabulary applied to shop drawing revisions, material submittal revisions and, later, compliance clauses, with a reviewed migration of today's two vocabularies; the required-deliverable registers for Shop Drawings and Material Submittals (distinct required items under the approved scope, duplicates and revisions folded into one identity, applicability recorded, unknown kept distinct from zero), extending the existing required-drawings service rather than adding a second register; and page-level stage coverage in the processing registry, which is the page ledger M26 reads.

**Exit:** rerunnable/recoverable processors produce stored domain records and relationships once; APIs can serve them without opening originals; engineer decisions survive reassessment. Shared physical equipment IDs and coordinate systems support Interfaces, BOQ and Drawings consistently.

### M8 — Deterministic Geometry, Placement & Coordination

**Prerequisites:** M5, M7.

**Status:** geometry/coverage components present; critical wall-index foundation remains missing.

Begin with the original bounded wall-index task: effective layer inheritance, block transforms, visibility/off/frozen/no-plot handling including viewport state, configurable wall-layer allow-lists and layer composition reporting. Validate a simple sheet and a rotated view as well as the exposed Golden drawing.

Then stage doors, ceilings, obstacles, containment, rotation, spacing, coverage and post-change clash checks. Reuse interface physical-symbol associations and shared artifact coordinates. Do not anchor equipment to labels.

**Exit:** no placement justified by invisible/non-wall geometry; accepted cases have valid transforms, containment and clearance; known failures improve without new critical clashes. Unresolved geometry remains held.

### M9 — Historical Backfill, Registry Completeness & Validation

**Prerequisites:** M6, M7.

**Status:** repair/backfill tooling exists; complete migrated-project validation is not demonstrated.

Replace the explicit 2,000-file refusal with bounded, checkpointed discovery that accounts for every eligible file. Backfill in isolated preview batches from verified backups, using accepted readers/classifiers. Reconcile duplicate identities, revisions, source links and merged legacy references while preserving manual decisions.

**Deliver:** target-project inventory, pre/post snapshots, per-record disposition, before/after differences, held cases, rollback and resume evidence.

**Exit:** 2,000/5,000/10,000-file tests account for eligible = processed + skipped + failed + unresolved; no unexplained loss or business change. Apply no historical repair merely because this roadmap exists.

Backfill also populates the M7 required-deliverable registers and consultant decisions for existing projects from their folders and reply records, with per-record disposition; unknown scope stays unknown. M28's calibration (M29) depends on this history being complete and honestly labelled.

### M10 — Database-Driven Tab Migration

**Prerequisites:** M7, M8, M9.

**Status:** many DB-backed views exist; residual read-time production prevents full acceptance.

Migrate each consumer using the matrix in section 9: compare old/new outputs, preserve controls, switch incrementally and observe. Move synchronization, extraction, status reconstruction and state mutation from ordinary GETs into background processors or explicit commands.

**Exit:** ordinary tab reads perform no source parsing/OCR/model calls/folder scans or business writes; completed compatible artifacts are reused across tabs. Evidence download/view may serve bytes. Show pending, stale, missing, partial and conflict states honestly. Home migrates after its inputs.

The Compliance tab's specification finding, verification and stale checks move off ordinary reads here. Task One's “read endpoints must not process or mutate” and Task Two's “read endpoints are side-effect free” are this gate; M26 and M28 are built to it from the start and need no later migration.

### M11 — Stabilization, Dependency Engine & Legacy Cleanup

**Prerequisites:** M7, M9, M10.

**Status:** jobs, deduplication, heartbeats, recovery, fingerprints and metrics exist; final unified stabilization is incomplete.

Use a shared dependency graph for source versions → artifacts → domain records → calculations/approvals → summaries/context. A shop drawing change must not invalidate unrelated Design Sheet BOQ. Reassess only the affected scope.

Test concurrent tabs, worker restarts, retries, partial failures, cache/version changes and stale-result prevention. Remove a legacy producer only after all consumers are verified. Monitor queue age, processing throughput, reuse, p95 latency, unknown/held rates and model drift.

Rehearse PostgreSQL migrations, driver/configuration, transactions, locking, constraints, connection pooling and backup/restore once the architecture is stable; record execution and rollback separately.

**Exit:** no material duplicate processing; reliable recovery and accurate invalidation; accepted database path for production scale. This is the gate before project RAG, new optional agent expansion, and the workflow milestones M26 and M28.

The dependency graph carries two workflow edges: specification version, product selection, evidence association or rule version → compliance assessment (M26 marks the approved version stale, never overwrites it); consultant decision, required scope, assignment, capacity or configuration version → workload snapshot (M28 queues one recalculation for the affected project and employees only).

### M12 — Multi-Stage AI & Visual Review

**Prerequisites:** M8, M11.

**Status:** placement/coordination/floor-review and preparation UI code present; complete rendered-review/repair acceptance missing.

Feed AI only geometrically valid candidates and relevant project constraints. Persist structured proposals/evidence, render the proposed changes, obtain separate visual review, then allow a bounded repair loop with deterministic rechecks. Structured-text review alone cannot prove visual placement.

**Exit:** deterministic and visual evidence agree; uncertain/conflicting proposals remain held; repair rounds, calls, failures, latency and review burden are visible; engineers approve before Apply. Demonstrate improvement against a frozen baseline.

### M13 — Real-Project Accuracy Validation & Release

**Prerequisites:** M5, M8, M11, M12.

**Status:** no completed fresh multi-project acceptance found.

Use reviewed fresh cases across project types, layouts, rotations and disciplines. Evaluate physical location, full equipment coverage, orientation, coordination, visual quality, repeated-run variation and safe Apply. Count missed/held devices and failed drawings.

**Exit:** predeclared gates pass with no unresolved critical error promoted; independent review, engineer acceptance, operational limits, backup/rollback and staged release are recorded. One exposed drawing and passing unit tests cannot support a general accuracy claim.

### M14 — Project Memory Database & Service Foundation

**Prerequisites:** M3, M7, M11.

**Status:** No dedicated memory schema/service.

**Deliverable and acceptance gate:** Migrations, scoped repository and lifecycle; same-project evidence constraints; atomic mutation/audit; no cross-project reads/writes. Reuse M7's event/evidence primitives.

### M15 — Structured Project Facts

**Prerequisites:** M14.

**Status:** Partial in existing domain tables.

**Deliverable and acceptance gate:** Deterministic adapters plus typed extensions with entity/floor/system/units, provenance and effective time. Fact questions answered without an LLM; no second editable owner.

### M16 — Memory Evidence & Source Traceability

**Prerequisites:** M14, M15.

**Status:** Partial domain provenance.

**Deliverable and acceptance gate:** Multiple sources per claim; immutable version/hash/page/region/clause or authorized user action; accessible exact source; critical confirmations have acceptable evidence/authority.

### M17 — Project Memory Tab & Manual Review

**Prerequisites:** M15, M16.

**Status:** Missing dedicated page.

**Deliverable and acceptance gate:** Overview, facts, decisions, approvals, corrections, changes, issues, lessons, search/filter/pin and candidate review; permitted manual lifecycle works end to end.

### M18 — Durable Engineering Events & Timeline

**Prerequisites:** M7, M14, M16, M17.

**Status:** Partial domain histories and ephemeral changes.

**Deliverable and acceptance gate:** Durable before/after events, actor, rationale, effective/recording times and source, transactional delivery and deduplication; query what/when/why across modules.

Consultant decisions at submission and clause level, capacity and ownership-share changes, strength overrides, configuration version changes and task-result events (the completion of a platform action under an Active Task Context, M30/M31) are durable events here, with effective and recording time. Task One's closed-loop consultant outcomes (M27) and Task Two's historical calibration (M29) read this timeline; neither keeps its own.

### M19 — Conflicts, Corrections & Revision Authority

**Prerequisites:** M15, M16, M18.

**Status:** Partial domain supersession.

**Deliverable and acceptance gate:** Scoped fact identity, authority precedence, confirmed corrections, effective periods, historical queries and atomic supersession. One applicable truth or explicit unresolved conflict; approved-source conflicts are reviewed. Per OD-20..OD-22: superseded values stay queryable as history and are never the default decision source; an engineer's resolution is stored with the structured rationale (selected value, rejected values, reason, evidence, authority basis, engineer, timestamp, revision and scope); a recurrence of the same conflict applies the stored resolution automatically, recorded as an event citing it, and is reopened only on materially stronger or higher-authority evidence or an invalidating change of scope or revision.

Authority precedence covers the workflow cases: a consultant's recorded decision outranks an inferred status; an engineer's approved assessment outranks an AI draft; the engineering manager's recorded override outranks a proposed strength score, with the previous value retained; a superseded specification revision or datasheet makes evidence ineligible without deleting it. Rejected wording, products and evidence patterns are retained as warning memory for retrieval, never as an automatic rejection rule.

### M20 — Versioned Project Summaries

**Prerequisites:** M18, M19.

**Status:** Current-state dashboard only.

**Deliverable and acceptance gate:** Versioned source-linked summaries, event watermark and stale flags; significant events refresh/invalidate them; stale summaries never override facts. Summaries present the latest valid authoritative state and mark superseded history as history (OD-20).

### M21 — Project-Scoped RAG

**Prerequisites:** M11, M16, M19, M20.

**Status:** Dedicated chunk/vector retrieval missing.

**Deliverable and acceptance gate:** After M11: index shared stored extraction with project/system/revision/status/location/model metadata, filter before ranking, keep global/project namespaces separate. No duplicate PDF reader.

The index carries the metadata Task One's consultant-first retrieval filters on: source class (consultant specification, approved product, exact-model datasheet, certificate or listing, approved submittal and reply, calculation/schedule/drawing/BOQ/design fact, verified knowledge, historical approved answer), eligibility, freshness and exact manufacturer/model. Compliance retrieval is a query against this index; it is not a second index.

### M22 — Shared Project Context Builder

**Prerequisites:** M15, M19, M20, M21, M30.

**Status:** Task-specific strings and budgets only.

**Deliverable and acceptance gate:** One ProjectContextBuilder chooses minimum facts/corrections/events/summary/RAG, applies authority/temporal rules and token budgets, and returns source IDs, uncertainty and version. Project/access/dependency-aware caching.

The builder ranks the latest valid authoritative state first and includes historical or superseded memories only as marked context and audit history when the task needs them (OD-20). The builder is task-aware (plan v1.1): its first input is the Active Task Context of the current platform action (M30), and retrieval is filtered by that context's project, system, revision, floor/zone and selections before ranking; a drawing review opened on floor L6 revision R2 must not silently pull L7 or R1 unless history is required. Task One's eight-tier consultant-first order and Task Two's “explanations only from stored inputs” are context policies of this builder, selected per task. The builder records provider, model, prompt version, project policy, evidence IDs, source hashes, usage and result for every attempt, which closes the AiUsage gap in section 3; failed, partial, refused, timed-out and budget-stopped attempts stay visible and never replace prior good evidence.

### M23 — Controlled Automatic Memory Capture

**Prerequisites:** M18, M19, M22, M30.

**Status:** Domain proposals exist; general memory capture missing.

**Deliverable and acceptance gate:** After M19 core: useful candidates from workflow results, approvals, corrections and meaningful system events (plan v1.1), schema/evidence validation, scoped deduplication and risk policy; workflow noise and temporary selections ignored, critical inference never auto-confirmed. Broad automatic promotion stays off until the v1.1 production acceptance gate passes: project isolation, revision correctness, evidence traceability, task-context isolation, correction priority, RAG filtering and the insufficient-evidence failure behavior.

Task One's rejection memory (rejected wording, products and evidence patterns from consultant outcomes) and Task Two's labelled strength overrides are captured under this policy as candidates with evidence; neither becomes a confirmed fact, a rule or training data by being captured. Candidates for global promotion carry links to every contributing project memory and evidence item (OD-23); a recurring conflict is not a new candidate but an application of its stored resolution (OD-22).

### M24 — Memory Integration Across Engineering Workflows

**Prerequisites:** M10, M13, M17, M22, M23, M27, M29, M30, M31.

**Status:** Multiple AI workflows; common memory contract missing.

**Deliverable and acceptance gate:** Connect compliance, drawings/review/preparation, interfaces, BOQ/IFC, material submittals, calculations and engineering workload through one task-context and memory contract (plan v1.1: every workflow creates its Active Task Context, retrieves through the one builder, and reports completion through M31); consistent corrections and versioned outcomes. The compliance adapter is M27's and the workload adapter M29's; M24 proves that the same correction (section 10: 125 → 105), the same consultant decision and the same specification revision reach every consumer consistently.

### M25 — End-to-End Quality, Operations & Acceptance

**Prerequisites:** M11, M13, M24.

**Status:** AI usage metrics only.

**Deliverable and acceptance gate:** Wrong-project/revision rates, task-context leakage (zero cross-project; near-zero stale floor/revision/selection reuse), transient-to-memory error rate (near zero), task completion traceability, critical evidence coverage, false-memory adjudication, retrieval precision, token use, duplicates, summary freshness, issue aging and agent consistency; labeled evaluations and recovery gates pass.

M25 also confirms the two workflow releases under the common scorer convention (section 6): M27's compliance cohort results and M29's calibration and manager-review record are re-read on the final tree, and their feature flags may be removed only here.

### M30 — Active Task Context & Workflow State

**Prerequisites:** M3, M7, M14.

**Status:** Missing dedicated implementation. BackgroundJob rows carry per-job payloads and the scoped drawing review passes floor/revision selections per request; neither is an explicit, isolated task context.

**Source:** Project Memory Master Plan v1.1, milestone M5.

**Deliverable and acceptance gate:** A task_run / workflow-state model and lightweight service: project, task type, system, revision, floor/zone, selected entities and files, attachment IDs, user inputs, current step and temporary outputs, created by each button-driven platform action (`POST /projects/{id}/tasks/context`, `PATCH /tasks/{id}/context`, `POST /tasks/{id}/execute`, `POST /tasks/{id}/complete`), referenced by every AI request, isolated to its project and selection, and expirable (TTL/cleanup). It is not project memory: nothing in it becomes a fact by being saved. Exit: every AI action has explicit, isolated temporary context; a task opened in project B retrieves B only; a temporary selection (for example a detector model tried during a check) is not a confirmed fact when the task ends; the ordinary-read rule of M10 holds (creating a task context is an explicit action, not a GET side effect).

### M31 — Task Result Feedback & Memory Promotion

**Prerequisites:** M18, M19, M22, M23, M30.

**Status:** Missing.

**Source:** Project Memory Master Plan v1.1, milestone M13.

**Deliverable and acceptance gate:** Standardised completion events for every platform action, and the policy that decides which outputs become structured facts, durable events, open issues, corrections or candidate memories, with evidence and the task context recorded; everything else is discarded with the task. Promotion of repeated validated knowledge to the global namespace keeps full provenance to the contributing projects and evidence (OD-23, OD-24). Exit: completed tasks improve project memory without saving transient state; each promoted item is traceable to its task context and evidence; the v1.1 production acceptance gate (M23) passes before promotion is broadened beyond reviewed candidates.

### M26 — Compliance Evidence, Requirements & Deterministic Verification

**Prerequisites:** M3, M4, M6, M7, M11.

**Status:** Clause handling, deterministic autofill, AI drafts, approval and export exist (Task One baseline items 1–8, with items 5 and 7 corrected as in section 3); an advisory five-value technical status with `insufficient_evidence` exists but is not evidence-gated; no page ledger use, atomic requirements, evidence items, product/model identity, immutable approved version or validators. The listed compliance GET handlers write or scan today; removing that is part of the exit (RC-22, RC-27, RC-34).

**Source:** Task One Phases 0–3.

Freeze the baseline behavior as regression tests (Phase 0), then build on M7's registry and evidence primitives:

- Page ledger over the specification's stored extraction: every page visited, skipped, unsupported, failed or unattempted with a reason; all in-scope pages stay in the denominator; an unread page blocks any claim of complete assessment.
- Atomic requirements split from compound clauses, keeping the original clause and its AND/OR/condition/exception/alternative relationships, with source hash, page, region, clause reference, exact text, requirement type, expected value/model/unit/standard/approval, extraction version, confidence and review provenance. Uncertain splitting goes to engineer review.
- Exact manufacturer and model identity with proposed, submitted, approved, rejected, superseded and installed states; evidence items as M7 typed evidence; controlled ingestion of datasheets, certificates, listings, approvals and test reports from the existing datasheet library, with hash, validity and exact-model verification and engineer review before a source becomes trusted. Automatic retrieval, if introduced, follows Task One's source, hash, URL/time and review rules.
- A deterministic verification library: exact model association, numeric comparison, unit conversion, standards and editions, certificate identity/validity/scope, approvals, revision currency, applicability, cross-source conflict and completeness of mandatory proof. Every requirement resolves to exactly one of the nine assessment states; missing or conflicting mandatory proof fails closed.
- Invalidation through the M11 dependency graph; the prior approved version is kept immutable and marked stale.
- The per-project feature flag convention (section 6); the existing response wording is derived from the assessment state through the recorded mapping while the flag is on, and the existing workflow is untouched while it is off.

**Exit:** on frozen fixtures, 100% of declared pages are accounted for; every extracted requirement links to its page and region; every positive state has an eligible evidence item for the correct project and exact model; every missing mandatory proof fails closed; no read endpoint processes or mutates; the Task One baseline regression suite passes. No model call is needed to pass this gate; AI drafting is M27.

### M27 — Compliance Retrieval, Drafting, Outcomes & Release

**Prerequisites:** M18, M19, M21, M22, M23, M26.

**Status:** Prompt-level guidance and cross-project learned answers only.

**Source:** Task One Phases 4–7.

Consultant-first retrieval as an M22 context policy over the M21 index; bounded AI tasks (split, locate, extract bounded facts, compare against verified evidence, explain conflicts, draft wording, propose citations, prioritise review) producing structured outputs that remain drafts; citations that show source name, revision, page and clause/region and open the cited page; `ALTERNATIVE_FOR_APPROVAL` with the unmet requirement, alternative, differences, evidence, risks and the explicit consultant approval still required.

Engineer review of every non-informative requirement; immutable approved statement versions; Excel/PDF export of the approved version with citations; consultant outcomes (approval, approved as noted, rejection, clarification, supersession) at clause and submission level recorded as M18 events under the M7 decision vocabulary and linked to the submitted version, evidence bundle and product; rejection memory captured under M23.

**Exit:** on a fresh, frozen, independently engineer-reviewed cohort spanning consultants, contractors, layouts, systems, products, scans, tables, compound clauses, units, standards, approvals, missing evidence, conflicts, deviations and alternatives: accepted-compliance precision ≥ 98%, recovery ≥ 90% per declared field/population, zero unresolved critical false-positive compliance claims, 100% of positive claims with current eligible citations, 100% of exports from an approved immutable version, reconciliation finds no lost, duplicated or silently overwritten approved record, every assessment change explainable from source, rule/model or reviewer history. Fields below the 12-case minimum report `NOT ESTABLISHED`. Baseline and candidate are compared under declared conditions and the limitations published. Release is per project behind the flag, with false positives, review load, latency and cost monitored and rollback verified.

### M28 — Engineering Workload Engine & Dashboard

**Prerequisites:** M1, M3, M7, M9, M11.

**Status:** No workload, capacity, share or snapshot code; the Project Team tab is a placeholder; inputs partly owned (section 3). The submittal GET handlers write or scan today, so the side-effect-free read exit is work, not a given; the existing Home and Drawings aggregates count approved-as-noted as approved and the submittal numerator needs the reply-code migration first (RC-34, RC-37).

**Source:** Task Two Phases 0–4.

Confirm the authoritative sources from the refreshed M1 matrix and measure their completeness (Phase 0). Read required Shop Drawing and Material Submittal scope and final approval from the M7 registers and decision vocabulary (Phase 1); only the canonical final approved decision counts, “approved as noted” per the M3 policy, duplicates and revisions never raise the denominator, an undiscovered scope is `UNKNOWN` and an explicitly not-required stream has its weight removed and the rest normalised to 1.00.

Deterministic engine (Phase 2): versioned configuration for BasePoints, stream weights, cost bands and factors, strength factors, ownership factor ranges, capacity and status thresholds, all recorded as proposals until the manager approves a version; EngineeringRemainingFactor, CostFactor from banded, currency-normalised contract value, StrengthFactor, OwnershipFactor, ProjectLoad, employee totals, load and overload percentages and status bands; immutable snapshots reproducible from recorded inputs, with missing-data flags and documented fallbacks. Handover and Testing and Commissioning status are not inputs. Ownership shares in one responsibility pool must total 1.00 unless an additive support exception is recorded and reported separately.

Strength review (Phase 3, deterministic part): the 1–5 level with manager accept/override, previous value, reason, actor, time, evidence and effective version; proposals at this milestone come from recorded rules over stored facts only and cite their sources; cost is never an input.

Dashboard and drill-down (Phase 4) under the Project Team tab behind the flag: employee summaries, ranked contributions, the complete calculation, effective weights, counts and percentages per stream, cost and strength provenance, share validation, assumptions, override and audit history, filters, last calculation time and configuration version. Plain-language driver explanations are generated from the snapshot's inputs and agree with them exactly.

**Exit:** Task Two acceptance criteria 1–13, 15 and 16 pass on fixtures and on at least one real project set under review by the engineering manager: every assigned project under the right employee; zero load only when both applicable streams are finally approved or explicitly not required; non-final statuses and unknown scope never count; the displayed calculation reproduces the stored load exactly; no double counting across shares; cost banded and not reused in strength; read endpoints side-effect free; snapshots reproducible; regression tests for zero-required streams, unknown data, duplicates, revisions, multi-currency, splits, reopened approvals and configuration change.

### M29 — Workload Scenarios, Strength Proposals, Calibration & Release

**Prerequisites:** M15, M16, M18, M22, M28.

**Status:** Missing.

**Source:** Task Two Phases 3 (model-assisted part), 5, 6 and 7.

Non-destructive redistribution scenarios with before/after load, share validation and an explicit authorised apply action; model-assisted strength proposals through M22 from M15 facts with M16 evidence, confidence and cited reasons, held when evidence is insufficient; calibration of weights, bands, factors and thresholds on completed historical periods from the M18 timeline, comparing predicted load with actual effort and delivery outcomes, publishing sample sizes and uncertainty, preserving the prior configuration and requiring manager approval for a new effective version; dated snapshot export.

**Exit:** Task Two acceptance criteria 9, 10, 14, 17 and 18 pass: proposals show documented reasons and sources; overrides are fully audited; scenarios change nothing until applied; the manager confirms the explanations name the true stored drivers with no invented facts; a calibrated configuration version is approved, or the proposed values stay labelled as proposals. Release per project behind the flag, compared with manager assessment and monitored for data quality and override rate.

## 9. Explicit tab coverage and migration contracts

| Tab / workflow | Reuse now present | Remaining integration contract |
|---|---|---|
| File Sync | Registry, pending states, worker jobs | Complete discovery beyond 2,000 files, checkpoints and stage-only scheduling. |
| Documents / Project Info | ProjectDocument and structured project fields | Documents keeps authoritative source-document semantics; file inventory remains separate. Read facts with DRF provenance, without reopening sources. |
| Drawings / review | ShopDrawing/Revision/issues; IFC drawing review | Stored scope/revision/approval and review projections; remove GET reconciliation; reuse extraction, geometry and evidence. |
| Interfaces | Saved scans, physical-symbol association, per-drawing reports, acceptance and fresh-run controls | Shared input artifact IDs with Drawings/IFC; persist schedule projection; no ordinary-read writes; explicit missing-stage/fresh actions. |
| Drawing Preparation / Redesign | Placement, coverage, coordination, review/gate UI | Trustworthy wall inputs, rendered independent review, approved-only server-enforced Apply, source-version consistency. |
| BOQ — Design Sheet | Stored lines, corrections, revisions, extraction provenance | Reliable accepted reader and central row artifacts; preserve manual edits. |
| BOQ — IFC | Drawing records, device extraction, comparisons | Reuse physical equipment/quantity artifacts; preserve IFC lineage separately from shop/Design Sheet records. |
| Floor Schedule | Persisted schedule and mappings | Move folder synchronization off GET; preserve ambiguous-row manual material choices on updates. |
| Battery / CBS, amplifier, 24V calculations | Deterministic calculation services and persisted inputs/results | Consume typed approved equipment/current/load constraints; recalculate only affected dependencies. Existing panel-battery support does not alone establish every CBS workflow. |
| Material Submittals | Register, revisions, replies, history, package services | Persist review-cycle/comment/reply/decision relationships under the one consultant decision vocabulary; a required-submittal register distinct from filed documents; protect overrides and approved revision state. Feeds M28. |
| Proposed Materials | BOQ/calculation-derived lists | Stored, versioned projection with source and engineer overrides. |
| Compliance / Knowledge | Statements, approval fingerprint and version, audit, lexical knowledge, learned answers, deterministic autofill | Project-local decisions, controlled global promotion, source indexing and stale checks off ordinary reads (M10); then M26 assessment states, page ledger, atomic requirements, evidence items and validators, and M27 retrieval, cited drafting, immutable versions, cited exports and consultant outcomes. The existing approval and export gates are the regression baseline throughout. |
| Datasheet library / Datasheet Engine | DatasheetDocument, PartDatasheetLink, BrandSupplier, company library | Controlled ingestion as evidence with hash, exact-model verification, validity and review (M26); served to compliance and to workload strength reasons through the shared evidence item, never as unverified attachments to a prompt. |
| Samples | Existing sample workflow | Dedicated domain contract and evidence; classification aids discovery only. |
| Logs | Existing register/report views | Pure reports over canonical revisions and domain records, using the one consultant decision vocabulary. |
| Engineering Workload (Project Team) | Placeholder navigation entry; users with roles; single design engineer per project | M28 engine, snapshots and dashboard over M7 registers and decisions; M29 scenarios, model-assisted strength and calibration. No separate copy of deliverable status. |
| Home | ProjectStateService and actions | Aggregate stored upstream truth after those consumers migrate. |
| Project Memory | Dedicated UI/service missing | Manual review, facts, evidence, timeline, summary and later retrieval through shared domain owners. |
| Cause & Effect / Estimation where applicable | Within original M1 inventory scope | Inventory and preserve supported behavior; defer new features explicitly rather than imply completion. |
| O&M / general Reports / Settings | Navigation entries marked soon | Outside the named milestone scope unless separately added; their placeholders do not count as implemented deliverables. The Project Team entry is now in scope through M28/M29. |

Each row needs a consumer acceptance record: input owner, source/artifact IDs, API contract, freshness, override behavior, legacy/new comparison, no-read-work check and rollback switch.

## 10. Shared memory architecture and acceptance scenarios

The memory capabilities in the unified sequence build on the accepted core. The governing plan is v1.1: four persistent layers (structured, semantic, episodic and summary memory) with an ephemeral Active Task Context in front of retrieval. Build a dedicated FastAPI service with the plan's memory endpoints (list, facts, summary, events, create, patch, confirm, reject, pin, retrieve, rebuild-summary) and its task endpoints (create/patch task context, execute, complete), a React memory tab, worker jobs and reusable workflow adapters. Every workflow sends explicit task context from its button or action; the frontend never relies on an implicit session.

The relational additions include project_memories, typed project_facts, decisions/corrections (or normalized subtype equivalents), project_events, project_summaries, memory_evidence and protected memory_audit_log. Extend existing document/domain identities with immutable versions and chunks; do not create competing document registries. Supporting access, conflicts, promotion, processing/outbox and retrieval traces need explicit contracts.

The detailed delivery stages are M14–M25 with M30 and M31, with policy established at M3 and shared infrastructure at M7. Active task context (M30) follows the memory foundation and precedes the context builder (M22). Durable events (M18) precede summaries (M20); conflicts and authority (M19) precede automated capture (M23), which precedes task-result promotion (M31). Project RAG (M21) follows stabilization (M11) and supplies the shared context builder (M22). Cross-workflow integration (M24) precedes final acceptance (M25).

**Required memory acceptance examples:**
- Project A Edwards / Project B Siemens: B returns only its applicable Siemens state and permitted sources.
- Eaton R0 / Edwards R1: default valid-current query and explicit R0 query return the correct evidence-backed values.
- Correction 125 → 105: every applicable consumer gets 105, with the old value and reasoning retained.
- Unsupported AI approval: stays unconfirmed; no model confidence or pin can grant authority.
- Source withdrawal/revision: affected facts, summaries, contexts and generated outputs become stale and require appropriate review.
- Token pressure: preserve required evidence or report insufficient context; never silently drop the critical constraint.
- Drawing review opened on floor L6, revision R2 (v1.1): the context builder does not silently pull L7 or R1 unless history is required for the task.
- Temporary selection (v1.1): a detector model the user tries during a check is not a confirmed project fact when the task ends, unless approved or promoted through M31.
- Insufficient evidence: the system says so rather than inventing a memory.
- Recurring conflict (OD-22): the same conflict appears in a later revision with the same sources and scope; the stored resolution is applied without asking, the application is logged citing the original; a higher-authority source then appears and the conflict reopens.
- History as context (OD-20): a query about R0 returns the superseded value marked as history; a current design query returns the latest valid authoritative value and never the superseded one by default.
- Provenance (OD-24): for any global rule, the system lists the projects and evidence items it was learned from.

## 11. Verification performed for this consolidation

**Focused isolated regression run: 89 passed, 0 failed, 0 errors; 45 deprecation warnings; 217.47 seconds.** The captured source was copied without the live .env, database, uploads or archive. The existing test fixtures created temporary databases/libraries/uploads and used scripted providers where AI behavior was exercised.

Suites: test_document_classification_v2.py, test_document_processing_v2.py, test_file_sync_v2_processing.py, test_project_state.py, test_redesign.py, test_drawing_prep.py, test_fa_efficiency.py.

Evidence: [test summary and command](roadmap-evidence/2026-10-06/TEST-RESULTS.md), [JUnit results](roadmap-evidence/2026-10-06/focused-tests-r2.xml), [test log](roadmap-evidence/2026-10-06/focused-tests-r2.log).

The first attempt had 40 passes and 49 setup errors, all caused by access denial to the default pytest temporary directory. It was rerun with an explicit isolated --basetemp; no application/test code was changed to obtain the passing run. This environment failure is recorded in the test summary.

These checks concern the captured code and named scenarios only. They do not validate engineering accuracy on unseen project drawings, real-model extraction, real AutoCAD output, PostgreSQL operation, production data completeness or formal milestone acceptance.

The [candidate integration comparison](roadmap-evidence/2026-10-06/candidate-integration-check.json) confirms the active redesign service differs from the M5 correction's declared file hash and that its dedicated Apply test file is absent. Semantic inspection also confirms the old proposed-change/archive-publication behavior remains; hash difference alone was not treated as proof of absence.

The [post-review drift check](roadmap-evidence/2026-10-06/source-drift-check.json) found one externally changed file: backend/tests/test_scoped_drawing_review.py, which is not in the focused test selection. Application files and the selected test sources still matched the captured hashes at that check; HEAD remained 831c198. The reported tests apply to the captured snapshot.

**Revision U3 check (branch tree, Linux container, Python 3.13, no Tesseract).** The 551 snapshot files were rehashed against the branch: 548 match (after line-ending normalisation), and the three that differ are `backend/app/review/service.py`, `backend/tests/test_drawing_review_outcome.py` and `backend/tests/test_scoped_drawing_review.py`, all changed by the later commit “Clarify incomplete drawing review outcomes”. The seven focused suites plus those two review test files were rerun: **106 passed, 3 skipped, 1 failed**. The one failure, `test_an_ocr_failure_on_one_page_is_noted_and_the_batch_continues`, needs Tesseract on the PATH and did not reach the OCR seam in this container; it is an environment gap, not a regression. The section 3 findings on compliance and workload were taken on the same tree by reading the source; no feature was built or evaluated.

**Revision U5 (M1 refresh).** Five read-only surveys and three scribe passes produced the records under docs/milestones/M1/refresh-2026-10-06/ from the branch at 771001e; the acceptance record there states the method, the counting units, the inconsistencies kept side by side and the independent verifier's disposition. The accepted M1 package is unchanged; its 108 known drifts are listed in the delta, not edited in place. Independent verification: first pass CHANGES REQUIRED (seven documentation corrections, applied), second pass **ACCEPT WITH NOTES** (static reading only; S1–S4 citations not mechanically span-checked). Records: [verification-01](milestones/M1/refresh-2026-10-06/evidence/verification-01/README.md), [verification-02](milestones/M1/refresh-2026-10-06/evidence/verification-02/REPORT.md).

**Revision U7 (owner decisions, M4 test health).** Five owner decisions on memory (OD-20..OD-24) recorded; see docs/milestones/M3/M3-DECISION-PACK.md §2a. M4 evidence: the 18 extraction suites on the current tree gave 214 passed, 13 skipped, 3 failed at c2f2671; all three failures were test defects (a hand-built provider fixture missing the later `_max_turns` attribute; two OCR tests that faked the OCR call without stubbing `ocr_available`) and were repaired in commits 32d8d55 and 58c838a with the diagnosis under docs/milestones/M4/evidence/. The diagnosis also raised a code question for M4: with Tesseract absent, a changed scan is stored as an empty “complete” reading with no note, against the unknown-is-never-complete rule.

**Revision U8 (bb5871d drawn rule; M2 refresh note).** Owner commit bb5871d ("Run the drawing review and preparation on the Claude subscription", on `merge/candidate`, author mohamedr69, 6 October 2026 23:41 +0400) changed `_drawn` in backend/app/redesign/service.py from drawing `approved` changes plus a `proposed` review change not rejected by the orchestrator, to drawing `approved` changes only (`git show bb5871d -- backend/app/redesign/service.py`). This is RD-M1 handoff decision A and M3 decision pack OD-14 option (a) implemented in code; it is decided by code, pending the owner's recorded confirmation in the M3 answer sheet (this session asked for that confirmation and it had not been filed). The branch commit e4fa306 ("Pin the approved-only drawn rule in the interface-module test") updated backend/tests/test_redesign.py to assert the new rule; the session handover (docs/SESSION-HANDOVER-2026-10-07.md) records that test_redesign.py and test_drawing_prep.py together give 30 passed on the Linux container after that change. The roadmap (section 3, section 8 M2 and M3 entries, section 6, section 14) and the M2 refresh record (docs/milestones/redesign/RD-M1-refresh-2026-10-06/) describe the pre-bb5871d behavior, which was true at the snapshot they surveyed (commit 771001e); nothing else in this revision changed.

**Revision U6 (M2 refresh).** Two read-only surveys, one test run and two scribe passes produced the records under docs/milestones/redesign/RD-M1-refresh-2026-10-06/; the acceptance record states the gate reading (met for the repository-reproducible part, not claimed for GC-01 instance findings), the two orchestrator mapping decisions (coordination findings F008–F012 owned by M8 with M12 for the rendered check; RD-M6 proposals mapped to M7/M10/M18) and the inconsistencies kept visible. Independent verification: first pass CHANGES REQUIRED (three record defects, applied), second pass **ACCEPT WITH NOTES** (static reading plus one independently reproduced test run; GC-01 instance findings need the owner's machine). Records: [verification-01](milestones/redesign/RD-M1-refresh-2026-10-06/evidence/verification-01/README.md), [verification-02](milestones/redesign/RD-M1-refresh-2026-10-06/evidence/verification-02/REPORT.md).

## 12. Historical milestone cross-reference

This appendix is for locating earlier PDFs, files and acceptance records. These historical identifiers are not additional milestones or separate roadmaps. Their status belongs to the exact snapshot named by their evidence; use M1–M31 for all new execution tracking.

| Unified milestone | Original source reference | Scope |
|---|---|---|
| M1 | Platform M1 | Data Requirements, Ownership & Current-State Map |
| M2 | Redesign RD-M1 | Baseline & Error Inventory |
| M3 | Project Memory PM-M0 | Ownership, Access & Memory Policy |
| M4 | Platform M2 | Extraction Reliability |
| M5 | Redesign RD-M2 | Safe Apply & AutoCAD Block Library |
| M6 | Platform M3 | Central Document Classification & Attribution |
| M7 | Platform M4 | Central Processing, Relationships & Domain Records |
| M8 | Redesign RD-M3 | Deterministic Geometry, Placement & Coordination |
| M9 | Platform M5 | Historical Backfill, Registry Completeness & Validation |
| M10 | Platform M6 | Database-Driven Tab Migration |
| M11 | Platform M7 | Stabilization, Dependency Engine & Legacy Cleanup |
| M12 | Redesign RD-M4 | Multi-Stage AI & Visual Review |
| M13 | Redesign RD-M5 | Real-Project Accuracy Validation & Release |
| M14 | Project Memory PM-M1 | Project Memory Database & Service Foundation |
| M15 | Project Memory PM-M2 | Structured Project Facts |
| M16 | Project Memory PM-M4 | Memory Evidence & Source Traceability |
| M17 | Project Memory PM-M3 | Project Memory Tab & Manual Review |
| M18 | Project Memory PM-M8 | Durable Engineering Events & Timeline |
| M19 | Project Memory PM-M10 | Conflicts, Corrections & Revision Authority |
| M20 | Project Memory PM-M5 | Versioned Project Summaries |
| M21 | Project Memory PM-M6 | Project-Scoped RAG |
| M22 | Project Memory PM-M7 | Shared Project Context Builder |
| M23 | Project Memory PM-M9 | Controlled Automatic Memory Capture |
| M24 | Project Memory PM-M11 | Memory Integration Across Engineering Workflows |
| M25 | Project Memory PM-M12 | End-to-End Quality, Operations & Acceptance |
| M26 | Task One Phases 0–3 | Compliance Evidence, Requirements & Deterministic Verification |
| M27 | Task One Phases 4–7 | Compliance Retrieval, Drafting, Outcomes & Release |
| M28 | Task Two Phases 0–4 | Engineering Workload Engine & Dashboard |
| M29 | Task Two Phases 3 (model-assisted), 5–7 | Workload Scenarios, Strength Proposals, Calibration & Release |
| M30 | Project Memory v1.1 M5 | Active Task Context & Workflow State |
| M31 | Project Memory v1.1 M13 | Task Result Feedback & Memory Promotion |

### Project Memory Master Plan v1.1 renumbering

The v1.0 identifiers (PM-M0–PM-M12) in the table above and in [milestones/project-memory/README.md](milestones/project-memory/README.md) refer to plan v1.0. Plan v1.1 renumbers to M1–M14; the unified numbers are unchanged.

| v1.1 milestone | v1.1 name | v1.0 equivalent | Unified |
|---|---|---|---|
| M1 | Project Memory Database | PM-M1 | M14 |
| M2 | Structured Project Facts | PM-M2 | M15 |
| M3 | Manual Memory UI | PM-M3 | M17 |
| M4 | Evidence & Trust | PM-M4 | M16 |
| M5 | Active Task Context & Workflow State | new | M30 |
| M6 | Project Summary Memory | PM-M5 | M20 |
| M7 | Project RAG Integration | PM-M6 | M21 |
| M8 | Task-Aware Retrieval Engine | PM-M7 | M22 |
| M9 | Episodic Memory & Workflow Timeline | PM-M8 | M18 |
| M10 | Automatic Memory Candidate Extraction | PM-M9 | M23 |
| M11 | Conflict & Revision Resolution | PM-M10 | M19 |
| M12 | Agent & Platform Workflow Integration | PM-M11 | M24 |
| M13 | Task Result Feedback & Memory Promotion | new | M31 |
| M14 | Analytics, Quality & Production Governance | PM-M12 | M25 |

v1.1's execution waves (Foundation M1–M4, Workflow Context M5–M6, Intelligence M7–M9, Automation M10–M11, Integration M12–M13, Scale M14) are consistent with the unified delivery order in section 7.

### Task phase cross-reference

| Task phase | Where it is delivered | Shared milestones it depends on |
|---|---|---|
| Task One P0 Baseline and contracts | M2 delta inventory (compliance baseline), M3 decisions, M26 schema/metric freeze | M1, M2, M3 |
| Task One P1 Requirements and traceability | M26 | M4 readers, M7 registry page coverage |
| Task One P2 Evidence and product identity | M26 | M7 evidence item, M11 invalidation |
| Task One P3 Deterministic verification | M26 | — |
| Task One P4 Retrieval and AI drafting | M27 | M21 index, M22 context builder |
| Task One P5 Review, export and outcome memory | M27 | M18 events, M19 authority, M23 capture |
| Task One P6 Independent evaluation | M27 exit gate | M4 scorer convention |
| Task One P7 Controlled rollout | M27 release; flags removed at M25 | M24, M25 |
| Task Two P0 Ownership and baseline | M1 refresh, M3 decisions, M28 completeness measure | M1, M3 |
| Task Two P1 Canonical progress | M7 registers and decision vocabulary; M9 backfill | M7, M9 |
| Task Two P2 Deterministic engine | M28 | M11 dependency edges |
| Task Two P3 Strength proposal and review | M28 (manual and rule-based), M29 (model-assisted) | M15, M16, M22 |
| Task Two P4 Dashboard and drill-down | M28 | M10 read gate |
| Task Two P5 Redistribution scenarios | M29 | — |
| Task Two P6 Historical calibration | M29 | M18 timeline |
| Task Two P7 Controlled rollout | M29 release; flags removed at M25 | M24, M25 |

## 13. Delivery and acceptance records

For every milestone, maintain one compact record containing:
- Requirement → current implementation → remaining gap → action → acceptance evidence.
- Exact code/artifact/data snapshot, model/profile/schema/policy versions where applicable.
- Named tests and actual results; functional, mocked, real-model and real-AutoCAD results separated.
- Independent review disposition and any engineer/owner-only decision still required.
- Integration status in the active tree, source/evidence retention, rollback and known limitations.

Use the complete [historical M2 acceptance matrix](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-ACCEPTANCE-MATRIX.md>) for M4 rather than replacing it with a shorter checklist. This unified roadmap does not silently descope its dates/sections, BOQ, sealed-pilot, label or accepted-tree requirements.

## 14. Immediate next work

1. M1 ownership and the M2 drawing baseline are refreshed (section 8, M1 and M2). Next: close the M3 access, retention, authority and reuse contracts together with the 25 ownership conflicts the M1 refresh recorded (18 proposed owners and 4 owner decisions), the owner decisions section 6 leaves to M3 (“approved as noted” finality, historical-answer namespace, who records capacity, shares, value and strength) and RD-M1's open Apply decisions A–D (approved-only drawing, archive write, AutoCAD run on an isolated copy, stored PC-A library paths), which M5 needs before it starts — A is decided by code at owner commit bb5871d, pending the owner's confirmation; B–D remain open.
2. Close M4 extraction reliability using the complete existing acceptance matrix and exact frozen validation rules.
3. Complete M5 safe Apply correction review and integration, preserving current drawing preparation behavior.
4. Deliver M6–M11: classification, shared processing (including the one consultant decision vocabulary, the required-deliverable registers and the typed evidence item), deterministic geometry, backfill, tab migration and stabilization. Verify that Drawings and Interfaces reuse the same compatible stored artifacts.
5. Complete M12 visual review and M13 real-project drawing validation; in parallel start M26 compliance evidence and M28 workload engine once M11 is accepted.
6. Complete M14–M23 with M30 and M31: governed memory storage, facts, evidence, UI, active task context, durable history, conflict control, summaries, RAG, task-aware shared context, automatic capture and task-result promotion.
7. Complete M27 compliance drafting and release and M29 workload scenarios, calibration and release, then M24 workflow integration and M25 final acceptance.

The next implementation task should name one unified milestone, its bounded scope, the snapshot it changes, its exact completion gate and evidence destination. Keep useful existing work and historical acceptance evidence.
