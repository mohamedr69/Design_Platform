"""Round 2: the BOQ profile-A (deterministic, AI off) baseline on the accepted candidate frozen-r12, default knobs,
scored by the frozen BOQ evaluator (scripts/m2_boq_eval.py). Usage: boq_baseline.py -- <m2_boq_eval args>"""
import os
import sys

os.environ["AI_ENABLED"] = "false"
sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
os.chdir("C:/t/iso/frozen-r12/backend")
from app.services import design_sheet_extractor as dse  # noqa: E402

print("PARSER_VERSION", dse.PARSER_VERSION, "CONFIRM_CATALOG_BELOW", dse.CONFIRM_CATALOG_BELOW, "HOLD_ON_PASS_DISAGREEMENT", dse.HOLD_ON_PASS_DISAGREEMENT, flush=True)
from scripts import m2_boq_eval  # noqa: E402

raise SystemExit(m2_boq_eval.main(sys.argv[2:]))
