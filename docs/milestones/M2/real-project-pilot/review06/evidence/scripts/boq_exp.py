"""BOQ deterministic experiment on the isolated candidate: knob overrides, then the frozen BOQ evaluator.
Usage: boq_exp.py <confirm_below|default> <hold on|off> -- <m2_boq_eval args>"""
import os, sys
os.environ["AI_ENABLED"] = "false"
sys.path.insert(0, r"C:/t/iso/ep-platform/backend"); os.chdir(r"C:/t/iso/ep-platform/backend")
from app.services import design_sheet_extractor as dse
if sys.argv[1] != "default":
    dse.CONFIRM_CATALOG_BELOW = float(sys.argv[1])
dse.HOLD_ON_PASS_DISAGREEMENT = sys.argv[2] == "on"
print("PARSER_VERSION", dse.PARSER_VERSION, "CONFIRM_CATALOG_BELOW", dse.CONFIRM_CATALOG_BELOW, "HOLD_ON_PASS_DISAGREEMENT", dse.HOLD_ON_PASS_DISAGREEMENT, flush=True)
from scripts import m2_boq_eval
raise SystemExit(m2_boq_eval.main(sys.argv[4:]))
