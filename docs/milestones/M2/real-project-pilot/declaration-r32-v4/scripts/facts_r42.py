"""ORCH-10 unit 1 (R42PORT-IMPL): re-verify the standing facts of the task section 0 (read-only). Writes one JSON file
(argv[1]). The CLI file is READ AS BYTES only (never executed); the AI ledger is opened mode=ro; the merged .env is never
opened (its existence is recorded by name only)."""
from __future__ import annotations

import datetime
import importlib.metadata as md
import json
import pathlib
import platform
import shutil
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402


def desktop_counts() -> dict:
    """How many bindings of the frozen v2 package name the absent Desktop installation."""
    b = json.loads(C.BINDING39.read_text(encoding="utf-8"))
    keys = [p for files in b["files"].values() for p in files]
    decl = json.loads((C.V2 / C.V2_NAME).read_text(encoding="utf-8"))
    n_decl = 0

    def walk(o):
        nonlocal n_decl
        if isinstance(o, dict):
            if isinstance(o.get("path"), str) and o["path"].startswith(C.DESKTOP_EP) and isinstance(o.get("sha256"), str):
                n_decl += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(decl)
    text = (C.V2 / C.V2_NAME).read_text(encoding="utf-8")
    return {"binding_r39_path_keyed": len(keys), "binding_r39_desktop_keys": sum(1 for p in keys if p.startswith(C.DESKTOP_EP)),
            "declaration_v2_desktop_path_bindings_with_sha256": n_decl, "declaration_v2_desktop_string_occurrences": text.count(C.DESKTOP_EP),
            "desktop_installation_exists": pathlib.Path(C.DESKTOP_EP).exists(), "desktop_python_exists": pathlib.Path(C.DESKTOP_PY).exists()}


def interpreter() -> dict:
    dists = sorted(f"{d.metadata['Name']}=={d.version}" for d in md.distributions())
    rec = C.VENV_FREEZE_RECORD.read_text(encoding="utf-8").splitlines() if C.VENV_FREEZE_RECORD.is_file() else []
    rec = sorted(x.strip() for x in rec if x.strip() and not x.startswith("#"))
    norm = lambda s: s.lower().replace("_", "-")  # noqa: E731
    return {"executable": sys.executable.replace("\\", "/"), "bound": C.PY, "equal_to_bound": sys.executable.replace("\\", "/").lower() == C.PY.lower(),
            "sys_version": sys.version, "implementation": platform.python_implementation(), "sha256": C.sha256_file(C.PY),
            "bytes": pathlib.Path(C.PY).stat().st_size, "optimize_flag": sys.flags.optimize, "dont_write_bytecode": sys.dont_write_bytecode,
            "distributions": dists, "distributions_sha256": C.sha256_bytes("\n".join(dists).encode()),
            "freeze_record": {"path": C.VENV_FREEZE_RECORD.as_posix(), "sha256": C.sha256_file(C.VENV_FREEZE_RECORD) if rec else None, "lines": len(rec),
                              "only_in_record": sorted(set(map(norm, rec)) - set(map(norm, dists))),
                              "only_in_venv": sorted(set(map(norm, dists)) - set(map(norm, rec)))},
            "pymupdf": md.version("PyMuPDF") if any(d.startswith("PyMuPDF==") for d in dists) else None,
            "sqlalchemy": md.version("SQLAlchemy")}


