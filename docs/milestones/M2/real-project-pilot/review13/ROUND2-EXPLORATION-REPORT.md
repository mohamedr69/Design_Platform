# M2 Round 2 exploration and human-truth preparation: report (index)

**Task.** "Resume M2 accuracy work — Round 2 exploration and human-truth preparation" (`reviews/M2-review-13/M2-NEXT-CLAUDE-INSTRUCTIONS.md`), on the candidate `3d5607d` accepted in Review 13.

**Where the work ran.** In the isolated scratch area only: `C:/t/iso`, `C:/t/r2x`.

**What was not touched.**
- No live code, services, settings or data.
- No commit or push to the owner's repository.
- No sealed content was opened.
- No candidate change.
- M3, production, live backfill and sealed validation were not started.

**This folder is a new package.** `review05`–`review12` and `human-review-packet-v2` are unchanged.

## Deliverables

| # | Deliverable | Where |
|---|---|---|
| 1 | The reviewed baseline's identity, and the file-level manifest | [BASELINE-AND-MANIFEST.md](BASELINE-AND-MANIFEST.md); `evidence/manifest/` |
| 2 | The defect inventory, and the change / diff explanation (no change was made, and why) | [DEFECT-INVENTORY.md](DEFECT-INVENTORY.md); `evidence/failure-inventory/` |
| 3 | The human-review worklist (packet v2 linked unchanged, with crops for all 13 findings, H-06, the unresolved labels, the critical accepts and the 20 % sample), plus the proposal labels | [worklist/HUMAN-REVIEW-WORKLIST.md](worklist/HUMAN-REVIEW-WORKLIST.md); `evidence/labels/` |
| 4 | The frozen experiment declaration, raw outputs, and the usage / failure ledger | [EXPERIMENT-AND-LEDGER.md](EXPERIMENT-AND-LEDGER.md); `evidence/run/` |
| 5 | Per-profile metrics, with truth status | [METRICS.md](METRICS.md); `evidence/eval/` |
| 6 | Regression evidence and manifests | [REGRESSION.md](REGRESSION.md); `evidence/regression/`; `evidence/EVIDENCE-MANIFEST.json` |
| 7 | The remaining blockers and the next gate | [BLOCKERS-AND-NEXT-GATE.md](BLOCKERS-AND-NEXT-GATE.md) |

## In short

- **Selection and staging (exploration projects only).**
  - Frozen selection `4e8190d0…` → staged manifest `ee9df7b5…`: **415 distinct documents against 450**. That is 35 short, all in small projects taken in full. It is not filled from anywhere else.
  - 42 duplicates were recorded (1 of them an exposed file); 0 were unreadable.
  - The frozen selection's file counts undercount long paths. This is a reporting defect; membership is unaffected.
- **Labels.**
  - The small batch (12 documents) was labelled from the source **before any prediction**, in a page-labels-v2-compatible format with identity roles and states. Hash `d21a83fd…`.
  - These are **AI proposals**. No reviewer exists yet, and no sign-off is claimed.
  - The remaining 403 documents and the 39 BOQ candidates are **not labelled yet**.
- **Real-model A/B/C** on the small batch, under the declaration `c146e575…`:
  - The application limits were **unchanged**, and the per-project daily limit was applied across tracks.
  - The Round 2 ledger scope was the request cap. The exhausted `r7-matched` scope was not touched.
  - **113 requests** (sonnet-5 ×108, opus-5 ×5). Reconciled with the application's usage table. 0 failures. **Cost unknown.**
- **Results (provisional truth only).**
  - Profile A made **no** requests: the application AI path reads only submittal forms.
  - B and C **held** 3 correct identities that the deterministic track missed. Neither accepted them, so recovery stays 4/8 for identity and 1/5 for revision.
  - They accepted **3 (B) and 2 (C) critical values** on pages the proposed labels call no-record. Among them is `Rev.0` accepted as an identity by B, which is a genuine error.
  - On H-06, **EV2 caught all three wrong accepted quantities** and validated no wrong row. EV1 caught only the rows its audit sampled.
- **No variant is selected.** Truth is unconfirmed.
- **Regression.** No candidate change was made. The reviewer's 188-test set plus the Review 12 module on `3d5607d`: **199 passed, exit code 0.**

## What is missing (stated exactly)

- **A named human reviewer, and filled answers.** Nothing in this package is human truth.
- **Labels for the remaining 403 exploration documents and the BOQ candidates**, before their batches run.
- **Calendar time for the remaining batch.** About 2,400 requests at the unchanged 60 per project per day means at least 4–5 days.
- **The owner's decision on the 35-document shortfall.** It cannot be filled from the sealed cohort.
