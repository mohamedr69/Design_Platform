"""ORCH-09 (R40DECL-IMPL): the live lane's own environment checks, run OFFLINE in one application tree for one lane, with the
environment the bound runner would give that lane in live mode (runner_r32.lane_env('live', ...)) -- so a declared value
the application cannot parse (the R39-18 class: '12.0' passes validate_declaration and fails in the lane) is found BEFORE
any owner authorization is consumed.

Usage (started by preflight_r40.py, never by hand): <venv python> -B lane_env_check_r40.py <lane> <cfg json> <out json>
  cwd: the lane's tree (B: C:/t/iso/frozen-r12/backend; C, R, P: C:/t/iso/cand-r29/backend)
What it does, exactly as lane_r32.py does before anything is built (live mode):
  get_settings(); preflight_r32.verify_lane_environment(lane, switches, provider_env, os.environ, settings, mode='live');
  preflight_r32.verify_application_env(lane, application_env, os.environ, settings); drawing_ai_review.enabled() is False.
What it never does: build a provider, open a database, touch the AI ledger (AI_LEDGER_PATH is only a string in the
settings), run the CLI, read a token (none is set), or write anything but <out json>."""
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
LANE, CFG_PATH, OUT = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
CFG = json.loads(CFG_PATH.read_text(encoding="utf-8"))
HARNESS = pathlib.Path(CFG["harness"])
sys.path.insert(0, str(HARNESS))
TREE = pathlib.Path(os.getcwd())
sys.path.insert(0, str(TREE))
assert "R34_OWNER_DISPATCH_TOKEN" not in os.environ, "no token in an offline check"

import preflight_r32 as PF  # noqa: E402
from app.core.config import get_settings  # noqa: E402

out = {"lane": LANE, "tree": TREE.as_posix(), "checks": {}}
settings = get_settings()
try:
    env_check = PF.verify_lane_environment(LANE, CFG["lane_switches"][LANE], CFG["provider_env"], os.environ, settings, mode="live")
    out["checks"]["verify_lane_environment"] = {"result": "PASSED", "switches": env_check["switches"],
                                                "provider_env_verified": env_check["provider_env_verified"]}
except PF.Refused as exc:
    out["checks"]["verify_lane_environment"] = {"result": "REFUSED", "reason": str(exc)}
try:
    app_check = PF.verify_application_env(LANE, CFG["application_env"], os.environ, settings)
    out["checks"]["verify_application_env"] = {"result": "PASSED"} | app_check
except PF.Refused as exc:
    out["checks"]["verify_application_env"] = {"result": "REFUSED", "reason": str(exc)}
from app.services import drawing_ai_review as dar  # noqa: E402

on, why = dar.enabled()
out["checks"]["drawing_ai_review_enabled"] = {"enabled": bool(on), "why": why, "result": "PASSED" if not on else "REFUSED"}
names = ("ai_provider", "ai_model_small", "ai_model_standard", "ai_effort", "ai_timeout_s", "ai_cli_timeout_s", "ai_claude_cli", "ai_ledger_scope",
         "ai_max_calls_per_project_per_day", "ai_read_max_calls_per_project_per_day", "ai_max_calls_per_document", "ai_max_elapsed_s_per_job",
         "ai_max_cost_per_job", "ai_price_input_per_million", "ai_price_output_per_million", "ai_price_cached_input_per_million", "ai_read_max_elapsed_s",
         "ai_read_max_calls_per_document", "ai_cache_ttl_days", "ai_max_input_tokens_per_task", "ai_max_output_tokens_per_task", "ai_max_retries",
         "ai_max_concurrency", "ai_max_escalations_per_document", "ai_read_effort", "ai_enabled", "drawings_ai_review_enabled", "ai_evidence_variant")
out["settings_parsed"] = {n: getattr(settings, n, "<absent>") for n in names}
out["ok"] = all(v.get("result") == "PASSED" for v in out["checks"].values())
OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"lane": LANE, "ok": out["ok"], "checks": {k: v["result"] for k, v in out["checks"].items()}}))
