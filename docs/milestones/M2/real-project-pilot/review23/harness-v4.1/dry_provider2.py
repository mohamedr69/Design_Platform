"""PILOT_DRY=1 only (v4): the scripted provider of the harness dry runs, extended for the runner integration tests.
  PILOT_DRY_MODE=schema     (default) minimal schema-shaped answers (as before)
  PILOT_DRY_MODE=coherent   coherent answers that make the reader spend its reads: discovery names an own identity,
                            revision AND a decision block with regions (four required reads per triggered page, so a
                            4-page reading attempts 16: more than the 12-per-document cap), blind reads answer the same
                            literals, the context read too
  PILOT_DRY_KILL_AFTER=n    os._exit(97) right after the n-th DISPATCHED request of this process (after the durable
                            allowance charged it, before the result is persisted): the interrupted-run probe
  PILOT_DRY_LATENCY_S=x     sleep x s per request (deadline probes)
  PILOT_DRY_FAIL_FROM=n     scripted provider FAILURES (error="transport") from the n-th dispatched request on;
  PILOT_DRY_FAIL_COUNT=k    ... k of them (default: every later request) -- the consecutive-failure stop probes
The dry redirections (runs folder, ledger, counter, allowance) live under PILOT_DRY_ROOT (default C:/t/r2x/dry-runs/r22)."""
import os
import time

DRY = os.environ.get("PILOT_DRY") == "1"
MODE = os.environ.get("PILOT_DRY_MODE", "schema")
DRY_ROOT = os.environ.get("PILOT_DRY_ROOT", "C:/t/r2x/dry-runs/r22")   # one isolated root per dry scenario: runs, ledger, counter, allowance
DRY_RUNS = DRY_ROOT + "/runs"
DRY_LEDGER = DRY_ROOT + "/dry-ledger.sqlite"
DRY_XTRACK = DRY_ROOT + "/dry-project-day.sqlite"
DRY_ALLOWANCE = DRY_ROOT + "/dry-allowance.sqlite"


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


COHERENT = {"discover": {"page_kind": "drawing_sheet", "own_identity": "X-DRY-1", "own_identity_label": "DRAWING NO", "own_identity_region": [760, 900, 900, 950],
                         "own_revision": "01", "own_revision_label": "REV", "own_revision_region": [900, 900, 990, 950], "decision_options_printed": ["A = APPROVED", "B = APPROVED AS NOTED"],
                         "decision_marked_option": "B = APPROVED AS NOTED", "decision_mark_type": "tick", "decision_actor": "consultant", "decision_region": [700, 850, 990, 990], "other_numbers": [], "notes": ""},
            "read_identity": {"label_text": "DRAWING NO", "value": "X-DRY-1", "legible": True, "other_values_in_crop": []},
            "read_revision": {"label_text": "REV", "value": "01", "legible": True, "other_values_in_crop": []},
            "read_field_context": {"value": "X-DRY-1", "printed_label": "DRAWING NO", "role": "own_identity", "region": [0, 0, 1000, 1000], "legible": True},
            "read_decision": {"options_printed": ["A = APPROVED", "B = APPROVED AS NOTED"], "marked_option": "B = APPROVED AS NOTED", "mark_type": "tick", "actor": "consultant", "legible": True},
            "read_boq_row": {"part_number": "", "quantity": "", "description": "", "legible": True, "row_is_heading": False}}


class DryProvider:
    name = "dry"
    ready = True
    status = f"dry-run scripted provider ({MODE})"

    def __init__(self):
        self.calls = 0
        self.kill_after = int(os.environ.get("PILOT_DRY_KILL_AFTER") or 0)
        self.latency = float(os.environ.get("PILOT_DRY_LATENCY_S") or 0)
        self.fail_from = int(os.environ.get("PILOT_DRY_FAIL_FROM") or 0)
        self.fail_count = int(os.environ.get("PILOT_DRY_FAIL_COUNT") or 0)

    def complete(self, request):
        from app.ai.provider import AiResponse, Usage
        self.calls += 1
        if self.kill_after and self.calls >= self.kill_after:
            os._exit(97)                 # the request "left"; nothing is persisted after it
        if self.latency:
            time.sleep(self.latency)
        if self.fail_from and self.calls >= self.fail_from and (not self.fail_count or self.calls < self.fail_from + self.fail_count):
            return AiResponse(data=None, usage=Usage(input_tokens=10, output_tokens=0), model="dry", latency_ms=1, error="transport", error_detail="scripted provider failure")
        if MODE == "coherent":
            key = "discover" if request.task.startswith("discover") else request.task
            data = dict(COHERENT.get(key) or _value(request.schema or {"type": "object"}))
            if key == "read_field_context" and "OWN current revision" in " ".join(getattr(p, "text", "") for p in request.parts):
                data = {**data, "value": "01", "printed_label": "REV", "role": "own_revision"}
        else:
            data = _value(request.schema or {"type": "object"})
        return AiResponse(data=data, usage=Usage(input_tokens=10, output_tokens=5), model="dry", latency_ms=1)


def install():
    import json

    from app.ai import ledger as ai_ledger
    from app.ai import provider
    from app.core.config import get_settings

    s = get_settings()
    assert s.ai_ledger_path == DRY_LEDGER, s.ai_ledger_path
    provider.set_provider(ai_ledger.LedgerProvider(DryProvider(), ai_ledger.Ledger(s.ai_ledger_path, s.ai_ledger_scope, ai_ledger.Limits(**json.loads(s.ai_ledger_limits or "{}")))))
