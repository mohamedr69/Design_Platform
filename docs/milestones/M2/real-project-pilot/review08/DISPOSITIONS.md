# M2 Review 08: dispositions

Candidate: `e02a8c1`, on the isolated scratch repository, child of `1455f8b`. The Review 07 freeze (`c9a1a14`) and the evaluator amendment (`1455f8b`) are kept as history.

Versions in this candidate:

| Component | Version |
|---|---|
| Evidence reader | `evidence-reader-2026-09-29.3` |
| Evidence policy | `evidence-policy-2026-09-29.3` |
| AI ledger | `ai-ledger-2026-09-29.2` |
| Evaluator | `m2-pilot-eval-2026-09-29.7` |
| Parser, profiles, register, request cache, submittal/transmittal code | unchanged |

- Regressions: [`tests/test_m2_review08.py`](evidence/tests/test_m2_review08.py) (27 tests).
- The 1455f8b reader and ledger are pinned byte-for-byte under `tests/fixtures/`, so the "before" behaviour runs in the same module.
- The same module run against the prior commit fails 24 of 27 tests, every one on a behavioural assertion ([REGRESSION.md](REGRESSION.md)).

## R8-01: every required read has its own outcome; a merge replaces only what was read — **Fixed**

**Before.** Suppose discovery succeeded and the blind identity read timed out. The page was still recorded as `evidence`, and the merge replaced the whole page. The validated decision was lost, and a discovery-only candidate stood in for the validated identity. This is the reviewer's probe `blind_timeout_replaces_good_page`.

A budget-stopped attempt that recorded no per-field outcomes also overwrote a validated identity with a candidate. This is the probe `budget_envelope_does_not_guard_page_overwrite`.

**Now.** `_read_page` records, per page, the outcome of discovery and of every required read:

| Field outcome | Meaning |
|---|---|
| `completed` | the field's blind read returned: a value, a negative such as "no decision marked", or an unreadable result |
| `absent_by_discovery` | discovery completed and saw no such field; its region was never read |
| `incomplete:no_region` | discovery named the field but gave no readable region |
| `failed:<kind>` | the read's request failed (timeout, transport, invalid response …) |
| `budget` | the read was refused by a budget or by the ledger |
| `not_attempted` | discovery failed first |

- **Page outcome.** A page is `evidence` only when every required read (own identity, revision, decision) is `completed` or `absent_by_discovery`. Otherwise it is `partial`, `failed` or `budget`.
- **Observations.** Every observation carries the outcome of its read. An observation from an unsuccessful read also carries the reason `read not completed (...): unverified`.

**Merge is field by field** (`merge_evidence`, supersession rule in the source):

- **A completed read replaces the field's evidence.** This includes a completed, source-supported negative, such as a legible, unmarked decision block. The replaced entry moves to the field's `history` with its own provenance: attempt, versions, policy, prompts, models, profile, variant, source hash.
- **A completed read that came back only unreadable supersedes nothing.**
- **These never supersede:** `absent_by_discovery`, `failed:*`, `budget`, `incomplete:*`, and a page that was not visited. Last-good evidence stays with its original provenance, and the failed attempt is appended to `attempts`, with its page and field outcomes and the list of what `changed` (empty when nothing was replaced).
- **A field with no evidence yet** keeps what an unsuccessful read produced (a discovery candidate), with status `incomplete`. It is never counted as verified, and the first completed read replaces it.
- **Legacy attempts** (Review 06/07 shape, no per-field outcomes): a produced field counts as read only if it carries a verified reading. A field made only of unverified candidates is `incomplete:legacy_unverified` and supersedes nothing. This closes the reviewer's second probe.
- **When a negative supersedes:** only when its read completed and the source supports it. "Discovery saw no decision block" is **not** a negative, because the region was never read. It is recorded as `absent_by_discovery` and the old decision stays.

**Tests.** Each runs through the real `evidence_stage` on a persisted `ProjectDocument`. The result cache is cleared before every step, and the row is reloaded from the database after it. The provider is scripted.

