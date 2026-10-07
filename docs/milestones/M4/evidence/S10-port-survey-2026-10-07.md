# S10 - Static port survey: candidate vs. merged tree (for unified M4, closure item 6)

| Item | Value |
|---|---|
| Scope | Roadmap section 8, M4 closure item 6: "Port accepted candidate changes onto an isolated copy of the current merged tree, preserving current interfaces/preparation behavior; run compatibility and final independent acceptance on the chosen acceptance tree." This record is the static survey a controlled port would start from. **No port is executed here; the owner's D10 decision (`OWNER-DECISION-CARD-M2.md`) is open.** |
| Date | 2026-10-07 |
| Method | Static reading; nothing run except read-only git commands and `sha256sum` of `git show`/`git cat-file` output. No pytest, no model, no OCR, no write to any tracked file, no checkout/stash/reset/merge, no process started or stopped. |
| Trees | Merged repository: `G:/dev (2)/dev/ep-platform-merged/ep-platform`, branch `claude/upbeat-lovelace-sa9j3w`, HEAD `2e407f87350f867f141e8ff1f076c0b9dc4bc781`. Baseline frozen tree: `C:/t/iso/frozen-r12`, commit `3d5607d99fcebf08ac45f5df937ad615ecc16fb3` (separate git repository). Candidate frozen tree: `C:/t/iso/cand-r29`, commit `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` (separate git repository), root commit `c692f1e...` ("AI-EV0 baseline", Review 05 Candidate C tree). Copies also exist under `G:/dev (2)/dev/ep-platform-merged/ep-platform/m2-workspaces/C_t/iso/`; **not used** — all commands below ran against `C:/t/iso/frozen-r12` and `C:/t/iso/cand-r29`. |

## 1. Identity

Commands: `git rev-parse HEAD`; `git status --short`; `git log --oneline -1`, run in each tree's own working directory.

| Tree | Path | `git rev-parse HEAD` | `git log --oneline -1` | `git status --short` | Clean? |
|---|---|---|---|---|---|
| Merged repository | `G:/dev (2)/dev/ep-platform-merged/ep-platform` | `2e407f87350f867f141e8ff1f076c0b9dc4bc781` | `2e407f8 Agent hooks call python, not python3, on the owner's Windows PC; session log` | 10 modified tracked files (`.claude/agents/ep-implementer.md`, `README.md`, `backend/.env.example`, `backend/library/symbols/symbol_library.json`, `docs/SESSION-LOG-2026-10-07-windows.md`, `docs/UNIFIED_MASTER_ROADMAP.md`, `docs/milestones/M3/M3-DECISION-PACK.md`, `docs/milestones/M3/M3-POLICY-CONTRACT-DRAFT.md`, `frontend/vite.config.ts`, `stop-backend.bat`) + 1 untracked dir (`docs/milestones/M4/evidence/m2-closure-package-2026-10-06/`) | **No** — dirty at the time of this survey (other agents/processes are active on this clone per the task brief; not touched by this survey) |
| Baseline frozen tree | `C:/t/iso/frozen-r12` | `3d5607d99fcebf08ac45f5df937ad615ecc16fb3` — matches the expected `3d5607d` | `3d5607d review12-candidate: legacy anchor reconstruction carries exact entries with reliable order (R12-01A value reselection, R12-01B unordered context)` | empty | Yes |
| Candidate frozen tree | `C:/t/iso/cand-r29` | `a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d` — matches the expected `a8aaced` | `a8aaced M2 review 29 candidate: C1 revision 2 -- the identity role guard applies to single-literal verdicts (a held conflict keeps its targeted read; the final verdict is guarded); identity-role-guard-2026-10-02.2; tests` | empty | Yes |

## 2. The closure decision's claim: merged 445ee27 vs. the frozen trees' root c692f1e

Commands: `git rev-parse 445ee27:backend/app` (merged repo); `git rev-parse c692f1e:backend/app` (cand-r29); `git merge-base --is-ancestor c692f1e HEAD` (frozen-r12, HEAD=3d5607d); `git merge-base --is-ancestor 445ee27 HEAD` and `git merge-base HEAD 445ee27` (merged repo).

