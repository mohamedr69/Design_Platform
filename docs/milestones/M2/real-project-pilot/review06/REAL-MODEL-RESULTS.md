# M2 Review 06: AI variants with the real model (exploration, exposed data)

**What these results are.**
- Real calls through the existing `claude-code` provider, in isolated sandboxes.
- **Not** mocked. The mocked contract tests are listed separately at the end.
- **Not** sealed, and **not** a generalization claim: every project used is exposed Round 1 pilot data.
- Cost is **unknown**: no pricing is configured. Unknown is not zero.

## Declaration, made before any call

| Item | Value |
|---|---|
| `realmodel/EXPERIMENT-DECLARATION.json` | SHA-256 `522abfe9…`, declared 2026-09-28T23:2x, before the first real call |
| Addendum 1 (`935b0da2…`) | BOQ-variant caps, declared before any BOQ-variant call |
| Addendum 2 (`109c2dc5…`) | AI-EV2 limited to EP-29076, and its per-project daily limit set to its run cap. Declared before any EV2 call, when only EV1 call counts and timings had been seen, no EV1 score. |
| Smoke call | one synthetic page with no client data (`realmodel/SMOKE.txt`): `claude-sonnet-5`, correct |
| Addendum 3 (`73b2bfad…`) | BOQ verifier `.2` track (AI-EV1b-BOQ), cap 60; declared after the `.1` verifier defects were found and before any `.2` call |
| **Requests used** | **690 of the declared 700**: EV0 documents 8, EV1 200, EV2 221, BOQ application EV0 41, BOQ EV1 67, BOQ EV2 99 (stopped), BOQ EV1b 54 |

- **Tree:** the isolated candidate (the declaration records the SHA-256 of every changed file). Deterministic base: `parse-2026-09-28.7`; the EV0 sandbox was made before `.8`.
- **Prompts, schema and policy:** `evidence-reader-2026-09-29.1`, `evidence-policy-2026-09-29.1`, the prompts `discover/read-*-2026-09-29.1`, and the existing `submittal-2026-09-17.1` / `read-sheet-2026-09-16.1`.
- **Provider:** `claude-code` (CLI 2.1.263). Configured aliases: small `sonnet`, standard `opus`. **Models returned:** `claude-sonnet-5` and `claude-opus-5`.
- **Project AI policies,** read from the live database without writing: 30784, 30880, 29076 and 30088 are `allowed`. **Only three projects with labels were eligible: EP-29076, EP-30088 and EP-30784.** None of the other pilot projects, and none of the four holdout projects, is registered in the application, so none has a recorded policy. They were **not sent to a model**. This is an evidence gap, and it covers exactly the H-03 decisions and the H-06 BOQ.
- **Budgets:**
  - EV0 used the application's own limits (150 calls per project per day, 12 per document job, 120 s).
  - EV1 and EV2: 8 calls per document, 300 s per document, at most 4 pages per document, at most 2 escalations per document. Run caps: EV1 200, EV2 300, total 700.
  - Concurrency 1. Time cap 6 h.
- **Stop conditions:**
  - an auth or refused outcome, or 5 consecutive transport failures, stops the track;
  - a cap records the remaining work as not run;
  - a sandbox assertion aborts the run before any call.

  None of these fired, apart from the caps.

## Matrix actually run

| Variant | What | Scope | Profile |
|---|---|---|---|
| model-disabled | the candidate with `AI_ENABLED=false` | 3 eligible projects | default |
| **AI-EV0-baseline** | the application's AI path as it is (submittal-form reader); evidence reader off | 3 eligible projects, 137 documents | default |
| **AI-EV1-targeted** | EV0 state (WAL-consistent snapshot) plus the evidence stage EV1: triggers and the frozen 20% audit | EP-29076 complete (53 documents); EP-30088 partial (13 documents) when the **200-call cap** stopped it; EP-30784 **not run** | default |
| **AI-EV2-broad** | EV0 state plus the evidence stage EV2: every page with a critical fact, escalation to `opus` | EP-29076 complete (53 documents) | default |

**Not run:**
- the promoted profile with a model;
- any non-eligible project;
- EV2 on EP-30088 and EP-30784 (time cap);
- sealed data.

## Usage

These are application requests. Provider-internal turns and retries are not visible to the application.

| Variant | Requests | Models returned | Escalated | Failed | Model time | Input tokens (of which cached) | Output tokens | p50 / p90 latency | Cost |
|---|---|---|---|---|---|---|---|---|---|
| AI-EV0 | 8 (`read_submittal_form`) | sonnet-5 × 8 | 0 | 0 | 178 s | 125,996 (54,824) | 12,933 | 20.8 s / 24.0 s | unknown |
| AI-EV1 | 200 (discover 81, identity 58, revision 34, decision 27) | sonnet-5 × 200 | 0 | 0 | 5,397 s | 2,710,060 (1,700,154) | 426,477 | 10.4 s / 70.3 s | unknown |
| AI-EV2 | 221 (discover 66, identity 91, revision 48, decision 16) | sonnet-5 × 165, opus-5 × 56 | 56 | 0 | 4,894 s | 2,535,690 (1,624,779) | 364,387 | 10.2 s / 53.6 s | unknown |

