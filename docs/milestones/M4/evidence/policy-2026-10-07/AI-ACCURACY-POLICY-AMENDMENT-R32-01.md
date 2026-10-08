# AI-ACCURACY-POLICY — Amendment R32-01 (section 8), append-only and run-specific

**Owner decision C-3, route (b), 2026-10-03** (authority register entry A-04). The original `AI-ACCURACY-POLICY.md` (sha256 `7efa891b55fd6a4113f08cff8d0acdca7832d611524bb7f884ec4e5bc30a4f47`) remains unchanged. This amendment is a separate document with its own hash and is bound in the fresh M2 validation declaration.

## Scope
This amendment applies only to the frozen R32 fresh M2 validation cohort (EP-3563, EP-22349, EP-27331, EP-15744, EP-26687, EP-29255; packages `fresh-cohort-r32`, `fresh-cohort-r32-reviewed`, `fresh-cohort-r32-reviewed-2`; label set `r32-labels-reviewed-2`, sha256 `89c60e9d6a2f06c9d2afaa74fc2a6d3fca471bc56c9eb1591a6a32d1df0bb9a6`) and its declared extensions. It applies to no other cohort, run or milestone.

## Amendment to section 8 ("Gold labels must be independently checked against originals, not generated or approved solely by another model")
For this frozen M2 validation only, labels independently drafted and independently reviewed by separate Claude agents may be used as an **AI-reviewed reference set**.

They must not be described as:
- human-signed labels;
- human Golden Truth;
- independently human-verified evidence.

## Required controls
- drafting and review agents remain separate;
- predictions were not consulted;
- every label and ruling remains source-bound;
- uncertainty stays explicit;
- the amendment applies only to the frozen R32 cohort and its declared extensions;
- the original policy remains unchanged;
- the amendment receives its own hash and is included in the declaration binding;
- final metrics explicitly state that their reference set is independently AI-reviewed.

## Record of how the controls are met for `r32-labels-reviewed-2`
- Drafting: one Claude Opus 5.5 session (packet `fresh-cohort-r32`, draft `r32-labels-draft-1` sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334`).
- Review: separate fresh Claude Opus 5.5 agents R32REV-B1 to B7, R32REV-CONSOLIDATE, R32REV-CRITIC, R32REV-DISPOSE (`MR/reviews/M2-label-review-r32-draft-1/REVIEWER-RESPONSE.final.json` sha256 `920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b`), and the Independent Preparation Review 33 agents (`MR/reviews/M2-review-33/INDEPENDENT-REVIEW.md` sha256 `8d20baecc8eef24d2047287de77b3c252c1e5641f2dc61c5ffe449f6bbd97804`).
- Predictions not consulted: stated and verified in each review record; no prediction exists for the cohort.
- Source binding: every value cites a staged render or crop bound by sha256 (`EVIDENCE-INDEX.json`).
- Explicit uncertainty: states `ambiguous`, `illegible`, `unsupported` and association `uncertain` are kept; nothing unresolved remains after Review 33.

Every metric computed against this reference set must carry the statement: "reference set independently AI-reviewed (Claude agents), not human-signed".