| Check | Result |
|---|---|
| `backend/app` tree hash at merged `445ee27` | `4c768e910173bd8d94a1087be8c19a5c90c98809` |
| `backend/app` tree hash at cand-r29 `c692f1e` (root commit) | `4c768e910173bd8d94a1087be8c19a5c90c98809` — **identical**, confirms `M2-CLOSURE-DECISION-2026-10-06.md` section 5's claim |
| Is `c692f1e` an object of frozen-r12? | Yes — `c692f1e` **is frozen-r12's own root commit** (`git log --oneline --reverse \| head -1` = `c692f1e AI-EV0 baseline...`); `git merge-base --is-ancestor c692f1e 3d5607d` = true; `git rev-list --count c692f1e..3d5607d` = 9 commits |
| Is `445ee27` an ancestor of merged HEAD (`2e407f8`)? | **No.** `git merge-base --is-ancestor 445ee27 HEAD` returns non-zero. `445ee27` sits on the local branch `desktop-worktree`, a sibling of HEAD's branch, not merged into it. |
| Where do they diverge? | `git merge-base HEAD 445ee27` = `636341796346ab7b13cd894570c9a9b42e87ebca`. From that point: `git rev-list --count 636341796346ab7b13cd894570c9a9b42e87ebca..HEAD -- backend/app` = **100** commits touching `backend/app` on HEAD's side; `git rev-list --count 636341796346ab7b13cd894570c9a9b42e87ebca..445ee27 -- backend/app` = **72** commits on the `445ee27` side. `backend/app` tree hash at HEAD is `08af6ab2c54015dfc0febf7790126ad76534ded9` and at the merge-base is `bf1098a41cdf69063d3f51d31d708a75ebe8bd45` — both differ from `445ee27`'s `4c768e91...`, confirming the merged tree diverged substantially and separately from the Desktop snapshot. |
| Is `bb5871d` (named in the task as the merge/candidate) an ancestor of HEAD? | **Yes** (`git merge-base --is-ancestor bb5871d HEAD` = true) — unlike `445ee27`, `bb5871d` is in HEAD's own history. |

**Net finding:** the closure decision's narrow claim (445ee27's `backend/app` == cand-r29's root `c692f1e`) checks out exactly. But `445ee27` itself is not part of merged HEAD's ancestry — it is a sibling snapshot on `desktop-worktree`. The tree that actually matters for a port target, merged HEAD (`2e407f8`), is a separate 100-commit line from the merge-base with `445ee27`, and its `backend/app` hash (`08af6ab2...`) differs from both `445ee27` and `c692f1e`.

## 3. The three deltas in cand-r29 / frozen-r12

Commands: `git diff --stat <a> <b>` and `git diff --name-status <a> <b>`, run in the repository that holds both endpoints.

### 3a. Candidate delta `c692f1e..a8aaced` (full Review 06-29 history, run in cand-r29)

`git diff --stat c692f1e a8aaced` tail: **52 files changed, 24161 insertions(+), 8613 deletions(-)**

| Group | Files (M=modified, A=added) |
|---|---|
| backend/app/ai (4) | M provider.py; M submittal_reader.py; A evidence_reader.py; A ledger.py |
| backend/app/core (1) | M config.py |
| backend/app/routers (1) | M submittal.py |
| backend/app/services (7) | M design_sheet_extractor.py; M document_control.py; M document_processing.py; M document_sync.py; M title_block.py; M transmittals.py; A labelled_fields.py |
| backend/app/alembic | none |
| backend/scripts (4) | M m2_boq_eval.py; A m2_eval4.py; A m2_eval5.py; A m2_eval6.py |
| backend/tests (35) | M test_design_sheet_extractor.py; M test_extraction_pilot.py; A (33 files): `_e_crop_coords.py`, `_e_frame_shim.py`, `_keyed_provider.py`, `_r29.py`, `fixtures/evidence_reader_r10.py`, `fixtures/evidence_reader_r11.py`, `fixtures/evidence_reader_r6.py`, `fixtures/evidence_reader_r7.py`, `fixtures/ledger_r7.py`, `test_ai_ledger.py`, `test_ai_pilot_2026_09_30.py`, `test_ai_pilot_r18.py`, `test_ai_pilot_r19.py`, `test_ai_pilot_r21.py`, `test_evidence_reader.py`, `test_evidence_reader_r7.py`, `test_m2_boq_eval3.py`, `test_m2_eval4.py`, `test_m2_eval5.py`, `test_m2_review06_boq.py`, `test_m2_review06_titleblock.py`, `test_m2_review07_boq.py`, `test_m2_review07_extraction.py`, `test_m2_review08.py`, `test_m2_review09.py`, `test_m2_review10.py`, `test_m2_review11.py`, `test_m2_review12.py`, `test_r29_adjudication.py`, `test_r29_association.py`, `test_r29_decision_region.py`, `test_r29_identity_guard.py`, `test_r29_persistence.py` |
| docs | none |
| other | none |

