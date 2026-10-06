# Unified Engineering Platform Master Roadmap

Revision U2 — 6 October 2026
Scope: one integrated delivery roadmap, M1–M25, covering the platform, drawing redesign and project memory.  
Status: consolidated implementation plan and evidence-based code assessment. No milestone acceptance, live validation authorization or deployment is granted by publishing this document.

## 1. Purpose and source precedence

This is one execution roadmap numbered M1–M25 in delivery order. All milestone references in the plan use this unified numbering. Original IDs appear only in the historical cross-reference appendix and unchanged source/evidence titles and paths; they are not separate execution tracks. Shared infrastructure is built once.

Source plans, preserved byte-for-byte in this project:

- [Platform-Master-Roadmap-M1-M7.pdf](roadmap-sources/Platform-Master-Roadmap-M1-M7.pdf): core data ownership, extraction, classification, central processing, backfill, consumer migration and stabilization.
- [Redesign-Accuracy-Roadmap-RD-M1-M5.pdf](roadmap-sources/Redesign-Accuracy-Roadmap-RD-M1-M5.pdf): baseline, safe Apply, deterministic geometry, staged AI/visual review and real-project validation.
- [Engineering_AI_Project_Memory_Master_Plan.pdf](roadmap-sources/Engineering_AI_Project_Memory_Master_Plan.pdf): persistent project facts, decisions, evidence, history, summaries, retrieval and shared agent context.

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

Existing active code provides file discovery, background document processing, hash reuse, classification metadata, domain registers, BOQ, calculations, interfaces, drawing review/preparation, job recovery and audit/activity records.

The latest [historical M2 closure decision](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-CLOSURE-DECISION-2026-10-06.md>) and [17-gate acceptance matrix](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-ACCEPTANCE-MATRIX.md>) say that fresh validation, BOQ evidence, expanded sealed evaluation, accepted-tree integration and final acceptance remain open. Verification 42 accepted the **experiment preparation**, not M4 accuracy. The older declaration summary still says verification pending; the later closure and verification disposition supersede that status.

The active source retains `parse-2026-10-05.5` and `titleblock-2`; the reviewed candidate's `app/ai/evidence_reader.py`, `app/ai/ledger.py` and candidate-only corrections are not automatically present merely because their reports are in docs. The integration comparison verifies the named files are absent; the closure report provides the wider candidate-lineage analysis. Treat candidate promotion as a controlled port with compatibility evidence.

### Drawings, interfaces and redesign

**The tabs and several advanced drawing functions exist, but M5 safety acceptance and M8/M12 correctness are not established for the active code.**

- M2's packaged independent review ends with **ACCEPT WITH NOTES** after its initial corrections. That is historical audit acceptance.
- M5's packaged independent review requests correction of the approval/publication race. A correction report says **READY FOR INDEPENDENT CORRECTION REVIEW**. An accepting final correction disposition was not found in the packaged files inspected.
- Active [redesign _drawn](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/service.py:695>) permits some `proposed` review changes; active [Apply](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/service.py:1479>) copies output into the project archive when a source folder exists. This does not meet the M5 approved-only/no-implicit-publication target.
- Active Apply does not implement the candidate's verified read-back/publication transaction. Its service hash differs from the correction manifest, and `tests/test_redesign_apply.py` is absent.
- Active [wall builder](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/walls.py:151>) still uses raw-layer deny-list filtering without the planned effective-layer visibility/allow-list contract. New room coverage code cannot compensate for an untrusted wall index.
- Placement, coordination, coverage and floor-review code now exist in [drawing preparation](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/prepare.py:133>). The plan stores a preparation gate, but Apply does not enforce that stored gate. The preparation floor reviewer at [_ask_review](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/redesign/prepare.py:650>) receives structured text; this alone is not the separate visual review of rendered proposals required by M12.
- [interface geometry](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/interfaces/geometry.py:188>) already associates labels with physical symbol candidates and holds ambiguity. Preserve and reuse that work; do not assume all remaining placement and cross-discipline coordination requirements are satisfied.

