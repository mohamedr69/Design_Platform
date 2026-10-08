"""One floor of a drawing's review asked of the model on a fixed call
budget, in a process of its own: the validation run (EP-30880, 6 October
2026) -- `scripts/scoped_drawing_review.py` runs it.

Nothing about the platform's own processes changes. The API and the
workers keep reading `.env` (AI_ENABLED and DRAWING_REVIEW_AI_ENABLED off);
the review's switch, its call limit and the Claude Code turn limit are put
on in this process alone and taken off again when the run ends, whatever
happens (`scoped_settings`). The job is written already running and held
by this process's heartbeat, so no worker takes it; one left behind by a
crash is failed by the workers' recovery, never queued again for them.

Before anything is asked (`preflight`), the run refuses unless the drawing,
its file's hash, the plot of that file, the floor on the page and its FLS
match are the ones named, and every window of the floor fits in the call
limit -- a limit that would leave a window unasked is refused, not run.
Every model invocation goes through `Guard`: one past the limit is refused,
and the first that shows more than it should (more turns than allowed,
another model answering, a usage limit) stops the rest.
"""
from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import socket
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

from app.ai import project_policy
from app.ai import provider as prov
from app.ai.provider import AiRequest, AiResponse, ImagePart, TextPart, Usage
from app.compliance import assist
from app.core.config import get_settings
from app.core.timeutils import utc_now
from app.database import SessionLocal
from app.models import BackgroundJob, Project, ProjectDrawingReview, ProjectIfcDrawing
from app.review import ai as A
from app.review import render, service
from app.services import jobs

KIND = "fa_drawing_review"
BACKEND = Path(__file__).resolve().parents[2]
# What the Claude Code program is told in this process only: no retries of its own (each would be a
# model request the limit does not see), no traffic it does not need.
CLI_ENV = {"CLAUDE_CODE_MAX_RETRIES": "0", "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"}
# A reply that says one of these stops the run: asking again would not change it.
STOPPING = ("rate_limit", "quota", "auth", "unsupported_model", "model_unverified", "model_substituted", "max_turns",
            "unavailable")


class Refused(Exception):
    """The run does not start: what was named is not what is there."""


@dataclasses.dataclass(frozen=True)
class Scope:
    ep_number: str
    drawing_id: int
    page: int
    floor: str
    source_sha: str          # the drawing file's SHA-256, or its first characters (12 at least)
    max_calls: int
    max_turns: int
    # the pictures inside the message (AI_CLI_INLINE_IMAGES) rather than read with the Read tool, a turn each
    inline_images: bool = False
    # The most turns a reply may *report* before the run stops -- apart from `max_turns`, the limit given to
    # the CLI: Claude Code 2.1.289 answered under --max-turns 1 and reported num_turns 2 (job 220).
    # Unset, the same as max_turns.
    max_reported_turns: int | None = None