13 app files + 4 scripts files + 35 test files = 52. No docs, no alembic, no `other` files in this delta.

### 3b. Baseline delta `c692f1e..3d5607d` (run in frozen-r12; what the baseline tree already carries, Reviews 06-12)

`git diff --stat c692f1e 3d5607d` tail: **38 files changed, 20334 insertions(+), 8613 deletions(-)**

Same groups as 3a minus the R29-only files: app/ai (evidence_reader.py A, ledger.py A, provider.py M, submittal_reader.py M — 4, same as candidate), core/config.py M, routers/submittal.py M, services (design_sheet_extractor.py M, document_control.py M, document_processing.py M, document_sync.py M, title_block.py M, transmittals.py M, labelled_fields.py A — 7, same as candidate), scripts (m2_boq_eval.py M, m2_eval4.py A, m2_eval5.py A — **3**, missing `m2_eval6.py` which is R29-only), tests (**18**: test_design_sheet_extractor.py M, test_extraction_pilot.py M, plus 16 of the "added" test files from 3a — missing the 17 R29-only test files `_e_crop_coords.py`, `_e_frame_shim.py`, `_keyed_provider.py`, `_r29.py`, `test_ai_pilot_2026_09_30.py`, `test_ai_pilot_r18.py`, `test_ai_pilot_r19.py`, `test_ai_pilot_r21.py`, `test_evidence_reader_r7.py`, `test_m2_eval4.py`... — see 3c for the exact R29-only set).

### 3c. The four R29 fixes on top of the baseline, `3d5607d..a8aaced` (run in cand-r29)

`git diff --stat 3d5607d a8aaced` tail: **18 files changed, 3851 insertions(+), 24 deletions(-)**

| Group | Files |
|---|---|
| backend/app/ai (1, modified only) | M evidence_reader.py — carries the R29 switches (section 6) |
| backend/scripts (1, new) | A m2_eval6.py |
| backend/tests (16) | A `_e_crop_coords.py`, `_e_frame_shim.py`, `_keyed_provider.py`, `_r29.py`, `test_ai_pilot_2026_09_30.py`, `test_ai_pilot_r18.py`, `test_ai_pilot_r19.py`, `test_ai_pilot_r21.py`; M `test_evidence_reader_r7.py`, `test_m2_review08.py`, `test_m2_review10.py`; A `test_r29_adjudication.py`, `test_r29_association.py`, `test_r29_decision_region.py`, `test_r29_identity_guard.py`, `test_r29_persistence.py` |

This is what Review 30 verified on top of the baseline: one application file (`evidence_reader.py`, modified again) plus 17 test-support files (4 new fixtures/shims, 4 new AI-pilot tests, 3 modified existing R-tests, 5 new R29 switch tests, 1 new eval script) — no other `backend/app` file changes between baseline and candidate.

## 4. Divergence of the merged tree against the candidate delta

Method: for every file touched in the candidate delta (3a), `sha256sum` of `git show c692f1e:<file>` (cand-r29), `git show a8aaced:<file>` (cand-r29), and `git show HEAD:<file>` (merged repo, `2e407f8`); existence checked first with `git cat-file -e`. Classification: **CLEAN PORT** = merged HEAD hash equals `c692f1e` hash (candidate diff applies without conflict); **DIVERGED** = merged HEAD hash differs from `c692f1e` (three-way merge needed); **NEW IN CANDIDATE** = absent at both `c692f1e` and merged HEAD; **ABSENT IN CANDIDATE** = present in the delta's old side but gone at `a8aaced` (none found).

