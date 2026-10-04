# Task One — Compliance Statement Improvement Requirements

## Purpose

Improve Compliance Statement so every answer is complete, traceable, evidence-grounded, and safe for engineer review. Reduce unsupported positive claims while preserving the current approval and export controls.

## Verified current behavior

The current implementation is the regression baseline:

1. Consultant specifications are handled clause by clause.
2. Existing rules handle informative clauses.
3. Deterministic autofill uses the knowledge base without an AI call.
4. AI autofill receives available project facts, scope, BOQ data, nearest historical answers, and engineer-approved learned answers.
5. AI output is a draft requiring engineer review.
6. Engineer approval is required before Excel or PDF export.
7. Approved row answers and approved statements can become learned drafting examples.
8. Datasheets and certificates are not automatically retrieved and supplied to AI today.

Historical answers improve wording; they are not proof that a new project complies.

## Target assessment model

Each consultant requirement must resolve to one structured state:

- `COMPLIES_EVIDENCED`
- `DOES_NOT_COMPLY`
- `PARTIALLY_COMPLIES`
- `INSUFFICIENT_EVIDENCE`
- `CONFLICTING_EVIDENCE`
- `ALTERNATIVE_FOR_APPROVAL`
- `NOT_APPLICABLE`
- `INFORMATIVE`
- `PENDING_ENGINEER_REVIEW`

A positive compliance statement is permitted only when current, eligible evidence supports the exact requirement, project, product, manufacturer, and model. Missing or conflicting mandatory proof must fail closed.

## Functional requirements

### Atomic requirements

Split compound clauses into independently assessable requirements while preserving the original clause and its AND, OR, condition, exception, and alternative relationships. Store source hash, page, region, clause reference, exact text, requirement type, expected value/model/unit/standard/approval, extraction version, confidence, and review provenance.

### Extraction completeness

Inventory every source page before extraction. Maintain a page ledger marking every page visited, skipped, unsupported, failed, or unattempted with a reason. Keep all in-scope pages in coverage denominators. Missing or unread pages must block a claim of complete assessment. Every extracted requirement must link to its page and region.

### Product and evidence identity

Store exact manufacturer and model identity and distinguish proposed, submitted, approved, rejected, superseded, and installed products. Each evidence item must retain source file/hash, project and product association, page/region, original and normalized values/units, extraction method/version, freshness, confidence, and reviewer decisions.

Evidence from another project, model, revision, or superseded source must never be silently reused.

### Datasheets and certificates

Support controlled ingestion of datasheets, certificates, listings, approvals, and test reports. Automatic retrieval, if introduced, must use approved sources, preserve the artifact and hash, record URL/time, verify exact manufacturer/model and validity, and require engineer review before the source becomes trusted evidence.

If exact-model proof is unavailable, return `INSUFFICIENT_EVIDENCE` or `ALTERNATIVE_FOR_APPROVAL`, never compliance.

## Consultant-first retrieval

For every atomic requirement, retrieve in this order:

1. current consultant specification and exact requirement;
2. current engineer-approved product and model;
3. current exact-model datasheet;
4. current certificate, listing, approval, or test report;
5. current approved submittal and consultant response;
6. current calculations, schedules, drawings, BOQ, scope, and design facts;
7. verified organizational knowledge;
8. historical approved answers as wording guidance only.

Every result must carry provenance, confidence, eligibility, and freshness. Similarity and history alone cannot establish compliance.

## Deterministic verification

Before proposing compliance, deterministic validators must check all applicable facts:

- exact manufacturer/model association;
- numeric values and comparison operators;
- unit compatibility and conversions;
- required standards and editions;
- certificate identifiers, validity, and scope;
- consultant, client, authority, or engineer approval;
- revision currency;
- project/system/clause applicability;
- conflicts between sources;
- completeness of mandatory proof.

AI may find candidates and explain results, but cannot override a failed deterministic check.

