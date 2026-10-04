"""Review 31 (R31-01): the projects and contractors USED by any M1 / M2 extraction, labelling, pilot or tuning stage, from
structured evidence of use -- not from every number that appears in a population inventory.

Sources (each recorded with what it contributed):
  S1 Round 2 selection: the 34 projects (exposed pilot + R5 holdout, exploration, sealed) and their contractor fields
  S2 Review 05 holdout selection: every EP it names (taken AND logged candidates, conservatively)
  S3 real-project pilot manifests: PROJECT-INVENTORY, FROZEN-SAMPLE, RUN-MANIFEST, FROZEN-BOQ-SET; M2-GOLDEN-MANIFEST
  S4 every SQLite database under C:/t (sandboxes, stages, dry runs, replays) and the live application database and its
     backups (read-only): projects.ep_number, and the contractor folder in projects.source_folder_path
  S5 narrative milestone documents (*.md under docs/milestones M1 / M2 and the reviewer roadmap folder) -- free-text EP
     mentions, EXCEPT the metadata-only candidate lists of Review 30 / 31 (review30/ and the Review 30+ sections of
     M2-REVIEW-RESPONSE.md), which name never-used projects as proposals
  S6 backend test trees (both): free-text EP mentions (fixtures of used documents)
  S4b / S7 a document path naming another EP number, in a processed / selected / staged document, exposes that project
EP numbers with fewer than 4 digits are document numbers, not projects, and are ignored."""
from __future__ import annotations

import json
import pathlib
import re
import sqlite3

ROOT_NAME = "SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects"
M2 = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2")
MILESTONES = M2.parent
REVIEWER = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
EPNUM = re.compile(r"\bEP[- ]?(\d{4,6})\b")
SEG = re.compile(re.escape(ROOT_NAME) + r"[\\/]+([^\\/\"'\n\r\t|]+)")


def _eps(text: str) -> set:
    return {m.group(1) for m in EPNUM.finditer(text)}


def build(extra_db_roots=(pathlib.Path("C:/t"),), live_dbs=None) -> dict:
    sources, eps, contractors = {}, set(), set()

    def add(name, e=(), c=()):
        e, c = set(e), {x.strip() for x in c if x and x.strip() and not EPNUM.search(x)}
        sources.setdefault(name, {"eps": set(), "contractors": set()})
        sources[name]["eps"] |= e
        sources[name]["contractors"] |= c
        eps.update(e)
        contractors.update(c)

    r2 = json.loads((M2 / "real-project-pilot/review06/evidence/round2/ROUND2-SELECTION.json").read_text(encoding="utf-8"))
    add("S1 round2 selection", [p["ep"] for p in r2["projects"]], [p.get("contractor") for p in r2["projects"]])
    add("S2 review05 holdout selection", _eps((M2 / "real-project-pilot/review05/holdout/SELECTION.json").read_text(encoding="utf-8")))
    for f in ("real-project-pilot/PROJECT-INVENTORY.json", "real-project-pilot/FROZEN-SAMPLE.json", "real-project-pilot/RUN-MANIFEST.json",
              "real-project-pilot/FROZEN-BOQ-SET.json", "M2-GOLDEN-MANIFEST.json"):
        t = (M2 / f).read_text(encoding="utf-8").replace("\\\\", "\\")
        add(f"S3 {f}", _eps(t), [m.group(1) for m in SEG.finditer(t)])
    # S7: document paths of every selected / staged document (exploration primary documents, staged manifests)
    ex = json.loads((M2 / "real-project-pilot/review13/evidence/manifest/EXPLORATION-SELECTION.json").read_text(encoding="utf-8"))
    add("S7 exploration primary document paths", {e for d in ex.get("documents", []) for e in _eps(str(d.get("doc_key", "")) + " " + str(d.get("relative_path", "")))})
    for f in [pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json")] + list(pathlib.Path("C:/t/r2x").glob("*-stage/*.json")) + list(pathlib.Path("C:/t/r2x/stage").glob("*.json")):
        if f.exists():
            add("S7 staged manifests", _eps(f.read_text(encoding="utf-8", errors="ignore")))
    # S8 (fail closed): an EP named by ANY document path inside a used project's folder (exploration inventories and the
    # replacement list -- read or not) is cross-project material a within-project run could read: treated as used
    add("S8 exploration replacement paths", {e for d in ex.get("replacements", []) for e in _eps(str(d.get("doc_key", "")) + " " + str(d.get("relative_path", "")))})
    for f in pathlib.Path("C:/t/iso/work/r2x/inventory").glob("inventory-EP-*.json"):
        t = f.read_text(encoding="utf-8", errors="ignore")
        add("S8 used-project inventories", {e for m in re.finditer(r'"relative_path":\s*"([^"]*)"', t) for e in _eps(m.group(1))})
    dbs = [p for root in extra_db_roots for p in root.rglob("*.db")] + list(live_dbs or [])
    n_db = 0
    for db in dbs:
        try:
            con = sqlite3.connect(f"file:{pathlib.Path(db).as_posix()}?mode=ro", uri=True)
            rows = con.execute("select ep_number, source_folder_path from projects").fetchall()
            try:
                doc_paths = [r[0] for r in con.execute("select relative_path from project_documents") if r[0]]
            except sqlite3.Error:
                doc_paths = []
            con.close()
        except sqlite3.Error:
            continue
        # S4b: a document the application processed whose path names another EP number exposes that project too
        add("S4b sqlite document paths", {e for d in doc_paths for e in _eps(str(d))})
        n_db += 1
        add("S4 sqlite projects", [str(r[0]) for r in rows if r[0] and str(r[0]).isdigit() and len(str(r[0])) >= 4],
            [m.group(1) for r in rows if r[1] for m in SEG.finditer(str(r[1]))])
    for p in list(MILESTONES.rglob("*.md")) + list(REVIEWER.rglob("*.md")):
        if "review30" in p.parts or "review31" in p.parts:
            continue
        t = p.read_text(encoding="utf-8", errors="ignore")
        if p.name == "M2-REVIEW-RESPONSE.md":
            t = t.split("# Response to Independent M2 Review 30")[0]
        add("S5 milestone narratives", _eps(t))
    for root in (pathlib.Path("C:/t/iso/cand-r29/backend/tests"), pathlib.Path("C:/t/iso/frozen-r12/backend/tests")):
        for p in root.rglob("*.py"):
            add("S6 backend tests", _eps(p.read_text(encoding="utf-8", errors="ignore")))
    return {"eps": eps, "contractor_names": contractors, "databases_read": n_db,
            "sources": {k: {"eps": len(v["eps"]), "contractors": len(v["contractors"])} for k, v in sources.items()},
            "per_source": {k: {"eps": sorted(v["eps"], key=int), "contractors": sorted(v["contractors"])} for k, v in sources.items()}}
