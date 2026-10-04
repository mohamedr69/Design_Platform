"""Step 2 of the cohort preparation (owner authorization AUTHORIZATION-2026-10-02.md): confirm from METADATA ONLY, for each
approved project in the Review 31 / 32 order, the EP number of its folder, its contractor identity, its hierarchy class
and its non-sealed status, re-using the tested Review 31 rules (selector_core, used_sets) unchanged. No file content is
read; no placeholder is hydrated (directory entries only).

A project passes when: exactly one folder carries the EP; the class is 'project' (no nested EP folder, not under a
container); the contractor folder is the one the Review 31 proposal recorded; the contractor cluster aliases no used
contractor; the EP is in no used source; it is not in the Round 2 selection (so not sealed). Mentions of the cohort EPs
in documents that only PROPOSE this cohort (the Review 31 / 32 reviewer notes) are listed per file and not counted as use.
A failing primary is replaced only by the next ordered alternate.
Writes PROJECT-AND-CONTRACTOR-VERIFICATION.csv and PROJECT-VERIFICATION.json."""
import csv
import datetime
import glob
import json
import pathlib
import re
import sys

sys.path.insert(0, "C:/t/iso/work/r2x/r31")
import selector_core as S  # noqa: E402
import used_sets  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
CONTAINERS = frozenset({"Catalogues - All", "Maintenance", "Authority Guideline", "Systems", "SPL Calculation", "Juma Al Majid Group  IT Division", "Kuthup files"})
PRIMARY = ["3563", "22349", "27331", "15744", "26687", "29255"]
ALTERNATES = ["22317", "29628", "25909", "28908"]
R31 = json.loads(pathlib.Path("C:/t/iso/work/r2x/r31/FRESH-PROJECTS-R31.json").read_text(encoding="utf-8"))
recorded = {r["ep"]: r for r in R31["picked"] + R31["alternates"]}
PROPOSAL_DOCS = re.compile(r"[\\/](M2-review-31|M2-review-32)[\\/]")

