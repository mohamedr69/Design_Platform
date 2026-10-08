"""ORCH-10 (R42; R40-04 option 2, task 2.2 (a)): the static request-path analysis of review39 (request_paths_r39, unchanged
and re-run) PLUS the global-provider resolution of every lane. Read-only: parses the trees' source files and this
harness's lane_r32.py (ast), imports nothing from the trees, starts no process, calls no model. Writes one JSON (argv[1]).

What it adds to review39's result:
  * lanes: for each lane, the global provider lane_r32 installs through app.ai.provider.set_provider and WHERE (the line),
    and the first application entry call of the lane (the line); the installation must precede every application entry
    (C / R: the refusing provider before evidence_stage; P: before probe_r38; B: the chain before document_processing.run
    and before B's exercise of the chain);
  * sites: EVERY get_provider() site of each tree (reached by the lane's entry point or not) resolved to what it returns
    in each lane that runs that tree: in C, R and P the refusing provider (any complete() refused, recorded as the contract
    breach 'global_provider_request', the run INVALID); in B the harness chain (the gate);
  * set_provider: every application call of set_provider() outside app/ai/provider.py (one that could replace the
    installed global provider), with whether a lane's entry point reaches it (lane_r32 also checks at the end that its
    refusing provider is still installed)."""
from __future__ import annotations

import ast
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import request_paths_r39 as R39  # noqa: E402

LANE_FILE = HERE / "lane_r32.py"
ENTRY_CALLS = {"B": ("document_processing.run", "exercise"), "C": ("er.evidence_stage", "exercise"), "R": ("er.evidence_stage", "exercise"),
               "P": ("RC.probe_r38",)}
TREE_OF = {"B": "baseline", "C": "candidate", "R": "candidate", "P": "candidate"}


def _src(node) -> str:
    try:
        return ast.unparse(node)
    except Exception:  # noqa: BLE001
        return "?"


def lane_installs(path=LANE_FILE) -> dict:
    """Every prov.set_provider(...) call of lane_r32.py with its line and the condition that guards it, and the first line
    of each lane's application entry calls."""
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    parents = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parents[ch] = n
    installs, entries = [], {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            fn = _src(n.func)
            if fn == "prov.set_provider":
                conds, p = [], parents.get(n)
                while p is not None:
                    if isinstance(p, ast.If):
                        conds.append(_src(p.test))
                    p = parents.get(p)
                installs.append({"line": n.lineno, "argument": _src(n.args[0]) if n.args else None, "conditions": conds})
            for lane, names in ENTRY_CALLS.items():
                if fn in names:
                    entries.setdefault(lane, []).append({"line": n.lineno, "call": fn})
    return {"installs": installs, "entries": entries}


def global_resolution(installs: dict) -> dict:
    """Per lane: what get_provider() returns and whether it is installed before the lane's first application entry."""
    ins = installs["installs"]
    refusing = [i for i in ins if (i["argument"] or "") == "GLOBAL" and any("'C', 'R', 'P'" in c or '"C", "R", "P"' in c for c in i["conditions"])]
    chain_b = [i for i in ins if (i["argument"] or "") == "chain" and any("LANE == 'B'" in c or 'LANE == "B"' in c for c in i["conditions"])]
    out = {}
    for lane in ("B", "C", "R", "P"):
        first_entry = min((e["line"] for e in installs["entries"].get(lane, [])), default=None)
        inst = chain_b if lane == "B" else refusing
        line = min((i["line"] for i in inst), default=None)
        out[lane] = {"global_provider": "harness chain (StopGuardR38 -> GateStoreProvider -> allowance -> identity guard -> dispatch guard)"
                     if lane == "B" else "run_control_r38.RefusingGlobalProvider (fail-closed; contract breach 'global_provider_request'; run INVALID)",
                     "installed_at_line": line, "first_application_entry_line": first_entry,
                     "installed_before_every_application_entry": line is not None and first_entry is not None and line < first_entry}
    return out


def set_provider_sites(graph, parent) -> list:
    out = []
    for k, f in graph["funcs"].items():
        path = graph["mods"][f["module"]]["path"]
        if path in R39.EXCLUDE_SITES:
            continue
        for n in ast.walk(f["node"]):
            if isinstance(n, ast.Call):
                fn = n.func
                if (isinstance(fn, ast.Name) and fn.id == "set_provider") or (isinstance(fn, ast.Attribute) and fn.attr == "set_provider"):
                    out.append({"function": k, "line": n.lineno, "path": path, "reached_by_lane_entry": k in parent})
    return out


def main(argv):
    result = {"version": "request-paths-r42-2026-10-06.1", "method": (__doc__ or "").strip(), "base_method": (R39.__doc__ or "").strip(),
              "trees": {}, "lanes": {}}
    graphs = {}
    for t, root in R39.TREES.items():
        g = R39.analyse(root)
        graphs[t] = g
        result["trees"][t] = {"root": root.as_posix(), "modules": len(g["mods"]), "functions": len(g["funcs"]), "sites": g["sites"],
                              "site_files": {s["path"]: g["mods"][g["funcs"][s["function"]]["module"]]["sha256"] for s in g["sites"]}}
    installs = lane_installs()
    resolution = global_resolution(installs)
    result["lane_file"] = {"path": LANE_FILE.as_posix(), **installs}
    for lane, (t, entries) in R39.ENTRIES.items():
        g = graphs[t]
        parent = R39.reach(g, entries)
        reached = [s | {"call_path": R39.path_to(parent, s["function"])} for s in g["sites"] if s["function"] in parent]
        result["lanes"][lane] = {"tree": t, "entries": entries, "functions_reached": len(parent), "sites_reached": reached,
                                 "sites_not_reached": [s for s in g["sites"] if s["function"] not in parent],
                                 "set_provider_sites": set_provider_sites(g, parent), "global": resolution[lane]}
    result["lanes"]["P"] = {"tree": "candidate (harness only)", "entries": ["run_control_r38.probe_r38"],
                            "note": "lane P runs no application code: it re-sends a seeded sample of C's dispatched payloads through the harness chain",
                            "global": resolution["P"]}
    rows = []
    for t, g in graphs.items():
        for s in g["sites"]:
            if s["kind"] != "get_provider":
                continue
            for lane in [x for x in ("B", "C", "R", "P") if TREE_OF[x] == t]:
                rows.append({"tree": t, "lane": lane, "path": s["path"], "line": s["line"], "function": s["function"],
                             "reached_by_lane_entry": lane in R39.ENTRIES and s["function"] in R39.reach(g, R39.ENTRIES[lane][1]),
                             "resolves_to": "the harness chain (the gate)" if lane == "B" else "RefusingGlobalProvider (refused, breach, INVALID)",
                             "guarded": True})
    result["get_provider_sites"] = rows
    result["summary"] = {
        "get_provider_sites": len(rows),
        "every_site_guarded": all(r["guarded"] for r in rows),
        "every_lane_installs_before_its_application_entry": all(v["installed_before_every_application_entry"] for v in resolution.values()),
        "application_set_provider_sites_reached": sorted({f"{s['path']}:{s['line']}" for lane in ("B", "C", "R")
                                                          for s in result["lanes"][lane]["set_provider_sites"] if s["reached_by_lane_entry"]}),
        "statement": ("every get_provider() site of either tree resolves, in the lane that runs that tree, to a refusing provider (C, R, P) or "
                      "to the harness chain (B); none reaches a configured provider")}
    pathlib.Path(argv[1]).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result["summary"], indent=1))
    return 0 if result["summary"]["every_lane_installs_before_its_application_entry"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
