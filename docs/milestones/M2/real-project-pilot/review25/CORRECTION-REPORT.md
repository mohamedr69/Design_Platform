# Review 25 correction: reject contradictory neutral journal results (2026-10-01)

**Scope:** R25-01 only. `provider_journal.load` accepted a result whose kind was neutral (`budget`, `cache_hit`, `none`) while its outcome said `transport`. The fix is a validator change in an isolated successor of review24's harness v4.2: no application change, model call, budget change, H-06 rerun, source-document or sealed-project read, label change, or service or live-data action. The R24-01 crash-boundary fix, the scorer, scheduling, allowances and the runner are not reopened (`arm_ev.py` is byte-identical to v4.2). Contract: [JOURNAL-KIND-OUTCOME-CONTRACT.md](JOURNAL-KIND-OUTCOME-CONTRACT.md). Files: [CHANGE-MAP.md](CHANGE-MAP.md). Commands and exit codes: [COMMANDS.md](COMMANDS.md). Status: [STATUS.md](STATUS.md).

## 1. Reproduction on the unchanged v4.2

The reviewer's probe, helper and regressions were staged byte-identical beside the unchanged v4.2 runner files ([repro/on-v4.2/](repro/on-v4.2/)). The runs used agreeing synthetic labels and the scripted provider. Each run produced three transport failures and was killed before the stop file (exit 98, 3 requests, no stop saved); then only the third result's `kind` was changed, with `outcome=transport` kept.

| Third result kind | Unaltered journal | Altered journal | Resume exit | New requests | Status |
|---|---|---|---:|---:|---|
| budget | ok, streak 3 | ok, streak 2 | 0 | 16 | completed |
| cache_hit | ok, streak 3 | ok, streak 2 | 0 | 16 | completed |
| none | ok, streak 3 | ok, streak 2 | 0 | 16 | completed |

Regressions: **3 failed, 3 valid-neutral controls passed, pytest exit 1**, as the reviewer reported. Logs, exit codes, the before and altered journals and the scenario roots are preserved ([repro/scenarios-on-v4.2/](repro/scenarios-on-v4.2/)).

## 2. Correction (harness v4.3, validator `provider-outcomes.v1/validator-2`)

The allowed kind/outcome combinations are now defined and enforced for all five kinds, derived from the writer and the reader's log semantics:

| Kind | Allowed `outcome` |
|---|---|
| `ok` | `"ok"` (unchanged) |
| `failure` | not `None`, not `"ok"`, not starting `budget` (unchanged) |
| `cache_hit` | `"ok"` (new check) |
| `budget` | starts with `budget` (new check) |
| `none` | `None` (new check) |

A contradiction makes the journal indeterminate, and the runner's existing exit-5 path applies unchanged. Nothing is coerced or repaired. The journal format needed no addition, so it stays `provider-outcomes.v1`. All 25 existing v4.2 journals load identically under the old and new validator (state, streak and reason), so no valid journal is reinterpreted. That set contains 252 `ok`, 28 `failure`, 22 `cache_hit` and 4 `budget` results; no `none` result occurs in practice. The edit is recorded in [harness-v4.3/patch_kind_outcome.py](harness-v4.3/patch_kind_outcome.py), and the harness was frozen before the final validation ([bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json)).

## 3. Final results on the frozen successor (actual runner, scripted provider, fresh isolated roots)

**R25-01, the reviewer's three mutations** (fresh runs, [neutral-evidence/NEUTRAL.json](neutral-evidence/NEUTRAL.json)). For each of budget, cache_hit and none:
- the unaltered journal loaded `ok` with streak 3, and only the kind was changed;
- the altered journal is **indeterminate**, with reason `record 7: kind and outcome disagree (kind '<kind>', outcome 'transport')`;
- resume gives **exit 5 with 0 new requests**;
- no stop file is written;
- the run record, allowance charges, journal and `io.jsonl` are byte-identical before and after;
- one refusal is recorded with that reason and `requests_sent: 0`.

The **unmutated control** loads with streak 3, and resume reconstructs the provider stop: exit 4, 0 new requests.

**The reviewer's probe on v4.3** ([repro/on-v4.3/](repro/on-v4.3/)): each mutation is indeterminate, exit 5, 0 new requests. **6 passed**, including the three valid-neutral controls, pytest exit 0.

**The original R24 before- and after-stop-file probe on v4.3** ([repro/r24-provider-probe-on-v4.3/](repro/r24-provider-probe-on-v4.3/)): before-file is 98 → 4, 0 new requests, `stopped`; after-file is 98 → 4, 0 new requests, `stopped`. **3 passed.** R24-01 remains corrected.

**The submitted 62-test set, run once on the frozen successor**: journal 23, scorer 19, runner 8, lifecycle 5, boundary 7. **62 passed, 0 failed, 0 errors, 0 skipped, pytest exit 0** ([harness-v4.3/logs/SUBMITTED-62.xml](harness-v4.3/logs/SUBMITTED-62.xml)). Its fixtures ran from freshly regenerated actual-runner evidence (the lifecycle, runner and boundary probes, each exit 0).

**R25 regressions**: **32 passed, pytest exit 0** ([harness-v4.3/logs/NEUTRAL-V4.3.xml](harness-v4.3/logs/NEUTRAL-V4.3.xml)). They cover:
- 15 contradictory combinations → indeterminate;
- 7 writer-produced combinations accepted;
- a valid cache hit, budget refusal (two outcome forms) or no-result neither resets nor extends a failure streak (F, neutral, F → 2; F, F, neutral, F → 3);
- a success still resets, and an unresolved attempt stays neutral across restarts;
- the three actual-runner mutations and the unmutated control;
- the legacy recheck.

## 4. What is unchanged

- **Accepted decisions:** restart does not reset the failure streak, and a reconstructed stop preserves the last-saved project lists. Neither was touched. The planned population stays the scoring denominator regardless of those historical lists.
- **Runner, lifecycle contract v2, scorer, scheduler and allowance module:** unchanged. The package check verifies their hashes.

## 5. Package and limits

[evidence/PACKAGE-CHECK.json](evidence/PACKAGE-CHECK.json) verifies:
- the manifest and links;
- clean trees;
- workspace and packaged harness equal the pre-validation freeze;
- the runner is unchanged from v4.2 and the scorer from v4;
- the reviewer files and copies are unchanged;
- earlier packages (review13 to review24) and the labels are unchanged;
- JUnit counts and pytest exit codes;
- the mutation, legacy and probe outcomes;
- the live ledger is at 128 settled, with no r21–r25 live scope.

Limits:
- The validator checks internal consistency only. It does not authenticate against a deliberately consistent rewrite.
- These are synthetic harness tests. They produce **no new accuracy evidence**.

**Ready for independent review. This is not self-approved.**
