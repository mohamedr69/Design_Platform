"""Dump the Redesign case records from the audit snapshot into the isolated work area (query-only)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from q import run  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "..", "work", "case")
os.makedirs(OUT, exist_ok=True)


def dump(name, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=1, default=str)


def loads(rows, *cols):
    for r in rows:
        for c in cols:
            if isinstance(r.get(c), str):
                try:
                    r[c] = json.loads(r[c])
                except ValueError:
                    pass
    return rows


dump("project_redesign.json", loads(run("SELECT * FROM project_redesign"), "changes", "symbols"))
dump("project_drawing_reviews.json", loads(run("SELECT * FROM project_drawing_reviews"), *[
    r["name"] for r in run("PRAGMA table_info(project_drawing_reviews)") if r["type"] == "JSON"]))
dump("project_ifc_drawings.json", loads(run("SELECT * FROM project_ifc_drawings WHERE project_id=5"), *[
    r["name"] for r in run("PRAGMA table_info(project_ifc_drawings)") if r["type"] == "JSON"]))
dump("project_fa_interfaces.json", loads(run("SELECT * FROM project_fa_interfaces"), *[
    r["name"] for r in run("PRAGMA table_info(project_fa_interfaces)") if r["type"] == "JSON"]))
dump("project.json", run("SELECT id, ep_number, status, ai_policy, source_folder_path IS NOT NULL AS has_folder FROM projects"))
dump("jobs.json", loads(run("SELECT * FROM background_jobs WHERE kind LIKE 'fa_%' ORDER BY id"), "progress", "result", "detail", "params"))
dump("ai_usage_redesign.json", run("SELECT * FROM ai_usage WHERE task LIKE '%redesign%' ORDER BY id"))
print(sorted(os.listdir(OUT)))
