# Commands run in RD-M1

All times local (UTC+4) on 2026-10-03, PC-B. `ISO` = the isolated session scratch folder (`…\AppData\Local\Temp\claude\…\scratchpad\rdm1`, on C:). `EP` = `G:\dev (2)\dev\ep-platform`. Commands are listed in order, grouped; each was read-only towards `EP`, the live DB and the source drawings unless stated. Writes went only to `ISO` and, at the end, to `EP/docs/milestones/redesign/RD-M1/`.

## Environment identity (read-only)

```
git -C "G:/dev (2)/dev" rev-parse HEAD; git branch --show-current; git status --porcelain=v1 -uall
git -C EP rev-parse HEAD; git branch --show-current; git status --porcelain=v1; git log --oneline -10
GIT_OPTIONAL_LOCKS=0 git -C "G:/dev (2)/dev" ls-files -s ep-platform
Get-CimInstance Win32_Process | ? Name -match 'python|node|acad|uvicorn|accoreconsole|cmd'   # PowerShell
Get-NetTCPConnection -State Listen                                                             # PowerShell
cat EP/backend/venv/pyvenv.cfg; cat EP/start.bat
sed -E 's/(KEY|SECRET|TOKEN|PASSWORD)...=.*/<redacted>/' EP/.env EP/backend/.env               # values of secrets never printed
sed -n 1,260p EP/backend/app/core/config.py; grep drawing_review_ …/config.py
python --version; node --version; <venv>/python.exe -c "import ezdxf, pymupdf, PIL, sqlalchemy, fastapi, pytest; print(versions)"
ls "C:/Program Files/Autodesk"; ls "C:/Program Files/ODA"
cat <outer>/backend-g-api.std{err,out}.log; tail worker-g.stderr.log; cat ifc-worker-g.stderr.log
```

Note: the first `git status` / `git diff --stat` ran **without** `GIT_OPTIONAL_LOCKS=0` and may have refreshed git's index stat cache (`.git/index`, not a working-tree file). All later git commands used `GIT_OPTIONAL_LOCKS=0`.

## Baseline and snapshot (writes to ISO only)

```
python ISO/scripts/hash_tree.py ISO/hash/BASELINE-T0.json          # 740 + 1,870 + 25 files, 2 m 16 s
git -C EP status --porcelain=v1 -uall > ISO/hash/git-status-ep-T0.txt
python ISO/scripts/snapshot_db.py ISO/db/ep_platform.audit-snapshot.db > ISO/hash/DB-SNAPSHOT-INFO.json
```

## Reading code (read-only)

`Read`/`grep`/`sed -n` on `EP/backend/app/redesign/{service,cad,walls,ai}.py`, `routers/redesign.py`, `review/{geometry,render,service}.py`, `ifc/services/runners.py`, `services/jobs.py`, `interfaces/service.py`, `database.py`, `tests/conftest.py`, `tests/test_redesign.py`, `frontend/src/pages/ProjectRedesignPage.tsx`, `frontend/package.json`.

## Reading uploads (read-only listing/hash; copies to ISO)

```
ls -la EP/backend/uploads/EP-30880/{ifc,review,interfaces,redesign,redesign/work-1}
cat EP/backend/app/redesign/library/modules.json
cat …/work-1/ErrorReports/<id>/cer.log | grep …
cp -p …/work-1/redesign.scr ISO/src/EP-30880/redesign-work-1/
cp -p …/review/66043c11fab9eaf5a1768ba2.pdf ISO/src/EP-30880/review-plot.pdf
cp -p …/redesign/walls-1-66043c11fab9eaf5-v1.pkl ISO/src/EP-30880/walls.pkl
cp -p …/ifc/60de2a377daa.dxf ISO/src/EP-30880/source.dxf
ls -d "C:/Users/<PC-A user>"   # confirms the stored library path does not exist on PC-B
```

## Queries (snapshot only, `mode=ro` + `PRAGMA query_only=ON`, total_changes asserted 0)

```
python ISO/scripts/q.py "<SQL>"     # background_jobs, project_redesign, ai_usage, result_cache, activity_events, PRAGMA table_info(...)
python ISO/scripts/dump_case.py
python ISO/scripts/analyse_changes.py
python ISO/scripts/ai_variation.py
```

## Tests (isolated code copy)

```
(cd EP/backend && tar --exclude=__pycache__ --exclude='*.pyc' -cf - app tests alembic) | (cd ISO/code/backend && tar -xf -)
cp -p EP/backend/{alembic.ini,pytest.ini,requirements.txt} ISO/code/backend/
python - (hash comparison of the copy with BASELINE-T0)       # 379 verified, 0 mismatch
cd ISO/code/backend && PYTHONDONTWRITEBYTECODE=1 <venv>/python.exe -m pytest -p no:cacheprovider tests/test_redesign.py -v -rA --durations=5
… tests/test_drawing_review.py | tests/test_fa_interfaces.py | tests/test_ifc_worker_and_ai.py  -q -rfEs
```

## Geometry and rendering (copies only)

```
python ISO/scripts/render_case.py ISO/work/renders ISO/work/render-spec.json     # twice; second run hashes identical
python ISO/scripts/wall_layers.py '[["invisible-rect-left-edge",714.45,156.4,714.65,162.5],["pumproom-top-wall",715.0,161.8,725.0,162.6],["pumproom-right-wall",721.6,154.0,722.2,161.0],["pumproom-left-wall-door",713.6,157.0,714.0,161.5]]'
python ISO/scripts/effective_layer.py '[["invisible-rect-left-edge",714.45,156.4,714.65,162.5],["invisible-rect-bottom",715.0,156.2,721.0,156.5]]'
<venv>/python.exe ISO/scripts/reproduce_apply_input.py
```

## Package (the only writes into EP)

```
python ISO/scripts/build_evidence.py "EP/docs/milestones/redesign/RD-M1"     # evidence/, renders/, crops/
python ISO/scripts/findings.py      "EP/docs/milestones/redesign/RD-M1"     # FAILURE-INVENTORY.csv/.md
Write tool: the .md files of the package
python ISO/scripts/package_check.py "EP/docs/milestones/redesign/RD-M1"     # BASELINE-MANIFEST.json, PACKAGE-MANIFEST.json, PACKAGE-CHECK.json
python ISO/scripts/hash_tree.py ISO/hash/AFTER-T1.json + comparison         # DATA-SAFETY-REPORT.md
```

## Not run (deliberately)

- No API call to any Redesign endpoint (no Plan, Apply, Sync, Reprocess, Repair, PATCH).
- No AutoCAD / accoreconsole / DWG TrueView.
- No model call (Claude Code CLI or API) from the platform. (Claude's visual review of the rendered PNG copies happened in this audit session itself, not through the platform.)
- No service start/stop; no port change; no git add/commit/push/stash/reset/checkout.
