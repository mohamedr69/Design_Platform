"""ORCH-10 section 2.1.3 (R42PORT-IMPL): path lengths on this machine (LongPathsEnabled = 0: ordinary file APIs fail at 260
characters). Read-only except the tiny probe files under C:/t/r2x/r42-sandbox/pathlen-probe.
  1. behaviour: does the bound interpreter's ordinary open (and pymupdf) open a path of 250..283 characters? (v2's probe)
  2. every BOUND path of BINDING-MANIFEST-R42 (its length; every one is opened by verify_binding / sha256 through the
     extended-length prefix since review42, so a length >= 260 would still verify);
  3. every file of the two new packages, of declaration-r32-v2 and of review39 at their merged paths;
  4. every LIVE run path: the staged PDF of every run-set document at <C:/t/r2x/r42-sandbox/r32-v3>/inv-<n>/B/s/EP-<ep>/<relative
     path> for n = 1..12, and every other run-folder file of a finished dry single run mapped onto the live folder.
Usage: pathlen_probe_r42.py <out json> [<dry single run folder>]"""
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

BS = chr(92)
BASE = "C:" + BS + "t" + BS + "r2x" + BS + "r42-sandbox" + BS + "pathlen-probe"


def behaviour() -> dict:
    res = {}
    try:
        import pymupdf
    except ImportError:
        pymupdf = None
    for total in (250, 259, 260, 261, 270, 283):
        d = BASE + BS + "d" * 100
        p = d + BS + ("f" * (total - len(d) - 1 - 4)) + ".pdf"
        assert len(p) == total
        os.makedirs(C.LONG + d, exist_ok=True)
        with open(C.LONG + p, "wb") as fh:
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
        try:
            with open(C.LONG + p, "rb") as fh:
                fh.read(4)
            ext = "ok"
        except OSError as e:
            ext = f"{type(e).__name__}"
        res[str(total)] = {"plain_open": plain, "extended_prefix_open": ext, "pymupdf_open": mu, "os_path_isfile": os.path.isfile(p)}
    return res


def lengths(paths) -> dict:
    ls = sorted(((len(p), p) for p in paths), reverse=True)
    return {"count": len(ls), "max": ls[0][0] if ls else 0, "at_or_over_260": [p for n, p in ls if n >= 260], "longest": [{"length": n, "path": p} for n, p in ls[:5]]}


def main(out, single=None) -> int:
    res = {"long_paths_enabled": C.long_paths_enabled(), "python": sys.version, "behaviour": behaviour()}
    man = json.loads(C.BINDING42.read_text(encoding="utf-8")) if C.BINDING42.exists() else {"files": {}}
    res["bound_paths"] = lengths([p for g in man["files"].values() for p in g])
    pk = {}
    for name in ("review42", "declaration-r32-v3", "declaration-r32-v2", "review39"):
        root = C.PILOT / name
        pk[name] = lengths([p.as_posix() for p in root.rglob("*") if p.is_file()]) if root.exists() else {"count": 0}
    res["package_paths"] = pk
    sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    T = PF.build_truth()
    docs = json.loads(C.RUN_SET.read_text(encoding="utf-8"))["documents"]
    staged = [f"{C.RUN_FOLDER.as_posix()}/inv-{n}/B/s/EP-{T['documents'][d['pool_id']]['ep']}/{T['documents'][d['pool_id']]['relative_path']}"
              for d in docs for n in range(1, 13)]
    res["live_staged_pdfs"] = lengths(staged) | {"by_invocation": {str(n): max(len(s) for s in staged if f"/inv-{n}/" in s) for n in range(1, 13)}}
    if single:
        sp = pathlib.Path(single)
        mapped = [(C.RUN_FOLDER / p.relative_to(sp)).as_posix() for p in sp.rglob("*") if p.is_file()]
        res["live_run_folder_files_mapped_from_dry_single"] = lengths(mapped) | {"dry_folder": sp.as_posix()}
    other = [C.RUN_FOLDER / "authorization" / ("consumed-" + "0" * 32 + ".json"), C.PACKAGE / C.RUN_NAME, C.PACKAGE / C.AUTH_NAME,
             C.RUN_FOLDER / "REENTRY-12.json", C.RUN_FOLDER / "allowance.sqlite.new"]
    res["owner_records"] = lengths([p.as_posix() for p in other])
    over = res["bound_paths"]["at_or_over_260"] + [p for v in pk.values() for p in v.get("at_or_over_260", [])] + res["owner_records"]["at_or_over_260"]
    res["summary"] = {"long_paths_enabled": res["long_paths_enabled"], "bound_max": res["bound_paths"]["max"],
                      "package_max": {k: v.get("max") for k, v in pk.items()}, "live_staged_max": res["live_staged_pdfs"]["max"],
                      "live_staged_max_inv_1_to_9": max(v for k, v in res["live_staged_pdfs"]["by_invocation"].items() if int(k) <= 9),
                      "live_run_folder_files_max": (res.get("live_run_folder_files_mapped_from_dry_single") or {}).get("max"),
                      "owner_records_max": res["owner_records"]["max"], "paths_at_or_over_260_outside_staged_pdfs": over,
                      "statement": (("every bound path, package path and live run-folder record stays below 260 characters; " if not over else
                                     f"{len(over)} path(s) reach 260 or more (listed): every harness hash and binding check opens them through the "
                                     "extended-length prefix; ")
                                    + "every harness hash and binding check opens files through the extended-length prefix anyway; the staged PDFs reach "
                                    f"{res['live_staged_pdfs']['max']} characters at most (inv-1..12) and are opened by the application's own extended-length helper")}
    C.write_json(out, res)
    print(json.dumps(res["summary"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:3]))
