# Task Two — Explainable Engineering Team Workload and Overload

## 1. Purpose

Provide Engineering Manager Khaled Eissa with an explainable view of the engineering workload assigned to every employee. For each employee, including examples such as Mohamed Ramadan, the feature must show:

- all assigned projects;
- engineering workload points contributed by each project;
- total capacity usage and overload percentage;
- the main drivers of the load in plain language;
- missing or uncertain inputs;
- the exact calculation and configuration version used.

The feature supports staffing and redistribution decisions. It is not an employee performance score and must not hide uncertainty behind an AI-generated number.

## 2. Scope and workload boundary

This feature calculates Engineering/Design workload only.

Testing and Commissioning status and project handover are not workload parameters. A project remains active engineering workload after handover whenever Shop Drawings or Material Submittals are still awaiting final approval.

Project engineering workload becomes zero only when both required deliverable streams are 100% finally approved:

- Shop Drawings;
- Material Submittals.

Uploaded, submitted, under review, revise and resubmit, rejected, incomplete, or otherwise non-final items do not count as approved.

The feature does not initially calculate procurement, site execution, testing and commissioning, commercial, logistics, or general management workload.

## 3. Core calculation

### 3.1 Engineering remaining factor

Use:

```text
EngineeringRemainingFactor =
    SDWeight × (1 - ShopDrawingApprovedPercent)
  + MSWeight × (1 - MaterialSubmittalApprovedPercent)
```

Initial proposed configuration:

```text
SDWeight = 0.60
MSWeight = 0.40
```

Weights must be configurable, versioned, and sum to 1.00 for streams that apply to the project. These initial values are proposals requiring calibration and manager approval; they are not established company policy.

### 3.2 Approval percentages

For each deliverable stream:

```text
ApprovedPercent =
    RequiredDeliverablesInFinalApprovedStatus
    / TotalRequiredDeliverables
```

The calculation must use required deliverables, not merely documents found in the folder. Only the canonical final `Approved` status counts in the numerator. Approved as noted counts only if company policy explicitly maps it to final approval for this calculation; that mapping must be configurable and auditable.

The following do not count as approved:

- uploaded;
- submitted;
- under review;
- pending;
- revise and resubmit;
- rejected or not approved;
- incomplete;
- unknown status;
- missing consultant response.

Duplicate files or revisions must not increase the required-deliverable denominator. The denominator represents distinct required deliverables under the current approved project scope.

### 3.3 Zero-required streams

A deliverable stream with zero genuinely required deliverables is not the same as an unknown stream.

- If a manager-approved scope record explicitly states that a stream is not required, exclude its weight and normalize the remaining applicable stream weights to 1.00.
- If both streams are explicitly not required, EngineeringRemainingFactor is 0.
- If the total required count is zero because the system has not discovered or confirmed the scope, mark the stream `UNKNOWN`; do not treat it as complete.
- If applicability is disputed, hold the calculation as provisional and show the missing decision.

Example: if Material Submittals are confirmed not applicable, Shop Drawings receive an effective weight of 1.00 for that project.

### 3.4 Missing and unknown data

Unknown data must never be interpreted as completed work.

If required counts, final statuses, project value, ownership, or strength inputs are missing:

- show a missing-data flag;
- calculate only when a documented fallback exists;
- label the result provisional;
- show the fallback and its effect;
- prevent an apparently precise status from hiding the uncertainty.

For approval progress, the safe default for an applicable but unknown stream is 0% approved until reviewed. The UI must clearly identify this as an assumption rather than an observed fact.

## 4. Overall project load

Use:

```text
ProjectLoad =
    BasePoints
  × CostFactor
  × StrengthFactor
  × EngineeringRemainingFactor
  × OwnershipFactor
```

Initial proposed `BasePoints = 100`.

All components must be configurable and versioned. A calculation snapshot must retain the exact input values, factor-table version, timestamp, and data sources.

ProjectLoad reaches zero when the two applicable deliverable streams are finally 100% approved. Handover and Testing and Commissioning status do not change this result.

## 5. Employee capacity and overload

Use:

