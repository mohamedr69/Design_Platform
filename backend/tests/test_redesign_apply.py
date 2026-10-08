"""Redesign Apply fails closed and draws only approved changes (RD-M2,
ported onto the current preparation code in M5, ORCH-039).

AutoCAD is replaced by a small script that echoes the AutoLISP it is given
(as the Core Console does) and prints the run's markers as told; the copy's
read-back is the source DXF with the script's inserts and erases applied.
No model, no live database, no real drawing, no real AutoCAD.

The candidate's 37 tests come first, adapted: readiness() -- the first
refusal since the candidate was written -- is stubbed "ready" in the `gc`
fixture so the second guard (`_drawn`, approved and confirmed only) is
exercised on its own; readiness() itself, its refusal inside the job and its
422 at the server boundary are tested below, as are coordination (Apply
never coordinates again), the concurrent publication on the file-backed
WAL database, the orphan sweep and the archive publication (OD-15 a)."""
from __future__ import annotations

import hashlib
import re
import sys
from datetime import timedelta
from pathlib import Path

import ezdxf
import pytest

from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.redesign import cad
from app.redesign import service as R
from app.redesign import verify as V
from tests.conftest import login

settings = get_settings()
OFFICE = "C:/Users/someone-else/OneDrive - Org/Desktop/dev/ep-platform/backend/app/redesign/library"

FAKE_ACAD = r'''
import os, re, sys, time
copy, script = sys.argv[1], sys.argv[2]
text = open(script, encoding="utf-8").read()
print(text)                                   # the Core Console echoes what it reads
nonce = re.search(r'\(setq ep_nonce "([0-9a-f]+)"', text).group(1)
ins, dele = re.search(r'\(/= ep_ins (\d+)\) \(/= ep_del (\d+)\)', text).groups()
mode = os.environ.get("FAKE_ACAD_MODE", "ok")
if mode == "slow":
    time.sleep(60)
if mode in ("ok", "badexit", "nomarker"):
    with open(copy, "ab") as f:
        f.write(b"EDITED")
if mode in ("ok", "badexit", "unchanged"):
    print("EP-RD" + "-OK:" + nonce + ":" + ins + ":" + dele)
if mode == "fail":
    print("EP-RD" + "-FAIL:" + nonce + ":insert:m1")
    print("EP-RD" + "-NOSAVE:" + nonce)
sys.exit(3 if mode == "badexit" else 0)
'''


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_dxf(path: Path) -> dict:
    doc = ezdxf.new()
    for name in ("CT1", "CT2", "CR", "CEILING SPEAKER", "HEAT DETECTOR"):
        doc.blocks.new(name).add_circle((0, 0), 0.1)
    msp = doc.modelspace()
    speaker = msp.add_blockref("CEILING SPEAKER", (5, 5))
    other = msp.add_blockref("CEILING SPEAKER", (40, 40))
    msp.add_line((0, 0), (50, 0))
    doc.saveas(path)
    return {"speaker": speaker.dxf.handle, "other": other.dxf.handle}


def _module(cid: str, code: str, at: tuple[float, float], status="approved") -> dict:
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "B3", "room": "Pump Room", "system": "interface",
            "system_name": "FA Interfaces", "action": "add", "device": f"{code} module", "instruction": f"{code} FOR PUMP",
            "status": status, "source": "interface", "candidates": [], "remove": None, "moved": True, "edited": True,
            "residual": 0.0, "interface": {"code": code, "for": "PUMP", "note_height": 0.3, "half": 0.2, "depth": 0.1},
            "insert": {"block": code, "layer": "fa", "scale": 0.00175, "rotation": 90.0, "model": list(at), "seen": list(at),
                       "placed": list(at), "offset": [0, 0], "library": f"{OFFICE}/{code}.dwg", "symbol": 800002}}


def _review_add(cid: str, block: str, at, status="approved", residual=0.0, moved=False) -> dict:
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "B3", "room": "Pump Room", "system": "detection",
            "system_name": "Detection", "action": "add", "device": "heat detector", "instruction": "Add H",
            "status": status, "candidates": [], "remove": None, "moved": moved, "residual": residual, "confidence": "medium",
            "insert": {"block": block, "layer": "fa", "scale": 1.0, "rotation": 0.0, "model": list(at), "seen": list(at),
                       "placed": list(at), "offset": [0, 0]}}


def _review_remove(cid: str, handle: str, at, status="approved", confidence="medium") -> dict:
    return {"id": cid, "page": 0, "sheet": "FA 101", "floor": "B3", "room": "Electrical Room", "system": "speaker",
            "system_name": "Speakers", "action": "remove", "device": "ceiling speaker", "instruction": "Remove CS",
            "status": status, "confidence": confidence, "insert": None, "moved": False, "residual": 0.0,
            "candidates": [{"n": 1, "handle": handle, "block": "CEILING SPEAKER", "insert_point": list(at), "page": [0, 0],
                            "model": list(at), "erasable": True}],
            "remove": {"n": 1, "handle": handle, "block": "CEILING SPEAKER", "name": "Ceiling Speaker", "page": [0, 0],
                       "model": list(at), "erasable": True}}


@pytest.fixture()
def gc(client, db_session, monkeypatch, tmp_path):
    """A project, its drawing (a stand-in DWG beside a real DXF) and a
    redesign: four approved changes to make (two library modules, an add,
    an erase) and three that must not be made."""
    from app.ifc.dxf import convert
    from app.models import ProjectIfcDrawing, ProjectRedesign

    assert login(client, settings.default_admin_email, settings.default_admin_password).status_code == 200
    pid = client.post("/projects", json={"ep_number": "40951", "project_name": "Tower", "design_sheets": []}).json()["id"]
    monkeypatch.setattr(settings, "uploads_root", str(tmp_path / "uploads"))      # this test's own uploads
    uploads = Path(settings.uploads_root).resolve()
    ifc = uploads / "EP-40951" / "ifc"
    ifc.mkdir(parents=True, exist_ok=True)
    handles = _source_dxf(ifc / "d1.dxf")
    dwg = ifc / "d1.dwg"
    dwg.write_bytes(b"STAND-IN SOURCE DWG")
    drawing = ProjectIfcDrawing(project_id=pid, filename="FA LAYOUT.dwg", stored_path="EP-40951/ifc/d1.dxf",
                                revision="R0", meta={}, groups=[])
    db_session.add(drawing)
    db_session.commit()
    changes = [_module("m1", "CT2", (10.0, 10.0)), _module("m2", "CR", (12.0, 10.0)),
               _review_add("r1", "HEAT DETECTOR", (20.0, 20.0)),
               _review_remove("rm", handles["speaker"], (5.0, 5.0)),
               _review_add("p1", "HEAT DETECTOR", (30.0, 30.0), status="proposed"),           # never drawn
               _review_remove("s1", handles["other"], (40.0, 40.0), status="skipped", confidence="low"),
               _review_add("c1", "HEAT DETECTOR", (35.0, 35.0), residual=1.5)]                # spot to confirm
    row = ProjectRedesign(project_id=pid, drawing_id=drawing.id, status="planned", source_sha256=_sha(dwg),
                          changes=changes, symbols=[])
    db_session.add(row)
    db_session.commit()

    fake = tmp_path / "fake_acad.py"
    fake.write_text(FAKE_ACAD, encoding="utf-8")
    calls = {"autocad": 0, "readback": 0}
    monkeypatch.setattr(convert, "find_converter",
                        lambda: convert.Converter("AutoCAD Core Console (test)", "accoreconsole", sys.executable))

    def command(converter, copy, script):
        calls["autocad"] += 1
        return [sys.executable, str(fake), str(copy), str(script)]

    monkeypatch.setattr(cad, "_command", command)

    def readback(dwg_path, dxf_path, converter=None):
        """The copy 'read back': the source DXF with the script's inserts and erases made."""
        calls["readback"] += 1
        mode = readback.mode
        if mode == "error":
            raise convert.ConversionError("unreadable")
        doc = ezdxf.readfile(ifc / "d1.dxf")
        script = Path(dwg_path).parent / "redesign.scr"
        if not script.is_file():                      # the source itself, read back
            doc.saveas(dxf_path)
            return
        text = script.read_text(encoding="utf-8")
        msp = doc.modelspace()
        for h in re.findall(r'\(ep_erase "([0-9A-F]+)"', text):
            msp.delete_entity(doc.entitydb[h])
        if mode == "extra_erasure":
            msp.delete_entity(doc.entitydb[handles["other"]])
        inserts = re.findall(r'\(command "_\.-INSERT" "([^"]+)" "_S" \(/ [0-9.]+ ep_f\) \(list ([-0-9.]+) ([-0-9.]+) 0\.0\)', text)
        for k, (block, x, y) in enumerate(inserts):
            if mode == "missing_insert" and k == 0:
                continue
            msp.add_blockref(block, (float(x), float(y)))
        doc.saveas(dxf_path)

    readback.mode = "faithful"
    monkeypatch.setattr(convert, "convert_dwg_to_dxf", readback)
    monkeypatch.setattr(R, "_units", lambda drawing, db: 1.0)
    # readiness() is tested on its own (below); here it says "ready" unless a test lists blockers
    blockers: list[str] = []
    monkeypatch.setattr(R, "readiness", lambda db, project, drawing, row: {"ready": not blockers,
                                                                           "blockers": list(blockers)})
    project = db_session.get(__import__("app.models", fromlist=["Project"]).Project, pid)
    return {"pid": pid, "project": project, "drawing": drawing, "row_id": row.id, "dwg": dwg, "uploads": uploads,
            "handles": handles, "calls": calls, "readback": readback, "db": db_session, "client": client,
            "blockers": blockers}


def _row(gc):
    from app.models import ProjectRedesign

    gc["db"].expire_all()
    return gc["db"].get(ProjectRedesign, gc["row_id"])


