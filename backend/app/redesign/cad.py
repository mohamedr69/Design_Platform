"""The changes made on a copy of the IFC drawing, by AutoCAD itself.

The copy is the DWG the review plotted, opened in the Core Console and
edited with AutoLISP, then saved: the drawing keeps everything it had --
xrefs, layouts, plot styles -- and gains only the changes.

  REMOVE   the symbol is erased by its handle (only a symbol drawn directly
           in model space: erasing one inside a block would take it out of
           every copy of that block), and a red marker left where it was;
  ADD      the drawing's own block inserted at the point, on the layer the
           drawing keeps that block on, at the scale its other copies have,
           with a green marker;
  REPLACE  both, at the old symbol's place, with an orange marker.

A change with no symbol to insert, or a symbol that cannot be erased, is a
marker and a note only -- the draftsman's to draw.

What the smoke test on EP-30880 settled (2 October 2026): the drawing opens
on a sheet layout, so TILEMODE 1 first or everything lands in paper space;
-INSERT multiplies the scale by the block's unit conversion (INSUNITS 0 is
not enough: each block brings its own), so each insert is made once at 1 to
learn the factor, then at the scale wanted divided by it; -INSERT "_S" scale first works for every block, uniform or
not; ATTREQ 0 keeps the attributes at their defaults.
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path

from app.ifc.dxf import convert

TIMEOUT_S = 1200
LAYERS = {"add": ("EP-REDESIGN-ADD", 3), "remove": ("EP-REDESIGN-REMOVE", 1), "replace": ("EP-REDESIGN-REPLACE", 30)}
LABEL = {"add": "ADD", "remove": "REMOVE", "replace": "REPLACE"}


class CadError(RuntimeError):
    pass


def _q(text: str) -> str:
    """A LISP string literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _n(value: float) -> str:
    return f"{float(value):.6f}"