These are code findings. No real DWG was generated or published during this roadmap assessment.

### Project memory and shared reuse

The dedicated memory model/service/API/UI, ProjectContextBuilder, controlled summaries and project vector-RAG pipeline are still absent in the inspected active code. Existing structured domain records, corrections, events, AI budgets and caches are reusable foundations.

Shared extraction already exists in parts: [document processing](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/document_processing.py:139>) skips unchanged content, interface scanning carries forward valid prior results, and the interface finding review can reuse rendered pictures. The implementation is not yet a universal cross-tab processing registry.

Additional gaps:

| Finding | Current evidence | Required owner milestone |
|---|---|---|
| Cross-project compliance learning | [learning.index_for](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/compliance/learning.py:139>) filters by system, not project; project sign-off supplies reusable historical answers, still subject to review. | M7 knowledge boundary + M3/M19: project-local by default; reviewed global promotion. |
| Project listing is not access isolation | [project access policy](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/routers/projects.py:425>) explicitly allows broader project opening; “mine” is a list preference. | M3 and M7 access contract: enforce allowed-project access for data, sources and jobs. |
| UI change notifications expire | [prune_changes](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_state.py:58>) removes changes older than 30 days. | M7 durable events / M18: keep ephemeral UI notifications separate from engineering history. |
| Project deletion removes history | [delete_project](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_deletion.py:64>) removes domain records and audit/correction rows. | M7 / M3: ordinary archive/deactivation and retained engineering evidence. |
| Registry still has a 2,000-file ceiling | [file enumeration](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/document_sync.py:53>) explicitly raises an error above the limit. This is not silent truncation, but is not complete large-project discovery. | M9: bounded/resumable complete discovery, including 5,000/10,000-file cases. |
| Read requests still perform work | Drawings GET can reconcile; Interfaces GET creates its row; floor schedule and IFC comparison GETs call folder synchronization; drawing review/preparation GET paths build state. | M10: background production and stored read models; no ordinary-read extraction or business mutation. |
| Shared content cache is not memory isolation | [cache reuse](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/cache.py:62>) and DocumentReading intentionally reuse content readings. | M7 artifact contract / M22: contextual outputs keyed by project and dependency versions. |

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
| User requests Fresh reread | Explicitly invalidate/re-run the selected stages, with reason, budget and retained prior history. |

Reprocessing is justified by changed content, a missing/incomplete artifact, an incompatible processing/profile change, changed relevant dependencies, or an explicit fresh-read request. A renamed/moved identical file changes its location/context; reuse its pure extraction when compatible while reevaluating contextual classification/relationships. A parser change requires an explicit compatibility decision, not automatic reprocessing of every project.

Viewing/downloading source evidence may serve the original bytes or precomputed images. That is not permission for ordinary page-load handlers to parse, run OCR, call models or mutate business truth.

### Required integration proof — M7, M10, M11, M24 and M25

At M10–M11, exercise every implemented consumer using M7 artifacts. Repeat the same proof with Project Memory at M24–M25 when that consumer exists; its later delivery does not block earlier consumer acceptance.

Process a synthetic drawing once, reset extraction/OCR/model counters, then open Drawings → Interfaces → BOQ → Calculations → Logs → Home → Project Memory. For the completed compatible stages, require **zero additional extraction/OCR/model calls**, unchanged artifact IDs, unchanged business records and consistent quantities/locations. Repeat with concurrent tabs, worker restart, renamed identical content, one changed revision and one incomplete stage. Only the affected/missing stage may run when an authorized processing action/event schedules it.

M8 and M12 reuse these geometry/evidence contracts. M21 indexes the stored extraction; it does not introduce a second PDF-reading pipeline.

## 6. Consistency decisions across the three plans

