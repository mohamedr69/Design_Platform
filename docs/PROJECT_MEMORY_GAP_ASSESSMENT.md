# Project Memory Master Plan — current-project gap assessment

Date: 6 October 2026
Project reviewed: G:\dev (2)\dev\ep-platform-merged\ep-platform
Source plan: Engineering_AI_Project_Memory_Master_Plan.pdf, version 1.0, all 19 pages.
Source snapshot: Git HEAD 7ecd2d3, plus the current modified and untracked application files.

## Verdict

The existing project is a substantial foundation for the plan, but it does not yet implement the shared Project Memory System. Add the memory layer inside the existing FastAPI backend and React workspace; preserve the current engineering modules.

Existing strengths include structured project information, BOQ and calculation records, document intake and processing, revision registers, approval workflows, drawing issues, project actions, activity/audit records, AI proposals, usage budgets and workers.

The principal missing capabilities are a general project-memory data model and API, evidence-linked memory lifecycle, durable engineering timeline, controlled summaries, project-filtered document chunk/vector retrieval, a task-aware ProjectContextBuilder, shared correction/conflict rules, memory UI, and cross-agent memory evaluation.

This is a source-code architecture assessment, not a runtime certification. I read the plan and active models, services, routes, UI navigation, dependencies and relevant test definitions. I did not start the application, inspect the live database or secrets, execute tests, call AI providers, or modify the project. Existing test results in milestone documents are historical evidence, not results of this review. No completion percentage is assigned because reusable infrastructure is not the same as passing memory acceptance tests.

## 1. What to reuse

| Existing capability | Evidence | How it supports the plan |
|---|---|---|
| Project identity, consultant, contractor, scope and system brands | [Project model](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/models.py:135>) | Expose deterministic facts through adapters. Preserve ownership in the existing tables. |
| Central project state, submittal status and open actions | [Project state service](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_state.py:1>) | Foundation for current-state facts and issue summaries. Extend rather than duplicate it. |
| Document identity, hash, system, revision, status, extraction and processing state | [ProjectDocument](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/models.py:478>) | Reuse as document registry; add immutable document versions and searchable chunks. |
| BOQ corrections with source page, region, original and final values | [Correction recorder](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/boq_corrections.py:29>) | Convert appropriate corrections into shared, scoped engineering constraints. Current records primarily serve evaluation. |
| Submittal revisions and status history; shop drawing revisions/events | [Submittal revision models](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/models.py:1197>), [Drawing revision model](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/models.py:2250>) | Feed revision and approval events into the memory layer without replacing the registers. |
| Domain evidence bundles and bounded source crops | [AI evidence](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/evidence.py:57>) | Reuse evidence construction patterns; extend to persistent, typed memory-source links. |
| AI policy, budgets and usage metrics | [Project AI policy](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/project_policy.py:21>), [Budget controls](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/budget.py:80>), [Metrics](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/metrics.py:97>) | Retain provider restrictions and cost control; add retrieval/context metrics. |
| Background jobs with lanes, deduplication and recovery | [Job lanes](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/jobs.py:67>) | Add ingestion, embedding, summary and candidate-extraction jobs. |
| Global compliance knowledge with lexical matching | [Knowledge matching](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/knowledge/autofill.py:134>) | Keep deterministic exact/lexical matching. It is not yet the PDF's project semantic-RAG layer. |

The existing docs/milestones/M1 report is **Data Requirements, Ownership & Current-State Map**; M2 is **Extraction Reliability**. These are not the PDF's M1 Project Memory Database and M2 Structured Project Facts. Use names such as PM-M1 through PM-M12 to avoid mixing acceptance records.

## 2. Coverage of all twelve memory milestones

“Partial” below means useful implementation exists, but the milestone's exit criteria have not been demonstrated.

