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

Fail closed (RD-M2, 3 October 2026). A script line that errors only ends
that line -- the Core Console reads on -- so every step is its own line,
guarded by `ep_failed`, and checked by the next one:
  * an insert is good only when (entlast) is a NEW INSERT of the expected
    block; only that entity is measured and erased again -- never an
    unknown one (RD-M1 F004);
  * an erase is made only on an INSERT of the expected block, in model
    space, at the expected insertion point;
  * markers and notes must be made (entmake returns the list);
  * QSAVE runs only when nothing failed and every insert and erase was
    counted; otherwise nothing is saved.
The outcome is printed as markers built at run time with (strcat ...), so
the Core Console's echo of the script itself can never read as an outcome:
  EP-RD-FAIL:<nonce>:<step>:<change>    a step that failed
  EP-RD-OK:<nonce>:<inserts>:<erases>   saved, with what was counted
  EP-RD-NOSAVE:<nonce>                  not saved
"""
from __future__ import annotations

import math
import secrets
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.ifc.dxf import convert

TIMEOUT_S = 1200
POLL_S = 1.0
LAYERS = {"add": ("EP-REDESIGN-ADD", 3), "remove": ("EP-REDESIGN-REMOVE", 1), "replace": ("EP-REDESIGN-REPLACE", 30)}
LABEL = {"add": "ADD", "remove": "REMOVE", "replace": "REPLACE"}
# An erased symbol must be within this of the insertion point the reading found, in drawing units.
ERASE_TOLERANCE = 0.01
MARK = "EP-RD"


class CadError(RuntimeError):
    pass


def _q(text: str) -> str:
    """A LISP string literal."""
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _n(value: float) -> str:
    return f"{float(value):.6f}"


def _marker(kind: str, *rest: str) -> str:
    """LISP that prints EP-RD-<kind>:<rest...> built at run time: the
    script's own text never contains the joined marker."""
    parts = " ".join(rest)
    return f'(princ (strcat "\\n" "{MARK}" "-{kind}:" {parts} "\\n"))'


def expected_counts(changes: list[dict]) -> tuple[int, int]:
    """(inserts, erases) the script must count before it saves."""
    return (sum(1 for c in changes if c.get("insert")), sum(1 for c in changes if c.get("remove_handle")))