def _apply(gc, **kw):
    return R.apply(gc["db"], gc["project"], gc["drawing"].id, None, **kw)


def _outputs(gc) -> list[Path]:
    folder = gc["uploads"] / "EP-40951" / "redesign"
    return sorted(p for p in folder.glob("*.dwg")) if folder.is_dir() else []


# --- 1-4: portable module resolution ---------------------------------------------------------


def test_ct1_ct2_and_cr_resolve_from_this_installations_library():
    for code in ("CT1", "CT2", "CR"):
        path = R.module_library(code, "x")
        assert path == (R.LIBRARY / f"{code}.dwg").resolve() and path.is_file() and path.parent == R.LIBRARY.resolve()


def test_a_stored_office_pc_path_never_reaches_the_script():
    changes = [_module("m1", "CT2", (10.0, 10.0)), _module("m2", "CT1", (11.0, 10.0)), _module("m3", "CR", (12.0, 10.0))]
    script = "\n".join(cad.script_lines(R.to_cad(changes), marker=0.6, text_height=0.25, nonce="ab12"))
    assert OFFICE not in script and "someone-else" not in script
    for code in ("CT1", "CT2", "CR"):
        assert f'"{code}={(R.LIBRARY / f"{code}.dwg").resolve().as_posix()}"' in script
    assert all(c["insert"]["library"].startswith(OFFICE) for c in changes)          # the stored history is kept


def test_an_unknown_module_code_is_refused():
    for code in ("CT9", "../CR", "cr", "", None):
        with pytest.raises(R.ApplyError):
            R.module_library(code, "m9")
    with pytest.raises(R.ApplyError, match="m9"):
        R.to_cad([_module("m9", "CT9", (1.0, 1.0))])


def test_a_missing_library_file_is_refused_before_autocad(gc, tmp_path, monkeypatch):
    lib = tmp_path / "library"
    lib.mkdir()
    (lib / "modules.json").write_text('{"modules": {"CT2": {}, "CR": {}}}', encoding="utf-8")
    (lib / "CR.dwg").write_bytes(b"x")
    with pytest.raises(R.ApplyError, match="CT2 module's file is missing") as exc:
        R.module_library("CT2", "m1", lib)
    assert OFFICE not in str(exc.value)
    monkeypatch.setattr(R, "LIBRARY", lib)
    with pytest.raises(R.ApplyError, match="missing"):
        _apply(gc)
    assert gc["calls"]["autocad"] == 0 and _outputs(gc) == []
    assert _row(gc).output_status == "failed"


# --- 5-8: approved only, confirmation ---------------------------------------------------------


def test_only_explicitly_approved_changes_are_drawn():
    placed = {"action": "add", "insert": {"block": "B"}, "remove": None}
    for status in ("proposed", "skipped", "failed", "pending", "rejected", "held", "uncertain", None, "APPROVED"):
        assert not R._drawn({**placed, "status": status}), status
        assert not R._drawn({**placed, "status": status, "source": "interface"}), status
    assert R._drawn({**placed, "status": "approved"}) and R._drawn({**placed, "status": "approved", "source": "interface"})
    assert not R._drawn({"action": "add", "insert": None, "remove": None, "status": "approved"})   # nothing to make


def test_proposed_and_skipped_changes_stay_out_of_the_apply(gc):
    result = _apply(gc)
    script = (gc["uploads"] / result["run"] / "redesign.scr").read_text(encoding="utf-8")
    assert all(f'"{cid}"' in script for cid in ("m1", "m2", "r1", "rm"))
    assert '"p1"' not in script and '"s1"' not in script
    assert '"c1"' not in script                                     # its spot not confirmed
    # the skipped low-confidence REMOVE is never erased; the approved one is (an exact erase step, not a
    # bare handle: ezdxf's short handles, such as "45", can occur inside the run's random nonce)
    assert f'(ep_erase "{gc["handles"]["other"]}" ' not in script
    assert f'(ep_erase "{gc["handles"]["speaker"]}" ' in script
    assert (result["inserts"], result["erases"]) == (3, 1)


def test_a_skipped_low_confidence_remove_like_rd_m1_f003_is_never_drawn():
    change = _review_remove("d89599", "5DD10", (1309.45, 155.68), status="skipped", confidence="low")
    assert not R._drawn(change)
    assert not R._drawn({**change, "status": "proposed"})


def test_a_spot_to_confirm_is_drawn_only_once_confirmed(gc):
    c1 = next(c for c in _row(gc).changes if c["id"] == "c1")
    assert R.requires_confirmation(c1) and not R._drawn(c1)
    assert R._drawn({**c1, "confirmed": True})
    assert not R.requires_confirmation({**c1, "moved": True})        # placed by the engineer: theirs
    view = R.view(gc["db"], gc["project"], gc["drawing"].id)
    shown = next(c for c in view["changes"] if c["id"] == "c1")
    assert shown["confirm"] and not shown["drawn"] and view["counts"]["drawn"] == 4
    R.adjust(gc["db"], gc["project"], gc["drawing"].id, "c1", confirmed=True)
    view = R.view(gc["db"], gc["project"], gc["drawing"].id)
    shown = next(c for c in view["changes"] if c["id"] == "c1")
    assert shown["confirmed"] and not shown["confirm"] and shown["drawn"] and view["counts"]["drawn"] == 5


# --- 9-12: fail-closed script, markers, output checks -------------------------------------------


def _script(changes, nonce="0f0f") -> list[str]:
    return cad.script_lines(R.to_cad(changes), marker=0.6, text_height=0.25, nonce=nonce)


def test_a_failed_insert_stops_before_any_entdel_or_save():
    lines = _script([_module("m1", "CT2", (10.0, 10.0)), _review_add("r1", "HEAT DETECTOR", (2.0, 2.0)),
                     _review_remove("rm", "5DD10", (3.0, 3.0))])
    body = [ln for ln in lines if ln.startswith("(") and not ln.startswith(("(defun", "(setq ep_", "(setvar", "(if (not (tblsearch"))]
    text = "\n".join(lines)
    assert "(entdel (entlast))" not in text
    # the only entdel outside the erase check is of the insert just checked to be new and of the block
    entdels = [ln for ln in lines if "(entdel " in ln and not ln.startswith("(defun ep_erase")]
    assert entdels and all("(setq ep_e (ep_new_insert ep_b " in ln for ln in entdels)
    # every step after the set-up is skipped once a step failed
    steps = [ln for ln in body if not ln.startswith(("(if ep_saved", '(if (and (not ep_failed)'))]
    assert steps and all(ln.startswith("(if (not ep_failed)") for ln in steps)
    # each insert is checked before the next step
    for k, ln in enumerate(lines):
        if '(command "_.-INSERT"' in ln:
            assert "(ep_new_insert ep_b " in lines[k + 1]
    # saved only when nothing failed and every insert and erase was counted
    assert "_.QSAVE" not in lines
    assert '(if (and (not ep_failed) (or (/= ep_ins 2) (/= ep_del 1))) (ep_fail "count" "all"))' in lines
    assert lines.index('(if (not ep_failed) (progn (command "_.QSAVE") (setq ep_saved T)))') > lines.index(
        '(if (and (not ep_failed) (or (/= ep_ins 2) (/= ep_del 1))) (ep_fail "count" "all"))')
    new_insert = next(ln for ln in lines if ln.startswith("(defun ep_new_insert"))
    assert '(not (eq e before))' in new_insert and '(= (cdr (assoc 0 d)) "INSERT")' in new_insert and "(strcase blk)" in new_insert


def test_an_insert_failure_in_autocad_publishes_nothing(gc, monkeypatch):
    monkeypatch.setenv("FAKE_ACAD_MODE", "fail")
    before = _sha(gc["dwg"])
    with pytest.raises(R.ApplyError, match="insert"):
        _apply(gc)
    row = _row(gc)
    assert row.output_status == "failed" and "did not verify" in row.output_error and row.output_path is None
    assert _outputs(gc) == [] and _sha(gc["dwg"]) == before and gc["calls"]["readback"] == 0
    run = next((gc["uploads"] / "EP-40951" / "redesign" / "runs").iterdir())
    assert (run / "autocad.log").is_file() and (run / "verification.json").is_file()   # kept as evidence


def test_an_erase_is_made_only_on_the_symbol_meant():
    lines = _script([_review_remove("rm", "5DD10", (1309.45, 155.68))])
    assert '(if (not ep_failed) (ep_erase "5DD10" "CEILING SPEAKER" 1309.450000 155.680000 0.010000 "rm"))' in lines
    erase = next(ln for ln in lines if ln.startswith("(defun ep_erase"))
    for check in ('(setq e (handent h))', '(= (cdr (assoc 0 d)) "INSERT")', "(strcase blk)", "(assoc 67 d)",
                  '"MODEL"', "(distance (list x y)", '(ep_fail "erase-target" id)', '(ep_fail "erase-verify" id)'):
        assert check in erase, check
    # not erasable (inside a block): marked only
    inside = _review_remove("rb", "BEEF", (1.0, 1.0))
    inside["remove"]["erasable"] = False
    assert "BEEF" not in "\n".join(_script([inside]))


def test_an_unexpected_erasure_in_the_read_back_fails_the_apply(gc):
    gc["readback"].mode = "extra_erasure"
    with pytest.raises(R.ApplyError, match="erased that no approved change erases"):
        _apply(gc)
    assert _outputs(gc) == [] and _row(gc).output_status == "failed"


def test_the_markers_are_this_runs_and_never_the_echo():
    nonce = "a1b2c3d4"
    echo = "\n".join(cad.script_lines([], marker=0.6, text_height=0.25, nonce=nonce))
    assert V.parse_log(echo, nonce) == {"failures": [], "ok": [], "nosave": 0}           # the echoed script is no outcome
    log = echo + f"\nEP-RD-OK:{nonce}:3:1\nEP-RD-OK:ffff:9:9\nEP-RD-FAIL:ffff:insert:x\n"
    parsed = V.parse_log(log, nonce)
    assert parsed["ok"] == [{"inserts": 3, "erases": 1}] and parsed["failures"] == []
    parsed = V.parse_log(f"EP-RD-FAIL:{nonce}:erase-target:rm\nEP-RD-NOSAVE:{nonce}\n", nonce)
    assert parsed["failures"] == [{"step": "erase-target", "change": "rm"}] and parsed["nosave"] == 1


