"""The static guard on the project AI policy (ORCH-053; M3 contract B-04): no
path may reach an AI provider without the fail-closed project-policy gate.

Read from the source (no import of the code under test, no provider, no
network). It enumerates every place in `backend/app` and `backend/scripts`
that

- sends to a provider (a `.complete(` call),
- goes through the central call path (`assist.call_task` / `assist._call`), or
- obtains a provider (`get_*provider(` or `_build(`),

and fails when

1. the central path `assist._call` does not open with `project_policy.enforce`;
2. a `.complete(` call is not preceded, in its own function, by a
   `project_policy` gate (`enforce`, `require`, `check`, `refusal_for`) --
   unless it is a provider wrapper's own `complete` (delegation, reached only
   from a gated call) or an exemption listed below with its reason;
3. a provider is obtained at a place not registered in `PROVIDER_SOURCES`
   (a NEW call site: give it a gate, then register it with how it is gated),
   or a registered place no longer exists (keep the register true);
4. a registered gate names a function that has no gate call.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
GATES = {"enforce", "require", "check", "refusal_for"}
PROVIDER_FN = re.compile(r"^(get_\w*provider|_build)$")

# Direct sends that are not project content, with the reason. Each is an operator script or harness,
# never reached from a route, a job or a worker.
EXEMPT_SENDS = {
    "scripts/ai_selftest.py:run": "a synthetic drawn cell and fixed text: no project content (the provider self-test)",
    "app/ai/evaluation.py:run_case": ("the offline evaluation harness (scripts/ai_eval.py run), operator-run on the "
                                      "case file; no route, job or worker reaches it. Open item: cases carry no "
                                      "project, so the harness cannot be gated per project yet"),
}

# Every place a provider is obtained, and how what it sends is gated:
#   central       -- the provider only reaches a model through assist.call_task -> assist._call (gated per call)
#   status        -- read for `ready` / `status` / a name only; nothing is sent from here
#   gate:<site>   -- sent directly from <site>, which carries its own project_policy gate
#   exempt:<why>  -- see EXEMPT_SENDS
PROVIDER_SOURCES = {
    "app/ai/sheet_reader.py:available": "status",
    "app/ai/sheet_reader.py:read_design_sheet": "central",
    "app/ai/submittal_reader.py:available": "status",
    "app/ai/submittal_reader.py:check": "central",
    "app/ai/verification.py:available": "status",
    "app/ai/verification.py:drf_run": "central",
    "app/ai/verification.py:read_drf": "central",
    "app/ai/verification.py:verify_boq": "central",
    "app/ai/verification.py:verify_details": "central",
    "app/compliance/assist.py:available": "status",
    "app/compliance/assist.py:open_session": "central",
    "app/extraction/pipeline.py:ask": "gate:app/extraction/pipeline.py:ask",
    "app/extraction/pipeline.py:assist_project": "gate:app/extraction/pipeline.py:ask",
    "app/ifc/services/ai_symbol_review.py:_call": "gate:app/ifc/services/ai_symbol_review.py:_call",
    "app/ifc/services/ai_symbol_review.py:enabled": "status",
    "app/interfaces/findings.py:_ask": "central",
    "app/interfaces/findings.py:readiness": "status",
    "app/interfaces/visual.py:_ask": "central",
    "app/interfaces/workflow.py:_ask_orchestrator": "central",
    "app/interfaces/workflow.py:readiness": "status",
    "app/redesign/prepare.py:_ask_coordination": "central",
    "app/redesign/prepare.py:_ask_review": "central",
    "app/redesign/service.py:_ask": "central",
    "app/review/scoped.py:run": "status",
    "app/review/service.py:_ask": "central",
    "app/review/service.py:run": "status",
    "app/routers/extraction.py:assist": "gate:app/extraction/pipeline.py:ask",
    "app/routers/extraction.py:get_extraction": "status",
    "app/routers/extraction.py:project_ai_budget": "status",
    "app/services/document_classification_ai.py:_session": "central",
    "app/services/document_classification_ai.py:available": "status",
    "app/services/document_processing.py:run": "central",
    "app/services/drawing_ai_review.py:_ask": "gate:app/services/drawing_ai_review.py:_ask",
    "app/services/drawing_ai_review.py:enabled": "status",
    "app/services/drawings_chat.py:_session": "central",
    "app/services/drawings_chat.py:available": "status",
    "scripts/ai_eval.py:main": "exempt:app/ai/evaluation.py:run_case",
    "scripts/ai_selftest.py:run": "exempt:scripts/ai_selftest.py:run",
    # the scoped CLI's --live provider: built only after preflight's gate, and used by the review through
    # assist.call_task (gated again per call)
    "scripts/scoped_drawing_review.py:main": "gate:app/review/scoped.py:preflight",
}
CENTRAL_MARKERS = ("assist.call_task", "assist.AssistSession", "assist.open_session", "_Run(", "AssistSession(")


def _sources() -> list[Path]:
    out = []
    for base in ("app", "scripts"):
        out += sorted((BACKEND / base).rglob("*.py"))
    return out


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


class _Site:
    def __init__(self, kind: str, where: str, line: int, function: ast.AST | None):
        self.kind, self.where, self.line, self.function = kind, where, line, function


def _gate_lines(function: ast.AST) -> list[int]:
    """Lines of `project_policy.<gate>(...)` calls directly in `function` (not in nested functions)."""
    lines = []

    def visit(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute) and child.func.attr in GATES
                    and isinstance(child.func.value, ast.Name) and child.func.value.id == "project_policy"):
                lines.append(child.lineno)
            visit(child)

    visit(function)
    return lines


def _scan() -> tuple[list[_Site], dict[str, ast.AST]]:
    sites: list[_Site] = []
    functions: dict[str, ast.AST] = {}
    for path in _sources():
        rel = path.relative_to(BACKEND).as_posix()
        tree = ast.parse(_read(path), filename=rel)

        def visit(node, stack, function):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    name = stack + [child.name]
                    fn = child if not isinstance(child, ast.ClassDef) else function
                    if not isinstance(child, ast.ClassDef):
                        functions[f"{rel}:{'.'.join(name)}"] = child
                    visit(child, name, fn)
                    continue
                if isinstance(child, ast.Call):
                    f = child.func
                    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
                    where = f"{rel}:{'.'.join(stack) or '<module>'}"
                    if name == "complete" and isinstance(f, ast.Attribute):
                        sites.append(_Site("send", where, child.lineno, function))
                    elif name and PROVIDER_FN.match(name) and rel != "app/ai/provider.py":
                        sites.append(_Site("source", where, child.lineno, function))
                    elif (name in ("call_task", "_call") and isinstance(f, ast.Attribute)
                          and isinstance(f.value, ast.Name) and f.value.id == "assist"):
                        sites.append(_Site("central", where, child.lineno, function))
                visit(child, stack, function)

        visit(tree, [], None)
    return sites, functions


SITES, FUNCTIONS = _scan()


def test_the_central_call_path_opens_with_the_fail_closed_gate():
    _call = FUNCTIONS["app/compliance/assist.py:_call"]
    body = [s for s in _call.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
    first = body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call), ast.dump(first)
    func = first.value.func
    assert (isinstance(func, ast.Attribute) and func.attr == "enforce" and isinstance(func.value, ast.Name)
            and func.value.id == "project_policy"), "assist._call must open with project_policy.enforce(...)"
    # keyed on the session's project, for the call's task
    args = ast.unparse(first.value)
    assert "session.db" in args and "session.project_id" in args and "task=task" in args, args
    # and call_task is only the public face of _call
    call_task = FUNCTIONS["app/compliance/assist.py:call_task"]
    assert "_call(session" in ast.unparse(call_task)


def test_every_direct_send_is_gated_before_it_sends():
    ungated = []
    for site in (s for s in SITES if s.kind == "send"):
        if site.where == "app/compliance/assist.py:_call" or site.where in EXEMPT_SENDS:
            continue
        if site.where.endswith(".complete"):
            continue                                  # a provider wrapper delegating: reached only from a gated call
        gates = _gate_lines(site.function) if site.function is not None else []
        if not any(line < site.line for line in gates):
            ungated.append(f"{site.where} (line {site.line})")
    assert not ungated, ("provider sends with no project_policy gate before them in the same function: "
                         + ", ".join(ungated))


def test_every_place_a_provider_is_obtained_is_registered_with_its_gate():
    found = sorted({s.where for s in SITES if s.kind == "source"})
    new = [w for w in found if w not in PROVIDER_SOURCES]
    gone = [w for w in PROVIDER_SOURCES if w not in found]
    assert not new, ("a new place obtains an AI provider: gate what it sends (project_policy.enforce, or route it "
                     "through assist.call_task) and register it in PROVIDER_SOURCES: " + ", ".join(new))
    assert not gone, "registered provider sources that no longer exist (update the register): " + ", ".join(gone)


def test_each_registered_gate_is_real():
    for where, how in PROVIDER_SOURCES.items():
        if how.startswith("gate:"):
            target = how[len("gate:"):]
            assert target in FUNCTIONS, f"{where}: gate function {target} not found"
            assert _gate_lines(FUNCTIONS[target]), f"{where}: {target} has no project_policy gate call"
        elif how.startswith("exempt:"):
            assert how[len("exempt:"):] in EXEMPT_SENDS, where
        elif how == "central":
            module = (BACKEND / where.split(":")[0])
            assert any(marker in _read(module) for marker in CENTRAL_MARKERS), \
                f"{where} is registered as central but its module does not use the central call path"
        else:
            assert how == "status", f"{where}: unknown register entry {how!r}"


def test_every_central_call_reaches_the_gated_function():
    central = [s for s in SITES if s.kind == "central"]
    assert central                                    # the enumeration found the callers
    # assist.call_task is defined as _call; nothing else in app/ defines another `call_task`
    definers = [w for w in FUNCTIONS if w.endswith(":call_task")]
    assert definers == ["app/compliance/assist.py:call_task"], definers


def test_the_entry_points_carry_their_own_gate():
    """The entry points ORCH-051 found ungated refuse before any work: each has a gate call."""
    for where in (
        "app/routers/drawing_review.py:start",
        "app/review/service.py:run",
        "app/review/service.py:_ask",
        "app/interfaces/visual.py:check",
        "app/interfaces/findings.py:review_all",
        "app/interfaces/workflow.py:run_workflow",
        "app/interfaces/workflow.py:run_retry",
        "app/routers/fa_interfaces.py:start_run",
        "app/routers/fa_interfaces.py:retry_review",
        "app/redesign/service.py:plan",
        "app/review/scoped.py:preflight",
        "app/ifc/services/ai_symbol_review.py:review",
        "app/services/shop_drawings.py:_ai_review",
        "app/ai/verification.py:read_drf",
        "app/services/document_classification_ai.py:run",
    ):
        assert where in FUNCTIONS, where
        assert _gate_lines(FUNCTIONS[where]), f"{where} has no project_policy gate"
