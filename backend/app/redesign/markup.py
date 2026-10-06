"""The draftsman's PDF of a prepared drawing (platform owner, 6 October 2026):
each floor's plan, plotted, with every change that will be drawn marked and
numbered where it was placed -- green ADD, red REMOVE, amber REPLACE, purple
an interface module, each new detector's coverage circle faint around it --
then the schedule of the same numbers (app.review.markup): action, device,
room, instruction and the piece of plan, for the draftsman to draw by.

Only what the copy of the drawing would carry (app.redesign.service._drawn):
the approved changes, and the review's proposed ones the orchestrator did
not reject.
"""
from __future__ import annotations

import pymupdf

from app.review import markup as M

COLOURS = {"add": (0.09, 0.64, 0.29), "remove": (0.86, 0.15, 0.15), "replace": (0.92, 0.55, 0.05)}
MODULE = (0.49, 0.13, 0.81)
_INK = (0.10, 0.13, 0.20)


def _where(c: dict) -> list[float] | None:
    return ((c.get("insert") or {}).get("page") or (c.get("remove") or {}).get("page") or c.get("at"))


def build(changes: list[dict], sheets: dict[int, dict], drawing: dict, project, pdf_path: str | None,
          interface: str = "interface") -> pymupdf.Document:
    by_page: dict[int, list[dict]] = {}
    for c in changes:
        if c.get("page", -1) >= 0:
            by_page.setdefault(c["page"], []).append(c)
    ordered = [c for page in sorted(by_page) for c in by_page[page]]
    doc = pymupdf.open()
    plot = None
    if pdf_path:
        try:
            plot = pymupdf.open(pdf_path)
        except Exception:  # noqa: BLE001 -- the schedule goes out without its plans rather than not at all
            plot = None
    title = f"EP-{project.ep_number} {project.project_name or ''}".strip()
    if plot is not None:
        for page in sorted(by_page):
            if not 0 <= page < plot.page_count:
                continue
            doc.insert_pdf(plot, from_page=page, to_page=page)
            out = doc[-1]
            size = max(out.rect.width, out.rect.height)
            r = size / 260
            sheet = sheets.get(page) or {}
            a = (sheet.get("geometry") or {}).get("a")
            for n, c in enumerate(by_page[page], 1):
                at = _where(c)
                if not at:
                    continue
                colour = MODULE if c.get("source") == interface else COLOURS.get(c["action"], _INK)
                reach = (c.get("coverage") or {}).get("radius")
                if reach and a and c.get("insert"):
                    out.draw_circle(at, reach / a, color=colour, width=0.6, dashes="[4 3] 0", stroke_opacity=0.6)
                out.draw_circle(at, r, color=colour, width=max(1.2, r / 4))
                out.insert_text((at[0] + r * 1.2, at[1] - r * 0.4), str(n), fontname="hebo", fontsize=r * 1.6, color=colour)
            out.insert_text((36, 40), f"{sheet.get('floor') or sheet.get('name') or ''} - prepared for the draftsman "
                                      f"({len(by_page[page])} changes, numbered as in the schedule)",
                            fontname="hebo", fontsize=size / 90, color=_INK)
            out.insert_text((36, 40 + size / 70), f"{drawing['filename']} {drawing['revision']} - {title} - green ADD, "
                                                  "red REMOVE, amber REPLACE, purple interface module; dashed: "
                                                  "the new detector's coverage",
                            fontname="helv", fontsize=size / 130, color=_INK)
    findings = [{"page": c["page"], "floor": c["floor"], "sheet": c["sheet"], "action": c["action"],
                 "device": c.get("device") or ((c.get("insert") or {}).get("name")),
                 "system_name": c.get("system_name") or "", "room": c.get("room") or "",
                 "instruction": c.get("instruction") or "", "issue": "", "box": c.get("box"), "mark": _where(c),
                 "decision": "accepted"} for c in ordered]
    schedule = M.build({"findings": findings, "drawing": drawing}, project, pdf_path,
                       footer="Drawings Preparation - for the draftsman")
    doc.insert_pdf(schedule)
    schedule.close()
    if plot is not None:
        plot.close()
    return doc
