# Project Memory Implementation Roadmap

> **Consolidated roadmap:** use [UNIFIED_MASTER_ROADMAP.md](../../UNIFIED_MASTER_ROADMAP.md), numbered **M1–M29**, for all current execution tracking, dependencies and the shared drawing-processing/reuse contract. This earlier memory-only plan retains historical IDs for traceability; use the unified roadmap's cross-reference appendix. In the unified sequence, stabilization/PostgreSQL readiness is M11 and project RAG is M21.

Date: 6 October 2026
Project: Engineering Project Platform
Status: Proposed implementation roadmap; milestone completion is not established by this document.

This roadmap implements the October 2026 Project Memory Master Plan against the current application. PM-M0 is an added prerequisite; PM-M1 through PM-M12 map to the PDF's M1–M12. Existing repository M1/M2 reports describe other work and do not establish completion here.

The accompanying [gap assessment](../../PROJECT_MEMORY_GAP_ASSESSMENT.md) contains current-code evidence, reusable components, behavioral gaps and additions required in the master plan. The source PDF remains at C:\Users\moham\Downloads\Engineering_AI_Project_Memory_Master_Plan.pdf.

## Delivery order

1. PM-M0: settle ownership, access and retention contracts.
2. Foundation: PM-M1 → PM-M2 → PM-M3 → PM-M4.
3. Intelligence: build PM-M8 durable events early; deliver PM-M6, PM-M5 and then PM-M7.
4. Controlled automation: implement PM-M10 core before PM-M9, then complete historical/conflict handling.
5. Scale: PM-M11 integration and PM-M12 acceptance.

Start quality instrumentation and isolation checks during the foundation. Do not postpone them until PM-M12. Reuse existing domain records as authoritative owners and add the shared layer inside the FastAPI backend, existing workers and React workspace.

## Tracking

| Milestone | Deliverable | Status | Owner | Acceptance evidence |
|---|---|---|---|---|
| PM-M0 | Baseline, ownership and policy | Planned | To assign | Pending |
| PM-M1 | Project Memory Database | Planned | To assign | Pending |
| PM-M2 | Structured Project Facts | Planned | To assign | Pending |
| PM-M3 | Manual Memory UI | Planned | To assign | Pending |
| PM-M4 | Evidence and Sources | Planned | To assign | Pending |
| PM-M5 | Project Summary | Planned | To assign | Pending |
| PM-M6 | Project RAG Integration | Planned | To assign | Pending |
| PM-M7 | Retrieval Engine and Context Builder | Planned | To assign | Pending |
| PM-M8 | Episodic Memory and Timeline | Planned | To assign | Pending |
| PM-M9 | Automatic Memory Extraction | Planned | To assign | Pending |
| PM-M10 | Conflict, Revision and Correction Resolution | Planned | To assign | Pending |
| PM-M11 | Integration Across Agents and Engineering Workflows | Planned | To assign | Pending |
| PM-M12 | Analytics, Quality and Deployment Acceptance | Planned | To assign | Pending |

## PM-M0 — Baseline, ownership and policy

Dependencies: None.

Implementation:

- [ ] Record the current code/database baseline and map canonical owners for each fact.
- [ ] Define project membership/access checks and the critical-memory confirmer capability.
- [ ] Define archive/retention, scoped revision semantics, authority rules and global-promotion policy.
- [ ] Separate project learned answers and context caches from reusable global knowledge.

Acceptance:

- [ ] An approved ownership/access/revision contract exists.
- [ ] Cross-project reuse requires explicit promotion; normal project removal preserves engineering history.

## PM-M1 — Project Memory Database

Dependencies: PM-M0.

Implementation:

- [ ] Add SQLAlchemy models and Alembic migrations for memories, typed facts/details, evidence, audit and conflicts.
- [ ] Enforce non-null project scope, same-project evidence links and current-value constraints.
- [ ] Implement repository/service operations with atomic lifecycle updates and immutable audit.
- [ ] Rehearse memory-schema migrations on a copied dataset; use the PostgreSQL deployment path qualified at Platform M7.

Acceptance:

- [ ] Scoped CRUD works and rejects cross-project record/evidence access.
- [ ] Creation and mutation produce durable audit records in the same transaction.

## PM-M2 — Structured Project Facts

Dependencies: PM-M1.

Implementation:

- [ ] Adapt existing Project, ProjectSystem, ProjectDesign, BOQ and approval registers without creating competing editable copies.
- [ ] Add typed authority, design constraints, loop rules, equipment/floor scope and engineering units.
- [ ] Expose fact provenance, effective revision and unresolved-conflict state through a deterministic API.

