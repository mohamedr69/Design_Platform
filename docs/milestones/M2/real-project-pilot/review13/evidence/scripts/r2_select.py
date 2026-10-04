"""M2 Round 2 exploration, step 2: freeze the file-level selection BEFORE any content is read (metadata only).

Rules (the Round 1 pilot's sample.py, with the frozen Round 2 plan's quotas):
  * cohort: the 10 frozen EXPLORATION projects only (ROUND2-SELECTION.json, hash-checked); sealed never touched;
  * eligibility: the frozen candidate's sync contract -- .pdf, and Word (.doc/.docx) that
    `app.services.transmittals.is_transmittal` accepts (the function itself, from frozen-r12);
  * strata: the Round 1 path rules (sample.py STRATA), unchanged;
  * target: 450 distinct-content documents for the exploration cohort; per-project cap 20 % of the cohort (90);
    small projects (eligible <= their equal share) are taken in full; the rest shares the remainder equally, capped;
    within a project: every stratum present gets one, the rest proportional, 45 % template-copy cap per stratum,
    top-up smallest strata first (sample.py's allocation);
  * order: a seeded shuffle within each stratum; the first `allocation` files are primary, the rest are the ordered
    replacement list -- used only when a primary turns out to be a content duplicate or unreadable at staging
    (never to pick easier documents); a shortfall is reported, never filled from another cohort;
  * BOQ / design sheets: a separate name rule (design sheet / BOQ / bill of quantities in the file name), recorded as
    candidates; which are real BOQ tables is established after staging."""
import collections
import datetime
import hashlib
import json
import pathlib
import random
import re
import sys

sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
from app.services.transmittals import is_transmittal  # noqa: E402  the sync contract's own rule

INV = pathlib.Path("C:/t/iso/work/r2x/inventory")
OUT = pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-SELECTION.json")
SEED = "m2-round2-exploration-2026-09-29"
TARGET, CAP_PROJECT, CAP_STRATUM = 450, 90, 0.45
STRATA = [("scan", r"\bscan"), ("design_sheet", r"design sheet|design\b.*\.pdf$|boq|bill of quant|\bdrf\b"), ("transmittal_word", None),
          ("reply", r"reply|comment|crs\b|response"), ("approval_sample", r"approv|sample|\bsar\b"), ("submittal", r"\bms\b|submittal|material|\bmas\b|method"),
          ("spec_compliance", r"spec|complian|standard"), ("calc", r"calc"), ("drawing_ifc_input", r"\bifc\b|input|tender|received from estimation|estimation"),
          ("shop_drawing", r"shop|\bsd\b|sdw|drawing|dwg|layout|plan"), ("other", None)]
BOQ_NAME = re.compile(r"design sheet|\bboq\b|bill of quant|\bdesign\.pdf$| design\.pdf$|design sheet", re.I)
WORD = (".doc", ".docx")


def stratum_of(rel: str, ext: str) -> str:
    low = rel.lower().replace("\\", "/")
    if ext in WORD:
        return "transmittal_word" if is_transmittal(rel.replace("\\", "/")) else "unsupported_word"
    if ext != ".pdf":
        return "unsupported"
    for name, rx in STRATA:
        if rx and re.search(rx, low):
            return name
    return "other"


def allocate(by: dict, quota: int) -> dict:
    strata = sorted(by, key=lambda k: (-len(by[k]), k))
    alloc = {k: 1 for k in strata}
    remaining = quota - len(strata)
    total = sum(len(by[k]) for k in strata) or 1
    for k in strata:
        alloc[k] += int(round(remaining * len(by[k]) / total))
    for k in strata:
        alloc[k] = min(alloc[k], len(by[k]), max(1, int(CAP_STRATUM * quota)))
    room = sorted(strata, key=lambda k: (len(by[k]), k))
    while sum(alloc.values()) < quota and any(alloc[k] < len(by[k]) for k in strata):
        for k in room:
            if sum(alloc.values()) >= quota:
                break
            if alloc[k] < len(by[k]):
                alloc[k] += 1
    while sum(alloc.values()) > quota:                        # rounding overshoot: trim the largest strata
        k = max(strata, key=lambda s: (alloc[s], s))
        alloc[k] -= 1
    return alloc


