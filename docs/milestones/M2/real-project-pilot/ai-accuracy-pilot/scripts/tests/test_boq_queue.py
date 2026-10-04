"""AI accuracy pilot, BOQ-T queue (boq_queue.py): offline tests with a scripted provider (no model request, no network),
a throw-away SQLite sandbox, the frozen application's own evidence_reader.verify_boq_rows / EvidenceRun / JobBudget and
the accepted r16.1 harness allowance, on the pilot sheet (EP-22510 FA Design, hash-checked) and its AI-off extraction.
Run: python -m pytest tests/test_boq_queue.py (cwd C:/t/iso/work/r2x/ai-pilot)."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile

import pytest

TMP = pathlib.Path(tempfile.mkdtemp(prefix="aipq-", dir="C:/t/iso/tmp"))
os.environ.update({"DATABASE_URL": f"sqlite:///{(TMP / 'sandbox.db').as_posix()}", "CACHE_ROOT": str(TMP / "cache"), "LIBRARY_ROOT": str(TMP / "lib"),
                   "UPLOADS_ROOT": str(TMP / "up"), "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "",
                   "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0"})
for k in ("AI_LEDGER_PATH", "AI_LEDGER_SCOPE", "AI_LEDGER_LIMITS", "AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"):
    os.environ.pop(k, None)
B = pathlib.Path("C:/t/iso/frozen-r12/backend")
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(B))
sys.path.insert(0, str(HERE))
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
os.chdir(B)

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app as api  # noqa: E402

with TestClient(api):
    pass
import pymupdf  # noqa: E402

from app.ai import evidence_reader as er  # noqa: E402
from app.ai.budget import open_budget  # noqa: E402
from app.ai.provider import AiResponse, Usage  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.services import design_sheet_extractor as dse  # noqa: E402

import boq_harness as bh  # noqa: E402
import boq_queue as bq  # noqa: E402

KEY = "EP-22510/EP-22510 Commercial/EP-22510 FA Design.pdf"
MAN = json.loads(pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
DOC = [d for d in MAN["boq_candidates"] + MAN["documents"] if (d.get("sha256") or "").startswith("6153dfe701f5")][0]
SHA = DOC["sha256"]
EXTRACTION = json.load(open(HERE / "boq/PILOT-BOQ-A-extraction.json", encoding="utf-8"))[KEY]
LIMIT = get_settings().ai_max_calls_per_document
TH = {"recheck_quantity_below": dse.RECHECK_QUANTITY_BELOW, "confirm_catalog_below": dse.CONFIRM_CATALOG_BELOW}
LONG = "\\\\?\\"


class ScriptedProvider:
    """Answers request n with part ROW-n (so a value can be traced to its request); optionally fails every k-th."""
    ready = True
    status = "scripted"

    def __init__(self, fail_every: int = 0) -> None:
        self.requests = 0
        self.fail_every = fail_every
        self.images = []

    def complete(self, request):
        self.requests += 1
        self.images.append([hashlib.sha256(p.png).hexdigest() for p in request.parts if hasattr(p, "png")])
        if self.fail_every and self.requests % self.fail_every == 0:
            return AiResponse(data=None, usage=Usage(input_tokens=None, output_tokens=None), model="scripted", error="transport", error_detail="scripted failure")
        return AiResponse(data={"part_number": f"ROW-{self.requests}", "quantity": str(self.requests), "description": "scripted", "legible": True,
                                "row_is_heading": False}, usage=Usage(input_tokens=100, output_tokens=10), model="scripted", latency_ms=1)


@pytest.fixture(autouse=True)
def _fresh_usage():
    from app.models import AiUsage
    with SessionLocal() as db:
        db.query(AiUsage).delete()
        db.commit()
    yield


def _pdf():
    data = open(LONG + DOC["staged_path"].replace("/", "\\"), "rb").read()
    assert hashlib.sha256(data).hexdigest() == SHA
    return pymupdf.open(stream=data, filetype="pdf")


def _queue(extraction=EXTRACTION):
    return bq.risk_queue(extraction["lines"], extraction["issues"], sha256=SHA, cap=LIMIT, **TH)


def _run_queue(provider, allowance, queue=None, profile="BOQ-T"):
    with SessionLocal() as db, _pdf() as pdf:
        run = er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant="EV1", fresh=True)
        res, info = bq.verify_queue(er, run, pdf, db=db, open_budget=open_budget, harness=bh, allowance=allowance, scope="t", profile=profile,
                                    lines=EXTRACTION["lines"], issues=EXTRACTION["issues"], queue=queue or _queue(), sha256=SHA,
                                    max_calls_per_document=LIMIT, render_dpi=dse.RENDER_DPI)
        return res, run, info


def test_thresholds_are_the_applications_own():
    assert TH == {"recheck_quantity_below": 90, "confirm_catalog_below": 90} and LIMIT == 12


def test_declared_order_for_the_pilot_sheet():
    q = _queue()
    tiers = [(i["tier"], i["kind"], i["index"]) for i in q["order"]]
    assert tiers[:4] == [("1_held", "issue", n) for n in range(4)]
    # risky accepted lines by signal count: SIGA-IB (raw 'A' rewritten to 4, q 75, catalog 89), the battery (count from
    # the description, no quantity confidence), the panel line (no part)
    assert tiers[4:7] == [("2_risk", "line", 5), ("2_risk", "line", 1), ("2_risk", "line", 0)]
    assert q["order"][4]["signals"] == ["quantity_rewritten", "low_quantity_confidence", "low_catalog_confidence"]
    assert q["order"][5]["signals"] == ["quantity_not_from_cell", "low_quantity_confidence"]
    assert q["order"][6]["signals"] == ["no_part"]
    assert [i["tier"] for i in q["order"][7:]] == ["3_audit", "3_audit", "4_residual_audit", "4_residual_audit", "4_residual_audit"]
    assert len(q["order"]) == LIMIT and len(q["not_reached"]) == 18 - LIMIT
    assert sorted((i["kind"], i["index"]) for i in q["order"] + q["not_reached"]) == sorted([("issue", n) for n in range(4)] + [("line", n) for n in range(14)])


def test_order_does_not_depend_on_scored_values_of_confident_rows():
    """Changing confident rows' printed quantity and part (consistently, as read) moves no row: the audit rank uses position only."""
    changed = json.loads(json.dumps(EXTRACTION))
    for l in changed["lines"][2:]:
        if l["catalog_no"] != "SIGA-IB":
            l["quantity"] = l["raw_quantity"] = "999"
            l["catalog_no"] = "X" + l["catalog_no"]
    assert [(i["kind"], i["index"]) for i in _queue(changed)["order"]] == [(i["kind"], i["index"]) for i in _queue()["order"]]


