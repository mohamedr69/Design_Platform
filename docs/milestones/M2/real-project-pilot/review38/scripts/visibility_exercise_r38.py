"""ORCH-08 (task item 8, A-09 point 7): the VISIBILITY dry exercise -- every scenario of the harness's visibility_r38 drill,
run with the refusing stub (no provider, 0 model requests), and the evidence of where each injected event is recorded.

Usage: visibility_exercise_r38.py <work dir (new, absolute)> <result json> <report md>
For each scenario (visibility_r38.SCENARIOS): the dry run(s), then visibility_r38.locate() over the run folder: the run
state (RUN-STATE.json / RUN-REPORT.json), the lane rows (LANE-<lane>.json limit_events), the scorer (lane-<lane>.r32.json
statuses, SCORE-BCR-R32.json limit_incomplete and coverage status_rows: the documents stay in the denominators) and the
audit view (ALLOWANCE-AUDIT.json refusals, charges, stops). A scenario passes when the event is recorded in every place
the scenario can reach (EXPECTED below) -- an empty place is 'silent' and fails the exercise. The AI ledger is read
mode=ro before and after (must be equal); every invocation's model_requests must be 0. Writes only the work dir, the two
output files and the dry run folders under C:/t/r2x/r38-sandbox."""
from __future__ import annotations

import datetime
import json
import pathlib
import sys

H = pathlib.Path("C:/t/iso/work/r2x/r38/harness-r32")
sys.path.insert(0, str(H))
import preflight_r32 as PF  # noqa: E402
import visibility_r38 as V  # noqa: E402

LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
ALL = ("run_state", "lane_rows", "scorer", "audit")
EXPECTED = {name: ALL for name in V.SCENARIOS}
STATUS_WORD = {"lane_allowance": "INCOMPLETE", "project_window": "DEFERRED", "deferral_beyond_bound": "INCOMPLETE",
               "bound_passed_while_deferred": "DEFERRED, then CLOSED INCOMPLETE", "breaker": "INCOMPLETE", "ledger": "INCOMPLETE",
               "provider_timeout": "INCOMPLETE", "interrupted": "INCOMPLETE (served interrupted_charged)", "unsaved": "INCOMPLETE (served interrupted_charged)",
               "identity_mismatch": "INVALID", "application_path": "INCOMPLETE", "application_project_limit": "INCOMPLETE"}


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _load(p):
    p = pathlib.Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def invocations(folder: pathlib.Path) -> list:
    st = _load(folder / "RUN-STATE.json")
    out = []
    for inv in st["invocations"]:
        rep = _load(folder / f"inv-{inv['n']}" / "out" / "RUN-REPORT.json") or {}
        out.append({"n": inv["n"], "kind": inv["kind"], "status": inv["status"], "run_state": inv.get("run_state"),
                    "comparison_state": inv.get("comparison_state"), "candidate_outcome": rep.get("candidate_outcome") or inv.get("outcome"),
                    "earliest_retry_utc": inv.get("earliest_retry_utc"), "model_requests": rep.get("model_requests"),
                    "ledger_unchanged": rep.get("ledger_unchanged"), "lane_gates": rep.get("lane_gates"),
                    "dry_stub_calls": {k: v.get("dry_stub_calls") for k, v in (rep.get("lanes") or {}).items()},
                    "documents": {lane: {pid: d["status"] for pid, d in docs.items()} for lane, docs in (rep.get("documents") or {}).items()},
                    "denominator": ((_load(folder / f"inv-{inv['n']}" / "out" / "SCORE-BCR-R32.json") or {}).get("metrics") or {}).get("C", {})
                    .get("fields", {}).get("decision", {}).get("coverage_resolved")})
    return out


def main(work, result, report):
    work = pathlib.Path(work)
    assert work.is_absolute() and not work.exists(), work
    work.mkdir(parents=True)
    before = PF.ledger_counts(LEDGER)
    started = _now()
    scen = {}
    for name in V.SCENARIOS:
        res = V.run_scenario(name, work / name)
        folder = pathlib.Path(res["run_folder"])
        loc = V.locate(folder, V.KINDS[name])
        invs = invocations(folder)
        places = {p: len(loc[p]) for p in ALL}
        silent = [p for p in EXPECTED[name] if not loc[p]]
        scen[name] = {"what": res["what"], "kinds": V.KINDS[name], "stamp": res["stamp"], "run_folder": res["run_folder"], "steps": res["steps"],
                      "invocations": invs, "recorded_in": places, "silent_places": silent, "status_word": STATUS_WORD[name],
                      "duplicates_in_capture_store": V.capture_duplicates(folder),
                      "model_requests_total": sum(int(i["model_requests"] or 0) for i in invs),
                      "locations": {p: loc[p][:12] for p in ALL}, "locations_truncated_at": 12}
        print(name, places, "silent" if silent else "ok", flush=True)
    after = PF.ledger_counts(LEDGER)
    out = {"kind": "ORCH-08 visibility dry exercise", "started_utc": started, "finished_utc": _now(), "work": work.as_posix(),
           "statement": ("dry runs only: the refusing stub (run_control_r38.DryStub) answers nothing usable, no provider is built, no model request is "
                         "made; the application path reads only SYNTHETIC EP-990001 documents; the real reviewed-2 labels are read only by the adapter "
                         "(reader 'none' runs read no document); FAKE ledgers live inside the dry run folders"),
           "ai_ledger": {"before": before, "after": after, "unchanged": before == after},
           "model_requests": sum(s["model_requests_total"] for s in scen.values()),
           "all_visible": all(not s["silent_places"] for s in scen.values()),
           "no_resend": all(s["duplicates_in_capture_store"] == 0 for s in scen.values()),
           "scenarios": scen}
    pathlib.Path(result).write_text(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    pathlib.Path(report).write_text(render(out), encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("ai_ledger", "model_requests", "all_visible", "no_resend")}))
    return 0 if out["all_visible"] and out["ai_ledger"]["unchanged"] and out["model_requests"] == 0 and out["no_resend"] else 1


