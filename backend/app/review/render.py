"""The FA IFC drawing as the engineer sees it: every sheet plotted to one
PDF by AutoCAD (the Core Console the DWG converter already uses), so the
review looks at the plans exactly as they print -- devices in colour, room
names, the legend -- rather than at a reconstruction.

A drawing of twenty sheets plots in about six minutes; the PDF is kept by
the drawing file's hash, so a review run again, or a second one, does not
plot again.
"""
from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

from app.ifc import storage
from app.ifc.dxf import convert

TIMEOUT_S = 30 * 60


class RenderError(Exception):
    pass


def source_file(project, drawing) -> Path:
    """The file AutoCAD plots: the DWG kept beside the drawing's DXF, else
    the copy filed in the project folder, else the DXF itself."""
    dxf = storage.dxf_path(drawing)
    for candidate in (dxf.with_suffix(".dwg"), dxf.with_suffix(".DWG")):
        if candidate.is_file():
            return candidate
    if drawing.archive_path and project.source_folder_path:
        filed = Path(project.source_folder_path) / drawing.archive_path
        if filed.is_file():
            return filed
    if dxf.is_file():
        return dxf
    raise RenderError("The drawing's file is not on this PC: import the fire alarm IFC drawing again.")


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def folder(project) -> Path:
    return storage.uploads_root() / f"EP-{project.ep_number}" / "review"


def render(project, drawing) -> tuple[Path, str]:
    """(the PDF of every sheet, the source's hash), plotted once per file."""
    return render_file(project, source_file(project, drawing))


def render_file(project, src: Path) -> tuple[Path, str]:
    """Any drawing as a PDF of its sheets: a PDF is itself; a DWG or DXF is
    plotted by AutoCAD, once per file (kept by its hash)."""
    sha = _sha(src)
    if src.suffix.lower() == ".pdf":
        return src, sha
    # absolute: AutoCAD runs in its own working folder, where a relative path means nothing
    out = (folder(project) / f"{sha[:24]}.pdf").resolve()
    if out.is_file() and out.stat().st_size > 0:
        return out, sha
    converter = convert.find_converter()
    if converter is None or converter.kind != "accoreconsole":
        raise RenderError("Plotting the drawing needs AutoCAD (its Core Console) on the PC the IFC worker runs on.")
    work = out.parent / f"plot-{sha[:12]}"
    work.mkdir(parents=True, exist_ok=True)
    local = work / f"drawing{src.suffix.lower()}"
    local.write_bytes(src.read_bytes())
    target = work / "sheets.pdf"
    target.unlink(missing_ok=True)
    script = work / "plot.scr"
    # -EXPORT, PDF, All layouts, then the file name: each layout plots with
    # its own page setup. Plain LF line ends (see convert._with_accoreconsole).
    script.write_bytes("\n".join(["_.FILEDIA", "0", "_.CMDDIA", "0", "-EXPORT", "P", "A", f'"{target}"',
                                  "_.QUIT", "_Y", ""]).encode("utf-8"))
    try:
        p = subprocess.run([converter.path, "/i", str(local), "/s", str(script), "/l", "en-US"],
                           capture_output=True, timeout=TIMEOUT_S, cwd=str(work),
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise RenderError(f"AutoCAD did not finish plotting within {TIMEOUT_S // 60} minutes.") from exc
    if not target.is_file() or target.stat().st_size == 0:
        log = convert._tail(convert._decode(p.stdout) + convert._decode(p.stderr))
        raise RenderError(f"AutoCAD did not write the PDF. Its last words:\n{log}")
    target.replace(out)
    for leftover in work.iterdir():
        leftover.unlink(missing_ok=True)
    work.rmdir()
    return out, sha
