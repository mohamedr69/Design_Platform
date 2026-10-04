"""Recorded harness v4.3 edits (review 25, R25-01), applied to a copy of review24's frozen v4.2.
  provider_journal.py -- validator revision `provider-outcomes.v1/validator-2`: the allowed kind / outcome combinations are
    defined for ALL five result kinds from the writer (`Journal.result` stores the reader log entry's `outcome`) and the
    reader's log semantics (EvidenceRun.call logs a cache hit with outcome "ok", every budget refusal with an outcome
    starting "budget", and a call that produced no log entry yields kind "none" with no outcome):
        ok        outcome == "ok"                                   (unchanged)
        failure   outcome not None, != "ok", not "budget..."        (unchanged)
        cache_hit outcome == "ok"                                   (new check)
        budget    outcome is a string starting with "budget"        (new check)
        none      outcome is None                                   (new check)
    A contradiction is reported (never repaired or coerced) and makes the journal INDETERMINATE, so the runner's existing
    path applies unchanged: exit 5 before dispatch, zero requests, no terminal stop written, run record / allowance /
    journal untouched, refusal recorded with its reason. The journal format (`provider-outcomes.v1`) and its writer are
    unchanged; every journal the v4.2 writer produced satisfies these rules (checked on all existing v4.2 journals by
    legacy_journal_recheck.py), so no valid journal is reinterpreted. The streak semantics are unchanged.
  arm_ev.py -- unchanged (byte-identical to v4.2).
  Explicit path adaptations (evidence roots of the successor, so review24's sandboxes are never overwritten):
    runner_probes.py r24-probes -> r25-probes; lifecycle_probes.py r24-lifecycle -> r25-lifecycle;
    provider_boundary_probes.py r24-boundary -> r25-boundary; test_boundary_v4_2.py r24-probes -> r25-probes."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent


def patch(fn, subs):
    p = HERE / fn
    s = p.read_text(encoding="utf-8")
    for o, n in subs:
        assert s.count(o) == 1, (fn, o[:90], s.count(o))
        s = s.replace(o, n)
    p.write_text(s, encoding="utf-8")


patch("provider_journal.py", [
    ('JOURNAL_VERSION = "provider-outcomes.v1"\nKINDS = ("ok", "failure", "cache_hit", "budget", "none")\n',
     'JOURNAL_VERSION = "provider-outcomes.v1"\nVALIDATOR_REVISION = "provider-outcomes.v1/validator-2"     # review 25: kind / outcome agreement for all five kinds\n'
     'KINDS = ("ok", "failure", "cache_hit", "budget", "none")\n\n\n'
     'def outcome_agrees(kind: str, outcome) -> bool:\n'
     '    """The allowed kind / outcome combinations, from the writer (Journal.result stores the log entry\'s outcome) and the\n'
     '    reader\'s log: a cache hit is logged with outcome "ok"; a budget refusal with an outcome starting "budget"; a call\n'
     '    that produced no log entry has no outcome. A transport (or any other) failure is never a budget refusal, a cache\n'
     '    hit or a no-result event."""\n'
     '    if kind == "ok":\n'
     '        return outcome == "ok"\n'
     '    if kind == "failure":\n'
     '        return outcome not in (None, "ok") and not str(outcome).startswith("budget")\n'
     '    if kind == "cache_hit":\n'
     '        return outcome == "ok"\n'
     '    if kind == "budget":\n'
     '        return isinstance(outcome, str) and outcome.startswith("budget")\n'
     '    if kind == "none":\n'
     '        return outcome is None\n'
     '    return False\n'),
    ('            if r["kind"] == "ok" and r.get("outcome") != "ok" or r["kind"] == "failure" and (r.get("outcome") in (None, "ok") or str(r.get("outcome")).startswith("budget")):\n'
     '                return bad(f"record {i}: kind and outcome disagree")\n',
     '            if not outcome_agrees(r["kind"], r.get("outcome")):\n'
     '                return bad(f"record {i}: kind and outcome disagree (kind {r[\'kind\']!r}, outcome {r.get(\'outcome\')!r})")\n'),
])
patch("runner_probes.py", [('"C:/t/r2x/dry-runs/r24-probes"', '"C:/t/r2x/dry-runs/r25-probes"')])
patch("lifecycle_probes.py", [('"C:/t/r2x/dry-runs/r24-lifecycle"', '"C:/t/r2x/dry-runs/r25-lifecycle"')])
patch("provider_boundary_probes.py", [('"C:/t/r2x/dry-runs/r24-boundary"', '"C:/t/r2x/dry-runs/r25-boundary"')])
patch("test_boundary_v4_2.py", [('"C:/t/r2x/dry-runs/r24-probes"', '"C:/t/r2x/dry-runs/r25-probes"')])
print("patched kind/outcome validation")
