"""R43-42 (review45, new): the before / after snapshot of everything task R43-42 must not change, read-only.
Usage: <bound python> -B r45_snapshot.py <out json>
Run under the guard copy with R43_GUARD_OWNER_RECORDS=hash-only (this process alone hashes the owner-records folder as a
whole: one aggregate value and a file count; never a per-file value, never content). Records: the AI ledger (mode=ro)
counts, scope-names hash, v3 / v4 scope presence; the pip freeze sha256; aggregate hashes of review42, review43,
declaration-r32 / -v2 / -v3 / -v4, the R43 review package and the owner records; the executed run folder r32-v3 by
os.stat only; whether r32-v4 exists; the five trees (HEAD, status lines, index hash); every authorization / RUN /
token-named file under PILOT and C:/t/r2x (names only); the sandbox base's entry names; C: free bytes. Writes only <out>."""
from __future__ import annotations

import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402


def named_files() -> list:
    hits = []
    for root in (C.PILOT, pathlib.Path("C:/t/r2x")):
        for dp, ds, fs in os.walk(root):
            ds[:] = [d for d in ds if d not in ("node_modules", ".git", "venv")]
            for f in fs:
                low = f.lower()
                if "dispatch-authorization" in low or low.endswith(".run.json") or "owner-token" in low or low.startswith("consumed-"):
                    hits.append((pathlib.Path(dp) / f).as_posix())
    return sorted(hits)


def main(out: str) -> int:
    res = {"taken_local": C.now_local(), "taken_utc": C.now_utc(), "ai_ledger": C.ledger_state(), "pip_freeze": C.pip_freeze(),
           "protected_folders": {k: C.aggregate(v) for k, v in C.PROTECTED.items()},
           "v3_run_folder": C.stat_listing(C.V3_RUN_FOLDER), "v4_run_folder_exists": C.V4_RUN_FOLDER.exists(),
           "trees": {t: C.tree_state(t) for t in C.TREES}, "authorization_run_token_named_files": named_files(),
           "sandbox_base_entries": sorted(p.name for p in C.SANDBOX_BASE.iterdir()), "c_free_bytes": C.free_bytes("C:/")}
    res["ledger_equals_expected"] = {k: res["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED
    C.write_json(out, res)
    print(json.dumps({"ai_ledger": {k: res["ai_ledger"][k] for k in ("entries", "scopes", "limit_amendments", "v4_scope_present")},
                      "pip_freeze_ok": res["pip_freeze"]["equals_precondition"], "v4_run_folder_exists": res["v4_run_folder_exists"],
                      "v3_files": res["v3_run_folder"].get("files"), "named_files": len(res["authorization_run_token_named_files"]),
                      "sandbox_entries": len(res["sandbox_base_entries"]), "c_free_bytes": res["c_free_bytes"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
