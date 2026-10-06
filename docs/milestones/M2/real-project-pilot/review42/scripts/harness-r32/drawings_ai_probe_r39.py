"""ORCH-08C (R39-04, task item 1(b) and 1(d)): a CHILD process run inside one application tree (the frozen baseline
C:/t/iso/frozen-r12/backend or the candidate C:/t/iso/cand-r29/backend) by test_request_paths_r39.py, read-only use of the
tree, every root in a sandbox under C:/t/r2x/r<NN>-sandbox/, no model and no network: the provider is a local fake.

  drawings_ai_probe_r39.py switch <out json>
      the application's own reading of the declared application_env: settings.drawings_ai_review_enabled and
      drawing_ai_review.enabled(), and whether shop_drawings._ai_review reaches the provider (it must not when the
      setting is false). The caller sets DRAWINGS_AI_REVIEW_ENABLED in the environment.
  drawings_ai_probe_r39.py feed <out json>
      1(d): with the drawings-AI review ENABLED (test sandbox only) and a fake provider that ANSWERS every drawings question
      with an accepted match, run shop_drawings._ai_review on a minimal project (a reply document whose reference matches
      no drawing of the log, one shop drawing with a submitted revision) and record (a) that the provider was asked and its
      answer applied (the revision's status and source), (b) every project_documents column the scorer reads (role, state,
      error, sha256, reference, revision, status, system_code, extracted) before and after, (c) every ProjectDocument the
      session flushed as new or changed during the review (SQLAlchemy before_flush).
Writes only <out json> and the sandbox root of its DATABASE_URL."""
import json
import os
import pathlib
import re
import sys

MODE, OUT = sys.argv[1], pathlib.Path(sys.argv[2])
TREE = pathlib.Path(os.getcwd())
assert TREE.as_posix().lower() in ("c:/t/iso/frozen-r12/backend", "c:/t/iso/cand-r29/backend"), TREE
url = os.environ.get("DATABASE_URL", "")
assert re.match(r"sqlite:///C:/t/r2x/r\d{2}-sandbox/.+/db/default\.db$", url), url
sys.path.insert(0, str(TREE))

from app.ai import provider as prov  # noqa: E402
from app.ai.provider import AiResponse, Usage  # noqa: E402
from app.core.config import get_settings  # noqa: E402


def _forbidden(self, request):
    raise RuntimeError("drawings probe: a live provider request is forbidden")


for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
    cls.complete = _forbidden


class Fake:
    """A local fake provider: it answers each drawings question with an accepted match (feed) and counts the calls."""
    name, ready, status = "drawings-probe-fake", True, "local fake (no model)"

    def __init__(self):
        self.calls = []

    def complete(self, request):
        self.calls.append(request.task)
        if request.task == "drawings_reply_match":
            return AiResponse(data={"drawing_reference": "ABC-FA-101", "revision": "R1", "status": "approved", "confidence": 0.99,
                                    "reason_code": "REFERENCE_PARTIAL_MATCH", "requires_engineer": False}, usage=Usage(1, 1), model="fake")
        if request.task == "drawings_reference_conflict":
            return AiResponse(data={"assessment": "renumbered", "keep_reference": None, "confidence": 0.9, "reason_code": "RENUMBERED",
                                    "requires_engineer": True}, usage=Usage(1, 1), model="fake")
        return AiResponse(data={"possible_same_floor": True, "confidence": 0.9, "evidence": "fake", "requires_engineer": True}, usage=Usage(1, 1), model="fake")


fake = Fake()
prov.set_provider(fake)
st = get_settings()
from app.services import drawing_ai_review, shop_drawings  # noqa: E402

out = {"tree": TREE.as_posix(), "mode": MODE, "env": {"DRAWINGS_AI_REVIEW_ENABLED": os.environ.get("DRAWINGS_AI_REVIEW_ENABLED"),
                                                     "AI_ENABLED": os.environ.get("AI_ENABLED")},
       "settings": {"drawings_ai_review_enabled": st.drawings_ai_review_enabled, "ai_enabled": st.ai_enabled,
                    "drawings_ai_max_calls_per_sync": st.drawings_ai_max_calls_per_sync}}
