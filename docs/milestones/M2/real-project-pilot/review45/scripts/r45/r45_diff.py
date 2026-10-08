"""R43-42 (review45, new): the file-by-file comparison of review45/scripts against review43/scripts (the harness copy record
and the unified diffs of DRILL-DIFF.md). Read-only; writes <out dir>/HARNESS-COMPARE-R43.json and <out dir>/DRILL-DIFF.patch.
Usage: <bound python> -B r45_diff.py <out dir>"""
from __future__ import annotations

import difflib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402


def files(root: pathlib.Path) -> dict:
    return {p.relative_to(root).as_posix(): p for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def main(out_dir: str) -> int:
    out = pathlib.Path(out_dir)
    a_root, b_root = C.REVIEW43 / "scripts", C.REVIEW45 / "scripts"
    a, b = files(a_root), files(b_root)
    rows, patch = [], []
    for rel in sorted(set(a) | set(b)):
        ra = C.sha256_file(a[rel]) if rel in a else None
        rb = C.sha256_file(b[rel]) if rel in b else None
        status = "unchanged" if ra == rb else ("new" if ra is None else ("removed" if rb is None else "changed"))
        row = {"file": rel, "r43_sha256": ra, "r45_sha256": rb, "status": status}
        if status in ("changed", "new") and not rel.startswith("r45/"):
            la = a[rel].read_text(encoding="utf-8").splitlines(keepends=True) if rel in a else []
            lb = b[rel].read_text(encoding="utf-8").splitlines(keepends=True)
            d = list(difflib.unified_diff(la, lb, fromfile=f"review43/scripts/{rel}" if rel in a else "/dev/null", tofile=f"review45/scripts/{rel}", n=3))
            row |= {"added": sum(1 for x in d if x.startswith("+") and not x.startswith("+++")),
                    "removed": sum(1 for x in d if x.startswith("-") and not x.startswith("---")), "lines_r43": len(la), "lines_r45": len(lb)}
            patch += d
        elif status == "new":
            row["note"] = "task tooling (review45/scripts/r45/): not part of the harness; listed, not diffed"
        rows.append(row)
    summary = {k: sum(1 for r in rows if r["status"] == k) for k in ("unchanged", "changed", "new", "removed")}
    rec = {"written_local": C.now_local(), "a": a_root.as_posix(), "b": b_root.as_posix(), "summary": summary, "files": rows}
    C.write_json(out / "HARNESS-COMPARE-R43.json", rec)
    (out / "DRILL-DIFF.patch").write_text("".join(x if x.endswith("\n") else x + "\n" for x in patch), encoding="utf-8", newline="\n")
    print(json.dumps(summary), json.dumps([(r["file"], r.get("added"), r.get("removed")) for r in rows if r["status"] in ("changed", "new")]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
