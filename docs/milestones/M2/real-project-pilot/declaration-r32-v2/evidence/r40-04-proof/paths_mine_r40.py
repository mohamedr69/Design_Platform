"""R40 (Verification 40, item 2): the verifier's OWN static enumeration of provider-call sites reachable from each lane's
entry point, written independently of review39/request_paths_r39.py. Read-only (ast only; nothing imported from the trees).

Sites (wider than the package's): every call whose callee attribute or name is 'complete', 'get_provider', 'set_provider',
'messages.create' / 'chat.completions.create' / 'responses.create', or the construction of a provider class
(ClaudeCodeProvider / ClaudeProvider / OpenAiProvider / LedgerProvider) -- in app/ and in the candidate's scripts/m2_eval6.py
(imported by the lanes' tripwire), excluding the definitions in app/ai/provider.py.
Edges, two resolutions:
  'scoped'  f() -> same-module def/class or a name imported into the module (module-level or inside any function);
            mod.f() -> f of an imported module; obj.f() with an unknown receiver -> every method f of a class defined in
            the same module or in any module the module imports (the package's rule, re-implemented);
  'global'  as 'scoped', but obj.f() with an unknown receiver -> EVERY function or method named f anywhere in the tree
            (a strict over-approximation: a site it does not reach cannot be reached by any name-resolved call).
  Both: a referenced (uncalled) function counts as an edge; a reached class brings all its methods; a nested def is
  reached with its parent.
Usage: paths_mine_r40.py <out json>"""
import ast
import hashlib
import json
import pathlib
import sys

TREES = {"baseline": pathlib.Path("C:/t/iso/frozen-r12/backend"), "candidate": pathlib.Path("C:/t/iso/cand-r29/backend")}
LANES = {"B": ("baseline", ["app.services.document_processing:run"]),
         "C": ("candidate", ["app.ai.evidence_reader:evidence_stage", "scripts.m2_eval6:*"]),
         "R": ("candidate", ["app.ai.evidence_reader:evidence_stage", "scripts.m2_eval6:*"])}
SITE_NAMES = {"complete", "get_provider", "set_provider"}
PROVIDER_CLASSES = {"ClaudeCodeProvider", "ClaudeProvider", "OpenAiProvider", "LedgerProvider"}


def modname(root, path):
    rel = path.relative_to(root).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