```text
EmployeeLoadPoints = Sum(ProjectLoad for assignments)
EmployeeLoadPercent =
    EmployeeLoadPoints / EmployeeCapacityPoints × 100
OverloadPercent = max(0, EmployeeLoadPercent - 100)
```

Employee capacity points must be configurable by employee and effective period. The system must preserve historical capacity changes, including reduced schedules, leave, temporary assignments, or approved role differences.

Initial status bands are proposals requiring calibration:

| Status | Proposed range |
|---|---:|
| Available | below 70% |
| Healthy | 70% to 100% |
| Overloaded | above 100% to 120% |
| Critical | above 120% |

Thresholds must be configurable, versioned, and calibrated using historical work, manager review, and observed delivery outcomes. They must not be presented as established company policy until approved.

## 6. Cost factor

Contract value must be categorized into company-specific bands or percentiles. Do not multiply workload linearly by raw contract value.

Initial example factors:

| Cost band | Proposed factor |
|---|---:|
| Small | 0.70 |
| Medium | 1.00 |
| Large | 1.25 |
| Mega | 1.50 |

The organization must define band boundaries by currency-normalized contract value or by approved percentiles from relevant historical projects.

Store:

- original contract value;
- original currency;
- normalized value and conversion source/date if conversion is used;
- value source document or field;
- band and factor;
- configuration version;
- manager override, reason, actor, and time.

Missing values must be flagged. A configured neutral fallback may be used provisionally but must remain visible.

Cost represents scale only. Project Strength must not reuse raw cost or cost band as a strength input, because that would double-count cost.

## 7. Project Strength Score

Project Strength is a separate 1-to-5 classification of engineering complexity:

| Level | Name | Proposed factor |
|---|---|---:|
| 1 | Small / Simple | 0.70 |
| 2 | Standard Small | 0.85 |
| 3 | Standard | 1.00 |
| 4 | Premium / Complex | 1.25 |
| 5 | Landmark / Ultra Luxury | 1.50 |

The system may propose a level, factor, confidence, and reasons from documented project facts:

- building and luxury type;
- number and complexity of systems;
- expected Shop Drawing volume;
- expected Material Submittal volume;
- custom designs or products;
- approval and technical requirements;
- coordination complexity.

Each reason must cite its source. Cost must not be an input to StrengthScore.

Khaled Eissa can accept or override the proposed score. Every override must record previous value, new value, reason, actor, timestamp, evidence, and effective version.

Manager overrides become labeled examples for future classification improvement. They do not authorize continuous model retraining. Any later model improvement requires a separately curated and evaluated dataset.

If evidence is insufficient, propose no score or use a visibly provisional configured default. AI confidence cannot replace missing evidence.

## 8. Ownership factor and split responsibility

Assignments must distinguish responsibility roles:

| Role | Suggested factor |
|---|---:|
| Primary owner | 1.00 |
| Shared owner | 0.50 to 0.75 |
| Support | 0.20 to 0.40 |

These are proposal ranges requiring calibration.

For a project with multiple employees, assignment shares must represent the intended distribution of the same project load. The sum of active OwnershipFactors for employees assigned to the same responsibility pool must equal 1.00 unless the manager explicitly records that additional support effort is additive.

Default behavior:

- one primary owner: 1.00;
- two equal shared owners: 0.50 each;
- primary plus support: manager assigns shares that total 1.00, such as 0.70 and 0.30;
- three shared owners: shares total 1.00.

The system must warn and block finalization when ordinary split shares total above or below 1.00. An additive support exception must be explicit, justified, and reported separately so total organizational workload is not silently inflated.

Ownership changes require effective dates. Historical snapshots must retain the assignment split that applied at calculation time.

## 9. Explainability

The deterministic formula is authoritative. AI may propose StrengthScore and generate explanations from documented facts, but it cannot replace the formula.

Every employee summary must explain the largest load drivers in plain language. Example:

> Mohamed Ramadan is at 118% of capacity. Project A contributes 52 points because it is a Level 4 complex project, only 35% of Shop Drawings and 20% of Material Submittals are finally approved, and Mohamed owns 70% of the engineering responsibility. Project B contributes 41 points and has unknown Material Submittal scope, so the total is provisional.

The explanation must be generated from the stored calculation inputs and must agree exactly with them. It cannot introduce unrecorded causes.