| PDF milestone | Current coverage | Required work and completion gate |
|---|---|---|
| M1 — Project Memory Database | Missing dedicated layer; SQLAlchemy/Alembic/project IDs exist | Add canonical memory records, lifecycle, evidence, audit and repository/service interfaces. Enforce project ownership on reads, writes and references. Gate: scoped CRUD and isolation tests. |
| M2 — Structured Project Facts | Partial | Adapt Project, ProjectSystem, ProjectDesign and domain registers. Add extensible typed facts for authority, constraints, loop rules, project type and scoped revisions. Gate: fact API answers without an LLM, with provenance and conflict state. |
| M3 — Manual Memory UI | Missing dedicated UI | Add Project Memory route/tab, categories, cards, filters, search, add/edit, confirm/reject, pin, sources and candidate queue. Gate: complete manual lifecycle with permission checks. |
| M4 — Evidence & Sources | Partial within individual modules | Add many-to-many memory evidence with document version/hash, page/region/clause or typed record/user action. Gate: every confirmed critical claim has acceptable evidence or authorized explicit confirmation, and source access is checked. |
| M5 — Project Summary | Dashboard state exists; controlled memory summary missing | Store versioned summaries by system, approvals, open issues and changes, with source IDs and last processed event. Gate: significant mutations invalidate/refresh summaries; stale summaries cannot override facts. |
| M6 — Project RAG | Ingestion and lexical knowledge lookup exist; project chunk/vector pipeline not found | Persist versioned chunks and required metadata, embed/index, filter scope and revision before ranking. Gate: project/system/revision/status filtering and historical source retrieval. |
| M7 — Retrieval Engine | Local fact strings and AI budgets exist | Add one task-aware context builder; combine facts, corrections, events, summary, project RAG and authorized global knowledge. Gate: deterministic fact-only route plus bounded, cited task contexts. |
| M8 — Episodic Memory | Partial domain history/activity | Add durable project events and engineering timeline with actor, before/after, rationale and source. Gate: query what changed, when and why across modules. |
| M9 — Automatic Extraction | Extraction proposals exist, general memory capture missing | Capture candidates from authorized conversations and domain events, validate structured output, deduplicate, apply risk policy and review queue. Gate: useful events captured; filler ignored; critical inference never auto-confirmed. |
| M10 — Conflict & Revision Resolution | Partial domain revisions and supersession | Add typed conflict keys, validity intervals, authority rules, correction priority, atomic supersession, historical queries and conflict review. Gate: one applicable current truth or an explicit unresolved conflict. |
| M11 — Agent Integration | Multiple AI workflows exist; common memory contract missing | Integrate compliance, drawing review/preparation, BOQ/IFC, material submittals, interfaces, battery/CBS and other calculation consumers through adapters. Gate: all consumers retrieve consistent project facts and emit candidates/events. |
| M12 — Analytics & Quality | AI usage/proposal metrics exist | Add wrong-project/revision rates, critical evidence coverage, retrieval precision, false-memory adjudication, duplicates, summary freshness, correction rate, issue aging and consistency. Gate: labeled evaluations, operational dashboards and release thresholds. |

No dedicated project-memory model, memory router, memory page, ProjectContextBuilder or document embedding/vector retrieval implementation was found in the active application sources searched. This conclusion is about those inspected sources, not undeployed code in unrelated folders.

## 3. Existing behavior that must change

### A. Project answers currently enter cross-project reuse

[learning.index_for](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/compliance/learning.py:139>) loads active learned answers by system, without a project filter. Its in-process index is keyed by system. [apply_learned](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/compliance/service.py:359>) drafts matching answers into later statements; related hints also go to AI.

There are safeguards: manufacturer applicability, historical attribution, conflict indicators, and a review requirement. This is intentional historical-answer reuse, not proof that approvals are automatically granted. However, a project sign-off currently makes an answer eligible for cross-project use without the separate promotion process required by this plan.

Required: default learned-answer retrieval to the current project. Move reusable company guidance into a separately approved global namespace, with authorized promotion, applicability conditions and removal of project-specific details. Reviewing a project clause must not automatically publish it as company policy.

### B. Project filtering is not project authorization

[Project listing policy](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/routers/projects.py:425>) explicitly says “mine” is not a permission boundary and permits listing/opening other projects, subject to the platform's broader role/division restrictions. [Project lookup](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/routers/projects.py:121>) checks existence rather than membership.

Required: agree an explicit access policy and enforce it centrally for memory, source documents, retrieval, exports and worker actions. Role checks alone do not satisfy the plan's assigned-project access requirement. Reuse existing roles, but add project membership/access checks and a designated critical-memory confirmer. A “Lead Engineer” capability can map to authorized users without renaming all current roles.

### C. Existing change notifications are not permanent history

[Change pruning](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_state.py:58>) deletes old ProjectChange records after 30 days. These are deliberately UI refresh notifications.

Required: retain that short-lived stream if useful, but write a separate durable engineering event/audit stream. Include reason and before/after values; a change-notification row alone cannot explain a design decision.

### D. Deletion conflicts with permanent engineering history

[Project deletion](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/services/project_deletion.py:64>) deletes domain data, compliance audit, learned answers, corrections, document records and other project children. Some activity and usage survive, but they cannot reconstruct the deleted state.

Required: use archive/deactivate for normal engineering-project removal, retain referenced evidence, and define any exceptional purge policy separately. Protect memory/audit history from update/delete by normal application roles; calling a table “immutable” is insufficient.

### E. Content caches need a separate boundary from project memory

