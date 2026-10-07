# M7 inventory: the classify phase added to document processing (7 October 2026)

Unified milestone: M7 (Central Processing, Relationships and Domain Records). Task: ORCH-037 (ep-scribe). Worktree `G:/dev (2)/dev/ep-platform-merged/roadmap-u2`, branch `roadmap/u2`, HEAD at start `573780a561fac560b5e5b5344c227f348eb65fb2`.

## Status

**Implemented / partial, not accepted; not M7 evidence.** The change is uncommitted in the live clone `G:/dev (2)/dev/ep-platform-merged/ep-platform` (branch `claude/upbeat-lovelace-sa9j3w`, HEAD 7a1bf6f) at 2026-10-07. Source: `MR/orchestrator/surveys/U2-DELTA-DRAWINGS-PROCESSING-2026-10-07.md` (the survey), snapshot 22:13:40 local; file sha256 per the survey: `document_classification_ai.py` ca9933373b1e. The sha256 of `document_processing.py` is not recorded in the survey. Nothing was run by the scribe.
The survey's own recommendation (section 6, M7 row): treat the pass as the **pilot consumer for the M7 stage record**; add its attributes to the M7 design list; do not count it as M7 evidence.

## 1. The sequence change (survey section 4)

- Where: after the drawings reconcile and its telemetry (`document_processing.py:516-523`), before `forms_changed`, `remaining` and `finished_at` (:541-543). It is the last stage of `run`, after reading, AI reading (`phase="ai"`, :450), register reconcile and shop-drawing reconcile. Sequence now: read, AI read, register reconcile, shop-drawing reconcile, **classify**.
- Trigger: `anything_read and classification_ai_on()` (:530). `anything_read` is set when a file was read in this run (:278, :422); a run that only marks stale or missing never classifies.
- Flag: `AI_ENABLED or DOCUMENT_CLASSIFICATION_AI_ENABLED` (`provider.py:1007-1011`); inside `run`, also `DOCUMENT_CLASSIFICATION_V2` (`document_classification_ai.py:151-152`) and the project policy (:155-156). Default off (`config.py:278`).
- Progress: `ctx.progress(..., phase="classify")` (`document_processing.py:532`). `ctx` is **not** passed to `document_classification_ai.run` (:536 versus `run(..., ctx=None)` at `document_classification_ai.py:363`): a stop request is not honored during the pass and no per-batch progress is shown.
- Call limit: 100 calls per run (`config.py:282`, enforced `document_classification_ai.py:380-385`), batch 12 (`config.py:280`), 240 s per call (:283). Worst case inside one processing job: 100 calls x 240 s. The daily AI budget also applies (`JobBudget`, `document_classification_ai.py:347`; `ai/budget.py:92-93`).
- Dedup: per content hash within a run (`by_sha`, :246, :271-273; followers receive the same verdict, :416-418) and across runs by `_earlier_ai` (:224-234, project-scoped).
- Failure handling: a failed batch is counted and the loop continues unless the budget tripped (:403-409). Any exception escapes to `document_processing.py:537-540`, which rolls back, logs and sets `counts["classification_ai"]=None`; the processing result is unaffected. A failed batch is not remembered (`invalid_output` is never cached, `assist.py:342-346`), so the same documents are re-sent on the next run, bounded only by the daily budget.
- Unchanged by the stage: roles, states, registers, statuses and engineer-confirmed rows (module docstring :10-13).

## 2. Mapping to the roadmap section 5 registry stages

Section 5 (shared processing registry and artifacts, owned by M7) requires, per project/document version, the elements below. Stage affected: capability "classification".

| Registry element (section 5) | What exists for the classify stage | What is missing (survey section 4 table) |
|---|---|---|
| Capability / stage | A stage row in `document_classifications` (rules, now AI, distinguished by the `source` column) | No capability or stage registry; the five stores remain (roadmap section 3, RC-36) |
| Immutable content hash and source identity | `content_sha256` (`models.py:565`) | None stated |
| Version / fingerprint (reader, parser, schema, profile, rules, config fingerprint, dependencies) | `rules_version` (the RULES version, `document_classification.py:93`, :847-853) and `context_fingerprint` | Model id and `PROMPT_VERSION` only in JSON (`document_classification_ai.py:325-328`); no schema or config fingerprint; a prompt change does not stale old answers |
| Status (pending, running, complete, partial, failed, cancelled, stale, not applicable; coverage, held items, reasons) | A row exists only for a complete answer | Skip reasons exist only as run counts (:372-374) and the job result (`document_processing.py:536`), never per document; no failed, not-applicable or held record |
| Artifact ids, producing job, timestamps, last-good | Superseded rows are history; `created_at` | Producing job id is not stored on the row |
| Idempotency key per stage and input fingerprint; concurrent-job dedup | Content-hash reuse; the AI cache key (`assist.py:284-291`) and its in-flight guard (:301) | No per-stage key; two jobs for one project can compute the same `plan` |
| Project-scoped by default (section 5) | `_earlier_ai` filters by project (:205) | The shared `AiResultCache` is not project-keyed (RC-20) |

Further M7 items the survey records for this stage:

| Item | Cite | Gap |
|---|---|---|
| Cancellation | `ctx` not threaded (`document_processing.py:536`; `document_classification_ai.py:363`) | no stop, no per-batch progress |
| Time bound | 100 calls x 240 s worst case in one job | no per-stage deadline |
| Project AI policy at every provider boundary (M7 obligation from M3) | Met by caller gate in each feature's `available()`; the processing hook tests only the switch (`document_processing.py:530`) | Not enforced at the boundary (`assist.call_task`, `assist.py:273-341`, has no policy check) |
| Whole-project plan | `plan` reads the whole project's weak rows (:241-245), though the comment at `document_processing.py:524-526` says "for the documents just read" | The stage input fingerprint would need the exact document set |
| Retry of failed work | Failed batches re-sent each run, bounded by the daily budget | No failed-state record to hold retry |

## 3. Other M7-relevant stores introduced by the same change (survey section 2)

These are recorded in `docs/milestones/M1/M1-DELTA-ADDENDUM-2026-10-07.md`; M7 is where their owner is to be decided, "owner decision pending (M7)":

- Sheet numbers in `ProjectIfcDrawing.meta["sheets"]` with no version for the number-reading logic (survey P4).
- Folder-import staging and job (P7); the reader does not use the job's `folder_path` (P5).
- `ProjectChange` written at IFC read (P6), ephemeral (RC-17).

## 4. What is proven and not proven (survey section 6, M7 row)

Proven by the survey, as design observation only: content-hash idempotence inside a project; failures do not fail processing.
Not proven: the registry contract. This pass does not count as M7 evidence.