### 4a. backend/app and backend/scripts files (17)

| File | sha256 (first 16) at c692f1e | at a8aaced | at merged HEAD | Classification |
|---|---|---|---|---|
| app/ai/evidence_reader.py | ABSENT | `d74397b374fc91a6` | ABSENT | NEW IN CANDIDATE |
| app/ai/ledger.py | ABSENT | `d9f92297f29ee9ca` | ABSENT | NEW IN CANDIDATE |
| app/ai/provider.py | `69dd9d77d416565b` | `d465961efb07b7f9` | `12b843cf2207e4e3` | DIVERGED |
| app/ai/submittal_reader.py | `da7d956395f47aca` | `7127640681241387` | `24126b115a9ca6c6` | DIVERGED |
| app/core/config.py | `29bad5a748b3b529` | `b4fbc07f5a50e147` | `f25eab75ef5da045` | DIVERGED |
| app/routers/submittal.py | `195b271e6bd86324` | `564c9f7a33653511` | `8774a7f83d6c1e53` | DIVERGED |
| app/services/design_sheet_extractor.py | `0e91c68a7acd4b83` | `b110d172df487aaa` | `0e91c68a7acd4b83` | **CLEAN PORT** (HEAD == c692f1e) |
| app/services/document_control.py | `9905f2f548d14f8f` | `78e392c4b880b37c` | `bfa527c7d422234c` | DIVERGED |
| app/services/document_processing.py | `9df8b03f983a35a0` | `5f5b25940ad0677f` | `9df8b03f983a35a0` | **CLEAN PORT** (HEAD == c692f1e) |
| app/services/document_sync.py | `6d4d87031d1f2574` | `5992f72647c857b0` | `f25dfadbe24ba4ee` | DIVERGED |
| app/services/labelled_fields.py | ABSENT | `7b81cfb4f319dbb7` | ABSENT | NEW IN CANDIDATE |
| app/services/title_block.py | `84a0a7d78416db89` | `afde12aa38f28f8a` | `8e0c7084391da29e` | DIVERGED |
| app/services/transmittals.py | `a7ce483990832355` | `e1038f946e338332` | `a7ce483990832355` | **CLEAN PORT** (HEAD == c692f1e) |
| scripts/m2_boq_eval.py | `45556d44d57ce190` | `550e1a3c8eafcc93` | `45556d44d57ce190` | **CLEAN PORT** (HEAD == c692f1e) |
| scripts/m2_eval4.py | ABSENT | `65f3e096dd8ec93b` | ABSENT | NEW IN CANDIDATE |
| scripts/m2_eval5.py | ABSENT | `38326f149a7f4924` | ABSENT | NEW IN CANDIDATE |
| scripts/m2_eval6.py | ABSENT | `268d86231260392d` | ABSENT | NEW IN CANDIDATE |

**Counts (app+scripts, 17 files): CLEAN PORT 4, DIVERGED 7, NEW IN CANDIDATE 6, ABSENT IN CANDIDATE 0.**

For each DIVERGED file, merged commits since `445ee27` that touched it (`git log --oneline 445ee27..HEAD -- <file>`, run in the merged repo):

