# M2 Review 07: provenance correction and freeze (R7-05)

## Correction to Review 06

Review 06's REAL-MODEL-RESULTS said the declaration recorded "the SHA-256 of every changed file". **That was wrong.** The packaged `EXPERIMENT-DECLARATION.json` has `tree.uncommitted_candidate_files_sha256 = {}`.

The cause: the script ran `git status` from `backend/`, the paths came back relative to the repository root, and none resolved, so the field stayed empty. The 18-file manifest in the Review 06 package describes the source **at the end** of Review 06. It does not show which bytes ran each earlier request.

**No per-run source snapshot was taken in Review 06, and none is invented now.**

## What can be recovered, and how it is labelled

1. **The Review 06 final source: recovered and verified.** Commit `043dee9` (`review06-final (reconstructed)`) in the isolated scratch repository was built by applying the Review 06 package's `candidate.diff` and `candidate_new_files` to the baseline `c692f1e`. **All 18 changed files match the package's SHA-256** (after restoring each file's own line endings). This is a genuine snapshot of the Review 06 final state.
2. **Which source each Review 06 run executed: reconstructed from timestamps, not recorded.**
   - The patch scripts' file times (local UTC+4) and each run manifest's `at_utc` give this order:
     - every evidence-reader change up to `er_patch5` (23:35) came before the AI-EV1 and AI-EV2 evidence runs (EV1 about 00:25, EV2 01:27 local);
     - `er_patch6` (BOQ verifier `.2`) came after EV2 finished (02:50);
     - `tb_patch5` (titleblock-3, parse `.8`) came after AI-EV0 (19:29Z) and does not affect the evidence stage, which reads stored rows.
   - The AI-EV0 run's rows carry `parse-2026-09-28.7`.
   - So the AI-EV1/EV2 **document** runs executed the evidence reader as of `er_patch5` (policy `.1`, prompts `2026-09-29.1`) on a parse `.7` deterministic base. The BOQ EV1b run used the verifier `.2`.
   - This is a **reconstruction**. Byte-exact hashes of those intermediate states cannot be proven after the fact.
3. **Review 06 identity strings stored in the outputs:**
   - each row: `extracted.parser_version` and `profile`;
   - each AI envelope: `version`, `policy` and `variant`;
   - each call: the model returned.

   These are consistent with the reconstruction.

## The Review 07 freeze

`evidence/freeze/FREEZE-R7.json`, SHA-256 `f2aad5711e69e076fee813c224e04f8ddf27bee23b8bcf705639231e73f4d76e` (including amendment 1).

| Item | Value |
|---|---|
| Frozen candidate | commit **`c9a1a1459c30115daf8bb40f47aba542f2b6079a`** in `C:/t/iso/ep-platform` (the isolated scratch repository; the owner's tree is untouched). Parent: `043dee9`, the verified Review 06 final. Worktree: `C:/t/iso/frozen-r7`, with no `.env` (hermetic). |
| Tracked files | 410 under `backend/app`, `scripts`, `tests` and `alembic`; `git ls-tree` SHA-256 is in the manifest (`evidence/freeze/git-ls-tree.txt`) |
| Parser | `parse-2026-09-29.9` |
| Title block | `titleblock-3` |
| Labelled fields | `fields-2026-09-29.1` |
| Transmittal observe | `transmittal-observe-2026-09-29.1` |
| Sheet extractor | `2026-09-29.2` |
| Listed-item association | `listed-item-2026-09-29.1` |
| Evidence reader | `evidence-reader-2026-09-29.2`, policy `evidence-policy-2026-09-29.2`, schema `evidence-schema-1`; prompts discover / read-* `2026-09-29.1` and read-boq-row `2026-09-29.2` |
| Prompt, system text and schemas | SHA-256 of each in the manifest |
| Audit | 20%, seed `audit-2026-09-29` |
| Ledger / estimator | `ai-ledger-2026-09-29.1`, `estimator-2026-09-29.1`, calibration p95 table in the manifest |
| Evaluators | document `m2-pilot-eval-2026-09-29.6` (see amendment), `.4` kept; BOQ `m2-boq-eval-2026-09-29.3`; files SHA-256 in the manifest |
| Labels | SHA-256 of Golden v1, the v2 page labels, the BOQ corrections v2, the holdout labels and pages, the holdout BOQ labels, and the frozen sample and BOQ sets |
| Models | provider claude-code; aliases small `sonnet`, standard `opus`; identifiers returned so far `claude-sonnet-5` and `claude-opus-5`. An alias is configuration, not a model version; the returned identifier is recorded per call. |
| Dependencies | Python 3.12; `pip freeze` (56 packages) SHA-256 in the manifest (`evidence/freeze/pip-freeze.txt`) |
| Default settings | `ai_evidence_variant=off`, `ai_ledger_path=None`, extraction profile default |

**Amendment 1** (commit `1455f8b`) changes only `scripts/m2_eval5.py` and `tests/test_m2_eval5.py`: evaluator `.5` → `.6`.
- **What changed:** on a no-record page, a cross-page copy of the document's own identity now associates, as `.4` did; and records the application holds as pending evidence hold all their facts.
- **Why:** inspecting the stored-output re-scores showed two false `fp` findings.
- **When:** after those re-scores and **before any matched-run result was read**. EV0 had finished processing; no score had been computed.
- The application code is unchanged from `c9a1a14`, so the matched run and the hermetic suite execute the `c9a1a14` application.
- The `.5` outputs are kept.

## Runs kept apart

| Run | Tree | Status |
|---|---|---|
| `det-*-parse7-superseded` | parse `.7` (Review 06) | kept, superseded; promoted pilot not completed (stopped) |
| `det-pilot` / `det-holdout` | parse `.8` (Review 06 final deterministic) | kept |
| `det9-pilot` / `det9-holdout`, both profiles | parse `.9` = the frozen candidate's reading rules | final deterministic |
| `ai-ev0` / `ai-ev1` / `ai-ev2` | Review 06 real-model runs: parse `.7` base, policy `.1`, verifier `.1`/`.2` for BOQ | historical exploration; **EV1 partial** outside EP-29076 (200-call cap); **EV2 on EP-29076 only** |
| `replay-ai-ev1/ev2` | the stored Review 06 readings re-validated under policy `.2`, **no new calls** | a policy replay; it cannot stand in for a changed prompt or model |
| `m-ev0` / `m-ev1` / `m-ev2` | **the frozen `c9a1a14` application**, the same 12 source hashes, default profile, one ledger | Review 07 matched run (MATCHED-RUN.md) |
