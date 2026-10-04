# Change map — Review 25 correction (journal kind / outcome validation, harness v4.3)

**Application code: no change.** Frozen candidate `719e8de` and accepted baseline `3d5607d` untouched and clean ([bindings/SOURCE-BINDINGS.json](bindings/SOURCE-BINDINGS.json)). **The runner `arm_ev.py` is byte-identical to review24's v4.2** (runner version `arm-ev-2026-10-01.v4.2` unchanged). The journal format and writer, the lifecycle contract, the scorer (byte-identical to review22's v4), the scheduler and the allowance module are unchanged. Frozen hashes, written before the final validation: [bindings/FROZEN-HARNESS.json](bindings/FROZEN-HARNESS.json).

| File (`harness-v4.3/`) | Change | Why |
|---|---|---|
| `provider_journal.py` | `VALIDATOR_REVISION = "provider-outcomes.v1/validator-2"`; `outcome_agrees(kind, outcome)` defines the allowed combinations for all five kinds ([JOURNAL-KIND-OUTCOME-CONTRACT.md](JOURNAL-KIND-OUTCOME-CONTRACT.md)); `load` uses it for every result record and names the kind and outcome in the indeterminate reason. The `ok` / `failure` rules and the streak arithmetic are unchanged. | R25-01 |
| `runner_probes.py`, `lifecycle_probes.py`, `provider_boundary_probes.py`, `test_boundary_v4_2.py` | Evidence roots `r24-*` → `r25-*` (explicit path adaptation only). | Fresh evidence for the successor, without overwriting review24's sandboxes. |
| `neutral_mutation_probes.py` (new) | The reviewer's three mutations plus an unmutated control through the actual runner, recording run record / charges / journal / io before and after the resume, the refusal and its reason. | Required validation. |
| `legacy_journal_recheck.py` (new) | Loads every existing v4.2 journal with validator-1 (from the frozen review24 package) and validator-2 and requires identical results. | Legacy compatibility. |
| `test_neutral_v4_3.py` (new) | 32 regressions: 15 contradictory combinations → indeterminate; 7 writer-produced combinations accepted; valid neutral results neither reset nor extend a streak; success still resets and unresolved attempts stay neutral; the three actual-runner mutations and the unmutated control; the legacy recheck. | |
| `patch_kind_outcome.py` (new) | The recorded edits, applied to a copy of review24's frozen v4.2. | Traceability. |
| `run_r25_chain.sh`, `bindings_r25.py`, `package_r25.py`, `verify_r25_package.py`, `append_response.py` | Packaging (new or re-pointed). | |

## Reproduction

[repro/run_neutral_probe.py](repro/run_neutral_probe.py) stages the reviewer's `neutral_kind_probe.py`, `lifecycle_probes_adapted.py`, `test_neutral_kind.py` and `pytest.ini` **byte-identical** (hashes checked; the reviewer folder is never written to) beside the runner files of the harness under test. Environment adaptations are explicit and recorded in each `RUN.json`:
- `R23_LIFECYCLE_ROOT` = a new scenario root;
- `TEMP` / `TMP` = `C:/t/iso/tmp`;
- `PYTHONDONTWRITEBYTECODE=1`;
- `PILOT_DRY*`, `XTRACK_FAKE_NOW` and `AI_EVIDENCE_*` cleared.

No code was substituted. On the unchanged v4.2 ([repro/on-v4.2/](repro/on-v4.2/)) every mutation loaded as `ok` / streak 2 and resumed with exit 0, 16 new requests and `completed`: **3 failed, 3 valid-neutral controls passed** (pytest exit 1). On v4.3 ([repro/on-v4.3/](repro/on-v4.3/)): 6 passed. The original R24 before- / after-stop-file probe was rerun on v4.3 with review24's staging script ([repro/r24-provider-probe-on-v4.3/](repro/r24-provider-probe-on-v4.3/)).