@pytest.mark.parametrize("mode,readback,message", [
    ("unchanged", "faithful", "same as the source"),
    ("nomarker", "faithful", "completion marker is missing"),
    ("badexit", "faithful", "exited with code 3"),
    ("ok", "error", "could not be read back"),
    ("ok", "missing_insert", "approved insert"),
])
def test_an_unchanged_unreadable_or_incomplete_output_is_refused(gc, monkeypatch, mode, readback, message):
    monkeypatch.setenv("FAKE_ACAD_MODE", mode)
    gc["readback"].mode = readback
    with pytest.raises(R.ApplyError, match=message):
        _apply(gc)
    assert _outputs(gc) == [] and _row(gc).output_status == "failed" and _row(gc).output_path is None


# --- 13-15: unique names, no overwrite, relative paths ------------------------------------------


def test_two_applies_in_the_same_minute_get_two_files(gc):
    first = _apply(gc)
    second = _apply(gc, job_id=None)
    assert first["file"] != second["file"] and len(_outputs(gc)) == 2
    for result in (first, second):
        assert f"d{gc['drawing'].id}" in result["file"] and result["source_sha256"][:12] in result["file"]


def test_an_existing_output_is_never_overwritten(tmp_path):
    copy, dest = tmp_path / "copy.dwg", tmp_path / "out.dwg"
    copy.write_bytes(b"new")
    dest.write_bytes(b"earlier result")
    with pytest.raises(R.ApplyError, match="already exists"):
        R._publish(copy, dest)
    assert dest.read_bytes() == b"earlier result"


def test_the_output_is_stored_relative_and_read_back_safely(gc):
    result = _apply(gc)
    row = _row(gc)
    assert row.output_status == "made" and row.output_path == result["path"]
    assert not Path(row.output_path).is_absolute() and ":" not in row.output_path and not row.output_path.startswith("/")
    assert row.output_relative is None                                             # never filed in the project archive
    assert R.output_file_for(row.output_path, "40951") == (gc["uploads"] / row.output_path).resolve()
    for bad in ("../../outside.dwg", "EP-40951/../../outside.dwg", "C:/Windows/win.ini", "/etc/passwd"):
        assert R.output_file_for(bad, "40951") is None
    client = gc["client"]
    url = f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/output.dwg"
    response = client.get(url)
    assert response.status_code == 200 and response.content.endswith(b"EDITED")
    row.output_path = "../../../outside.dwg"
    gc["db"].commit()
    assert client.get(url).status_code == 404


def test_an_older_absolute_path_from_another_pc_is_found_under_this_uploads_folder(gc):
    legacy = gc["uploads"] / "EP-40951" / "redesign" / "FIRE ALARM LAYOUT R0 - Redesign 2026-10-02 1654.dwg"
    legacy.parent.mkdir(parents=True, exist_ok=True)
    legacy.write_bytes(b"made on another PC")
    stored = r"C:\Users\someone-else\OneDrive - Org\Desktop\dev\ep-platform\backend\uploads\EP-40951\redesign" \
             "\\" + legacy.name
    assert R.output_file_for(stored, "40951") == legacy.resolve()
    row = _row(gc)
    row.output_status, row.output_path = "made", stored
    gc["db"].commit()
    response = gc["client"].get(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/output.dwg")
    assert response.status_code == 200 and response.content == b"made on another PC"


# --- 16-19: recovery, source, cancellation, snapshot ----------------------------------------------


def test_a_completed_apply_is_not_run_again_after_worker_recovery(gc):
    """RD-M1 F017: job 119 had made its drawing when its worker stopped; the
    copied database still said 'running', and a new worker ran it again."""
    from app.ifc.services import processing, runners
    from app.models import BackgroundJob
    from app.services import jobs

    db = gc["db"]
    created = utc_now() - timedelta(hours=26)
    job = BackgroundJob(project_id=gc["pid"], kind=R.KIND_APPLY, status="running", progress={}, cancel_requested=False,
                        created_at=created, started_at=created, heartbeat_at=created + timedelta(seconds=68),
                        worker_id="ifc:OTHER-PC:1:1:0", attempts=0, params={"drawing_id": gc["drawing"].id, "user_id": 5})
    db.add(job)
    row = _row(gc)
    row.output_status, row.output_path = "made", "EP-40951/redesign/earlier.dwg"
    row.output_at = created + timedelta(seconds=76)
    db.commit()
    jobs.recover_stale(db, stale_after=timedelta(minutes=1))
    db.refresh(job)
    assert job.status == "queued" and job.attempts == 1                  # requeued, as before RD-M2
    with pytest.raises(processing.ReadError, match="already made"):
        runners.RUNNERS[R.KIND_APPLY](db, job, jobs.JobContext(job_id=job.id))
    row = _row(gc)
    assert gc["calls"]["autocad"] == 0 and row.output_status == "made" and row.output_path == "EP-40951/redesign/earlier.dwg"


def test_the_same_approved_set_is_not_made_twice_by_a_second_job(gc):
    from app.models import BackgroundJob

    result = _apply(gc, job_id=1)
    db = gc["db"]
    db.add(BackgroundJob(project_id=gc["pid"], kind=R.KIND_APPLY, status="succeeded", progress={},
                         cancel_requested=False, created_at=utc_now(), attempts=0, params={}, result=result))
    db.commit()
    with pytest.raises(R.ApplyRefused, match="already made by job"):
        _apply(gc, job_id=99)
    assert len(_outputs(gc)) == 1


def test_a_changed_source_is_refused(gc):
    request = R.apply_request(gc["db"], gc["project"], gc["drawing"])
    with pytest.raises(R.ApplyRefused, match="drawing changed"):
        _apply(gc, request={**request, "source_sha256": "0" * 64})
    gc["dwg"].write_bytes(b"STAND-IN SOURCE DWG, EDITED SINCE THE REVIEW")
    with pytest.raises(R.ApplyError, match="changed since it was reviewed"):
        _apply(gc)
    assert gc["calls"]["autocad"] == 0 and _outputs(gc) == []


def test_a_cancel_before_autocad_runs_nothing(gc):
    from app.services import jobs

    def cancel():
        raise jobs.Cancelled()

    before = _sha(gc["dwg"])
    with pytest.raises(jobs.Cancelled):
        _apply(gc, check=cancel)
    assert gc["calls"]["autocad"] == 0 and _outputs(gc) == [] and _sha(gc["dwg"]) == before
    assert _row(gc).output_status == "none"                  # nothing started: the output left as it was


def test_a_cancel_while_autocad_works_stops_it_and_publishes_nothing(gc, monkeypatch):
    from app.services import jobs

    monkeypatch.setenv("FAKE_ACAD_MODE", "slow")
    monkeypatch.setattr(cad, "POLL_S", 0.2)
    calls = {"n": 0}

    def check():
        calls["n"] += 1
        if calls["n"] >= 5:                       # a few polls into the AutoCAD run
            raise jobs.Cancelled()

    before = _sha(gc["dwg"])
    with pytest.raises(jobs.Cancelled):
        _apply(gc, check=check)
    row = _row(gc)
    assert gc["calls"]["autocad"] == 1 and row.output_status == "cancelled" and "nothing was published" in row.output_error
    assert _outputs(gc) == [] and _sha(gc["dwg"]) == before
    run = next((gc["uploads"] / "EP-40951" / "redesign" / "runs").iterdir())
    assert (run / "autocad.log").is_file()                     # the log kept


def test_approvals_changed_while_autocad_worked_are_not_published(gc, monkeypatch):
    from app.database import SessionLocal

    original = R._readback

    def engineer_approves_meanwhile(*args, **kw):
        db = SessionLocal()
        try:
            from app.models import ProjectRedesign

            row = db.get(ProjectRedesign, gc["row_id"])
            row.changes = [{**c, "status": "approved"} if c["id"] == "p1" else c for c in row.changes]
            db.commit()
        finally:
            db.close()
        return original(*args, **kw)

    monkeypatch.setattr(R, "_readback", engineer_approves_meanwhile)
    with pytest.raises(R.ApplyStale, match="not published"):
        _apply(gc)
    row = _row(gc)
    assert row.output_status == "stale" and _outputs(gc) == []


def test_a_job_asked_for_before_the_approvals_changed_is_refused(gc):
    request = R.apply_request(gc["db"], gc["project"], gc["drawing"])
    row = _row(gc)
    row.changes = [{**c, "status": "skipped"} if c["id"] == "r1" else c for c in row.changes]
    gc["db"].commit()
    with pytest.raises(R.ApplyRefused, match="approvals or placings changed"):
        _apply(gc, request=request)
    assert gc["calls"]["autocad"] == 0


# --- 20: the successful path, end to end ---------------------------------------------------------


def test_the_approved_changes_are_made_checked_and_kept(gc):
    before = _sha(gc["dwg"])
    result = _apply(gc)
    row = _row(gc)
    out = (gc["uploads"] / row.output_path)
    assert row.output_status == "made" and row.output_changes == 4 and out.is_file()
    assert out.read_bytes().endswith(b"EDITED") and _sha(gc["dwg"]) == before
    run = gc["uploads"] / result["run"]
    assert {p.name for p in run.iterdir()} >= {"redesign.scr", "autocad.log", "verification.json", "readback.dxf"}
    assert not (run / "redesign.dwg").exists()                      # published, the work copy removed
    import json

    checks = json.loads((run / "verification.json").read_text(encoding="utf-8"))
    assert checks["ok"] and checks["readback"]["unexpected_erasures"] == [] and len(checks["readback"]["inserts_found"]) == 3
    assert checks["readback"]["erased_as_expected"] == [gc["handles"]["speaker"]]


def test_the_page_says_a_proposed_change_is_not_drawn_and_asks_for_approval_before_an_apply(gc):
    client = gc["client"]
    base = f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}"
    view = client.get(base).json()
    assert view["counts"]["drawn"] == 4 and view["counts"]["proposed"] == 1
    assert next(c for c in view["changes"] if c["id"] == "p1")["drawn"] is False
    assert client.patch(f"{base}/changes/c1", json={"confirmed": True}).json()["counts"]["drawn"] == 5
    started = client.post(f"{base}/apply/jobs")
    assert started.status_code == 202
    from app.models import BackgroundJob

    job = gc["db"].query(BackgroundJob).filter(BackgroundJob.kind == R.KIND_APPLY).one()
    assert job.params["source_sha256"] == _row(gc).source_sha256 and len(job.params["fingerprint"]) == 64
    assert job.params["drawn"] == 5


