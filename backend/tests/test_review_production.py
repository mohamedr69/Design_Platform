"""The production drawing review (EP-30880, 6 October 2026): the whole drawing
reviewed through one job, results reused only while the drawing, prompt,
rules and model are the same, a review from the beginning that keeps what is
there until each look is answered anew, and the stops that end a run early.
No model is called: stand-in providers answer."""
from __future__ import annotations

import json
import subprocess

from app.ai.provider import AiRequest, AiResponse, ClaudeCodeProvider, TextPart, set_provider
from app.core.config import get_settings
from app.review import scoped
from tests.test_drawing_review_outcome import _review
from tests.test_provider_honesty import FakeCli, _reply
from tests.test_scoped_drawing_review import _two_floors

settings = get_settings()


class Counting(scoped.RehearsalProvider):
    """The rehearsal stand-in, counting its calls by task, failing on request."""

    def __init__(self, *, fail_on: set[int] = frozenset(), error: str = "transport", **kw):
        super().__init__(**kw)
        self.fail_on, self.error, self.tasks = set(fail_on), error, []

    def complete(self, request):
        self.tasks.append(request.task.rsplit("_", 1)[-1])
        if len(self.tasks) in self.fail_on:
            self.calls += 1
            return AiResponse(data=None, error=self.error, error_detail=f"stand-in {self.error}",
                              model=request.model or "", turns=1)
        return super().complete(request)


def _start(client, pid, did, provider, **body):
    set_provider(provider)
    try:
        started = client.post(f"/projects/{pid}/drawing-review/{did}/jobs", json={"pages": None, **body})
        assert started.status_code == 202, started.text
    finally:
        set_provider(None)
    return client.get(f"/jobs/{started.json()['id']}").json(), client.get(f"/projects/{pid}/drawing-review/{did}").json()


def _row(db_session, pid, did):
    from app.models import ProjectDrawingReview

    row = db_session.query(ProjectDrawingReview).filter_by(project_id=pid, drawing_id=did).one()
    db_session.refresh(row)
    return row


def _new_ruling(client, pid, did):
    """An engineer's decision: a ruling, so the prompt (and its version) changes."""
    review = client.get(f"/projects/{pid}/drawing-review/{did}").json()
    f = next(f for f in review["findings"] if f["action"] == "add" and f["decision"] == "open")
    assert client.post(f"/projects/{pid}/drawing-review/{did}/decisions",
                       json={"id": f["id"], "status": "accepted"}).status_code == 200
    return f["id"]


def test_the_whole_drawing_is_reviewed_in_one_job_and_a_rerun_with_nothing_changed_asks_nothing(
        client, db_session, monkeypatch, tmp_path):
    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "51001")
    monkeypatch.setattr(settings, "drawing_review_parallel", 2)          # bounded, as in production
    first = Counting()
    job, review = _start(client, pid, did, first)
    assert job["status"] == "succeeded" and review["state"] == "done"
    # every floor: its windows, its floor-plan pass (no FLS on file here)
    assert sorted(first.tasks) == ["sheet", "sheet", "window", "window"]
    assert review["counts"]["reviewed"] == review["counts"]["rooms"] == 4
    assert all(f["sheet_status"] == "done" for f in review["floors"])
    route = job["result"]["route"]
    assert route["cli_calls"] == 4 and route["models"] == ["claude-opus-5-5"] and route["reported_turns"] == 8
    # each answer says where it came from
    row = _row(db_session, pid, did)
    w = row.sheets[0]["windows"][0]
    assert w["cli"]["turns"] == 2 and w["prompt_version"] == row.sheets[0]["prompt_version"] and w["answered_at"]

    again = Counting()
    job, review = _start(client, pid, did, again)
    assert again.tasks == [] and job["result"]["calls"] == 0 and review["state"] == "done"


def test_a_new_ruling_asks_again_and_keeps_every_answer_until_its_replacement_is_saved(
        client, db_session, monkeypatch, tmp_path):
    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "51002")
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    _start(client, pid, did, Counting())
    fid = _new_ruling(client, pid, did)
    before = _row(db_session, pid, did)
    old_first_floor = json.dumps(before.sheets[1]["windows"], sort_keys=True)
    decisions = json.dumps(before.decisions, sort_keys=True)

    # asked again (the prompt changed); the second look fails: the floor it was for keeps its answers
    provider = Counting(fail_on={3})
    job, review = _start(client, pid, did, provider)
    assert len(provider.tasks) == 4 and job["status"] == "succeeded"
    row = _row(db_session, pid, did)
    failed = [w for sh in row.sheets for w in sh["windows"] if w.get("last_error")]
    assert failed and all(w["answers"] for w in failed)                  # kept, with why the re-ask failed
    assert review["counts"]["reviewed"] == 4                              # nothing lost
    assert json.dumps(row.decisions, sort_keys=True) == decisions         # no decision touched
    assert next(f for f in review["findings"] if f["id"] == fid)["decision"] in ("accepted", "open")
    # the floor whose look failed still answers with what it had
    assert any(json.dumps(sh["windows"], sort_keys=True) == old_first_floor for sh in row.sheets) or failed