projects = []
for f in sorted(INV.glob("inventory-EP-*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    p = d["project"]
    assert "exploration" in p["cohort"]
    by = collections.defaultdict(list)
    unsupported = collections.Counter()
    boq = []
    for x in d["files"]:
        rel_key = (x["folder_name"] + "\\" + x["relative_path"]) if len(p["folders"]) > 1 else x["relative_path"]
        x = {**x, "doc_key": f"EP-{p['ep']}/" + rel_key.replace("\\", "/")}
        st = stratum_of(x["relative_path"], x["extension"])
        if st.startswith("unsupported"):
            unsupported[x["extension"] + ("" if st == "unsupported" else " (Word outside a transmittal folder)")] += 1
            continue
        by[st].append(x)
        if x["extension"] == ".pdf" and BOQ_NAME.search(pathlib.Path(x["relative_path"]).name):
            boq.append(x["doc_key"])
    projects.append({"ep": p["ep"], "contractor": p["contractor"], "folders": p["folders"], "by": by, "unsupported": unsupported, "boq": boq,
                     "eligible": sum(len(v) for v in by.values())})

# quotas (frozen plan: "no project exceeds 20 % of its cohort; small projects are inspected in full"): a project
# whose eligible count is within the 20 % cap is taken in full; the larger ones share the remainder equally, capped.
# (Draft 1 used an equal-share threshold that left three projects of 55-59 files short; superseded before staging.)
quota = {}
small = [q for q in projects if q["eligible"] <= CAP_PROJECT]
for q in small:
    quota[q["ep"]] = q["eligible"]
large = sorted([q for q in projects if q["eligible"] > CAP_PROJECT], key=lambda q: q["ep"])
share = (TARGET - sum(quota.values())) // max(1, len(large))
for q in large:
    quota[q["ep"]] = min(CAP_PROJECT, q["eligible"], share)
leftover = TARGET - sum(quota.values())
for q in sorted(projects, key=lambda q: -q["eligible"]):     # rounding remainder to the largest, within the cap
    while leftover > 0 and quota[q["ep"]] < min(CAP_PROJECT, q["eligible"]):
        quota[q["ep"]] += 1
        leftover -= 1

rng = random.Random(SEED)
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "seed": SEED, "target_distinct_documents": TARGET,
       "cap_per_project": CAP_PROJECT, "cap_per_stratum": CAP_STRATUM, "strata_rules": STRATA, "boq_name_rule": BOQ_NAME.pattern,
       "eligibility": "the frozen candidate's sync contract: .pdf, and .doc/.docx accepted by app.services.transmittals.is_transmittal",
       "content_read": "none: this selection is frozen from names and stat metadata before staging",
       "inventory": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(INV.glob("*.json"))},
       "projects": [], "documents": [], "replacements": [], "boq_candidates": []}
for q in sorted(projects, key=lambda q: q["ep"]):
    alloc = allocate(q["by"], quota[q["ep"]])
    for k in sorted(q["by"]):
        pool = sorted(q["by"][k], key=lambda x: x["doc_key"].lower())
        rng.shuffle(pool)
        for rank, x in enumerate(pool):
            rec = {"ep": q["ep"], "doc_key": x["doc_key"], "folder": x["folder"], "relative_path": x["relative_path"], "extension": x["extension"],
                   "size": x["size"], "mtime_ns": x["mtime_ns"], "path_length": x["path_length"], "placeholder_before": x["recall_on_data_access"],
                   "stratum": k, "rank_in_stratum": rank, "selection": f"seeded shuffle within stratum ({SEED}); rank {rank}"}
            (out["documents"] if rank < alloc.get(k, 0) else out["replacements"]).append(rec)
    out["projects"].append({"ep": q["ep"], "contractor": q["contractor"], "eligible": q["eligible"], "eligible_by_stratum": {k: len(v) for k, v in q["by"].items()},
                            "unsupported": dict(q["unsupported"].most_common()), "quota": quota[q["ep"]], "in_full": quota[q["ep"]] >= q["eligible"],
                            "allocation": alloc, "boq_name_candidates": len(q["boq"])})
    out["boq_candidates"] += [{"ep": q["ep"], "doc_key": k} for k in sorted(q["boq"])]
out["accounting"] = {"primary": len(out["documents"]), "replacements_available": len(out["replacements"]),
                     "by_project": {p["ep"]: p["quota"] for p in out["projects"]},
                     "by_stratum": dict(collections.Counter(d["stratum"] for d in out["documents"])),
                     "boq_name_candidates": len(out["boq_candidates"])}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(out["accounting"], indent=1))
for p in out["projects"]:
    print(p["ep"], "eligible", p["eligible"], "quota", p["quota"], "in_full" if p["in_full"] else "", "alloc", p["allocation"], "| boq-name", p["boq_name_candidates"])
print("selection sha256", hashlib.sha256(OUT.read_bytes()).hexdigest())
