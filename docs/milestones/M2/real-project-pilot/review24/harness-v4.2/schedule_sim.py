"""Rolling-day schedule simulation of the runner's WHOLE-PROJECT batch contract with a fake clock (offline; no request):
an arm enters a project only when the project's rolling 24 h capacity (60 minus the requests of the last 24 h across
all tracks, including the A base) covers the arm's WORST case for that project (12 per pending PDF document); otherwise
the project is deferred for that arm and the arm moves on; deferred work resumes in declared order on later windows.
Simulated with per-document request DEMAND (expected or worst) consumed at the batch's start time. Reports the windows,
elapsed time and, per arm and project, when each batch runs. Pure functions for the tests and the workload table."""
from __future__ import annotations

import collections

DAY = 86400.0


def simulate(projects: dict, arms: list[str], demand: dict, *, limit=60, cap=12, a_usage=None, start=0.0, step=3600.0, max_days=30) -> dict:
    """projects: {ep: [doc ids]}; demand[(arm, doc)] = requests the batch will actually send (<= cap); a_usage: {ep: n}
    requests already spent by the A base at `start`. Arms in declared order; within an arm, projects in EP order."""
    log = collections.defaultdict(list)          # ep -> [(time, n)] requests charged to the rolling window
    for ep, n in (a_usage or {}).items():
        if n:
            log[ep].append((start, n))
    used = lambda ep, t: sum(n for at, n in log[ep] if at > t - DAY)
    pending = {arm: list(sorted(projects)) for arm in arms}
    events, t = [], start
    while any(pending.values()) and t - start <= max_days * DAY:
        progressed = False
        for arm in arms:
            for ep in list(pending[arm]):
                docs = projects[ep]
                worst = cap * len(docs)
                if limit - used(ep, t) >= worst:
                    sent = sum(demand.get((arm, d), 0) for d in docs)
                    log[ep].append((t, sent))
                    pending[arm].remove(ep)
                    events.append({"t_h": round((t - start) / 3600, 1), "arm": arm, "ep": ep, "worst_case_reserved": worst, "sent": sent, "capacity_before": limit - used(ep, t)})
                    progressed = True
                else:
                    events.append({"t_h": round((t - start) / 3600, 1), "arm": arm, "ep": ep, "deferred": True, "needed": worst, "capacity": limit - used(ep, t)})
        if not any(pending.values()):
            break
        t += step
        if not progressed:
            # jump to the next time any rolling-window entry expires (nothing changes before that)
            expiries = [at + DAY for eps in log.values() for at, n in eps if at + DAY > t]
            t = max(t, min(expiries)) if expiries else t
    done = not any(pending.values())
    ran = [e for e in events if not e.get("deferred")]
    return {"complete": done, "elapsed_h": round((max(e["t_h"] for e in ran) if ran else 0), 1), "elapsed_days_ceil": int(-(-max((e["t_h"] for e in ran), default=0) // 24)),
            "batches": ran, "deferrals": sum(1 for e in events if e.get("deferred")), "sent_total": sum(e["sent"] for e in ran),
            "unfinished": {a: p for a, p in pending.items() if p}}