def main(out) -> int:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    f = {"task": "ORCH-10 unit 1: standing facts re-verified (read-only)", "started_utc": started}
    f["task_file"] = {"path": C.TASK_FILE.as_posix(), "sha256": C.sha256_file(C.TASK_FILE), "expected": C.TASK_FILE_SHA}
    f["v2_declaration"] = {"sha256": C.sha256_file(C.V2 / C.V2_NAME), "expected": C.V2_SHA,
                           "DECLARATION.sha256": (C.V2 / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0]}
    f["manifests"] = {name: C.manifest_check(C.PILOT / name) for name in ("declaration-r32-v2", "review39")}
    f["manifests"]["declaration-r32-v2"]["expected"] = C.V2_MANIFEST_SHA
    f["manifests"]["review39"]["expected"] = C.REVIEW39_MANIFEST_SHA
    f["binding_r39"] = {"sha256": C.sha256_file(C.BINDING39), "expected": C.BINDING39_SHA}
    f["bounds_r39"] = {"sha256": C.sha256_file(C.BOUNDS39), "expected": C.BOUNDS39_SHA}
    f["desktop_bindings"] = desktop_counts()
    f["heads"] = {r: C.git_state(r) for r in (C.CANDIDATE[0], C.BASELINE[0])}
    f["heads_expected"] = {C.CANDIDATE[0]: C.CANDIDATE[1], C.BASELINE[0]: C.BASELINE[1]}
    led = C.ledger_state()
    f["ai_ledger"] = {k: led[k] for k in ("entries", "scopes", "limit_amendments", "scope_names_sha256")} | {
        "opened": "file:...?mode=ro, uri=True", "scope_v3_exists": C.SCOPE in led["scope_names"]}
    f["staging"] = {"path": "C:/t/r2x/r32-stage", "files": sum(1 for p in pathlib.Path("C:/t/r2x/r32-stage").rglob("*") if p.is_file())}
    f["cli"] = {"which_claude": (shutil.which("claude") or "").replace("\\", "/"), "file": C.CLI_EXE.as_posix(),
                "sha256": C.sha256_file(C.CLI_EXE), "bytes": C.CLI_EXE.stat().st_size, "expected_sha256": C.CLI_EXE_SHA,
                "expected_bytes": C.CLI_EXE_BYTES, "executed": False,
                "embedded_version_strings_263": C.CLI_EXE.read_bytes().count(b'VERSION:"2.1.263"'),
                "bundled_2_1_289_exists": C.BUNDLED_CLI_NOT_USED.exists(), "bundled_2_1_289_used": False}
    f["interpreter"] = interpreter()
    f["merged_env_file"] = {"path": C.MERGED_ENV_FILE.as_posix(), "exists": C.MERGED_ENV_FILE.exists(), "read": False}
    f["policy"] = {n: {"sha256": C.sha256_file(C.MR / n), "expected": w} for n, w in C.POLICY.items()}
    f["r40_work_records"] = {p: {"sha256": C.sha256_file(p), "expected": w} for p, w in C.R40_WORK_RECORDS.items()}
    f["response_ledger"] = {"path": C.RESPONSE_LEDGER.as_posix(), "sha256": C.sha256_file(C.RESPONSE_LEDGER), "expected": C.RESPONSE_BEFORE[0],
                            "bytes": C.RESPONSE_LEDGER.stat().st_size}
    f["disk"] = {"C_free_bytes": C.free_bytes("C:/"), "G_free_bytes": C.free_bytes("G:/"), "long_paths_enabled": C.long_paths_enabled()}
    f["live_run_folder_exists"] = C.RUN_FOLDER.exists()
    f["sandbox_base_exists"] = C.SANDBOX_BASE.exists()
    f["packages_new_exist"] = {"review42": C.REVIEW42.exists(), "declaration-r32-v3": C.PACKAGE.exists()}
    f["forbidden_files"] = C.forbidden_files()
    checks = {
        "task_file": f["task_file"]["sha256"] == C.TASK_FILE_SHA,
        "v2_declaration": f["v2_declaration"]["sha256"] == C.V2_SHA == f["v2_declaration"]["DECLARATION.sha256"],
        "v2_manifest": f["manifests"]["declaration-r32-v2"]["manifest_sha256"] == C.V2_MANIFEST_SHA and not f["manifests"]["declaration-r32-v2"]["differ"],
        "review39_manifest": f["manifests"]["review39"]["manifest_sha256"] == C.REVIEW39_MANIFEST_SHA and not f["manifests"]["review39"]["differ"],
        "binding_r39": f["binding_r39"]["sha256"] == C.BINDING39_SHA,
        "bounds_r39": f["bounds_r39"]["sha256"] == C.BOUNDS39_SHA,
        "heads": all(f["heads"][r]["head"] == w and f["heads"][r]["clean"] for r, w in f["heads_expected"].items()),
        "ai_ledger": {k: f["ai_ledger"][k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and not f["ai_ledger"]["scope_v3_exists"],
        "cli": f["cli"]["sha256"] == C.CLI_EXE_SHA and f["cli"]["bytes"] == C.CLI_EXE_BYTES,
        "interpreter": f["interpreter"]["equal_to_bound"] and f["interpreter"]["sys_version"].startswith("3.12.10"),
        "policy": all(v["sha256"] == v["expected"] for v in f["policy"].values()),
        "r40_work_records": all(v["sha256"] == v["expected"] for v in f["r40_work_records"].values()),
        "response_ledger": f["response_ledger"]["sha256"] == C.RESPONSE_BEFORE[0],
        "disk_C_at_least_2GiB": f["disk"]["C_free_bytes"] >= C.MIN_FREE_BYTES,
        "no_live_run_folder": not f["live_run_folder_exists"],
        "no_forbidden_files": not f["forbidden_files"],
        "desktop_absent": not f["desktop_bindings"]["desktop_installation_exists"],
    }
    f["checks"] = checks
    f["all_ok"] = all(checks.values())
    f["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    C.write_json(out, f)
    print(json.dumps({"all_ok": f["all_ok"], "failed": [k for k, v in checks.items() if not v], "desktop": f["desktop_bindings"],
                      "ledger": f["ai_ledger"], "disk": f["disk"], "manifests": {k: (v["equal"], v["entries"], v["unlisted"]) for k, v in f["manifests"].items()}},
                     indent=1))
    return 0 if f["all_ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