| File | Commits since 445ee27 (count) | Commit list (oldest last) |
|---|---|---|
| app/ai/provider.py | 9 | `bb5871d`, `c6aabd6`, `b844adc`, `8a2f409`, `664a942`, `dcea9f6`, `fe35933`, `e49c2bf`, `eb057eb` |
| app/ai/submittal_reader.py | 14 | `8a2f409`, `b5c2222`, `e49c2bf`, `6db2558`, `4a8e02e`, `da691bb`, `2cf0783`, `7d1a36a`, `540baa5`, `0db160f`, `af31580`, `0cca19c`, `daded8e`, `196d060` |
| app/core/config.py | 19 | `bb5871d`, `b844adc`, `8a2f409`, `dcea9f6`, `bb86483`, `a990dbe`, `0427eff`, `fe35933`, `b5c2222`, `b01f2c6`, `e49c2bf`, `eb057eb`, `ccef2c2`, `74c6fba`, `123a7c9`, `a88c1fc`, `79c3b19`, `701a910`, `7d8027f` |
| app/routers/submittal.py | 14 | `b5c2222`, `6db2558`, `4a8e02e`, `da691bb`, `2cf0783`, `7d1a36a`, `8e08a8c`, `e651378`, `0db160f`, `b29de36`, `aa857e7`, `af31580`, `127d6b9`, `6a58de1` |
| app/services/document_control.py | 19 | `909d87c`, `9bac4be`, `77b68f7`, `11865f2`, `81cddb3`, `8e6465a`, `761a213`, `882433b`, `b81f4fc`, `b01f2c6`, `e49c2bf`, `1e1f394`, `5fa1a5b`, `3cb0a49`, `17a1698`, `123a7c9`, `7d1a36a`, `79c3b19`, `0c30299` |
| app/services/document_sync.py | 19 | `909d87c`, `9bac4be`, `81cddb3`, `882433b`, `b81f4fc`, `b01f2c6`, `e49c2bf`, `eb057eb`, `6db2558`, `3cb0a49`, `ccef2c2`, `74c6fba`, `123a7c9`, `7d1a36a`, `79c3b19`, `ece478f`, `3b1ba2c`, `0c30299`, `0cca19c` |
| app/services/title_block.py | 2 | `81cddb3`, `b81f4fc` |

The density (2 commits for `title_block.py` vs. 19 for `document_control.py`/`document_sync.py`/`config.py`) is a rough proxy for merge-conflict risk: `title_block.py` has the shallowest independent history and would likely be the easiest three-way merge of the diverged set; `document_control.py`, `document_sync.py` and `config.py` have the deepest, unrelated histories (file sync, drawings log, archive, power calculations, OCR-unavailable handling — none of it candidate-related) and the highest conflict risk.

### 4b. Test files of the delta, same method

Full pairwise check on the two modified test files plus a bulk existence check on the 33 added test files (30 checked individually by name against merged HEAD in one pass, plus 3 more — `test_evidence_reader_r7.py`, `test_m2_review08.py`, `test_m2_review10.py` — checked individually):

| File | at c692f1e | at a8aaced | at merged HEAD | Classification |
|---|---|---|---|---|
| tests/test_design_sheet_extractor.py | `e44fa5c6cffa4da5` | `9bbdbd735e100858` | `e44fa5c6cffa4da5` | **CLEAN PORT** (HEAD == c692f1e) |
| tests/test_extraction_pilot.py | `6ce724005cb5cd91` | `ee622bfcb196eee4` | `1e11f837ac42d447` | DIVERGED (HEAD differs from both candidate endpoints — this test file was independently edited on the merged line) |
| tests/test_evidence_reader_r7.py | ABSENT | present | ABSENT at HEAD | NEW IN CANDIDATE |
| tests/test_m2_review08.py | ABSENT | present | ABSENT at HEAD | NEW IN CANDIDATE |
| tests/test_m2_review10.py | ABSENT | present | ABSENT at HEAD | NEW IN CANDIDATE |
| other 30 added test/fixture files (listed in 3a) | ABSENT (28 of them are new after c692f1e per 3b/3c; `test_evidence_reader.py`, `test_m2_boq_eval3.py`, etc. are new between c692f1e and 3d5607d) | present | **ABSENT at HEAD, all 30** (`git cat-file -e HEAD:<file>` checked individually for each) | NEW IN CANDIDATE (all 30) |

**Counts (tests, 35 files): CLEAN PORT 1, DIVERGED 1, NEW IN CANDIDATE 33, ABSENT IN CANDIDATE 0.**

### 4c. Combined counts (52 files in the full candidate delta)

| Classification | app/scripts | tests | Total |
|---|---|---|---|
| CLEAN PORT | 4 | 1 | 5 |
| DIVERGED | 7 | 1 | 8 |
| NEW IN CANDIDATE | 6 | 33 | 39 |
| ABSENT IN CANDIDATE | 0 | 0 | 0 |
| **Total** | **17** | **35** | **52** |

Roadmap note satisfied by this table: the candidate's regression tests (33 of 35 test files, all NEW IN CANDIDATE) are entirely absent from the merged tree today — a port of the 8 diverged + 6 new application files without also porting the 33 new + 1 diverged test files would leave the ported behavior with no regression coverage in the merged tree.

