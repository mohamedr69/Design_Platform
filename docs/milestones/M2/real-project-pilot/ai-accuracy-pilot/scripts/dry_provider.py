"""PILOT_DRY=1 only: a scripted provider that answers every request with a minimal schema-shaped object (no model, no
network), and the dry-run redirections (runs folder, ledger file, cross-track counter). Used to exercise the runners'
plumbing before any real request; never active in a real run (the runners assert PILOT_DRY is unset for real tags)."""
import os

DRY = os.environ.get("PILOT_DRY") == "1"
DRY_RUNS = "C:/t/r2x/dry-runs"
DRY_LEDGER = "C:/t/r2x/dry-runs/dry-ledger.sqlite"
DRY_XTRACK = "C:/t/r2x/dry-runs/dry-project-day.sqlite"
DRY_ALLOWANCE = "C:/t/r2x/dry-runs/dry-allowance.sqlite"


def _value(schema: dict):
    t = schema.get("type")
    if isinstance(t, list):
        t = [x for x in t if x != "null"][0] if [x for x in t if x != "null"] else "null"
    if "enum" in schema:
        return schema["enum"][0]
    if t == "object":
        return {k: _value(v) for k, v in (schema.get("properties") or {}).items()}
    if t == "array":
        return []
    if t == "boolean":
        return True
    if t in ("integer", "number"):
        return 0
    if t == "string":
        return ""
    return None


class DryProvider:
    name = "dry"
    ready = True
    status = "dry-run scripted provider"

    def __init__(self):
        self.calls = 0

    def complete(self, request):
        from app.ai.provider import AiResponse, Usage
        self.calls += 1
        return AiResponse(data=_value(request.schema or {"type": "object"}), usage=Usage(input_tokens=10, output_tokens=5), model="dry", latency_ms=1)


def install():
    """Replace the application's provider with the dry provider, behind the configured (dry) ledger as in a real run."""
    import json

    from app.ai import ledger as ai_ledger
    from app.ai import provider
    from app.core.config import get_settings

    s = get_settings()
    assert s.ai_ledger_path == DRY_LEDGER, s.ai_ledger_path
    provider.set_provider(ai_ledger.LedgerProvider(DryProvider(), ai_ledger.Ledger(
        s.ai_ledger_path, s.ai_ledger_scope, ai_ledger.Limits(**json.loads(s.ai_ledger_limits or "{}")))))