Acceptance:

- [ ] Consultant/brand/constraint questions can be answered without an LLM.
- [ ] Each fact identifies its canonical owner, scope and source.

## PM-M3 — Manual Memory UI

Dependencies: PM-M1, PM-M2.

Implementation:

- [ ] Add the Project Memory tab and routes to the React workspace.
- [ ] Provide facts, decisions, approvals, corrections, design changes, issues, lessons and candidate views.
- [ ] Implement add/edit/confirm/reject/pin, search, filters and pagination with role/project checks.

Acceptance:

- [ ] Engineers can complete the permitted manual memory lifecycle.
- [ ] Viewers cannot mutate records; unauthorized projects cannot be accessed.

## PM-M4 — Evidence and Sources

Dependencies: PM-M1–PM-M3.

Implementation:

- [ ] Link claims to immutable document versions/hashes, pages/regions/clauses, records or explicit authorized user actions.
- [ ] Support multiple evidence items and distinguish evidence verification from AI confidence.
- [ ] Add a source viewer and critical confirmation policy; preserve historical source bytes.

Acceptance:

- [ ] Every confirmed critical claim has permitted source evidence or explicit authorized confirmation.
- [ ] Source links open the correct version and location with access checks.

## PM-M5 — Project Summary

Dependencies: PM-M4; production refresh depends on PM-M8.

Implementation:

- [ ] Store versioned summaries by domain, approvals, issues and significant changes.
- [ ] Record source memory IDs, event watermark, generator version and stale state.
- [ ] Invalidate on facts, corrections, approvals, revisions and issue changes; refresh through jobs.

Acceptance:

- [ ] Compact current summaries are available and source-traceable.
- [ ] Stale summaries cannot override canonical facts or confirmed corrections.

## PM-M6 — Project RAG Integration

Dependencies: PM-M4 and accepted Platform M7.

Implementation:

- [ ] Reuse document processing and add versioned chunks with canonical text and complete source metadata.
- [ ] Add embeddings and an index with project/system/revision/status filters before ranking.
- [ ] Preserve exact and lexical lookup; keep global knowledge in a separate governed namespace.
- [ ] Make indexing idempotent and recoverable, and retain source text independently of embeddings.

Acceptance:

- [ ] Project B never retrieves Project A-only chunks or source links.
- [ ] Current and explicitly historical document queries retrieve the intended version.

## PM-M7 — Retrieval Engine and Context Builder

Dependencies: PM-M2, PM-M4–PM-M6, PM-M8.

Implementation:

- [ ] Implement one task-aware ProjectContextBuilder combining facts, corrections, events, summaries and project/global retrieval.
- [ ] Apply authorization, eligibility and revision filters before relevance/authority ranking.
- [ ] Enforce token budgets and return source IDs, context version, conflicts and uncertainty.
- [ ] Include project/access/revision/memory-policy versions in context cache keys.

Acceptance:

- [ ] Simple fact questions take the deterministic route.
- [ ] Contexts remain within budget and preserve required evidence or report insufficiency.
- [ ] Permission or fact changes invalidate stale contexts.

## PM-M8 — Episodic Memory and Timeline

Dependencies: PM-M1, PM-M4.

Implementation:

- [ ] Write durable engineering events with actor, effective/recording time, before/after, rationale and evidence.
- [ ] Emit events transactionally from approval, revision, design, correction and issue mutations.
- [ ] Use idempotency keys and an outbox or equivalent reliable delivery mechanism.
- [ ] Add a timeline and historical queries; retain the existing short-lived UI notification stream separately.

Acceptance:

- [ ] What changed, when and why is queryable across modules.
- [ ] Retries emit one event; UI notification pruning does not remove engineering history.

## PM-M9 — Automatic Memory Extraction

Dependencies: PM-M3, PM-M4, PM-M7, PM-M8, PM-M10 core.

Implementation:

- [ ] Detect useful candidates from authorized conversations and domain events.
- [ ] Validate structured extraction, deduplicate within project/system/type and preserve evidence inputs.
- [ ] Ignore acknowledgements and transient reasoning; apply explicit risk/confirmation policies.
- [ ] Add review queues and feature flags; record model/prompt/schema/policy versions.

Acceptance:

- [ ] Useful events create candidates without conversational noise.
- [ ] Unsupported critical AI claims never auto-confirm.
- [ ] Candidate extraction cannot publish project facts globally.

## PM-M10 — Conflict, Revision and Correction Resolution

