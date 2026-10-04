"""R40 (item 4): Verification 39's scenarios A (4 + 4), B (7 + 5) and C (reader exception) through the candidate's REAL
evidence_stage (real sandbox database row, real tiny PDF, real JobBudget from open_budget, real merge_evidence), a local fake
provider passed as the lane passes its chain; then the review39 rule from my twin: unread_pages_of_attempt -> LaneRecorder
-> documents() status, and score_bcr_r32.unread_pages(). Also: every get_provider() in the application modules is
replaced by a recorder that RAISES -- it must never be called on this path when the provider is passed (C / R lanes do
not install the chain as the global provider). Run with cwd C:/t/iso/cand-r29/backend; env: DATABASE_URL in my sandbox,
lane C's AI_EVIDENCE_* switches. Usage: unread_r40.py <out json>"""
import json
import os
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1])
TREE = pathlib.Path(os.getcwd())
assert TREE.as_posix().lower() == "c:/t/iso/cand-r29/backend"
assert "scratchpad/r40" in os.environ["DATABASE_URL"].replace("\\", "/")
sys.path.insert(0, str(TREE))

import pymupdf  # noqa: E402

from app.ai import provider as prov  # noqa: E402
from app.ai.provider import AiResponse, TextPart, Usage  # noqa: E402

GP_CALLS = []


def _gp(*a, **k):
    GP_CALLS.append("get_provider")
    raise RuntimeError("r40: get_provider() called on the C path")


prov.get_provider = _gp
for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
    cls.complete = lambda self, request: (_ for _ in ()).throw(RuntimeError("r40: real provider"))

from app.ai import evidence_reader as er  # noqa: E402
from app.ai import submittal_reader  # noqa: E402
import app.services.drawing_ai_review as dar  # noqa: E402

submittal_reader.get_provider = _gp
dar.get_provider = _gp
from app.core.timeutils import utc_now  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.migrations import upgrade_to_head  # noqa: E402
from app.models import Project, ProjectDocument, User  # noqa: E402
from app.seed import seed_default_admin  # noqa: E402

import run_state_r38 as RS  # noqa: E402  (twin)
import score_bcr_r32 as S  # noqa: E402  (twin)

submittal_reader.available = lambda project, provider=None: None      # as the C / R lanes do


class Prov:
    name, ready, status = "r40-fake", True, "local fake"

    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return AiResponse(data={"ok": True}, usage=Usage(10, 2), model="claude-sonnet-5")


def make_pdf(path, pages):
    doc = pymupdf.open()
    for i in range(pages):
        p = doc.new_page()
        p.insert_text((72, 72), f"r40 synthetic page {i + 1}")
    doc.save(str(path))
    doc.close()


def run_case(db, project, label, calls_per_page=None, raise_reader=False, pages=4):
    root = pathlib.Path(os.environ["DATABASE_URL"].split("sqlite:///", 1)[1]).parent.parent
    pdf = root / f"{label}.pdf"
    make_pdf(pdf, pages)
    sha = (label * 64)[:64]
    now = utc_now()
    row = ProjectDocument(project_id=project.id, role="document", path=str(pdf), relative_path=f"{label}.pdf", filename=f"{label}.pdf",
                          first_seen_at=now, last_seen_at=now, acknowledged=[], findings=[], state="fresh", sha256=sha,
                          extracted={"records": [], "observations": [], "notes": []})
    db.add(row)
    db.commit()
    p = Prov()
    saved = er._read_page_required, er.triggers, er.read_document
    seq = list(calls_per_page or [])

    def fake_required(run, page, *, sha256, number, facts, reason, ocr_lines=None):
        for i in range(seq[number - 1]):
            run.call(sha256=sha256, task="discover_page", page=number, reason=reason, parts=[TextPart("t", f"{label}-p{number}-{i}")], schema={"type": "object"})
        return {"_outcome": "evidence", "_observations": [], "_fields": {}, "_requests": {}}

    def raising(*a, **k):
        raise RuntimeError("r40 injected evidence-reader exception")

    er._read_page_required = fake_required
    er.triggers = lambda facts, **kw: ["document_empty"]
    if raise_reader:
        er.read_document = raising
    try:
        counts = er.evidence_stage(db, project, [(row, pdf)], provider=p, variant="EV1")
        db.commit()
    finally:
        er._read_page_required, er.triggers, er.read_document = saved
    db.refresh(row)
    attempt = ((row.extracted or {}).get("ai_evidence") or {}).get("attempts")[-1]
    unread = RS.unread_pages_of_attempt(attempt, pages)
    rec = RS.LaneRecorder("C", [{"pool_id": label}])
    rec.unread_pages(label, unread)
    rec.set(label, "COMPLETE", "read by the application's evidence stage")
    doc = rec.documents()[label]
    lane = {"lane": "C", "documents": {label: {"status": doc["status"], "unread_pages": doc["unread_pages"], "unread_page_count": doc["unread_page_count"],
                                              "partially_read_pages": doc["partially_read_pages"]}}}
    return {"calls_per_page": calls_per_page, "raise_reader": raise_reader, "provider_calls": p.calls, "stage_counts": counts,
            "attempt_outcome": attempt.get("outcome"), "attempt_error": attempt.get("error"),
            "attempt_pages": attempt.get("pages"), "unread": [(u["page"], u["kind"], u["partial"]) for u in unread],
            "recorder_status": doc["status"], "recorder_reason": doc["reason"], "classes": doc["classes"],
            "events": [(e["kind"], e["class"], e["page"]) for e in rec.events], "scorer_unread": S.unread_pages(lane)}


def main():
    upgrade_to_head(engine)
    out = {"reader_soft_cap": er.MAX_CALLS_PER_DOCUMENT, "policy": er.EVIDENCE_POLICY_VERSION}
    with SessionLocal() as db:
        seed_default_admin(db)
        admin = db.query(User).order_by(User.id).first()
        project = Project(ep_number="990004", project_name="EP-990004 r40 unread", source_folder_path=None, created_by_id=admin.id)
        db.add(project)
        db.commit()
        out["A"] = run_case(db, project, "a", [4, 4, 4, 4])
        out["B"] = run_case(db, project, "b", [7, 7, 7, 7])
        out["C"] = run_case(db, project, "c", raise_reader=True)
        out["D_three_pages_3_3_3"] = run_case(db, project, "d", [3, 3, 3], pages=3)
    out["get_provider_calls"] = len(GP_CALLS)
    OUT.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: ({kk: vv for kk, vv in v.items() if kk in ("provider_calls", "attempt_outcome", "unread", "recorder_status", "classes", "events")}
                          if isinstance(v, dict) else v) for k, v in out.items()}, indent=1, default=str))


main()
