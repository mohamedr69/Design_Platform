@echo off
rem Start the Engineering Project Platform (the merged installation): the API on
rem http://localhost:8002, the sync worker, the document processing worker, the
rem IFC worker, and the web app on http://localhost:5175, each in its own window.
rem Its ports, database, uploads and logs are its own (backend\.env), apart from
rem the G and Desktop installations. Run setup.bat once first on a new PC.
setlocal
cd /d "%~dp0"

if not exist backend\venv (
    echo The platform is not set up on this PC yet: run setup.bat first.
    exit /b 1
)

rem The old backend processes first (the web app is left alone): a worker
rem has no hot reload, and one left running keeps the code it started with.
call "%~dp0stop-backend.bat"

rem --timeout-graceful-shutdown: a reload waits at most 3 s for open page
rem connections, instead of hanging on them with the old code still serving.
start "EP Platform (merged) - API" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m uvicorn app.main:app --reload --reload-dir app --timeout-graceful-shutdown 3 --port 8002"
rem The sync worker runs every file sync (the index: a stat per file, seconds
rem a project), so listing a project folder never slows the pages. Below
rem normal priority: the engineer's programs and the API come first. It has
rem no hot reload: after changing backend code, close its window and start it
rem again with the same command.
start "EP Platform (merged) - Worker" /belownormal cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m app.workers.sync_worker"
rem The document processing worker reads the documents the sync found (the
rem PDFs, OCR, the AI on material submittal forms), one project at a time,
rem in the background while the platform is in use. Same rule: no hot reload.
start "EP Platform (merged) - Documents" /belownormal cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m app.workers.document_worker"
rem The IFC worker reads the uploaded IFC drawings (DWG conversion, CAD
rem extraction, the AI symbol review), IFC_WORKER_CONCURRENCY at a time, so
rem a building's drawings never slow the pages. Same rule: no hot reload.
start "EP Platform (merged) - IFC Worker" /belownormal cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m app.workers.ifc_worker"
start "EP Platform (merged) - Web" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 8 >nul
start "" http://localhost:5175
endlocal
