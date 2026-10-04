# M2 Review 09: dispositions

**Candidate:** `689d95e` on the isolated scratch repository.

- **Commits since `e02a8c1`:**
  - `ec4f0fc`, the first freeze. It was superseded before any result was reported: judgements on unscored pages still dropped `target` and `association`, and no score was affected.
  - `689d95e`, which fixes that.
- **Versions:**

| Component | Version |
|---|---|
| Evidence reader and policy | `2026-09-29.4` |
| Evaluator | `.8` |
| Ledger | `.2`, unchanged; documentation wording only |
| Parser, profiles, register, request cache, submittal/transmittal code | unchanged |

- **The contract** is [CONTRACT.md](CONTRACT.md).
- **Regressions:** [`tests/test_m2_review09.py`](evidence/tests/test_m2_review09.py), 34 tests. On `e02a8c1` 22 fail and 12 pass (the controls). 21 of the 22 fail on behaviour; the other checks the corrected ledger wording. See [REGRESSION.md](REGRESSION.md).
- **Persisted tests:** each runs through the real `evidence_stage` on a persisted `ProjectDocument`. The result cache is cleared before each step, the row is reloaded from the database after it, and the provider is scripted.

## R9-01: usable reads, not returned responses — **Fixed**

**Reproduced first.** The reviewer's `probes.py` was run unchanged on `e02a8c1`, and its output reproduces their `probe-results.json` exactly. The same cases also fail in the new persisted tests on `e02a8c1`.

1. Discovery reads X-SD-9 and the blind read returns `legible=false`. On `e02a8c1` the page is `evidence` and the current identity becomes the discovery-only candidate X-SD-9.
2. Discovery sees an unmarked block and the blind read is illegible. On `e02a8c1` ANN becomes `no_decision_marked`.

**Now.**
- **Request and field outcomes are recorded separately.** A returned but illegible answer is request `ok`, field `unusable:illegible`. A legible answer without an identity or revision value is `unusable:empty`.
- **Only a `completed` (usable) read supersedes.** Discovery-only candidates and discovery-only negatives never replace good evidence. The unusable readings are kept with the attempt (`unapplied`), with their read outcome and target.
- **What still supersedes:** a genuinely completed, legible negative (history kept), and a completed conflict, which stays explicit.
- **Probes on the candidate:** X-SD-1 validated, page `partial`, `own:identity: unusable:illegible`. ANN stays validated, with `own:decision: unusable:illegible`.

**Tests:**

| Requirement | Test | On `e02a8c1` |
|---|---|---|
| Identity blind illegibility, then a later successful retry (history kept) | `test_an_illegible_blind_identity_keeps_the_last_good_identity` | fails |
| Revision blind illegibility, and a legible-but-empty answer | `test_an_illegible_blind_revision_keeps_the_last_good_revision` | fails |
| Discovery unmarked, blind illegible | `test_an_unmarked_discovery_and_an_illegible_blind_read_never_erase_a_decision` | fails |
| Discovery marked, blind illegible | `test_a_marked_discovery_and_an_illegible_blind_read_never_replace_a_decision` | fails |
| No prior evidence: incomplete, never verified | `test_a_first_read_with_an_illegible_blind_answer_is_incomplete_never_verified` | fails |
| Both legible and unmarked: supersedes | `test_a_legible_unmarked_block_read_both_ways_supersedes` | control, passes |
| Completed conflicting evidence stays a conflict | `test_completed_conflicting_readings_stay_an_explicit_conflict` | control, passes |
| Timeout and budget (a real `LedgerProvider` refusal) | `test_timeout_and_budget_controls` | control, passes |

## R9-02: a retained fact keeps its association — **Fixed**

**Reproduced.** Validate X-SD-1 with ANN, then complete X-SD-9 without seeing a decision block. On `e02a8c1`, `ai_groups` puts ANN, validated, beside X-SD-9 and drops the target. The evaluator then scores ANN `correct` and the decision `recovered_clean` for X-SD-9.

**Now.**
- **What each fact records.** Decisions record `target` and `target_revision`; new revisions record `target`.
- **Selection labels the association.** `evidence_for` labels each dependent fact `current`, `held:target_changed`, `held:revision_changed`, `by_target` or `not_recorded` (see [CONTRACT.md](CONTRACT.md) §2).
- **The evaluator uses it.** Evaluator .8 judges a held or `by_target` fact only under its own target, in its own group, and never beside another identity. Held facts stay visible: `held_unassociated`, `held_correct` or `held_wrong`. `target` and `association` travel into every judgement.
- **What is preserved:** same-identity retries are `current`, and legacy facts without a target are grouped as before, with nothing invented.
- **Probe on the candidate:** `ai:1:own@X-SD-1` holds ANN (held, target X-SD-1); `ai:1:own` holds X-SD-9.

**Tests.** Each checks the persisted evidence and the evaluator's judgement.

| Requirement | Test | On `e02a8c1` |
|---|---|---|
| Changed identity with a retained decision | `test_a_changed_identity_does_not_inherit_the_retained_decision` | fails: `correct` / `recovered_clean` for X-SD-9 |
| Unchanged identity with a retained decision | `test_a_same_identity_retry_keeps_its_decision_associated` | control, passes |
| No usable current identity | `test_a_decision_with_no_usable_current_identity_associates_only_by_its_target` | fails: recovered for the page's other component |
| Changed revision, target revision known | `test_a_changed_revision_holds_a_decision_made_for_the_earlier_revision` | fails |
| Multiple components on a page (own and referenced) | `test_multiple_components_on_a_page_keep_their_own_associations` | fails |
| Legacy fact with no recorded association | `test_a_legacy_fact_without_a_recorded_target_is_never_given_one` | control, passes |
| Metadata kept on unscored pages | `test_target_and_association_survive_on_unscored_pages_too` | fails: metadata dropped |