## 10. User interface

### 10.1 Manager dashboard

Provide:

- employee name and role;
- capacity points;
- total load points;
- load percentage and overload percentage;
- status band;
- number of active engineering projects;
- missing-data and provisional-result indicators;
- ranked project contributions;
- last calculation time and configuration version.

Support filtering by employee, department, project, status band, system, and time period.

### 10.2 Employee drill-down

For every project contribution show:

- project and assignment role;
- ProjectLoad points;
- Shop Drawing required, finally approved, and percentage;
- Material Submittal required, finally approved, and percentage;
- effective SD/MS weights;
- EngineeringRemainingFactor;
- contract value source, cost band, and CostFactor;
- StrengthScore, StrengthFactor, confidence, reasons, and sources;
- OwnershipFactor and split validation;
- BasePoints;
- missing-data assumptions;
- the complete calculation;
- override and audit history.

### 10.3 Redistribution scenarios

Allow Khaled Eissa to create non-destructive scenarios by moving or splitting assignments and changing proposed ownership shares. Show before/after load for affected employees and validate share totals.

A scenario must never change real assignments until explicitly applied through an authorized action. Saved scenarios need owner, timestamp, assumptions, and version.

## 11. Data model

Provide versioned entities or equivalent structures for:

- employee capacity and effective dates;
- project engineering assignment and ownership share;
- project contract value, currency, normalization, and source;
- cost-band configuration;
- strength proposal, evidence, review, and override;
- required Shop Drawing and Material Submittal scope;
- canonical deliverable identity and final approval state;
- workload configuration and status thresholds;
- calculation snapshot and per-project contribution;
- missing-data flags and fallback assumptions;
- redistribution scenario;
- audit events.

Snapshots must be immutable and reproducible from recorded inputs.

## 12. API requirements

Read endpoints must be side-effect free.

Required capabilities include:

- list current employee workload summaries;
- retrieve employee/project calculation breakdown;
- retrieve input provenance and audit history;
- calculate or refresh workload through an explicit idempotent command/job;
- review or override StrengthScore;
- update capacity with effective date;
- update assignment ownership shares with validation;
- create, update, compare, and apply redistribution scenarios;
- manage versioned factor and threshold configurations;
- export a dated workload snapshot.

Every write requires authorization, validation, actor identity, reason where applicable, and audit logging.

## 13. Edge cases

The design must explicitly handle:

- a project with no confirmed required-deliverable scope;
- one confirmed non-applicable stream;
- both streams confirmed non-applicable;
- duplicate documents or revisions;
- approved documents superseded by a later revision;
- Approved as Noted policy differences;
- missing or conflicting consultant responses;
- multiple currencies and missing exchange rates;
- zero or missing employee capacity;
- employees on leave or part-time;
- ownership shares that do not total 1.00;
- assignment changes during a reporting period;
- missing contract value;
- missing or low-confidence StrengthScore evidence;
- archived or cancelled projects;
- reopened deliverables after prior final approval;
- project handed over while approvals remain open;
- rounding: retain full precision internally and round only for display.

Unknown must never mean complete, approved, zero workload, or zero risk.

## 14. Worked examples

### Example A — Primary owner

Inputs:

- BasePoints = 100
- CostFactor = 1.25
- StrengthFactor = 1.25
- SDWeight = 0.60
- MSWeight = 0.40
- Shop Drawing ApprovedPercent = 50%
- Material Submittal ApprovedPercent = 25%
- OwnershipFactor = 1.00
- EmployeeCapacityPoints = 100

```text
EngineeringRemainingFactor
= 0.60 × (1 - 0.50) + 0.40 × (1 - 0.25)
= 0.30 + 0.30
= 0.60

ProjectLoad
= 100 × 1.25 × 1.25 × 0.60 × 1.00
= 93.75 points
```

This project alone uses 93.75% of a 100-point employee capacity.

### Example B — Shared ownership

Using the same project with two equal shared owners:

```text
Each OwnershipFactor = 0.50
Each ProjectLoad = 46.875 points
Total allocated project load = 93.75 points
```

The project is not double-counted.

### Example C — One stream not applicable

