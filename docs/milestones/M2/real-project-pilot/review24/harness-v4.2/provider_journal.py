"""Provider-outcome journal of one document-arm run (review 24, R24-01) -- `provider-outcomes.v1`.

One file per sandbox, out/PROVIDER-OUTCOMES.jsonl, append-only, one JSON object per line, each line written in full,
flushed and fsync'd before the runner goes on. Write order (the recovery depends on it):
  1. `header`   once, when the run is created, before any request can leave: the run binding (declaration hash, arm,
                tag, A tag, allowance scope / profile, policy) and its digest `b`;
  2. `attempt`  before a call that may dispatch is handed to the reader (seq, pid, document sha256, task, page);
  3. `result`   right after that call returns and BEFORE the runner's failure-streak decision (kind: ok / failure /
                cache_hit / budget / none, the provider outcome).
Hence: a provider-failure stop can only have been decided when its three failures are already durable here, and an
`attempt` without its `result` is an UNRESOLVED request (in flight when the process ended) -- neither a failure nor a
success.

Streak semantics (the lifecycle contract): over the run's resolved results in journal order, across processes, a
`failure` adds one, an `ok` resets to zero, `cache_hit` / `budget` / `none` and unresolved attempts change nothing. A
process restart neither resets nor extends the streak (plain --resume is not a breaker reset). Three consecutive
completed failures are terminal.

Validation fails closed: any unparsable or torn line, a header that is missing / not first / bound to another run, a
record with another binding digest, a result without its open attempt, a second open attempt in one process, a process
whose records are not contiguous, a non-increasing seq, an unknown kind or a document outside the declared sources makes
the journal INDETERMINATE -- the runner then refuses to dispatch and fabricates no failure history."""
from __future__ import annotations

import hashlib
import json
import os
import pathlib

JOURNAL_VERSION = "provider-outcomes.v1"
KINDS = ("ok", "failure", "cache_hit", "budget", "none")


def binding_digest(binding: dict) -> str:
    return hashlib.sha256(json.dumps(binding, sort_keys=True).encode()).hexdigest()[:24]


def classify(entry: dict | None) -> str:
    """One EvidenceRun log entry -> journal kind (the same classes the runner's streak loop uses)."""
    if not entry:
        return "none"
    if entry.get("cache_hit"):
        return "cache_hit"
    outcome = str(entry.get("outcome", ""))
    if outcome.startswith("budget"):
        return "budget"
    return "ok" if outcome == "ok" else "failure"


class Journal:
    def __init__(self, path: pathlib.Path, binding: dict) -> None:
        self.path = pathlib.Path(path)
        self.binding = binding
        self.b = binding_digest(binding)
        self.seq = 0

    def _append(self, rec: dict) -> None:
        line = json.dumps(rec, default=str, sort_keys=True) + "\n"
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())

    def create(self, *, lifecycle: str, pid: int) -> None:
        assert not self.path.exists(), "a provider-outcome journal already exists for this sandbox"
        self._append({"type": "header", "journal": JOURNAL_VERSION, "lifecycle": lifecycle, "binding": self.binding, "b": self.b, "pid": pid})

    def continue_from(self, info: dict) -> None:
        self.seq = info["last_seq"]

    def attempt(self, *, pid: int, sha256, task, page, tier) -> int:
        self.seq += 1
        self._append({"type": "attempt", "seq": self.seq, "pid": pid, "b": self.b, "sha256": sha256, "task": task, "page": page, "tier": tier})
        return self.seq

    def result(self, seq: int, *, pid: int, entry: dict | None) -> str:
        kind = classify(entry)
        e = entry or {}
        self._append({"type": "result", "seq": seq, "pid": pid, "b": self.b, "kind": kind, "outcome": e.get("outcome"), "error_detail": e.get("error_detail"),
                      "model": e.get("model"), "task": e.get("task"), "page": e.get("page")})
        return kind


def load(path: pathlib.Path, binding: dict, *, planned_sha256: set) -> dict:
    """Validate the journal and compute the durable streak. Returns {"state": "ok" | "absent" | "indeterminate", ...}."""
    path = pathlib.Path(path)
    if not path.exists():
        return {"state": "absent"}
    raw = path.read_bytes()
    bad = lambda why, **kw: {"state": "indeterminate", "why": why, **kw}
    if raw and not raw.endswith(b"\n"):
        return bad("torn trailing record (the last line is incomplete)")
    try:
        recs = [json.loads(l) for l in raw.decode("utf-8").splitlines()]
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return bad(f"unparsable record: {type(exc).__name__}")
    if not recs or recs[0].get("type") != "header":
        return bad("the header is missing or not first")
    h = recs[0]
    if h.get("journal") != JOURNAL_VERSION or h.get("binding") != binding or h.get("b") != binding_digest(binding):
        return bad("the journal is bound to another run", header_binding=h.get("binding"))
    open_by_pid: dict = {}
    closed_pids: set = set()
    current_pid = None
    last_seq = 0
    streak, failures, unresolved, results = 0, [], [], []
    for i, r in enumerate(recs[1:], 2):
        t, pid = r.get("type"), r.get("pid")
        if r.get("b") != h["b"]:
            return bad(f"record {i} carries another binding digest")
        if pid != current_pid:
            if pid in closed_pids:
                return bad(f"record {i}: records of pid {pid} are not contiguous (two writers?)")
            if current_pid is not None:
                closed_pids.add(current_pid)
                if current_pid in open_by_pid:            # the previous process ended with a request in flight
                    unresolved.append(open_by_pid.pop(current_pid))
            current_pid = pid
        if t == "attempt":
            if pid in open_by_pid:
                return bad(f"record {i}: a second open attempt in pid {pid}")
            if not isinstance(r.get("seq"), int) or r["seq"] <= last_seq:
                return bad(f"record {i}: seq not increasing")
            if r.get("sha256") not in planned_sha256:
                return bad(f"record {i}: a document outside the declared sources")
            last_seq = r["seq"]
            open_by_pid[pid] = r
        elif t == "result":
            a = open_by_pid.get(pid)
            if a is None or a["seq"] != r.get("seq"):
                return bad(f"record {i}: a result without its open attempt")
            if r.get("kind") not in KINDS:
                return bad(f"record {i}: unknown kind {r.get('kind')!r}")
            if r["kind"] == "ok" and r.get("outcome") != "ok" or r["kind"] == "failure" and (r.get("outcome") in (None, "ok") or str(r.get("outcome")).startswith("budget")):
                return bad(f"record {i}: kind and outcome disagree")
            del open_by_pid[pid]
            results.append({**r, "sha256": a["sha256"]})
            if r["kind"] == "ok":
                streak, failures = 0, []
            elif r["kind"] == "failure":
                streak += 1
                failures.append({"seq": r["seq"], "pid": pid, "sha256": a["sha256"], "task": r.get("task") or a.get("task"), "page": r.get("page") or a.get("page"),
                                 "outcome": r.get("outcome"), "error_detail": r.get("error_detail"), "model": r.get("model")})
        else:
            return bad(f"record {i}: unknown record type {t!r}")
    if current_pid in open_by_pid:
        unresolved.append(open_by_pid.pop(current_pid))
    counts = {k: sum(1 for r in results if r["kind"] == k) for k in KINDS}
    return {"state": "ok", "streak": streak, "trailing_failures": failures, "unresolved": [{k: u.get(k) for k in ("seq", "pid", "sha256", "task", "page")} for u in unresolved],
            "last_seq": last_seq, "records": len(recs), "result_counts": counts, "processes": len(closed_pids | ({current_pid} if current_pid is not None else set()))}
