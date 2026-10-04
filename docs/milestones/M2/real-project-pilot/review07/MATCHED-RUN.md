# M2 Review 07: small matched run on the frozen candidate (R7-05)

**Scope.** This is exposed exploration data, not sealed and not a generalization claim. It is too small to choose a variant. It shows the repaired paths working end to end on real pages, and gives a first like-for-like comparison.

## Setup, declared before any call

| Item | Value |
|---|---|
| Declaration | `matched/MATCHED-DECLARATION.json`, SHA-256 `449afc7e…` |
| Authorization | `matched/SANDBOX-AUTHORIZATION.json`, SHA-256 `527c353d…`: the **recorded** live `ai_policy` (read only). No new owner reply was received, so nothing beyond the recorded policies is assumed. Authorized for this run: 29076, 30088 and 30784. 30880 is allowed but has no labels; every other project has no policy and was not sent. No live policy or registration was changed. |
| Code | the frozen `c9a1a14` application, run from the worktree `C:/t/iso/frozen-r7` (no `.env`); runners `matched/run_r7f.py` and `run_evf.py` |
| Sources | 12 labelled PDFs, 4 per authorized project, drawn by the seed `m2-review07-matched-2026-09-29` from the sorted lists (truth and predictions not consulted). Staged copies; SHA-256 in the declaration. |
| Tracks | **AI-EV0**: sync plus processing with the application's AI path (the submittal-form reader), evidence stage off. **AI-EV1** and **AI-EV2**: the evidence stage (policy `.2`) on a WAL-consistent snapshot of the EV0 database. Same bytes, default profile. |
| Model-disabled baseline | `det9` (parse `.9`, the same application code), restricted to the same 12 documents |
| Ledger | one scope for all tracks: requests 120, per-request input 70,000 and output 20,000, aggregate input 3,000,000 and output 400,000, 3 h |

## Usage, from the ledger

| | Value |
|---|---|
| Requests | **120 of 120**, all `ok`. 1 further request was **refused** at the cap. |
| By track | EV0 2 (`read_submittal_form`); EV1 64; EV2 54 (6 escalations to the standard tier) |
| Models returned | `claude-sonnet-5` ×114, `claude-opus-5` ×6 |
| Tokens | input 1,245,351 actual against 2,768,047 reserved; output 172,441 |
| Estimates | 1 request's actual input exceeded its estimate. No per-request or aggregate cap was breached, so the breaker stayed closed. |
| Usage unknown | 0 |
| Model latency | 2,387 s total. Wall time: EV1 1,286 s, EV2 1,099 s. |
| Cost | **unknown**: no prices are configured, and that is not zero |

**Coverage.** EV2 is **partial**:
- 3 page attempts were refused by the ledger at 120/120, and 2 stopped at the per-document call limit;
- EV1 had 1 per-document stop;
- every stop is recorded as a budget stop, never as a negative.

## Accuracy

Evaluator `.6`, evidence layer; labels Golden v1 with the v2 page labels.

| Run | Identity | Revision | Decision | Register critical | Accepted AI errors reported |
|---|---|---|---|---|---|
| model-disabled (`det9`) | 14/16 clean, prec 14/15 | 13/16, prec 13/14 | 6/9 clean (+7 tn) | 0 | — |
| AI-EV0 | identical to model-disabled | identical | identical | 0 | — |
| **AI-EV1** | 14/16 (+1 held) | 13/16 (+2 held) | **7/9** (+2 held) | 0 | 2 (see below) |
| **AI-EV2** (partial) | 14/16 (+1 held) | 13/16 (+2 held) | 6/9 (+2 held) | 0 | 1 (see below) |

- **Adjudication.** Every "AI error" reported here is on one page, `EP-30784/03- MS/03- FRC/03- TIANJIE/BBY006_1.PDF` page 3. The page prints `EP-30627/SS/EML/ 1293` and Revision `00`. The labels mark it a no-record page (ADJUDICATIONS #9, `label_gap_unlabelled_own`). The model-disabled baseline's one false-positive identity and one false-positive revision are the same page. **So there is no confirmed AI false acceptance in the matched run**, and the page is in the human-review packet.
- **Records untouched.** The register mirror columns are identical between EV0 and each of EV1 and EV2.
- **Gains.** EV1 adds one clean decision recovery and three held-evidence recoveries (identity and revision) for 64 requests. EV2, with 54 requests and partial coverage, adds the held evidence and no clean recovery.

## Reading

- On this sample, targeted verification (EV1) adds a decision and some held evidence at no confirmed error cost. Broad verification (EV2) adds nothing automatic, although it had less budget and partial coverage.
- Per the policy, additional calls alone are not improvement. A 12-document sample, with 9 readable decisions, cannot select a variant. **No variant is adopted.** The Review 06 exploration and this run both point the same way; neither settles it.
- The objective stays unmet on this sample:
  - clean identity recovery is 87.5%, revision 81.3% and decision 66.7–77.8%, all below 90%;
  - identity precision is 93.3%, below 98%, because of the label gap.