def test_nothing_approved_means_no_apply_job(gc):
    row = _row(gc)
    row.changes = [{**c, "status": "proposed"} for c in row.changes]
    gc["db"].commit()
    response = gc["client"].post(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/apply/jobs")
    assert response.status_code == 422 and "approve" in response.json()["detail"]


def test_the_source_is_read_back_by_the_same_converter_once_per_source(gc):
    """Copy and source are compared like for like: both read back by this PC's converter,
    the source once per hash (not the DXF another PC's converter made)."""
    _apply(gc)
    folder = gc["uploads"] / "EP-40951" / "redesign"
    cached = list(folder.glob("source-readback-*.dxf"))
    assert len(cached) == 1 and cached[0].name == f"source-readback-{_sha(gc['dwg'])[:16]}.dxf"
    assert gc["calls"]["readback"] == 2                       # the source, then the copy
    _apply(gc)
    assert gc["calls"]["readback"] == 3                       # only the new copy


def test_the_core_consoles_echo_of_a_printed_marker_is_not_a_second_outcome():
    """Seen in the RD-M2 AutoCAD validation on GC-01: the marker is printed, then the
    expression's value is echoed as a quoted string. One outcome, not two."""
    nonce = "52a556553816824b"
    # the echoed value is a LISP string as AutoCAD prints it: a backslash and "n", not a line break
    log = ('Command: (if ep_saved (princ (strcat "\\n" "EP-RD" "-OK:" ep_nonce ":" (itoa ep_ins) ":" '
           '(itoa ep_del) "\\n")) (princ (strcat "\\n" "EP-RD" "-NOSAVE:" ep_nonce "\\n")))\r\n\r\n'
           f'EP-RD-OK:{nonce}:11:0\r\n"\\nEP-RD-OK:{nonce}:11:0\\n"\r\n\r\nCommand: _.QUIT\r\n')
    assert '"\\nEP-RD-OK:' in log and log.count("\n") == 6      # the quoted echo is on one line, as in the real log
    assert V.parse_log(log, nonce) == {"failures": [], "ok": [{"inserts": 11, "erases": 0}], "nosave": 0}


def test_a_script_cancelled_by_autocad_has_no_outcome_and_is_refused(tmp_path):
    """Seen in the RD-M2 AutoCAD validation: a failed -INSERT ends the whole script
    ("; error: Function cancelled"), AutoCAD exits 0, nothing is saved, no marker is printed."""
    nonce = "54912c00e717f76f"
    log = ("Command: (if (not ep_failed) (command \"_.-INSERT\" \"RDM2-MISSING-BLOCK\" \"_S\" 1.0 (list 716.0 158.0 0.0) 0.0))\r\n"
           "\"RDM2-MISSING-BLOCK.dwg\": Can't find file in search path:\r\n*Invalid*\r\n; error: Function cancelled\r\n")
    copy = tmp_path / "redesign.dwg"
    copy.write_bytes(b"same as the source")
    run = cad.CadRun(work=tmp_path, copy=copy, script=tmp_path / "s.scr", log_path=tmp_path / "l.log", log=log, nonce=nonce,
                     returncode=0, expected_inserts=12, expected_erases=0, seconds=11.6,
                     source_sha256=_sha(copy), copy_sha256=_sha(copy))
    result = V.verify(run, expect={"erase": [], "insert": []}, readback=None)
    assert not result.ok
    assert "AutoCAD's completion marker is missing." in result.problems
    assert "The redesigned copy is the same as the source: nothing was saved." in result.problems

# --- RDM2-R1: publication is serialized with approval writes -----------------------------


def test_publication_lock_blocks_an_approval_write_until_the_result_commits(tmp_path):
    """The lock used around final snapshot + publish is a real database lock,
    not an in-process mutex: another session cannot commit an approval inside
    the publication window."""
    import threading
    import time

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import ProjectRedesign

    engine = create_engine(f"sqlite:///{tmp_path / 'publish-lock.db'}",
                           connect_args={"check_same_thread": False, "timeout": 3})
    ProjectRedesign.__table__.create(engine)
    Sessions = sessionmaker(bind=engine)
    setup = Sessions()
    row = ProjectRedesign(project_id=1, drawing_id=1, status="planned", changes=[], symbols=[])
    setup.add(row)
    setup.commit()
    row_id = row.id
    setup.close()

    publisher = Sessions()
    locked = R._locked_publish_row(publisher, row_id)
    assert locked.id == row_id
    attempted = threading.Event()
    committed = threading.Event()
    errors = []

    def approve():
        other = Sessions()
        try:
            changed = other.get(ProjectRedesign, row_id)
            changed.changes = [{"id": "late", "status": "approved"}]
            attempted.set()
            other.commit()
            committed.set()
        except Exception as exc:  # pragma: no cover - reported by the assertion
            errors.append(exc)
        finally:
            other.close()

    thread = threading.Thread(target=approve, daemon=True)
    thread.start()
    assert attempted.wait(1)
    time.sleep(0.15)
    assert not committed.is_set()                   # blocked inside the publication transaction
    publisher.commit()
    thread.join(2)
    assert not errors and committed.is_set()
    check = Sessions()
    try:
        assert check.get(ProjectRedesign, row_id).changes == [{"id": "late", "status": "approved"}]
    finally:
        check.close()
        engine.dispose()


def test_a_commit_failure_after_exclusive_publication_removes_the_output(gc, monkeypatch):
    """A file does not remain published when its database state cannot commit."""
    db = gc["db"]
    real_commit = db.commit
    failed = False

    def fail_final_commit_once():
        nonlocal failed
        row = db.get(__import__("app.models", fromlist=["ProjectRedesign"]).ProjectRedesign, gc["row_id"])
        if not failed and row.output_status == "made":
            failed = True
            raise RuntimeError("scripted final commit failure")
        return real_commit()

    monkeypatch.setattr(db, "commit", fail_final_commit_once)
    with pytest.raises(RuntimeError, match="scripted final commit failure"):
        _apply(gc)
    assert failed and _outputs(gc) == []
    row = _row(gc)
    assert row.output_status == "failed" and "scripted final commit failure" in row.output_error


# =====================================================================================================
# M5 (ORCH-039): the port onto the current preparation code, and the disposition's corrections
# =====================================================================================================

import json  # noqa: E402
import os  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402

# readiness() as the service defines it, kept before any fixture stands in for it
REAL_READINESS = R.readiness


def _session_project(gc):
    """A second, real connection to the test database (a file in WAL mode),
    with the project as that session sees it."""
    from app.database import SessionLocal
    from app.models import Project

    db = SessionLocal()
    return db, db.get(Project, gc["pid"])


def _status_of(cid: str, gc) -> str:
    return next(c for c in _row(gc).changes if c["id"] == cid)["status"]


def _publish_folder_files(gc) -> list[str]:
    folder = gc["uploads"] / "EP-40951" / "redesign"
    return sorted(p.name for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []


def _apply_in_thread(gc, out: dict, **kw):
    """apply() on a connection of its own, in a thread, as the IFC worker runs it."""
    def work():
        db, project = _session_project(gc)
        try:
            out["result"] = R.apply(db, project, gc["drawing"].id, None, **kw)
        except BaseException as exc:  # noqa: BLE001 -- reported by the test
            out["error"] = exc
        finally:
            db.close()
    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    return thread


def _approve_in_thread(gc, cid: str, out: dict):
    """The engineer's PATCH (service.adjust, as the route calls it) on another
    connection -- bypassing the 409 guard, which is a check-then-act
    convenience, to reach the publication window (U2M5-19)."""
    def work():
        db, project = _session_project(gc)
        try:
            out["started"] = time.monotonic()
            R.adjust(db, project, gc["drawing"].id, cid, status="approved")
            out["done"] = time.monotonic()
        except BaseException as exc:  # noqa: BLE001
            out["error"] = exc
        finally:
            db.close()
    thread = threading.Thread(target=work, daemon=True)
    thread.start()
    return thread


def test_the_test_database_is_a_file_in_wal_mode_with_the_apps_busy_timeout(gc):
    from sqlalchemy import text as sql

    from app.database import SQLITE_BUSY_TIMEOUT_S

    db, _project = _session_project(gc)
    try:
        assert db.execute(sql("PRAGMA journal_mode")).scalar() == "wal"
        assert db.execute(sql("PRAGMA busy_timeout")).scalar() == SQLITE_BUSY_TIMEOUT_S * 1000
        assert db.get_bind().url.database not in (None, "", ":memory:")
    finally:
        db.close()


def test_concurrent_publication_an_edit_started_inside_the_window_waits_and_its_approval_is_kept(gc, monkeypatch):
    """(a) An approval PATCH started while Apply is inside the publication
    transaction (after the final compare, at the rename) cannot commit until
    Apply has committed; the output is made from the pre-PATCH snapshot and
    the new approval is kept. With the lock removed this test FAILS (the
    PATCH commits inside the window): mutation evidence in the M5 package."""
    fingerprint_before = R.content_fingerprint(_row(gc), _row(gc).source_sha256)
    inside, release = threading.Event(), threading.Event()
    original = R._finalize

    def held_finalize(part, dest):
        inside.set()
        assert release.wait(30)
        return original(part, dest)

    monkeypatch.setattr(R, "_finalize", held_finalize)
    applied: dict = {}
    approved: dict = {}
    a = _apply_in_thread(gc, applied)
    assert inside.wait(60), applied.get("error")
    b = _approve_in_thread(gc, "p1", approved)
    time.sleep(1.5)                                  # the PATCH has had every chance to commit
    blocked = "done" not in approved and "error" not in approved
    release.set()
    a.join(60)
    b.join(60)
    assert blocked, "an approval committed inside the publication window"
    assert "error" not in applied, applied.get("error")
    assert "error" not in approved, approved.get("error")
    result = applied["result"]
    row = _row(gc)
    assert row.output_status == "made" and row.output_path == result["path"]
    assert result["fingerprint"] == fingerprint_before                 # made from the pre-PATCH snapshot
    assert _status_of("p1", gc) == "approved"                          # the newer approval kept
    assert R.content_fingerprint(row, row.source_sha256) != fingerprint_before
    assert len(_outputs(gc)) == 1


def test_concurrent_publication_an_edit_committed_before_the_lock_makes_the_apply_stale_and_writes_nothing(gc,
                                                                                                         monkeypatch):
    """(b) A PATCH committed after the read-back, before the lock: Apply is
    stale, no output file is left in the output folder (nor its staged
    copy), and the newer approval is kept."""
    original = R._stage

    def stage_then_engineer_approves(source, dest):
        staged = original(source, dest)
        approved: dict = {}
        _approve_in_thread(gc, "p1", approved).join(30)
        assert "done" in approved, approved.get("error")
        return staged

    monkeypatch.setattr(R, "_stage", stage_then_engineer_approves)
    applied: dict = {}
    _apply_in_thread(gc, applied).join(120)
    assert isinstance(applied.get("error"), R.ApplyStale), applied
    row = _row(gc)
    assert row.output_status == "stale" and row.output_path is None
    assert _outputs(gc) == [] and not [n for n in _publish_folder_files(gc) if n.endswith(".part")]
    assert _status_of("p1", gc) == "approved"


def test_the_dwg_copy_holds_no_database_lock_a_writer_to_another_table_is_not_blocked(gc, monkeypatch):
    """U2M5-02: the slow copy is staged before the publication lock, so a
    write to an unrelated table (another drawing's job progress, here an
    activity event) is not blocked while it runs."""
    from app.models import ActivityEvent, User

    copying, release = threading.Event(), threading.Event()
    original = R._stage

    def slow_stage(source, dest):
        copying.set()
        assert release.wait(30)
        return original(source, dest)

    monkeypatch.setattr(R, "_stage", slow_stage)
    applied: dict = {}
    a = _apply_in_thread(gc, applied)
    assert copying.wait(60), applied.get("error")
    db, _project = _session_project(gc)
    try:
        user = db.query(User).first()
        t0 = time.monotonic()
        db.add(ActivityEvent(user_id=user.id, action="test.write", summary="an unrelated write"))
        db.commit()
        waited = time.monotonic() - t0
    finally:
        db.close()
    release.set()
    a.join(60)
    assert waited < 1.0, f"an unrelated write waited {waited:.2f} s during the copy"
    assert "error" not in applied and _row(gc).output_status == "made"


def test_a_failed_attempt_and_a_stale_one_leave_the_earlier_copy_downloadable(gc, monkeypatch):
    """U2M5-09: the earlier valid output stays reachable from the page."""
    first = _apply(gc)
    url = f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}"
    earlier = gc["client"].get(f"{url}/output.dwg").content
    monkeypatch.setenv("FAKE_ACAD_MODE", "fail")
    with pytest.raises(R.ApplyError):
        _apply(gc)
    row = _row(gc)
    assert row.output_status == "failed" and row.output_path == first["path"]
    assert gc["client"].get(f"{url}/output.dwg").content == earlier
    view = gc["client"].get(url).json()
    assert view["output"]["status"] == "failed" and view["output"]["available"] is True
    assert view["output"]["file"] == first["file"]
    # stale: approvals changed while it was made
    monkeypatch.setenv("FAKE_ACAD_MODE", "ok")
    original = R._readback

    def meanwhile(*args, **kw):
        db, _project = _session_project(gc)
        try:
            from app.models import ProjectRedesign

            other = db.get(ProjectRedesign, gc["row_id"])
            other.changes = [{**c, "status": "skipped"} if c["id"] == "p1" else c for c in other.changes]
            db.commit()
        finally:
            db.close()
        return original(*args, **kw)

    monkeypatch.setattr(R, "_readback", meanwhile)
    with pytest.raises(R.ApplyStale):
        _apply(gc)
    assert _row(gc).output_status == "stale" and _row(gc).output_path == first["path"]
    assert gc["client"].get(f"{url}/output.dwg").content == earlier


# --- readiness: the first refusal, in the job and at the server boundary -------------------------


def test_a_drawing_not_ready_is_refused_by_the_apply_job_before_anything_runs(gc):
    first = _apply(gc)
    gc["blockers"].append("2 placements the agents proposed to approve or skip.")
    with pytest.raises(R.ApplyRefused, match="not ready for the draftsman: 2 placements"):
        _apply(gc)
    row = _row(gc)
    assert gc["calls"]["autocad"] == 1                                   # only the first Apply ran AutoCAD
    assert row.output_status == "refused" and "2 placements" in row.output_error
    assert row.output_path == first["path"]                              # the earlier copy kept


def test_the_apply_endpoint_refuses_with_422_when_not_ready_and_queues_nothing(gc):
    from app.models import BackgroundJob

    gc["blockers"].extend(["The drawing review is in progress: 3 of 9 rooms reviewed.",
                           "1 change the orchestrator rejected or asked the engineer to check."])
    response = gc["client"].post(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/apply/jobs")
    assert response.status_code == 422
    assert "Not ready for the draftsman" in response.json()["detail"] and "orchestrator rejected" in response.json()["detail"]
    assert gc["db"].query(BackgroundJob).filter(BackgroundJob.kind == R.KIND_APPLY).count() == 0


def _review_view(state="done", reviewed=9, rooms=9, open_=0, findings=None, pairs=None):
    return {"state": state, "counts": {"reviewed": reviewed, "rooms": rooms, "open": open_},
            "findings": findings if findings is not None else [], "possible_duplicate_pairs": pairs or []}


def _ready_changes() -> list[dict]:
    return [_review_add("r1", "HEAT DETECTOR", (20.0, 20.0))]


def test_readiness_names_every_blocker_and_is_ready_only_when_none_is_left(gc, monkeypatch):
    """Every readiness() blocker, one at a time, against the real function
    (the review's view stubbed); and an unconfirmed approved spot, the
    blocker the port adds."""
    from app.models import ProjectRedesign
    from app.redesign import prepare as PR
    from app.review import service as review

    real = REAL_READINESS                                # the real readiness(), not the fixture's stand-in
    accepted = [{"id": "r1", "decision": "accepted", "action": "add"}]
    project, drawing = gc["project"], gc["drawing"]

    def check(view, changes, run=None, drawing_=drawing) -> list[str]:
        monkeypatch.setattr(review, "build", lambda db, p, d: view)
        row = ProjectRedesign(project_id=gc["pid"], drawing_id=drawing.id, changes=changes, symbols=[], run=run)
        return real(gc["db"], project, drawing_, row)["blockers"]

    assert check(_review_view(findings=accepted), _ready_changes()) == []
    assert real(gc["db"], project, None, ProjectRedesign(changes=[]))["blockers"] == ["The drawing is not on file."]
    cases = [
        (_review_view(state="in_progress", reviewed=3, findings=accepted), _ready_changes(), None,
         "The drawing review is in progress: 3 of 9 rooms reviewed."),
        (_review_view(open_=2, findings=accepted), _ready_changes(), None, "2 review findings are still undecided."),
        (_review_view(findings=accepted + [{"id": "x", "decision": "accepted", "action": "note"}],
                      pairs=[{"a": "r1", "b": "x"}]), _ready_changes(), None, "1 possible duplicate pair to settle"),
        (_review_view(findings=[]), _ready_changes(), None, "1 placed change is no longer accepted in the review"),
        (_review_view(findings=accepted + [{"id": "r2", "decision": "accepted", "action": "add"}]), _ready_changes(),
         None, "1 accepted finding is not placed yet"),
        (_review_view(findings=accepted + [{"id": "r3", "decision": "accepted", "action": "add"}]),
         _ready_changes() + [_review_add("r3", "HEAT DETECTOR", (1.0, 1.0), status="proposed")], None,
         "1 placement the agents proposed to approve or skip."),
        (_review_view(findings=accepted), _ready_changes() + [{**_review_add("cv", "SD", (1.0, 1.0), status="proposed"),
                                                               "source": PR.COVERAGE}], None,
         "1 extra detector proposed for coverage to approve or skip."),
        (_review_view(findings=accepted), _ready_changes() + [_module("m9", "CR", (1.0, 1.0), status="proposed")], None,
         "1 interface module to approve or skip."),
        (_review_view(findings=accepted), _ready_changes() + [{**_module("m8", "CR", (1.0, 1.0)), "status": "failed"}],
         None, "1 change could not be placed."),
        (_review_view(findings=accepted), _ready_changes() + [{**_module("m7", "CR", (1.0, 1.0), status="skipped"),
                                                               "status": "pending", "check": {"verdict": "reject"}}],
         None, "1 change the orchestrator rejected or asked the engineer to check."),
        (_review_view(findings=accepted + [{"id": "c1", "decision": "accepted", "action": "add"}]),
         _ready_changes() + [_review_add("c1", "HEAT DETECTOR", (35.0, 35.0), residual=1.5)], None,
         "1 approved spot placed less exactly than 1 m to confirm (or move) before it is drawn."),
        (_review_view(findings=accepted), _ready_changes(), {"coordination": {"gaps_left": 2}},
         "At the last plan, 2 room(s) short of detector coverage."),
        (_review_view(findings=accepted), _ready_changes(), {"coordination": {"open_rooms": 1}},
         "At the last plan, 1 room(s) whose coverage could not be measured."),
        (_review_view(findings=accepted), _ready_changes(), {"gate": {"reasons": ["1 detector on a column"]}},
         "At the last plan: 1 detector on a column."),
        (_review_view(findings=accepted), [{**_review_add("r1", "HEAT DETECTOR", (20.0, 20.0)), "placeholder": True}],
         None, "1 change without a symbol in the drawing."),
        (_review_view(findings=accepted), _ready_changes(), {"review": {"state": "partial"}},
         "The orchestrator's review did not finish on every floor at the last plan."),
        (_review_view(findings=accepted), [{**_review_add("r1", "HEAT DETECTOR", (20.0, 20.0)), "status": "skipped"}],
         None, "No approved change to make."),
    ]
    for view, changes, run, expected in cases:
        blockers = check(view, changes, run)
        assert any(b.startswith(expected) for b in blockers), (expected, blockers)
    # the unconfirmed spot, confirmed: ready
    confirmed = [{**_review_add("c1", "HEAT DETECTOR", (35.0, 35.0), residual=1.5), "confirmed": True}]
    assert check(_review_view(findings=[{"id": "c1", "decision": "accepted", "action": "add"}]), confirmed) == []


def test_the_real_readiness_refuses_this_fixtures_proposed_and_unconfirmed_changes(gc, monkeypatch):
    """With readiness() itself (not the fixture's stand-in), the fixture's
    redesign -- one proposed change, one unconfirmed spot -- is refused at the
    endpoint with 422 and inside the job, AutoCAD never started."""
    from app.review import service as review

    monkeypatch.setattr(R, "readiness", REAL_READINESS)
    findings = [{"id": i, "decision": "accepted", "action": "add"} for i in ("r1", "p1", "c1")] + \
               [{"id": i, "decision": "accepted", "action": "remove"} for i in ("rm", "s1")]
    monkeypatch.setattr(review, "build", lambda db, p, d: _review_view(findings=findings))
    row = _row(gc)
    blockers = R.readiness(gc["db"], gc["project"], gc["drawing"], row)["blockers"]
    assert any("placement the agents proposed" in b for b in blockers)
    assert any("approved spot placed less exactly" in b for b in blockers)
    response = gc["client"].post(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/apply/jobs")
    assert response.status_code == 422 and "agents proposed" in response.json()["detail"]
    with pytest.raises(R.ApplyRefused, match="not ready"):
        _apply(gc)
    assert gc["calls"]["autocad"] == 0


# --- coordination: Apply makes what was approved, as it was approved ----------------------------


def test_apply_never_places_or_coordinates_again_and_leaves_the_stored_changes_as_they_were(gc, monkeypatch):
    before = json.dumps(_row(gc).changes, sort_keys=True)

    def must_not_run(*_a, **_k):
        raise AssertionError("Apply placed or coordinated the changes again")

    for name in ("coordinate", "refresh", "_place", "_place_module", "_measure_again"):
        monkeypatch.setattr(R, name, must_not_run)
    result = _apply(gc)
    assert result["changes"] == 4 and json.dumps(_row(gc).changes, sort_keys=True) == before


def test_a_change_placed_by_an_earlier_version_is_refused_not_placed_again(gc):
    row = _row(gc)
    row.changes = [{**c, "insert": {k: v for k, v in c["insert"].items() if k != "placed"}} if c["id"] == "r1" else c
                   for c in row.changes]
    gc["db"].commit()
    with pytest.raises(R.ApplyError, match="placed by an earlier version"):
        _apply(gc)
    assert gc["calls"]["autocad"] == 0 and _outputs(gc) == []


def test_a_moved_approved_change_stays_approved_and_its_confirmation_is_asked_again(gc, monkeypatch):
    """adjust(): an approved change, moved, stays approved (preserved); a
    spot confirmed, then placed again, needs confirming again (RD-M2)."""
    from app.models import ProjectDrawingReview

    sheet = {"index": 0, "name": "FA 101", "plan": [0, 0, 2000, 2000],
             "geometry": {"v": 1, "a": 0.1, "bx": 0.0, "by": 0.0, "residual": 1.5}}
    gc["db"].add(ProjectDrawingReview(project_id=gc["pid"], drawing_id=gc["drawing"].id, status="done",
                                      sheets=[sheet], decisions={}))
    row = _row(gc)
    symbols = [{"id": 2, "name": "Heat Detector", "code": "HD", "block": "HEAT DETECTOR", "layer": "fa", "scale": 1.0,
                "scales": {}, "count": 3}]
    row.symbols = symbols
    row.changes = [{**c, "box": [100, 100, 300, 300], "insert": {**c["insert"], "symbol": 2, "page": [200, 200]},
                    "confirmed": True} if c["id"] == "c1" else c for c in row.changes]
    gc["db"].commit()
    monkeypatch.setattr(R, "_walls", lambda *a, **k: None)
    from app.redesign import prepare as PR

    monkeypatch.setattr(PR, "columns", lambda *a, **k: None)
    changed = R.adjust(gc["db"], gc["project"], gc["drawing"].id, "c1", rotation=90)
    assert changed["status"] == "approved" and "confirmed" not in changed      # re-placed: confirm again
    assert changed["status"] == "approved" and R.requires_confirmation(changed) and not R._drawn(changed)
    moved = R.adjust(gc["db"], gc["project"], gc["drawing"].id, "c1", point=[0.4, 0.6])
    assert moved["status"] == "approved" and moved["moved"] and R._drawn(moved)  # the engineer's own spot


def test_the_409_guard_on_edits_while_an_apply_job_runs_is_kept(gc):
    from app.services import jobs

    job, _created = jobs.enqueue(gc["db"], kind=R.KIND_APPLY, project_id=gc["pid"], user_id=None,
                                 dedup_key=f"{R.KIND_APPLY}:{gc['pid']}:{gc['drawing'].id}",
                                 params={"drawing_id": gc["drawing"].id}, progress={}, message="")
    response = gc["client"].patch(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/changes/p1",
                                  json={"status": "approved"})
    assert response.status_code == 409 and _status_of("p1", gc) == "proposed"


# --- library paths: resolved from the active library when the script is made (OD-17 b) ------------


def _library(folder: Path, codes=("CT1", "CT2", "CR")) -> Path:
    folder.mkdir(parents=True)
    (folder / "modules.json").write_text(json.dumps({"modules": {c: {} for c in codes}}), encoding="utf-8")
    for code in codes:
        (folder / f"{code}.dwg").write_bytes(b"block " + code.encode())
    return folder


def test_library_paths_with_spaces_are_resolved_at_script_time_from_the_active_library(gc, tmp_path, monkeypatch):
    spaced = _library(tmp_path / "Redesign library (copy) with spaces")
    other = _library(tmp_path / "another installation" / "library")
    stored = json.dumps(_row(gc).changes, sort_keys=True)
    monkeypatch.setattr(R, "LIBRARY", spaced)
    first = "\n".join(_script([_module("m1", "CT2", (10.0, 10.0))]))
    assert f'"CT2={(spaced / "CT2.dwg").resolve().as_posix()}"' in first and " with spaces/CT2.dwg" in first
    monkeypatch.setattr(R, "LIBRARY", other)                    # the active library changed: so does the script
    second = "\n".join(_script([_module("m1", "CT2", (10.0, 10.0))]))
    assert f'"CT2={(other / "CT2.dwg").resolve().as_posix()}"' in second and "with spaces" not in second
    # through Apply: the run's own script names the active library's file; the stored paths are untouched
    monkeypatch.setattr(R, "LIBRARY", spaced)
    result = _apply(gc)
    script = (gc["uploads"] / result["run"] / "redesign.scr").read_text(encoding="utf-8")
    assert f'"CR={(spaced / "CR.dwg").resolve().as_posix()}"' in script and OFFICE not in script
    assert json.dumps(_row(gc).changes, sort_keys=True) == stored


# --- no archive write by Apply; publication is a separate, explicit action (OD-15 a) --------------


def _archive(gc, tmp_path) -> Path:
    archive = tmp_path / "archive" / "EP-40951 Tower"
    archive.mkdir(parents=True)
    project = gc["project"]
    project.source_folder_path = str(archive)
    gc["db"].commit()
    return archive


def _succeeded(gc, result: dict):
    from app.models import BackgroundJob

    job = BackgroundJob(project_id=gc["pid"], kind=R.KIND_APPLY, status="succeeded", progress={},
                        cancel_requested=False, created_at=utc_now(), attempts=0, params={}, result=result)
    gc["db"].add(job)
    gc["db"].commit()
    return job


def test_apply_never_writes_into_the_project_archive(gc, tmp_path):
    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    assert list(archive.rglob("*")) == []                       # nothing at all: not even the folder
    row = _row(gc)
    assert row.output_relative is None and "filed" not in result
    assert (gc["uploads"] / row.output_path).is_file()


def test_publishing_to_the_archive_is_explicit_unique_never_overwrites_and_is_recorded(gc, tmp_path):
    from app.models import ActivityEvent

    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    job = _succeeded(gc, result)
    url = f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/publish"
    response = gc["client"].post(url, json={})
    assert response.status_code == 200, response.text
    published = response.json()["published"]
    target = archive / R.FOLDER / result["file"]
    assert target.is_file() and target.read_bytes() == (gc["uploads"] / result["path"]).read_bytes()
    assert published["archive"] == f"{R.FOLDER}/{result['file']}" and published["job_id"] == job.id
    assert published["sha256"] == _sha(target) and published["by"] is not None and published["at"]
    assert not [p for p in (archive / R.FOLDER).iterdir() if p.name.endswith(".part")]
    assert response.json()["output"]["relative"] == published["archive"]           # "published separately"
    event = gc["db"].query(ActivityEvent).filter(ActivityEvent.action == "redesign.published").one()
    assert event.user_id == published["by"] and event.at is not None
    assert event.detail["archive"] == published["archive"] and event.detail["sha256"] == published["sha256"]
    # the same name again: refused, the archive copy untouched
    before = target.read_bytes()
    again = gc["client"].post(url, json={"output": result["path"]})
    assert again.status_code == 409 and "nothing was overwritten" in again.json()["detail"]
    assert target.read_bytes() == before
    assert gc["db"].query(ActivityEvent).filter(ActivityEvent.action == "redesign.published").count() == 1


def test_only_a_verified_copy_can_be_published_and_only_where_there_is_an_archive(gc, tmp_path):
    url = f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/publish"
    assert gc["client"].post(url, json={}).status_code == 422                       # nothing made yet
    result = _apply(gc)
    assert gc["client"].post(url, json={}).status_code == 422                       # no archive folder
    archive = _archive(gc, tmp_path)
    # made, but no succeeded Apply job vouches for it: not published
    response = gc["client"].post(url, json={})
    assert response.status_code == 422 and "verified" in response.json()["detail"]
    # a legacy copy from before M5 (no job, no checks): not published
    legacy = gc["uploads"] / "EP-40951" / "redesign" / "FA LAYOUT R0 - Redesign 2026-10-02 1654.dwg"
    legacy.write_bytes(b"made by the old Apply")
    assert gc["client"].post(url, json={"output": "EP-40951/redesign/" + legacy.name}).status_code == 422
    # its checks say it did not verify: not published
    job = _succeeded(gc, result)
    checks = gc["uploads"] / result["run"] / "verification.json"
    data = json.loads(checks.read_text(encoding="utf-8"))
    checks.write_text(json.dumps({**data, "ok": False}), encoding="utf-8")
    assert gc["client"].post(url, json={}).status_code == 422
    checks.write_text(json.dumps(data), encoding="utf-8")
    assert gc["client"].post(url, json={}).status_code == 200 and job.id
    assert [p.name for p in (archive / R.FOLDER).iterdir()] == [result["file"]]
    # outside the uploads folder: never
    assert gc["client"].post(url, json={"output": "../../outside.dwg"}).status_code == 404


def test_publish_needs_an_editor(gc, tmp_path):
    from app.models import RoleEnum
    from tests.conftest import login, make_user

    archive = _archive(gc, tmp_path)
    _succeeded(gc, _apply(gc))
    make_user(gc["db"], "viewer@example.com", RoleEnum.viewer)
    assert login(gc["client"], "viewer@example.com").status_code == 200
    assert gc["client"].post(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/publish", json={}).status_code == 403
    assert list(archive.rglob("*")) == []


# --- the orphan sweep (U2M5-04) -------------------------------------------------------------------


def _old(path: Path) -> Path:
    stamp = time.time() - 3600
    os.utime(path, (stamp, stamp))
    return path


def test_the_sweep_removes_staged_copies_and_sets_aside_unreferenced_outputs_after_a_crash(gc):
    """A stop between the exclusive rename and the commit leaves a final-named
    output no record refers to; a stop during the copy leaves a staged
    ".part". The sweep removes the staged copy, moves the orphan aside (never
    deletes a DWG), and leaves every referenced output, the run folders and
    the legacy outputs alone."""
    result = _apply(gc)                                         # a referenced output
    _succeeded(gc, result)
    folder = gc["uploads"] / "EP-40951" / "redesign"
    orphan_name = R._unique_output(folder, gc["drawing"], "ab" * 32, "j7-0123456789").name
    orphan = folder / orphan_name
    orphan.write_bytes(b"verified, renamed, never committed")
    _old(orphan)
    part = folder / f".{orphan_name}{R.PART}"
    part.write_bytes(b"half a copy")
    _old(part)
    legacy = folder / "FA LAYOUT R0 - Redesign 2026-10-02 1654.dwg"
    legacy.write_bytes(b"old")
    _old(legacy)
    fresh = folder / f".fresh.dwg{R.PART}"
    fresh.write_bytes(b"being written now")                   # too new: an Apply may be copying it
    _old(gc["uploads"] / result["path"])
    done = R.sweep_orphans(gc["db"])
    assert done == {"parts_removed": 1, "outputs_moved": 1}
    assert not part.exists() and not orphan.exists() and (folder / R.ORPHANED / orphan_name).read_bytes().startswith(b"verified")
    assert (gc["uploads"] / result["path"]).is_file() and legacy.is_file() and fresh.is_file()
    assert (gc["uploads"] / result["run"]).is_dir()
    assert R.sweep_orphans(gc["db"]) == {"parts_removed": 0, "outputs_moved": 0}


def test_the_sweep_leaves_a_project_alone_while_its_apply_runs(gc):
    from app.services import jobs

    folder = gc["uploads"] / "EP-40951" / "redesign"
    folder.mkdir(parents=True, exist_ok=True)
    part = folder / f".x.dwg{R.PART}"
    part.write_bytes(b"copy in progress")
    _old(part)
    jobs.enqueue(gc["db"], kind=R.KIND_APPLY, project_id=gc["pid"], user_id=None,
                 dedup_key=f"{R.KIND_APPLY}:{gc['pid']}:{gc['drawing'].id}", params={}, progress={}, message="")
    assert R.sweep_orphans(gc["db"]) == {"parts_removed": 0, "outputs_moved": 0} and part.exists()


def test_the_ifc_worker_sweeps_the_redesign_outputs_in_its_housekeeping(gc, monkeypatch):
    from app.workers import ifc_worker

    called = []
    monkeypatch.setattr(R, "sweep_orphans", lambda db, **kw: called.append(db) or {})
    worker = ifc_worker.IfcWorker.__new__(ifc_worker.IfcWorker)
    worker.slot = 0
    from app.database import SessionLocal

    worker.session_factory = SessionLocal
    worker.housekeeping()
    assert len(called) == 1


def test_service_py_has_no_byte_order_mark():
    raw = (Path(R.__file__)).read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")


# --- ORCH-041: the M5 verification's low findings (U2M5V-01..04, -07) ----------------------------


def test_an_approval_committed_between_the_request_check_and_the_making_write_is_refused_not_drawn(gc):
    """U2M5V-01 (probe P3): an approval committed after Apply's first look at
    the request and before its own "making" write was drawn -- Apply made the
    newer approved set, not the one it was asked for. The request is now
    checked again inside the serialized transaction that writes "making" and
    takes the snapshot: refused, nothing run, the newer approval kept."""
    request = R.apply_request(gc["db"], gc["project"], gc["drawing"])
    assert request["drawn"] == 4
    approved: dict = {}

    def check():
        if not approved:                              # the first check after the request's first look
            _approve_in_thread(gc, "p1", approved).join(30)
            assert "done" in approved, approved.get("error")

    applied: dict = {}
    _apply_in_thread(gc, applied, request=request, check=check).join(120)
    assert isinstance(applied.get("error"), R.ApplyRefused), applied
    assert "approvals or placings changed" in str(applied["error"])
    row = _row(gc)
    assert row.output_status == "refused" and row.output_path is None
    assert gc["calls"]["autocad"] == 0 and _outputs(gc) == []
    assert _status_of("p1", gc) == "approved"                          # the newer approval kept


def _publish_url(gc) -> str:
    return f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}/publish"


def test_publish_stages_its_temporary_copy_in_the_platform_folder_never_in_the_archive(gc, tmp_path, monkeypatch):
    """U2M5V-02: the publication's ".part" is staged in the platform's own
    redesign folder (redesign/publishing), then put into the archive under
    its final name; no temporary file is ever created in the archive."""
    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    _succeeded(gc, result)
    staged: list[Path] = []
    in_archive_while_staged: list[list[str]] = []
    original = R._stage

    def stage(source, dest):
        part = original(source, dest)
        staged.append(Path(part))
        in_archive_while_staged.append(sorted(p.name for p in archive.rglob("*") if p.is_file()))
        return part

    monkeypatch.setattr(R, "_stage", stage)
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200, response.text
    platform = (gc["uploads"] / "EP-40951" / "redesign" / "publishing").resolve()
    assert [p.parent.resolve() for p in staged] == [platform]
    assert in_archive_while_staged == [[]]                               # nothing in the archive while staging
    assert [p.name for p in (archive / R.FOLDER).iterdir()] == [result["file"]]
    assert not [p for p in archive.rglob("*") if p.name.endswith(R.PART)]
    assert not [p for p in platform.iterdir() if p.name.endswith(R.PART)]  # the temporary removed


def test_a_leftover_publication_temporary_is_said_as_such_swept_and_does_not_block_for_good(gc, tmp_path):
    """U2M5V-02: a publication stopped mid-copy leaves its temporary copy in
    the platform's staging folder. A publication meanwhile is refused with a
    409 that says so (not "already in the archive"), the worker's sweep
    removes it, and the copy can then be published. A ".part" an earlier
    version left in the archive itself never blocks a publication and is
    never touched by the platform."""
    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    _succeeded(gc, result)
    platform = gc["uploads"] / "EP-40951" / "redesign" / "publishing"
    platform.mkdir(parents=True, exist_ok=True)
    leftover = platform / f".{result['file']}{R.PART}"
    leftover.write_bytes(b"half a copy")
    _old(leftover)
    (archive / R.FOLDER).mkdir(parents=True)
    earlier = archive / R.FOLDER / f".{result['file']}{R.PART}"
    earlier.write_bytes(b"left by the earlier version")
    refused = gc["client"].post(_publish_url(gc), json={})
    assert refused.status_code == 409
    detail = refused.json()["detail"]
    assert "temporary" in detail and "already in the project archive" not in detail
    assert not (archive / R.FOLDER / result["file"]).exists()
    assert R.sweep_orphans(gc["db"])["parts_removed"] == 1 and not leftover.exists()
    done = gc["client"].post(_publish_url(gc), json={})
    assert done.status_code == 200, done.text
    assert (archive / R.FOLDER / result["file"]).read_bytes() == (gc["uploads"] / result["path"]).read_bytes()
    assert earlier.read_bytes() == b"left by the earlier version"


def test_publishing_to_an_archive_on_another_volume_copies_exclusively_and_never_overwrites(gc, tmp_path, monkeypatch):
    """U2M5V-02: where the archive is on another volume (no hard link, no
    rename across volumes) the final name is created exclusively and
    filled; a name already there is refused, and the 409 says whether it
    holds the same file or a different one."""
    import errno

    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    _succeeded(gc, result)
    link, rename = os.link, os.rename

    def no_cross_volume(real):
        def op(src, dst, *a, **kw):
            if str(archive) in str(dst):
                raise OSError(errno.EXDEV, "not the same device")
            return real(src, dst, *a, **kw)
        return op

    monkeypatch.setattr(os, "link", no_cross_volume(link))
    monkeypatch.setattr(os, "rename", no_cross_volume(rename))
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200, response.text
    target = archive / R.FOLDER / result["file"]
    assert target.read_bytes() == (gc["uploads"] / result["path"]).read_bytes()
    assert [p.name for p in (archive / R.FOLDER).iterdir()] == [result["file"]]
    same = gc["client"].post(_publish_url(gc), json={})
    assert same.status_code == 409 and "already in the project archive (the same file)" in same.json()["detail"]
    target.write_bytes(b"someone else's drawing")
    other = gc["client"].post(_publish_url(gc), json={})
    assert other.status_code == 409 and "a different file" in other.json()["detail"].lower()
    assert target.read_bytes() == b"someone else's drawing"                 # never overwritten


def _running_apply_job(gc, request: dict, minutes_ago: float = 5.0):
    from app.models import BackgroundJob

    created = utc_now() - timedelta(minutes=minutes_ago)
    job = BackgroundJob(project_id=gc["pid"], kind=R.KIND_APPLY, status="running", progress={}, cancel_requested=False,
                        created_at=created, started_at=created, heartbeat_at=created, worker_id="ifc:PC:1:1:0",
                        attempts=0, params={"drawing_id": gc["drawing"].id, "user_id": None, **request})
    gc["db"].add(job)
    gc["db"].commit()
    return job


def _made_then_worker_stopped(gc):
    """Apply made and verified the copy and committed "made"; the worker
    stopped before the job's own "succeeded" commit."""
    request = R.apply_request(gc["db"], gc["project"], gc["drawing"])
    job = _running_apply_job(gc, request)
    made = _apply(gc, request=request, job_id=job.id, job_created_at=job.created_at)
    assert _row(gc).output_status == "made" and gc["calls"]["autocad"] == 1
    return job, made


def test_a_copy_made_whose_job_never_succeeded_is_reconciled_when_the_recovered_job_runs_again(gc, tmp_path):
    """U2M5V-03: the recovered job finds the copy it made and verified
    (bound by its run's verification.json and the copy's sha256) and
    succeeds with it -- AutoCAD is not run again -- so the copy can be
    published."""
    from app.ifc.services import runners
    from app.models import BackgroundJob
    from app.services import jobs

    db = gc["db"]
    job, made = _made_then_worker_stopped(gc)
    jobs.recover_stale(db, stale_after=timedelta(minutes=1))
    db.refresh(job)
    assert job.status == "queued"
    ended = jobs.execute(db, job.id, lambda s, ctx: runners.RUNNERS[R.KIND_APPLY](s, s.get(BackgroundJob, job.id), ctx))
    db.expire_all()
    job = db.get(BackgroundJob, job.id)
    assert ended == "succeeded" and job.result["path"] == made["path"], (ended, job.error)
    assert gc["calls"]["autocad"] == 1 and _row(gc).output_path == made["path"]
    _archive(gc, tmp_path)
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200, response.text
    assert response.json()["published"]["job_id"] == job.id


def test_a_made_copy_whose_job_failed_is_reconciled_by_housekeeping_only_while_it_still_verifies(gc, tmp_path):
    """U2M5V-03: a job left "failed" (its own commit failed, or it was given
    up after the worker stopped) is reconciled by the worker's housekeeping
    from the verified copy -- but never while the copy is not the file its
    run verified."""
    from app.models import BackgroundJob
    from app.workers import ifc_worker
    from app.database import SessionLocal

    db = gc["db"]
    job, made = _made_then_worker_stopped(gc)
    job.status, job.error, job.finished_at = "failed", "The worker stopped without finishing this job", utc_now()
    db.commit()
    copy = gc["uploads"] / made["path"]
    good = copy.read_bytes()
    copy.write_bytes(good + b" ALTERED")
    assert R.reconcile_made(db) == []
    _archive(gc, tmp_path)
    assert gc["client"].post(_publish_url(gc), json={}).status_code == 422
    copy.write_bytes(good)
    worker = ifc_worker.IfcWorker.__new__(ifc_worker.IfcWorker)
    worker.slot, worker.session_factory = 0, SessionLocal
    worker.housekeeping()
    db.expire_all()
    job = db.get(BackgroundJob, job.id)
    assert job.status == "succeeded" and job.result["path"] == made["path"] and job.result["fingerprint"]
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200 and response.json()["published"]["job_id"] == job.id


def test_a_made_copy_whose_job_failed_is_reconciled_by_the_next_publish_or_apply_request(gc, tmp_path):
    """U2M5V-03: without housekeeping, the next publish request reconciles
    the job from the verified copy; the next Apply of the same approved set
    is then refused as already made instead of drawing it again."""
    from app.models import BackgroundJob

    db = gc["db"]
    job, made = _made_then_worker_stopped(gc)
    job.status, job.error = "failed", "OperationalError: database is locked"
    db.commit()
    _archive(gc, tmp_path)
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200, response.text
    db.expire_all()
    assert db.get(BackgroundJob, job.id).status == "succeeded"
    with pytest.raises(R.ApplyRefused, match="already made by job"):
        _apply(gc, job_id=job.id + 1)
    assert gc["calls"]["autocad"] == 1


def test_a_made_copy_whose_job_failed_is_reconciled_when_the_next_apply_is_asked_for(gc):
    from app.models import BackgroundJob

    db = gc["db"]
    job, made = _made_then_worker_stopped(gc)
    job.status = "failed"
    db.commit()
    with pytest.raises(R.ApplyRefused, match=f"already made by job {job.id}"):
        _apply(gc, job_id=job.id + 1)
    db.expire_all()
    assert db.get(BackgroundJob, job.id).status == "succeeded" and gc["calls"]["autocad"] == 1


def test_publish_refuses_a_copy_that_is_no_longer_the_file_apply_verified(gc, tmp_path):
    """U2M5V-07: publication is bound to the copy_sha256 its run's
    verification.json recorded: a platform copy altered on disk since is
    refused, and nothing reaches the archive."""
    archive = _archive(gc, tmp_path)
    result = _apply(gc)
    _succeeded(gc, result)
    copy = gc["uploads"] / result["path"]
    good = copy.read_bytes()
    copy.write_bytes(good + b" ALTERED")
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 422 and "no longer the file" in response.json()["detail"]
    assert [p for p in archive.rglob("*") if p.is_file()] == []
    copy.write_bytes(good)
    assert gc["client"].post(_publish_url(gc), json={}).status_code == 200


def test_a_copy_filed_by_the_pre_m5_apply_is_said_filed_by_an_earlier_version_not_published(gc, tmp_path):
    """U2M5V-04: a row the pre-M5 Apply filed keeps output_relative; with
    no publication event it is "filed by an earlier version, not verified",
    never "published". A copy the engineer published is said published."""
    folder = gc["uploads"] / "EP-40951" / "redesign"
    folder.mkdir(parents=True, exist_ok=True)
    name = "FA LAYOUT R0 - Redesign 2026-10-02 1654.dwg"
    (folder / name).write_bytes(b"made by the old Apply")
    row = _row(gc)
    row.output_status, row.output_path, row.output_relative = "made", f"EP-40951/redesign/{name}", f"{R.FOLDER}/{name}"
    row.output_at = utc_now()
    gc["db"].commit()
    out = gc["client"].get(f"/projects/{gc['pid']}/redesign/{gc['drawing'].id}").json()["output"]
    assert out["available"] and out["published"] is None and out["filed_earlier"] == f"{R.FOLDER}/{name}"
    _archive(gc, tmp_path)
    result = _apply(gc)
    _succeeded(gc, result)
    response = gc["client"].post(_publish_url(gc), json={})
    assert response.status_code == 200, response.text
    out = response.json()["output"]
    assert out["published"] == f"{R.FOLDER}/{result['file']}" and out["filed_earlier"] is None


def test_the_panel_says_a_pre_m5_filing_apart_from_a_publication_and_keeps_the_two_meanings_apart():
    """U2M5V-04/-05: the panel's wording follows the view."""
    path = Path(__file__).resolve().parents[2] / "frontend" / "src" / "components" / "prep" / "RedesignPanel.tsx"
    if not path.is_file():
        pytest.skip("the frontend is not beside this backend")
    panel = path.read_text(encoding="utf-8")
    assert "filed by an earlier version, not verified" in panel
    assert "published separately to the project archive" not in panel
    assert "Not published, stale" not in panel and "Nothing was published:" not in panel
