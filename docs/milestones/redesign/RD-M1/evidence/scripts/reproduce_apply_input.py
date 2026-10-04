"""Offline reproduction of the Apply input (stages 14, 18, 20, 21) from the snapshot's stored plan.

Runs the ISOLATED CODE COPY with an in-memory database, AI off and temporary
roots, so nothing can reach the live DB, uploads or a model. No AutoCAD.
  1. coordinate() on a deep copy of the stored changes, with the copied wall
     index -> is the stored plan a fixed point of coordination?
  2. _drawn() + to_cad() + cad.script_lines(marker=0.6, text=0.25 [units m])
     -> compare with the preserved work-1/redesign.scr byte for byte.
"""
import copy
import hashlib
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
os.environ.update({"DATABASE_URL": "sqlite:///:memory:", "AI_ENABLED": "false", "PROJECTS_ROOT": "",
                   "PROJECTS_ROOT_AUTODETECT": "false", "UPLOADS_ROOT": tempfile.mkdtemp(prefix="rdm1-up-"),
                   "CACHE_ROOT": tempfile.mkdtemp(prefix="rdm1-cache-"), "LIBRARY_ROOT": tempfile.mkdtemp(prefix="rdm1-lib-"),
                   "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
                   "ARCHIVE_DATASHEET_LIBRARIES": "{}", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_SUBMITTAL_LIBRARY": ""})
sys.path.insert(0, os.path.join(ROOT, "code", "backend"))

from app.core.config import get_settings  # noqa: E402

s = get_settings()
assert s.database_url == "sqlite:///:memory:", s.database_url
assert not s.ai_enabled
from app.redesign import cad  # noqa: E402
from app.redesign import service as R  # noqa: E402
from app.redesign import walls as W  # noqa: E402

case = os.path.join(ROOT, "work", "case")
row = json.load(open(os.path.join(case, "project_redesign.json"), encoding="utf-8"))[0]
sheets = {sh["index"]: sh for sh in json.load(open(os.path.join(case, "project_drawing_reviews.json"), encoding="utf-8"))[0]["sheets"]}
walls = W.load(__import__("pathlib").Path(os.path.join(ROOT, "src", "EP-30880", "walls.pkl")))
assert walls is not None

out = {"code_root": "isolated copy", "db": s.database_url}
stored = row["changes"]
again = copy.deepcopy(stored)
moved = R.coordinate(again, sheets, walls, row["symbols"])
diff = []
for a, b in zip(stored, again):
    if (a.get("insert") or {}).get("seen") != (b.get("insert") or {}).get("seen"):
        diff.append({"id": a["id"], "stored": a["insert"]["seen"], "recomputed": b["insert"]["seen"]})
out["coordinate_touched"] = moved
out["coordinate_seen_differences"] = diff

todo = [c for c in stored if R._drawn(c)]
lines = cad.script_lines(R.to_cad(todo), marker=0.6 * 1.0, text_height=0.25 * 1.0)
regen = "\n".join(lines).encode("utf-8")
preserved = open(os.path.join(ROOT, "src", "EP-30880", "redesign-work-1", "redesign.scr"), "rb").read()
out["drawn_changes"] = len(todo)
out["regenerated_sha256"] = hashlib.sha256(regen).hexdigest()
out["preserved_sha256"] = hashlib.sha256(preserved).hexdigest()
out["byte_identical"] = regen == preserved
if not out["byte_identical"]:
    rl, pl = regen.decode().splitlines(), preserved.decode().splitlines()
    out["first_difference"] = next(({"line": i + 1, "regen": x[:200], "preserved": y[:200]}
                                    for i, (x, y) in enumerate(zip(rl, pl)) if x != y), {"lengths": [len(rl), len(pl)]})
json.dump(out, open(os.path.join(ROOT, "work", "reproduce-apply-input.json"), "w"), indent=1)
print(json.dumps(out, indent=1)[:3000])
