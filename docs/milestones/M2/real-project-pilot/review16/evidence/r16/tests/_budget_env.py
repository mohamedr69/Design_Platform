"""Shared offline environment for the R15-01 tests: the frozen application's OWN JobBudget / Limits / BudgetExceeded
classes (compiled from app/ai/budget.py without application startup, as the Review 15 probe does), a scripted
evidence reader standing at the provider boundary (it reserves, then 'sends' by writing an fsync'd log line), and a
runner for either harness version. Child-process modes: 'crash' (os._exit after N sends, inside the first chunk),
'hold' (take the key's writer lock and sleep)."""
import ast
import importlib.util
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

SUBMITTED = Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review14/evidence/r14")
CORRECTED = Path(__file__).resolve().parents[1]
_budget = Path("C:/t/iso/frozen-r12/backend/app/ai/budget.py")
_tree = ast.parse(_budget.read_text(encoding="utf-8-sig"))
_ns = {"dataclass": dataclass, "field": field, "threading": threading, "time": time, "__name__": "frozen_budget"}
exec(compile(ast.Module(body=[n for n in _tree.body if isinstance(n, ast.ClassDef) and n.name in ("Limits", "JobBudget", "BudgetExceeded")],
                        type_ignores=[]), str(_budget), "exec"), _ns)
Limits, JobBudget, BudgetExceeded = _ns["Limits"], _ns["JobBudget"], _ns["BudgetExceeded"]


_loaded = {}


def load(code_dir: Path, name: str):
    """One module object per (folder, module), so exception classes compare by identity."""
    key = (str(code_dir), name)
    if key not in _loaded:
        spec = importlib.util.spec_from_file_location(f"h_{code_dir.name}_{name}", code_dir / f"{name}.py")
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        _loaded[key] = m
    return _loaded[key]


def open_budget(db, project):
    # the frozen defaults that matter here: 12 calls / document, 120 s, 2 escalations (others generous)
    return JobBudget(Limits(100000, 100000, 12, 1000, 0, 120, 2, 0, 0, 0), 0)


class DB:
    def commit(self):
        pass


class ScriptedER:
    def __init__(self, log: Path, crash_after=None, fail_after_dispatch_at=None, escalate=False):
        self.log, self.crash_after, self.fail_at, self.escalate = Path(log), crash_after, fail_after_dispatch_at, escalate
        self.sent = 0

    def boq_rows_to_verify(self, lines, issues, **kw):
        return [(l, None) for l in lines]

    def verify_boq_rows(self, run, pdf, *, extraction, **kw):
        out = []
        for _row in extraction["lines"]:
            if run.exhausted:
                out.append({"state": "budget_refused", "limit": run.exhausted})
                continue
            try:
                run.budget.reserve(1, 1, escalation=self.escalate)
            except BudgetExceeded as exc:
                run.exhausted = exc.limit
                out.append({"state": "budget_refused", "limit": exc.limit})
                continue
            self.sent += 1                                   # the request leaves the process here
            with self.log.open("a", encoding="utf-8") as f:
                f.write("scripted_provider_request\n")
                f.flush()
                os.fsync(f.fileno())
            if self.crash_after and self.sent == self.crash_after:
                os._exit(91)                                 # inside the first chunk, before the harness can save
            if self.fail_at and self.sent == self.fail_at:
                out.append({"state": "failed_after_dispatch"})   # a transport failure: the request was made
                continue
            out.append({"state": "read"})
        return out


def run_sheet(code_dir: Path, folder: Path, *, rows=25, profile="EV2", crash_after=None, fail_at=None, escalate=False):
    bh = load(code_dir, "boq_harness")
    er = ScriptedER(folder / "provider-log.txt", crash_after, fail_at, escalate)
    run = SimpleNamespace(exhausted=None, budget=None)
    res, info = bh.verify_sheet(er, run, None, db=DB(), open_budget=open_budget, allowance=bh.DocAllowance(str(folder / "allowance.sqlite")),
                                scope="frozen-scope", profile=profile, lines=[{"id": i} for i in range(rows)], issues=[], variant="EV2",
                                sha256="same-document-sha", max_calls_per_document=12, render_dpi=150)
    return {"sent": er.sent, "results": res, **info}


def provider_log_count(folder: Path) -> int:
    p = folder / "provider-log.txt"
    return len(p.read_text().splitlines()) if p.exists() else 0


if __name__ == "__main__":        # child modes
    mode, code, folder = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if mode == "crash":
        run_sheet(code, folder, crash_after=int(sys.argv[4]))
        raise SystemExit("child did not stop")
    if mode == "hold":
        bh = load(code, "boq_harness")
        lock = bh.DocAllowance(str(folder / "allowance.sqlite")).acquire("frozen-scope", "EV2", "same-document-sha")
        (folder / "holding").write_text("1")
        time.sleep(float(sys.argv[4]))
        raise SystemExit(0)
