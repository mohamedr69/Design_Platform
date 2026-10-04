"""Round 2 project selection (M2 review 06, section 7): reproducible, seeded, stratified by contractor; metadata only.
No file content is read: directory entries, sizes and attributes (a OneDrive placeholder is not hydrated)."""
import collections, datetime, hashlib, json, os, random, re, stat

SEED = "m2-round2-2026-09-28"
ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
EXPOSED = {"30784": "pilot", "30088": "pilot", "29076": "pilot", "26369": "pilot", "26082": "pilot", "25091": "pilot", "13777": "pilot",
           "19977": "pilot", "14119": "pilot", "27474": "pilot", "28569": "R5 holdout (exposed)", "8430": "R5 holdout (exposed)",
           "19138": "R5 holdout (exposed)", "28605": "R5 holdout (exposed)"}
NOT_PROJECT_CONTAINERS = {"Catalogues - All", "Maintenance", "Authority Guideline", "Systems", "SPL Calculation", "Juma Al Majid Group  IT Division",
                          "Kuthup files"}
RECALL = 0x400000   # FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
OFFLINE = 0x1000


def walk(path):
    ext, placeholders, files, size = collections.Counter(), 0, 0, 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            try:
                st = os.stat(os.path.join(dirpath, f), follow_symlinks=False)
            except OSError:
                continue
            files += 1; size += st.st_size
            ext[os.path.splitext(f)[1].lower()] += 1
            attrs = getattr(st, "st_file_attributes", 0)
            placeholders += bool(attrs & (RECALL | OFFLINE))
    return {"files": files, "bytes": size, "pdf": ext[".pdf"], "word": ext[".doc"] + ext[".docx"], "extensions": dict(ext.most_common(12)),
            "placeholders_not_local": placeholders}


folders = []
for c in sorted(os.scandir(ROOT), key=lambda e: e.name):
    if not c.is_dir():
        continue
    for p in sorted(os.scandir(c.path), key=lambda e: e.name):
        if p.is_dir():
            m = re.search(r"EP[- ]?(\d{3,6})", p.name, re.I)
            folders.append({"contractor": c.name, "folder": p.name, "path": p.path, "ep": m.group(1) if m else None})
by_ep = collections.defaultdict(list)
for f in folders:
    if f["ep"]:
        by_ep[f["ep"]].append(f)
population = {ep: fs for ep, fs in by_ep.items() if ep not in EXPOSED and not any(f["contractor"] in NOT_PROJECT_CONTAINERS for f in fs)}
exclusions = {"exposed": sorted(EXPOSED), "no_EP_number_folders": sum(1 for f in folders if not f["ep"]),
              "only_in_non_project_containers": sorted(ep for ep, fs in by_ep.items() if ep not in EXPOSED and all(f["contractor"] in NOT_PROJECT_CONTAINERS for f in fs)),
              "multi_folder_projects": {ep: len(fs) for ep, fs in population.items() if len(fs) > 1}}
# stratum = contractor of the project's first folder; one project per contractor per round of picks, contractors in seeded order
rng = random.Random(SEED)
strata = collections.defaultdict(list)
for ep, fs in sorted(population.items()):
    strata[fs[0]["contractor"]].append(ep)
contractors = sorted(strata); rng.shuffle(contractors)
for c in contractors:
    rng.shuffle(strata[c])
picked, alternates = [], []
used = set()
# walk contractors round-robin; accept a project with at least 5 PDFs (a project we can learn from); record rejects
rounds = 0
while len(picked) < 20 and rounds < 6:
    for c in contractors:
        if len(picked) >= 20:
            break
        pool = [ep for ep in strata[c] if ep not in used]
        if not pool:
            continue
        ep = pool[0]; used.add(ep)
        meta = [walk(f["path"]) for f in population[ep]]
        agg = {"files": sum(m["files"] for m in meta), "pdf": sum(m["pdf"] for m in meta), "word": sum(m["word"] for m in meta),
               "placeholders_not_local": sum(m["placeholders_not_local"] for m in meta), "bytes": sum(m["bytes"] for m in meta),
               "extensions": dict(sum((collections.Counter(m["extensions"]) for m in meta), collections.Counter()).most_common(10))}
        entry = {"ep": ep, "contractor": c, "folders": [f["path"] for f in population[ep]], **agg}
        if agg["pdf"] >= 5:
            picked.append(entry)
        else:
            alternates.append({**entry, "rejected": "fewer than 5 PDFs"})
    rounds += 1
# cohort assignment by a second seeded shuffle: first 10 exploration, next 10 sealed
order = list(range(len(picked))); random.Random(SEED + ":cohort").shuffle(order)
for i, k in enumerate(order):
    picked[k]["cohort"] = "exploration (new)" if i < 10 else "sealed validation (new)"
exposed = []
for ep, why in EXPOSED.items():
    fs = by_ep.get(ep) or []
    exposed.append({"ep": ep, "cohort": f"regression / exposed ({why})", "contractor": fs[0]["contractor"] if fs else None, "folders": [f["path"] for f in fs]})
out = {"at": datetime.datetime.now().isoformat(timespec="seconds"), "seed": SEED, "root": ROOT,
       "method": "population = EP-numbered project folders outside non-project containers and outside the 14 exposed projects; strata = contractor; "
                 "contractors shuffled with the seed, one project per contractor per round, a project needs >= 5 PDFs; cohort split by a second seeded shuffle",
       "population": {"folders": len(folders), "distinct_ep": len(by_ep), "eligible_distinct_ep": len(population), "contractors": len(strata)},
       "exclusions": exclusions, "projects": exposed + picked, "alternates_rejected": alternates,
       "content_read": "none (metadata only); template families are unobserved until staging",
       "totals": {"exposed": len(exposed), "exploration": sum(1 for p in picked if p["cohort"].startswith("exploration")),
                  "sealed": sum(1 for p in picked if p["cohort"].startswith("sealed")),
                  "pdf_exploration": sum(p["pdf"] for p in picked if p["cohort"].startswith("exploration")),
                  "pdf_sealed": sum(p["pdf"] for p in picked if p["cohort"].startswith("sealed")),
                  "word_new": sum(p["word"] for p in picked)}}
json.dump(out, open(r"C:\t\iso\work\round2\ROUND2-SELECTION.json", "w", encoding="utf-8"), indent=1)
print(json.dumps(out["population"]), json.dumps(out["totals"]))
for p in picked:
    print(p["cohort"][:11], p["ep"], p["contractor"][:40], "pdf", p["pdf"], "word", p["word"], "not local", p["placeholders_not_local"])
print("rejected", [(a["ep"], a["pdf"]) for a in alternates])
