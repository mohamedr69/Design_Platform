# Commands run in RD-M2

`ISO` = the session scratch folder `…\scratchpad\rdm2` on C: (outside the repository). `EP` = `G:\dev (2)\dev\ep-platform`. `VENV` = the interpreter the G services use (`…\Desktop\dev\dev\ep-platform\backend\venv\Scripts\python.exe`, CPython 3.12.10). Every Python run set `PYTHONDONTWRITEBYTECODE=1`; every pytest run used `-p no:cacheprovider`. Git commands used `GIT_OPTIONAL_LOCKS=0`.

## Preconditions (read-only)

```
git -C EP rev-parse HEAD; git branch --show-current; git status --porcelain=v1 -uall      # 187 entries = RD-M1 T0 108 + RD-M1 package 79
python: RD-M1 PACKAGE-MANIFEST.json re-hashed (78/78) and PACKAGE-CHECK.json all_pass read
Get-NetTCPConnection / Get-CimInstance Win32_Process                                       # services and ports, not touched
python ISO/scripts/hash_tree.py ISO/hash/RDM2-T0.json                                      # compared with RD-M1 AFTER-T1: code unchanged
```

## Isolated copies

```
tar (EP/backend: app tests alembic alembic.ini pytest.ini requirements.txt; no __pycache__) -> ISO/base/backend, ISO/cand/backend
cp EP/frontend/src/pages/ProjectRedesignPage.tsx -> ISO/{base,cand}/frontend/src/pages/
python: both copies hashed against RDM2-T0 (380/380 each, 0 mismatch)
```

## Implementation (only in ISO/cand)

Write/Edit tools on `ISO/cand/backend/app/redesign/{cad.py, verify.py(new), service.py}`, `ISO/cand/backend/app/routers/redesign.py`, `ISO/cand/backend/app/ifc/services/runners.py`, `ISO/cand/frontend/src/pages/ProjectRedesignPage.tsx`, `ISO/cand/backend/tests/test_redesign_apply.py` (new), plus `python ISO/scripts/patch_existing_tests.py` (3 assertions in `test_redesign.py`) and `python ISO/scripts/patch_frontend.py`. Line endings were normalised to LF where an editor had changed them.

## Tests

```
cd ISO/cand/backend && VENV -m pytest -p no:cacheprovider tests/test_redesign.py tests/test_redesign_apply.py -q
ISO/scripts/run_suite.sh base   # VENV -m pytest -p no:cacheprovider -q -rfEs --deselect tests/test_ifc_boq.py::test_real_dwg_converts_to_the_same_symbols_as_a_hand_saved_dxf --junitxml=…
ISO/scripts/run_suite.sh cand   # same, on the frozen candidate (an earlier cand run on a pre-freeze version was stopped and discarded)
```

The deselected test would run the real AutoCAD Core Console on a drawing from the owner's Desktop when that file exists. It does not exist on this PC, so the test would skip anyway; it was deselected in both runs so that no unauthorised AutoCAD run could happen.

## Frontend type check (no build, no write to the live tree)

```
copy EP/frontend/src -> ISO/tscheck/{base,cand}/src (cand page swapped in); tsconfig.check.json = tsconfig.app.json without tsBuildInfoFile
New-Item -ItemType Junction ISO/tscheck/*/node_modules -> EP/frontend/node_modules      (read-only use)
node node_modules/typescript/bin/tsc -p tsconfig.check.json                            # base 0 errors, cand 0 errors
sha256 of EP/frontend/node_modules/.tmp/* before and after                              # unchanged
```

Two first junctions were created with a malformed target and failed to resolve; they were removed with `rmdir` (which removes the link only) and recreated.

## Freeze

```
python (ISO): candidate-files.json (382 files; changed/added hashes; base hashes of changed)
diff -ruN --exclude=__pycache__ ISO/base ISO/cand > ISO/work/rdm2-candidate.patch
```

## AutoCAD validation (see AUTOCAD-VALIDATION.md)

```
copies: RD-M1 snapshot -> ISO/iso/db/gc01.db; EP/backend/uploads/EP-30880/ifc/60de2a377daa.{dwg,dxf} -> ISO/iso/uploads/EP-30880/ifc/
frozen candidate -> "ISO/iso/code (2)/backend" (381/381 = manifest)
rehearsal: VENV ISO/scripts/autocad_validation.py ISO/iso-dry dry     (stand-in AutoCAD; no AutoCAD process)
the run:   VENV ISO/scripts/autocad_validation.py ISO/iso             (real Core Console)
```

## Package (the only writes into EP)

Write tool: the `.md` files under `EP/docs/milestones/redesign/RD-M2/`; `python ISO/scripts/build_rdm2_package.py` (evidence/, PACKAGE-MANIFEST.json, PACKAGE-CHECK.json).

## Not run

No live endpoint call; no live Plan/Apply/Sync/Repair/Reprocess; no service start, stop or reconfiguration; no `git add/commit/push/stash/reset/checkout`; no change to the live tree outside `docs/milestones/redesign/RD-M2/`; no model call.