topology, projects, ambiguous = S.classify(ROOT, CONTAINERS)
names = sorted({p["contractor"] for ps in projects.values() for p in ps})
clusters, cluster_of = S.cluster(names)
USED = used_sets.build(live_dbs=glob.glob("C:/Users/moham/Desktop/dev/dev/ep-platform/backend/*.db"))
r2 = json.loads(pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
round2 = {p["ep"]: p for p in r2["projects"]}
sealed = sorted(ep for ep, p in round2.items() if "seal" in json.dumps(p).lower())
# S5 per-file attribution for the cohort EPs (narratives only)
cohort = set(PRIMARY + ALTERNATES)
narr = {}
for p in list(used_sets.MILESTONES.rglob("*.md")) + list(used_sets.REVIEWER.rglob("*.md")):
    if "review30" in p.parts or "review31" in p.parts:
        continue
    t = p.read_text(encoding="utf-8", errors="ignore")
    if p.name == "M2-REVIEW-RESPONSE.md":
        t = t.split("# Response to Independent M2 Review 30")[0]
    for ep in used_sets._eps(t) & cohort:
        narr.setdefault(ep, []).append(str(p))
used_canon = {S.canon(n) for n in USED["contractor_names"] if S.canon(n)}
for ep in USED["eps"] - cohort:
    for p in projects.get(ep, []):
        used_canon.add(S.canon(p["contractor"]))
amb = {a["ep"]: a for a in ambiguous if a.get("ep")}


def check(ep):
    ps = projects.get(ep, [])
    rows = {"ep": ep}
    fails = []
    rows["folders"] = len(ps)
    if len(ps) != 1:
        fails.append(f"{len(ps)} folders carry EP-{ep}")
    p = ps[0] if ps else {}
    rows["folder"] = p.get("path")
    rows["folder_name_ep"] = bool(p) and re.search(r"EP[- ]?" + ep + r"\b", pathlib.Path(p["path"]).name, re.I) is not None
    if p and not rows["folder_name_ep"]:
        fails.append("folder name does not carry the EP number")
    rows["class"] = p.get("class")
    if p and p.get("class") != "project":
        fails.append(f"hierarchy class {p.get('class')}")
    if ep in amb:
        fails.append(f"ambiguous hierarchy ({amb[ep]['class']})")
    rows["contractor"] = p.get("contractor")
    rows["contractor_canonical"] = S.canon(p.get("contractor", ""))
    rows["contractor_matches_r31"] = p.get("contractor") == recorded[ep]["contractor_raw"] and p.get("path") == recorded[ep]["folder"]
    if p and not rows["contractor_matches_r31"]:
        fails.append("contractor / folder differs from the Review 31 record")
    hits = sorted({u for m in clusters[cluster_of[p["contractor"]]] for u in used_canon if S.aliases(S.canon(m), u)}) if p else []
    rows["cluster_aliases"] = clusters[cluster_of[p["contractor"]]] if p else []
    rows["contractor_cluster_used_by"] = hits
    if hits:
        fails.append(f"contractor cluster aliases used contractors {hits}")
    srcs = [k for k, v in USED["per_source"].items() if ep in v["eps"]]
    proposal_only = ep in narr and all(PROPOSAL_DOCS.search(f) for f in narr[ep])
    rows["used_sources"] = srcs
    rows["narrative_mentions"] = narr.get(ep, [])
    real = [s for s in srcs if not (s == "S5 milestone narratives" and proposal_only)]
    if real:
        fails.append(f"EP in used sources {real}")
    rows["round2_selection"] = ep in round2
    rows["sealed"] = ep in sealed
    if ep in round2:
        fails.append("EP is in the Round 2 selection (exposed / exploration / sealed)")
    rows["passes"] = not fails
    rows["reasons"] = fails
    return rows


results = {ep: check(ep) for ep in PRIMARY + ALTERNATES}
alts = list(ALTERNATES)
cohort_final, replacements = [], []
for ep in PRIMARY:
    if results[ep]["passes"]:
        cohort_final.append(ep)
        continue
    while alts:
        a = alts.pop(0)
        if results[a]["passes"]:
            cohort_final.append(a)
            replacements.append({"failed": ep, "reasons": results[ep]["reasons"], "replaced_by": a})
            break
        replacements.append({"failed_alternate": a, "reasons": results[a]["reasons"]})
    else:
        replacements.append({"failed": ep, "reasons": results[ep]["reasons"], "replaced_by": None})
out = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "authorization": "AUTHORIZATION-2026-10-02.md",
       "content_read": "none: directory entries only", "rules": "selector_core / used_sets of Review 31 (sha256 bound in review31/BINDING-MANIFEST.json), unchanged",
       "used_eps": len(USED["eps"]), "databases_read": USED["databases_read"], "sealed_round2": sealed,
       "proposal_documents_not_counted_as_use": "reviewer notes M2-review-31 / M2-review-32 that only propose this cohort",
       "results": results, "replacements": replacements, "cohort": cohort_final, "remaining_alternates_in_order": alts}
(HERE / "PROJECT-VERIFICATION.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
with open(HERE / "PROJECT-AND-CONTRACTOR-VERIFICATION.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["role", "order", "ep", "folder", "folder_name_carries_ep", "folders_with_ep", "hierarchy_class", "contractor", "contractor_canonical",
                "matches_review31_record", "contractor_cluster_used_by", "used_sources", "narrative_mentions", "in_round2_selection", "sealed", "passes", "reasons", "in_cohort"])
    for i, ep in enumerate(PRIMARY + ALTERNATES):
        r = results[ep]
        w.writerow(["primary" if ep in PRIMARY else "alternate", i + 1, ep, r["folder"], r["folder_name_ep"], r["folders"], r["class"], r["contractor"], r["contractor_canonical"],
                    r["contractor_matches_r31"], "; ".join(r["contractor_cluster_used_by"]), "; ".join(r["used_sources"]), "; ".join(r["narrative_mentions"]),
                    r["round2_selection"], r["sealed"], r["passes"], "; ".join(r["reasons"]), ep in cohort_final])
print(json.dumps({"cohort": cohort_final, "replacements": replacements, "sealed": sealed, "used_eps": len(USED["eps"]), "dbs": USED["databases_read"]}, indent=1))
for ep in PRIMARY + ALTERNATES:
    print(ep, results[ep]["passes"], results[ep]["reasons"], results[ep]["used_sources"], results[ep]["narrative_mentions"])