## 5. Version constants

Commands: `git grep -n "PARSER_VERSION\s*=\|TITLE_BLOCK_VERSION\s*=\|INDEX_VERSION\s*=\|OCR_VERSION\s*=\|BOX_VERSION\s*="` against each ref, restricted to `backend/app`.

| Constant | Merged HEAD (`2e407f8`) | cand-r29 `c692f1e` (root) | frozen-r12 `3d5607d` | cand-r29 `a8aaced` |
|---|---|---|---|---|
| `document_control.PARSER_VERSION` | `document_control.py:431` = `"parse-2026-10-05.5"` | `document_control.py:361` = `"parse-2026-09-28.6"` | `document_control.py:362` = `"parse-2026-09-29.9"` | `document_control.py:362` = `"parse-2026-09-29.9"` |
| `document_control.BOX_VERSION` | `document_control.py:926` = `"box-4"` | `document_control.py:821` = `"box-4"` | `document_control.py:825` = `"box-4"` | `document_control.py:825` = `"box-4"` |
| `title_block.TITLE_BLOCK_VERSION` | `title_block.py:34` = `"titleblock-2"` | `title_block.py:27` = `"titleblock-1"` | `title_block.py:27` = `"titleblock-3"` | `title_block.py:27` = `"titleblock-3"` |
| `document_sync.INDEX_VERSION` | `document_sync.py:51` = `"index-2026-09-24.4"` | same (`:51`) | same | same |
| `page_cache.OCR_VERSION` | `page_cache.py:37` = `"ocr-1"` | same | same | same |
| `design_sheet_extractor.PARSER_VERSION` | `design_sheet_extractor.py:47` = `"2026-09-28.2"` | same value and line | `"2026-09-29.2"` (:47) | `"2026-09-29.2"` (:47) |
| `drf_extractor.PARSER_VERSION` | `drf_extractor.py:241` = `"2026-09-13.2"` | same | same | same |
| (unrelated, not asked for but caught by the grep) `spec_text.PARSER_VERSION` / `statements.STATEMENT_PARSER_VERSION` | `"spec-text-1"` / `"statement-1"`, unchanged across all four trees | — | — | — |

No `OCR_VERSION`/`BOX_VERSION` keys other than those listed were found by the grep in any tree.

**Reading:** the merged tree's `document_control.PARSER_VERSION` (`parse-2026-10-05.5`) and `title_block.TITLE_BLOCK_VERSION` (`titleblock-2`) are **ahead in date but not in content** of both frozen trees — they come from the merged line's own 2026-10-05 changes (`g/project-log-and-drawing-scan`, per S8/G14), never evaluated by M2, and are numerically higher than `a8aaced`'s `titleblock-3` while representing unrelated rule changes. `design_sheet_extractor.PARSER_VERSION` at merged HEAD (`2026-09-28.2`) matches the pre-candidate baseline `c692f1e`, consistent with the CLEAN PORT finding for that file in section 4a.

## 6. Switches: the four R29 switches and the evidence-stage hook

All four switches and the hook are defined only in `backend/app/ai/evidence_reader.py` as raw `os.environ.get(...)` reads (not as `Settings`/`config.py` keys), gated to require `AI_EVIDENCE_SCHEDULING=required_first` set explicitly; `config.py` carries one related key, `ai_evidence_variant`, that gates whether the evidence stage runs at all.

