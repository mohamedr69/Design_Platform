"""Review 31 (R31-01): why each Review 30 pick / alternate is or is not a Review 31 pick, from the same tested rules and
structured used sets as select_fresh_projects_r31.py. Metadata only; writes R30-PICKS-RECONCILED.json."""
import glob
import json
import pathlib

import selector_core as S
import used_sets

ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
CONTAINERS = frozenset({"Catalogues - All", "Maintenance", "Authority Guideline", "Systems", "SPL Calculation", "Juma Al Majid Group  IT Division", "Kuthup files"})
HERE = pathlib.Path(__file__).resolve().parent
R30 = {"picked": ["22936", "19905", "20561", "16385", "29255", "24752"], "alternates": ["25883", "19199", "28328", "26214"]}
topology, projects, ambiguous = S.classify(ROOT, CONTAINERS)
names = sorted({p["contractor"] for ps in projects.values() for p in ps})
clusters, cluster_of = S.cluster(names)
USED = used_sets.build(live_dbs=glob.glob("C:/Users/moham/Desktop/dev/dev/ep-platform/backend/*.db"))
used_canon = {S.canon(n) for n in USED["contractor_names"] if S.canon(n)}
for ep in USED["eps"]:
    for p in projects.get(ep, []):
        used_canon.add(S.canon(p["contractor"]))
fresh = S.fresh_projects(projects, ambiguous, cluster_of, USED["eps"], CONTAINERS)
r31 = json.loads((HERE / "FRESH-PROJECTS-R31.json").read_text(encoding="utf-8"))
r31_eps = {r["ep"]: k for k in ("picked", "alternates") for r in r31[k]}
amb = {a["ep"]: a for a in ambiguous if a.get("ep")}
out = []
for role, eps in R30.items():
    for ep in eps:
        ps = projects.get(ep, [])
        why = []
        if ep in USED["eps"]:
            why.append("EP in a used source: " + ", ".join(s for s, v in USED["per_source"].items() if ep in v.get("eps", ())))
        if ep in amb:
            why.append(f"ambiguous hierarchy ({amb[ep]['class']}): fail closed")
        if len(ps) > 1:
            why.append(f"{len(ps)} folders carry this EP: fail closed")
        used_cl = [p["contractor"] for p in ps if any(S.aliases(S.canon(m), u) for m in clusters[cluster_of[p["contractor"]]] for u in used_canon)]
        if used_cl:
            hits = sorted({u for p in ps for m in clusters[cluster_of[p["contractor"]]] for u in used_canon if S.aliases(S.canon(m), u)})
            why.append(f"contractor cluster already used (aliases of {hits[:4]})")
        if not why and ep in r31_eps:
            why.append(f"fresh; selected again by the Review 31 rules ({r31_eps[ep]})")
        elif not why and ep in fresh:
            why.append("fresh, but not reached in the seeded cluster order or below the metadata thresholds (eligible, not drawn)")
        out.append({"review30_role": role, "ep": ep, "contractor": [p["contractor"] for p in ps], "class": [p["class"] for p in ps],
                    "review31": r31_eps.get(ep, "not selected"), "reasons": why or ["no project folder found by the classifier"]})
(HERE / "R30-PICKS-RECONCILED.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for r in out:
    print(r["review30_role"], r["ep"], r["contractor"], r["review31"], r["reasons"])
