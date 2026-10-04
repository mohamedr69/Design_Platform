"""RD-M2 AutoCAD validation session 2 (owner authorisation of 2026-10-03): candidate v2.

usage: autocad_validation2.py <root> <AB|C> [dry]
  <root>/code (2)/backend   frozen candidate v2 (hash-checked against the manifest first)
  <root>/db/*.db            a copy of the RD-M1 snapshot (never the live DB)
  <root>/uploads/...        copies of the GC-01 DWG/DXF (never the live uploads)
AB: A = the 11 approved GC-01 changes; B = the same with a missing block first.
C : synthetic approved-erase control on a disposable copy: one approved REMOVE of
    model-space INSERT 5DD10 (CEILING SPEAKER), nothing else approved.
Publication happens only inside <root>/uploads (the isolated validation output).
"""
import hashlib
import json
import os
import re
import sys
import tempfile
import time
import traceback
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
MODE = sys.argv[2]
DRY = len(sys.argv) > 3 and sys.argv[3] == "dry"
CODE = ROOT / "code (2)" / "backend"
HERE = Path(__file__).resolve().parent
MANIFEST = HERE.parent / "work" / "candidate-files.json"
LIVE_DWG = Path(r"G:\dev (2)\dev\ep-platform\backend\uploads\EP-30880\ifc\60de2a377daa.dwg")
TEMP = Path(tempfile.gettempdir())


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# 0. the code is exactly frozen v2
manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
assert manifest.get("version") == "v2", "not the v2 manifest"
code_bad = [rel for rel, h in manifest["all_candidate_sha256"].items()
            if rel.startswith("backend/") and sha(CODE.parent / rel) != h]
code_files = sum(1 for rel in manifest["all_candidate_sha256"] if rel.startswith("backend/"))
assert not code_bad, f"code differs from frozen v2: {code_bad[:5]}"

os.environ.update({
    "DATABASE_URL": "sqlite:///" + next((ROOT / "db").glob("*.db")).as_posix(),
    "UPLOADS_ROOT": str(ROOT / "uploads"),
    "CACHE_ROOT": str(ROOT / "work" / "cache"), "LIBRARY_ROOT": str(ROOT / "work" / "library"),
    "AI_ENABLED": "false", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
    "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": "",
    "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
    "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false"})
os.environ.pop("DATA_ROOT", None)
sys.path.insert(0, str(CODE))
(ROOT / "work").mkdir(exist_ok=True)
os.chdir(ROOT / "work")

from app.core.config import get_settings  # noqa: E402

s = get_settings()
assert Path(s.uploads_root).resolve() == (ROOT / "uploads").resolve() and "/db/" in s.database_url
assert not s.ai_enabled and not s.projects_root
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectRedesign  # noqa: E402
from app.redesign import cad  # noqa: E402
from app.redesign import service as R  # noqa: E402

assert Path(R.__file__).resolve().is_relative_to(CODE)
if DRY:
    from app.ifc.dxf import convert as _convert

    fake = HERE / "fake_acad.py"
    _convert.find_converter = lambda: _convert.Converter("fake", "accoreconsole", sys.executable)
    cad._command = lambda conv, copy, script: [sys.executable, str(fake), str(copy), str(script)]

    def _fake_readback(dwg, dxf, converter=None):
        import ezdxf as _ez
        doc = _ez.readfile(ROOT / "uploads" / "EP-30880" / "ifc" / "60de2a377daa.dxf")
        scr = Path(dwg).parent / "redesign.scr"
        if scr.is_file():
            text = scr.read_text(encoding="utf-8")
            msp = doc.modelspace()
            for h in re.findall(r'\(ep_erase "([0-9A-F]+)"', text):
                msp.delete_entity(doc.entitydb[h])
            for blk, x, y in re.findall(r'\(command "_\.-INSERT" "([^"]+)" "_S" \(/ [0-9.]+ ep_f\) \(list ([-0-9.]+) ([-0-9.]+) 0\.0\)', text):
                if blk not in doc.blocks:
                    doc.blocks.new(blk)
                msp.add_blockref(blk, (float(x), float(y)))
        doc.saveas(dxf)
    _convert.convert_dwg_to_dxf = _fake_readback

SRC = ROOT / "uploads" / "EP-30880" / "ifc" / "60de2a377daa.dwg"
OUT = ROOT / "uploads" / "EP-30880" / "redesign"


def temp_state() -> dict:
    out = {}
    for p in TEMP.iterdir():
        try:
            st = p.stat()
            out[p.name] = {"mtime": st.st_mtime, "ctime": st.st_ctime, "dir": p.is_dir(),
                           "size": st.st_size if p.is_file() else None}
        except OSError:
            pass
    return out


def tree(root: Path) -> dict:
    return {str(p.relative_to(root)).replace("\\", "/"): (p.stat().st_size if p.is_file() else -1)
            for p in sorted(root.rglob("*"))} if root.exists() else {}


