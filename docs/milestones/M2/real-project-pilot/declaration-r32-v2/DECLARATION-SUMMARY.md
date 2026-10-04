# Declaration summary for the owner: fresh validation R32, corrected declaration v2 (ORCH-09)

**Status: frozen, NOT authorized. No dispatch has happened.**
- **What does not exist:** a ledger scope, a token, an authorization file, a RUN file, a budget, a model request. Nobody ran the model-identity probe.
- **What comes next:** Independent Verification 41 of this package, then the owner's decisions (section 14). Then STOP.
- **Standing:** M2 is **CHANGES STILL REQUIRED**. M3 has **not started**.
- **Reference set:** every metric of this run is stated against a reference set independently AI-reviewed (Claude agents), not human-signed (`r32-labels-reviewed-2`, `89c60e9d…b9a6`).
- **Supersedes:** `declaration-r32/FRESH-VALIDATION-DECLARATION-R32.json` `38e08df9…76b0` (A-09: never authorized, never run, never to be run). Every difference is listed in `DECLARATION-DIFF.md`.

## 1. Declaration hash (A-08)

| | |
|---|---|
| File | `docs/milestones/M2/real-project-pilot/declaration-r32-v2/FRESH-VALIDATION-DECLARATION-R32-V2.json` (147,764 bytes, canonical JSON, LF) |
| **Frozen sha256** | **`f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af`** (also in `DECLARATION.sha256`); declared 2026-10-04T11:51:31Z |
| Contract | `r39-live-contract-4` (review39 `preflight_r32.validate_declaration`) |
| Binds | Harness `review39` (manifest `2430fa2b…d990`; `BINDING-MANIFEST-R39` `a6f703b4…567b`, 239 bound files)<br>`PROJECT-REQUEST-BOUNDS.json` `99be01fb…1721`, `RESUME-INVOCATIONS-R39.json` `9791fa89…cf6b`, `VISIBILITY-RESULT.json` `1811e456…192c`, `MODEL-ID-EVIDENCE.md` `37bec20e…0fb`, `REQUEST-PATHS.md` `0359ba76…619`, `DRAWINGS-AI-PROBE-R39.json` `19dcd79b…a4b8`<br>Run set `9058f3d6…7ce8`, truth `4e237a4e…e064`, reference set `89c60e9d…b9a6`<br>Policy `7efa891b…4f47`, amendment R32-01 `815d43fd…5de6`, authority register `346597d3…ffcfd` (A-09, A-10)<br>Candidate `a8aacedd…` and baseline `3d5607d9…` (both clean)<br>Verifications 38, 39 and 40; the review39 work-folder records (R40-20); Verification 40's R40-04 proof |
| The placeholder | `authorization.owner_token_sha256` holds `TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION`, exactly once. The preflight and the guard refuse it. |
| The RUN declaration | The owner makes it: the frozen file with only that value replaced by the token digest (`build_declaration_r40.py fill_owner_digest`). Its sha256, the **RUN hash**, is the one the runner, the guard, the authorization file and the scope command use. The frozen hash is never given to the runner (RUNBOOK section 2). |

## 2. Arm definitions (A-08; unchanged from the superseded declaration)

| Lane | Code | Switches | Task kinds (contract 4) | Role |
|---|---|---|---|---|
| **B** | baseline `3d5607d` | `AI_EVIDENCE_VARIANT=off` | `read_submittal_form` | The accepted path. The drawings-AI review is switched off (`application_env`). Runs first. |
| **C** | candidate `a8aaced` | L3 set (`VARIANT=EV1`, `GUARD=1`, `SUPPORT=v2`, `SCHEDULING=required_first`, `DEADLINE=1`, `TARGETED=1`) + IG `IDGUARD=1`, CA `ADJUDICATE=1`, DR `DECISION_REGION=1`, PA `ASSOC=1` | `discover_page`, `locate_decision`, `read_decision`, `read_field_context`, `read_identity`, `read_revision` | The combined candidate, from a verified copy of B's database. |
| **R** | candidate `a8aaced` | the L3 set | the same without `locate_decision` | The reference: served C's capture; requests C never made sent once. **No credit; never eligibility.** |
| **P** | candidate | `{}` | as C | The probe: a seeded 15 % of C's answered dispatches **as drawn at P's first run**, re-sent once, cap 36. **No credit.** |

## 3. Run-set counts (A-08)

- **24 documents:** 16 decision-bearing, 4 revision top-ups (F060, F043, F057, F046), 4 negative controls (F051, F042, F047, F066); 6 projects.
- **Matched projection (minimum 12):** identity **23** (margin 11), revision **16** (margin 4), decision **16** (margin 4).
- **Decision controls:** 16 positive, 8 negative.
- **Unsupported controls: 0 of 2** — a declared scope limitation (section 11).