## Citations and output

Every substantive sentence must link to eligible evidence. A citation must show source name, revision, page, and clause/region and open the cited page.

The answer must separately show assessment state, concise wording, citations, missing proof, conflicts, deviations/alternatives, confidence, and review status. No eligible citation means the answer cannot be `COMPLIES_EVIDENCED`.

## AI capability and limits

Use an AI agent with structured memory, retrieval, evidence verification, and engineer review. Do not continuously retrain from project activity.

AI may split clauses, locate candidate evidence, extract bounded facts, compare requirements with verified evidence, explain conflicts, draft wording, propose citations, and prioritize review.

AI must not invent a model/value/certificate/approval/citation; treat history as proof; claim compliance with missing evidence; approve itself; overwrite engineer decisions silently; transmit content without project AI permission; or write unreviewed output into approved records.

Record provider, model, prompt version, project policy, evidence IDs, source hashes, timestamp, usage, and result for every attempt. Failed, partial, refused, timed-out, and budget-stopped attempts remain visible and cannot replace prior good evidence.

Fine-tuning is optional later, only after a large curated engineer-reviewed dataset exists and evidence controls already pass.

## Confidence, freshness, and invalidation

Report separate confidence for extraction, association, and assessment. Changes to source bytes, specification revision, product selection, project facts, evidence association, or rules must invalidate affected assessments. Preserve the prior approved version in immutable history and mark it stale until reviewed again.

## Deviations and alternatives

When an offering does not meet a requirement, do not label it compliant. Produce `ALTERNATIVE_FOR_APPROVAL` with the unmet requirement, proposed alternative, quantitative/qualitative differences, evidence, risks and interfaces, explicit consultant approval required, and engineer review status.

## Closed-loop consultant outcomes

Capture approval, approval as noted, rejection, clarification request, and supersession at clause and submission level. Link each outcome to the submitted statement version, evidence bundle, product/model, and consultant response.

Use rejected wording/products/evidence patterns as warning and retrieval memory, never automatic rejection. Approved history guides style but does not prove compliance elsewhere.

## Engineer workflow

1. Register and hash specifications and project documents.
2. Inventory pages and establish denominators.
3. Extract and split clauses into atomic requirements.
4. Engineer reviews uncertain extraction/splitting.
5. Resolve systems, products, manufacturers, and exact models.
6. Retrieve current evidence and exact-model datasheets/certificates.
7. Run deterministic association, numeric, unit, standard, certificate, approval, and freshness checks.
8. AI drafts structured assessments from eligible evidence only.
9. UI displays evidence, missing proof, conflicts, alternatives, and citations.
10. Engineer reviews every non-informative requirement.
11. Engineer approves an immutable statement version.
12. Excel/PDF export only that approved version with citations.
13. Consultant outcomes link back to the submitted version.

## Audit, safety, and governance

- Version sources, requirements, evidence bundles, assessments, reviews, approvals, and exports.
- Record actor, time, rule/model version, and reason for every change.
- Make overrides explicit, reasoned, and attributable.
- Separate drafting, evidence review, engineering approval, export, and repair permissions.
- Apply project AI/provider policy before transmitting content; send only bounded evidence.
- Never expose secrets in prompts, code, logs, fixtures, or reports.
- Use explicit idempotent processing jobs. Read endpoints must not process or mutate.
- Never silently overwrite approved records; create new versions.
- Use reviewed migrations, backups, rollback, and reconciliation for data changes.

## Required data and API capabilities

Provide versioned structures for source documents/page ledger, clauses/atomic requirements, products/models, evidence items/bundles, structured assessments/citations, AI attempts/provenance, engineer reviews/approvals, deviations/alternatives, consultant outcomes/rejection memory, invalidation dependencies, and immutable statement/export versions.

Processing endpoints must be explicit, idempotent, auditable, and separate from read endpoints.

## Evaluation framework

