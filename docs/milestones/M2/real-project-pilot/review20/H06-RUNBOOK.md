# H-06 completion runbook (the frozen control; no new permission or budget)

This is the exact sequence for finishing H-06 under the **existing frozen binding**:

| Item | Value |
|---|---|
| Declaration | `C:/t/iso/work/r2x/ai-pilot-r18/CONT-DECLARATION.json`, sha `7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3` |
| Runner | `cont_boq.py` (sha as declared) |
| BOQ reader | accepted `3d5607d` |
| Queue | `boq_queue.py` (unchanged) |
| Matcher / evaluator | r16.1 harness / replay |
| Scopes | `ai-pilot-r18-2026-09-30-H06-S` / `-H06-T`, 12 each |

The newer document-reader candidates (`c216206`, `69ee759`) are **not** bound into this control.

## Steps

1. **Preflight (read-only).** `python C:/t/iso/work/r2x/review19/h06_preflight.py`. It verifies:
   - the declaration and every binding hash;
   - the durable ledger: settled count, open reservations, and that the H-06 scopes are unused;
   - the exclusive H-06 allowance store;
   - the sandbox tags;
   - the **current** rolling EP-8430 count.

   Proceed only if `dispatch_allowed.S` is true, and `both_arms` for the second arm. Historical timestamps are not evidence of capacity.
2. **Arm S:** `python cont_boq.py cont-h06-S S --declaration <decl> --declaration-sha 7b2513b2…` (cwd `C:/t/iso/work/r2x/ai-pilot-r18`, `PILOT_DRY` unset). The runner refuses by itself when EP-8430 cannot fit 12. It writes the declared selection before the first request.
3. **Arm T:** re-run the preflight, then `python cont_boq.py cont-h06-T T …`. It writes the declared queue before the first request.
4. **Score:** `python score_cont.py --declaration <decl> --declaration-sha 7b2513b2… --runs C:/t/r2x/runs --tags A=cont-A,S=cont-S,T2=cont-T2,BOQ-S=cont-h06-S,BOQ-T=cont-h06-T --out <new folder>`. This writes `CONT-H06.json` with:
   - reached / unreached rows;
   - the three wrong accepted targets and the control, identified in the evaluation only;
   - outcomes at equal request count and at each cap.
5. **Package** the outputs, ledger rows and allowance rows as a new immutable completion artifact, and append one response entry.

## Rules that stay in force

- No reorder or skip of held rows.
- No budget reset, replacement scope, chunk allowance or reopened breaker.
- 12 requests per arm, 24 total; 60 per project per rolling day.
- A target that is never reached is **not** detected.
- A zero-detection result is a valid finding.
- A stop rule (three provider failures, a breaker, a hash or scope mismatch) ends the run; every partial attempt is preserved.
