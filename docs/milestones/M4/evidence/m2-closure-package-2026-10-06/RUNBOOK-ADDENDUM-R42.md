# Runbook addendum R42 — the one recommendation of Verification 42 for the frozen declaration v3 `9a55fa7b…1b40`

Written 2026-10-06 by the orchestrator (ledger ORCH-032) under A-03, A-06, A-09, A-10, A-11. It changes nothing in the frozen packages `PILOT/review42/` (manifest `ab2bc40d…e782`) and `PILOT/declaration-r32-v3/` (manifest `a2df60dc…1a24`; declaration `FRESH-VALIDATION-DECLARATION-R32-V3.json` `9a55fa7b2d52dad5c87fff72b3225cb9ce1b3f0aba002357ad53d1f33fa81b40`), which stay frozen and NOT authorized. It is read together with `declaration-r32-v3/RUNBOOK.md` and supersedes `RUNBOOK-ADDENDUM-R41.md` where the two differ (R41's C1 disk condition is now enforced by the runner itself, contract v5; the dead-end class and the CLI re-check are closed in code). Verification 42: `MR/reviews/M2-review-42/INDEPENDENT-VERIFICATION.md` `b0f4ad9998266434a235a37fe7fe307dde243e6e45c9fc2c19d20a2574899b30`, `FINDINGS.json` `28ec335a…b561`, verdict **ORCH-10 VERIFIED** (0 blockers, 0 majors, 1 minor R42-09, 15 info; no conditions).

## 1. R42-09 (minor): the bound interpreter's packages (owner precondition; no new hash)
The declaration binds the interpreter `G:\dev (2)\dev\ep-platform-merged\ep-platform\backend\venv\Scripts\python.exe` by path, sha256 and version, and records its 57 distributions in `declaration-r32-v3/evidence/INTERPRETER-CHECK.json` (sha256 `96639af969dcf4601b20d03661681779d30a2ae57986bb88000d99786c35c504`), but the runner does not re-check the packages at run time, and the same venv serves the live merged installation. **Procedure:** before invocation 1 and before every resume the owner runs, in the runbook's cmd window,

```cmd
"%PY%" -B -m pip freeze
```

and compares the output with the `distributions` of `INTERPRETER-CHECK.json` (the orchestrator provides a read-only comparison on request). Any difference: stop; do not install, upgrade or remove anything in that venv for the run's duration (the merged installation's `setup.bat` must not be run while the experiment is open).

## 2. Records bound by hash (R42-11)
`C:/t/iso/work/r2x/r42/AUDIT-LOG.md` `4608b55a2237f2d9887b6de3429438f4dd769b7096981f488143cbe104eba953`; `PROGRESS.md` `dd9c17cb3a6e0b76226e90eec7a94a7efc7f1fc635c8b736dce60d2b14192a0d`; `RESPONSE-APPEND-RECORD.json` `2ee0fb085aaabcdd48e8313e5567b60c5dc2c50bee23cc7086683dedcaccf5b8`. Not to be modified or deleted.

## 3. Corrections to statements in the frozen package (R42-10)
The v3 package's longest path is 172 characters (not 134 as one disclosure says); the live staged PDFs reach 255 characters, and 256 from invocation 10 onward. Both are below 260; `LongPathsEnabled` = 0 is unchanged.

## 4. Unchanged owner items
D1 (served-model identity), D2 (budget authorization; the per-invocation or the one-file-three-nonces form), D3 (acknowledgements), D4 (owner-confirmable values) of `OWNER-DECISION-CARD-M2.md`, now against `9a55fa7b…1b40`. v2 `f38fb281…25af` is never to be run. Nothing in this addendum authorizes a scope, a token, an authorization file, a RUN file, a request, a dispatch of B, C, R or P, a default, M2 acceptance or M3.