Build a frozen, independently engineer-reviewed set spanning consultants, contractors, layouts, systems, products, scans, tables, compound clauses, units, standards, approvals, missing evidence, conflicts, deviations, and alternatives. AI-drafted labels remain provisional and are not human sign-off.

Measure extraction coverage, page completeness, product/model precision and recall, citation precision, numeric/unit and standard/certificate/approval accuracy, accepted-compliance precision, recovery, unsupported positives, critical false accepts, false absences, association errors, engineer edit rate/time, benefit per AI request, usage, latency, and cost.

False-positive compliance is the primary risk. Unsupported files, timeouts, budget stops, and unattempted pages remain in denominators.

## Acceptance criteria

On a fresh, frozen, independently reviewed cohort:

1. 100% of declared source pages are accounted for.
2. Accepted compliance precision is at least 98%.
3. Recovery is at least 90% for every declared primary field/population.
4. Zero unresolved critical false-positive compliance claims.
5. 100% of positive claims have current eligible citations tied to the correct project and exact model.
6. 100% of missing mandatory proof fails closed.
7. 100% of exports use an engineer-approved immutable version.
8. No AI draft, historical answer, or similar-model datasheet is proof by itself.
9. No read endpoint processes or mutates data.
10. Reconciliation finds no lost, duplicated, or silently overwritten approved record.
11. Every assessment change is explainable from source, rules/model, or reviewer history.
12. Existing deterministic autofill, engineer review, approval, learning, and export gates pass regression tests.

If a field has insufficient independently reviewed examples, report its accuracy as `NOT ESTABLISHED`.

## Phased implementation

### Phase 0 — Baseline and contracts
Freeze behavior, ownership, schemas, and metrics. Define assessment/evidence contracts plus migration, rollback, and reconciliation plans.

### Phase 1 — Requirements and traceability
Implement page ledger, immutable source bindings, atomic requirements, clause relationships, and extraction review.

### Phase 2 — Evidence and product identity
Implement exact product/model records, evidence ingestion/provenance, freshness, and invalidation.

### Phase 3 — Deterministic verification
Implement numeric, unit, model, standard, certificate, approval, revision, scope, and conflict validators with fail-closed states.

### Phase 4 — Retrieval and AI drafting
Implement consultant-first retrieval, bounded AI tasks, structured outputs, citations, provenance, budgets, and failure handling. Keep AI output draft/held.

### Phase 5 — Review, export, and outcome memory
Implement engineer review, deviations/alternatives, immutable approvals, cited exports, consultant outcomes, and rejection memory.

### Phase 6 — Independent evaluation
Freeze a fresh cohort and reviewed labels, compare baseline/candidate under declared conditions, and publish safety, accuracy, recovery, coverage, cost, and limitations.

### Phase 7 — Controlled rollout
Deploy behind feature flags to selected projects, monitor false positives/review load/latency/cost, verify rollback, and expand only after reviewed evidence.

## Required deliverables

- architecture and data-model decision record;
- migration, rollback, and reconciliation plan;
- page ledger and atomic requirements;
- evidence registry and retrieval design;
- deterministic verification library;
- AI contracts and safety policy;
- engineer review and approval workflow;
- citation-rich Excel/PDF exports;
- consultant outcome and rejection-memory design;
- evaluation dataset policy and scorer;
- security, privacy, audit, and retention review;
- operational runbook;
- requirement-to-evidence traceability matrix;
- independent review report per phase.

## Definition of done

The improvement is done only when it is evidence-grounded, safely migrated, independently reviewed, and proven on a fresh cohort against the acceptance criteria.

A passing test suite alone is insufficient. Precision without recovery is insufficient. AI-generated labels without declared independent review are insufficient. Drafting without exact citations is insufficient.

Until all production gates pass, the new behavior remains behind feature flags, outputs remain drafts requiring engineer approval, and the existing approved workflow remains authoritative.
