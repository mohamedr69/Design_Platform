"""The reviewer's Review 08 probes (M2-review-08/probes.py), re-run on the prior reader/ledger (pinned 1455f8b copies)
and on the Review 08 candidate. Same scenarios and inputs; adapted only where the candidate's API changed:
the stub Run keeps a call log (the real EvidenceRun does), and evidence is requested for a context (evidence_for).
No model or app service calls; the ledger writes only disposable sqlite files."""
import copy
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

ISO = Path("C:/t/iso/ep-platform/backend")
sys.path.insert(0, str(ISO))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


MODULES = {"prior_1455f8b": (load("er_prior", ISO / "tests/fixtures/evidence_reader_r7.py"), load("ledger_prior", ISO / "tests/fixtures/ledger_r7.py")),
           "candidate_r8": (load("er_r8", ISO / "app/ai/evidence_reader.py"), load("ledger_r8", ISO / "app/ai/ledger.py"))}


def attempt(n, obs, outcome="complete", pages=None, policy="p1"):
    return dict(attempt=n, version="r1", policy=policy, observations=obs, outcome=outcome,
                coverage={"pages": pages if pages is not None else [{"page": 1, "outcome": "evidence"}]})


def view(g, ai, profile="default"):
    if hasattr(g, "evidence_for"):
        got = g.evidence_for(ai, sha256="same", profile=profile, variant="EV1")
        return {"state": got["state"], "profile": (got.get("envelope") or {}).get("profile"),
                "observations": [{k: o.get(k) for k in ("field", "value", "state")} for o in got.get("observations") or []]}
    got = g.current_evidence(ai)
    return {"state": "current (the only accessor; the request is ignored)", "profile": got.get("profile"),
            "observations": [{k: o.get(k) for k in ("field", "value", "state")} for o in got.get("observations") or []]}


class Run:
    variant, profile, escalations, exhausted = "EV1", "default", 0, None

    def __init__(self):
        self.log = []

    def call(self, **kw):
        if kw["task"] == "discover_page":
            self.log.append({"outcome": "ok"})
            return {"own_identity": "X-SD-1", "own_identity_region": [1, 1, 100, 100], "page_kind": "drawing_sheet"}
        self.log.append({"outcome": "timeout"})
        return None   # call() returns None on timeout/error; the budget is not exhausted


results = {}
for label, (g, ledger) in MODULES.items():
    r = results[label] = {"reader": g.READER_VERSION, "ledger": ledger.LEDGER_VERSION}
    old = [dict(page=1, field="identity", value="X-SD-1", state="validated"), dict(page=1, field="decision", value="approved", state="validated")]
    base = g.merge_evidence(None, attempt(1, old), sha256="same", profile="default", variant="EV1")
    fail = g.merge_evidence(copy.deepcopy(base), attempt(2, [], "failed", []), sha256="same", profile="promoted", variant="EV1")
    r["failed_profile_switch"] = {"requested_profile": "promoted", "returned": view(g, fail, "promoted")}

    saved = {k: getattr(g, k) for k in ("page_png", "crop_png", "_det_region", "region_from_norm", "region_texts")}
    g.page_png, g.crop_png = (lambda p: b""), (lambda *a, **k: b"")
    g._det_region, g.region_from_norm, g.region_texts = (lambda *a: None), (lambda *a: (0, 0, 10, 10)), (lambda *a: [("text", "X-SD-1")])
    try:
        found = g._read_page(Run(), None, sha256="same", number=1, facts=SimpleNamespace(identities=[], revisions=[], records=[]), reason="probe")
    finally:
        for k, v in saved.items():
            setattr(g, k, v)
    cov = {"page": 1, "outcome": found["_outcome"], **({"fields": found["_fields"]} if "_fields" in found else {})}
    merged = g.merge_evidence(copy.deepcopy(base), attempt(2, found["_observations"], pages=[cov]), sha256="same", profile="default", variant="EV1")
    r["blind_timeout_replaces_good_page"] = {"page_outcome": found["_outcome"], "field_outcomes": found.get("_fields"),
                                             "new_observations": [{k: o.get(k) for k in ("field", "value", "state", "reasons")} for o in found["_observations"]],
                                             "after_merge": view(g, merged)}
    budget_page = g.merge_evidence(copy.deepcopy(base), attempt(3, [dict(page=1, field="identity", value="X-SD-NEW", state="candidate")], outcome="budget",
                                                                pages=[{"page": 1, "outcome": "evidence"}, {"page": 2, "outcome": "budget: requests"}]),
                                   sha256="same", profile="default", variant="EV1")
    r["budget_envelope_does_not_guard_page_overwrite"] = view(g, budget_page)
    r["heading_validated_without_verified_fields"] = g.validate_boq_row({"part_number": "P-1", "quantity": None}, {"row_is_heading": True, "legible": True})

    with tempfile.TemporaryDirectory(prefix="m2-review08-ledger-", ignore_cleanup_errors=True) as td:
        p = str(Path(td) / "ledger.db")
        first = ledger.Ledger(p, "fixed-scope", ledger.Limits(requests=1))
        first.settle(first.reserve("test", 1, 1), input_tokens=1, output_tokens=1)
        out = {}
        try:
            second = ledger.Ledger(p, "fixed-scope", ledger.Limits(requests=2))
            out["reopen_with_requests_2"] = "opened"
            try:
                second.reserve("test", 1, 1)
                out["second_request_dispatched_if_wrapped"] = True
            except ledger.LedgerRefused as e:
                out["second_request_dispatched_if_wrapped"] = False
                out["refused"] = str(e)
        except Exception as e:  # noqa: BLE001 -- the candidate refuses the handle
            out["reopen_with_requests_2"] = f"{type(e).__name__}: {e}"
            out["second_request_dispatched_if_wrapped"] = False
        reopened = ledger.Ledger(p, "fixed-scope")
        out["handle_without_limits_uses"] = reopened.limits.as_dict()
        try:
            reopened.reserve("test", 1, 1)
            out["reserve_on_stored_policy"] = "reserved"
        except ledger.LedgerRefused as e:
            out["reserve_on_stored_policy"] = f"refused ({e.limit})"
        out["totals"] = {k: v for k, v in reopened.totals().items() if k in ("requests", "in_flight", "refused")}
        r["scope_reopened_with_looser_limit"] = out

text = json.dumps(results, indent=2, default=str)
Path(sys.argv[1] if len(sys.argv) > 1 else "probe-results-r8.json").write_text(text + "\n", encoding="utf-8", newline="\n")
print(text)