| Requirement | Test |
|---|---|
| Discovery succeeds, the identity read times out, the old decision survives | `test_a_blind_identity_timeout_keeps_the_old_decision_and_identity`; the reviewer's exact case on the pinned 1455f8b reader and on the candidate: `test_before_a_blind_identity_timeout_replaced_the_good_page` |
| Identity succeeds; revision times out; decision refused by a real ledger budget (`LedgerProvider`) | `test_identity_completes_while_revision_times_out_and_decision_is_refused_by_budget` |
| Two components, one completes, one fails, no contamination | `test_one_component_completes_and_another_fails_without_contaminating_each_other` |
| A resume completes with correct provenance; the replaced value is in history | `test_a_later_resume_completes_the_missing_work_with_its_own_provenance` |
| Successful absence vs failed discovery vs completed negative | `test_a_completed_negative_supersedes_but_absence_by_discovery_or_a_failure_never_does` |
| A field known only from an unsuccessful read is incomplete, never verified | `test_a_field_known_only_from_an_unsuccessful_read_is_incomplete_never_verified` |
| A budget attempt without field outcomes (the reviewer's probe) | `test_a_budget_attempt_without_field_outcomes_never_overwrites_with_a_candidate` |

## R8-02: evidence is selected for a requested context, never substituted — **Fixed**

**Before.** `current_evidence(ai)` returned the most recently written envelope, whatever was asked for. After a failed switch to `promoted`, a consumer asking about `promoted` got the `default` evidence (the probe `failed_profile_switch`). Evaluator .6 used the same accessor.

**Now.** Stored evidence has schema `ai-evidence-2`: envelopes keyed `profile|variant`, fields with provenance and history, attempts carrying their key, and superseded envelopes. The consumer API is `evidence_for(ai, sha256=, profile=, variant=, policies=None, accept_unknown_profile=False)`. It returns an explicit state:

| State | Meaning |
|---|---|
| `current` | read for exactly this source hash, profile and variant, and for the given policies if any; lists the fields that are only `incomplete` |
| `pending` | reading was attempted for this context and has produced no evidence yet |
| `unavailable` | nothing was read for this context, or nothing under a compatible policy; `history` names the envelopes that exist |
| `stale` | read for this context from other bytes |

- **No substitution.** Another profile's or variant's evidence is never returned. `last_known(ai)` returns the most recently written envelope explicitly as **history**.
- **The old accessor refuses.** `current_evidence(ai)` without a context returns `{"state": "context_required"}`; it no longer guesses.
- **Unknown legacy profiles.** A Review 06 flat envelope has no recorded profile and is keyed `unknown|<variant>`. It is used only when the caller declares `accept_unknown_profile`, for a historical run whose manifest declares its profile.
- **Review 07 envelopes.** They are normalised with their recorded provenance and marked `completeness: not recorded`. Their attempts get their context key where they recorded one.
- **Policy compatibility is explicit.** `policies={…}` keeps only fields read under those policies. Reader and prompt versions stay in each field's provenance.
- **Evaluator .7.** It scores AI evidence only for the run's declared `ai_context` (variant; profile, defaulting to the row's own; policies; and the legacy-profile declaration). Each document records its `ai_evidence_state`. With no context, no AI evidence is scored (`no_context`).

**Re-scoring under .7** ([METRICS.md](METRICS.md)). Every stored run was re-scored with the context its manifest declares, and every one reproduces its evaluator .6 totals exactly. Document-level differences are ordering only: all documents are equal as unordered judgements. The negative controls give no AI contribution:
- the Review 06 EV1 rows without the legacy declaration;
- the same rows scored as EV2;
- the matched EV1 rows scored as EV2;
- the matched EV1 rows scored as `promoted`.

**Tests:**

| Requirement | Test |
|---|---|
| Failed switch, both directions (default → promoted and back); previous envelope kept as history; successful retry with its own provenance | `test_a_failed_profile_switch_is_pending_never_the_other_profile` (2 cases) |
| The prior accessor returned the other profile as current | `test_before_a_failed_switch_returned_the_previous_profile_as_current` |
| Budget-stopped variant switch (ledger cap 0: no call dispatched); changed bytes give `stale` | `test_a_budget_stopped_variant_switch_and_changed_bytes` |
| Unknown legacy profile | `test_unknown_legacy_profiles_are_used_only_when_the_caller_declares_them` |
| Evaluator selection | `test_the_evaluator_scores_ai_evidence_only_for_the_declared_context` |
| Cache reuse per profile, retained provenance, resume (updated to `evidence_for`) | `test_evidence_reader_r7.py::test_the_stage_binds_the_actual_profile_into_the_cache_and_the_envelope`, `::test_resumed_work_keeps_what_was_read_and_reads_the_rest` |

## R8-03: the persisted scope policy is authoritative — **Fixed**

**Before.** Ledger .1 used the limits of whichever handle it was given. In the reviewer's probe, a scope saved with `requests=1` and already holding one settled request was reopened with `requests=2`, and a second reservation was allowed.

That is a defect in how a scope's limits are enforced. **It does not mean the Review 07 matched run overspent**, and nothing here claims it did. What the evidence shows about that run:

- **One scope.** It used one declared scope, `r7-matched`, stored with `requests=120` and the token and time caps of the declaration.
- **Three processes.** It ran as three sequential processes, one per track.
- **One settings file.** Each process was configured from the run's single settings file, `budget_matched.json`, whose limits are those of the declaration.
- **The outcome.** The ledger holds 120 settled requests and 1 refusal.

Ledger .1 did not record each handle's limits. The statement that no handle opened the scope with other limits therefore rests on the runner's configuration, not on the ledger itself.

**Now (ledger .2):**

- **The first handle records the limits.** The first handle to open a scope stores its limits, inside one `BEGIN IMMEDIATE` transaction that covers schema, upgrade and scope creation.
- **Every later handle is compared with them.** This covers another worker, another OS process and a restart. A handle that supplies a limit with a different value, looser **or stricter**, is refused with `LedgerConfigMismatch`, before any reservation.
  - A partial dictionary is accepted when every supplied value equals the stored one; the other limits come from the scope.
  - A handle that supplies none uses the scope's limits.
