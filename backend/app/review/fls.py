"""The FLS (fire & life safety) drawings, for the Drawings Review: the
escape routes and exits the consultant set out, that the IFC drawing's exit
and directional signs have to follow.

Read from the project folder's 03- Drawings/IFC/FLS (PDF, or DWG / DXF
plotted the same way the IFC drawing is). Each page is the floor its title
names; each IFC floor plan is reviewed beside the FLS page of the same floor
-- the floors matched the way every other part of the platform matches
them (drawing_log.floor_identity), so "GROUND FLOOR" and "GF" are one.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

import pymupdf

from app.ifc.dxf import sheets as S
from app.services import document_control, drawing_log

FOLDER = "03- Drawings/IFC/FLS"
SUFFIXES = (".pdf", ".dwg", ".dxf")
_TITLE = re.compile(r"FLOOR|LEVEL|BASEMENT|ROOF|PODIUM|MEZZ|GROUND|TYP", re.I)


def files(project) -> list[Path]:
    """The FLS drawings filed for the project (a later revision of the same
    drawing stands for it: the newest file of each name)."""
    if not project.source_folder_path:
        return []
    root = Path(project.source_folder_path) / FOLDER
    found: dict[str, tuple[float, Path]] = {}
    for dirpath, _dirs, names in os.walk(document_control._os_path(root)):
        for name in names:
            if not name.lower().endswith(SUFFIXES) or name.startswith("~$"):
                continue
            path = Path(dirpath) / name
            try:
                mtime = os.stat(path).st_mtime
            except OSError:
                continue
            stem = re.sub(r"[\s_-]*(\(.*\)|R(?:EV)?\.?\s*\d+)\s*$", "", path.stem, flags=re.I).upper()
            if stem not in found or mtime > found[stem][0]:
                found[stem] = (mtime, path)
    return sorted((p for _m, p in found.values()), key=lambda p: p.name.lower())


def keys(title: str) -> set[str]:
    """The floors a title names, as the platform keys them."""
    floor = S.identify_floor(title or "")
    return set(drawing_log.floor_identity(floor, title)) if floor else set()


def page_floors(doc: pymupdf.Document) -> list[dict]:
    """Each page of an FLS PDF with the floor its title names: the title-like
    lines in the title panel (the right of the page) first, then anywhere."""
    out = []
    for index in range(doc.page_count):
        page = doc[index]
        width = page.rect.width
        lines = []
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines", []):
                text = " ".join(" ".join(span["text"] for span in line["spans"]).split())
                if text and _TITLE.search(text) and len(text) <= 80:
                    size = max((span["size"] for span in line["spans"]), default=0)
                    lines.append((line["bbox"][0] > width * 0.7, size, text))
        # the title panel's lines first, the larger first
        lines.sort(key=lambda l: (not l[0], -l[1]))
        title, found = "", set()
        for _panel, _size, text in lines:
            found = keys(text)
            if found:
                title = text
                break
        out.append({"page": index, "title": title, "keys": sorted(found)})
    return out
