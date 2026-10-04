"""RD-M2 isolated AutoCAD validation on GC-01 (owner decision 3: one validation run).

Everything is a copy under ISO: the frozen candidate code (at a path with a space
and parentheses, like the real install), the RD-M1 DB snapshot, the source DWG and
DXF. AutoCAD works only on per-run copies in ISO/uploads/EP-30880/redesign/runs/.
No archive path, no live DB, no live uploads, no model.

Scenario A: the 11 approved GC-01 changes (5 of them carrying the office PC's
           library path) -> the CT1/CT2/CR files resolved from this code's library.
Scenario B: the same, with an approved change whose block exists nowhere put first
           (RD-M1 F004's case: a first insert that fails) -> nothing published.
"""
import hashlib
import json
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

ISO = Path(sys.argv[1]).resolve()
CODE = ISO / "code (2)" / "backend"
LIVE_DWG = Path(r"G:\dev (2)\dev\ep-platform\backend\uploads\EP-30880\ifc\60de2a377daa.dwg")
TEMP = Path(tempfile.gettempdir())

os.environ.update({
    "DATABASE_URL": "sqlite:///" + (ISO / "db" / "gc01.db").as_posix(),
    "UPLOADS_ROOT": str(ISO / "uploads"),
    "CACHE_ROOT": str(ISO / "work" / "cache"), "LIBRARY_ROOT": str(ISO / "work" / "library"),
    "AI_ENABLED": "false", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
    "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "",
    "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
    "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "DATA_ROOT": "",
})
for k in ("DATA_ROOT",):
    os.environ.pop(k, None)
sys.path.insert(0, str(CODE))
os.chdir(ISO / "work")


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def tree(root: Path) -> dict:
    return {str(p.relative_to(root)).replace("\\", "/"): (p.stat().st_size if p.is_file() else -1)
            for p in sorted(root.rglob("*"))} if root.exists() else {}


def temp_top() -> dict:
    out = {}
    for p in TEMP.iterdir():
        try:
            out[p.name] = p.stat().st_mtime
        except OSError:
            pass
    return out


from app.core.config import get_settings  # noqa: E402

s = get_settings()
assert s.database_url.endswith("/db/gc01.db") and Path(s.uploads_root).resolve() == (ISO / "uploads").resolve(), s.database_url
assert not s.ai_enabled and not s.projects_root

from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectRedesign  # noqa: E402
from app.redesign import service as R  # noqa: E402

assert Path(R.__file__).resolve().is_relative_to(CODE), R.__file__
DRY = len(sys.argv) > 2 and sys.argv[2] == "dry"
if DRY:
    # harness rehearsal only: a stand-in for AutoCAD and the read-back (no AutoCAD process)
    import subprocess as _sp
    from app.ifc.dxf import convert as _convert
    from app.redesign import cad as _cad

    _fake = ISO / "work" / "fake_acad.py"
    _fake.write_text(open(Path(__file__).with_name("fake_acad.py"), encoding="utf-8").read(), encoding="utf-8")
    _convert.find_converter = lambda: _convert.Converter("fake", "accoreconsole", sys.executable)
    _cad._command = lambda conv, copy, script: [sys.executable, str(_fake), str(copy), str(script)]

    def _fake_readback(dwg, dxf, converter=None):
        import re as _re2
        import ezdxf as _ez
        doc = _ez.readfile(ISO / "uploads" / "EP-30880" / "ifc" / "60de2a377daa.dxf")
        if not (Path(dwg).parent / "redesign.scr").is_file():
            doc.saveas(dxf)
            return
        text = (Path(dwg).parent / "redesign.scr").read_text(encoding="utf-8")
        msp = doc.modelspace()
        for blk, x, y in _re2.findall(r'\(command "_\.-INSERT" "([^"]+)" "_S" \(/ [0-9.]+ ep_f\) \(list ([-0-9.]+) ([-0-9.]+) 0\.0\)', text):
            if blk not in doc.blocks:
                doc.blocks.new(blk)
            msp.add_blockref(blk, (float(x), float(y)))
        doc.saveas(dxf)
    _convert.convert_dwg_to_dxf = _fake_readback
SRC = ISO / "uploads" / "EP-30880" / "ifc" / "60de2a377daa.dwg"
OUT = ISO / "uploads" / "EP-30880" / "redesign"
report = {"started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "code": "ISO/code (2)/backend (frozen candidate copy)",
          "library_dir": R.LIBRARY.resolve().as_posix().replace(ISO.as_posix(), "ISO"),
          "before": {"live_source_sha256": sha(LIVE_DWG), "iso_source_sha256": sha(SRC),
                     "iso_uploads": tree(ISO / "uploads")}, "scenarios": {}}
temp_before = temp_top()