- **A stricter handle is refused too, by design.** A second, unrecorded policy for one scope is exactly what must not exist. A caller that wants tighter limits must amend the scope, or use a new scope.
- **`reserve` and `settle` read the effective limits from the database** inside their own transaction, never from the handle's memory. The limits are requests, input tokens, output tokens, elapsed time and the per-request caps, all in one policy.
- **Amendment is the only way to change the limits:** `amend_limits(new, authorized_by=…, reason=…)`.
  - Both fields are required.
  - It bumps `limits_version` and writes a `limit_amendments` row with who, why, when, the process, and the old and new limits.
  - A handle opened with the earlier limits is refused afterwards.
  - An amendment does not re-open a tripped breaker.
- **A concurrency defect found by the new test.** Opening a new ledger file from several workers at once could fail with `database is locked`: switching the journal mode takes an exclusive lock that does not wait. The WAL switch is now done once and retried while another handle holds the file, and all setup runs in the immediate transaction. The race test repeated 15 times: 0 failures.

**Tests.** No external provider is involved; subprocesses use the candidate's own module.

| Requirement | Test |
|---|---|
| Saved cap 1, consumed 1, reopened with cap 2: no second reservation, handle refused | `test_the_reviewers_case_a_reopened_scope_cannot_loosen_its_saved_cap` (the same case on the pinned .1 ledger still reserves) |
| A second OS process with different limits, stricter limits, and a partial dictionary (the stored input cap applies) | `test_another_process_with_different_or_partial_limits` |
| Eight simultaneous workers with conflicting settings creating the scope: one policy wins, the four others are refused, none opens on another policy | `test_simultaneous_workers_with_conflicting_settings` |
| Restart with a request in flight; settled after a timeout with unknown usage (charged at its reservation); the stored output cap then refuses | `test_restart_after_reservations_a_timeout_and_settlement` |
| Input, output and time caps in one policy | `test_input_output_and_time_caps_are_one_scope_policy` |
| An auditable, versioned, authorised amendment | `test_an_authorised_amendment_is_explicit_versioned_and_audited` |

## R8-04: a heading answer is a row-type outcome, never validated item data — **Fixed**

**Before.** When the blind reading said "heading", `validate_boq_row` returned `validated`, even for a row whose reader had a part number (the probe), and even when the reading was illegible.

**Now (policy .3).** A heading answer gives one of three outcomes:

| Case | Outcome |
|---|---|
| The reading is illegible | `unverified` |
| The reader has a part or a quantity, the reading has either, or the reading's description carries a `( n )` count | `conflict`, `row_type: disputed`: a held disagreement, with the reasons listed |
| Otherwise | `state: not_an_item`, `row_type: heading_confirmed`, part and quantity `not_applicable` |

- **Nothing is deleted.** The outcome annotates the row; no BOQ line is removed on any read, complete or not. The AI stage writes only its own key. The existing no-loss test (`test_evidence_reader.py::test_stage_is_off_by_default_and_writes_only_its_own_key`) is unchanged and passes.
- **Part and quantity stay separate**:
  - an absent quantity gives `part_verified_quantity_unverified`;
  - an unreadable read gives `unverified`;
  - a description count is a located quantity (`quantity_source: description_count`).

**Tests:**

| Requirement | Test |
|---|---|
| Part-only heading; quantity-only heading; a clean heading; a heading with a `( 2 )` count; an illegible heading | `test_a_heading_answer_is_a_row_type_outcome_never_validated_data` (5 cases) |
| The prior policy validated the part-only heading | `test_before_a_heading_answer_validated_a_part_only_row` |
| Absent quantity, unreadable read, description count | `test_part_and_quantity_stay_separate_for_absent_and_unreadable_quantities` |

## Human-review handoff — **Prepared (not reviewed)**

[`human-review-packet-v2/`](human-review-packet-v2/INSTRUCTIONS-v2.md) is a versioned successor of the Review 07 packet, which is kept unchanged.

- **Same scope.** 339 component items and 194 BOQ rows, with the same seed.
- **Identities one per row.** 359 identity rows, each with its literal, printed label and role (own document, alternate own number, permit, request, reviewed document, transmitted or listed item, referenced document, project or contract). One is marked as the identity to evaluate. "Ambiguous" is reserved for an unresolved fact or association.
- **BOQ row type.** Part and quantity status are kept separate.
- **[FINDINGS-INDEX.md](human-review-packet-v2/FINDINGS-INDEX.md).** The 13 Review 07 source findings, each linked to its items and page images:
  - 8 groups (10 items) need a decision;
  - 5 groups (13 items) need only a label-literal confirmation.

  It also corrects one Review 07 transcription error: finding 10 is in EP-26082, not EP-29076.
- **Nothing is signed.** No reviewer name or signature is filled in. The appointment is still the owner's choice.
