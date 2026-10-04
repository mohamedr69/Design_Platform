"""Review 31 (R31-01): metadata-only fresh-project selection using the TESTED rules (selector_core.py) and the structured
used sets (used_sets.py). No file is opened, rendered, downloaded or staged; a OneDrive placeholder is not hydrated by stat.
Every pick and alternate carries an evidence row stating why its project AND its contractor cluster are fresh.
Writes FRESH-PROJECTS-R31.json."""
import collections
import datetime
import difflib
import glob
import json
import os
import pathlib
import random
import re

import selector_core as S
import used_sets

SEED = "m2-r31-fresh-projects-2026-10-02"
ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
CONTAINERS = frozenset({"Catalogues - All", "Maintenance", "Authority Guideline", "Systems", "SPL Calculation", "Juma Al Majid Group  IT Division", "Kuthup files"})
REVIEW = re.compile(r"approv|comment|review|status|consultant|reply|stamp|resubmit|reject|\bnoc\b", re.I)
DRAWING = re.compile(r"shop ?d(?:wg|rawing)|\bdwg|\bsd\b|drawing|layout|riser|schematic", re.I)
RECALL, OFFLINE = 0x400000, 0x1000
HERE = pathlib.Path(__file__).resolve().parent

topology, projects, ambiguous = S.classify(ROOT, CONTAINERS)
names = sorted({p["contractor"] for ps in projects.values() for p in ps})
clusters, cluster_of = S.cluster(names)
USED = used_sets.build(live_dbs=glob.glob("C:/Users/moham/Desktop/dev/dev/ep-platform/backend/*.db"))
used_eps = USED["eps"]
used_canon = {S.canon(n) for n in USED["contractor_names"] if S.canon(n)}
for ep in used_eps:
    for p in projects.get(ep, []):
        used_canon.add(S.canon(p["contractor"]))
used_clusters = {cluster_of[n] for n in names if any(S.aliases(S.canon(n), u) for u in used_canon)}
fresh = S.fresh_projects(projects, ambiguous, cluster_of, used_eps, CONTAINERS)
by_cluster = collections.defaultdict(list)
for ep, ps in sorted(fresh.items()):
    if cluster_of[ps[0]["contractor"]] not in used_clusters:
        by_cluster[cluster_of[ps[0]["contractor"]]].append(ep)
rng = random.Random(SEED)
order = sorted(by_cluster)
rng.shuffle(order)
for cl in order:
    rng.shuffle(by_cluster[cl])


def walk(path):
    c = collections.Counter()
    for dirpath, _d, files in os.walk(path):
        for f in files:
            if f.lower().endswith(".pdf"):
                full = os.path.join(dirpath, f)
                try:
                    st = os.stat(full, follow_symlinks=False)
                except OSError:
                    continue
                rel = os.path.relpath(full, path)
                c["pdf"] += 1
                c["review_signal_paths"] += bool(REVIEW.search(rel))
                c["drawing_signal_paths"] += bool(DRAWING.search(rel))
                c["placeholders_not_local"] += bool(getattr(st, "st_file_attributes", 0) & (RECALL | OFFLINE))
    return c


def nearest(cl):
    best = (0.0, None)
    for n in clusters[cl]:
        for u in used_canon:
            r = difflib.SequenceMatcher(None, S.canon(n).replace(" ", ""), u.replace(" ", "")).ratio()
            if r > best[0]:
                best = (round(r, 3), u)
    return best


picked, alternates, rejected = [], [], []
for cl in order:
    if len(picked) >= 6 and len(alternates) >= 4:
        break
    for ep in by_cluster[cl]:
        p = fresh[ep][0]
        meta = walk(p["path"])
        sim, near = nearest(cl)
        row = {"ep": ep, "folder": p["path"], "topology_class": p["class"], "contractor_raw": p["contractor"], "contractor_canonical": S.canon(p["contractor"]),
               "contractor_cluster_aliases": clusters[cl], **dict(meta),
               "project_fresh": {"ep_in_used_sources": ep in used_eps, "ambiguous_hierarchy": False, "folders": 1,
                                 "used_sources_checked": sorted(USED["sources"])},
               "contractor_fresh": {"cluster_used": False, "aliases_checked_against_used": len(used_canon), "nearest_used_canonical": near,
                                    "nearest_similarity": sim, "alias_rules": "space-free equality, token subset, same first distinctive word, similarity >= 0.85"}}
        if meta["pdf"] >= 20 and meta["review_signal_paths"] >= 5 and meta["drawing_signal_paths"] >= 5:
            row["eligibility"] = "pdf >= 20, review-signal paths >= 5, drawing-signal paths >= 5 (names only)"
            (picked if len(picked) < 6 else alternates).append(row)
            break
        rejected.append({**row, "rejected": "below the metadata thresholds"})
out = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "seed": SEED, "root": ROOT,
       "content_read": "none: directory entries, file names, sizes and attributes only; nothing opened, rendered, downloaded, staged or sent",
       "topology": dict(topology), "ambiguous_count": len(ambiguous), "ambiguous": ambiguous,
       "contractor_clusters": len(clusters), "alias_clusters": [c for c in clusters if len(c) > 1],
       "used": {"eps": len(used_eps), "eps_list": sorted(used_eps, key=int), "contractor_names": sorted(USED["contractor_names"]),
                "databases_read": USED["databases_read"], "sources": USED["sources"]},
       "used_clusters": len(used_clusters), "fresh_clusters_with_projects": len(by_cluster),
       "picked": picked, "alternates": alternates, "rejected_before_pick": rejected,
       "permission": "NOT permitted: outside the Round 2 permission; a new owner permission naming these EP numbers is required before any document is downloaded, opened or rendered"}
(HERE / "FRESH-PROJECTS-R31.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("topology", "ambiguous_count", "contractor_clusters", "used_clusters", "fresh_clusters_with_projects")}), "used eps", len(used_eps))
for r in picked + alternates:
    print(r["ep"], r["contractor_raw"][:40], "|", r["contractor_canonical"], "| near", r["contractor_fresh"]["nearest_used_canonical"], r["contractor_fresh"]["nearest_similarity"],
          "| pdf", r["pdf"], r["review_signal_paths"], r["drawing_signal_paths"])