def entity_diff(src_dxf: Path, out_dxf: Path, limit: int = 25) -> dict:
    """Every model-space entity present in both read-backs, attribute by attribute."""
    import ezdxf

    a = {e.dxf.handle: e for e in ezdxf.readfile(src_dxf).modelspace()}
    b = {e.dxf.handle: e for e in ezdxf.readfile(out_dxf).modelspace()}
    changed = []
    for h in set(a) & set(b):
        da, db_ = a[h].dxfattribs(), b[h].dxfattribs()
        if a[h].dxftype() != b[h].dxftype() or da != db_:
            keys = sorted(k for k in set(da) | set(db_) if da.get(k) != db_.get(k))
            changed.append({"handle": h, "type": a[h].dxftype(), "attribs": keys[:8]})
    return {"common": len(set(a) & set(b)), "changed": len(changed), "examples": changed[:limit]}


def run_scenario(name: str, mutate=None, expect_made: bool = True) -> dict:
    db = SessionLocal()
    rec = {"name": name}
    try:
        project = db.get(Project, 5)
        row = db.query(ProjectRedesign).filter_by(project_id=5, drawing_id=1).one()
        if mutate:
            row.changes = mutate([dict(c) for c in row.changes])
            db.commit()
        todo = [c for c in row.changes if R._drawn(c)]
        rec["drawn"] = [c["id"] for c in todo]
        cad_changes = R.to_cad(todo)
        rec["expected_markers"] = {"CIRCLE": len(cad_changes),
                                   "TEXT": len(cad_changes) + sum(1 for c in cad_changes if c.get("note"))}
        rec["expected_counts"] = list(cad.expected_counts(cad_changes))
        before_out = sorted(p.name for p in OUT.glob("*.dwg")) if OUT.is_dir() else []
        rec["source_sha256_before"] = sha(SRC)
        t0 = time.time()
        try:
            rec["result"] = R.apply(db, project, 1, None)
            rec["outcome"] = "made"
        except Exception as exc:  # noqa: BLE001
            rec["outcome"], rec["error"] = type(exc).__name__, str(exc)
            rec["trace_tail"] = traceback.format_exc().splitlines()[-3:]
        rec["seconds"] = round(time.time() - t0, 1)
        rec["source_sha256_after"] = sha(SRC)
        db.expire_all()
        row = db.query(ProjectRedesign).filter_by(project_id=5, drawing_id=1).one()
        rec["row"] = {"output_status": row.output_status, "output_path": row.output_path,
                      "output_relative": row.output_relative, "output_changes": row.output_changes,
                      "output_error": (row.output_error or "")[:600]}
        after_out = sorted(p.name for p in OUT.glob("*.dwg")) if OUT.is_dir() else []
        rec["outputs_new"] = [n for n in after_out if n not in before_out]
        runs = sorted((OUT / "runs").iterdir(), key=lambda p: p.stat().st_mtime) if (OUT / "runs").is_dir() else []
        run = runs[-1]
        rec["run_folder"], rec["run_files"] = run.name, tree(run)
        log = (run / "autocad.log").read_text(encoding="utf-8", errors="replace")
        rec["standalone_markers"] = [ln.strip() for ln in log.splitlines() if re.match(r"^EP-RD-(OK|FAIL|NOSAVE):", ln.strip())]
        rec["echoed_marker_lines"] = [ln.strip() for ln in log.splitlines() if '"\\nEP-RD-' in ln]
        rec["verification"] = json.loads((run / "verification.json").read_text(encoding="utf-8"))
        script = (run / "redesign.scr").read_text(encoding="utf-8")
        rec["script_library_refs"] = sorted(set(re.findall(r'"([A-Z0-9]+)=([^"]+)"', script)))
        rec["script_has_office_path"] = bool(re.search(r"C:/Users/[^/]+/OneDrive", script))
        if (run / "redesign.dwg").is_file():
            rec["work_copy_sha256"] = sha(run / "redesign.dwg")
            rec["work_copy_equals_source"] = rec["work_copy_sha256"] == sha(SRC)
        if rec["outcome"] == "made":
            out_file = ROOT / "uploads" / rec["result"]["path"]
            rec["published"] = {"path": rec["result"]["path"], "sha256": sha(out_file),
                                "inside_isolated_uploads": out_file.resolve().is_relative_to((ROOT / "uploads").resolve()),
                                "differs_from_source": sha(out_file) != sha(SRC)}
            src_rb = next(OUT.glob("source-readback-*.dxf"))
            rb = rec["verification"]["readback"]
            rec["markers_added_vs_expected"] = {"added_by_type": rb.get("added_by_type"),
                                                "expected": rec["expected_markers"]}
            rec["existing_entities_changed"] = entity_diff(src_rb, run / "readback.dxf")
    finally:
        db.close()
    return rec