## 4. Request caps, parent budget and lane allowances (A-08; A-09 point 3)

- **Parent budget (immutable):** 556 requests, 16,300,000 input tokens, 3,260,000 output tokens, 604,800 s elapsed.
- **Lane allowances:** **B 240 = C 240, R 40, P 36** (sum 556). No lane borrows another's. Failed, interrupted, timed-out and dispatched-but-unsaved requests stay charged. A resume resets nothing.
- **The ledger scope** `m2-fresh-validation-r32-v2-2026-10-04` has limits equal to the parent and is the backstop.
- **Harness project rolling window:** 60 requests per project per 86,400 s, **all lanes**. A refusal is a deferral, not a permanent stop.

## 5. Token thresholds (A-08)

- **Per request:** 90,000 input and 20,000 output, reserved on **estimates** before dispatch. They are breakers, not hard limits: the CLI has no hard bound, and one actual overshoot opens the scope's breaker for every later request (margins are thin: largest actual 81,625 / 19,568; R38-13).
- **Totals:** 16,300,000 / 3,260,000, enforced by the allowance on reported usage and by the scope. Per-lane estimates (B 7.0 M / 1.4 M, C 7.0 M / 1.4 M, R 1.2 M / 0.24 M, P 1.1 M / 0.22 M) are not enforced per lane (R35-10).

## 6. Estimated usage (A-08)

| | B | C | R | P | Total | Ceiling |
|---|---|---|---|---|---|---|
| Planning | 6 | 112 | 10 | 17 | **145** | 556 |
| Structural maximum (`PROJECT-REQUEST-BOUNDS`) | 48 | 240 (255 before the cap) | 40 (222 before the cap) | 36 (171 before the cap) | **364** | 556 |

- **Tokens, planning:** about 1.71 M input / 0.26 M output.
- **Tokens at the structural maximum with every request at the calibrated p95 of the largest task:** 15.6 M input / **3.62 M output**: above the 3.26 M output bound, so in that deliberately pessimistic case the ledger would refuse first (a visible budget stop).
- The superseded "conservative" 277 (8 requests per document) was not a bound (R38-08); the structural maximum replaces it.
- Retries of failed requests across resumes are not in these figures; they are bounded by the allowances, the parent and the window.

**Per project** (A-09 point 1; `PROJECT-REQUEST-BOUNDS.json`):

| Project | Docs | Pages | Planning, all lanes | Structural B / C / R / P = all lanes | Windows (60 per 24 h) | Largest lane-database rows |
|---|---|---|---|---|---|---|
| **EP-27331** | 6 | 23 | **63.0** | 12 / 72 / 40 / 36 = **160** | **3** | **84** |
| EP-26687 | 7 | 9 | 25.3 | 14 / 69 / 40 / 36 = 159 | 3 | 83 |
| EP-22349 | 5 | 11 | 29.3 | 10 / 51 / 40 / 36 = 137 | 3 | 61 |
| EP-3563 | 3 | 6 | 17.9 | 6 / 30 / 24 / 30 = 90 | 2 | 36 |
| EP-29255 | 2 | 3 | 9.4 | 4 / 21 / 18 / 21 = 64 | 2 | 25 |
| EP-15744 | 1 | 4 | 9.9 | 2 / 12 / 12 / 12 = 38 | 1 | 14 |

EP-27331's structural maximum is 160, not 154: B's reconcile repeat of a failed form read is now dispatched, so B is 2 per document. It would be **170** with the drawings-AI path enabled; that path is switched off.

## 7. Cost status (A-08)

**Unknown, and never zero.** The provider is `claude-code` on the owner's subscription; no price is configured (`AI_PRICE_*` `"0"`).

## 8. Stop rules (A-08)

| Event | Effect |
|---|---|
| Resolved-truth critical in **B** | **INVALID**; C never starts |
| Resolved-truth critical in **C** | C terminal; **RESULT**, NOT ELIGIBLE |
| Resolved-truth critical in **R or P** | a reference finding only |
| Unresolved-truth critical | reported only |
| Three consecutive provider failures | B: INVALID; C: INCOMPLETE; R or P: that lane only |
| Lane allowance, parent, ledger, breaker or guard refusal | a durable budget stop; INCOMPLETE in B or C |
| Project-window refusal | **DEFERRED** (resume at `resume_not_before`) |
| Model-identity mismatch; undeclared request path | **INVALID**; never resumed |
| Pages unread under the application's own per-document limits | document COMPLETE, pages listed and counted unread |

Terminal and run states: **INCOMPLETE**, **DEFERRED**, **INVALID**, **CLOSED**, RESULT, FINISHED (RUNBOOK section 5.3). The review39 resume rules (LIVE-RUN-CONTRACT v4 §4, §5, §6, §13) are carried verbatim and replace the review34 ones.