[AI cache access](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/ai/cache.py:62>) intentionally permits reuse by document content; [DocumentReading](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/models.py:1482>) also describes reuse across projects containing identical documents.

This can be appropriate for a pure reading of identical bytes. It does not establish a current data leak. Required: prohibit project-specific decisions, corrections, approvals and composed contexts from entering content-only shared caches. Project memory caches must include project/access scope, applicable revision, memory version and policy version, with invalidation on mutations and permission changes.

### F. PostgreSQL needs a tested deployment path

The default configuration is SQLite ([Default database](<G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/core/config.py:63>)). SQLAlchemy provides a starting point, but a production PostgreSQL driver is not listed in the reviewed requirements. The actual running database was not inspected.

Required: add and test the selected driver, migration/backfill process, concurrency behavior, constraints, backup/restore and worker operation on PostgreSQL. Changing DATABASE_URL alone is not evidence of production readiness.

## 4. Proposed implementation architecture

Existing domain tables/registers
→ domain fact adapters + durable transactional events
→ ProjectMemoryService / EvidenceService / RevisionPolicy
→ ProjectContextBuilder
→ all engineering AI workflows and deterministic calculation inputs

Document processing
→ immutable document versions + chunks
→ project-filtered semantic/lexical retrieval
→ same ProjectContextBuilder

Global knowledge remains a separate, permission-controlled source with an explicit promotion workflow.

### Ownership and data additions

Keep ProjectDocument and the domain registers as canonical owners. Add memory as a governed interpretation of those records, not a second editable BOQ or submittal register.

Recommended additions:
- project_memories: the plan's types/lifecycle, system/category, importance, confidence, author, confirmation, current/pinned flags and supersession.
- project_facts: typed extensions or projections of authoritative domain fields; record which source owns each fact and avoid two independently editable copies.
- project_decisions and project_corrections: typed detail records linked to memory, or equivalent normalized subtype tables; preserve owner/rationale/effective time.
- project_events: durable engineering events with idempotency keys and before/after state.
- project_summaries: system/domain summaries, source-memory IDs, source event watermark, generation version and stale state.
- document_versions and document_chunks: immutable bytes/hash reference, revision identity, canonical text and source location; embeddings remain disposable indexes.
- memory_evidence: multiple evidence items per claim, typed source references, quote/region and verification status.
- memory_audit_log: actor, action, old/new values, reason, request ID and timestamp, protected from normal mutation.
- supporting access membership, global-promotion decisions, conflict records, processing/outbox jobs and retrieval traces.

Use composite project ownership checks/constraints so a memory cannot link to another project's evidence. Add conditional uniqueness for the current confirmed value of each scoped fact key. Update fact state, supersession, audit and the event/outbox record in one transaction.

### API and UI

Implement all eleven endpoint patterns in PDF section 17: memory list; facts; summary; events; create; patch; confirm; reject; supersede; retrieve; rebuild-summary.

Add explicit contracts for candidate review, conflicts, source viewing, search/pagination, pinning, issue resolution and global promotion. These can be actions on the existing endpoints where clear; they do not all require new services.

Retrieval should return the plan's seven sections plus context version, selected source IDs, effective revision scope, applied policy, token counts, stale/missing-source flags and unresolved conflicts. Server-derived authorization must govern project_id; callers cannot bypass it by changing a body field.

Add the memory tab to [Project workspace navigation](<G:/dev (2)/dev/ep-platform-merged/ep-platform/frontend/src/pages/ProjectWorkspace.tsx:20>) and show concise memory/source indicators inside existing engineering pages.

## 5. Additions and clarifications needed in the master plan

These make the proposed design implementable and verifiable; they are not claims that the PDF already specifies them fully.

