"""ORCH-08C (R39-08; task item 3): how many invocations a project needs under each resume policy -- the runbook input for
the declaration task. A deterministic simulation of the harness's own rules, no request and no model:
  * one project, its requests in lane order B -> C -> R -> P (a later lane starts only when the earlier one deferred
    nothing); every invocation re-runs every lane: answered requests are served (no charge), the rest are dispatched in
    order until the project's rolling window (limit L per W seconds, all lanes) refuses one -- the invocation then ends
    DEFERRED (allowance_r32: a refusal is never a charge);
  * the resume times: 'earliest' = when the oldest charge in the window leaves it (one slot); 'full' = the harness's
    default policy, runner_r32.resume_times: the structural-basis retry_at_full (the project's remaining structural
    maximum fits the window, or -- when it exceeds one window -- the window is empty: allowance_r32.full_retry_time);
  * timing: the first invocation dispatches one request every d seconds (default 20 s: the claude-code CLI's typical
    latency per crop read); a resume either dispatches at the same pace ('paced': old charges leave the window as fast as
    new ones arrive) or in a burst 0.01 s apart ('burst': its served replays and new requests outrun the ageing of the
    earlier charges -- the worst case for 'earliest', where each resume finds only the slots freed at its start).
The demand is the project's requests that actually occur: its planning estimate or its structural maximum (bounds file).
Usage: resume_invocations_r39.py <PROJECT-REQUEST-BOUNDS.json> <out json> [project]"""
from __future__ import annotations

import json
import pathlib
import sys

import allowance_r32 as AL


def simulate(lanes: dict, structural_total: int, *, limit: int, window_s: int, policy: str, timing: str, d: float = 20.0,
             max_invocations: int = 2000) -> dict:
    queue = [lane for lane in ("B", "C", "R", "P") for _ in range(int(lanes.get(lane, 0)))]
    charges: list[float] = []
    t, invocations, done, starts = 0.0, 0, 0, []
    while done < len(queue) and invocations < max_invocations:
        invocations += 1
        starts.append(t)
        gap = d if (invocations == 1 or timing == "paced") else 0.01
        now = t
        while done < len(queue):
            inside = [a for a in charges if a > now - window_s]
            if len(inside) >= limit:
                break
            charges.append(now)
            done += 1
            now += gap
        if done >= len(queue):
            break
        inside = sorted(a for a in charges if a > now - window_s)
        earliest = inside[0] + window_s
        if policy == "earliest":
            t = max(now, earliest)
        else:
            remaining = max(1, structural_total - len(charges))
            t = max(now, AL.full_retry_time(inside, limit, window_s, remaining, now))
    return {"invocations": invocations, "requests": len(queue), "completed": done >= len(queue),
            "finished_after_s": round(t if done >= len(queue) else float("nan"), 1) if done >= len(queue) else None,
            "resume_starts_s": [round(s, 1) for s in starts[:12]] + (["..."] if len(starts) > 12 else [])}


def main(argv):
    bounds = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    project = argv[3] if len(argv) > 3 else "EP-27331"
    p = bounds["projects"][project]
    lim, win = bounds["project_window"]["limit"], bounds["project_window"]["window_s"]
    plan_round = {lane: int(round(p["planning"][lane])) for lane in ("B", "C", "R", "P")}
    demands = {"planning": plan_round, "structural": {lane: p["structural_maximum"][lane] for lane in ("B", "C", "R", "P")}}
    total_struct = p["structural_maximum"]["all_lanes"]
    out = {"version": "resume-invocations-r39-2026-10-04.1", "project": project, "window": {"limit": lim, "window_s": win},
           "structural_total": total_struct, "planning_total": p["planning"]["all_lanes"], "demands": demands,
           "demand_note": "planning lanes rounded to whole requests (R 4.1 -> 4, P 6.9 -> 7: 63)", "rule": (__doc__ or "").strip(), "results": {}}
    for dname, lanes in demands.items():
        for policy in ("full", "earliest"):
            for timing in ("paced", "burst"):
                out["results"][f"{dname}|{policy}|{timing}"] = simulate(lanes, total_struct, limit=lim, window_s=win, policy=policy, timing=timing)
    out["table"] = {dname: {"full": out["results"][f"{dname}|full|paced"]["invocations"],
                            "full_burst": out["results"][f"{dname}|full|burst"]["invocations"],
                            "earliest_paced": out["results"][f"{dname}|earliest|paced"]["invocations"],
                            "earliest_burst": out["results"][f"{dname}|earliest|burst"]["invocations"]} for dname in demands}
    out["statement"] = ("each invocation after the first is a resume with its own owner authorization (one nonce per invocation); "
                        "a resume before the declared policy's time is refused and creates nothing; numbers are a model, not a measurement")
    pathlib.Path(argv[2]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out["table"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
