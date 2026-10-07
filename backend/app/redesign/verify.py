"""What AutoCAD made, checked before it counts (RD-M2, 3 October 2026).

An Apply is a success only when every check below passes; otherwise its
copy stays in the run's folder as evidence and is never promoted:

  1. AutoCAD exited with code 0;
  2. its log carries this run's EP-RD-OK marker with the counts the script
     expected, and no EP-RD-FAIL / EP-RD-NOSAVE marker of this run;
  3. the copy exists and differs from the source;
  4. read back (the copy converted to DXF and opened with ezdxf), compared
     with the source drawing's own DXF by handle:
       - every expected erase is gone, and nothing else in model space is;
       - every expected insert is there: a new INSERT of its block at its
         insertion point.

The markers are bound to the run's nonce, so an echo of another run's
script, or of this one's, never passes for an outcome."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from pathlib import Path

INSERT_TOLERANCE = 0.001        # drawing units: the script writes six decimals


@dataclass
class Verification:
    ok: bool = False
    problems: list[str] = field(default_factory=list)
    log: dict = field(default_factory=dict)
    readback: dict = field(default_factory=dict)

    def fail(self, message: str) -> None:
        self.problems.append(message)


def parse_log(log: str, nonce: str) -> dict:
    """The run's markers, each counted only as a line of its own: the Core
    Console also echoes a top-level expression's value, so a printed marker
    comes back once more as a quoted string ("\\nEP-RD-OK:...\\n") -- seen
    in the RD-M2 AutoCAD validation -- which is not a second outcome."""
    nonce = re.escape(nonce)
    fails = re.findall(rf"(?m)^EP-RD-FAIL:{nonce}:([^:\s]+):(\S*)[ \t]*\r?$", log)
    ok = re.findall(rf"(?m)^EP-RD-OK:{nonce}:(\d+):(\d+)[ \t]*\r?$", log)
    nosave = re.findall(rf"(?m)^EP-RD-NOSAVE:{nonce}[ \t]*\r?$", log)
    return {"failures": [{"step": s, "change": c} for s, c in fails],
            "ok": [{"inserts": int(i), "erases": int(e)} for i, e in ok],
            "nosave": len(nosave)}


def expectation(cad_changes: list[dict]) -> dict:
    return {"erase": sorted(c["remove_handle"] for c in cad_changes if c.get("remove_handle")),
            "insert": [{"id": c.get("id"), "block": c["insert"]["block"], "point": list(c["insert"]["model"])}
                       for c in cad_changes if c.get("insert")]}


def _modelspace(doc) -> dict[str, object]:
    return {e.dxf.handle: e for e in doc.modelspace()}


def reconcile(source_dxf: Path, output_dxf: Path, expect: dict) -> dict:
    """The output read back against the source, by handle."""
    import ezdxf

    src = _modelspace(ezdxf.readfile(source_dxf))
    out = _modelspace(ezdxf.readfile(output_dxf))
    gone = set(src) - set(out)
    wanted_gone = set(expect["erase"])
    new = [out[h] for h in set(out) - set(src)]
    new_inserts = [e for e in new if e.dxftype() == "INSERT"]
    found, missing = [], []
    used: set[str] = set()
    for item in expect["insert"]:
        hit = next((e for e in new_inserts if e.dxf.handle not in used
                    and e.dxf.name.upper() == item["block"].upper()
                    and math.dist((e.dxf.insert.x, e.dxf.insert.y), item["point"]) <= INSERT_TOLERANCE), None)
        if hit is None:
            missing.append(item)
        else:
            used.add(hit.dxf.handle)
            found.append({"id": item["id"], "handle": hit.dxf.handle, "block": item["block"]})
    by_type: dict[str, int] = {}
    for e in new:
        by_type[e.dxftype()] = by_type.get(e.dxftype(), 0) + 1
    return {"source_entities": len(src), "output_entities": len(out),
            "erased_as_expected": sorted(gone & wanted_gone), "not_erased": sorted(wanted_gone - gone),
            "unexpected_erasures": sorted(gone - wanted_gone), "inserts_found": found, "inserts_missing": missing,
            "unexpected_inserts": sorted(e.dxf.handle for e in new_inserts if e.dxf.handle not in used),
            "added_by_type": by_type}


def verify(run, *, expect: dict, readback: dict | None) -> Verification:
    """`run`: cad.CadRun; `readback`: reconcile()'s result, or None when
    the copy could not be read back (then the Apply is not a success)."""
    v = Verification()
    if run.returncode != 0:
        v.fail(f"AutoCAD exited with code {run.returncode}.")
    log = parse_log(run.log, run.nonce)
    v.log = log
    for f in log["failures"]:
        v.fail(f"AutoCAD reported a failed step: {f['step']} (change {f['change']}).")
    if log["nosave"]:
        v.fail("AutoCAD did not save the copy.")
    if len(log["ok"]) != 1:
        v.fail("AutoCAD's completion marker is missing." if not log["ok"] else "More than one completion marker.")
    elif (log["ok"][0]["inserts"], log["ok"][0]["erases"]) != (run.expected_inserts, run.expected_erases):
        v.fail(f"AutoCAD counted {log['ok'][0]['inserts']} inserts / {log['ok'][0]['erases']} erases; "
               f"{run.expected_inserts} / {run.expected_erases} were expected.")
    if not Path(run.copy).is_file():
        v.fail("The redesigned copy is missing.")
    elif not run.copy_sha256 or run.copy_sha256 == run.source_sha256:
        v.fail("The redesigned copy is the same as the source: nothing was saved.")
    if readback is None:
        v.fail("The redesigned copy could not be read back.")
    else:
        v.readback = readback
        if readback["not_erased"]:
            v.fail(f"{len(readback['not_erased'])} symbol(s) to erase are still in the drawing.")
        if readback["unexpected_erasures"]:
            v.fail(f"{len(readback['unexpected_erasures'])} entity(ies) were erased that no approved change erases.")
        if readback["inserts_missing"]:
            v.fail(f"{len(readback['inserts_missing'])} approved insert(s) are not in the drawing.")
        if readback["unexpected_inserts"]:
            v.fail(f"{len(readback['unexpected_inserts'])} insert(s) are in the drawing that no approved change makes.")
    v.ok = not v.problems
    return v