1. **Define fact identity and engineering scope.** Add entity/asset, floor/zone, system, parameter and units. “105 devices per loop” needs a loop/panel/system scope; a raw text sentence is inadequate for calculations.
2. **Distinguish revision states.** Latest uploaded, latest issued and latest approved can differ. Revisions belong to a document/equipment/system lineage, not one global project R-number. State which version each task needs.
3. **Define temporal queries.** Preserve both engineering effective time and recording time so “what was valid in R0?” and “what did we know on that date?” are distinguishable.
4. **Resolve the authority/correction ambiguity.** A confirmed correction should defeat AI inference, but cannot silently override a higher-authority approved requirement. Such changes require an explicit conflict/approval step; pinning and recency must not bypass it.
5. **Make isolation a hard filter.** The PDF's illustrative multiplicative score must not be used as the security boundary. Apply project access, evidence eligibility and revision validity before ranking.
6. **Preserve source bytes and exact locations.** File paths can change and documents can be overwritten. Retain version hashes, source snapshots, page/region/clause and the complete evidence chain for critical claims.
7. **Define staleness propagation.** A changed/withdrawn source must invalidate dependent facts, summaries, contexts and generated outputs. Reuse existing dependency concepts, and require recalculation or reapproval where applicable.
8. **Specify concurrency and worker reliability.** Use idempotent event IDs, an outbox or equivalent transactional delivery, retries, dead-letter handling and atomic current-state updates.
9. **Version every AI-derived result.** Record extractor/model/prompt/schema/trust-policy versions and evidence inputs. Treat retrieved document text as untrusted content, and give candidate extractors no permission to confirm critical memory.
10. **Specify missing-evidence behavior.** Return unknown, stale or conflicting status, and abstain on unsupported claims. If critical evidence cannot fit the token budget, narrow the task or report the limit instead of silently dropping it.
11. **Define deployment and recovery gates.** Add PostgreSQL migration rehearsals, evidence storage backup, vector reindexing, restore drills, rollback, feature flags and measurable latency/token budgets.
12. **Define measured acceptance thresholds.** “Near zero” and “high coverage” need denominators and a labeled test set. Suggested gates: zero wrong-project cases in release tests; 100% of confirmed critical claims traceable to permitted evidence/authorized confirmation; no critical candidate auto-confirmed; explicit review of every detected critical false memory.

PDF section 23 is future scope after M12. Cross-project promotion becomes an immediate boundary requirement because reuse already exists. Full knowledge graphs, fine-tuning and proactive alerts can remain deferred. Basic dependency invalidation is needed now even if advanced change-impact analysis comes later.

## 6. Delivery sequence

1. **PM-0 — baseline and boundary contract.** Snapshot the current working tree, map fact owners, settle project-access and deletion policies, isolate project learning from global knowledge, and define scoped revision/authority semantics.
2. **PM-M1–M4 — safe manual foundation.** Add schema/migrations, adapters, CRUD, evidence, authorization, immutable audit and manual memory UI. Pilot on synthetic projects and a copied dataset. No automatic memory confirmation.
3. **PM-M5–M8 — retrieval and history.** Build durable events first, then source-versioned chunks, summaries and context builder. Extend existing workers. Start with deterministic fact queries and a small labeled retrieval set.
4. **PM-M10 core before PM-M9 automation.** Establish conflict keys, atomic supersession, authority handling and historical retrieval before allowing candidate extraction at scale. Then introduce low-risk extraction behind feature flags.
5. **PM-M11 — integrate incrementally.** Start compliance and drawing review, then BOQ/IFC, material submittals, interfaces, battery/CBS and drawing preparation. Give each consumer the same versioned context contract.
6. **PM-M12 — release gate and operation.** Run cross-agent and adversarial evaluations, exercise recovery, compare pilot outcomes and enable broader deployment only after the agreed thresholds pass.

Do not estimate calendar duration until the access policy, historical backfill volume, document corpus, vector-storage choice and available team capacity are known.

## 7. Acceptance checks for full coverage

| Check | Required outcome |
|---|---|
| Project A Edwards / Project B Siemens | B returns Siemens and no A-only fact, quote, source link or cached context. |
| Unauthorized project/evidence ID | List, retrieve, source viewer, export and write paths all deny access. |
| Eaton R0 / Edwards R1 | Current valid query returns Edwards; explicit R0 returns Eaton with R0 evidence. |
| New upload not yet approved | Approval-dependent work continues using the applicable approved revision or reports conflict. |
| Correction 125 → 105 | Every applicable consumer receives 105, with original value and rationale retained. |
| Conflicting high-authority requirements | No silent latest-wins overwrite; display conflict and require resolution. |
| Critical AI approval claim without evidence | Remains unconfirmed and cannot become authoritative context. |
| BOQ/calculation/approval mutation | Durable event/audit emitted once; dependencies and summary invalidated. |
| Concurrent confirmations | No duplicate current fact; stale write rejected or resolved atomically. |
| Retry after worker interruption | No duplicate memory, event or chunk publication; partial work is recoverable. |
| Source moved, replaced or withdrawn | Exact historical evidence remains traceable; current claims are reevaluated. |
| Summary/context cache after correction | No stale inferred value survives as current truth. |
| Token pressure | Context stays within limits and preserves mandatory evidence or reports insufficiency. |
| Global promotion | Project sign-off alone does not make a project answer globally retrievable. |
| Archive and restore | Engineering history/evidence survive; database and indexes recover consistently. |
| Cross-agent scenario | Compliance, BOQ, drawings, interfaces and calculations consume the same applicable state. |

Full coverage means passing these end-to-end gates as well as delivering PM-M1–PM-M12. Existing screens, historical milestone approvals, and the mere presence of project_id columns are not enough to establish it.