def script_lines(changes: list[dict], marker: float, text_height: float) -> list[str]:
    """The AutoLISP for the changes. `changes`: {action, remove_handle,
    insert: {block, layer, scale, rotation, model: [x, y]} or None, at:
    [x, y] (where the marker goes), label}."""
    lines = ["_.FILEDIA", "0", "_.CMDDIA", "0",
             '(setvar "TILEMODE" 1)', '(setvar "CMDECHO" 0)', '(setvar "ATTREQ" 0)', '(setvar "ATTDIA" 0)',
             '(setvar "OSMODE" 0)', '(setq ep_layer (getvar "CLAYER"))', '(setq ep_units (getvar "INSUNITS"))']
    for name, colour in LAYERS.values():
        lines.append(f'(if (not (tblsearch "LAYER" {_q(name)})) (entmake (list (cons 0 "LAYER") '
                     f'(cons 100 "AcDbSymbolTableRecord") (cons 100 "AcDbLayerTableRecord") (cons 2 {_q(name)}) '
                     f'(cons 70 0) (cons 62 {colour}) (cons 6 "Continuous"))))')
    lines.append('(setvar "INSUNITS" 0)')
    # new blocks (a weatherproof emergency light: the drawing's own with "WP"
    # under it): a copy of the block's entities, the letters, on layer 0 by block
    made = set()
    for change in changes:
        make = (change.get("insert") or {}).get("make")
        if not make or change["insert"]["block"] in made:
            continue
        made.add(change["insert"]["block"])
        if len(made) == 1:
            lines.append("(defun ep_copy (src new / e d out) (setq ep_txt nil) "
                         "(if (and (tblsearch \"BLOCK\" src) (not (tblsearch \"BLOCK\" new))) "
                         "(progn (setq d (entget (tblobjname \"BLOCK\" src))) "
                         "(entmake (list (cons 0 \"BLOCK\") (cons 2 new) (cons 70 0) (cons 10 (cdr (assoc 10 d))))) "
                         "(setq e (entnext (tblobjname \"BLOCK\" src))) "
                         "(while (and e (/= (cdr (assoc 0 (setq d (entget e)))) \"ENDBLK\")) (setq out nil) "
                         "(foreach p d (if (not (member (car p) (quote (-1 5 102 330 360)))) (setq out (cons p out)))) "
                         "(if (and (not ep_txt) (= (cdr (assoc 0 d)) \"TEXT\")) (setq ep_txt d)) "
                         "(entmake (reverse out)) (setq e (entnext e))) T)))")
        x, y = make["at"]
        new = _q(change["insert"]["block"])
        lines.append(f'(if (ep_copy {_q(make["from"])} {new}) (progn '
                     # the letters as the block's own letter ("E"): its layer, colour and style
                     f'(entmake (list (cons 0 "TEXT") (cons 8 (if ep_txt (cdr (assoc 8 ep_txt)) "0")) '
                     f'(cons 62 (if (and ep_txt (assoc 62 ep_txt)) (cdr (assoc 62 ep_txt)) 0)) '
                     f'(cons 7 (if ep_txt (cdr (assoc 7 ep_txt)) "Standard")) (list 10 {_n(x)} {_n(y)} 0.0) '
                     f'(list 11 {_n(x)} {_n(y)} 0.0) (cons 40 {_n(make["height"])}) (cons 1 {_q(make["text"])}) '
                     f'(cons 72 1) (cons 73 0))) (entmake (list (cons 0 "ENDBLK")))))')
    # markers close together: their labels one under the other, not on top of each other
    rows: list[tuple[float, float]] = []
    lifts = []
    for change in changes:
        mx, my = change["at"]
        n = sum(1 for (x, y) in rows if abs(x - mx) < 12 * text_height and abs(y - my) < 3 * text_height)
        rows.append((mx, my))
        lifts.append(n)
    for change, lift in zip(changes, lifts):
        action = change["action"]
        if change.get("remove_handle"):
            h = _q(change["remove_handle"])
            lines.append(f"(if (handent {h}) (entdel (handent {h})))")
        insert = change.get("insert")
        if insert:
            x, y = insert["model"]
            if insert.get("layer"):
                lines.append(f'(if (tblsearch "LAYER" {_q(insert["layer"])}) (setvar "CLAYER" {_q(insert["layer"])}))')
            # AutoCAD scales an insert by the block's own units (by 1/25.4 for
            # one, by 39.37 for another): inserted once at 1 to learn that
            # factor, then again at the scale wanted divided by it.
            point, rot = f"(list {_n(x)} {_n(y)} 0.0)", _n(insert.get("rotation") or 0)
            name = _q(insert["block"])
            if insert.get("library"):
                # a block of the platform's library (the interface modules), brought in
                # from its file only where the drawing has none of the name: once
                name = f'(if (tblsearch "BLOCK" {name}) {name} {_q(insert["block"] + "=" + insert["library"])})'
            lines.append(f'(command "_.-INSERT" {name} "_S" 1.0 {point} {rot})')
            lines.append('(setq ep_f (cdr (assoc 41 (entget (entlast)))))')
            lines.append("(entdel (entlast))")
            lines.append(f'(command "_.-INSERT" {_q(insert["block"])} "_S" (/ {_n(insert["scale"])} ep_f) {point} {rot})')
            lines.append('(setvar "CLAYER" ep_layer)')
        note = change.get("note")
        if note:
            nx, ny = note["at"]
            # rotation in radians, as AutoLISP has it; right-aligned on its point when it runs back to it
            turn = f"(cons 50 {_n(math.radians(note.get('rotation') or 0))}) "
            align = (f"(cons 72 2) (list 11 {_n(nx)} {_n(ny)} 0.0) " if note.get("align") == "right" else "")
            lines.append(f"(entmake (list (cons 0 \"TEXT\") (cons 8 {_q(note['layer'])}) (list 10 {_n(nx)} {_n(ny)} 0.0) "
                         f"(cons 40 {_n(note['height'])}) {turn}{align}(cons 1 {_q(note['text'][:60])})))")
        layer, colour = LAYERS[action]
        mx, my = change["at"]
        lines.append(f"(entmake (list (cons 0 \"CIRCLE\") (cons 8 {_q(layer)}) (list 10 {_n(mx)} {_n(my)} 0.0) "
                     f"(cons 40 {_n(marker)}) (cons 62 {colour})))")
        ty = my + marker * 0.6 - lift * text_height * 1.8
        lines.append(f"(entmake (list (cons 0 \"TEXT\") (cons 8 {_q(layer)}) (list 10 {_n(mx + marker * 1.1)} "
                     f"{_n(ty)} 0.0) (cons 40 {_n(text_height)}) (cons 1 {_q(change['label'][:120])}) "
                     f"(cons 62 {colour})))")
    lines += ['(setvar "INSUNITS" ep_units)', '(setvar "CLAYER" ep_layer)', "_.QSAVE", "_.QUIT", "_Y", ""]
    return lines


def apply(source: Path, out: Path, changes: list[dict], marker: float, text_height: float, work: Path) -> str:
    """Copy `source`, make the changes on the copy, save it as `out`.
    Returns AutoCAD's log. Raises CadError when AutoCAD is not here or did
    not save."""
    converter = convert.find_converter()
    if converter is None or converter.kind != "accoreconsole":
        raise CadError("Making the redesigned drawing needs AutoCAD (its Core Console) on the PC the IFC worker runs on.")
    work = work.resolve()
    work.mkdir(parents=True, exist_ok=True)
    copy = work / f"redesign{source.suffix.lower()}"
    shutil.copyfile(source, copy)
    before = copy.stat().st_mtime
    script = work / "redesign.scr"
    # Plain LF line ends, as bytes (see convert._with_accoreconsole).
    script.write_bytes("\n".join(script_lines(changes, marker, text_height)).encode("utf-8"))
    try:
        proc = subprocess.run([converter.path, "/i", str(copy), "/s", str(script), "/l", "en-US"],
                              capture_output=True, timeout=TIMEOUT_S, cwd=str(work),
                              creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except subprocess.TimeoutExpired as exc:
        raise CadError(f"AutoCAD did not finish within {TIMEOUT_S // 60} minutes.") from exc
    log = convert._decode(proc.stdout) + convert._decode(proc.stderr)
    if copy.suffix.lower() == ".dxf":
        raise CadError("The drawing's DWG is not on this PC: import the fire alarm IFC drawing again.")
    if not copy.is_file() or copy.stat().st_mtime <= before:
        raise CadError(f"AutoCAD did not save the redesigned drawing. Its last words:\n{convert._tail(log)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(copy, out)
    for leftover in work.iterdir():
        try:
            leftover.unlink()
        except OSError:
            pass
    return log
