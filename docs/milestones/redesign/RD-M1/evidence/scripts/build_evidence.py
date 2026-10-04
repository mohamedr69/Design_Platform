"""Write the RD-M1 package's evidence/, renders/, crops/ from the isolated work area.

Only derived, redacted data goes into the package: host names and Windows user
names are pseudonymised, the project's name is omitted, and no copied DB,
drawing or full baseline is packaged (they stay in the isolated area and are
referenced by SHA-256)."""
import glob
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
PKG = sys.argv[1]
CASE = os.path.join(ROOT, "work", "case")
EV = os.path.join(PKG, "evidence")
for d in ("evidence", "evidence/tests", "evidence/scripts", "renders", "crops"):
    os.makedirs(os.path.join(PKG, d), exist_ok=True)

# Built at run time from the data, so no user or host name is written in this file.
def _hosts():
    js = json.load(open(os.path.join(ROOT, "work", "case", "jobs.json"), encoding="utf-8"))
    seen = []
    for j in sorted(js, key=lambda j: j["id"]):
        h = (j.get("worker_id") or ":").split(":")[1]
        if h and h not in seen:
            seen.append(h)
    return {h: f"PC-{chr(65 + i)}" for i, h in enumerate(seen)}


SUBS = [
    (re.compile(r"OneDrive - <org>\\/\"]+", re.I), "OneDrive - <org>"),
    (re.compile(r"C:(\\\\|\\|/)+Users(\\\\|\\|/)+" + re.escape(os.environ.get("USERNAME", "")) + r"(?=[\\/])", re.I),
     "<PC-B user profile>"),
    (re.compile(r"C:(\\\\|\\|/)+Users(\\\\|\\|/)+[^\\/<\"]+", re.I), "<PC-A user profile>"),
] + [(re.compile(re.escape(h)), alias) for h, alias in _hosts().items()] + [
    (re.compile(r"[A-Z]{4,}-AL-[A-Z]{4,}---AI-PLATFORM"), "<sibling clone folder>")]


def red(text):
    if text is None:
        return None
    for pat, rep in SUBS:
        text = pat.sub(rep, text)
    return text


def redj(obj):
    return json.loads(red(json.dumps(obj, default=str)))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dump(name, obj):
    with open(os.path.join(EV, name), "w", encoding="utf-8", newline="\n") as f:
        json.dump(redj(obj), f, indent=1, ensure_ascii=False, default=str)


row = json.load(open(os.path.join(CASE, "project_redesign.json"), encoding="utf-8"))[0]
changes = row["changes"]
review = json.load(open(os.path.join(CASE, "project_drawing_reviews.json"), encoding="utf-8"))[0]
jobs = json.load(open(os.path.join(CASE, "jobs.json"), encoding="utf-8"))

# E01 the failed Apply script (redacted copy) + original hash
src_scr = os.path.join(ROOT, "src", "EP-30880", "redesign-work-1", "redesign.scr")
raw = open(src_scr, encoding="utf-8").read()
with open(os.path.join(EV, "E01-apply-script-job121.redacted.scr"), "w", encoding="utf-8", newline="\n") as f:
    f.write("; RD-M1 redacted copy. Original: GC-01 work-1/redesign.scr sha256 " + sha(src_scr) + "\n")
    f.write("; Only user-profile path prefixes are replaced; E01 line number = original script line + 2 (two header lines).\n")
    f.write(red(raw))

# E02 jobs
dump("E02-jobs-fa.json", [{
    "id": j["id"], "kind": j["kind"], "project_id": j["project_id"], "status": j["status"], "attempts": j["attempts"],
    "created_by_id": j["created_by_id"], "created_at_utc": j["created_at"], "started_at_utc": j["started_at"],
    "finished_at_utc": j["finished_at"], "worker": (j["worker_id"] or "").split(":")[1] if j.get("worker_id") else None,
    "params": j["params"], "result": j["result"], "error_head": "\n".join((j["error"] or "").splitlines()[:2]) or None,
} for j in jobs if j["project_id"] == 5])

# E03 redesign row summary
from collections import Counter  # noqa: E402
dump("E03-redesign-row.json", {
    "table": "project_redesign", "id": row["id"], "project_id": row["project_id"], "drawing_id": row["drawing_id"],
    "status": row["status"], "error": row["error"], "source_sha256": row["source_sha256"], "calls": row["calls"],
    "output_status": row["output_status"], "output_error_head": "\n".join((row["output_error"] or "").splitlines()[:2]),
    "output_path": row["output_path"], "output_relative": row["output_relative"], "output_at_utc": row["output_at"],
    "output_changes": row["output_changes"], "started_at_utc": row["started_at"], "finished_at_utc": row["finished_at"],
    "updated_at_utc": row["updated_at"], "changes": len(changes), "symbols": len(row["symbols"]),
    "status_by_source": Counter(f"{c.get('source') or 'review'}|{c['status']}" for c in changes),
    "change_keys_present": sorted(set().union(*[set(c) for c in changes])),
})

# E04 analysis (computed by analyse_changes.py)
shutil.copyfile(os.path.join(ROOT, "work", "changes-analysis.json"), os.path.join(EV, "E04-changes-analysis.json"))

# E05 stale library paths
dump("E05-library-paths.json", [{
    "id": c["id"], "status": c["status"], "moved": c.get("moved"), "edited": c.get("edited"), "code": c["interface"]["code"],
    "for": c["interface"]["for"], "library": c["insert"]["library"],
    "drawn_at_apply": c["status"] == "approved", "page": c["page"], "seen_model": c["insert"]["seen"],
} for c in changes if (c.get("insert") or {}).get("library")])

