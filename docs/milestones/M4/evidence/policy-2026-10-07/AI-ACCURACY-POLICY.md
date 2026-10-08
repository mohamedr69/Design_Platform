# AI Accuracy Policy — Roadmap Revision 01
Owner direction: increase AI involvement to improve measured extraction and classification accuracy.
Owner evaluation permission addendum (2026-09-29): [AI use for the frozen 34-project sample](OWNER-AI-PERMISSION-ROUND2.md). This changes evaluation eligibility only; existing holdout, budget, human-review and production gates remain in place.
Updated: 2026-09-28. Status: approved planning direction, implementation and validation pending.

This policy supplements MASTER-ROADMAP.md and the current milestone instructions. It replaces the blanket restriction "AI only for ambiguity". It does not accept M2, establish a new milestone, change business policy or enable any live model/processing setting. Historical review packages and completed pilot evidence remain immutable.

## 1. Objective
Use AI for primary reading where useful, independent verification of critical facts, detection of missed components and bounded escalation. Promote additional automation only when a frozen comparison demonstrates benefit while preserving correctness, recovery and engineering overrides.

Target zero observed errors among adjudicated automatically accepted critical facts, with at least 90% correct automatic recovery on clear applicable facts in the expanded M2 evaluation. Preserve the existing 98% minimum accepted-precision gate for other evaluated fields. Report all numerators, denominators and gaps by field/project/template/profile. These are sample acceptance objectives, never a guarantee for future documents.

## 2. Critical evidence
Prioritize:
- Document/drawing reference and its own-sheet identity.
- Printed revision and its association with that identity.
- Consultant decision, actor, target revision and target component.
- BOQ literal part number, quantity and same-row association.

Also evaluate raw system, floor, date, originator and package-component evidence. M3 adds type, mixed-component and scope assessment. Fields that control routing or ownership can be critical even when they do not determine an approval directly.

Keep printed observations separate from normalized values, domain status and engineer confirmations. A model must not convert a contractor reply, receipt, folder name or absence of rejection into approval.

## 3. Reading and verification design
A candidate reading can come from native text, local OCR or AI. The next verifier receives the original source region and sufficient page/component context, but does not receive the first reader's proposed value or reasoning in the blind-verification experiment. Identify the region geometrically or by source labels, not by asking the verifier to confirm the predicted answer.

Compare outputs only after independent extraction. Include tests where several readers agree on the wrong table or wrong component. A different model or image crop reduces some shared failure modes but does not prove statistical independence.

Use a deterministic, versioned validation policy to check:
- literal source support and readable coverage;
- same component / identity / revision;
- same-row part and quantity;
- actor and decision evidence;
- conflicts, stale provenance and source changes.

The final gate is not an LLM confidence statement or an uncalibrated weighted score. Keep all candidates, disagreements and review reasons. An unrecognized template is a review/routing signal, not proof that every field is unusable.

## 4. Reader profiles to compare
Use an identical frozen input and truth set on the regression/exploration cohorts.

| Profile | Behavior | Purpose |
|---|---|---|
| A — current baseline | Frozen existing implementation, including AI where it already uses AI | Establish actual current errors and recovery |
| B — targeted AI verification | Verify high-risk, conflicting, incomplete and novel-layout facts, plus a predeclared random audit of apparently confident critical outputs | Detect both obvious uncertainty and confident errors |
| C — broader critical-field verification | Blind second reading of every eligible critical fact in the experiment; bounded stronger-model escalation for disagreements or insufficient evidence | Measure whether more calls provide worthwhile additional accuracy |

Keep a separate deterministic-only diagnostic track where the reader supports it. Do not pretend disabling AI in the model-dependent Design Sheet application path creates an equivalent OCR baseline.

For B, freeze an initial 20% random audit of otherwise eligible high-confidence critical outputs, stratified by project/template/field, before predictions are reviewed. Report audited and unaudited populations separately. This percentage is an experimental starting point, not a permanent production guarantee.

Apply proposed verification to all new positive consultant-approval candidates in the AI verification profiles during shadow evaluation. Approval projection remains governed by the existing domain contract until independently reviewed compatibility gates permit migration.

The saved provider configuration currently uses Claude Code with sonnet for the small tier and opus for the standard tier. These are observed aliases, not mandatory permanent vendors or exact model versions. Record the actual returned model where available; do not assume an alias stayed fixed between runs.

## 5. M2 integration
First establish a reproducible reviewed baseline from Review 05 corrections. Then add verification alongside the existing reader paths without silently replacing them.

Drawings: inspect own identity, title block, printed revision and associated decision evidence. Include reference-drawing tables, revision histories and nearby dates as negative/confusion controls.

Submittals: preserve the primary form read. Verify critical identity/revision/decision facts and distinguish form, attachment, contractor reply and consultant evidence. Page limits remain explicit.

BOQ: compare current selective row verification with broader part/quantity verification and, where useful, the existing optional full second pass. Enabling AI_READ_FULL_SECOND_PASS is an experiment, not an accepted accuracy fix. Keep OCR witnesses and row geometry. Missing/damaged part numbers remain literal or unresolved; a catalogue suggestion must not silently replace printed evidence.