Material Submittals are explicitly confirmed not required. Shop Drawings are 70% finally approved.

The Shop Drawing weight normalizes to 1.00:

```text
EngineeringRemainingFactor = 1.00 × (1 - 0.70) = 0.30
```

### Example D — Unknown scope

No required Material Submittal count exists and no approved record says the stream is not applicable. The system must not treat it as 100% approved. It uses the configured safe fallback, flags the result provisional, and explains the missing scope decision.

### Example E — Completion

Both applicable streams are 100% finally approved:

```text
EngineeringRemainingFactor = 0
ProjectLoad = 0
```

This remains true regardless of Testing and Commissioning or handover status.

## 15. Governance and calibration

Initial BasePoints, weights, factors, ranges, capacity values, and status thresholds are proposals. They require calibration from historical project data and manager review before becoming company policy.

Calibration must:

- use completed historical periods with preserved inputs;
- compare predicted workload with actual engineering effort and delivery outcomes;
- avoid optimizing only for one employee, project type, or contractor;
- publish sample sizes and uncertainty;
- preserve the prior configuration;
- require manager approval for a new effective version.

No opaque AI-only workload score is allowed.

## 16. Acceptance criteria

1. Every assigned engineering project appears under the correct employee.
2. Handover and Testing and Commissioning do not reduce EngineeringRemainingFactor.
3. ProjectLoad becomes zero only when both applicable deliverable streams are finally 100% approved or explicitly not required.
4. Non-final statuses never count as approved.
5. Unknown scope never counts as complete.
6. The displayed calculation reproduces stored ProjectLoad exactly.
7. Split ownership does not double-count total project load.
8. Cost is banded rather than used linearly and is not duplicated in StrengthScore.
9. StrengthScore proposals show documented reasons and sources.
10. Khaled Eissa can override StrengthScore with a reason and full audit history.
11. All factors, capacities, bands, and thresholds are configurable and versioned.
12. Every workload snapshot is reproducible from stored inputs.
13. Read endpoints cause no processing or writes.
14. Redistribution scenarios do not change assignments until explicitly applied.
15. Missing-data flags and provisional assumptions are visible in summaries and drill-down.
16. Status bands and overload percentages are calculated consistently.
17. Regression tests cover zero-required streams, unknown data, duplicate deliverables, revisions, multi-currency values, ownership splits, reopened approvals, and configuration changes.
18. Manager review confirms that explanations identify the true stored load drivers and contain no invented facts.

## 17. Phased implementation plan

### Phase 0 — Ownership and baseline

Confirm authoritative sources for employees, project assignments, contract values, deliverable scope, approval statuses, and capacity. Measure data completeness and document current definitions.

### Phase 1 — Canonical progress

Create distinct required-deliverable registers for Shop Drawings and Material Submittals. Normalize final approval statuses, duplicates, revisions, applicability, and unknown states.

### Phase 2 — Deterministic engine

Implement versioned configuration, EngineeringRemainingFactor, CostFactor, StrengthFactor, OwnershipFactor, ProjectLoad, employee totals, status bands, snapshots, and audit records.

### Phase 3 — Strength proposal and review

Implement evidence-based StrengthScore proposals, explanations, confidence, manager review/override, and labeled override history. Keep the deterministic formula authoritative.

### Phase 4 — Dashboard and drill-down

Implement employee summaries, project contribution breakdown, missing-data indicators, provenance, calculation details, and filters.

### Phase 5 — Redistribution scenarios

Implement non-destructive reassignment and ownership-split scenarios with before/after comparisons and application controls.

### Phase 6 — Historical calibration

Evaluate proposed factors and thresholds on historical data, review with Khaled Eissa, freeze an approved configuration version, and document limitations.

### Phase 7 — Controlled rollout

Release behind a feature flag, compare results with manager assessments, monitor data quality and overrides, and expand only after acceptance criteria pass.

## 18. Definition of done

The feature is complete when managers can see every employee's engineering workload, reproduce every point from versioned inputs, understand the main load drivers, identify uncertainty, and safely model redistribution.

A visually complete dashboard is insufficient without canonical deliverable scope, final-approval semantics, auditable calculations, calibrated configuration, and manager review.