| Topic | Consolidated decision |
|---|---|
| Milestone naming | One canonical M1–M25 sequence. Historical IDs are mapped in the appendix; source PDFs and acceptance reports retain their original names. |
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
| Quality evidence | Functional tests, real-model accuracy, real AutoCAD behavior, independent AI review and engineer/human sign-off remain separate claims. |
| Budgets and sources | Reuse existing valid permissions only within their exact scope. This roadmap creates no experimental allowance, default-model selection, backfill or live cutover. |
| Future extensions | Full knowledge graphs, fine-tuning, advanced proactive alerts and handover packages remain post-foundation extensions. Global-promotion control and basic stale-dependency propagation are required earlier. |

## 7. Single delivery sequence — M1–M25

Use this sequence for planning, issue titles, progress reporting and completion records. The prerequisite column names technical dependencies; the ordered list is the default delivery order. Earlier work remains credited to its assessed snapshot. Renumbering neither resets completed work nor declares an incomplete milestone accepted.

Design and isolated preparation may overlap where prerequisites allow, but integration and release must satisfy the stated gates. Shared event/evidence contracts start at M7; their complete memory features are delivered later. Quality instrumentation starts with the foundation and closes at M25.

| Milestone | Scope | Current assessed status | Prerequisites |
|---|---|---|---|
| M1 | Data Requirements, Ownership & Current-State Map | accepted historical snapshot; update required for current code. | Baseline; no earlier milestone |
| M2 | Baseline & Error Inventory | historical independent review ACCEPT WITH NOTES. | M1 |
| M3 | Ownership, Access & Memory Policy | Prior assessment exists; boundary decisions incomplete. | M1, M2 |
| M4 | Extraction Reliability | partial active implementation; reviewed candidate work exists separately; not accepted. | M1, M2, M3 |
| M5 | Safe Apply & AutoCAD Block Library | candidate and race correction exist; final correction acceptance and active integration unverified/not present in inspected code. | M2, M3, M4 |
| M6 | Central Document Classification & Attribution | Classification V2 code/inspector foundations present; not formally accepted. | M4 |
| M7 | Central Processing, Relationships & Domain Records | document worker, domain records and some dependencies exist; unified contract is incomplete. | M3, M4, M5, M6 |
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
| M22 | Shared Project Context Builder | Task-specific strings and budgets only. | M15, M19, M20, M21 |
| M23 | Controlled Automatic Memory Capture | Domain proposals exist; general memory capture missing. | M18, M19, M22 |
| M24 | Memory Integration Across Engineering Workflows | Multiple AI workflows; common memory contract missing. | M10, M13, M17, M22, M23 |
| M25 | End-to-End Quality, Operations & Acceptance | AI usage metrics only. | M11, M13, M24 |

The current extraction closure belongs to **M4** and safe Apply closure to **M5**. Their historical evidence retains the source-plan identifiers; use the appendix when reading those reports. Owners and dates remain to be assigned against actual capacity and validation scope.

## 8. Milestone details — M1–M25

### M1 — Data Requirements, Ownership & Current-State Map

**Prerequisites:** Baseline; no earlier milestone.

**Status:** accepted historical snapshot; update required for current code.

Reuse the existing 155-field ownership inventory and consumer map. Add current interface scans/reviews, drawing preparation/coverage, source artifacts, project memory and every new producer introduced since that snapshot. Identify all GET-side work and manual-override writers.

**Deliver:** refreshed field/producer/persistence/consumer/freshness/override matrix; shared artifact capability map; protected behavior list; traceable changes from the accepted M1 snapshot.

**Exit:** every critical fact/artifact has exactly one authoritative owner, producer and consumer contract; no unresolved conflict over whether the tab, processor or memory service owns it. Do not redo the accepted audit wholesale.

### M2 — Baseline & Error Inventory

**Prerequisites:** M1.

**Status:** historical independent review ACCEPT WITH NOTES.

Retain the 35-finding inventory and frozen Golden evidence. Add a delta inventory for current preparation/coverage/agents and interface changes; distinguish fixed, still open, superseded by verified behavior and not yet reproduced.

