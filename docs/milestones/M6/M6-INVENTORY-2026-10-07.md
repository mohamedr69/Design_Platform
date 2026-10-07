# M6 inventory: the AI classification pass (7 October 2026)

Unified milestone: M6 (Central Document Classification and Attribution). Task: ORCH-037 (ep-scribe). Worktree `G:/dev (2)/dev/ep-platform-merged/roadmap-u2`, branch `roadmap/u2`, HEAD at start `573780a561fac560b5e5b5344c227f348eb65fb2`.

## Status

**Implemented / partial, not accepted.** The pass is uncommitted in the live clone `G:/dev (2)/dev/ep-platform-merged/ep-platform` (branch `claude/upbeat-lovelace-sa9j3w`, HEAD 7a1bf6f) at 2026-10-07; file sha256 per the survey: `backend/app/services/document_classification_ai.py` ca9933373b1e (486 lines at the 22:13:40 snapshot; it changed at 22:13:09 and grew from 461 lines between two of the surveyor's reads). Anything edited after 22:14 is not covered.
Source: `MR/orchestrator/surveys/U2-DELTA-DRAWINGS-PROCESSING-2026-10-07.md` (the survey). No measured result exists: the survey states precision, recall, false-supported, mixed-component recall and system accuracy are "none measured". Nothing was run by the scribe.
`docs/DOCUMENT_CLASSIFICATION_AI.md:57` is cited by the survey as saying the classification switch is "on in the live installation since 7 October 2026". Whether the live switch is on now is not established by this inventory.

Provider-boundary review ORCH-038 pending. Section 4 therefore carries only the survey's own provider-boundary observations (survey section 5), not a reviewed finding set.

## 1. What exists (survey sections 1, 2, 4)

| Item | Cite |
|---|---|
| Module: second look at weak (hint / unknown / ambiguous) classifications | `document_classification_ai.py`: `plan` (:237), batched `assist.call_task` loop in `run` (:363), `keep` (:318-332), CLI `main` (:440) |
| Output | A new `DocumentClassification` row with `source="ai"`, via `DC.record` (:322); commits per batch (:378, :419) |
| Hook | Classify phase at the end of `document_processing.run` (`document_processing.py:524-540`), gated by `anything_read and classification_ai_on()` (:530) |
| Flags | `classification_ai_on()` = `AI_ENABLED or DOCUMENT_CLASSIFICATION_AI_ENABLED` (`provider.py:1007-1011`); inside `run`, `available()` also requires `DOCUMENT_CLASSIFICATION_V2` (`document_classification_ai.py:151-152`) and the project policy (:155-156). Default off (`config.py:278`) |
| Limits | Batch 12 (`config.py:280`); 100 calls per run (:282, enforced `document_classification_ai.py:380-385`); 240 s per call (`config.py:283`); the daily AI budget (`JobBudget`, :347; `ai/budget.py:92-93`) |
| Tests | `backend/tests/test_document_classification_ai.py`, 3 tests. None for engineer-confirmed rows, blocked projects, the processing hook or the call limit (survey section 6, M6 row; section 5) |

## 2. Design points that match the M6 exit

The M6 section of `docs/UNIFIED_MASTER_ROADMAP.md` asks for "bounded AI where justified", stored extraction first, initial hints kept apart from final content-supported classification, and an exit where "classification changes no approval or engineer-confirmed business state". The survey records these design points; they are design, not measured behavior.

| M6 point | What the survey shows in the pass | Cite |
|---|---|---|
| Bounded AI where justified | Weak-only gating: hint / unknown / ambiguous only (:67, :248); not already `source=="ai"`; path-settled specs and IFC drawings skipped (:259-261); PDF/DOCX with text only (:262-264; `first_page_text` :195-221). Batch, call and budget limits as above | `document_classification_ai.py` |
| Stored beside rules | The AI answer is a row in the same `document_classifications` table with `source="ai"`, so rows are separable from the rules baseline. The rules' answer is kept inside `assessment["rules"]` (:329-330). Model id and `PROMPT_VERSION` (:64) are only inside JSON `assessment["ai"]` (:325-328) | survey sections 2 and 6 |
| Initial hints separate from content-supported answers | The AI row is written with `basis=CONTENT` (:313) | survey section 2 |
| Never confirmed | `plan` skips `engineer_confirmed` rows (:248); `record` stores the automatic row already superseded when the current one is confirmed (`document_classification.py:855-857`); one-current-row unique index (`models.py:558`). Reuse keyed on content hash inside the project (`_earlier_ai` :224-234) | survey section 2, P1 |
| No business-state change | Module docstring (:10-13): never changes roles, states, registers, statuses or engineer-confirmed rows. It does replace the document's current classification row with the AI row (supersede, history kept). Failure handling: an exception rolls back, is logged and sets `counts["classification_ai"]=None`; the processing result is unaffected (`document_processing.py:537-540`) | survey section 4 |

## 3. What the M6 shadow evaluation must measure for this pass

The M6 exit lists: per-type precision and recall, mixed-component recall, system and scope accuracy, false-supported rate and false-OUR_SCOPE rate, plus a declared audit of confidently supported results. For this pass the survey identifies the following. All are **to be measured; none is measured today**.

1. Per-type precision and recall of `source="ai"` rows against engineer-confirmed rows and a labeled sample, compared with the rules answer kept in `assessment["rules"]`. Survey's smallest action: `--dry-run` plus a labeled sample compared with rules and engineer-confirmed rows; `source="ai"` already makes the rows separable.
2. False-supported rate. A single model reading of a first page can set `stage=SUPPORTED`, `strength=MODERATE` (`document_classification_ai.py:294-299`) with `basis=CONTENT` (:313). The roadmap tracks false-supported as an M6 metric and M3 P-10 says no model confidence grants authority. Nothing downstream reads classification today (RC-01), so the survey calls this latent.
3. Mixed-component recall: the pass reads first-page text only (:195-221); whether mixed documents are covered is not established.
4. System and scope accuracy, and false-OUR_SCOPE: no part of the survey addresses attribution states; the pass is not recorded as setting scope.
5. A declared audit sample of confidently supported AI results (the M6 exit requires a declared audit): none exists.
6. Disagreement with confirmed rows: P-02 of the M3 policy contract (`M3-POLICY-CONTRACT-DRAFT.md:34`) is met for this pass by supersede-history, but no conflict record is written when the AI answer disagrees with a confirmed one; the AI row is just stored already superseded (`document_classification.py:856-857`). The evaluation should count these cases.
7. Staleness: reuse ignores `PROMPT_VERSION` and the model, so a prompt change never refreshes old answers (:224-234). The evaluation must state which prompt and model produced each evaluated row; that is recoverable only from the JSON `assessment["ai"]`.
8. Churn and cost: a rules reassessment supersedes the AI row and the next classify run recreates it from the reuse path without a model call (`plan` :266-270, `run` :375-378): churn, not a cost leak. A failed batch is never cached (`assist.py:342-346`), so the same documents are re-sent each run, bounded only by the daily budget.
9. Scope of the pass: `plan` reads the whole project's weak rows (:241-245), not only the documents just read, though the comment at `document_processing.py:524-526` says "for the documents just read". The sample frame must account for this.
10. Coverage: the AI row covers complete answers only; skip reasons exist only as run counts (:372-374), so "not applicable" and "held" documents cannot be sampled from stored data.

## 4. Provider-boundary findings

Provider-boundary review ORCH-038 pending. No review file was available at launch; none is cited. The survey's own observations (survey section 5) are listed so the reviewer can confirm or reject them; they are not findings of this inventory.

- `get_classification_provider` returns `get_provider()` when `AI_ENABLED` is on, the feature flag is off, or a non-Null provider was swapped in (`provider.py:1020-1022`); otherwise it builds and caches a live provider (:1023-1026). The pattern copies the committed `get_review_provider` (:963-978).
- The blocked-project check sits in the feature's `available(project)` (`document_classification_ai.py:155-156`), called at the top of `run` (:367). `assist.call_task` contains no policy check (`assist.py:273-341`). The processing hook tests only the switch (`document_processing.py:530`). No test of the blocked case for classification.
- `set_provider(NullProvider())` is not treated as swapped (`isinstance(_provider, NullProvider)`, :995, :1020), so installing a NullProvider while the flag is on still reaches the live per-feature provider. `conftest.py:25-26` forces both flags false for tests.
- Content sent: first-page text of project documents (:195-221). M3 B-04(a) names document reading among the paths that must honor the project AI policy (`M3-POLICY-CONTRACT-DRAFT.md:211`); the server-boundary enforcement the clause defers to M7/M12 is still absent.
- `ctx` is not passed to `document_classification_ai.run`, so a stop request is not honored (see the M7 inventory).
- The AI result cache key has no project in it (RC-20).

## 5. Not placed under a milestone by the survey beyond M6

The classification-in-processing sequence is carried to M7 in `docs/milestones/M7/M7-INVENTORY-2026-10-07.md`.