## 9. Concentration results (A-08)

`concentration_r32.py` is byte-identical in review36 and review39 (`fc5052f8…`) and the run set is unchanged, so the results on the proposal carry (`declaration-r32/concentration/CONCENTRATION-ON-PROPOSAL.json`, bound by hash):
- **ELIGIBLE is reachable in every field;** the smallest ELIGIBLE net gain is 2.
- **Never ELIGIBLE:** a net gain of 1; a net gain of 2 inside one project or one layout; any gain confined to EP-27331 / the EMAAR template (6 of 16 decision and 6 of 16 revision documents).
- Any C false acceptance on the 8 negative decision controls makes the field NOT ELIGIBLE.
- 1,084 gain sets cross-checked, 0 mismatches (reproduced by Verification 38).

## 10. Dispatch order (A-08)

1. **Owner, before invocation 1:** the probe (or acceptance of UNRESOLVED identity), `claude --version`, the two-hash procedure, the scope creation.
2. **Runner preflight** (nothing created before it passes): binding, contract 4, HEADs, truth and population gate, run set, bounds recomputation, scope, guard preview; then the run folder, the CLI version record and the nonce consumption.
3. **B**, then **C** only when no B document is deferred, then **R** and **P** only when no C document is deferred.
4. **Offline scoring** with one candidate-level outcome, the mandatory C ≥ R diagnostic and the unread pages.
5. **Deferral / resume** under `full`: **2 invocations** at the planning estimate (the last starts about 24.3 h after the first), **3** at the structural maximum (about 48.5 h); one owner authorization per invocation.

**No default is ever selected.**

## 11. A-09 items

| A-09 point | In this declaration |
|---|---|
| 1. Compatible limits; visible INCOMPLETE / deferral | EP-27331 planning **63.0**, structural **160**, **170** with the drawings path; the window governs; refusals visible; deferral and resume. **Compatible application limits (integer strings):** `AI_MAX_CALLS_PER_PROJECT_PER_DAY` **"96"** (required ≥ 84; margin 12 = one document's JobBudget), `AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY` **"600"** (tree default; governs only B's form reads, at most 12 rows), `AI_MAX_CALLS_PER_DOCUMENT` **"12"**, `AI_MAX_ELAPSED_S_PER_JOB` **"120"**. |
| 2. Pinned identities, CLI version | `claude-sonnet-5` (small), `claude-opus-5` (standard), provider `claude-code`, CLI line **`2.1.263 (Claude Code)`** (file `0b35df94…5b03`); recorded per invocation; a mismatch makes the run INVALID. |
| 3. Parent budget and lane allowances | section 4. |
| 4. Cross-page identity | **Rule CP-R38:** an association with another page's identity only when source, document identity, target and the labels' recorded page relationship (R1 / R2 / R3) are evidenced; held or conflicting identity earns no recovery credit. It replaces the .10-parity rule (H4, H5 closed). |
| 5. Shortfall | The 2 unsupported-format controls: 0 found. A declared scope limitation, never replaced after predictions, never removed from a report; unsupported-format safety and generalization are not claimed. |
| 6 and 7. R / P | No accuracy or recovery credit; never select a default; a truncated R or P makes its diagnostic **INCOMPLETE**. |
| 8. Authorization preconditions | Verification 41 accepts this package; the owner's budget authorization names the frozen hash, the digest, the RUN hash, the RUN-file and authorization paths, the scope with its limits and the first invocation; the RUN hash is independently verified; the authorization file names the RUN hash; the scope is created by `create_scope_r40.py` only then (RUNBOOK sections 2–3). |

## 12. A-10 items

