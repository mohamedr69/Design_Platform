"""R43-44: the same snapshot for task R43-44: review45 and declaration-r32-v4 added; the executed v3 run folder by os.stat only (names,
sizes, mtimes; no file opened, as Verification 45); the v4 and v5 scopes and run folders.
R43-40 (new): the before / after snapshot of everything task R43-40 must not change, read-only.
Usage: <bound python> -B snapshot_r43p.py <out json>   (with the package guard; R43_GUARD_OWNER_RECORDS=hash-only lets THIS
process hash the owner-records folder as a whole: one aggregate sha256 and a file count, never a per-file value or content)
Records: the AI ledger (mode=ro) counts and scope names hash; whether the v4 scope exists; the pip freeze sha256 (the bound
interpreter, no cache, no version check); aggregate hashes of the executed v3 run folder, the owner records, review42,
review43, declaration-r32, -v2 and -v3 and the R43 review package; the five application trees (HEAD, clean status, index
file hash); every authorization / RUN / token-named file under PILOT and C:/t/r2x (names only); whether the v4 run folder
exists; C: free bytes. Aggregate hash = sha256 over the sorted lines '<relative path>\\t<size>\\t<sha256>' (extended-length
opens). Writes only <out json>. No provider, model, network or CLI."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

TREES = ("C:/t/iso/frozen-r12", "C:/t/iso/cand-r29", "C:/t/iso/frozen-r13", "C:/t/iso/cand-r30", "C:/t/iso/cand-r30n")
FOLDERS = {"owner_records": C.OWNER_RECORDS, "review42": C.REVIEW42, "review43": C.REVIEW43, "review45": C.REVIEW45,
           "declaration_r32_v4": C.V4,
           "declaration_r32": C.PILOT / "declaration-r32", "declaration_r32_v2": C.V2, "declaration_r32_v3": C.V3,
           "r43_review_package": pathlib.Path("C:/t/r2x/r42-sandbox/R43-REVIEW-PACKAGE")}


def aggregate(root: pathlib.Path) -> dict:
    lines = []
    for dp, _ds, fs in os.walk(C.long_path(root)):
        for f in fs:
            full = os.path.join(dp, f)
            rel = os.path.relpath(full, C.long_path(root)).replace("\\", "/")
            lines.append(f"{rel}\t{os.path.getsize(full)}\t{C.sha256_file(full)}")
    lines.sort()
    return {"path": root.as_posix(), "files": len(lines), "sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()}


def stat_listing(root: pathlib.Path) -> dict:
    """R43-44: a live run folder by os.stat only (relative path, size, mtime_ns); no file is opened."""
    if not root.exists():
        return {"path": root.as_posix(), "exists": False}
    lines = []
    for dp, _ds, fs in os.walk(C.long_path(root)):
        for f in fs:
            full = os.path.join(dp, f)
            st = os.stat(full)
            lines.append(f"{os.path.relpath(full, C.long_path(root)).replace(chr(92), '/')}\t{st.st_size}\t{st.st_mtime_ns}")
    lines.sort()
    return {"path": root.as_posix(), "exists": True, "files": len(lines), "stat_sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(),
            "method": "os.stat only; no file opened"}


def tree(repo: str) -> dict:
    env = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    g = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, env=env).stdout.strip()  # noqa: E731
    idx = g("rev-parse", "--path-format=absolute", "--git-path", "index")
    return {"repo": repo, "head": g("rev-parse", "HEAD"), "status_lines": len([x for x in g("status", "--porcelain").splitlines() if x.strip()]),
            "index_sha256": C.sha256_file(idx) if idx and os.path.isfile(idx) else None}


def named_files() -> list:
    hits = []
    for root in (C.PILOT, pathlib.Path("C:/t/r2x")):
        for dp, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if d not in ("node_modules", ".git", "venv")]
            for f in fs:
                low = f.lower()
                if "dispatch-authorization" in low or low.endswith(".run.json") or "owner-token" in low:
                    hits.append((pathlib.Path(dp) / f).as_posix())
    return sorted(hits)


def main(out: str) -> int:
    led = C.ledger_state()
    env = {**os.environ, "PIP_DISABLE_PIP_VERSION_CHECK": "1", "PIP_NO_CACHE_DIR": "1", "PIP_NO_INPUT": "1"}
    pf = subprocess.run([C.PY, "-B", "-m", "pip", "freeze"], capture_output=True, env=env)
    res = {"taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "ai_ledger": {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")},
           "v3_scope_present": C.V3_SCOPE in led["scope_names"], "v4_scope_present": C.V4_SCOPE in led["scope_names"],
           "v5_scope_present": C.SCOPE in led["scope_names"], "v3_run_folder_stat": stat_listing(C.V3_RUN_FOLDER),
           "pip_freeze": {"sha256": hashlib.sha256(pf.stdout).hexdigest(), "lines": len(pf.stdout.splitlines()), "returncode": pf.returncode},
           "folders": {k: aggregate(v) for k, v in FOLDERS.items()}, "trees": {t: tree(t) for t in TREES},
           "authorization_run_token_named_files": named_files(), "v4_run_folder_exists": C.V4_RUN_FOLDER.exists(),
           "v5_run_folder_exists": C.RUN_FOLDER.exists(), "v5_package_exists": C.PACKAGE.exists(),
           "c_free_bytes": C.free_bytes("C:/")}
    C.write_json(out, res)
    print(json.dumps({"ai_ledger": res["ai_ledger"], "pip_freeze": res["pip_freeze"]["sha256"], "v4_scope": res["v4_scope_present"],
                      "v5_scope": res["v5_scope_present"], "v4_run_folder": res["v4_run_folder_exists"], "v5_run_folder": res["v5_run_folder_exists"], "named_files": len(res["authorization_run_token_named_files"]),
                      "c_free_bytes": res["c_free_bytes"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
