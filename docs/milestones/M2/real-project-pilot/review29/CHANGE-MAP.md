# Change map: Review 29 candidate

**Candidate tree.** The candidate is `C:/t/iso/cand-r29`, branch `r29-candidate`, commit **`a4ce6a3`**. Its parent is `719e8de`. It is an isolated clone, with `core.autocrlf=false` like `cand-ai4`, so every unchanged file is byte-identical to `cand-ai4`.

**Untouched.** None of these changed: the accepted baseline `3d5607d` (`C:/t/iso/frozen-r12`), the four-arm candidate `719e8de` (`C:/t/iso/cand-ai4`), harness v4.3, labels r26.1 and r26.2, evaluator .9, the `four-arm-final/` package, the live ledger, live settings, services and data, sealed content and the owner's repository.

The candidate source changed through a reproducible patcher, not by hand edits. `scripts/apply_patch.py` makes 13 counted, anchor-checked edits. `make_eval6.py` creates `m2_eval6.py` from `m2_eval5.py`.

## Files

| File | Change |
|---|---|
| `backend/app/ai/evidence_reader.py` | +545 / −12. The four switches and their identities, plus the C1 to C4 code described below. |
| `backend/scripts/m2_eval6.py` | New. Evaluator `.10`, derived from `.9` (`m2_eval5.py`, unchanged, sha256 `38326f14…`) with one change in `score_layer`. |
| `backend/tests/_r29.py` | New. Explicit switch sets, identities from a fresh interpreter, synthetic pages. |
| `backend/tests/test_r29_identity_guard.py` | New. 39 tests: C1 controls and the D03 shape end to end. |
| `backend/tests/test_r29_adjudication.py` | New. 18 tests: C2 shapes, order invariance and the split-text regression. |
| `backend/tests/test_r29_decision_region.py` | New. 14 tests: D16, D17 and D18 shapes, rotations, controls and bounds. |
| `backend/tests/test_r29_association.py` | New. 6 tests: the D26 shape under `.9` and `.10`, and PA round trips. |
| `backend/tests/test_r29_persistence.py` | New. 12 tests: identities, isolation, cache, retry, profile and repeated processing. |

## `evidence_reader.py`, by contract

| Contract | Where | What |
|---|---|---|
| Switches | before `MIN_REQUEST_S` | `IDGUARD_ENABLED`, `ADJUDICATE_ENABLED`, `DECISION_REGION_ENABLED` and `ASSOC_ENABLED` are read from their own environment variables. CA, DR and PA refuse to start without an explicit `AI_EVIDENCE_SCHEDULING=required_first`. Each appends its own suffix to `EVIDENCE_POLICY_VERSION`, and DR also to `READER_VERSION`, adding the prompt `locate_decision`. With all four off, nothing is appended. |
| C1 | `identity_structure`, `_in_margin_band`, `_role_evidence`, `identity_role_guard`, `_guard_verdict`, `_value_verdict` | Every identity and revision verdict now goes through `_value_verdict`: 6 sites in `_read_page` and `_read_page_required`, and 1 in `_finish_page`. With IG off, that is `validate_value` itself. With IG on, a guarded identity becomes a `candidate` carrying `guard`, `guard_evidence` and a reason. Its value, region and readings are kept, it establishes no page identity, and it gets no targeted read. |
| C1 / C2 | `_discovery_reading` | Under IG or CA, discovery's reading carries the printed label discovery gave. With both off, the reading dict is unchanged. |
| C2 | `adjudicate_conflict`, `_identity_established`, `_adjudicate_page` | Under CA, the per-reading region texts are kept (`texts_by_source`). After the targeted reads, `_finish_page` adjudicates identity and then revision conflicts. The observation gains `adjudication` and, on resolution, `superseded`. **Revision 1:** E4 counts model readings only, and the identity string is `conflict-adjudication-2026-10-02.2`. |
| C3 | `LOCATE_DECISION_*`, `validate_decision_dr`, `_decision_vocab_regions`, `_full_text_coverage`, `_decision_region_read` | Under DR, `_read_page_required` takes the decision-region path instead of the discovery-only decision block, which becomes an `elif`, so DR off is unchanged. The `_finish_page` decision verdict uses `validate_decision_dr` when the context came from DR. The decision observation gains `decision_path`, and the page fields gain `decision:route`. A new field outcome, `incomplete:decision_unknown`, is used. |
| C4 | `_page_target`, `_apply_page_association`; `association_of` | Under PA, the decision target is the identity established on the page. At the end of `_finish_page`, own observations gain `page_binding`. A targetless revision or decision is held with `association = held:no_page_target`, carrying its candidates and reason. `association_of` returns that hold unchanged, and only for observations that carry `page_binding`, which PA alone writes. |

## Evaluator `.10` (`m2_eval6.py`)

There is one functional change, in `score_layer`. When a group associates with another page's component (`cross_page` or `target_cross_page`), only its identity facts take that association. Its dependent facts are judged on their own page:
- on a page with no record, a false positive when asserted and held on a no-record page when held;
- on a page with one component, against that component (`own_page_component`);
- otherwise, unassociated.

The version string and docstring are the only other changes.

## Not changed

Prompts and schemas of existing tasks are unchanged. So are `validate_value`, `validate_decision`, `merge_evidence`, `evidence_for` (apart from the PA-only branch in `association_of`), the BOQ path, triggers, caps (8 and 12), the deadline and ROI logic, the ledger and the scorer v4.
