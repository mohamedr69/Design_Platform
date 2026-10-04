"""R40DECL-IMPL: does the application's Python (the backend venv) open a file whose full path is longer than 259 characters
on this machine (LongPathsEnabled = 0)? Writes only under C:/t/r2x/r40-sandbox/pathlen-probe (a tiny fake PDF per length).
Usage: <venv python> -B pathlen_probe_r40.py <out json>"""
import json
import os
import sys

BS = chr(92)
LONG = BS + BS + "?" + BS
BASE = "C:" + BS + "t" + BS + "r2x" + BS + "r40-sandbox" + BS + "pathlen-probe"


def main(out):
    res = {"python": sys.version, "base": BASE, "lengths": {}}
    try:
        import pymupdf
    except ImportError:
        pymupdf = None
    for total in (250, 259, 260, 261, 270, 283):
        d = BASE + BS + "d" * 100
        fname_len = total - len(d) - 1
        p = d + BS + ("f" * (fname_len - 4)) + ".pdf"
        assert len(p) == total, (len(p), total)
        os.makedirs(LONG + d, exist_ok=True)
        with open(LONG + p, "wb") as fh:
            fh.write(b"%PDF-1.4\n%probe\n")
        try:
            with open(p, "rb") as fh:
                fh.read(4)
            plain = "ok"
        except OSError as e:
            plain = f"{type(e).__name__}: errno {e.errno}"
        mu = "pymupdf not importable"
        if pymupdf is not None:
            try:
                pymupdf.open(p)
                mu = "opened"
            except Exception as e:  # noqa: BLE001
                mu = f"{type(e).__name__}: {str(e)[:100]}"
        res["lengths"][str(total)] = {"plain_open": plain, "pymupdf_open": mu, "os_path_exists": os.path.exists(p),
                                      "os_path_isfile": os.path.isfile(p)}
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1, sort_keys=True))


if __name__ == "__main__":
    main(sys.argv[1])