**Re-score.** Every stored run was re-scored under evaluator .8, each with its declared context ([RESCORE.md](RESCORE.md)). All 33 scored runs reproduce their .7 results, with no count changed. The .8 output only adds `target` and `association` to AI judgements. In the stored runs every decision is `current` (matched) or `not_recorded` (Review 06), and every revision is `not_recorded`. The stored runs are single-attempt, so none retained a fact across an identity change.

## R9-03: unknown bytes are not exact-file evidence — **Fixed**

**Reproduced.** With the source hash removed from both the envelope and the field provenance, a request for `sha256='same'` got `state=current` on `e02a8c1`.

**Now.**
- **Source identity is decided per field**, from each field's own provenance, with the states `current`, `stale`, `unknown_source` and `source_required`. A current answer also lists what it `withheld`.
- **The legacy-profile declaration** no longer implies anything about bytes.
- **Retained fields are never relabelled** by a later partial attempt.
- **Historical compatibility is its own explicit mode,** `historical_source`, backed by a manifest and never used operationally. Evaluator .8 passes it only from a declared `ai_context.historical_source`.
- **No stored run needs it.** All stored AI envelopes record matching hashes (Review 06: 66 and 53 flat envelopes; matched: 12 and 12).

**Tests:**

| Requirement | Test | On `e02a8c1` |
|---|---|---|
| Unknown envelope and field hashes | `test_unknown_envelope_and_field_hashes_are_not_current` | fails |
| Legacy flat evidence | `test_legacy_flat_evidence_without_a_hash_is_not_current_even_with_the_legacy_profile_declared` | fails |
| Known mismatch and exact match | `test_known_mismatch_is_stale_and_an_exact_match_is_current` | control, passes |
| The requested context has no hash | `test_a_request_without_a_source_hash_gets_no_exact_file_evidence` | fails |
| Mixed retained and new fields; partial reread | `test_mixed_and_partial_rereads_never_relabel_retained_fields` | fails |
| Explicit historical compatibility control | `test_an_explicit_historical_binding_is_a_separate_manifest_backed_mode` | fails |
| Evaluator behaviour | `test_the_evaluator_scores_unknown_bytes_only_under_a_declared_historical_manifest` | fails |

## R9-04: a heading is confirmed only without item evidence — **Fixed**

**Reproduced on `e02a8c1`:**
- the reader's description `( 2 ) Dual Input Module` gives `not_an_item`;
- a reader quantity of numeric `0` gives `not_an_item`;
- a blind quantity of `0` in the item comparison is treated as absent.

**Now.**
- **The normal verifier passes the reader's description.** Item evidence on either side (a part, a present quantity, a `( n )` count) against a heading answer gives a held `conflict`, with the evidence named.
- **Zero is present.** `0` and `"0"` are present; only `None` and blank are absent.
- **The other outcomes:** an illegible answer gives `unverified`, and a true heading with no item evidence gives `not_an_item`.
- **Nothing is lost or inferred.** Literals are kept (`reader`, `blind`), no line is removed, and nothing is inferred.
- **Replay.** The stored Review 06 BOQ readings keep neither the heading flag nor legibility. The only readings that can be replayed are the two whose recorded reason names a heading: the same row in `boq-ev1` and in `boq-ev1b`. Both give `conflict`, `disputed` under both policies, so there is no change ([`evidence/replay/replay-boq-headings.json`](evidence/replay/replay-boq-headings.json)).

**Tests:**

| Requirement | Test | On `e02a8c1` |
|---|---|---|
| Reader-only count, blind-only count, numeric and string zero (reader and blind), blank and null quantity, part-only, true heading, illegible | `test_a_heading_answer_against_item_evidence` (9 cases) | 3 of 9 fail: reader count, numeric zero, blind numeric zero |
| Zero in the item comparison | `test_numeric_zero_is_a_present_quantity_in_the_item_comparison_too` | fails |
| The normal verifier path: description carried, every line reported, literals kept | `test_the_normal_verifier_carries_the_readers_description_and_keeps_every_line` | fails |

## Ledger (R8-03 accepted): wording corrected

The module documentation now says:
- **after an amendment,** a handle that is already open reads the saved, amended policy;
- **a newly opened handle** that supplies the old, conflicting limits is refused.

`test_an_open_handle_reads_the_amended_policy_and_a_new_handle_with_the_old_limits_is_refused` demonstrates both. The behaviour is unchanged (`ai-ledger-2026-09-29.2`); on `e02a8c1` the test fails only on the old wording. Nothing here claims that the Review 07 run of 120 requests overspent.

The Review 08 package's sentence ("A handle opened with the earlier limits is refused afterwards") stays as history. This is its correction.

## Carried unchanged

- Packet v2, including its blank human-reviewer fields.
- Project permissions: 29076, 30088 and 30784 only.
- The separation of automatic-acceptance precision from raw-observation precision.
- The two views of the pending disputes.

No owner answer has been received, and none is assumed.