class Index:
    def __init__(self, root):
        self.root = root
        self.files = sorted(list((root / "app").rglob("*.py")) + ([root / "scripts" / "m2_eval6.py"] if (root / "scripts" / "m2_eval6.py").exists() else []))
        self.mods = {}
        self.funcs = {}          # qual -> (module, node, class or None)
        self.by_name = {}        # simple name -> set(qual)
        self.classes = {}        # module:Class -> [method quals]
        self.imports = {}        # module -> {alias: target}  target 'mod' or 'mod:name'
        for f in self.files:
            m = modname(root, f)
            tree = ast.parse(f.read_text(encoding="utf-8"), filename=str(f))
            self.mods[m] = (f, tree)
        for m, (f, tree) in self.mods.items():
            imp = {}
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for a in node.names:
                        imp[(a.asname or a.name).split(".")[0] if not a.asname else a.asname] = a.name if a.asname else a.name.split(".")[0]
                        if not a.asname:
                            imp[a.name] = a.name
                elif isinstance(node, ast.ImportFrom):
                    base = node.module or ""
                    if node.level:
                        pkg = m.split(".")
                        pkg = pkg[:len(pkg) - node.level] if not f.name == "__init__.py" else pkg[:len(pkg) - node.level + 1]
                        base = ".".join(pkg + ([node.module] if node.module else []))
                    for a in node.names:
                        imp[a.asname or a.name] = f"{base}:{a.name}"
            self.imports[m] = imp
            self._defs(m, tree.body, prefix="", cls=None)

    def _defs(self, m, body, prefix, cls):
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                q = f"{m}:{prefix}{node.name}"
                self.funcs[q] = (m, node, cls)
                self.by_name.setdefault(node.name, set()).add(q)
                if cls:
                    self.classes.setdefault(f"{m}:{cls}", []).append(q)
                self._defs(m, node.body, prefix + node.name + ".", None)
            elif isinstance(node, ast.ClassDef):
                q = f"{m}:{prefix}{node.name}"
                self.funcs[q] = (m, node, "__class__")
                self.by_name.setdefault(node.name, set()).add(q)
                self._defs(m, node.body, prefix + node.name + ".", node.name)

    def resolve_name(self, m, name):
        if f"{m}:{name}" in self.funcs:
            return {f"{m}:{name}"}
        t = self.imports[m].get(name)
        if t and ":" in t:
            mod, n = t.split(":", 1)
            if f"{mod}:{n}" in self.funcs:
                return {f"{mod}:{n}"}
            if f"{mod}.{n}" in self.mods:
                return {"MODULE:" + f"{mod}.{n}"}
        if t and t in self.mods:
            return {"MODULE:" + t}
        return set()

    def module_of_expr(self, m, expr):
        if isinstance(expr, ast.Name):
            r = self.resolve_name(m, expr.id)
            mods = [x[7:] for x in r if x.startswith("MODULE:")]
            if mods:
                return mods[0]
            t = self.imports[m].get(expr.id)
            if t and t in self.mods:
                return t
        if isinstance(expr, ast.Attribute):
            base = self.module_of_expr(m, expr.value)
            if base and f"{base}.{expr.attr}" in self.mods:
                return f"{base}.{expr.attr}"
        return None

    def imported_modules(self, m):
        out = {m}
        for t in self.imports[m].values():
            out.add(t.split(":")[0])
            if ":" in t and t.replace(":", ".") in self.mods:
                out.add(t.replace(":", "."))
        return out

    def edges(self, q, mode):
        m, node, cls = self.funcs[q]
        out = set()
        if cls == "__class__":
            out |= set(self.classes.get(q, []))
            return out
        prefix = q.split(":", 1)[1] + "."
        for other in self.funcs:
            if other.startswith(f"{m}:{prefix}") and other.count(".") == q.count(".") + 1:
                out.add(other)                                   # nested defs
        scoped = self.imported_modules(m)
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                out |= {x for x in self.resolve_name(m, sub.id) if not x.startswith("MODULE:")}
            elif isinstance(sub, ast.Attribute):
                mod = self.module_of_expr(m, sub.value)
                if mod:
                    if f"{mod}:{sub.attr}" in self.funcs:
                        out.add(f"{mod}:{sub.attr}")
                    continue
                cands = self.by_name.get(sub.attr, set())
                if mode == "global":
                    out |= cands
                else:
                    out |= {c for c in cands if c.split(":")[0] in scoped and self.funcs[c][2] not in (None, "__class__")}
                    out |= {c for c in cands if c.split(":")[0] == m}
        return out

    def sites(self):
        out = []
        for q, (m, node, cls) in self.funcs.items():
            if cls == "__class__" or m == "app.ai.provider":
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    f = sub.func
                    name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else None)
                    kind = None
                    if name in SITE_NAMES:
                        kind = name
                    elif name == "create" and isinstance(f, ast.Attribute) and isinstance(f.value, ast.Attribute) and f.value.attr in ("messages", "completions", "responses"):
                        kind = "sdk_create"
                    elif name in PROVIDER_CLASSES:
                        kind = "provider_class:" + name
                    if kind:
                        # the innermost function owning the call
                        owner = q
                        out.append({"function": owner, "line": sub.lineno, "kind": kind, "file": str(self.mods[m][0].relative_to(self.root)).replace("\\", "/")})
        # keep the innermost owner only (a call inside a nested def is listed under the nested def)
        best = {}
        for s in out:
            k = (s["file"], s["line"], s["kind"])
            if k not in best or len(s["function"]) > len(best[k]["function"]):
                best[k] = s
        return sorted(best.values(), key=lambda s: (s["file"], s["line"]))


def reach(ix, entries, mode):
    seen, stack = set(), []
    for e in entries:
        mod, name = e.split(":", 1)
        if name == "*":
            stack += [q for q in ix.funcs if q.startswith(mod + ":")]
        else:
            stack.append(e)
    while stack:
        q = stack.pop()
        if q in seen or q not in ix.funcs:
            continue
        seen.add(q)
        stack += list(ix.edges(q, mode) - seen)
    return seen


def main(argv):
    out = {"version": "r40-paths-mine-1", "trees": {}, "lanes": {}}
    ixs = {}
    for t, root in TREES.items():
        ix = Index(root)
        ixs[t] = ix
        sites = ix.sites()
        out["trees"][t] = {"modules": len(ix.mods), "functions": len(ix.funcs), "sites": sites, "site_count": len(sites),
                           "site_files": {s["file"]: hashlib.sha256((root / s["file"]).read_bytes()).hexdigest() for s in sites}}
    for lane, (t, entries) in LANES.items():
        ix = ixs[t]
        sites = out["trees"][t]["sites"]
        lane_out = {"tree": t, "entries": entries}
        for mode in ("scoped", "global"):
            r = reach(ix, entries, mode)
            reached = [s for s in sites if s["function"] in r]
            lane_out[mode] = {"functions_reached": len(r), "sites_reached": reached,
                              "reached_functions_with_sites": sorted({s["function"] for s in reached})}
        out["lanes"][lane] = lane_out
    pathlib.Path(argv[1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
    for lane, v in out["lanes"].items():
        for mode in ("scoped", "global"):
            print(lane, mode, v[mode]["functions_reached"], v[mode]["reached_functions_with_sites"])
    for t, v in out["trees"].items():
        print(t, v["modules"], v["functions"], v["site_count"])


if __name__ == "__main__":
    main(sys.argv)