def _sha_file(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def preflight(db, scope: Scope) -> dict:
    """What the run will ask, checked against what was named; `Refused`
    when anything differs. Asks no model and plots nothing."""
    s = get_settings()
    if s.ai_enabled:
        raise Refused("AI_ENABLED is on: the validation runs with the platform's AI off")
    if len(scope.source_sha) < 12:
        raise Refused("name the drawing file's hash (12 characters at least)")
    project = db.query(Project).filter(Project.ep_number == scope.ep_number).one_or_none()
    if project is None:
        raise Refused(f"no project EP-{scope.ep_number}")
    try:   # the project's AI policy, fail closed, before any provider is built (ORCH-053; --live included)
        project_policy.enforce(db, project.id, task=service.TASK_WINDOW)
    except project_policy.AiPolicyRefused as exc:
        raise Refused(str(exc)) from exc
    drawing = db.get(ProjectIfcDrawing, scope.drawing_id)
    if drawing is None or drawing.project_id != project.id:
        raise Refused(f"drawing {scope.drawing_id} is not EP-{scope.ep_number}'s")
    src = render.source_file(project, drawing)
    sha = render._sha(src)
    if not sha.startswith(scope.source_sha):
        raise Refused(f"the drawing's file is {sha[:24]}, not the {scope.source_sha} named")
    plot = render.folder(project) / f"{sha[:24]}.pdf"
    if not plot.is_file() or plot.stat().st_size == 0:
        raise Refused(f"no plot of {sha[:24]} on file: the run would start AutoCAD, which it does not")
    row = db.query(ProjectDrawingReview).filter_by(project_id=project.id, drawing_id=drawing.id).one_or_none()
    if row is not None and row.status == "running":
        raise Refused("a review of this drawing is running")
    if jobs.active_by_key(db, f"{KIND}:{project.id}:{drawing.id}") is not None:
        raise Refused("a review job of this drawing is queued or running")
    _pdf, _sha, sheets = service.plan_job(db, project, drawing, [scope.page])
    if [sh["index"] for sh in sheets] != [scope.page]:
        raise Refused(f"page {scope.page} is not a floor plan with named rooms on this plot")
    sh = sheets[0]
    if sh["floor"].strip().upper() != scope.floor.strip().upper():
        raise Refused(f"page {scope.page} is {sh['floor']!r} ({sh['name']} {sh['title']}), not {scope.floor!r}")
    fls = sh.get("fls")
    if fls and scope.floor.strip().upper() not in (fls.get("title") or "").upper():
        raise Refused(f"the floor's FLS match is {fls.get('file')} page {fls.get('page')} "
                      f"({fls.get('title')!r}), not {scope.floor!r}")
    # the looks exactly as the run will plan them: what a model already answered (windows in full, the
    # rooms it answered of a window, plan and FLS passes) is kept and not asked again
    from types import SimpleNamespace

    from app.review import rulings as R

    _extra, ruled = R.prompt(db)
    held = row if row is not None else SimpleNamespace(sheets=[], source_sha256=None, model=None)
    merged, tasks = service.plan_looks(held, sheets, sha, f"{A.PROMPT_VERSION}+{ruled}", [scope.page],
                                       keep_answered=True)
    sh = next(m for m in merged if m["index"] == scope.page)
    windows = sh["windows"]
    by_id = {w["id"]: w for w in windows}
    calls = []
    for kind, _index, ids, mode in tasks:
        if kind == "window":
            calls.append({"task": "window", "windows": ids,
                          "rooms": [r["name"] for i in ids for r in service.rooms_to_ask(by_id[i], mode == "anew")]})
        elif kind == "sheet":
            calls.append({"task": "sheet", "rooms": sum(len(w["rooms"]) for w in windows)})
        else:
            calls.append({"task": "fls", "file": fls.get("file"), "page": fls.get("page")})
    if not calls:
        raise Refused(f"nothing is left to ask on {scope.floor}")
    if len(calls) > scope.max_calls:
        raise Refused(f"the floor needs {len(calls)} calls ({', '.join(c['task'] for c in calls)}) and the limit is "
                      f"{scope.max_calls}: windows would be left unasked")
    return {
        "project": {"id": project.id, "ep_number": project.ep_number, "name": project.project_name},
        "drawing": {"id": drawing.id, "filename": drawing.filename, "revision": drawing.revision or "R0",
                    "source": str(src), "source_sha256": sha},
        "plot": {"pdf": str(plot), "bytes": plot.stat().st_size},
        "page": {"index": sh["index"], "sheet": sh["name"], "title": sh["title"], "floor": sh["floor"]},
        "windows": [{"id": w["id"], "status": w.get("status", "pending"), "rooms": [r["name"] for r in w["rooms"]],
                     "answered": len((w.get("answers") or {}) if service._usable(w) else {})} for w in windows],
        "rooms": sum(len(w["rooms"]) for w in windows),
        "rooms_answered_before": sum(len(w.get("answers") or {}) for w in windows if service._usable(w)),
        "plan_pass_before": "done" if service._pass_done(sh, "sheet") else "to ask",
        "fls_pass_before": ("done" if service._pass_done(sh, "fls") else "to ask") if fls else None,
        "fls": {k: v for k, v in (fls or {}).items() if k != "pdf"} or None,
        "calls": calls,
        "decisions": len((row.decisions or {}) if row else {}),
        "settings": {"ai_enabled": s.ai_enabled, "fa_ai_enabled": s.fa_ai_enabled,
                     "drawing_review_ai_enabled": s.drawing_review_ai_enabled,
                     "drawing_review_max_calls": s.drawing_review_max_calls, "ai_provider": s.ai_provider,
                     "drawing_review_model": s.drawing_review_model},
    }


def _evidence(request: AiRequest) -> list[dict]:
    """What a request carried, without the pictures themselves."""
    out = []
    for p in request.parts:
        if isinstance(p, TextPart):
            out.append({"label": p.label, "text": p.text[:400]})
        elif isinstance(p, ImagePart):
            out.append({"label": p.label, "png_bytes": len(p.png), "sha256": hashlib.sha256(p.png).hexdigest()[:16]})
    return out


class Guard:
    """The run's provider: every invocation counted under one lock, none past
    `limit`, each one's turns, models, usage and evidence kept; the first
    that shows more than it should stops the rest."""

    def __init__(self, inner, limit: int, max_turns: int, floor: str | None = None):
        # max_turns here is the most turns a reply may report (Scope.max_reported_turns)
        self.inner, self.limit, self.max_turns = inner, limit, max_turns
        self.floor = floor.strip().upper() if floor else None
        self.invocations: list[dict] = []
        self.stopped: str | None = None
        self._lock = threading.Lock()

    name = property(lambda self: getattr(self.inner, "name", "guarded"))
    ready = property(lambda self: getattr(self.inner, "ready", True))
    status = property(lambda self: getattr(self.inner, "status", ""))

    def supports(self, model: str, *, exact: bool = False):
        supports = getattr(self.inner, "supports", None)
        return supports(model, exact=exact) if supports else (True, None)

    def complete(self, request: AiRequest) -> AiResponse:
        model = request.model or ""
        floors = [p.text for p in request.parts if isinstance(p, TextPart) and p.label == "floor"]
        with self._lock:
            if self.stopped:
                return AiResponse(data=None, error="stopped", error_detail=self.stopped, model=model)
            if self.floor and (not floors or not all(t.strip().upper().startswith(self.floor) for t in floors)):
                # never sent: a request about anything but the floor named is outside the run
                self.stopped = f"a request outside the floor named ({(floors or ['no floor given'])[0][:80]!r})"
                return AiResponse(data=None, error="out_of_scope", error_detail=self.stopped, model=model)
            if len(self.invocations) >= self.limit:
                self.stopped = f"the limit of {self.limit} model calls was reached"
                return AiResponse(data=None, error="invocation_limit", error_detail=self.stopped, model=model)
            entry = {"n": len(self.invocations) + 1, "task": request.task, "model_asked": model,
                     "started_at": utc_now().isoformat(), "evidence": _evidence(request)}
            self.invocations.append(entry)
        response = self.inner.complete(request)
        entry.update(model=response.model, models_used=dict(response.models_used or {}), turns=response.turns,
                     error=response.error, error_detail=(response.error_detail or "")[:300] or None,
                     usage=dataclasses.asdict(response.usage), latency_ms=response.latency_ms,
                     route_meta=dict(getattr(response, "route_meta", None) or {}))
        problem = None
        if response.error in STOPPING:
            problem = f"call {entry['n']}: {response.error} ({(response.error_detail or '')[:160]})"
        elif response.turns is not None and response.turns > self.max_turns:
            problem = f"call {entry['n']} reported {response.turns} turns, more than the {self.max_turns} allowed"
        elif any(m != model for m in response.models_used or {}):
            problem = f"call {entry['n']}: other models took part ({', '.join(response.models_used)})"
        elif response.ok and response.model != model:
            problem = f"call {entry['n']}: answered as {response.model!r}, not the {model!r} asked for"
        if problem:
            entry["stopped_after"] = problem
            with self._lock:
                self.stopped = self.stopped or problem
        return response


class RehearsalProvider:
    """A stand-in for the model, for the rehearsal: every room it is shown
    answered (one with an emergency light to add), nothing on the plan or
    the FLS -- or, as asked, a room left out or every call failing."""

    name = "rehearsal"
    ready = True
    status = "rehearsal provider: no model is called"
    MODEL = "rehearsal"
    KNOWN = "Add an emergency light by the door (rehearsal)"

    def __init__(self, *, skip_rooms: int = 0, fail: bool = False, turns: int = 2):
        self.skip_rooms, self.fail, self.turns = skip_rooms, fail, turns
        self.calls = 0

    def complete(self, request: AiRequest) -> AiResponse:
        self.calls += 1
        if self.fail:
            return AiResponse(data=None, error="transport", error_detail="rehearsal: the call fell over",
                              model=self.MODEL, turns=self.turns)
        # it answers as the model asked for, as the real route does (the guard checks that)
        model = request.model or self.MODEL
        common = dict(model=model, models_used={model: 1}, turns=self.turns, usage=Usage())
        if request.task != service.TASK_WINDOW:
            return AiResponse(data={"findings": []}, **common)
        numbers = []
        for p in request.parts:
            if isinstance(p, TextPart) and p.label.endswith(" rooms"):
                numbers += [int(line.split(":", 1)[0]) for line in p.text.splitlines() if ":" in line]
        numbers = numbers[:len(numbers) - self.skip_rooms] if self.skip_rooms else numbers

        def check(system, status, action="none", device="", instruction=""):
            return {"system": system, "status": status, "seen": "", "action": action, "device": device,
                    "instruction": instruction, "x": 0.5 if action != "none" else -1, "y": 0.5 if action != "none" else -1}

        rooms = [{"n": n, "room_type": "room", "checks": [check(s, "present") for s in A.SYSTEMS]} for n in numbers]
        if rooms:
            rooms[0]["checks"] = [check(s, "present") for s in A.SYSTEMS if s != "emergency_light"] + [
                check("emergency_light", "absent", "add", "emergency light (E)", self.KNOWN)]
        return AiResponse(data={"rooms": rooms, "other": []}, **common)


@contextmanager
def scoped_settings(scope: Scope):
    """The review's switch, its call limit and the CLI's turn limit on, in this
    process only, and every look asked afresh -- no stored answer (an earlier
    model's, the 1-2 October ones) stands in for a call of the run; everything
    as it was afterwards, whatever happened."""
    s = get_settings()
    saved = {k: getattr(s, k) for k in ("drawing_review_ai_enabled", "drawing_review_max_calls", "ai_cli_max_turns",
                                        "ai_cli_inline_images", "drawing_review_parallel")}
    saved_env = {k: os.environ.get(k) for k in CLI_ENV}
    saved_provider = prov._review_provider
    saved_call = assist.call_task

    def fresh_call(*args, **kwargs):
        return saved_call(*args, **{**kwargs, "fresh": True})

    try:
        s.drawing_review_ai_enabled = True
        s.drawing_review_max_calls = scope.max_calls
        s.ai_cli_max_turns = scope.max_turns
        s.ai_cli_inline_images = scope.inline_images
        # one look at a time: the guard sees each reply before the next look is sent
        s.drawing_review_parallel = 1
        os.environ.update(CLI_ENV)
        assist.call_task = fresh_call
        yield
    finally:
        assist.call_task = saved_call
        for k, v in saved.items():
            setattr(s, k, v)
        for k, v in saved_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        prov._review_provider = saved_provider


def _beat(session_factory, worker_id: str, job_id: int, stop: threading.Event) -> None:
    while True:
        db = session_factory()
        try:
            jobs.worker_beat(db, worker_id, pid=os.getpid(), hostname=socket.gethostname(), current_job_id=job_id,
                             lane="validation")
        except Exception:  # noqa: BLE001 -- the next beat tries again
            pass
        finally:
            db.close()
        if stop.wait(jobs.HEARTBEAT_SECONDS):
            return


def _floor_view(db, project_id: int, drawing_id: int, page: int) -> dict:
    project, drawing = db.get(Project, project_id), db.get(ProjectIfcDrawing, drawing_id)
    view = service.build(db, project, drawing)
    floor = next((f for f in view["floors"] if f["page"] == page), None)
    found = [f for f in view["findings"] if f["page"] == page]
    return {
        "state": view["state"], "state_message": view["state_message"], "answered_by": view["answered_by"],
        "counts": view["counts"],
        "floor": None if floor is None else {
            "rooms": len(floor["rooms"]), "reviewed": sum(1 for r in floor["rooms"] if r["checks"]),
            "room_status": {st: sum(1 for r in floor["rooms"] if r["status"] == st)
                            for st in sorted({r["status"] for r in floor["rooms"]})},
            "windows": floor["windows"], "windows_done": floor["windows_done"],
            "windows_incomplete": floor["windows_incomplete"], "windows_failed": floor["windows_failed"],
            "rooms_not_reviewed": [r["name"] for r in floor["rooms"] if not r["checks"]],
            "plan_pass": floor["sheet_status"], "fls_pass": floor["fls_status"],
            "unsolicited": floor.get("unsolicited") or []},
        "merged_duplicates": view.get("merged_duplicates", 0),
        "possible_duplicate_pairs": view.get("possible_duplicate_pairs", []),
        "last_attempt": view.get("last_attempt"),
        "findings": [{k: f.get(k) for k in ("id", "room", "system", "kind", "action", "device", "instruction",
                                              "decision", "previous_decision", "sources", "possible_duplicates")}
                     for f in found],
    }


def run(scope: Scope, provider_factory: Callable[[], object], *, session_factory=SessionLocal,
        report_path: Path | None = None) -> dict:
    """The validation run: preflight, the one floor asked through the job
    runner the IFC worker uses, the settings and the provider put back, and
    a report of every invocation and of what the page will show."""
    env_file = BACKEND / ".env"
    env_before = _sha_file(env_file)
    db = session_factory()
    try:
        plan = preflight(db, scope)
        row = db.query(ProjectDrawingReview).filter_by(project_id=plan["project"]["id"],
                                                       drawing_id=scope.drawing_id).one_or_none()
        decisions_before = json.dumps((row.decisions if row else None) or {}, sort_keys=True)
    finally:
        db.close()
    report: dict = {"scope": dataclasses.asdict(scope), "plan": plan, "started_at": utc_now().isoformat()}
    worker_id = f"validation:{socket.gethostname()}:{os.getpid()}:{int(time.time())}"[:64]
    job_id = None
    guard = None
    stop = threading.Event()
    beat = None
    try:
        with scoped_settings(scope):
            guard = Guard(provider_factory(), scope.max_calls, scope.max_reported_turns or scope.max_turns,
                          floor=scope.floor)
            prov._review_provider = guard
            report["provider"] = {"name": guard.name, "ready": guard.ready, "status": guard.status}
            db = session_factory()
            try:
                now = utc_now()
                job = BackgroundJob(
                    kind=KIND, project_id=plan["project"]["id"], status="running", worker_id=worker_id,
                    started_at=now, heartbeat_at=now, attempts=jobs.MAX_ATTEMPTS,
                    dedup_key=f"{KIND}:{plan['project']['id']}:{scope.drawing_id}",
                    params={"drawing_id": scope.drawing_id, "pages": [scope.page], "user_id": None,
                            "keep_answered": True,
                            "validation": {"max_calls": scope.max_calls, "max_turns": scope.max_turns,
                                           "max_reported_turns": scope.max_reported_turns or scope.max_turns,
                                           "inline_images": scope.inline_images}},
                    progress={"done": 0, "total": 1, "message": f"Validation run: {scope.floor} only"})
                db.add(job)
                db.commit()
                job_id = job.id
                beat = threading.Thread(target=_beat, args=(session_factory, worker_id, job_id, stop), daemon=True)
                beat.start()
                from app.ifc.services.runners import run_drawing_review

                report["job_status"] = jobs.execute(
                    db, job_id, lambda session, c: run_drawing_review(session, session.get(BackgroundJob, job_id), c),
                    ctx=jobs.JobContext(job_id, session_factory=session_factory), claimed=True)
            finally:
                stop.set()
                if beat is not None:
                    beat.join(timeout=30)
                db.close()
    finally:
        db = session_factory()
        try:
            if job_id is not None:
                job = db.get(BackgroundJob, job_id)
                if job is not None and job.status in ("queued", "running"):
                    # never left for a worker to pick up
                    job.status, job.finished_at = "failed", utc_now()
                    job.error = "The validation run ended without finishing this job"
                    db.commit()
                report["job"] = {"id": job.id, "status": job.status, "error": job.error, "result": job.result}
            try:
                jobs.worker_stopped(db, worker_id)
            except Exception:  # noqa: BLE001
                pass
            s = get_settings()
            report["settings_after"] = {"drawing_review_ai_enabled": s.drawing_review_ai_enabled,
                                        "drawing_review_max_calls": s.drawing_review_max_calls,
                                        "ai_cli_max_turns": s.ai_cli_max_turns,
                                        "ai_cli_inline_images": s.ai_cli_inline_images,
                                        "drawing_review_parallel": s.drawing_review_parallel, "ai_enabled": s.ai_enabled,
                                        "fa_ai_enabled": s.fa_ai_enabled,
                                        "review_provider": type(prov.get_review_provider()).__name__,
                                        "cli_env": {k: os.environ.get(k) for k in CLI_ENV}}
            report["env_file_unchanged"] = _sha_file(env_file) == env_before
            if guard is not None:
                report["invocations"] = guard.invocations
                report["stopped"] = guard.stopped
            if job_id is not None:
                report["review"] = _floor_view(db, plan["project"]["id"], scope.drawing_id, scope.page)
                row = db.query(ProjectDrawingReview).filter_by(project_id=plan["project"]["id"],
                                                               drawing_id=scope.drawing_id).one()
                after = row.decisions or {}
                report["decisions"] = {"before": len(json.loads(decisions_before)), "after": len(after),
                                       "unchanged": json.dumps(after, sort_keys=True) == decisions_before}
        finally:
            db.close()
        report["finished_at"] = utc_now().isoformat()
        if report_path is not None:
            report_path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
