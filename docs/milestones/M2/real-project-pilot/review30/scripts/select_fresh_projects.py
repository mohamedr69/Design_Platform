"""Review 30, R30-03 Option B: metadata-only candidate list of FRESH projects for a generalisation validation.
No file content is read and nothing is rendered: directory entries, file names, sizes and attributes only (a OneDrive
placeholder is not hydrated by a stat). Nothing is staged, labelled or sent anywhere.

Excluded projects: every EP number referenced anywhere in the M1 / M2 milestone documents, packages and the backend test
suites (M2-USED-PROJECTS.json: the 34 Round 2 projects -- exposed, exploration, sealed -- the Review 05 holdout, the
pilot, fixtures and any number merely mentioned in a selection record), and projects only in non-project containers.
Excluded contractors: the contractor of any excluded project that has a folder under the root (template families of a
used contractor are treated as exposed). One project per remaining contractor, contractors in seeded order; a project is
eligible with >= 20 PDFs, >= 5 PDFs whose path names a review / approval signal and >= 5 whose path names a drawing
signal. Six picks and four alternates. Seed fixed below.
Writes FRESH-PROJECT-CANDIDATES.json."""
import collections
import datetime
import json
import os
import pathlib
import random
import re

SEED = "m2-r30-fresh-projects-2026-10-02"
ROOT = r"C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
NOT_PROJECT_CONTAINERS = {"Catalogues - All", "Maintenance", "Authority Guideline", "Systems", "SPL Calculation", "Juma Al Majid Group  IT Division",
                          "Kuthup files"}
HERE = pathlib.Path(__file__).resolve().parent
USED = json.loads((HERE / "M2-USED-PROJECTS.json").read_text(encoding="utf-8"))
used_eps = set(USED["ep_referenced_in_m1_m2_docs_and_tests"]) | set(USED["round2_projects"])
REVIEW = re.compile(r"approv|comment|review|status|consultant|reply|stamp|resubmit|reject|\bnoc\b", re.I)
DRAWING = re.compile(r"shop ?d(?:wg|rawing)|\bdwg|\bsd\b|drawing|layout|riser|schematic", re.I)
RECALL, OFFLINE = 0x400000, 0x1000


def walk(path):
    pdf = review = drawing = placeholders = 0
    for dirpath, _dirs, files in os.walk(path):
        for f in files:
            if not f.lower().endswith(".pdf"):
                continue
            full = os.path.join(dirpath, f)
            try:
                st = os.stat(full, follow_symlinks=False)
            except OSError:
                continue
            pdf += 1
            rel = os.path.relpath(full, path)
            review += bool(REVIEW.search(rel))
            drawing += bool(DRAWING.search(rel))
            placeholders += bool(getattr(st, "st_file_attributes", 0) & (RECALL | OFFLINE))
    return {"pdf": pdf, "pdf_with_review_signal_in_path": review, "pdf_with_drawing_signal_in_path": drawing, "pdf_placeholders_not_local": placeholders}


folders = []
for c in sorted(os.scandir(ROOT), key=lambda e: e.name):
    if c.is_dir():
        for p in sorted(os.scandir(c.path), key=lambda e: e.name):
            if p.is_dir():
                m = re.search(r"EP[- ]?(\d{3,6})", p.name, re.I)
                folders.append({"contractor": c.name, "folder": p.name, "path": p.path, "ep": m.group(1) if m else None})
by_ep = collections.defaultdict(list)
for f in folders:
    if f["ep"]:
        by_ep[f["ep"]].append(f)
used_contractors = sorted({f["contractor"] for ep in used_eps for f in by_ep.get(ep, [])} - NOT_PROJECT_CONTAINERS)
population = {ep: fs for ep, fs in by_ep.items() if ep not in used_eps and not any(f["contractor"] in NOT_PROJECT_CONTAINERS for f in fs)
              and not any(f["contractor"] in used_contractors for f in fs)}
strata = collections.defaultdict(list)
for ep, fs in sorted(population.items()):
    strata[fs[0]["contractor"]].append(ep)
rng = random.Random(SEED)
contractors = sorted(strata)
rng.shuffle(contractors)
for c in contractors:
    rng.shuffle(strata[c])
picked, alternates, rejected = [], [], []
for c in contractors:
    if len(picked) >= 6 and len(alternates) >= 4:
        break
    for ep in strata[c]:
        meta = collections.Counter()
        for f in population[ep]:
            meta.update(walk(f["path"]))
        entry = {"ep": ep, "contractor": c, "folders": [f["path"] for f in population[ep]], **dict(meta)}
        ok = meta["pdf"] >= 20 and meta["pdf_with_review_signal_in_path"] >= 5 and meta["pdf_with_drawing_signal_in_path"] >= 5
        if ok:
            (picked if len(picked) < 6 else alternates).append({**entry, "eligibility": "pdf >= 20, review-signal paths >= 5, drawing-signal paths >= 5 (names only)"})
            break
        rejected.append({**entry, "rejected": "below the metadata thresholds"})
out = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "seed": SEED, "root": ROOT,
       "content_read": "none: directory entries, file names, sizes and attributes only; nothing opened, rendered, staged or sent",
       "excluded_projects": len(used_eps), "excluded_contractors": used_contractors,
       "population": {"folders": len(folders), "distinct_ep": len(by_ep), "eligible_distinct_ep_after_exclusions": len(population), "eligible_contractors": len(strata)},
       "picked": picked, "alternates": alternates, "rejected_before_pick": rejected,
       "permission": "NOT permitted: these projects are outside the owner's Round 2 permission (34 frozen projects); a separate owner permission naming them is required before any document is opened"}
(HERE / "FRESH-PROJECT-CANDIDATES.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out["population"]), "excluded contractors", len(used_contractors))
for p in picked + alternates:
    print(p["ep"], p["contractor"][:40], {k: p[k] for k in ("pdf", "pdf_with_review_signal_in_path", "pdf_with_drawing_signal_in_path", "pdf_placeholders_not_local")})
print("rejected", len(rejected))
