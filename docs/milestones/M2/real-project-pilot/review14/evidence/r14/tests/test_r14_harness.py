"""R14-01 / R14-02 offline tests. A scripted provider only (no model request, no network); a throw-away SQLite
sandbox; the frozen candidate's own evidence_reader.verify_boq_rows, JobBudget and EvidenceRun on the exposed EP-8430
design sheet (the H-06 sheet, hash-checked). Each defect is shown on the SUBMITTED code path first, then the corrected
one. Run: python -m pytest tests/test_r14_harness.py (cwd C:/t/iso/work/r2x/r14)."""
import hashlib
import json
import os
import pathlib
import sys
import tempfile
import time

import pytest

TMP = pathlib.Path(tempfile.mkdtemp(prefix="r14-", dir="C:/t/iso/tmp"))
os.environ.update({"DATABASE_URL": f"sqlite:///{(TMP / 'sandbox.db').as_posix()}", "CACHE_ROOT": str(TMP / "cache"), "LIBRARY_ROOT": str(TMP / "lib"),
                   "UPLOADS_ROOT": str(TMP / "up"), "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
                   "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "",
                   "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0"})
for k in ("AI_LEDGER_PATH", "AI_LEDGER_SCOPE", "AI_LEDGER_LIMITS"):
    os.environ.pop(k, None)
B = pathlib.Path("C:/t/iso/frozen-r12/backend")
sys.path.insert(0, str(B))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
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

import boq_contract as bc  # noqa: E402
import boq_harness as bh  # noqa: E402

SHEET = pathlib.Path("C:/t/holdout/stage/EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf")
SHA = "719f8714d2a75673c8ba390a884a2d2889b2438fd587eaa2c42f62d75f344fec"
EXTRACTION = [v for k, v in json.load(open("C:/t/iso/work/r2x/boq/holdout-A-r12-extraction.json", encoding="utf-8")).items() if "8430" in k][0]
LIMIT = get_settings().ai_max_calls_per_document


class ScriptedProvider:
    """Answers every BOQ-row request with a fixed legible row; optionally fails every n-th request (a transport error)."""
    ready = True
    status = "scripted"

    def __init__(self, fail_every: int = 0) -> None:
        self.requests = 0
        self.fail_every = fail_every

    def complete(self, request):
        self.requests += 1
        if self.fail_every and self.requests % self.fail_every == 0:
            return AiResponse(data=None, usage=Usage(input_tokens=None, output_tokens=None), model="scripted", error="transport", error_detail="scripted failure")
        return AiResponse(data={"part_number": "PRS-X", "quantity": "1", "description": "scripted", "legible": True, "row_is_heading": False},
                          usage=Usage(input_tokens=100, output_tokens=10), model="scripted", latency_ms=1)


@pytest.fixture(autouse=True)
def _fresh_usage():
    """Each test starts with an empty sandbox usage table: the application's per-project day count (60) reads it, and
    earlier tests' scripted requests must not starve a later test (that limit is exercised by xtrack, not here)."""
    from app.models import AiUsage
    with SessionLocal() as db:
        db.query(AiUsage).delete()
        db.commit()
    yield


def _sheet():
    data = SHEET.read_bytes()
    assert hashlib.sha256(data).hexdigest() == SHA
    return pymupdf.open(stream=data, filetype="pdf")


def _run(db, provider, variant="EV2"):
    return er.EvidenceRun(db=db, project_id=None, provider=provider, budget=open_budget(db, None), variant=variant, fresh=True)


def _submitted(provider, variant="EV2"):
    with SessionLocal() as db, _sheet() as pdf:
        run = _run(db, provider, variant)
        res = bh.verify_sheet_submitted(er, run, pdf, db=db, open_budget=open_budget, lines=EXTRACTION["lines"], issues=EXTRACTION["issues"],
                                        variant=variant, sha256=SHA, max_calls_per_document=LIMIT, render_dpi=dse.RENDER_DPI)
        return res, run


