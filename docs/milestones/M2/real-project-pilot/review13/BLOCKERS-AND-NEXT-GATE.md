# Round 2 exploration: remaining blockers and the next gate (deliverable 7)

**M2 is not accepted by this round, and nothing here asks for it.** No variant is selected, because truth is unconfirmed. The sealed cohort stays sealed. M3, production, live backfill and sealed validation are not authorized by this task and were not started.

## 1. Blockers

| ID | Blocker | Where it stands after this round | What closes it |
|---|---|---|---|
| **H-1** | **No human truth.** Reviewer appointment and sign-off are pending (OWNER-AI-PERMISSION-ROUND2.md). Every exploration label is an AI proposal. | The worklist ([HUMAN-REVIEW-WORKLIST.md](worklist/HUMAN-REVIEW-WORKLIST.md)) links packet v2 unchanged. It adds crops for all 13 source findings (23 items), the 4 H-06 rows, the small batch's 7 unresolved items, every critical false accept and the seeded independent 20 % sample. **No answer is filled in.** | A named person fills the answers. Only then can any figure in [METRICS.md](METRICS.md) become accuracy evidence. |
| **B-1** | **Recovery.** | On the exposed runs, missed discovery dominates (DEFECT-INVENTORY.md). On the small batch, the AI stage **holds** correct identities and revisions but seldom **accepts** them: held ≠ recovered (METRICS.md). | Reviewed truth, then the targeted page-1 identity change (DEFECT-INVENTORY.md §3) with regression tests and a new freeze. Then a re-run of A/B/C. |
| **B-2** | **Identity precision.** | Critical accepts under provisional truth: **B 3, C 2**. B accepted `Rev.0` as an identity (EP-17428 p4), wrong however the labels settle. C accepted the letterhead code `P06/TRANS/R1` as an identity; that is wrong if the proposed label is confirmed. The other three depend on label conventions a person must settle. | Refuse, as an identity, a value that is a revision literal (`Rev.`) or a repeated letterhead / form code. These are targeted validation rules, to be written after review and tested on these cases. The exposed F01, F07, F10, F12 and F13 decisions must also be settled. |
| **B-5** | **Variant selection.** | The small batch has 8 identity, 5 revision and **0 decision** components with truth. That is far too small, and it has no decisions. | The remaining exploration batch within the daily limits (§3), scored on reviewed truth. |
| **B-6** | **H-06 BOQ.** | EV2 caught all three H-06 rows (the blind read `1` against the accepted `4`) and validated no wrong row. EV1 caught only the rows its 20 % audit selected. Both raise a conflict; neither corrects the row. EV2 used EP-8430's whole day limit (35 + 25 requests) and left 3 held rows unread. | A person confirms the quantity. Then a policy decision on whether an accepted BOQ row must be verified before it counts, given its cost of about one request per row. |
| **R2-S** | **Exploration shortfall.** 415 of 450 distinct documents (35 short, all in small projects taken in full). | Reported, not filled. The sealed cohort is not touched. | Accept the shortfall, or have the owner add eligible **new** exposed / exploration material. The sealed projects can never fill it. |
| **R2-L** | **Labels cover 12 of 415 documents.** The BOQ set (39 name candidates) is unclassified. | The small batch only. | Label the remaining exploration documents and BOQ candidates before their batches run, in the same format, before any prediction. |
| **R2-C** | **Counting defect in the frozen selection's file counts** (long paths). | Documented. Membership is unaffected. | A correction note in the Round 2 plan (the owner's decision); no re-selection. |

## 2. What this round established that the next round relies on

- The frozen, reproducible file-level manifest, and the small batch.
- The run declaration format with its addendum discipline.
- The application limits unchanged, with the 60-per-project-per-day limit applied **across** tracks.
- Ledger accounting that reconciles with the application's usage table (METRICS.md §4).
- The evaluator run under declared contexts, with controls.
- Profile A (the application's AI path) makes **no** requests on documents that are not submittal forms. On such documents, A equals the deterministic track.

## 3. The next gate (not started)

1. **Human review** of the worklist's mandatory items and the independent sample, by a named person.
2. **Labels** for the remaining 403 exploration documents, in batches, each before its predictions. The label hashes go into each batch's declaration.
3. **The remaining batch**, under a new declaration or addendum:
   - its own ledger scope in the same ledger file;
   - the same unchanged application limits;
   - the cross-track 60 per project per day.

   **What this means for the schedule.** A/B/C over ~400 documents at the observed rate (B about 2, C about 4 requests per document) needs about **2,400 requests**. With 10 projects × 60 per day, that is at least **4–5 days**. Projects with many documents take longer, because each project's day limit binds separately.
4. **Only after the above:** the targeted changes (the page-1 identity read, and refusing revision literals as identities), their regression tests, a new freeze, and a re-run.
5. **Sealed readiness:** the sealed cohort can be opened only after:
   - the candidate is frozen;
   - its baseline comparison is predeclared;
   - human-reviewed labels exist for it, made before any prediction.

   None of these is met now. **Sealed validation is not ready.**
