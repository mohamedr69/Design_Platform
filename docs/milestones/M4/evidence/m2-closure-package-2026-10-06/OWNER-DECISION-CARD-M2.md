# Owner decision card — M2 closure (one card; final, Verification 42 recorded)

Written by the orchestrator (Fable 5.1) under A-11, 2026-10-06. Nothing here is authorized until the owner decides. Every item below is owner-only; every other preparation step is complete or in independent verification. `PILOT` = `G:\dev (2)\dev\ep-platform-merged\ep-platform\docs\milestones\M2\real-project-pilot`; `MR` = this roadmap folder.

## A. What is ready (exact identities)

| Item | Value |
|---|---|
| Frozen declaration v3 | `PILOT\declaration-r32-v3\FRESH-VALIDATION-DECLARATION-R32-V3.json`, sha256 **`9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`** (supersedes v2 `f38fb281…25af`, which binds the absent Desktop installation and is never to be run) |
| Package manifests | declaration-r32-v3 `a2df60dca2dfba5ebaff8bdc4b73ef76926cbecd7fd58c8916885e7e709a1a24` (277 files); review42 `ab2bc40d6ab5a45b0f7dca710f188b1e9f2a9cb4da80118177c7b1df9658e782` (126 files); `BINDING-MANIFEST-R42.json` `00ae5f98a7a2b415c43980d0e56d1dc207a3cdf24ca8935f586845695ee59a3c` (319 bindings) |
| Code | baseline `C:\t\iso\frozen-r12` `3d5607d99fcebf08ac45f5df937ad615ecc16fb3`; candidate `C:\t\iso\cand-r29` `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d`; both clean |
| Independent verification | Verification 41 of v2: VERIFIED WITH CONDITIONS (C1 disk). **Verification 42 of review42 + v3: ORCH-10 VERIFIED, 0 blockers, 0 majors, 1 minor (R42-09: the venv's packages are not re-checked at run time → owner `pip freeze` precondition in `RUNBOOK-ADDENDUM-R42.md`), no conditions** (`MR\reviews\M2-review-42\INDEPENDENT-VERIFICATION.md` `b0f4ad99…9b30`) |
| Cohort and models | 24 documents (16 decision-bearing, 4 revision top-ups, 4 negative controls) from EP-3563, EP-22349, EP-27331, EP-15744, EP-26687, EP-29255 (A-02, A-06); reference set `r32-labels-reviewed-2` `89c60e9d…b9a6`, independently AI-reviewed (Claude agents), not human-signed (amendment R32-01); lanes B (baseline, form reads) / C (candidate, L3+IG+CA+DR+PA) / R (reference, no credit) / P (probe 15 %, cap 36, no credit); models `claude-sonnet-5` (every read) and `claude-opus-5` (EV2 escalation only, unreachable under the declared switches); provider `claude-code`; CLI pinned by absolute path, sha256 `0b35df94…5b03`, version line `2.1.263 (Claude Code)` |
| Limits | parent 556 requests (B 240, C 240, R 40, P 36, no borrowing); 16,300,000 input / 3,260,000 output tokens; per request 90,000 / 20,000 (estimates, breakers); elapsed 604,800 s (7 days) from scope creation; project window 60 requests per project per rolling 24 h (deferral, never a charge); disk floor 2 GiB on C: enforced by the runner |
| Estimated usage | planning 145 requests (about 1.71 M input / 0.26 M output tokens); structural maximum 364; binding project EP-27331 63 / 160 requests → 2 or 3 invocations about 24 h apart |
| Cost | **unknown, never zero** (owner's Claude subscription; no price configured) |
| Residual risks | served-model identity UNRESOLVED offline (echoed id passes the runtime check); disk floor checked at each invocation's start only; isolation compares path text; an application path building its own provider object would bypass the chain (none found statically); the multi-nonce file lets a leaked token run up to 3 invocations within the 556 parent; results depend on the number of invocations (retry rule, R40-13); the 2 unsupported-format controls are absent (declared scope limitation); the labels are AI-reviewed, same model family as the system under test |

## B. Decisions needed from the owner (answer each by number)

**D1. Served-model identity** (A-10 item 2). Either (a) run the probe in `PILOT\declaration-r32-v3\RUNBOOK.md` §1.2 for both pinned ids and give the `init`, `assistant` and `result` lines to the orchestrator (a failed row = no dispatch, new declaration), or (b) accept UNRESOLVED identity with the fail-closed runtime check and its two limits.

**D2. Budget authorization for the R32 v3 fresh validation** (A-09 point 8; this is the 556-request parent budget, not authorized by anything so far). If yes, the owner performs, in one sitting, RUNBOOK §1.1 (CLI hash, version line, disk) plus the `pip freeze` comparison of `RUNBOOK-ADDENDUM-R42.md` §1 → §2.1–2.2 (token, digest, RUN file) → the orchestrator's independent `verify_run_file` (§2.3) → the owner's authorization message naming exactly: the frozen hash `9a55fa7b…1b40`, the digest, the RUN hash, the absolute RUN-file and authorization paths, the scope `m2-fresh-validation-r32-v3-2026-10-06` with limits `{"elapsed_s": 604800, "input_tokens": 16300000, "output_tokens": 3260000, "per_request_input": 90000, "per_request_output": 20000, "requests": 556}` in `C:\t\r2x\ledger\r2x-ledger.sqlite`, and invocation 1 (§5.1) → §2.5 authorization file → §3 scope creation → §5.1 `run`. **D2a (sub-choice):** per-invocation authorization files (2 or 3 files, one per resume) or ONE file with 3 nonces covering all planned resumptions (`write_authorization --invocations 3`, RUNBOOK §2.5 (b); a 4th invocation would need a new file). The orchestrator can run invocations only if the owner sets the token in the orchestrator's environment; otherwise the owner runs each command and the orchestrator verifies read-only. The orchestrator will never fabricate the token, the digest or the authorization.

**D3. Acknowledgements** (none blocking): R40-15 (application page limits leave documents COMPLETE with unread pages, affecting R's diagnostic only); R40-13 (the failed-read retry changes plan v2 §4); keep the CLI at 2.1.263 with auto-update off for the run's duration; the output-token bound would be hit first in lane P in the pessimistic case; the scope date is the local date 2026-10-06.

**D4. Owner-confirmable values** (any change = new hash + new verification): per-project application limit `"96"`; scope name `m2-fresh-validation-r32-v3-2026-10-06`; run folder `C:\t\r2x\r42-sandbox\r32-v3`; `AI_EFFORT` low; `resume_policy` `full`; disk floor 2 GiB; `max_invocations_per_file` 3.

**D5. The expanded sealed pilot (30 projects / 1,200 documents / 40 sheets; policy §10, roadmap step 4).** It is still a required M2 gate; no decision has descoped it. Confirm it stays (after R32 and a selection) or descope it by a register entry. (Acceptance-matrix gate G6.)

**D6. The BOQ track** (policy §2; `ACCEPTANCE.md` item 6 "a model-enabled BOQ run is M2 evidence still missing"). Order a separate BOQ validation declaration (labelled sheets, own budget) or descope it. (G8.)

**D7. Dates and document sections** (roadmap completion criterion; not scored by R32). A separate validation scope or a descoping entry. (G3.)

**D8. Human Golden truth beyond the R32 cohort** (roadmap "manually verified Golden cases"; policy §8). A human check of a declared sample, or a general amendment admitting AI-reviewed reference sets for M2 closure. (G9.)

**D9. H-03 eligibility** (client MTS forms need the model; their project is not AI-eligible). Grant eligibility for that project's staged copies, or leave H-03 open. (G1.)

**D10. Which tree M2 accepts** (G14). The running merged application (`7ecd2d3`) contains none of the reviewed M2 corrections (its `backend\app` equals the frozen trees' root commit) and has since diverged with rules M2 never evaluated. Either (a) accept M2, when its gates pass, on the frozen candidate lineage and make the port into an isolated copy of the merged installation (with the compatibility checks of `M2-COMPATIBILITY-REPORT.md`) the first M3-entry condition, or (b) require that port and its independent compatibility review before M2 acceptance.

**D11. Recorded owner policies** (DEFECTS.md P-obs-4; SAR stamp-vs-tick; 6538-G5 grouping): rule, or leave as review items.

## C. What happens without a decision
Nothing is dispatched. The orchestrator continues only offline work (none remains that does not depend on D1–D11 or on the R32 result). M2 stays CHANGES STILL REQUIRED; M3 does not start.