**Exit for the refreshed baseline:** a reviewer can trace current findings to source/input/output hashes and reproduce bounded cases. Do not treat historical findings as automatically fixed by new UI or AI code.

### M3 — Ownership, Access & Memory Policy

**Prerequisites:** M1, M2.

**Status:** Prior assessment exists; boundary decisions incomplete.

**Deliverable and acceptance gate:** Align with refreshed M1: fact ownership, project access, critical confirmer, archive retention, global promotion, scoped revisions and artifact reuse. Recorded contract accepted before authoritative memory writes.

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

**Status:** document worker, domain records and some dependencies exist; unified contract is incomplete.

Implement the shared registry/artifact contract in section 5. Add central orchestration over domain-specific DRF, drawing, interface, submittal, BOQ, calculation and knowledge processors. Persist document/page/component → drawing revision/submittal cycle/comment/reply/decision relationships with provenance and freshness.

Keep raw observations and proposed values separate from effective engineer-confirmed values. Write audit/event/outbox records in the same transaction. Define typed facts and source adapters for future memory. Add project access, archive retention and controlled global promotion at the domain boundary.

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

### M10 — Database-Driven Tab Migration

**Prerequisites:** M7, M8, M9.

**Status:** many DB-backed views exist; residual read-time production prevents full acceptance.

Migrate each consumer using the matrix in section 9: compare old/new outputs, preserve controls, switch incrementally and observe. Move synchronization, extraction, status reconstruction and state mutation from ordinary GETs into background processors or explicit commands.

**Exit:** ordinary tab reads perform no source parsing/OCR/model calls/folder scans or business writes; completed compatible artifacts are reused across tabs. Evidence download/view may serve bytes. Show pending, stale, missing, partial and conflict states honestly. Home migrates after its inputs.

### M11 — Stabilization, Dependency Engine & Legacy Cleanup

**Prerequisites:** M7, M9, M10.

**Status:** jobs, deduplication, heartbeats, recovery, fingerprints and metrics exist; final unified stabilization is incomplete.

Use a shared dependency graph for source versions → artifacts → domain records → calculations/approvals → summaries/context. A shop drawing change must not invalidate unrelated Design Sheet BOQ. Reassess only the affected scope.

Test concurrent tabs, worker restarts, retries, partial failures, cache/version changes and stale-result prevention. Remove a legacy producer only after all consumers are verified. Monitor queue age, processing throughput, reuse, p95 latency, unknown/held rates and model drift.

Rehearse PostgreSQL migrations, driver/configuration, transactions, locking, constraints, connection pooling and backup/restore once the architecture is stable; record execution and rollback separately.

**Exit:** no material duplicate processing; reliable recovery and accurate invalidation; accepted database path for production scale. This is the gate before project RAG and new optional agent expansion.

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

### M19 — Conflicts, Corrections & Revision Authority

**Prerequisites:** M15, M16, M18.

**Status:** Partial domain supersession.

**Deliverable and acceptance gate:** Scoped fact identity, authority precedence, confirmed corrections, effective periods, historical queries and atomic supersession. One applicable truth or explicit unresolved conflict; approved-source conflicts are reviewed.

### M20 — Versioned Project Summaries

**Prerequisites:** M18, M19.

**Status:** Current-state dashboard only.

**Deliverable and acceptance gate:** Versioned source-linked summaries, event watermark and stale flags; significant events refresh/invalidate them; stale summaries never override facts.

### M21 — Project-Scoped RAG

**Prerequisites:** M11, M16, M19, M20.

**Status:** Dedicated chunk/vector retrieval missing.

**Deliverable and acceptance gate:** After M11: index shared stored extraction with project/system/revision/status/location/model metadata, filter before ranking, keep global/project namespaces separate. No duplicate PDF reader.

### M22 — Shared Project Context Builder

**Prerequisites:** M15, M19, M20, M21.

**Status:** Task-specific strings and budgets only.

**Deliverable and acceptance gate:** One ProjectContextBuilder chooses minimum facts/corrections/events/summary/RAG, applies authority/temporal rules and token budgets, and returns source IDs, uncertainty and version. Project/access/dependency-aware caching.