# E06 review-sourced changes
dump("E06-review-changes.json", [{
    k: c.get(k) for k in ("id", "status", "action", "page", "sheet", "floor", "room", "system", "device", "instruction",
                          "at", "box", "confidence", "note", "on_wall", "moved", "edited", "coordinated", "residual", "ai")
} | {"remove": c.get("remove"), "insert": {k: (c.get("insert") or {}).get(k) for k in
                                         ("symbol", "name", "block", "layer", "scale", "rotation", "page", "seen", "model", "facing")}
     if c.get("insert") else None, "candidates": [{k: x[k] for k in ("n", "handle", "name", "page", "erasable")} for x in c.get("candidates") or []]}
    for c in changes if c.get("source") != "interface"])

# E07 approved interface modules (drawn) + all interface module index
dump("E07-interface-changes.json", [{
    "id": c["id"], "status": c["status"], "page": c["page"], "sheet": c["sheet"], "floor": c["floor"], "error": c.get("error"),
    "code": c["interface"]["code"], "for": c["interface"]["for"], "anchor_model": c["interface"].get("anchor"),
    "at_page": c.get("at"), "on_wall": c.get("on_wall"), "moved": c.get("moved"), "coordinated": c.get("coordinated"),
    "seen_model": (c.get("insert") or {}).get("seen"), "rotation": (c.get("insert") or {}).get("rotation"),
} for c in changes if c.get("source") == "interface"])

# E08 AI variation, E09 AI usage
shutil.copyfile(os.path.join(ROOT, "work", "ai-variation.json"), os.path.join(EV, "E08-ai-variation.json"))
usage = json.load(open(os.path.join(CASE, "ai_usage_redesign.json"), encoding="utf-8"))
dump("E09-ai-usage-redesign.json", usage)

# E10/E11 wall layers
wl = json.load(open(os.path.join(ROOT, "work", "wall-layers.json")))
dump("E10-wall-index-layers.json", {k: v for k, v in wl.items()})
el = json.load(open(os.path.join(ROOT, "work", "effective-layers.json")))
dump("E11-effective-layers.json", el)

# E12 DB snapshot info
shutil.copyfile(os.path.join(ROOT, "hash", "DB-SNAPSHOT-INFO.json"), os.path.join(EV, "E12-db-snapshot-info.json"))

# E13 worker log excerpt
log = open(r"G:\dev (2)\dev\ifc-worker-g.stderr.log", encoding="utf-8", errors="replace").read()
with open(os.path.join(EV, "E13-ifc-worker-log.redacted.txt"), "w", encoding="utf-8", newline="\n") as f:
    f.write("# RD-M1 redacted copy of <outer repo>/ifc-worker-g.stderr.log as read at audit time; sha256 of the read bytes: "
            + hashlib.sha256(log.encode("utf-8")).hexdigest() + " (live log, still appended by the owner's worker)\n")
    f.write(red(log))

# E14 activity
import sqlite3, urllib.parse  # noqa: E402,E401
sys.path.insert(0, HERE)
from q import run  # noqa: E402
acts = run("SELECT id, user_id, at, action, summary, entity_type, entity_id FROM activity_events "
           "WHERE project_id=5 AND (action LIKE 'redesign%' OR action LIKE 'drawing_review%') ORDER BY id")
dump("E14-activity-redesign.json", acts)

# E15 sheet geometry
dump("E15-sheet-geometry.json", [{
    "index": s["index"], "name": s["name"], "title": s.get("title"), "floor": s.get("floor"), "kind": s.get("kind"),
    "plan_box_pt": s.get("plan"), "legend_box_pt": s.get("legend"), "geometry": s.get("geometry")}
    for s in review["sheets"]])

# E16 source binding (from the T0 baseline)
b = json.load(open(os.path.join(ROOT, "hash", "BASELINE-T0.json")))["groups"]["ep_platform_ignored_relevant"]
binding = {k.replace("backend/uploads/EP-30880/", "GC01:"): v for k, v in b.items()
           if "EP-30880" in k or "redesign/library" in k}
dump("E16-source-binding.json", {"note": "SHA-256/size/mtime_ns from the pre-audit baseline (T0). GC01: = the case's upload folder.",
                                 "review_source_sha256": review["source_sha256"], "redesign_source_sha256": row["source_sha256"],
                                 "review_pdf_path": review["pdf_path"], "files": binding})

# E17 render index (copied after rendering)
ri = json.load(open(os.path.join(ROOT, "work", "renders", "_render-index.json")))
for r in ri:
    dest = "renders" if "-sheet-" in r["id"] else "crops"
    for fn in r["files"]:
        shutil.copyfile(os.path.join(ROOT, "work", "renders", fn), os.path.join(PKG, dest, fn))
    r["folder"] = dest
dump("E17-render-index.json", ri)

# E18 offline reproduction of the Apply input
shutil.copyfile(os.path.join(ROOT, "work", "reproduce-apply-input.json"), os.path.join(EV, "E18-reproduce-apply-input.json"))

# tests + scripts
for p in glob.glob(os.path.join(ROOT, "work", "tests", "*.txt")):
    with open(os.path.join(EV, "tests", os.path.basename(p)), "w", encoding="utf-8", newline="\n") as f:
        f.write(red(open(p, encoding="utf-8", errors="replace").read()))
for p in glob.glob(os.path.join(HERE, "*.py")):
    with open(os.path.join(EV, "scripts", os.path.basename(p)), "w", encoding="utf-8", newline="\n") as f:
        f.write(red(open(p, encoding="utf-8").read()))
print("ok")
