# Change map: frozen R21 candidate (from the reviewed `69ee759`)

The candidate lives in the scratch clone `C:/t/iso/ep-platform`, worktree `C:/t/iso/cand-ai4`, branch `ai-pilot-r21-2026-09-30`. It is not the owner's checkout. The frozen commit is in [bindings/SOURCE-BINDINGS.json](bindings/SOURCE-BINDINGS.json); the diff and patches are in [candidate/](candidate/).

## Application: `backend/app/ai/evidence_reader.py` only

One switch per behaviour. With every switch unset the identities equal the accepted `3d5607d`'s (asserted by the identity-matrix test and by the declaration writer). The reviewed legacy configurations keep their identity strings byte-for-byte: G; T (`+region-support…+targeted-completion…` / `+targeted…`); T+E (`+located-discovery-2026-09-30.2`).

| Switch | Env | Behaviour | Identity suffix |
|---|---|---|---|
| G | `AI_EVIDENCE_GUARD=1` | bare revision token never an identity | policy `+guard-rev-token-2026-09-30.1` |
| Rsup | `AI_EVIDENCE_SUPPORT=v2` | rotation-correct clip + bounded local OCR support in **every** read path (before: only through the targeted branch) | policy `+region-support-2026-09-30.1` |
| Sched | `AI_EVIDENCE_SCHEDULING=required_first` | the required-first reader path (`_read_page_required` / `_finish_page`) with or without optional reads | reader `+required-first-2026-09-30.1` (when X is off) |
| D | `AI_EVIDENCE_DEADLINE=1` | request timeout = min(provider timeout, remaining job time); 20 s floor; OCR bounded by remaining time | reader `+deadline-2026-09-30.1` |
| ROI | `AI_EVIDENCE_ROI=1` | located title-block discovery for drawing sheets (R19-01 absence rule), **without** the deadline | policy + reader `+roi-discovery-2026-09-30.1`, prompt `discover_region` |
| X | `AI_EVIDENCE_TARGETED=1` | optional targeted context reads (requires G; implies Rsup and Sched, as reviewed) | policy `+targeted-completion-2026-09-30.2`, reader `+targeted-2026-09-30.2` |
| E (legacy) | `AI_EVIDENCE_EFFICIENT=1` | ROI + D together | unchanged `+located-discovery-2026-09-30.2` |

Code changes:
- `_region_texts(page, region, ocr_lines, run)` chooses the support policy in force and is used by the legacy page reader, the required-first reader and the targeted read; the targeted branch no longer selects the support policy on its own.
- `_finish_page` makes optional reads only when X is on; with X off the same required path runs and the observations are built the same way.
- `_discover` gates on ROI; the timeout and OCR bound gate on D.
- The switch attributes hold the **explicit** environment values only; the legacy implications (T ⇒ Rsup + Sched, E ⇒ ROI + D) are applied at use time (`_support_v2()`, `_required_first()`, `_deadline()`, `_roi()`) and in the identity block, so a configuration behaves the same whether it is set by the environment or by a test through either the explicit or the legacy attribute. Identity strings are computed at import from the environment, unchanged.
- Three commits on the branch (`48ba991` switches + arm tests; `a03939d` adapters recognise ROI; the final commit: explicit-only attributes, pilot fixtures stating their full switch set, adapters skipping the r21 module). The first two matrix runs on the intermediate commits exposed the fixture snapshot problem; they are superseded by the matrix on the frozen commit.

**Not changed:** thresholds, validation, role checks, retained evidence / association / incomplete-read rules, request caps, merge / selection, the evaluator, BOQ verification and queue, business consumers. No migration, no role / category / status edits, no default activation.

## Arms

| Arm | Switches | Reader / policy identity |
|---|---|---|
| L1 | G + Rsup + Sched + D | `…+required-first…+deadline…` / `…+guard…+region-support…` |
| L2 | L1 + ROI | `…+required-first…+roi-discovery…+deadline…` / `…+region-support…+roi-discovery…` |
| L3 | L1 + X | `…+targeted…+deadline…` / `…+region-support…+targeted-completion…` |
| L4 | L2 + X | `…+targeted…+roi-discovery…+deadline…` / `…+targeted-completion…+roi-discovery…` |

The result cache is keyed by policy, reader and prompt versions, so no result crosses arms (verified in the dry chain: cache keys pairwise disjoint).

## Tests

| File | What |
|---|---|
| `tests/test_ai_pilot_r21.py` (new, 8 tests) | identity matrix (flags off == accepted; legacy strings unchanged; four arms distinct); each arm on a rotated A2 sheet through the persisted path with the real crop for L2 / L4 (discovery task and image, fixed order, X only in L3 / L4, rotation-correct support in every arm, deadline stamp on every request); arm caches never cross and a same-arm restart reuses its own; cap refusal as a recorded budget stop; the deadline floor |
| `tests/_e_crop_coords.py`, `tests/_e_frame_shim.py` | also recognise the explicit ROI switch (tests only) |

## Harness (outside the application)

- `coverage_v3.py`: the review20 draft made caller-safe: `select_attempt` binds to source hash / profile / variant / policy; `complete_in_scope` distinguishes long files; `extra_facts` counts emitted facts outside scope.
- `score_arms_v3.py`: per-arm coverage, evaluator recovery over all planned documents, field-specific read-in-both sets per pair with IDs, transport separate, usage.
- `arm_a.py`, `arm_shares.py`, `arm_ev.py`: derived from the continuation runners by recorded substitutions.
- `declare_r21.py`: DRY (synthetic stage) and DRAFT (frozen sample) declarations.
