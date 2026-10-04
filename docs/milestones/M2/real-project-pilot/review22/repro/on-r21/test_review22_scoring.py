"""Independent offline regressions against the submitted Review 21 scorer.

Run scorer_probes.py first. Its two actual main() calls produce the source-binding
integration evidence consumed below. No provider or original document is used.
"""
import json
from pathlib import Path

import sys; sys.path.insert(0, 'C:/t/iso/work/r2x/review22/harness-r21')
import coverage_v3 as cv

ROOT = Path(__file__).parent
CTX = {"profile": "default", "variant": "EV1", "policy": "P"}
PLAN = {"doc": "one-page", "pages": 1, "sha256": "a" * 64, "extension": ".pdf"}


def emitted(page):
    return {"sha256": "a" * 64, "extracted": {"ai_evidence": {"envelopes": {
        "default|EV1": {"profile": "default", "variant": "EV1", "pages": {
            str(page): {"fields": {"own:identity": {"observations": [
                {"value": "X-3", "field": "identity", "state": "validated", "policy": "P"}
            ]}}}
        }}
    }}}}


def test_correct_source_control_has_positive_recovery():
    result = json.loads((ROOT / "score-control/ARMS-METRICS.v3.json").read_text())
    assert result["arms"]["L4"]["recovery_all_planned"]["identity"]["recovery"]["recovered_clean"] == 9


def test_wrong_source_cannot_earn_accuracy_after_coverage_rejects_it():
    result = json.loads((ROOT / "score-mismatch/ARMS-METRICS.v3.json").read_text())
    assert result["coverage"]["L4"]["summary"]["binding_reasons"]["source_mismatch"] == 4
    facts = result["arms"]["L4"]["recovery_all_planned"]
    assert facts["identity"]["recovery"].get("recovered_clean", 0) == 0


def test_page_outside_document_is_extra_even_inside_reader_limit():
    assert cv.extra_facts(emitted(3), PLAN, CTX, max_pages=4)


def test_real_page_control_is_not_extra():
    assert cv.extra_facts(emitted(1), PLAN, CTX, max_pages=4) == []


def test_page_beyond_reader_limit_control_is_extra():
    assert cv.extra_facts(emitted(5), PLAN, CTX, max_pages=4)