def missing_first(changes):
    bad = {"id": "rdm2-missing-block", "page": 0, "sheet": "FA 101", "floor": "3RD BASEMENT", "room": "Pump Room",
           "system": "detection", "system_name": "Detection", "action": "add", "device": "validation: missing block",
           "instruction": "RD-M2 validation", "status": "approved", "candidates": [], "remove": None, "moved": True,
           "residual": 0.0, "insert": {"block": "RDM2-MISSING-BLOCK", "layer": "fire alarm", "scale": 1.0, "rotation": 0.0,
                                         "model": [716.0, 158.0], "seen": [716.0, 158.0], "placed": [716.0, 158.0],
                                         "offset": [0, 0]}}
    return [bad] + changes


def erase_only(changes):
    """Synthetic control on a disposable copy: nothing approved but one REMOVE of 5DD10."""
    target = {"n": 11, "handle": "5DD10", "block": "CEILING SPEAKER", "name": "Ceiling Speaker", "code": "SPK",
              "page": [761.45, 656.6], "model": [1309.45, 155.68], "insert_point": [1309.2, 155.93], "rotation": 270.0,
              "scale": 0.009, "layer": "-SPK", "erasable": True}
    out = [{**c, "status": "skipped"} if c.get("status") == "approved" else c for c in changes]
    out.append({"id": "rdm2-erase-control", "page": 4, "sheet": "FA 105", "floor": "1ST PODIUM", "room": "LIFT LOBBY",
                "system": "speaker", "system_name": "Speakers", "action": "remove", "device": "validation: erase control",
                "instruction": "RD-M2 synthetic erase control", "status": "approved", "confidence": "high",
                "candidates": [target], "insert": None, "moved": False, "residual": 0.0, "at": target["page"],
                "remove": {k: target[k] for k in ("n", "handle", "block", "name", "page", "model", "erasable")}})
    return out


report = {"mode": MODE, "dry": DRY, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
          "candidate": {"manifest_sha256": sha(MANIFEST), "version": manifest["version"], "backend_files_checked": code_files,
                        "mismatch": len(code_bad)},
          "live_source_sha256_before": sha(LIVE_DWG), "iso_uploads_before": tree(ROOT / "uploads"), "scenarios": {}}
temp_before = temp_state()
t_start = time.time()
if MODE == "AB":
    report["scenarios"]["A_success"] = run_scenario("A: 11 approved GC-01 changes")
    report["scenarios"]["B_missing_block"] = run_scenario("B: missing block first", missing_first, expect_made=False)
elif MODE == "C":
    report["scenarios"]["C_erase_control"] = run_scenario("C: synthetic approved erase of 5DD10", erase_only)
t_end = time.time()
temp_after = temp_state()
report["live_source_sha256_after"] = sha(LIVE_DWG)
report["iso_uploads_after"] = tree(ROOT / "uploads")
new = {n: v for n, v in temp_after.items() if n not in temp_before}
report["temp_new"] = sorted(new)
report["temp_changed"] = sorted(n for n in temp_after if n in temp_before and temp_after[n]["mtime"] != temp_before[n]["mtime"])
report["temp_removed"] = sorted(n for n in temp_before if n not in temp_after)
# delete only AutoCAD-named files created during this run's window, when not locked
deleted, kept = [], []
for n, v in new.items():
    p = TEMP / n
    conclusive = (not v["dir"]) and re.fullmatch(r"(ACAS|UNDO)\{[0-9A-F-]{36}\}\.ac\$", n) and t_start - 1 <= v["ctime"] <= t_end + 1
    if conclusive and not DRY:
        try:
            p.unlink()
            deleted.append(n)
        except OSError as exc:
            kept.append(f"{n} (locked: {exc.__class__.__name__})")
    else:
        kept.append(n)
report["temp_deleted_conclusive"] = deleted
report["temp_left_uncertain"] = kept
report["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
out = ROOT / "evidence" / f"autocad-validation2-{MODE}{'-dry' if DRY else ''}.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
summary = {k: {kk: v.get(kk) for kk in ("outcome", "error", "seconds", "outputs_new", "standalone_markers",
                                         "echoed_marker_lines", "work_copy_equals_source", "script_has_office_path",
                                         "published", "markers_added_vs_expected", "existing_entities_changed")}
           for k, v in report["scenarios"].items()}
for k, v in report["scenarios"].items():
    summary[k]["problems"] = v["verification"].get("problems")
    rb = v["verification"].get("readback") or {}
    summary[k]["readback"] = {x: rb.get(x) for x in ("erased_as_expected", "not_erased", "unexpected_erasures",
                                                    "inserts_missing", "unexpected_inserts")} | {
        "inserts_found": len(rb.get("inserts_found") or [])}
print(json.dumps(summary, indent=1, default=str)[:9000])
print("live source unchanged:", report["live_source_sha256_before"] == report["live_source_sha256_after"])
print("temp new:", report["temp_new"], "deleted:", deleted)
