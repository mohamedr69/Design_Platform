"""R40: for each site function reached only in the 'global' mode, the shortest call path from the lane entry (with the
edge kind of each step: scoped or global-only), to read by hand. Read-only. Usage: paths_why_r40.py <out json>"""
import collections, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import paths_mine_r40 as PM

def bfs(ix, entries):
    starts = []
    for e in entries:
        mod, name = e.split(":", 1)
        starts += [q for q in ix.funcs if q.startswith(mod + ":")] if name == "*" else [e]
    parent = {s: None for s in starts}
    kind = {}
    dq = collections.deque(starts)
    while dq:
        q = dq.popleft()
        if q not in ix.funcs:
            continue
        sc = ix.edges(q, "scoped")
        gl = ix.edges(q, "global")
        for n in sorted(sc) + sorted(gl - sc):
            if n not in parent:
                parent[n] = q
                kind[n] = "scoped" if n in sc else "global-only"
                dq.append(n)
    return parent, kind

out = {}
for lane, (t, entries) in PM.LANES.items():
    ix = PM.Index(PM.TREES[t])
    sites = ix.sites()
    parent, kind = bfs(ix, entries)
    sc_reach = PM.reach(ix, entries, "scoped")
    extra = sorted({s["function"] for s in sites if s["function"] in parent and s["function"] not in sc_reach})
    out[lane] = {}
    for f in extra:
        path, x = [], f
        while x is not None:
            path.append(f"{x} [{kind.get(x, 'entry')}]")
            x = parent[x]
        out[lane][f] = list(reversed(path))
pathlib.Path(sys.argv[1]).write_text(json.dumps(out, indent=1), encoding="utf-8")
for lane, v in out.items():
    print("==", lane)
    for f, p in v.items():
        print("  ", f)
        for step in p:
            print("       ", step)