| Switch | Env var | Defined at (a8aaced) | Default | Version string added when on | Same-named key in merged HEAD `app/core/config.py`? |
|---|---|---|---|---|---|
| IG — identity role guard (C1) | `AI_EVIDENCE_IDGUARD=1` | `evidence_reader.py:125,132` | off (`== "1"` test, unset -> False) | `IDGUARD_VERSION = "identity-role-guard-2026-10-02.2"` | No — `git grep -n AI_EVIDENCE_ HEAD -- backend/app` returns nothing |
| CA — conflict adjudication (C2) | `AI_EVIDENCE_ADJUDICATE=1` | `evidence_reader.py:126,133` | off; requires `AI_EVIDENCE_SCHEDULING=required_first` or raises `RuntimeError` (`:136-139`) | `ADJUDICATE_VERSION = "conflict-adjudication-2026-10-02.2"` | No |
| DR — bounded decision-region path (C3) | `AI_EVIDENCE_DECISION_REGION=1` | `evidence_reader.py:127,134` | off; same required-first guard | `DECISION_REGION_VERSION = "decision-region-2026-10-02.1"` | No |
| PA — page/target association invariant (C4) | `AI_EVIDENCE_ASSOC=1` | `evidence_reader.py:128,135` | off; same required-first guard | `ASSOC_VERSION = "page-association-2026-10-02.1"` | No |
| Evidence-stage hook | `ai_evidence_variant` (Settings key, `config.py:413` in a8aaced) + `evidence_stage()` function (`evidence_reader.py:2652`) | `config.py:413` default `"off"`; called from `document_processing.py:494-502` ("off unless `AI_EVIDENCE_VARIANT` names a variant") | off | `AI_EVIDENCE_SCHEMA = "ai-evidence-2"` (`:2065`) | No — `git show HEAD:backend/app/core/config.py \| grep ai_evidence_variant` returns nothing; `backend/app/ai/` at merged HEAD lists `__init__.py, budget.py, cache.py, evaluation.py, evidence.py, guard.py, metrics.py, project_policy.py, proposals.py, provider.py, sheet_reader.py, submittal_reader.py, verification.py` — no `evidence_reader.py`, no `ledger.py` |

**Finding:** none of the four switches, their required-first scheduling precondition, or the evidence-stage hook exist anywhere in the merged tree's `app/core/config.py` or `app/ai/` directory. A port must bring the whole `evidence_reader.py` module (absent, section 4a) and its required upstream module `ledger.py` (also absent) before any switch can be turned on; `config.py`'s `ai_evidence_variant` key would need to be added to the diverged merged `config.py` as part of the three-way merge.

## 7. Compatibility evidence the port would have to repeat

Taken from `docs/milestones/M2/M2-COMPATIBILITY-REPORT.md` and gate G14 of `docs/milestones/M4/evidence/m2-closure-package-2026-10-06/M2-ACCEPTANCE-MATRIX.md`; **listed as the acceptance checks a port must redo on whichever tree the owner picks (D10), not run here:**

1. **Full-suite failure-identity check** — candidate `a8aaced` full suite reported 1,824 pass / 35 skip / 2 fail; baseline `3d5607d` reported 1,657 / 35 / 2; the 2 failures were identical by name and message between the two (`FAILURE-COMPARISON.json`, verified by Review 30). A port's acceptance would need the same pairwise pass/skip/fail counts and identical-failure check, run on the ported tree against whichever tree is chosen as the pre-port baseline (merged HEAD today has its own, different, pre-existing failures per `docs/milestones/M4/evidence/S9-defect-delta-2026-10-07.md` — 9 pre-existing failures, 3 of them Windows-only-by-design — so "identical failures" would need to be reconciled against that separate baseline, not the frozen trees' 2 failures).
2. **Flags-off identity** — `M2-COMPATIBILITY-REPORT.md` section 1's preserved-contracts table (legacy `ProjectDocument.role` unchanged; `extracted.records` shape additive only; revision values unchanged; business-status ownership unchanged — only `project_documents` and `document_dependencies` changed on the clone repair; manual overrides/domain identities untouched, 0 rows changed; `G-01` not reachable from the changed code on the default path; classification/M3 routing untouched). A port's acceptance would need to re-show the same contracts hold with the R29 switches (section 6) left off.
3. **Ordinary-processing deltas explained** — section 3 of the compatibility report's before/after snapshot on a disposable clone of two named projects (EP-30088 project 4, EP-30784 project 1): exact row/table/field counts (e.g. project 4 `document_dependencies` 164 -> 335 rows, 203 changed; `project_documents` 525 -> 525, 520 changed; 0 roles changed in either project). A port's acceptance would need an equivalent clone-repair comparison on the isolated copy of whichever tree is chosen, with the same "0 roles/manual-override rows changed" result.

None of these three checks were executed by this survey; they are named here as exactly what the port's compatibility step would have to reproduce, per the task's instruction not to propose or perform the port.

