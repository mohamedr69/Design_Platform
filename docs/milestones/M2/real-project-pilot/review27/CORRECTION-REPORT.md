# Review 27 correction — funding clarity and independent label binding (2026-10-01)

**Scope:** documentation, label provenance and declaration binding only. No model or provider request, scope creation, schedule, dispatch or H-06 rerun. No provider switch, new model, raised request or token limit, ledger or harness change, sample replacement, default adoption, production action or M3. The application baseline `3d5607d`, candidate `719e8de`, harness v4.3, every earlier package, the r26.1 labels, the R21 skeletons, the reviewer files, live settings, services and data, and all sealed content are unchanged. **The 688-request proposal remains unapproved.**

| Document | Content |
|---|---|
| [DECISION-CARD.md](DECISION-CARD.md) | the single owner decision, with the CLI token limitation and unknown cost stated |
| [BUDGET-PROPOSAL.md](BUDGET-PROPOSAL.md) | budget proposal v2 (replaces review26's) |
| [OWNER-CLAIMS-DIFF.md](OWNER-CLAIMS-DIFF.md) | old → new owner-facing claims |
| [LABELS-SUMMARY.md](LABELS-SUMMARY.md) | label r26.2 provenance, rulings and the three off-title-block populations |
| [RUNBOOK.md](RUNBOOK.md) | runbook v2 (declaration v2, token semantics) |
| [CHANGE-MAP.md](CHANGE-MAP.md) · [COMMANDS.md](COMMANDS.md) | files and commands |
| [declaration/FINAL-DECLARATION.v2.json](declaration/FINAL-DECLARATION.v2.json) | sha256 **`6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1`** |
| [labels-r26.2/](labels-r26.2/) | the frozen labels (manifest sha256 `ed3c88e40daadaee6e4a7271d7dd9be430773a8c1b0976030d1bfb2a27a9a72d`) |

## R27-01 — accurate funding statement: corrected

The budget proposal, decision card, runbook and declaration (`ledger.limit_semantics`) now consistently state four things:
1. **Requests:** at most 688 **application-visible** requests (A 8 / L1 160 / L2 160 / L3 180 / L4 180). One CLI request can contain several provider-internal turns.
2. **Tokens:** the thresholds act on **estimates before dispatch**. Actual usage is recorded after the response, and an overshoot opens a breaker that stops **later** requests. The CLI cannot enforce actual token limits, and timeout or unknown usage stays charged at the estimate.
3. **Removed claims:** "at most 20 M / 3 M", the hard per-request bounds and "never an overspend" are gone. Cost is unknown.
4. **Elapsed time:** 96 h per document arm and 4 h for A are kept, clearly as an unapproved proposal and not a completion guarantee.

These statements cite the frozen ledger contract (module docstring, `reserve()`, `settle()`) and the Review 27 independent probe. No ledger code was changed and no limiter was built.

## R27-02 — independent label rulings: applied as r26.2

- The independent owner-delegated **AI** source review is credited and bound to its record by hash. It is not human sign-off and not blind.
- **D17:** the readable decision value is kept, and the actor becomes explicit field-level uncertainty (inferred, not established). The schema limitation is disclosed: the runner's uncertainty list is document-level and doubles as the stop-policy exclusion, so the stop policy is unchanged and the actor is not scored.
- **D19:** the literal C. Revise & Resubmit is recorded beside the evaluator's coarse `rejected`. It is not propagated to the enclosed sheets.
- **D05:** the printed ASBUILT stage is kept as metadata.
- **D27:** marked not visually verified, with no extraction credit.
- All other literals and uncertainties are unchanged; the diff touches only those fields.
- The reviewer's pre-run interpretation is recorded: 5 source-attributed decision documents among the 24 primary meet the minimum of 4 (6 readable decision documents, 7 records; the screen found 1/4; no top-up).
- The ROI population is stated from the frozen predicate, recomputed here: only D16–D18 are crop-eligible (one project, 2 explicit stamps), while D04, D19 and D22 use whole-page discovery. It is a small diagnostic, the non-regression gate is retained, and unsupported and incomplete pages stay in the denominators.

## Verification (offline; existing tests reused)

- **Labels:** r26.1's manifest and files were re-hashed and found unchanged before deriving r26.2. The r26.1 → r26.2 diff is limited to D05.stage_printed, D17.decision_actor and actor_attribution, and D19.decision_literal and decision_normalization, plus provenance and version fields. Register values, confidences and the document-level uncertainty set are identical.
- **Declaration:** v2 versus v1 differs only in labels, the review bindings, `supersedes`, `limit_semantics`, name, time, `harness_dir` and the workload note. Scopes, limits and caps are identical.
- **Evaluator binding:** the frozen v4 scorer loaded the r26.2 labels through declaration v2 and re-scored the review26 preflight runs. Recovery, coverage and eligibility are identical for every arm ([evidence/RESCORE-DELTA.json](evidence/RESCORE-DELTA.json)), so the rebinding changes no scored value.
- **ROI population:** recomputed with the frozen `title_block.is_drawing_sheet` ([evidence/ROI-POPULATION.json](evidence/ROI-POPULATION.json)), matching the reviewer.
- **Budget arithmetic and package integrity:** 8 + 160 + 160 + 180 + 180 = 688. The package check covers the manifest, links, hashes, earlier packages, reviewer files and the live ledger ([evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json)).

## Status, stated separately

| Item | Status |
|---|---|
| Correction readiness | R27-01 and R27-02 corrected; package frozen; submitted for review (not self-approved) |
| Owner funding decision | **pending**: [DECISION-CARD.md](DECISION-CARD.md), declaration `6c0189b3…` |
| Experiment | **not run** (live ledger still 128/150; no scope of the new family) |
| Extraction accuracy | **unresolved** |
| Default variant | **none selected** |
| M2 | **CHANGES STILL REQUIRED** (H-06 complete and unchanged) |
