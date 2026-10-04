"""Offline demonstration of how the implemented ledger enforces the proposal's aggregate maximum (no model request): the
ACTUAL ledger class of the frozen candidate (app.ai.ledger) on a throw-away ledger file under C:/t/iso/tmp, never the live
ledger. Cases:
  E1 a scope refuses the (cap + 1)-th request: requests counted at RESERVE (before dispatch)
  E2 an interrupted request (reserved, never settled) stays counted: a crash cannot free cap
  E3 cache hits and refusals are not counted as requests
  E4 the scope's limits are persisted on first use: a different supplied limit raises LedgerConfigMismatch (no silent increase)
  E5 the elapsed limit is measured from the scope's creation: after it passes, every reservation is refused -- why the
     proposal raises the document-arm scopes' elapsed limit from 4 h to 96 h (the deferral schedule spans rolling days)
  E6 a provider failure is still a counted request (the CLI adapter does not retry; each attempt is one reservation)
Writes enforcement/ENFORCEMENT.json."""
import json
import os
import pathlib
import sys
import tempfile
import time

R = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, "C:/t/iso/cand-ai4/backend")
os.environ.setdefault("AI_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "sqlite:///C:/t/iso/tmp/enf-no-db.db")
from app.ai import ledger as L  # noqa: E402

tmp = pathlib.Path(tempfile.mkdtemp(prefix="r26-enforcement-", dir="C:/t/iso/tmp"))
path = str(tmp / "throwaway-ledger.sqlite")
assert "r2x-ledger" not in path
out = {"ledger_module": L.__file__, "throwaway_ledger": path, "cases": {}}

led = L.Ledger(path, "E1", L.Limits(requests=3))
ids = [led.reserve("t", 100, 10) for _ in range(3)]
try:
    led.reserve("t", 100, 10)
    refused = None
except L.LedgerRefused as exc:
    refused = exc.limit
out["cases"]["E1_cap_enforced_at_reserve"] = {"cap": 3, "reserved": len(ids), "fourth": refused, "ok": refused == "requests"}

led2 = L.Ledger(path, "E2", L.Limits(requests=2))
a = led2.reserve("t", 100, 10)                    # interrupted: never settled
b = led2.reserve("t", 100, 10)
led2.settle(b, input_tokens=90, output_tokens=5)
try:
    led2.reserve("t", 100, 10)
    r2 = None
except L.LedgerRefused as exc:
    r2 = exc.limit
out["cases"]["E2_interrupted_request_stays_counted"] = {"totals": led2.totals(), "third": r2, "ok": r2 == "requests" and led2.totals()["in_flight"] == 1}

led3 = L.Ledger(path, "E3", L.Limits(requests=1))
led3.note_cache_hit("t")
led3.note_cache_hit("t")
c = led3.reserve("t", 100, 10)
out["cases"]["E3_cache_hits_not_counted"] = {"totals": led3.totals(), "ok": led3.totals()["requests"] == 1 and led3.totals()["cache_hits"] == 2}

try:
    L.Ledger(path, "E1", L.Limits(requests=999))
    mism = None
except L.LedgerConfigMismatch as exc:
    mism = str(exc)[:200]
out["cases"]["E4_limits_persisted_no_silent_increase"] = {"attempt": "reopen scope E1 with requests=999", "raised": mism, "ok": mism is not None}

led5 = L.Ledger(path, "E5", L.Limits(requests=10, elapsed_s=1))
led5.reserve("t", 100, 10)
time.sleep(1.5)
try:
    led5.reserve("t", 100, 10)
    r5 = None
except L.LedgerRefused as exc:
    r5 = exc.limit
out["cases"]["E5_elapsed_from_scope_creation"] = {"elapsed_limit_s": 1, "second_reservation_after_s": 1.5, "refused": r5, "ok": r5 == "elapsed_s",
                                                  "consequence": "with the R21/R22 limit of 14,400 s, an arm whose project is deferred to the next rolling day is refused when it resumes; the revised proposal sets 345,600 s (96 h) for the document-arm scopes"}

led6 = L.Ledger(path, "E6", L.Limits(requests=2))
e = led6.reserve("t", 100, 10)
led6.settle(e, input_tokens=None, output_tokens=None, outcome="transport")
out["cases"]["E6_failed_request_counted"] = {"totals": led6.totals(), "ok": led6.totals()["requests"] == 1 and led6.totals()["usage_unknown"] == 1}
out["all_ok"] = all(v["ok"] for v in out["cases"].values())
(R / "enforcement").mkdir(exist_ok=True)
(R / "enforcement/ENFORCEMENT.json").write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
for k, v in out["cases"].items():
    print(k, v["ok"])
print("all ok", out["all_ok"])
