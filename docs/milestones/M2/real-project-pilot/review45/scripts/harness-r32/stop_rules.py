"""Review 31 (R31-04): the executable stop contract for lanes B, C, R and P (tested in test_stop_rules.py).

Events per lane: ok | provider_failure | budget_refusal | critical(resolved: bool, detail).
  B, critical on RESOLVED truth   -> B terminal; comparison INVALID (the baseline is incomplete); C must not start / stops
  C, critical on RESOLVED truth   -> C terminal; comparison RESULT = candidate failed the safety gate (valid, not resumed)
  R (offline replay or reference-only live), critical on resolved truth -> recorded as a REFERENCE finding; no live arm is
                                     stopped and no live arm is reported as having safely stopped; the R contrast stays diagnostic
  any lane, critical on UNRESOLVED truth -> reported, never a stop (the four-arm rule)
  three consecutive completed provider failures in a lane -> that lane terminal; B -> comparison INVALID; C -> comparison
                                     INCOMPLETE; R / P -> only that lane stops; the comparison is unaffected (the R contrast is incomplete)
  budget refusal / breaker        -> budget stop of that lane, never raised; B or C budget stop -> comparison INCOMPLETE
  P (variation probe)             -> never affects B, C or the comparison; its own failures stop only P
Failures are counted per lane: a reference-only or probe failure never counts toward B's or C's streak."""
from __future__ import annotations

LANES = ("B", "C", "R", "P")


class StopController:
    def __init__(self):
        self.lanes = {l: {"state": "running", "streak": 0, "reason": None} for l in LANES}
        self.comparison = "PENDING"
        self.findings = []
        self.log = []

    def can_dispatch(self, lane: str) -> bool:
        if lane == "C" and self.comparison.startswith("INVALID"):
            return False
        return self.lanes[lane]["state"] == "running"

    def _terminal(self, lane, reason):
        st = self.lanes[lane]
        if st["state"] == "running":
            st["state"], st["reason"] = "terminal", reason

    def observe(self, lane: str, kind: str, *, resolved: bool | None = None, detail=None) -> dict:
        assert lane in LANES and kind in ("ok", "provider_failure", "budget_refusal", "critical")
        st = self.lanes[lane]
        self.log.append({"lane": lane, "kind": kind, "resolved": resolved, "detail": detail})
        if kind == "ok":
            st["streak"] = 0
        elif kind == "provider_failure":
            st["streak"] += 1
            if st["streak"] >= 3:
                self._terminal(lane, "three consecutive provider failures")
                if lane == "B":
                    self.comparison = "INVALID: baseline terminal (provider failures)"
                elif lane == "C" and not self.comparison.startswith(("INVALID", "RESULT")):
                    self.comparison = "INCOMPLETE: candidate terminal (provider failures)"
        elif kind == "budget_refusal":
            if st["state"] == "running":
                st["state"], st["reason"] = "budget_stopped", "budget refusal / breaker (never raised)"
            if lane in ("B", "C") and self.comparison == "PENDING":
                self.comparison = f"INCOMPLETE: {lane} budget-stopped"
        elif kind == "critical":
            if not resolved:
                self.findings.append({"lane": lane, "critical": "unresolved truth", "detail": detail, "stop": False})
            elif lane == "B":
                self._terminal("B", "critical acceptance on resolved truth")
                self.comparison = "INVALID: baseline incomplete (critical acceptance on resolved truth in B)"
            elif lane == "C":
                self._terminal("C", "critical acceptance on resolved truth")
                if not self.comparison.startswith("INVALID"):
                    self.comparison = "RESULT: candidate failed the safety gate (critical acceptance on resolved truth in C)"
            else:
                self.findings.append({"lane": lane, "critical": "resolved truth", "detail": detail, "stop": False,
                                      "note": "reference / probe finding: offline or reference-only; no live arm stopped"})
        return self.state()

    def state(self) -> dict:
        return {"lanes": {k: dict(v) for k, v in self.lanes.items()}, "comparison": self.comparison, "findings": list(self.findings)}
