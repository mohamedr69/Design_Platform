"""Time and calls (2026-10-05, after EP-30880's fresh run: 40 min, 112 calls):
several damper windows a look call, the finding review showing the pictures
the look already drew, items of one sheet reviewed together, the orchestrator's
package reviews side by side, drawings read side by side, and pictures inline in
the CLI's message. Each is a setting; each keeps what is asked and checked the
same. A scripted provider stands in for the models: no model is called."""
from __future__ import annotations

import json
import subprocess
import threading
import time

import pytest

from app.ai import provider as P
from app.core.config import get_settings
from app.interfaces import findings, render, service, visual, workflow
from tests.test_fa_opus_review import ALONE, _answer, _lone_item, _view, _with_lone_label  # noqa: F401
from tests.test_fa_workflow import _latest, _run, w  # noqa: F401  (fixture)

settings = get_settings()


def _looks(w):
    return [r for r in w.models.requests if r.task == visual.TASK]


# --- several windows a look call ----------------------------------------------------------------------------------


@pytest.mark.parametrize("per_call, calls", [(2, 1), (1, 2)])
def test_damper_windows_are_looked_at_together_numbered_on_and_answered_each(w, monkeypatch, per_call, calls):
    monkeypatch.setattr(settings, "fa_look_windows_per_call", per_call)
    _with_lone_label(w)                                          # two windows: the pair of dampers, the lone label
    _run(w)
    looks = _looks(w)
    assert len(looks) == calls
    pictures = [p for r in looks for p in r.parts if isinstance(p, P.ImagePart)]
    assert len(pictures) == 2
    listed = "\n".join(p.text for r in looks for p in r.parts if isinstance(p, P.TextPart))
    assert "1: MSD (picture 1)" in listed and ("3: MSD (picture 2)" in listed if per_call == 2 else True)
    # each answer went to its own label: both drawn dampers counted at their symbols, the lone one held
    view = _view(w)
    assert len([r for r in view["rows"] if r["key"] == "motorized_smoke_fire_damper"]) == 2
    (agent,) = _latest(w)["agent_reports"]
    assert agent["look"]["labels_looked"] == 3 and agent["coverage_state"] == "complete"


# --- the finding review shows the look's pictures again -----------------------------------------------------------


def test_the_finding_review_shows_the_pictures_the_look_drew_without_opening_the_drawing_again(w, monkeypatch):
    opened = []
    real = render.RenderSession

    class Counting(real):
        def __init__(self, dxf, boxes, metre, **kw):
            opened.append(len(boxes))
            super().__init__(dxf, boxes, metre, **kw)
    monkeypatch.setattr(render, "RenderSession", Counting)
    _with_lone_label(w)
    _run(w)
    assert len(opened) == 1                                      # the look's; the finding review drew nothing
    (asked,) = [r for r in w.models.requests if r.task == findings.TASK]
    (picture,) = [p for p in asked.parts if isinstance(p, P.ImagePart)]
    assert picture.label == "V1" and picture.png[:4] == b"\x89PNG"
    item = _lone_item(_view(w))
    assert item["review"]["views_shown"] == ["V1"]


def test_a_fresh_run_draws_its_pictures_again(w):
    _run(w)
    w.db.expire_all()
    project = w.db.get(workflow.Project, w.pid)
    src = next(e for e in service.state(w.db, project).sources if visual.wanted(e))
    folder = visual.picture_folder(project, src["sha256"])
    stale = folder / "left-by-an-earlier-run.png"
    stale.write_bytes(b"old")
    workflow.run_workflow(w.db, project, fresh=True)
    assert not stale.exists() and any(folder.glob("*.png"))


# --- items of one sheet reviewed together -------------------------------------------------------------------------