def test_one_allowance_twelve_requests_rows_in_declared_order_no_leakage():
    p = ScriptedProvider()
    res, run, info = _run_queue(p, bh.DocAllowance(str(TMP / "a1.sqlite")))
    assert p.requests == LIMIT and info["calls_after"] == LIMIT and not info["resumed"]
    assert [r["queue"]["position"] for r in res] == list(range(1, LIMIT + 1))
    for n, r in enumerate(res, 1):
        assert r["request"] == "ok"
        assert r["blind"]["part_number"] == f"ROW-{n}" and r["blind"]["quantity"] == str(n)   # the n-th answer stays with the n-th row
    for r, item in zip(res, _queue()["order"]):
        if item["kind"] == "line":
            src = EXTRACTION["lines"][item["index"]]
            assert r["row"]["part_number"] == src["catalog_no"] and r["row"]["quantity"] == src["quantity"] and r["accepted_by_reader"]
        else:
            assert r["row"]["part_number"] == EXTRACTION["issues"][item["index"]]["detail"]["catalog_no"] and not r["accepted_by_reader"]
    assert len({tuple(i) for i in p.images}) == LIMIT                 # every request carried its own row crop


def test_a_second_run_gets_no_fresh_allowance():
    allowance = bh.DocAllowance(str(TMP / "a2.sqlite"))
    _run_queue(ScriptedProvider(), allowance)
    p2 = ScriptedProvider()
    res, run, info = _run_queue(p2, allowance)
    assert p2.requests == 0 and info["resumed"] and info["calls_before"] == LIMIT
    assert all(r["request"].startswith("budget") and r["reasons"] == ["no reading"] for r in res)


def test_failed_requests_are_consumed_and_marked():
    p = ScriptedProvider(fail_every=4)
    res, run, info = _run_queue(p, bh.DocAllowance(str(TMP / "a3.sqlite")))
    assert p.requests == LIMIT
    failed = [r for r in res if r["request"] == "transport"]
    assert len(failed) == LIMIT // 4 and all(r["state"] == "unverified" for r in failed)


def test_a_longer_queue_is_refused_beyond_the_cap_and_marked_budget():
    q = bq.risk_queue(EXTRACTION["lines"], EXTRACTION["issues"], sha256=SHA, cap=18, **TH)
    p = ScriptedProvider()
    res, run, info = _run_queue(p, bh.DocAllowance(str(TMP / "a4.sqlite")), queue=q)
    assert p.requests == LIMIT
    assert [r["request"] for r in res[LIMIT:]] == ["budget: calls_per_document"] * (18 - LIMIT)
    assert all(r["state"] == "unverified" for r in res[LIMIT:])


def test_s_boq_selection_through_the_unchanged_harness():
    """BOQ-S: the accepted EV1 selection (held rows + the seeded 20 % audit) through boq_harness.verify_sheet."""
    sel = er.boq_rows_to_verify([dict(l, _accepted=True) for l in EXTRACTION["lines"]], [], variant="EV1", sha256=SHA)
    p = ScriptedProvider()
    with SessionLocal() as db, _pdf() as pdf:
        run = er.EvidenceRun(db=db, project_id=None, provider=p, budget=open_budget(db, None), variant="EV1", fresh=True)
        res, info = bh.verify_sheet(er, run, pdf, db=db, open_budget=open_budget, allowance=bh.DocAllowance(str(TMP / "a5.sqlite")), scope="t",
                                    profile="BOQ-S", lines=EXTRACTION["lines"], issues=EXTRACTION["issues"], variant="EV1", sha256=SHA,
                                    max_calls_per_document=LIMIT, render_dpi=dse.RENDER_DPI)
    assert p.requests == len(sel) + 4 == len(res) <= LIMIT
    print("BOQ-S rows", len(res), "audit", [r.get("y_px") for r, _ in sel])