Word/mixed packages: cover supported formats and all expected components rather than scoring only PDF first pages.

The new verification path must be reversible and profile-versioned. Default/promoted extraction profiles and AI verification variants are separate experiment axes. Do not mix their caches, evidence or acceptance results.

## 6. Persistence, failure and cache contracts
Store or link field/page/component evidence with source hash, reader/parser version, prompt/schema version, verification profile, model identity and timestamp. Add provenance alongside compatible existing shapes first.

Version reuse decisions for both high-level stored readings and lower-level request caches. A changed model, prompt, profile or validation policy must not silently certify an older reading as verified under the new contract. Explicitly distinguish cached historical evidence from a fresh execution of the candidate verifier.

Failures, refusals, timeouts, missing pages and budget exhaustion remain explicit. They do not mean absent evidence or successful verification. Preserve last-good readings and per-record retained provenance without overstating freshness.

New candidate facts remain in shadow storage until promotion passes the existing compatibility and review gates. Keep accepted evidence, unresolved candidates and derived business records separate. Engineer-confirmed values and history retain priority.

## 7. Real-model experiment contract
Before executing the experiment, record:
- code/tree, parser, prompt, schema and policy identities;
- source/truth hashes, selected files and project AI policies;
- provider, configured aliases and actual model identity when returned;
- per-run request/token/time budgets and concurrency scope;
- a bounded spend cap when valid pricing/account controls are available;
- stop conditions, partial-result handling and continuation procedure.

Use isolated copies and project-policy-eligible documents. Reuse existing source permissions. Do not change live settings, production routing, application services or OneDrive originals as part of evaluation. This planning update itself performs no model calls.

A zero estimated cost with unconfigured pricing is unknown cost, not free usage. Count application requests separately from internal model turns, provider retries and billing events. If the real-model track cannot run, report the concrete evidence gap and do not substitute mocked or deterministic results as model accuracy.

## 8. Evaluation and selection
Gold labels must be independently checked against originals, not generated or approved solely by another model.

For each profile report:
- critical false accepts and known-negative false positives;
- accepted precision and correct automatic recovery;
- component/row recall and extra/missing records;
- review burden and unresolved conflicts;
- requests, cache reuse, escalations, retries and failure rates;
- elapsed time and latency distributions, plus measured/unknown cost.

Report false accepted values, correctly held values, model-detected extra evidence and human-adjudicated corrections separately. Do not inflate precision by counting UR/no-record outcomes as approvals, or inflate recovery by counting withheld values as accepted.

Select the candidate and acceptance policy using exploration results. A candidate needs demonstrated error reduction or increased correct recovery with no new critical false acceptance, unacceptable review burden or unexplained regression. Additional calls alone are not improvement.

Freeze the selected candidate before sealed evaluation. Predeclare any baseline comparison on that cohort and do not select/tune a winner from its outcomes. Failed holdouts become exposed regression evidence; use new unseen data for a renewed generalization claim.

## 9. Mapping to the remaining roadmap
M1: retain accepted ownership decisions; add AI as a producer of evidence without creating a second owner of business truth.

M2: implement/test reading and verification contracts, provenance, no-loss persistence and real-model accuracy.

M3: use AI to assist ambiguous/mixed/new-layout classification and audit confidently supported classifications and scope assignments. Start in shadow mode. Preserve role/category, separate stage from freshness and require evidence for OUR_SCOPE. Classifier proposals do not decide business approval.

M4: orchestrate approved reader/verifier profiles in background domain workflows. Persist the evidence-to-domain relationship. Preserve deterministic business/calculation rules and engineer overrides.

M5: run previewable, resumable historical reassessment with explicit AI budgets and before/after comparisons. No implicit live backfill from the policy update.

M6: tabs consume stored results and review candidates through APIs. Opening a tab must not trigger new AI/OCR or reconstruct business state in the target architecture.

M7: track model/prompt drift, per-stratum quality and cost/latency; control promotion/rollback by verified versions. Keep an ongoing sampled audit of apparently confident outputs, with the rate selected from evidence.

RAG, fine-tuning and optional agent workflows remain post-M7 directions. No automatic M2.5 milestone is added.

## 10. Required handoff artifacts
An implementation task must return:
1. AS-IS call inventory and bounded changes to it.
2. Frozen A/B/C experiment specification and source/truth manifests.
3. Independent-verifier input examples showing no answer leakage.
4. Traceable candidate/evidence and compatibility/cache tests.
5. Real-model versus deterministic versus mocked-test results, clearly separated.
6. Per-profile metrics, observed improvement/regressions and budget usage.
7. Promotion/rollback proposal with the exact frozen version.
8. An independent-review request, never self-approval.

The 30-project / 1,200-document / 40-sheet expanded pilot remains the next planned validation scale. Preserve the old exposed pilot and separate exploration from sealed validation.
