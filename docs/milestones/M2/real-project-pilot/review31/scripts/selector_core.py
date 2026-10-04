"""Review 31 (R31-01) selector rules, importable and unit-tested (test_selector_core.py): contractor canonicalisation, alias
detection, and the explicit, fail-closed folder topology classification. Metadata only (os.scandir)."""
from __future__ import annotations

import collections
import difflib
import os
import re

EP = re.compile(r"EP[- ]?(\d{3,6})", re.I)
GENERIC = {"llc", "l", "c", "co", "company", "est", "establishment", "trading", "contracting", "contractors", "contractor", "group", "fze", "fzc", "fzco",
           "ltd", "limited", "plc", "wll", "the", "and", "of", "uae", "inc", "corp", "corporation", "old", "projects", "project", "new", "files"}


def canon(name: str) -> str:
    s = re.sub(r"\([^)]*\)", " ", name or "").lower().replace("&", " and ")
    return " ".join(t for t in re.sub(r"[^a-z0-9]+", " ", s).split() if t not in GENERIC)


def aliases(a: str, b: str) -> bool:
    """Two CANONICAL contractor names are one company (fail closed): equal space-free forms, one token set inside the
    other, the same distinctive first word (ignoring al / el / the; >= 4 letters), or space-free similarity >= 0.85."""
    if not a or not b:
        return False
    na, nb = a.replace(" ", ""), b.replace(" ", "")
    ta, tb = set(a.split()), set(b.split())
    lead = lambda toks: next((t for t in toks if t not in ("al", "el", "the")), "")
    la, lb = lead(a.split()), lead(b.split())
    return (na == nb or (bool(ta) and bool(tb) and (ta <= tb or tb <= ta)) or (len(la) >= 4 and la == lb)
            or difflib.SequenceMatcher(None, na, nb).ratio() >= 0.85)


def cluster(names):
    clusters = []
    for n in names:
        c = canon(n)
        for cl in clusters:
            if any(aliases(c, canon(m)) for m in cl):
                cl.append(n)
                break
        else:
            clusters.append([n])
    return clusters, {n: i for i, cl in enumerate(clusters) for n in cl}


def classify(root: str, containers=frozenset()) -> tuple[collections.Counter, dict, list]:
    """(topology counts, projects: ep -> [{contractor, path, class}], ambiguous). Classes: project_at_root, container,
    contractor, no_projects; per EP folder: project, project_with_nested_eps, nested_project."""
    topology, projects, ambiguous = collections.Counter(), collections.defaultdict(list), []
    for top in sorted(os.scandir(root), key=lambda e: e.name):
        if not top.is_dir():
            continue
        if EP.search(top.name):
            topology["project_at_root"] += 1
            ambiguous.append({"path": top.path, "class": "project_at_root", "ep": EP.search(top.name).group(1)})
            continue
        if top.name in containers:
            topology["container"] += 1
            continue
        kids = [k for k in os.scandir(top.path) if k.is_dir()]
        topology["contractor" if any(EP.search(k.name) for k in kids) else "no_projects"] += 1
        for k in kids:
            if EP.search(k.name):
                ep = EP.search(k.name).group(1)
                nested = [g.name for g in os.scandir(k.path) if g.is_dir() and EP.search(g.name) and EP.search(g.name).group(1) != ep]
                cls = "project_with_nested_eps" if nested else "project"
                projects[ep].append({"contractor": top.name, "path": k.path, "class": cls})
                if nested:
                    ambiguous.append({"path": k.path, "class": cls, "ep": ep, "nested": nested[:5]})
            else:
                for g in os.scandir(k.path):
                    if g.is_dir() and EP.search(g.name):
                        ep = EP.search(g.name).group(1)
                        projects[ep].append({"contractor": top.name, "path": g.path, "class": "nested_project"})
                        ambiguous.append({"path": g.path, "class": "nested_project", "ep": ep})
    return topology, projects, ambiguous


def fresh_projects(projects: dict, ambiguous: list, cluster_of: dict, used_eps: set, containers=frozenset()) -> dict:
    """Unambiguous projects not used: one folder, class 'project', one contractor cluster, not in a container, not used."""
    amb = {a["ep"] for a in ambiguous}
    return {ep: ps for ep, ps in projects.items()
            if ep not in used_eps and ep not in amb and len(ps) == 1 and ps[0]["class"] == "project"
            and ps[0]["contractor"] not in containers and len({cluster_of[p["contractor"]] for p in ps}) == 1}