### M23 — Controlled Automatic Memory Capture

**Prerequisites:** M18, M19, M22.

**Status:** Domain proposals exist; general memory capture missing.

**Deliverable and acceptance gate:** After M19 core: useful event/conversation candidates, schema/evidence validation, scoped deduplication and risk policy; filler ignored, critical inference never auto-confirmed.

### M24 — Memory Integration Across Engineering Workflows

**Prerequisites:** M10, M13, M17, M22, M23.

**Status:** Multiple AI workflows; common memory contract missing.

**Deliverable and acceptance gate:** Connect compliance, drawings/review/preparation, interfaces, BOQ/IFC, material submittals and calculations through one context contract; consistent corrections and versioned outcomes.

### M25 — End-to-End Quality, Operations & Acceptance

**Prerequisites:** M11, M13, M24.

**Status:** AI usage metrics only.

**Deliverable and acceptance gate:** Wrong-project/revision rates, critical evidence coverage, false-memory adjudication, retrieval precision, token use, duplicates, summary freshness, issue aging and agent consistency; labeled evaluations and recovery gates pass.

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
| Material Submittals | Register, revisions, replies, history, package services | Persist review-cycle/comment/reply/decision relationships; protect overrides and approved revision state. |
| Proposed Materials | BOQ/calculation-derived lists | Stored, versioned projection with source and engineer overrides. |
| Compliance / Knowledge | Statements, audit, lexical knowledge, learned answers | Project-local decisions, controlled global promotion, source indexing and stale checks off ordinary reads. |
| Samples | Existing sample workflow | Dedicated domain contract and evidence; classification aids discovery only. |
| Logs | Existing register/report views | Pure reports over canonical revisions and domain records. |
| Home | ProjectStateService and actions | Aggregate stored upstream truth after those consumers migrate. |
| Project Memory | Dedicated UI/service missing | Manual review, facts, evidence, timeline, summary and later retrieval through shared domain owners. |
| Cause & Effect / Estimation where applicable | Within original M1 inventory scope | Inventory and preserve supported behavior; defer new features explicitly rather than imply completion. |
| O&M / general Reports / Team / Settings | Some navigation entries marked soon | Outside the named milestone scope unless separately added; their placeholders do not count as implemented deliverables. |

Each row needs a consumer acceptance record: input owner, source/artifact IDs, API contract, freshness, override behavior, legacy/new comparison, no-read-work check and rollback switch.

## 10. Shared memory architecture and acceptance scenarios

The memory capabilities in the unified sequence build on the accepted core. Its source plan's four layers remain structured, semantic, episodic and summary memory. Build a dedicated FastAPI service with the original eleven endpoint patterns, a React memory tab, worker jobs and reusable workflow adapters.

The relational additions include project_memories, typed project_facts, decisions/corrections (or normalized subtype equivalents), project_events, project_summaries, memory_evidence and protected memory_audit_log. Extend existing document/domain identities with immutable versions and chunks; do not create competing document registries. Supporting access, conflicts, promotion, processing/outbox and retrieval traces need explicit contracts.

The detailed delivery stages are M14–M25, with policy established at M3 and shared infrastructure at M7. Durable events (M18) precede summaries (M20); conflicts and authority (M19) precede automated capture (M23). Project RAG (M21) follows stabilization (M11) and supplies the shared context builder (M22). Cross-workflow integration (M24) precedes final acceptance (M25).

**Required memory acceptance examples:**
- Project A Edwards / Project B Siemens: B returns only its applicable Siemens state and permitted sources.
- Eaton R0 / Edwards R1: default valid-current query and explicit R0 query return the correct evidence-backed values.
- Correction 125 → 105: every applicable consumer gets 105, with the old value and reasoning retained.
- Unsupported AI approval: stays unconfirmed; no model confidence or pin can grant authority.
- Source withdrawal/revision: affected facts, summaries, contexts and generated outputs become stale and require appropriate review.
- Token pressure: preserve required evidence or report insufficient context; never silently drop the critical constraint.