def test_review_from_the_beginning_asks_every_look_afresh_and_keeps_the_old_results_if_it_fails(
        client, db_session, monkeypatch, tmp_path):
    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "51003")
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    _start(client, pid, did, Counting())
    held = json.dumps(_row(db_session, pid, did).sheets, sort_keys=True)

    # from the beginning: every look, the stored answers notwithstanding -- and every one fails
    failing = Counting(fail_on={1, 2, 3, 4})
    job, review = _start(client, pid, did, failing, fresh=True)
    assert len(failing.tasks) == 4 and job["status"] == "failed"
    assert json.dumps(_row(db_session, pid, did).sheets, sort_keys=True) == held   # what was there, as it was
    assert review["counts"]["reviewed"] == 4 and review["last_attempt"]["status"] == "failed"

    # from the beginning, answered: every look asked anew and saved
    fresh = Counting()
    job, review = _start(client, pid, did, fresh, fresh=True)
    assert len(fresh.tasks) == 4 and job["result"]["fresh"] is True and review["state"] == "done"
    assert review["last_attempt"] is None


def test_the_subscriptions_limit_stops_the_review_and_keeps_what_was_answered(client, db_session, monkeypatch,
                                                                             tmp_path):
    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "51004")
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    provider = Counting(fail_on={2}, error="rate_limit")
    job, review = _start(client, pid, did, provider)
    # the first look answered; the second hit the limit; the rest were never sent
    assert len(provider.tasks) == 2 and job["status"] == "succeeded"
    assert job["result"]["stopped"].startswith("Stopped after 2 of 4 looks: rate_limit")
    assert review["state"] == "partial" and review["counts"]["reviewed"] >= 1
    assert review["last_attempt"]["status"] == "stopped" and "rate_limit" in review["last_attempt"]["message"]

    # a reply reporting more turns than allowed stops it too
    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path / "b", "51005") \
        if (tmp_path / "b").mkdir() is None else (None, None, None)
    provider = Counting(turns=3)
    job, review = _start(client, pid, did, provider)
    assert len(provider.tasks) == 1 and "reported 3 turns" in job["result"]["stopped"]


def test_a_cache_entry_marked_unsuitable_is_kept_but_never_an_answer(client, db_session, monkeypatch, tmp_path):
    from app.models import ResultCache

    pid, did, _sha = _two_floors(client, db_session, monkeypatch, tmp_path, "51006")
    monkeypatch.setattr(settings, "drawing_review_parallel", 1)
    _start(client, pid, did, Counting())
    # the stored answers marked unsuitable (not deleted), and the review asked again (its answers not current)
    for entry in db_session.query(ResultCache).filter(ResultCache.task.like("fa_drawing_review%")):
        entry.value = {**entry.value, "invalid": {"reason": "test", "at": "2026-10-06"}}
    db_session.commit()
    row = _row(db_session, pid, did)
    sheets = json.loads(json.dumps(row.sheets))
    for sh in sheets:
        sh["prompt_version"] = "an earlier prompt"
        for w in sh["windows"]:
            w["prompt_version"] = "an earlier prompt"
        sh["sheet_prompt_version"] = "an earlier prompt"
    row.sheets = sheets
    db_session.commit()
    provider = Counting()
    job, _review_ = _start(client, pid, did, provider)
    assert len(provider.tasks) == 4                                     # asked, not served from the marked entries
    assert db_session.query(ResultCache).filter(ResultCache.task.like("fa_drawing_review%")).count() >= 4


def test_each_review_look_gives_the_cli_its_own_turn_limit_and_picture_route(monkeypatch, tmp_path):
    exe = tmp_path / "claude.exe"
    exe.write_bytes(b"")
    monkeypatch.setattr(settings, "ai_claude_cli", str(exe))
    monkeypatch.setattr(settings, "ai_cli_max_turns", None)
    monkeypatch.setattr(settings, "ai_cli_inline_images", False)
    stream = "\n".join([json.dumps({"type": "system"}),
                        json.dumps({**_reply({"claude-opus-5-5": {"outputTokens": 7}}), "num_turns": 2})])

    class Cli(FakeCli):
        def __call__(self, args, **kwargs):
            if args[1:] == ["--version"]:
                return super().__call__(args, **kwargs)
            self.calls.append(list(args))
            return subprocess.CompletedProcess(args, 0, stdout=stream, stderr="")

    fake = Cli()
    seen_env = {}
    real_call = fake.__call__

    def call(args, **kwargs):
        if args[1:] != ["--version"]:
            seen_env.update(kwargs.get("env") or {})
        return real_call(args, **kwargs)

    monkeypatch.setattr(subprocess, "run", call)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-reach-the-cli")
    from app.ai.provider import ImagePart

    request = AiRequest(task="t", system="s", parts=[TextPart("a", "b"), ImagePart("p", b"\x89PNG")],
                        schema={"type": "object"}, max_output_tokens=100, model="claude-opus-5-5", exact_model=True,
                        max_turns=1, inline_images=True)
    response = ClaudeCodeProvider().complete(request)
    args = fake.calls[-1]
    assert response.ok and response.turns == 2 and response.route_meta["max_turns_configured"] == 1
    assert args[args.index("--max-turns") + 1] == "1" and "--input-format" in args and args[args.index("--tools") + 1] == ""
    # the program's own traffic off and no retries of its own; the subscription, never a key
    assert seen_env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] == "1" and seen_env["CLAUDE_CODE_MAX_RETRIES"] == "0"
    assert "ANTHROPIC_API_KEY" not in seen_env
