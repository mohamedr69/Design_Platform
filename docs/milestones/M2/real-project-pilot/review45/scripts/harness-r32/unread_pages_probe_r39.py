"""ORCH-08C (R39-06, task item 2): a CHILD process run inside the candidate tree (C:/t/iso/cand-r30n/backend, read-only use)
by test_unread_pages_r39.py: Verification 39's scenarios reproduced with the candidate's OWN reader and budget, no
database, no model (a local fake provider answers every request):
  A  4 + 4 calls on pages 1 and 2, then the reader's own MAX_CALLS_PER_DOCUMENT (8, checked between pages) skips pages 3
     and 4 without any exhaustion ('budget: calls per document');
  B  7 + 5 calls: the per-document JobBudget (12) is exhausted on page 2; pages 3 and 4 are skipped ('budget: <limit>');
  C  the evidence attempt raises (evidence_stage records outcome 'failed' and no page).
For each, the reader's coverage and the attempt summary the application stores (evidence_reader.merge_evidence) are
written to <out json>; the test derives the unread pages from both. Usage: unread_pages_probe_r39.py <out json>"""
import json
import os
import pathlib
import sys

OUT = pathlib.Path(sys.argv[1])
TREE = pathlib.Path(os.getcwd())
assert TREE.as_posix().lower() == "c:/t/iso/cand-r30n/backend", TREE
assert os.environ.get("AI_ENABLED") == "false"
sys.path.insert(0, str(TREE))

from app.ai import evidence_reader as er  # noqa: E402
from app.ai.budget import JobBudget, Limits  # noqa: E402
from app.ai.provider import AiResponse, TextPart, Usage  # noqa: E402


class DB:
    def add(self, *a, **k):
        pass

    def get(self, *a, **k):
        return None

    def commit(self):
        pass


class Prov:
    name, ready, status = "unread-probe-fake", True, "local fake (no model)"

    def __init__(self):
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return AiResponse(data={"ok": True}, usage=Usage(10, 2), model="fake")


class Page:
    def get_text(self):
        return ""


class Pdf:
    def __init__(self, n):
        self.page_count = n

    def __getitem__(self, i):
        return Page()


def scenario(calls_per_page, pages=4):
    prov = Prov()
    run = er.EvidenceRun(db=DB(), project_id=1, provider=prov, budget=JobBudget(limits=Limits.from_settings(), calls_today_before=0),
                         variant="EV1", fresh=True)
    seq = list(calls_per_page)

    def fake_required(run, page, *, sha256, number, facts, reason, ocr_lines=None):
        for _ in range(seq[number - 1]):
            run.call(sha256=sha256, task="discover_page", page=number, reason=reason, parts=[TextPart("t", f"p{number}")], schema={"type": "object"})
        return {"_outcome": "completed", "_observations": [], "_fields": {}, "_requests": {}}

    saved = er._read_page_required, er.triggers
    er._read_page_required = fake_required
    er.triggers = lambda facts, **kw: ["document_empty"]
    try:
        _obs, cov = er.read_document(run, Pdf(pages), sha256="0" * 64, records=[], observations=[])
    finally:
        er._read_page_required, er.triggers = saved
    attempt = {"attempt": 1, "at": "2026-10-04T00:00:00+00:00", "version": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION,
               "outcome": cov.get("outcome"), "coverage": cov, "observations": [], "calls": [], "models": []}
    merged = er.merge_evidence(None, attempt, sha256="0" * 64, profile="default", variant="EV1")
    return {"calls_per_page": calls_per_page, "coverage": cov, "stored_summary": merged["attempts"][-1], "provider_calls": prov.calls,
            "run_exhausted": run.exhausted, "run_calls": run.calls}


def exception_case(pages=4):
    attempt = {"attempt": 1, "at": "2026-10-04T00:00:00+00:00", "version": er.READER_VERSION, "policy": er.EVIDENCE_POLICY_VERSION,
               "outcome": "failed", "error": "RuntimeError: injected reader exception", "coverage": {"pages": []}, "observations": [],
               "calls": [], "models": []}
    merged = er.merge_evidence(None, attempt, sha256="0" * 64, profile="default", variant="EV1")
    return {"in_scope_pages": pages, "stored_summary": merged["attempts"][-1],
            "evidence_stage_branch": "except Exception -> attempt.update(outcome='failed', error=..., coverage={'pages': []})"}


src = (TREE / "app/ai/evidence_reader.py").read_text(encoding="utf-8")
out = {"reader_soft_cap": er.MAX_CALLS_PER_DOCUMENT, "job_calls_per_document": Limits.from_settings().max_calls_per_document,
       "evidence_stage_exception_branch_present": 'attempt.update(outcome="failed", error=f"{type(exc).__name__}: {exc}"[:300], coverage={"pages": []}, observations=[])' in src,
       "A": scenario([4, 4, 4, 4]), "B": scenario([7, 7, 7, 7]), "C": exception_case()}
OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: (v["coverage"]["outcome"] if isinstance(v, dict) and "coverage" in v else v) for k, v in out.items() if k != "C"}, default=str))