## What this survey does not establish

- Whether a three-way merge of the 7 DIVERGED app files (section 4a) and the 1 DIVERGED test file actually resolves without manual conflict — only that the merged tree's content differs from the candidate's pre-change state, and which commits touched each file since `445ee27`. No merge was attempted (disallowed; read-only).
- Semantic compatibility between the candidate's behavior and the merged tree's independent 2026-10-05 changes to `document_control.py`/`title_block.py` (parse-2026-10-05.5 / titleblock-2) — this survey compares bytes and version strings only, not behavior.
- Any accuracy, pass-rate, or model-cost consequence of applying the port — no model was run, per the task's prohibition and because no budget is authorized (D2 in `OWNER-DECISION-CARD-M2.md` is open).
- Whether the frozen copies under `m2-workspaces/C_t/iso/` (explicitly excluded by the task) match the `C:/t/iso/` originals used here — not compared.
- The full content of `docs/roadmap-evidence/2026-10-06/candidate-integration-check.json` (named in S8 as not opened) — not read here either.
- Windows CRLF vs. LF normalization for the sha256 comparisons in section 4: all hashes above are of raw `git show`/`git cat-file` bytes in each repository as git stores them, with no conversion applied. Where a CLEAN PORT finding is reported (section 4a, 4b), the bytes were byte-for-byte identical with no normalization needed; this survey did not need to invoke the CRLF-conversion caveat that S8 used for the roadmap-snapshot comparison.

## Inputs still needed

1. **Owner decision D10** (`OWNER-DECISION-CARD-M2.md` section B) — which tree M2/M4 accepts: (a) the frozen candidate lineage, with the port into an isolated copy of the merged installation as the first M3-entry condition, or (b) require that port and its independent compatibility review before M2 acceptance. Nothing below can be authorized without it.
2. **A model budget** for any accuracy claim about the ported code — none is authorized (D2 is open); this survey used no model and makes no accuracy claim.
3. **The isolated copy on which the port would be made** — the task brief and `M2-CLOSURE-DECISION-2026-10-06.md` section 5 both specify the port target is an isolated copy of the *current* merged tree, not `C:/t/iso/frozen-r12`, `C:/t/iso/cand-r29`, or the live merged checkout itself; no such isolated copy exists yet (not created by this survey, which is read-only).

## Commands used

```
# per tree
git rev-parse HEAD
git status --short
git log --oneline -1

# section 2
git rev-parse 445ee27:backend/app                      # merged repo
git rev-parse c692f1e:backend/app                       # cand-r29
git log --oneline --reverse | head -1                   # frozen-r12 root check
git merge-base --is-ancestor c692f1e HEAD                # frozen-r12
git rev-list --count c692f1e..HEAD                       # frozen-r12
git merge-base --is-ancestor 445ee27 HEAD                 # merged repo
git merge-base --is-ancestor bb5871d HEAD                 # merged repo
git merge-base HEAD 445ee27                               # merged repo
git rev-list --count <merge-base>..HEAD -- backend/app    # merged repo
git rev-list --count <merge-base>..445ee27 -- backend/app # merged repo
git rev-parse HEAD:backend/app                            # merged repo

# section 3
git diff --stat c692f1e a8aaced ; git diff --name-status c692f1e a8aaced       # cand-r29
git diff --stat c692f1e 3d5607d ; git diff --name-status c692f1e 3d5607d       # frozen-r12
git diff --stat 3d5607d a8aaced ; git diff --name-status 3d5607d a8aaced      # cand-r29

# section 4 (repeated per file)
git cat-file -e <ref>:<path>
git show <ref>:<path> | sha256sum
git log --oneline 445ee27..HEAD -- <path>                 # merged repo

# section 5
git grep -n "PARSER_VERSION\s*=\|TITLE_BLOCK_VERSION\s*=\|INDEX_VERSION\s*=\|OCR_VERSION\s*=\|BOX_VERSION\s*=" <ref> -- backend/app

# section 6
git grep -n -i "AI_EVIDENCE_" <ref> -- backend/app
git show <ref>:backend/app/core/config.py | grep -n "ai_evidence_variant"
git show <ref>:backend/app/ai/   (tree listing)
```