def script_lines(changes: list[dict], marker: float, text_height: float, nonce: str = "0") -> list[str]:
    """The AutoLISP for the changes. `changes`: {id, action, remove_handle,
    remove_block, remove_point, insert: {block, layer, scale, rotation,
    model: [x, y], library} or None, at: [x, y] (where the marker goes),
    label, note}."""
    n_ins, n_del = expected_counts(changes)
    lines = ["_.FILEDIA", "0", "_.CMDDIA", "0",
             '(setvar "TILEMODE" 1)', '(setvar "CMDECHO" 0)', '(setvar "ATTREQ" 0)', '(setvar "ATTDIA" 0)',
             '(setvar "OSMODE" 0)', '(setq ep_layer (getvar "CLAYER"))', '(setq ep_units (getvar "INSUNITS"))',
             f"(setq ep_nonce {_q(nonce)} ep_failed nil ep_saved nil ep_ins 0 ep_del 0)",
             f'(defun ep_fail (what id) (setq ep_failed T) {_marker("FAIL", "ep_nonce", chr(34) + ":" + chr(34), "what", chr(34) + ":" + chr(34), "id")} (princ))',
             # the newest entity, when it is a new INSERT of the block; else the step fails
             "(defun ep_new_insert (before blk id / e d) (setq e (entlast)) "
             "(if (and e (not (eq e before)) (setq d (entget e)) (= (cdr (assoc 0 d)) \"INSERT\") "
             "(= (strcase (cdr (assoc 2 d))) (strcase blk))) e (progn (ep_fail \"insert\" id) nil)))",
             # an erase only of the expected symbol: an INSERT of the block, in model space, where it was read
             "(defun ep_erase (h blk x y tol id / e d p) (setq e (handent h)) "
             "(if (and e (setq d (entget e)) (= (cdr (assoc 0 d)) \"INSERT\") "
             "(or (not blk) (= (strcase (cdr (assoc 2 d))) (strcase blk))) "
             "(/= (cdr (assoc 67 d)) 1) (= (strcase (cond ((cdr (assoc 410 d))) (\"MODEL\"))) \"MODEL\") "
             "(or (not x) (and (setq p (cdr (assoc 10 d))) (< (distance (list x y) (list (car p) (cadr p))) tol)))) "
             "(progn (entdel e) (if (entget e) (ep_fail \"erase-verify\" id) (setq ep_del (1+ ep_del)))) "
             "(ep_fail \"erase-target\" id)))",
             "(defun ep_make (lst id) (if (not (entmake lst)) (ep_fail \"entmake\" id)))"]
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
        lines.append(f'(if (not ep_failed) (if (ep_copy {_q(make["from"])} {new}) (progn '
                     # the letters as the block's own letter ("E"): its layer, colour and style
                     f'(entmake (list (cons 0 "TEXT") (cons 8 (if ep_txt (cdr (assoc 8 ep_txt)) "0")) '
                     f'(cons 62 (if (and ep_txt (assoc 62 ep_txt)) (cdr (assoc 62 ep_txt)) 0)) '
                     f'(cons 7 (if ep_txt (cdr (assoc 7 ep_txt)) "Standard")) (list 10 {_n(x)} {_n(y)} 0.0) '
                     f'(list 11 {_n(x)} {_n(y)} 0.0) (cons 40 {_n(make["height"])}) (cons 1 {_q(make["text"])}) '
                     f'(cons 72 1) (cons 73 0))) (entmake (list (cons 0 "ENDBLK"))))))')
    # markers close together: their labels one under the other, not on top of each other
    rows: list[tuple[float, float]] = []
    lifts = []
    for change in changes:
        mx, my = change["at"]
        n = sum(1 for (x, y) in rows if abs(x - mx) < 12 * text_height and abs(y - my) < 3 * text_height)
        rows.append((mx, my))
        lifts.append(n)
    for k, (change, lift) in enumerate(zip(changes, lifts)):
        action = change["action"]
        cid = _q(change.get("id") or f"#{k + 1}")
        if change.get("remove_handle"):
            point = change.get("remove_point")
            px, py = (_n(point[0]), _n(point[1])) if point else ("nil", "nil")
            blk = _q(change["remove_block"]) if change.get("remove_block") else "nil"
            lines.append(f"(if (not ep_failed) (ep_erase {_q(change['remove_handle'])} {blk} {px} {py} "
                         f"{_n(ERASE_TOLERANCE)} {cid}))")
        insert = change.get("insert")
        if insert:
            x, y = insert["model"]
            block = _q(insert["block"])
            point, rot = f"(list {_n(x)} {_n(y)} 0.0)", _n(insert.get("rotation") or 0)
            name = block
            if insert.get("library"):
                # a block of the platform's library (the interface modules), brought in
                # from its file only where the drawing has none of the name: once
                name = f'(if (tblsearch "BLOCK" {block}) {block} {_q(insert["block"] + "=" + insert["library"])})'
            layer = (f'(if (tblsearch "LAYER" {_q(insert["layer"])}) (setvar "CLAYER" {_q(insert["layer"])}))'
                     if insert.get("layer") else "")
            lines.append(f"(if (not ep_failed) (progn (setq ep_b (entlast)) {layer}))")
            # AutoCAD scales an insert by the block's own units (by 1/25.4 for
            # one, by 39.37 for another): inserted once at 1 to learn that
            # factor -- that new insert, checked, is measured and erased again --
            # then at the scale wanted divided by it, checked again.
            lines.append(f'(if (not ep_failed) (command "_.-INSERT" {name} "_S" 1.0 {point} {rot}))')
            lines.append(f"(if (not ep_failed) (if (setq ep_e (ep_new_insert ep_b {block} {cid})) "
                         "(progn (setq ep_f (cdr (assoc 41 (entget ep_e)))) (entdel ep_e) (setq ep_b (entlast)))))")
            lines.append(f'(if (not ep_failed) (command "_.-INSERT" {block} "_S" (/ {_n(insert["scale"])} ep_f) {point} {rot}))')
            lines.append(f"(if (not ep_failed) (if (ep_new_insert ep_b {block} {cid}) (setq ep_ins (1+ ep_ins))))")
            lines.append('(setvar "CLAYER" ep_layer)')
        note = change.get("note")
        if note:
            nx, ny = note["at"]
            # rotation in radians, as AutoLISP has it; right-aligned on its point when it runs back to it
            turn = f"(cons 50 {_n(math.radians(note.get('rotation') or 0))}) "
            align = (f"(cons 72 2) (list 11 {_n(nx)} {_n(ny)} 0.0) " if note.get("align") == "right" else "")
            lines.append(f"(if (not ep_failed) (ep_make (list (cons 0 \"TEXT\") (cons 8 {_q(note['layer'])}) "
                         f"(list 10 {_n(nx)} {_n(ny)} 0.0) (cons 40 {_n(note['height'])}) {turn}{align}"
                         f"(cons 1 {_q(note['text'][:60])})) {cid}))")
        layer, colour = LAYERS[action]
        mx, my = change["at"]
        lines.append(f"(if (not ep_failed) (ep_make (list (cons 0 \"CIRCLE\") (cons 8 {_q(layer)}) "
                     f"(list 10 {_n(mx)} {_n(my)} 0.0) (cons 40 {_n(marker)}) (cons 62 {colour})) {cid}))")
        ty = my + marker * 0.6 - lift * text_height * 1.8
        lines.append(f"(if (not ep_failed) (ep_make (list (cons 0 \"TEXT\") (cons 8 {_q(layer)}) "
                     f"(list 10 {_n(mx + marker * 1.1)} {_n(ty)} 0.0) (cons 40 {_n(text_height)}) "
                     f"(cons 1 {_q(change['label'][:120])}) (cons 62 {colour})) {cid}))")
    lines += ['(setvar "INSUNITS" ep_units)', '(setvar "CLAYER" ep_layer)',
              # saved only when nothing failed and every insert and erase was counted
              f'(if (and (not ep_failed) (or (/= ep_ins {n_ins}) (/= ep_del {n_del}))) (ep_fail "count" "all"))',
              '(if (not ep_failed) (progn (command "_.QSAVE") (setq ep_saved T)))',
              "(if ep_saved " + _marker("OK", "ep_nonce", chr(34) + ":" + chr(34), "(itoa ep_ins)", chr(34) + ":" + chr(34),
                                        "(itoa ep_del)")
              + " " + _marker("NOSAVE", "ep_nonce") + ")",
              # not saved: QUIT discards the copy's changes; saved: nothing is left to ask
              "_.QUIT", "_Y", ""]
    return lines