def _group(gid, key="motorized_smoke_fire_damper", path="SM/S.dwg", sheet="SM-111", floors=("L3",), x=0.0, **kw):
    return {"id": gid, "key": key, "equipment": "Motorized Smoke Fire Dampers", "discipline": "SM", "system": "SM",
            "source": "S.dwg", "ref": sheet, "reason": "held", "proposed_floor_keys": list(floors),
            "proposed_floors": list(floors), "proposed_qty": None, "tags": [], "location": "", "labels": 1,
            "evidence": "1 label", "points": [{"relative_path": path, "sheet": sheet, "x": x, "y": 0.0, "text": "SMD"}],
            **kw}


def test_items_of_one_kind_sheet_and_floors_are_batched_up_to_the_bound():
    a, b, c = _group("a"), _group("b", x=1), _group("c", x=2)
    other_sheet, other_floors = _group("d", sheet="SM-112"), _group("e", floors=("L4",))
    conflict, schedule = _group("f", conflict=True), _group("SCHED|x|Sheet1|3|verify")
    out = findings.batches([a, b, c, other_sheet, other_floors, conflict, schedule], 2)
    assert [[g["id"] for g in batch] for batch in out] == [["a", "b"], ["c"], ["d"], ["e"], ["f"],
                                                           ["SCHED|x|Sheet1|3|verify"]]
    assert all(len(b) == 1 for b in findings.batches([a, b, c], 1))          # 1: one call an item, as before


def test_a_shared_picture_counts_only_as_evidence_for_the_items_whose_points_it_shows():
    src = {"relative_path": "SM/S.dwg", "filename": "S.dwg", "result": {"units": "m", "sheets": []}}
    near, far = _group("a", x=0.0), _group("b", x=50.0)                      # 50 m apart: two windows
    pk = findings.packet([near, far], {"floors": [{"key": "L3", "name": "Level 3"}], "rows": [], "coverage": []},
                         [src], [], 3)
    assert pk.letters == ["A", "B"] and {"E-A", "E-B", "V1", "V2", "M1", "C1"} <= pk.ids
    v_a, = pk.views_of("A")
    v_b, = pk.views_of("B")
    pk.pictures = {v_a: b"png", v_b: b"png"}
    answer = {"item": "B", "outcome": "not_applicable", "floor_keys": [], "qty_per_floor": 0, "tags": [],
              "location": "", "evidence_refs": [v_a], "rationale": "door tag", "coverage_checked": "",
              "unclear": "", "engineer_action": "", "confidence": "high"}
    assert findings.assess(pk, answer, "B")["outcome"] == "unresolved"       # A's picture is not B's evidence
    assert findings.assess(pk, {**answer, "evidence_refs": [v_b]}, "B")["outcome"] == "not_applicable"


def test_an_item_the_answer_leaves_out_is_said_not_reviewed(w, monkeypatch):
    _with_lone_label(w)
    w.models.finding = lambda request: {"items": [{**_answer("not_applicable")(request)["items"][0], "item": "Z"}]}
    out = _run(w)
    item = _lone_item(_view(w))
    assert item["status"] == "open" and item["review"]["state"] == "failed" and "left item A out" in item["review"]["reason"]
    assert out["findings_review"]["state"] == "missing" and out["publication_state"] == "provisional"


# --- side by side -------------------------------------------------------------------------------------------------


def test_the_package_reviews_run_side_by_side_then_the_run_review(w, monkeypatch):
    ff = w.root / "03- Drawings" / "IFC" / "Mechanical" / "FF"
    ff.mkdir(parents=True, exist_ok=True)
    from tests.test_fa_workflow import _damper_drawing

    sm = w.root / "03- Drawings" / "IFC" / "Mechanical" / "SM"
    sm.mkdir(parents=True, exist_ok=True)
    _damper_drawing(sm / "SMOKE LAYOUT.dxf", x0=719.25 + 300)
    (ff / "FF.pdf").write_bytes(b"%PDF-1.4")
    running, peak, lock = [0], [0], threading.Lock()
    real = w.models.review

    def slow(request):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
        time.sleep(0.3)
        with lock:
            running[0] -= 1
        return real(request)
    w.models.review = slow
    _run(w)
    reviews = [r.parts[0].label for r in w.models.requests if r.task == workflow.TASK_REVIEW]
    assert reviews[-1] == "run_review" and len(reviews) >= 3
    assert peak[0] >= 2                                                     # the packages' reviews overlapped