on, why = drawing_ai_review.enabled()
out["enabled"] = {"on": on, "why": why}

if MODE == "switch":
    # _ai_review returns at enabled() when the setting is false: no database is touched, the provider is never asked
    try:
        shop_drawings._ai_review(None, None, ["FAS"], [], [], False, [])
        out["ai_review"] = "returned at enabled(): nothing read, nothing asked"
    except AttributeError as exc:              # enabled: it went on to query the (absent) database -- the path is live
        out["ai_review"] = f"went past enabled() to the database ({exc})"
    out["provider_calls"] = list(fake.calls)
else:
    from sqlalchemy import event, text

    from app.core.timeutils import utc_now
    from app.database import SessionLocal, engine
    from app.migrations import upgrade_to_head
    from app.models import Project, ProjectDocument, ProjectShopDrawing, ShopDrawingRevision, User
    from app.seed import seed_default_admin

    assert on, f"feed mode needs the drawings-AI review ENABLED in this test sandbox ({why})"
    upgrade_to_head(engine)
    measured = ("role", "state", "error", "sha256", "reference", "revision", "status", "system_code", "extracted")

    def snapshot():
        with engine.connect() as con:
            rows = con.execute(text(f"select id, {', '.join(measured)} from project_documents order by id")).mappings().all()
        return [dict(r) for r in rows]

    flushed = []
    with SessionLocal() as db:
        seed_default_admin(db)
        admin = db.query(User).order_by(User.id).first()
        project = Project(ep_number="990002", project_name="EP-990002 drawings probe", source_folder_path=None, created_by_id=admin.id)
        db.add(project)
        db.flush()
        now = utc_now()
        reply = ProjectDocument(project_id=project.id, role="document", path="C:/nowhere/reply.pdf", relative_path="Replies/reply.pdf",
                                filename="reply.pdf", first_seen_at=now, last_seen_at=now, acknowledged=[], findings=[], state="fresh",
                                sha256="a" * 64, reference="ABC-FA-0101", revision="R1", status="approved", system_code="FAS",
                                extracted={"records": [{"category": "reply", "reference": "ABC-FA-0101", "revision": "R1", "status": "approved",
                                                        "reply_text": "approved"}], "notes": []})
        sheet = ProjectDocument(project_id=project.id, role="document", path="C:/nowhere/sheet.pdf", relative_path="Shop/ABC-FA-101.pdf",
                                filename="ABC-FA-101.pdf", first_seen_at=now, last_seen_at=now, acknowledged=[], findings=[], state="fresh",
                                sha256="b" * 64, reference="ABC-FA-101", revision="R1", status=None, system_code="FAS",
                                extracted={"records": [{"category": "drawings", "reference": "ABC-FA-101", "revision": "R1"}], "notes": []})
        db.add_all([reply, sheet])
        drawing = ProjectShopDrawing(project_id=project.id, system_code="FAS", drawing_reference="ABC-FA-101", floor_keys=["L01"],
                                     floor_label="Level 1", active=True)
        db.add(drawing)
        db.flush()
        rev = ShopDrawingRevision(shop_drawing_id=drawing.id, revision="R1", number=1, status="under_review", submitted=True)
        db.add(rev)
        db.commit()
        before = snapshot()
        rev_before = {"status": rev.status, "source": rev.source}

        @event.listens_for(db, "before_flush")
        def _watch(session, ctx, instances):
            for o in list(session.new) + list(session.dirty):
                if isinstance(o, ProjectDocument) and (o in session.new or session.is_modified(o)):
                    flushed.append({"id": o.id, "new": o in session.new})

        rows = db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id).all()
        shop_drawings._ai_review(db, project, ["FAS"], rows, [], False, [])
        db.commit()
        db.refresh(rev)
        after = snapshot()
        out |= {"provider_calls": list(fake.calls), "revision_before": rev_before, "revision_after": {"status": rev.status, "source": rev.source},
                "project_documents_before": before, "project_documents_after": after, "measured_columns": list(measured),
                "measured_unchanged": before == after, "project_documents_flushed_during_review": flushed}
OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: out.get(k) for k in ("tree", "mode", "enabled", "provider_calls", "measured_unchanged")}, default=str))