def _corrected(provider, allowance, scope="t", profile="EV2", variant="EV2"):
    with SessionLocal() as db, _sheet() as pdf:
        run = _run(db, provider, variant)
        res, info = bh.verify_sheet(er, run, pdf, db=db, open_budget=open_budget, allowance=allowance, scope=scope, profile=profile,
                                    lines=EXTRACTION["lines"], issues=EXTRACTION["issues"], variant=variant, sha256=SHA,
                                    max_calls_per_document=LIMIT, render_dpi=dse.RENDER_DPI)
        return res, run, info


# --- R14-01: budget continuity ----------------------------------------------------------------------------------------
def test_limit_is_the_declared_frozen_default():
    assert LIMIT == 12


def test_submitted_loop_sends_more_than_the_document_limit():
    p = ScriptedProvider()
    res, run = _submitted(p)
    read = [r for r in res if r.get("state") != "no_geometry"]
    assert p.requests > LIMIT                        # the defect: every chunk had a fresh 12-call budget
    assert p.requests == len(read)                   # every row with geometry reached the provider (EV2: all rows)


def test_corrected_loop_sends_exactly_the_document_limit_across_chunk_boundaries():
    p = ScriptedProvider()
    res, run, info = _corrected(p, bh.DocAllowance(str(TMP / "allow-a.sqlite")))
    assert p.requests == LIMIT                       # 11 in the first chunk, the 12th in the second chunk, none after
    assert run.exhausted == "calls_per_document"
    read = [r for r in res if r.get("state") != "no_geometry"]
    answered = [r for r in read if r.get("reasons") != ["no reading"]]
    refused = [r for r in read if r.get("reasons") == ["no reading"]]
    assert len(answered) == LIMIT and len(refused) == len(read) - LIMIT
    assert read[:LIMIT] == answered                  # earlier evidence intact, in order
    budget_log = [e for e in run.log if str(e.get("outcome", "")).startswith("budget")]
    assert len(budget_log) == len(refused) and all(e["outcome"] == "budget: calls_per_document" for e in budget_log)


def test_failed_requests_count_against_the_document_budget():
    p = ScriptedProvider(fail_every=3)
    res, run, info = _corrected(p, bh.DocAllowance(str(TMP / "allow-b.sqlite")))
    assert p.requests == LIMIT                       # a transport failure is a request; no extra allowance for it
    assert sum(1 for e in run.log if e.get("outcome") == "transport") == LIMIT // 3


def test_resume_or_new_process_gets_no_fresh_allowance_for_the_same_document_and_profile():
    allowance = bh.DocAllowance(str(TMP / "allow-c.sqlite"))
    p1 = ScriptedProvider()
    _corrected(p1, allowance)
    p2 = ScriptedProvider()
    res, run, info = _corrected(p2, allowance)
    assert p1.requests == LIMIT and p2.requests == 0 and info["resumed"] and info["calls_before"] == LIMIT
    p3 = ScriptedProvider()
    _corrected(p3, allowance, profile="EV1-other-profile", variant="EV2")
    assert p3.requests == LIMIT                      # per document PER PROFILE, as declared


def test_elapsed_basis_is_the_first_start_not_the_chunk():
    allowance = bh.DocAllowance(str(TMP / "allow-d.sqlite"))
    allowance.load("t", "EV2", SHA)
    import sqlite3
    con = sqlite3.connect(allowance.path, isolation_level=None)
    con.execute("update allowance set first_started = ?", (time.time() - (get_settings().ai_max_elapsed_s_per_job + 5),))
    con.close()
    p = ScriptedProvider()
    res, run, info = _corrected(p, allowance)
    assert p.requests == 0 and run.exhausted == "elapsed_time"


# --- R14-02: typed comparison -----------------------------------------------------------------------------------------
@pytest.mark.parametrize("a,b,kind", [("PT-1S", "PT-1S+", "part"), ("1.0", "10", "quantity"), ("-1", "1", "quantity"), (0, None, "quantity")])
def test_submitted_comparison_equates_different_values_and_the_contract_does_not(a, b, kind):
    assert bc.old_values_equal(a, b) is True         # the submitted defect, reproduced on the submitted expression
    new = bc.parts_equal(a, b) if kind == "part" else bc.quantities_equal(a, b)
    assert new is False


def test_identical_value_control():
    for a in ("PRS-CSNKP", "2", "LBB4430/00"):
        assert bc.old_values_equal(a, a) and bc.parts_equal(a, a)
    assert bc.quantities_equal("2", "2")