Dependencies: PM-M2, PM-M4, PM-M8; core precedes PM-M9.

Implementation:

- [ ] Define scoped conflict keys, validity intervals and current versus historical retrieval.
- [ ] Implement authority-aware correction handling, explicit conflicts and atomic supersession.
- [ ] Separate latest uploaded/issued/approved revision states by document/system/entity lineage.
- [ ] Invalidate dependent facts, summaries, contexts and outputs when sources change or are withdrawn.

Acceptance:

- [ ] Current queries return applicable current state and historical queries retain older truth.
- [ ] Confirmed corrections defeat inference; conflicts with approved requirements require resolution.
- [ ] Concurrent writes cannot produce two authoritative current values.

## PM-M11 — Integration Across Agents and Engineering Workflows

Dependencies: PM-M7, PM-M10.

Implementation:

- [ ] Connect compliance and drawing review first, then BOQ/IFC, material submittals, interfaces, battery/CBS and drawing preparation.
- [ ] Use one versioned memory/context contract rather than independent stores.
- [ ] Pass typed approved constraints into deterministic calculations where applicable.
- [ ] Emit events/candidates from significant workflow outcomes and show evidence/memory indicators.

Acceptance:

- [ ] All applicable consumers receive the same confirmed fact and correction.
- [ ] Each listed workflow has an integration test for context consumption and event publication.

## PM-M12 — Analytics, Quality and Deployment Acceptance

Dependencies: All preceding milestones.

Implementation:

- [ ] Measure wrong-project/revision retrieval, evidence coverage, retrieval precision, false memories, duplicates and corrections.
- [ ] Track token use, summary freshness, issue aging and cross-agent consistency.
- [ ] Run labeled end-to-end evaluations, adversarial scope checks and recovery/restore drills.
- [ ] Enable deployment in stages with feature flags, rollback and PostgreSQL acceptance.

Acceptance:

- [ ] Zero wrong-project cases in release tests; every confirmed critical claim is traceable.
- [ ] All roadmap acceptance scenarios pass and quality thresholds have defined denominators.
- [ ] Migration, backup/restore and interrupted-worker recovery are demonstrated.

## Required acceptance scenarios

| Scenario | Expected behavior |
|---|---|
| Project A Edwards / Project B Siemens | B returns Siemens; no A-only memory, quote, evidence link or context is retrieved. |
| Unauthorized project or evidence ID | Read, search, source viewer, export and mutation paths deny access. |
| Eaton R0 / Edwards R1 | Current valid query returns Edwards; explicit R0 returns Eaton with R0 evidence. |
| Latest upload is not approved | Approval-dependent work uses the applicable approved version or reports conflict. |
| Correct 125 devices to 105 | Applicable consumers use 105; original value, actor, rationale and evidence remain retained. |
| Conflicting authoritative requirements | Explicit conflict and resolution; no silent overwrite. |
| Unsupported AI approval claim | Remains unconfirmed and is excluded from authoritative context. |
| Concurrent confirmation | One applicable current value; stale writes are rejected or resolved atomically. |
| Worker interruption and retry | Recoverable progress with no duplicate event, memory or chunk publication. |
| Source replaced or withdrawn | Historic evidence is preserved; dependencies and current claims are reevaluated. |
| Summary/context after correction | Stale inferred state is invalidated. |
| Token pressure | Required evidence is preserved or the task reports insufficient context. |
| Global promotion | Project sign-off alone does not authorize cross-project retrieval. |
| Archive and restore | Engineering history and evidence survive; indexes can be rebuilt. |
| Cross-agent task | Applicable workflows consume the same versioned state. |

## Milestone completion record

For each milestone, record the implemented files/migrations, acceptance commands and results, evaluated code revision, source/data snapshot, known limitations and reviewer outcome. Historical test reports must be labeled as historical. Mark a milestone complete only when its acceptance gates pass.

Calendar estimates and assigned owners remain open until project access policy, backfill scope, document corpus, storage choice and team capacity are settled.



## Shared drawing results across tabs — consolidated requirement

A completed compatible extraction stage is reused by Drawings, Interfaces, BOQ, calculations and memory. Store source versions, physical equipment/geometry, coverage, producer/profile versions and dependency fingerprints in the central M4 processing registry. M6 verifies ordinary tab reads make zero duplicate extraction/OCR/model calls; M7 handles selective invalidation. Missing interface interpretation may run against saved artifacts without repeating completed base extraction. Explicit Fresh reread remains supported and auditable. See section 5 of the unified roadmap for the full contract.