def test_drawings_are_read_side_by_side_and_kept_in_the_folders_order(w, monkeypatch):
    from tests.test_fa_workflow import _damper_drawing

    for i in range(1, 4):
        _damper_drawing(w.hvac / f"VENTILATION LAYOUT {i}.dxf", x0=719.25 + 300 * i)
    monkeypatch.setattr(settings, "fa_read_parallel", 2)
    running, peak, lock = [0], [0], threading.Lock()
    real = service.scan.read

    def slow(*a, **kw):
        with lock:
            running[0] += 1
            peak[0] = max(peak[0], running[0])
        time.sleep(0.3)
        try:
            return real(*a, **kw)
        finally:
            with lock:
                running[0] -= 1
    monkeypatch.setattr(service.scan, "read", slow)
    _run(w)
    assert peak[0] == 2
    w.db.expire_all()
    names = [e["filename"] for e in service.state(w.db, w.db.get(workflow.Project, w.pid)).sources
             if e.get("discipline") == "HVAC"]
    assert names == sorted(names, key=str.lower)                            # the folder's order, not finishing order


# --- pictures inline in the CLI's message ---------------------------------------------------------------------------


class StreamCli:
    def __init__(self):
        self.calls, self.stdin = [], []

    def __call__(self, args, **kw):
        if args[1:] == ["--version"]:
            return subprocess.CompletedProcess(args, 0, stdout="2.1.289 (Claude Code)\n", stderr="")
        self.calls.append(list(args))
        self.stdin.append(kw.get("input"))
        result = {"type": "result", "subtype": "success", "is_error": False, "structured_output": {"ok": True},
                  "result": "{}", "usage": {"input_tokens": 3, "output_tokens": 5},
                  "modelUsage": {"claude-opus-5-5": {"outputTokens": 5}}}
        out = "\n".join(json.dumps(m) for m in ({"type": "system", "subtype": "init"},
                                                 {"type": "assistant", "message": {"content": []}}, result))
        return subprocess.CompletedProcess(args, 0, stdout=out + "\n", stderr="")


@pytest.mark.parametrize("inline", [True, False])
def test_pictures_go_inline_only_when_switched_on(monkeypatch, tmp_path, inline):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    monkeypatch.setattr(settings, "ai_cli_inline_images", inline)
    cli = StreamCli()
    if not inline:                                          # the json output: one object
        def plain(args, **kw):
            done = cli(args, **kw)
            if args[1:] == ["--version"]:
                return done
            last = done.stdout.strip().splitlines()[-1]
            return subprocess.CompletedProcess(args, 0, stdout=last, stderr="")
        monkeypatch.setattr(subprocess, "run", plain)
    else:
        monkeypatch.setattr(subprocess, "run", cli)
    req = P.AiRequest(task="t", system="s", parts=[P.TextPart("a", "b"), P.ImagePart("V1", b"\x89PNGdata")],
                      schema={"type": "object"}, max_output_tokens=10, model="claude-opus-5-5", exact_model=True)
    out = P.ClaudeCodeProvider().complete(req)
    assert out.error is None and out.data == {"ok": True}
    (args,) = cli.calls
    if inline:
        assert args[args.index("--input-format") + 1] == "stream-json" and args[args.index("--tools") + 1] == ""
        message = json.loads(cli.stdin[0])
        kinds = [c["type"] for c in message["message"]["content"]]
        assert kinds == ["text", "text", "image"] and "Read tool" not in cli.stdin[0]
    else:
        assert "--input-format" not in args and args[args.index("--tools") + 1] == "Read"
        assert "image-1.png" in cli.stdin[0]
