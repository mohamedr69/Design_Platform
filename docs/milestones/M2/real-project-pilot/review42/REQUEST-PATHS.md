# Request paths of every lane, review42 (ORCH-10 task 2.2; Verification 40 R40-04; owner decision A-11, option 2)

- **What this is:** review39's request-path analysis, re-run unchanged on the same two frozen trees, plus what the application's **global provider** is in each lane of the review42 harness and where it is installed. It replaces review39's claim (R40-04) that the runtime gate covers "a missed static edge" in every lane: that held for lane B only. In review42 it holds in every lane, by construction.
- **Author:** R42PORT-IMPL (Claude Opus 5.5, `claude-opus-5-5`, self-reported), 2026-10-05/06. Not self-approved; pending Verification 42.
- **Trees (read-only):** baseline `C:/t/iso/frozen-r12/backend` (HEAD `3d5607d9…`, clean) for lane B; candidate `C:/t/iso/cand-r29/backend` (HEAD `a8aacedd…`, clean) for C, R and P.
- **Evidence:** `REQUEST-PATHS-STATIC.json` (`8b6488cf…621f`; `scripts/harness-r32/request_paths_r42.py`), `tests/test_global_provider_r42.xml` (7 tests), `evidence/demos/DEMO-global_provider.json`.
- **Standing status:** M2 CHANGES STILL REQUIRED; M3 not started. No provider or model request was made to produce this.

## 1. The static analysis, re-run (unchanged method)

`request_paths_r42.py` imports `request_paths_r39.py` (byte-identical to review39's) and re-runs it: 192 modules and 31 provider-call sites per tree. The sites reached from each lane's entry point are **identical** to review39's (B 10 sites from `document_processing.run`, 664 functions; C and R 5 sites from `evidence_reader.evidence_stage`, 243 functions; `evidence/OUTPUTS-R42.json` `reached_sites_equal_to_review39`). Review39's site-by-site reading (`PILOT/review39/REQUEST-PATHS.md` section 2) therefore stands unchanged: every reached site is declared and bounded, disabled, readiness-only, or the ledger wrapper.

## 2. The global provider of each lane (new in review42)

| Lane | Global provider (`app.ai.provider.get_provider()` returns) | Installed at (`lane_r32.py`) | First application entry | Installed first |
|---|---|---|---|---|
| B | the harness chain: StopGuardR38 → GateStoreProvider → allowance → identity guard → dispatch guard (unchanged since review38) | line 434, `if LANE == "B"` | line 471 | yes |
| C | `run_control_r38.RefusingGlobalProvider` | line 144, `if LANE in ("C", "R", "P")`, right after the provider module is imported | line 471 | yes |
| R | the same | line 144 | line 471 | yes |
| P | the same | line 144 | line 564 (`probe_r38`) | yes |

- **What the refusing provider does.** Any `complete()` returns `dispatch_refused` and never reaches the CLI, a ledger, the chain or the allowance's charges. It writes the contract breach `global_provider_request` (`CONTRACT-BREACH.json` and its log), records a refusal in the allowance, an event in the lane's recorder (per document and page, class `limit`: the document is INCOMPLETE), and makes every lane terminal. The run is INVALID under the contract's undeclared-request rule; a resume is refused.
- **`ready` is True on purpose.** An application path that first asks whether AI is available is told yes, so a path that would then send a request reaches the refusal (recorded) instead of skipping silently.
- **The lane checks at its end** that its refusing provider is still the global provider (a replacement would refuse the lane).

## 3. Every `get_provider()` site resolved

`REQUEST-PATHS-STATIC.json` `get_provider_sites` lists all 88 site-lane pairs: the 22 `get_provider()` sites of the baseline tree in lane B, and the 22 of the candidate tree in each of C, R and P (reached by the lane's entry point or not). Each one resolves to the harness chain (B) or to the refusing provider (C, R, P); none reaches a configured provider. No application `set_provider()` call is reached from any lane's entry point.

## 4. Dynamic proof (dry, 0 CLI invocations, ledger unchanged)

A dry drill injects an **application path** (`from app.ai.provider import get_provider; get_provider().complete(...)`, with a declared task kind and the current document's context) into each lane:

| Lane | Result |
|---|---|
| C, R, P | refused `dispatch_refused`; `CONTRACT-BREACH.json` kind `global_provider_request`; run INVALID; never charged (every charge of the lane is a dispatch through the chain to the dry stub); the resume refused |
| B | unchanged: the call reaches the harness chain, passes the gate as a declared request and ends at the dry stub (`dry_refused`); no breach; the run FINISHED |

Tests: `test_global_provider_r42.py` (7). Demonstration: `evidence/demos/DEMO-global_provider.json`. The suite and the demonstration ran under the R42 audit guard (any `claude` process or network use refused; 0 refusals).

## 5. Residual risk (stated plainly)

An application path that builds a provider object itself (not through `get_provider()`) and calls it would bypass the chain. The static analysis finds no such reached site in either tree: every reached `complete()` site is the reader's own call on the provider the lane passes in, or the ledger wrapper. The declared ledger scope (556 requests, the token and elapsed limits) and the post-run `ledger_live_check` still bound and expose any request.
