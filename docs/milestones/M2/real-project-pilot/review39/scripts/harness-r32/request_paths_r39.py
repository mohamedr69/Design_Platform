"""ORCH-08C change 1(a) (R39-04): a static, over-approximating call graph of each application tree, from each lane's
entry point to every provider-call site. Read-only: parses the trees' source files (ast), imports nothing from them,
starts no process, calls no model. Writes one JSON file (argv[1]).

Resolution (deliberately over-approximating, so a site is never missed by being under-resolved):
  * f(...)            -> a function / class of the same module, or a name imported into the module (anywhere in it)
  * mod.f(...)        -> mod's function / class f when mod is an imported module alias
  * self.f / cls.f    -> every method f of the classes of the same module
  * obj.f(...)        -> every method f of a class defined in the same module or in a module it imports
  * a function / method referenced without a call (a callback, functools.partial(f), task=f) is an edge too
  * a class reached is reached with all its methods (dataclass / protocol dispatch)
Provider-call sites: every `<x>.complete(` call and every `get_provider()` call outside app/ai/provider.py.
The result is a superset: every site it lists as reached is then read by hand (REQUEST-PATHS.md) for the setting that
enables it and its bounds; a site it lists as not reached has no static path from the lane's entry point."""
from __future__ import annotations

import ast
import hashlib
import json
import pathlib
import sys

TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r12/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r29/backend")}
ENTRIES = {"B": ("baseline", ["app.services.document_processing:run"]),
           "C": ("candidate", ["app.ai.evidence_reader:evidence_stage"]),
           "R": ("candidate", ["app.ai.evidence_reader:evidence_stage"])}
EXCLUDE_SITES = {"app/ai/provider.py"}