def test_declared_numeric_contract():
    assert bc.quantities_equal("1", "1.0") and bc.quantities_equal("1 no.", "1") and bc.quantities_equal("1,000", "1000")
    assert not bc.quantities_equal("1 m", "1") and not bc.quantities_equal("0", "")
    assert bc.parse_quantity("?") == ("unreadable",) and bc.parse_quantity("") == ("absent",) and bc.parse_quantity("0")[0] == "number"
    assert not bc.quantities_equal("?", "?")         # unreadable is a state, never an agreement
    assert bc.parts_equal(None, "  ") and not bc.parts_equal(None, "PRS-X")


def _pairs_two_keypads():
    """Two source rows, same part, different truth quantities (the H-06 shape), both emitted as '2'."""
    return [{"page": 1, "emitted": {"part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad", "accepted": True},
             "truth": {"part_number": "PRS-CSNKP", "quantity": "1", "description": "Numeric Keypad"}},
            {"page": 1, "emitted": {"part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad", "accepted": True},
             "truth": {"part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}}]


def test_repeated_part_submitted_join_takes_the_first_row_and_the_contract_uses_order():
    pairs = _pairs_two_keypads()
    second = {"page": 1, "row": {"part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}, "accepted_by_reader": True}
    assert bc.old_join(pairs, second)[0]["truth"]["quantity"] == "1"          # the defect: the second row gets the first row's truth
    emitted = [{"id": "e1", "page": 1, "y": 980.5, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"},
               {"id": "e2", "page": 1, "y": 2718.5, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}]
    truth = [{"ordinal": 6, "page": 1, "part_number": "PRS-CSNKP", "quantity": "1", "description": "Numeric Keypad"},
             {"ordinal": 37, "page": 1, "part_number": "PRS-CSNKP", "quantity": "2", "description": "Numeric Keypad"}]
    j = bc.join_rows(emitted, truth)
    assert ("e2", 37, "matched") in j["pairs"] and ("e1", 6, "matched") in j["pairs"]


def test_same_prefix_description_collision():
    pairs = [{"page": 1, "emitted": {"part_number": None, "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)", "accepted": True},
              "truth": {"part_number": "LBB4428/00-EU", "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)"}},
             {"page": 1, "emitted": {"part_number": None, "quantity": "1", "description": "Power Amplifier 4 X 125 W (EU)", "accepted": True},
              "truth": {"part_number": "PRS-4P125-EU", "quantity": "3", "description": "Power Amplifier 4 X 125 W (EU)"}}]
    r = {"page": 1, "row": {"part_number": None, "quantity": "1", "description": "Power Amplifier 4 X 125 W (EU)"}, "accepted_by_reader": True}
    assert bc.old_join(pairs, r)[0]["truth"]["part_number"] == "LBB4428/00-EU"   # the defect: 12-character prefix, first candidate
    emitted = [{"id": "a", "page": 1, "y": 1214, "part_number": None, "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)"},
               {"id": "b", "page": 1, "y": 1260, "part_number": None, "quantity": "1", "description": "Power Amplifier 4 X 125 W (EU)"}]
    truth = [{"ordinal": 11, "page": 1, "part_number": "LBB4428/00-EU", "quantity": "1", "description": "Power Amplifier 8 X 60 W (EU)"},
             {"ordinal": 12, "page": 1, "part_number": "PRS-4P125-EU", "quantity": "3", "description": "Power Amplifier 4 X 125 W (EU)"}]
    assert ("b", 12, "matched") in bc.join_rows(emitted, truth)["pairs"]


def test_indistinguishable_rows_are_held_not_guessed():
    emitted = [{"id": "x", "page": 1, "y": 100, "part_number": "A-1", "quantity": "1", "description": "Widget"}]
    truth = [{"ordinal": 1, "page": 1, "part_number": "A-1", "quantity": "1", "description": "Widget"},
             {"ordinal": 2, "page": 1, "part_number": "A-1", "quantity": "1", "description": "Widget"}]
    j = bc.join_rows(emitted, truth)
    assert j["pairs"] == [("x", 1, "ambiguous")] and j["unmatched_truth"] == [2]