- **Wall time:** EV0 1,547 s for 3 projects (including the deterministic reading). EV1 on EP-29076 took 3,695 s; EV2 on EP-29076 took 4,948 s.
- **Cache hits:** within a run only, where the same content appears under two paths. EV1 had 7; EV2 had 0 on EP-29076. No answer is shared across variants, because the variant is part of the key.

**D-R6-D (budget-control gap).** Discovery requests used 16–30k input tokens against the declared per-task cap of 6,000. The application's `JobBudget` checks the *reservation estimate* (4,000), not the actual count. The declared cap was therefore not enforced on actual usage. Call, time and escalation caps did hold.

## Accuracy

Scoring uses the frozen evaluator .4 with labels v1 and the v2 page labels, restricted to the scored projects. The evidence layer is the raw layer plus the `ai_evidence` observations:
- `validated` counts as accepted, and is wrong or critical like any other value;
- `candidate` and `conflict` count as held.

Cells show recovered / readable.

### EP-29076: all variants complete, 53 documents

| Run | Critical | Register reference | Register decision | Evidence identity | Evidence revision | Evidence decision | Held | Introduced errors | Review items |
|---|---|---|---|---|---|---|---|---|---|
| model-disabled (`.7`) | 4 | 21/29 (4 wrong) | 0/8 | 29/53 | 15/48 | 0/8 | 0 | — | — |
| **AI-EV0** | **5** | 21/29 (**5 wrong**) | 1/8 | 29/53 | 15/48 | 1/8 | 0 | — | — |
| **AI-EV1** | 5 (register unchanged) | 21/29 | 1/8 | **32/53** | **17/48** | 1/8 | 3 | **0** | 52 |
| **AI-EV2** | 5 (register unchanged) | 21/29 | 1/8 | 31/53 | 16/48 | **2/8** | 4 | **0** | 73 |

Review items are candidate plus conflict observations.

### Eligible projects combined

EP-29076, EP-30088 and EP-30784; EV1 is partial as noted above.

| Run | Critical | Evidence identity | Evidence revision | Evidence decision | Introduced errors |
|---|---|---|---|---|---|
| model-disabled | 5 | 93/142 | 68/120 | 28/43 | — |
| AI-EV0 | 6 | 93/142 | 68/120 | 29/43 | — |
| AI-EV1 | 6 (register unchanged) | **100/142** | **70/120** | **30/43** | **0** |

### Findings

1. **The existing application AI path (AI-EV0) introduced a critical false acceptance.**
   - **Document:** `EP-29076 FA MS & Sam B CBS Ack 14.05.26.pdf`.
   - **What happened:** the submittal-form reader keyed the register row under a listed submittal, `25H-S202-NCC-MAS-MEP-ELE-005-R3`.
   - **Truth:** the page's own identity is transmittal `TR/0127/26`.
   - **What EV1 did:** its blind discovery reported that page's identity as `TR/0127/26` and held it as a `conflict` against the register key. It did not override it.
2. **The evidence stage never changed a record.** The register mirror columns (reference, revision, status, system) are **identical** between EV0 and each of EV1 and EV2, across all 137 documents.
3. **Zero introduced errors.** No `validated` AI value is wrong against the labels, in either variant.
4. **The gain is real but small.**
   - EV1 on EP-29076: identity +3, revision +2, decision +0, for 134 requests.
   - EV2: identity +2, revision +1, decision +1, for 221 requests including 56 `opus` escalations, with more review items (73 against 52).

   **Broader verification did not pay for itself on this project.** The policy's rule applies: additional calls alone are not improvement.
5. **Why the recovery is limited.** Most AI identity readings end as `conflict` (EV1 30, EV2 36 on EP-29076). The typical case is a consultant reply that carries the contractor's drawing number and the consultant's own reference. The policy rightly refuses to pick one. Resolving these needs a component-role rule, not more calls. That is an exploration finding for the next policy version, and it is not tuned here.
6. **Decision noise.** A compliance statement's "Comply" is read as an unmapped option, giving a `conflict` (held). This is safe, but it adds to the review burden.

### Against the objectives

Targets: zero critical false accepts, at least 90% recovery, at least 98% precision on other fields.

- **Not met by any variant.** AI-EV1 moves evidence recovery a few points and introduces no error.
- The register layer keeps its critical errors. They come from the deterministic reader and from the **AS-IS** AI path, and the evidence layer does not feed the register.
- No variant is promoted (PROMOTION-ROLLBACK).

## Mocked contract tests

These are separate from the real-model results: `tests/test_evidence_reader.py`, 19 tests with a scripted provider. They cover:
- off makes no call;
- the frozen audit;
- triggers on pages with no record;
- **blind reads never carry a proposed value**;
- records untouched;
- the validation states;
- the decision policy;
- no repeated call, and variant cache isolation;
- failure is not a negative, and nothing is cached from a failure;
- budget stops recorded;
- unknown price is not zero;
- the BOQ row policy and its selection;
- blind BOQ rows;
- the stage off by default, writing only its own key;
- no GET handler reaching the stage.
