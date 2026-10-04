"""Recorded harness v4.1 edit after the first lifecycle probe run: the evidence of a consecutive-provider-failure stop is
the last three FAILED requests across documents (each document is its own EvidenceRun, so `self.log[-3:]` of the run
that saw the third failure held only that run's entries); the runner now keeps the failed entries in its own state
(cleared by a successful request) and persists those three."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
p = HERE / "arm_ev.py"
s = p.read_text(encoding="utf-8")
subs = [
    ('state = {"consecutive_failures": 0, "stopped": None, "terminal_stop": None, "xtrack_refusals": 0,',
     'state = {"consecutive_failures": 0, "recent_failures": [], "stopped": None, "terminal_stop": None, "xtrack_refusals": 0,'),
    ('        if entry.get("outcome") == "ok":\n            state["consecutive_failures"] = 0\n        else:\n            state["consecutive_failures"] += 1\n',
     '        if entry.get("outcome") == "ok":\n            state["consecutive_failures"] = 0\n            state["recent_failures"] = []\n        else:\n            state["consecutive_failures"] += 1\n'
     '            state["recent_failures"].append({"sha256": kw.get("sha256"), **{k: entry.get(k) for k in ("task", "page", "outcome", "error_detail", "model")}})\n'),
    ('                state["terminal_stop"] = persist_terminal_stop("provider_failures", state["stopped"], [{k: e.get(k) for k in ("task", "page", "outcome", "error_detail", "model")} for e in self.log[-3:]])\n',
     '                state["terminal_stop"] = persist_terminal_stop("provider_failures", state["stopped"], state["recent_failures"][-3:])\n'),
]
for o, n in subs:
    assert s.count(o) == 1, (o[:70], s.count(o))
    s = s.replace(o, n)
p.write_text(s, encoding="utf-8")
print("patched lifecycle 2")
