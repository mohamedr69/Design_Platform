# Document classification with the model

Date: 7 October 2026. Code: `backend/app/services/document_classification_ai.py`; the hook at the end of
`document_processing.run`; the switch `classification_ai_on` / `get_classification_provider` in `app/ai/provider.py`.
Tests: `backend/tests/test_document_classification_ai.py`.

## What it does

The classification rules (`document_classification`) answer every document from its path and from what processing
stored. Most answers stay a `hint` (path words only); some are `unknown` or `ambiguous`. This pass sends the first
page's text of those documents, and only those, to the small model, several documents per call, and keeps the answer
as a new classification row with `source = "ai"`:

| Field | From the model |
|---|---|
| `primary_type`, `component_types` | the document's kind, and other kinds bound into the same file |
| `stage`, `evidence_strength` | review-only, never supported: high confidence: hint / moderate; medium: hint / weak; low: hint / weak (ambiguous / conflicting when it names components); UNKNOWN, or OTHER at low confidence: unknown |
| `system_code`, `discipline` | only from the platform's lists; else the rules' |
| `evidence`, `evidence_sources` | "the model read the first page (… confidence): <its reason>", then the rules' lines; `ai_page_text` added |
| `assessment["ai"]` | the verdict as given, the model, the prompt version and the page size (`page_chars`) it came from, whether it was reused |
| `assessment["rules"]` | the rules' answer it stands beside (type, stage, strength, reason) |

The model may not answer DRF or DESIGN_SHEET: those are the project's own documents, named by the intake.
A document of none of the types that the model can still name (a calculation, a company profile, a log) is
OTHER, with the kind first in its reason, and counts as known; UNKNOWN is a document the text does not name.
Earlier answers are reused only when their prompt version is in `COMPATIBLE_PROMPT_VERSIONS` (an explicit list; a
version left out is asked again), and a reused answer keeps the model, prompt version and page size it came from.
The provenance (`assessment["ai"]`, `["rules"]`) is written in the row's one insert (`record(..., extra=...)`), so
a failure afterwards cannot leave an AI row without it.

Nothing else changes: no role, state, record, register or status. An engineer's confirmed answer is never replaced.

## What is sent, and what is not

Sent: a document whose current answer is `hint`, `unknown` or `ambiguous`, read and `fresh`, a PDF or a Word file with
text on its first page. Not sent: supported answers; hints the folder settles (specifications, drawings in an IFC
folder); files waiting to be read; answers made under earlier rules (re-assess first: the free backfill); other file
types; pages with no text layer.

Each call carries: the task's instructions once, then per document its path, the rules' guess and at most
`DOCUMENT_CLASSIFICATION_AI_PAGE_CHARS` characters of the first page (the second page's too when the first says
little). No images.

## Keeping the cost down

* Batches of `DOCUMENT_CLASSIFICATION_AI_BATCH` documents a call (24): the instructions and the route's own overhead
  are paid once per batch.
* The same content is sent once: files with the same content hash take the answer of the one sent.
* Never twice: an earlier AI answer for the same content in the project is reused, including after new rules
  supersede it.
* Through the platform's cache, daily AI budget and usage log (`ai_usage`, task `document_classification`); at most
  `DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_RUN` calls a run (100).
* Its own daily cap: at most `DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_PROJECT_PER_DAY` calls (25) of this task per
  project over a rolling 24 hours, checked before each batch, inside the platform's `AI_MAX_CALLS_PER_PROJECT_PER_DAY`
  (150, shared by every AI task). Cache hits do not count.
* A stop asked for on the processing job is honoured between batches: the job's context is handed to the pass.
* Each row it writes also fills the M6 stage-record slots (`model`, `prompt_version`, `page_chars`, `producing_job_id`
  through `record(stage_record=...)`), so a conflict with an engineer's confirmation carries the prompt version
  (DOCUMENT_CLASSIFICATION_V2.md, section E).
* After documents are processed, the pass runs for that project by itself; only new or changed documents cost.

## Running it

    venv\Scripts\python -m app.services.document_classification_ai --dry-run             # what would be sent, and its tokens
    venv\Scripts\python -m app.services.document_classification_ai --project 30784       # one project
    venv\Scripts\python -m app.services.document_classification_ai                      # every project

## Switches

| Setting | Default | Meaning |
|---|---|---|
| `DOCUMENT_CLASSIFICATION_AI_ENABLED` | off | the pass alone, `AI_ENABLED` staying off; on in the live installation since 7 October 2026 |
| `DOCUMENT_CLASSIFICATION_AI_MODEL` | the small tier | a model for it alone |
| `DOCUMENT_CLASSIFICATION_AI_BATCH` | 24 | documents per call (the Claude Code route spends about 35,000 tokens a call before any document) |
| `DOCUMENT_CLASSIFICATION_AI_PAGE_CHARS` | 2500 | first-page text per document |
| `DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_RUN` | 100 | calls per run and project |
| `DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_PROJECT_PER_DAY` | 25 | the pass's own calls per project a rolling day, apart from the platform's cap |
| `DOCUMENT_CLASSIFICATION_AI_TIMEOUT_S` / `_MAX_OUTPUT_TOKENS` | 240 / 5000 | one call's limits |

`DOCUMENT_CLASSIFICATION_V2` must be on as well. A project whose AI policy is "blocked" is never sent.

## Pilot conditions (owner, 8 October 2026; A-15 item 1, ORCH-047)

The live pass is an owner-authorised pilot ahead of M6, on two conditions:

1. **A separate daily cap** for the classification pass: `DOCUMENT_CLASSIFICATION_AI_MAX_CALLS_PER_PROJECT_PER_DAY`
   (default 25), counted on the `document_classification` task alone and checked before each batch; the platform's
   150-a-day cap still applies to all tasks together.
2. **Review-only answers.** A model reading alone never makes an answer `supported`: the most it reaches is `hint`
   with `moderate` strength, and every `source = "ai"` row is flagged for review ("answered by the model, not
   confirmed: a person confirms it") until an engineer confirms it. `supported` requires the rules' content
   reading or an engineer's confirmation.

Rows the pass wrote before this change (7 October) keep the stage they were stored with until they are answered
again; they are flagged for review like every AI row. Changing their stored stage is a database change and is
left to the owner.

## First run (7 October 2026)

Pilot on EP-30784 Skyblade: 85 files sent in 8 calls of 12, all answered; supported answers 257 to 356, ambiguous 22
to 0, hint 102 to 23. Measured usage: 215,645 input tokens (62,142 of them cached) and 11,495 output tokens --
three times the first estimate, because the Claude Code route spends about 18,000 tokens a call before any
document; hence batches of 24 and the estimate's measured overhead. Prompt version 2 followed: 20 calculations had
been named DESIGN_SHEET.

Run on every project (7 October 2026, prompt 2, batches of 24): 41 calls, none failed; 1,904,102 input tokens
(330,598 cached) and 97,955 output tokens, against an estimate of 1.24 million input: the route's overhead per call
measured about 35,000 tokens, now the estimate's constant. Across all projects 1,128 documents carry the model's
answer; current answers: supported 1,829, hint 1,470, unknown 80, ambiguous 1. Most remaining hints are settled by
their folder (specifications, IFC) and were never sent; IVY Garden 2 has 307 files still waiting to be read.