- **The decision coverage gate is C ≥ B only. This is a change from plan v2** (plan v2's gate was C ≥ B **and** C ≥ R). It is not an unchanged gate. **C ≥ R is a mandatory diagnostic** in every result and report, with both lanes' counts, the missing coverage per document and page with each lane's class and the reason, and INCOMPLETE when R did not complete its population. R never determines eligibility. Every other safety, accuracy and completeness gate is carried verbatim.
- **The probe:** RUNBOOK section 1 (Verification 40 §6, amended): stream-json, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`, `--max-turns 1`, `--no-session-persistence --disable-slash-commands --strict-mcp-config --tools ""`, cmd.exe, an empty folder, once per pinned id; the expected evidence; the reading (an alias or an echoed id is never proof; `"<synthetic>"` is a CLI-made message; `message.model` is the server's statement, not proof; **the request count cannot be verified offline**).
- **Served-model identity: UNRESOLVED.** The runtime check is fail-closed under INVALID, with two limits: it compares the requested id the CLI reports, and an echoed id passes.

## 13. Verification 40 items

| Item | Where answered |
|---|---|
| R40-04 | `request_path_coverage`: the claim corrected (belt and braces for lane B only), the proof bound by hash (`evidence/r40-04-proof/`), the residual risk, the owner's two options (section 14) |
| R40-08 | integer strings for every count and time limit; the R39-18 risk and its handling (RUNBOOK section 6) |
| R40-10 | the `no_trigger` exclusion and the two unguarded corners as declared scope statements (`unread_page_rule`) |
| R40-12 | P's population drawn at P's first run (3 of 20 under the frozen sample, where an unfrozen draw would give 4 of 25), cap 36, seed `m2-r30-variation-2026-10-02` |
| R40-13 | the failed-read retry named a change from plan v2 §4 (`retry_rule`); the review39 resume rules replace review34's |
| R40-15 | acknowledgement (section 14) |
| R40-16 | the amended probe; no "exactly one request" claim |
| R40-19 | review39's SNAPSHOT-BEFORE cited as taken at 09:55:49Z |
| R40-20 | review39's final `AUDIT-LOG.md` (`62cac012…92d4`) and `PROGRESS.md` (`e0d60667…3107`) copied and bound |

## 14. Unresolved issues and the exact decisions needed from the owner

1. **Served-model identity: UNRESOLVED.** Decide one:
   - (a) **run the probe** of RUNBOOK section 1 yourself (both pinned ids), before any dispatch, and give the orchestrator the `init`, `assistant` and `result` lines; a failed probe means no dispatch and a new declaration; or
   - (b) **accept UNRESOLVED identity** with the fail-closed runtime check and its two stated limits.
2. **R40-04 (lanes C, R and P do not install the gate as the application's global provider).** Decide one:
   - (1) **accept the proof-based coverage** for C, R and P (two static analyses and one dynamic run with `get_provider()` raising: 0 calls), with the residual risk: an unknown application path calling `get_provider()` there would bypass the gate, the lane allowance, the window, the capture and the identity check; the ledger scope and the post-run ledger check would still bound and expose it; or
   - (2) **order a bounded harness change** that installs a refusing (or the chained) global provider in C, R and P, with its own independent verification and a re-declaration (a new hash). This declaration would then not be used.
3. **Acknowledgements (not blocking):**
   - **R40-15:** documents with application-internal page limits are COMPLETE with their unread pages listed (the orchestrator's reading of A-09, ORCH-021). It changes R's diagnostic completeness only, never eligibility.
   - **R40-13:** the failed-read retry is a change from plan v2 §4. B and C can obtain an answer on a retry; results can depend on the number of invocations; the rule is symmetric in rule, not necessarily in count.
   - **The CLI-version dead-end** (found in this task): if the runner's own version check refuses invocation 1, the run folder exists without an allowance and the run cannot continue (a new declaration would be needed). The runbook prevents it by having the owner check `claude --version` immediately before invocation 1. The alternative is a bounded harness change (record the version before creating the folder), its verification and a re-declaration.
   - **Token bounds:** in a pessimistic case (the structural maximum, every request at the p95) the output bound of 3.26 M would refuse first; a higher bound would be a new declaration.
4. **Owner-confirmable values** (changing any of them is a new declaration with a new hash): `AI_MAX_CALLS_PER_PROJECT_PER_DAY` 96; the scope name `m2-fresh-validation-r32-v2-2026-10-04`; the run folder `C:/t/r2x/r40-sandbox/r32-v2`; `AI_EFFORT` low (inert for the CLI adapter); `resume_policy` full.
5. **The budget authorization itself** (only after Verification 41): authorize, or not, the 556-request parent budget (16.3 M / 3.26 M tokens, 7 days from the scope's creation), the scope with exactly those limits, and the first invocation, naming the frozen hash, the digest, the RUN hash and the paths (RUNBOOK section 2.4). Expect **2** invocations (planning) to **3** (structural), each with its own authorization file. Cost unknown (subscription).

## 15. What is NOT authorized

Nothing in this package authorizes: a ledger scope; a token; an authorization file; a RUN file; a provider or model request; the probe by anyone other than the owner; any dispatch of B, C, R or P; a budget; a default variant; M2 acceptance; M3; production use or production database writes; any OneDrive change; opening a sealed project; any project outside the six; human sign-off claims for the AI-reviewed labels.

**Statuses, stated separately:** correction readiness: the corrected declaration is delivered, pending Verification 41 (not self-approved). Accuracy: none (no prediction exists). Label truth: reference set independently AI-reviewed (Claude agents), not human-signed. Permissions and budget: eligibility only (A-06); no scope, token, authorization or budget. **M2: CHANGES STILL REQUIRED. M3: not started.**