## 11. Verification performed for this consolidation

**Focused isolated regression run: 89 passed, 0 failed, 0 errors; 45 deprecation warnings; 217.47 seconds.** The captured source was copied without the live .env, database, uploads or archive. The existing test fixtures created temporary databases/libraries/uploads and used scripted providers where AI behavior was exercised.

Suites: test_document_classification_v2.py, test_document_processing_v2.py, test_file_sync_v2_processing.py, test_project_state.py, test_redesign.py, test_drawing_prep.py, test_fa_efficiency.py.

Evidence: [test summary and command](roadmap-evidence/2026-10-06/TEST-RESULTS.md), [JUnit results](roadmap-evidence/2026-10-06/focused-tests-r2.xml), [test log](roadmap-evidence/2026-10-06/focused-tests-r2.log).

The first attempt had 40 passes and 49 setup errors, all caused by access denial to the default pytest temporary directory. It was rerun with an explicit isolated --basetemp; no application/test code was changed to obtain the passing run. This environment failure is recorded in the test summary.

These checks concern the captured code and named scenarios only. They do not validate engineering accuracy on unseen project drawings, real-model extraction, real AutoCAD output, PostgreSQL operation, production data completeness or formal milestone acceptance.

The [candidate integration comparison](roadmap-evidence/2026-10-06/candidate-integration-check.json) confirms the active redesign service differs from the M5 correction's declared file hash and that its dedicated Apply test file is absent. Semantic inspection also confirms the old proposed-change/archive-publication behavior remains; hash difference alone was not treated as proof of absence.

The [post-review drift check](roadmap-evidence/2026-10-06/source-drift-check.json) found one externally changed file: backend/tests/test_scoped_drawing_review.py, which is not in the focused test selection. Application files and the selected test sources still matched the captured hashes at that check; HEAD remained 831c198. The reported tests apply to the captured snapshot.

## 12. Historical milestone cross-reference

This appendix is for locating earlier PDFs, files and acceptance records. These historical identifiers are not additional milestones or separate roadmaps. Their status belongs to the exact snapshot named by their evidence; use M1–M25 for all new execution tracking.

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

## 13. Delivery and acceptance records

For every milestone, maintain one compact record containing:
- Requirement → current implementation → remaining gap → action → acceptance evidence.
- Exact code/artifact/data snapshot, model/profile/schema/policy versions where applicable.
- Named tests and actual results; functional, mocked, real-model and real-AutoCAD results separated.
- Independent review disposition and any engineer/owner-only decision still required.
- Integration status in the active tree, source/evidence retention, rollback and known limitations.

Use the complete [historical M2 acceptance matrix](<G:/dev (2)/dev/ep-platform-merged/m2-closure/M2-ACCEPTANCE-MATRIX.md>) for M4 rather than replacing it with a shorter checklist. This unified roadmap does not silently descope its dates/sections, BOQ, sealed-pilot, label or accepted-tree requirements.

## 14. Immediate next work

1. Refresh M1 ownership and M2 drawing baseline for the current code, then close the M3 access, retention, authority and reuse contracts.
2. Close M4 extraction reliability using the complete existing acceptance matrix and exact frozen validation rules.
3. Complete M5 safe Apply correction review and integration, preserving current drawing preparation behavior.
4. Deliver M6–M11: classification, shared processing, deterministic geometry, backfill, tab migration and stabilization. Verify that Drawings and Interfaces reuse the same compatible stored artifacts.
5. Complete M12 visual review and M13 real-project drawing validation.
6. Complete M14–M25: governed memory storage, facts, evidence, UI, durable history, conflict control, summaries, RAG, shared context, automatic capture, workflow integration and final acceptance.

The next implementation task should name one unified milestone, its bounded scope, the snapshot it changes, its exact completion gate and evidence destination. Keep useful existing work and historical acceptance evidence.
