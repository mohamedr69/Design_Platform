"""Pilot step 0: identify the candidate exactly -- commit, dirty-tree hashes, parser/evidence/BOQ versions, profile,
budget and OCR settings, dependencies, timestamp -- and the sandbox roots that every pilot process will use."""
import hashlib, json, os, subprocess, sys, pathlib, datetime, platform

S = pathlib.Path(sys.argv[1]); REPO = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform"); B = REPO / "backend"
os.environ.update({"DATABASE_URL": "sqlite:///:memory:", "AI_ENABLED": "false", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false"})
sys.path.insert(0, str(B)); os.chdir(B)
from app.services import document_control as dc, document_sync as ds, design_sheet_extractor as dse, content_evidence as ce  # noqa: E402
from app.ai import sheet_reader  # noqa: E402
from app.core.config import get_settings  # noqa: E402
st = get_settings()
head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True).stdout.splitlines()
dirty = {l[3:].strip(): (hashlib.sha256((REPO / l[3:].strip()).read_bytes()).hexdigest() if (REPO / l[3:].strip()).is_file() else None) for l in status}
src = ["backend/app/services/document_control.py", "backend/app/services/document_sync.py", "backend/app/services/document_processing.py", "backend/app/services/design_sheet_extractor.py",
       "backend/app/services/transmittals.py", "backend/app/services/content_evidence.py", "backend/app/ai/sheet_reader.py", "backend/app/core/config.py", "backend/scripts/repair_extraction.py",
       "backend/scripts/boq_metrics.py", "backend/tests/conftest.py"]
freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True).stdout.splitlines()
rec = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "head": head, "git_status_lines": len(status), "dirty_files": dirty,
       "source_hashes": {f: hashlib.sha256((REPO / f).read_bytes()).hexdigest() for f in src},
       "versions": {"PARSER_VERSION": dc.PARSER_VERSION, "BOX_VERSION": dc.BOX_VERSION, "INDEX_VERSION": ds.INDEX_VERSION, "design_sheet_extractor.PARSER_VERSION": dse.PARSER_VERSION,
                    "EVIDENCE_VERSION": getattr(ce, "EVIDENCE_VERSION", None), "sheet_reader.PROMPT_VERSION": getattr(sheet_reader, "PROMPT_VERSION", None)},
       "budgets": {"PAGE_SCAN_LIMIT": dc.PAGE_SCAN_LIMIT, "REPLY_SEARCH_LIMIT": dc.REPLY_SEARCH_LIMIT, "OCR_PAGE_LIMIT": dc.OCR_PAGE_LIMIT, "OCR_TIMEOUT_S": getattr(dc, "OCR_TIMEOUT_S", None),
                   "RENDER_DPI(sheets)": dse.RENDER_DPI, "RECHECK_QUANTITY_BELOW": dse.RECHECK_QUANTITY_BELOW, "LOW_QUANTITY_CONFIDENCE": dse.LOW_QUANTITY_CONFIDENCE},
       "settings": {"extraction_promote_observations(default)": st.extraction_promote_observations, "ai_enabled": st.ai_enabled, "tesseract_cmd": st.tesseract_cmd, "sync_file_workers": st.sync_file_workers},
       "profiles": ["default", "promoted"], "python": sys.version, "platform": platform.platform(),
       "dependencies": [l for l in freeze if l.split("==")[0].lower() in ("pymupdf", "pytesseract", "pillow", "numpy", "sqlalchemy", "fastapi", "alembic", "python-docx", "opencv-python")],
       "tesseract_version": subprocess.run([st.tesseract_cmd or "tesseract", "--version"], capture_output=True, text=True).stdout.splitlines()[:1],
       "sandbox_roots": {"stage": "C:/t/pilot/stage", "db": "C:/t/pilot/db", "cache": "C:/t/pilot/cache", "library": "C:/t/pilot/library", "uploads": "C:/t/pilot/uploads", "out": "C:/t/pilot/out",
                         "live_database_untouched": str(B / "ep_platform.db"), "note": "every pilot process sets DATABASE_URL/CACHE_ROOT/LIBRARY_ROOT/UPLOADS_ROOT to the sandbox before importing app code; originals under the OneDrive root are read for metadata and copied once into the stage tree; no write-capable workflow points at the OneDrive folders"}}
json.dump(rec, open(S / "REPRODUCIBILITY.json", "w", encoding="utf-8"), indent=1)
print(json.dumps({k: rec[k] for k in ("head", "git_status_lines", "versions", "budgets", "settings", "tesseract_version")}, indent=1))