def modname(rel: pathlib.Path) -> str:
    parts = list(rel.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def analyse(root: pathlib.Path) -> dict:
    files = sorted(p for p in (root / "app").rglob("*.py"))
    mods = {}
    for p in files:
        rel = p.relative_to(root)
        mods[modname(rel)] = {"path": rel.as_posix(), "tree": ast.parse(p.read_text(encoding="utf-8")),
                              "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "is_pkg": p.name == "__init__.py"}
    funcs, classes = {}, {}
    for m, info in mods.items():
        def visit(node, prefix, cls, m=m):
            for ch in ast.iter_child_nodes(node):
                if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    q = f"{prefix}{ch.name}"
                    funcs[f"{m}:{q}"] = {"module": m, "name": ch.name, "class": cls, "node": ch}
                    visit(ch, q + ".", cls)
                elif isinstance(ch, ast.ClassDef):
                    q = f"{prefix}{ch.name}"
                    classes[f"{m}:{q}"] = {"module": m, "name": ch.name}
                    visit(ch, q + ".", f"{m}:{q}")
        visit(info["tree"], "", None)
    imports = {}
    for m, info in mods.items():
        names, aliases = {}, {}
        for n in ast.walk(info["tree"]):
            if isinstance(n, ast.Import):
                for a in n.names:
                    if a.asname:
                        aliases[a.asname] = a.name
                    else:
                        aliases[a.name] = a.name
                        aliases[a.name.split(".")[0]] = a.name.split(".")[0]
            elif isinstance(n, ast.ImportFrom):
                base = n.module or ""
                if n.level:
                    pkg = m.split(".") if info["is_pkg"] else m.split(".")[:-1]
                    pkg = pkg[: len(pkg) - (n.level - 1)]
                    base = ".".join(pkg + ([n.module] if n.module else []))
                for a in n.names:
                    full = f"{base}.{a.name}" if base else a.name
                    if full in mods:
                        aliases[a.asname or a.name] = full
                    else:
                        names[a.asname or a.name] = (base, a.name)
        imports[m] = {"names": names, "aliases": aliases}
    by_method = {}
    for k, f in funcs.items():
        if f["class"]:
            by_method.setdefault(f["name"], []).append(k)

    def targets_of_name(m, name):
        out = []
        k = f"{m}:{name}"
        if k in funcs or k in classes:
            out.append(k)
        if name in imports[m]["names"]:
            base, n = imports[m]["names"][name]
            k = f"{base}:{n}"
            if k in funcs or k in classes:
                out.append(k)
        return out

    def related_modules(m):
        return {m} | set(imports[m]["aliases"].values()) | {b for b, _ in imports[m]["names"].values()}

    edges, sites = {}, []
    for k, f in funcs.items():
        m = f["module"]
        out = set()
        for n in ast.walk(f["node"]):
            if isinstance(n, ast.Call) and mods[m]["path"] not in EXCLUDE_SITES:
                fn = n.func
                if isinstance(fn, ast.Attribute) and fn.attr == "complete":
                    sites.append({"function": k, "line": n.lineno, "kind": "complete", "path": mods[m]["path"]})
                if (isinstance(fn, ast.Name) and fn.id == "get_provider") or (isinstance(fn, ast.Attribute) and fn.attr == "get_provider"):
                    sites.append({"function": k, "line": n.lineno, "kind": "get_provider", "path": mods[m]["path"]})
            if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load):
                out.update(targets_of_name(m, n.id))
            elif isinstance(n, ast.Attribute) and isinstance(n.ctx, ast.Load):
                v = n.value
                if isinstance(v, ast.Name) and v.id in imports[m]["aliases"]:
                    tm = imports[m]["aliases"][v.id]
                    kk = f"{tm}:{n.attr}"
                    if kk in funcs or kk in classes:
                        out.add(kk)
                    elif f"{tm}.{n.attr}" in mods:
                        pass
                elif isinstance(v, ast.Name) and v.id in ("self", "cls"):
                    out.update(x for x in by_method.get(n.attr, []) if funcs[x]["module"] == m)
                else:
                    rel = related_modules(m)
                    out.update(x for x in by_method.get(n.attr, []) if funcs[x]["module"] in rel)
        edges[k] = sorted(out - {k})
    for c in classes:
        edges[c] = sorted(x for x, f in funcs.items() if f["class"] == c)
    return {"mods": mods, "funcs": funcs, "classes": classes, "edges": edges, "sites": sites}


def reach(graph, entries):
    parent = {e: None for e in entries}
    todo = list(entries)
    while todo:
        x = todo.pop(0)
        for y in graph["edges"].get(x, []):
            if y not in parent:
                parent[y] = x
                todo.append(y)
    return parent


def path_to(parent, x):
    out = []
    while x is not None:
        out.append(x)
        x = parent[x]
    return list(reversed(out))


def main(argv):
    result = {"version": "request-paths-r39-2026-10-04.1", "method": (__doc__ or "").strip(), "trees": {}, "lanes": {}}
    graphs = {}
    for t, root in TREES.items():
        g = analyse(root)
        graphs[t] = g
        result["trees"][t] = {"root": root.as_posix(), "modules": len(g["mods"]), "functions": len(g["funcs"]), "sites": g["sites"],
                              "site_files": {s["path"]: g["mods"][g["funcs"][s["function"]]["module"]]["sha256"] for s in g["sites"]}}
    for lane, (t, entries) in ENTRIES.items():
        g = graphs[t]
        parent = reach(g, entries)
        reached = [s | {"call_path": path_to(parent, s["function"])} for s in g["sites"] if s["function"] in parent]
        result["lanes"][lane] = {"tree": t, "entries": entries, "functions_reached": len(parent), "sites_reached": reached,
                                 "sites_not_reached": [s for s in g["sites"] if s["function"] not in parent]}
    result["lanes"]["P"] = {"tree": "none (harness only)", "entries": ["run_control_r38.probe_r38"],
                            "note": "lane P runs no application code: it re-sends a seeded sample of C's dispatched payloads through the harness chain"}
    pathlib.Path(argv[1]).write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    for lane, v in result["lanes"].items():
        if "sites_reached" in v:
            print(lane, v["functions_reached"], sorted({s["function"] for s in v["sites_reached"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