@dataclass
class CadRun:
    """One AutoCAD run on the copy in `work`."""
    work: Path
    copy: Path
    script: Path
    log_path: Path
    log: str
    nonce: str
    returncode: int | None
    expected_inserts: int
    expected_erases: int
    seconds: float
    source_sha256: str = ""
    copy_sha256: str = ""
    extra: dict = field(default_factory=dict)


def _command(converter, copy: Path, script: Path) -> list[str]:
    """The Core Console's command line (a seam for tests)."""
    return [converter.path, "/i", str(copy), "/s", str(script), "/l", "en-US"]


def _sha(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run(source: Path, work: Path, changes: list[dict], marker: float, text_height: float, *,
        check=None, nonce: str | None = None) -> CadRun:
    """Copy `source` into `work` (a folder of this run's own), make the
    changes on the copy and return the run -- its full log kept in
    `work/autocad.log`. Nothing is promoted here: the caller verifies.
    `check` is called before the run and about once a second while AutoCAD
    works; when it raises (a cancel), AutoCAD is stopped and the error
    passes on, the log kept."""
    converter = convert.find_converter()
    if converter is None or converter.kind != "accoreconsole":
        raise CadError("Making the redesigned drawing needs AutoCAD (its Core Console) on the PC the IFC worker runs on.")
    work = work.resolve()
    work.mkdir(parents=True, exist_ok=False)          # a run's own folder, never shared
    source = source.resolve()
    copy = work / f"redesign{source.suffix.lower()}"
    if copy == source:
        raise CadError("AutoCAD must work on a copy, never on the source drawing.")
    shutil.copyfile(source, copy)
    nonce = nonce or secrets.token_hex(8)
    script = work / "redesign.scr"
    # Plain LF line ends, as bytes (see convert._with_accoreconsole).
    script.write_bytes("\n".join(script_lines(changes, marker, text_height, nonce)).encode("utf-8"))
    n_ins, n_del = expected_counts(changes)
    log_path = work / "autocad.log"
    run_ = CadRun(work=work, copy=copy, script=script, log_path=log_path, log="", nonce=nonce, returncode=None,
                  expected_inserts=n_ins, expected_erases=n_del, seconds=0.0, source_sha256=_sha(source))
    if check:
        check()
    t0 = time.monotonic()
    proc = subprocess.Popen(_command(converter, copy, script), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            cwd=str(work), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = b""
    try:
        while True:
            try:
                out, _err = proc.communicate(timeout=POLL_S)
                break
            except subprocess.TimeoutExpired:
                if time.monotonic() - t0 > TIMEOUT_S:
                    raise CadError(f"AutoCAD did not finish within {TIMEOUT_S // 60} minutes.") from None
                if check:
                    check()
    except BaseException:
        # cancelled, timed out or interrupted: AutoCAD stopped, its log kept, nothing promoted
        proc.kill()
        try:
            out, _err = proc.communicate(timeout=30)
        except Exception:  # noqa: BLE001
            out = out or b""
        run_.log = convert._decode(out or b"")
        log_path.write_text(run_.log, encoding="utf-8", errors="replace")
        raise
    run_.seconds = time.monotonic() - t0
    run_.returncode = proc.returncode
    run_.log = convert._decode(out or b"")
    log_path.write_text(run_.log, encoding="utf-8", errors="replace")
    run_.copy_sha256 = _sha(copy) if copy.is_file() else ""
    return run_
