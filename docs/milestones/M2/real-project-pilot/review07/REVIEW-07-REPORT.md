# M2 Review 07: correction package

**Verdict: CHANGES STILL REQUIRED.**

- The Review 07 corrections (R7-01 to R7-05, section E) are implemented, frozen and tested. They are ready for an independent re-review of those corrections.
- M2 itself stays **not accepted**. The acceptance targets are not met, and the truth that would measure them still needs a human reviewer.
- Nothing is promoted, committed to the owner's repository or pushed, and M3 is not started.

## Boundaries kept

| Item | Status |
|---|---|
| Owner's tree | Not modified in code: HEAD `2221b43` plus the uncommitted Candidate C, with its 11 frozen hashes still matching. The only additions are documents under `docs/`. |
| Live services, `.env`, symbol library, OneDrive originals | Not touched |
| Live database | Read only, twice: the recorded AI policies, and the uncertain-reference case list |
| Where the work happened | the isolated scratch repository `C:/t/iso/ep-platform` (never served) and the sandboxes `C:/t/r6` and `C:/t/r7` |
| Round 2 | The 34-project selection and the **10 sealed projects stay sealed**: not staged, not read |
| Real-model use | Within the **recorded** project policies only (29076, 30088, 30784). No owner reply was received, and an unanswered question is not taken as approval. |

## Package

| Document | Contents |
|---|---|
| [DISPOSITIONS.md](DISPOSITIONS.md) | R7-01 to R7-05, section E, G, and the carried B-items |
| [EVALUATOR.md](EVALUATOR.md) | Evaluator `.5`/`.6`: rules, 13 tests including the reviewer's probes, and every stored output re-scored under `.6` |
| [ADJUDICATIONS.md](ADJUDICATIONS.md) | Source adjudication of every changed critical finding (13 cases), with crops |
| [VALIDATOR-AND-LIFECYCLE.md](VALIDATOR-AND-LIFECYCLE.md) | Policy `.2`, the reviewer's probes against the pinned `.1` reader, the replay of the stored readings, the evidence lifecycle and profile binding |
| [BUDGET-LEDGER.md](BUDGET-LEDGER.md) | The shared ledger: what is enforced hard and what is an estimate plus breaker, the units, and the scripted tests |
| [EXTRACTION-SAFETY.md](EXTRACTION-SAFETY.md) | The uncertain-reference guard with dry-run diffs, the transmittal listed-item association, and BOQ description counts |
| [PROVENANCE-AND-FREEZE.md](PROVENANCE-AND-FREEZE.md) | The corrected Review 06 claim, the recovered and verified `043dee9`, the freeze `c9a1a14` plus amendment `1455f8b`, and how the runs are kept apart |
| [MATCHED-RUN.md](MATCHED-RUN.md) | 12 documents, frozen code, EV0/EV1/EV2 under one ledger |
| [REGRESSION.md](REGRESSION.md) | The hermetic full suite on the frozen code, the new modules, and every changed assertion |
| [human-review-packet/](human-review-packet/INSTRUCTIONS.md) | The source-review packet (prepared, **not** reviewed) |
| `evidence/` | `EVIDENCE-MANIFEST.json` (SHA-256 of 134 files and of every changed candidate file); `candidate-r7.diff` (`043dee9..1455f8b`); new files; re-scores; runs; ledger; scripts; logs |

## Results in brief

All projects here are exposed data.

1. **R7-01, evaluator.**
   - Every emitted fact is scored; the reviewer's probes now fail `.4` and pass `.6`. Every stored output is re-scored.
   - **The Review 06 "zero introduced AI errors" is withdrawn.** `.6` reports 2 for AI-EV1 and 1 for AI-EV2. Source adjudication finds both to be **disputed truth** (a permit with two own identities, and a consultant stamp the label misses), not confirmed AI false acceptances. They are pending human review.
2. **R7-02, validation policy `.2`:**
   - support is region-bound and literal;
   - a near match is only a candidate;
   - decisions need corroboration, the printed legend, one evidenced actor and a target;
   - escalation keeps every reading;
   - own and referenced identities are kept apart;
   - numbers keep their decimal, sign and unit.

   Each reviewer probe is shown validated by `.1` and refused by `.2`.
3. **R7-03, lifecycle:**
   - last-good evidence is kept per page, with its own provenance;
   - attempts are additive;
   - a stale envelope is never current;
   - the profile is bound through the entry point, the cache and the envelope.
4. **R7-04, ledger:**
   - a shared persistent ledger with atomic reservations, a calibrated adapter-aware estimate, reconciliation and a breaker;
   - proven with scripted providers, then used on the matched run: exactly 120/120 requests, with the 121st refused;
   - the stated limit: CLI token use is **estimated plus a breaker, not enforced by the provider**.
5. **E, extraction safety:**
   - **Register critical: 2 → 0** in both pilot profiles. The flagged references are held as pending evidence under stable internal keys. The dry run shows no business-row change and one mirror moved off a cut key. The live database holds no such case.
   - The transmittal/listed-submittal defect is fixed on all three business paths, tested through the application path with no loss on a second sync.
   - Description counts are located facts, and part and quantity are verified apart.
6. **R7-05:**
   - the provenance claim is corrected, and the Review 06 final state is recovered and hash-verified;
   - the Review 07 candidate is frozen (`c9a1a14`, the evaluator amended in `1455f8b` before any matched result was read);
   - **the hermetic full suite on the frozen code: 1,563 passed, 35 skipped, 2 pre-existing failures.**
7. **Matched run (12 documents):**
   - EV1 adds one clean decision recovery and some held evidence;
   - EV2 (54 requests, partial at the cap) adds no clean recovery;
   - every reported AI error is one adjudicated label gap;
   - records are untouched;
   - **no variant is adopted.**

## Blockers: why CHANGES STILL REQUIRED

| # | Blocker | What it needs |
|---|---|---|
| B-1 | **Recovery below 90%.** Pilot, final candidate: register reference 83.5% (default) / 86.7% (promoted), revision 74–76%, decision 37–40%. Raw identity 67%, raw decision 32–36%. The matched sample is below 90% on every field. | More extraction work. For the AI, a component-role rule, since most AI identity readings end as conflicts between an own and a referenced number. |
| B-2 | **Accepted-output precision below 98% on identity**, raw layer 92.8%. Much of that is label disputes and gaps (ADJUDICATIONS). The real raw-observation errors are 2 OCR literal errors and 11 referenced-as-own numbers. | Human settlement of the disputed labels; a fix for the drawing-sheet observation's reference-table pick. |
| B-3 | **Truth unresolved.** 339 component items and 194 BOQ items await the human reviewer. Disputed labels stay out of acceptance denominators until settled. | The **owner, or a reviewer the owner appoints** (owner decision). |
| B-4 | **Project-model eligibility.** Only three exposed projects have a recorded policy. H-03 decisions and the H-06 BOQ cannot be evaluated with the model. | The **owner's** policy decision, per project |
| B-5 | **Variant choice unsupported.** The samples are small, and EV2 was always budget-limited. | A matched run on a larger authorized exploration set, under the ledger, after B-3 and B-4 |
| B-6 | **H-06 deterministic BOQ misreads** (three "1 read as 4") remain accepted; the model path and the verifier `.2` read parts better, but EP-8430 is not authorized | B-4, then a frozen verifier policy tested on fresh sheets |