def _first(loc, place):
    items = loc.get(place) or []
    if not items:
        return "**none (silent)**"
    x = items[0]
    keys = [k for k in ("kind", "status", "outcome", "pool_id", "page", "pages", "retry_at_utc", "classes", "ledger_entry", "status_rows",
                        "pages_denominator", "comparison_state") if x.get(k) not in (None, [], {})]
    return f"`{x['where']}`" + ("; " + ", ".join(f"{k}={x[k]}" for k in keys) if keys else "") + (f" (+{len(items) - 1} more)" if len(items) > 1 else "")


def render(out) -> str:
    L = ["# VISIBILITY-REPORT (ORCH-08, task item 8; A-09 point 7)", "",
         f"- **Exercise:** `scripts/visibility_exercise_r38.py`, {out['started_utc']} to {out['finished_utc']} (UTC); raw evidence `VISIBILITY-RESULT.json`.",
         f"- **Nature:** {out['statement']}.",
         f"- **AI ledger (mode=ro):** before {out['ai_ledger']['before']['entries']} entries / {out['ai_ledger']['before']['scopes']} scopes, "
         f"after {out['ai_ledger']['after']['entries']} / {out['ai_ledger']['after']['scopes']}; unchanged: {out['ai_ledger']['unchanged']}.",
         f"- **Model requests:** {out['model_requests']} (every invocation of every scenario).",
         f"- **Every injected event visible in every place it can reach:** {out['all_visible']}. **No bound fingerprint re-sent:** {out['no_resend']}.",
         "- **Where:** run state = `RUN-STATE.json` + `inv-<n>/out/RUN-REPORT.json` (documents per lane with status, kinds, pages); lane rows = "
         "`inv-<n>/out/LANE-<lane>.json` `limit_events`; scorer = `lane-<lane>.r32.json` document status / classes / pages and "
         "`SCORE-BCR-R32.json` `limit_incomplete` and coverage `status_rows` (the documents stay in every denominator); audit = "
         "`inv-<n>/out/ALLOWANCE-AUDIT.json` refusals, charges (outcome, ledger entry) and durable stops.",
         "- This report authorizes nothing; M2 is CHANGES STILL REQUIRED; M3 has not started.", "",
         "| Scenario | Injected | Status shown | Run state | Lane rows | Scorer (denominators) | Audit view |",
         "|---|---|---|---|---|---|---|"]
    for name, s in out["scenarios"].items():
        r = s["recorded_in"]
        L.append(f"| `{name}` | {s['what']} | {s['status_word']} | {r['run_state']} | {r['lane_rows']} | {r['scorer']} | {r['audit']} |")
    L += ["", "Counts are the number of records found in each place (0 would be a silent loss; none is 0).", ""]
    for name, s in out["scenarios"].items():
        L += [f"## `{name}`", "", f"- **Injected:** {s['what']}. **Kinds located:** {', '.join(s['kinds'])}.",
              f"- **Run folder:** `{s['run_folder']}`; steps: " + "; ".join(f"{x['command']} -> {x['result']}" + (f" ({x['why'][:90]})" if x.get("why") else "")
                                                                      for x in s["steps"]) + "."]
        for i in s["invocations"]:
            docs = "; ".join(f"{lane}: " + ", ".join(f"{p} {st}" for p, st in d.items()) for lane, d in (i["documents"] or {}).items() if d)
            den = i["denominator"]
            L.append(f"- **Invocation {i['n']} ({i['kind']}, {i['status']}):** run state {i['run_state']}; comparison {i['comparison_state']}; "
                     f"candidate outcome {i['candidate_outcome']}; earliest retry {i['earliest_retry_utc']}; model requests {i['model_requests']}; "
                     f"documents [{docs}]" + (f"; C decision coverage denominator {den['pages']} pages, status rows {den.get('status_rows')}" if den else "") + ".")
        for p in ALL:
            L.append(f"- **{p}:** {_first(s['locations'], p)}")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