def scenario(name: str, mutate=None) -> dict:
    db = SessionLocal()
    rec = {"name": name}
    try:
        project = db.get(Project, 5)
        row = db.query(ProjectRedesign).filter_by(project_id=5, drawing_id=1).one()
        if mutate:
            row.changes = mutate([dict(c) for c in row.changes])
            db.commit()
        rec["drawn"] = [c["id"] for c in row.changes if R._drawn(c)]
        rec["stored_library_paths_other_pc"] = sum(
            1 for c in row.changes if R._drawn(c) and (c.get("insert") or {}).get("library", "").startswith("C:/Users/"))
        outputs_before = sorted(p.name for p in OUT.glob("*.dwg")) if OUT.is_dir() else []
        t0 = time.time()
        try:
            rec["result"] = R.apply(db, project, 1, None, progress=lambda d, t, m: rec.setdefault("progress", []).append(m))
            rec["outcome"] = "made"
        except Exception as exc:  # noqa: BLE001
            rec["outcome"] = type(exc).__name__
            rec["error"] = str(exc)
            rec["trace_tail"] = traceback.format_exc().splitlines()[-3:]
        rec["seconds"] = round(time.time() - t0, 1)
        db.expire_all()
        row = db.query(ProjectRedesign).filter_by(project_id=5, drawing_id=1).one()
        rec["row"] = {"output_status": row.output_status, "output_path": row.output_path,
                      "output_relative": row.output_relative, "output_changes": row.output_changes,
                      "output_error": (row.output_error or "")[:600]}
        outputs_after = sorted(p.name for p in OUT.glob("*.dwg")) if OUT.is_dir() else []
        rec["outputs_new"] = [n for n in outputs_after if n not in outputs_before]
        runs = sorted((OUT / "runs").iterdir(), key=lambda p: p.stat().st_mtime) if (OUT / "runs").is_dir() else []
        run = runs[-1] if runs else None
        if run:
            rec["run_folder"] = run.name
            rec["run_files"] = tree(run)
            log = (run / "autocad.log").read_text(encoding="utf-8", errors="replace") if (run / "autocad.log").is_file() else ""
            rec["log_markers"] = [ln.strip() for ln in log.splitlines() if ln.strip().startswith("EP-RD-")]
            rec["log_errors"] = [ln.strip() for ln in log.splitlines() if "error" in ln.lower() or "invalid" in ln.lower()][:20]
            if (run / "verification.json").is_file():
                rec["verification"] = json.loads((run / "verification.json").read_text(encoding="utf-8"))
            if (run / "redesign.dwg").is_file():
                rec["work_copy_sha256"] = sha(run / "redesign.dwg")
                rec["work_copy_equals_source"] = rec["work_copy_sha256"] == sha(SRC)
            script = (run / "redesign.scr").read_text(encoding="utf-8")
            import re as _re
            rec["script_library_refs"] = sorted(set(_re.findall(r'"([A-Z0-9]+)=([^"]+)"', script)))
            rec["script_has_other_pc_path"] = "C:/Users/" in script and "/library/" in script and \
                any("OneDrive" in ln for ln in script.splitlines())
        for name_ in rec["outputs_new"]:
            rec.setdefault("output_sha256", {})[name_] = sha(OUT / name_)
    finally:
        db.close()
    return rec


report["scenarios"]["A_success"] = scenario("A: approved GC-01 changes, current library")


def missing_first(changes):
    bad = {"id": "rdm2-missing-block", "page": 0, "sheet": "FA 101", "floor": "3RD BASEMENT", "room": "Pump Room",
           "system": "detection", "system_name": "Detection", "action": "add", "device": "validation: missing block",
           "instruction": "RD-M2 validation", "status": "approved", "candidates": [], "remove": None, "moved": True,
           "residual": 0.0, "insert": {"block": "RDM2-MISSING-BLOCK", "layer": "fire alarm", "scale": 1.0, "rotation": 0.0,
                                         "model": [716.0, 158.0], "seen": [716.0, 158.0], "placed": [716.0, 158.0],
                                         "offset": [0, 0]}}
    return [bad] + changes


report["scenarios"]["B_missing_block"] = scenario("B: first insert's block missing", missing_first)
report["after"] = {"live_source_sha256": sha(LIVE_DWG), "iso_source_sha256": sha(SRC), "iso_uploads": tree(ISO / "uploads")}
temp_after = temp_top()
report["temp_new_entries"] = sorted(n for n in temp_after if n not in temp_before)
report["temp_changed_entries"] = sorted(n for n in temp_after if n in temp_before and temp_after[n] != temp_before[n])
report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
(ISO / "evidence").mkdir(exist_ok=True)
(ISO / "evidence" / "autocad-validation.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: {kk: v.get(kk) for kk in ("outcome", "error", "seconds", "outputs_new", "log_markers",
                                                 "work_copy_equals_source", "script_has_other_pc_path", "drawn")}
                  for k, v in report["scenarios"].items()}, indent=1, default=str)[:6000])
print("live source unchanged:", report["before"]["live_source_sha256"] == report["after"]["live_source_sha256"])
print("iso source unchanged:", report["before"]["iso_source_sha256"] == report["after"]["iso_source_sha256"])
