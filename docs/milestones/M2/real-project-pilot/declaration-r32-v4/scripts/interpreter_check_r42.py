"""ORCH-10 unit (task 2.1.1, R42PORT-IMPL): the bound interpreter against the two frozen trees. Read-only for the trees.
  * the interpreter: sys.version, the sha256 of the venv's python.exe and of the base interpreter it runs, the installed
    distributions (importlib.metadata; no pip process) and their difference from the recorded merged-venv freeze;
  * per tree: requirements.txt pins against the installed versions (any difference recorded);
  * per tree: an import check in a CHILD process under the bound interpreter, cwd = the tree's backend, with the harness's
    sandbox environment (every root in C:/t/r2x/r42-sandbox/importcheck-<tree>, AI disabled, no ledger) and the R42 audit
    guard: every application module a lane, the ingestion child or the scorer imports must import, and `app` must resolve
    to the tree (never to the merged installation); every other app.* module is imported too and its result recorded.
Writes one JSON (argv[1]). Nothing is executed in the trees beyond imports; no database is opened by this script."""
from __future__ import annotations

import importlib.metadata as md
import json
import pathlib
import re
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

HARNESS = C.HARNESS42
sys.path.insert(0, str(HARNESS))
import sandbox_ingest_r32 as SI  # noqa: E402

TREES = {"baseline": C.BASELINE_BACKEND, "candidate": C.CANDIDATE_BACKEND}
LANE_MODULES = {
    "baseline": ["app.core.config", "app.database", "app.models", "app.services.document_processing", "app.services.document_sync",
                 "app.ai.submittal_reader", "app.services.drawing_ai_review", "app.ai.provider", "app.ai.ledger", "app.migrations", "app.seed",
                 "app.core.timeutils"],
    "candidate": ["app.core.config", "app.database", "app.models", "app.ai.evidence_reader", "app.ai.submittal_reader",
                  "app.services.drawing_ai_review", "app.ai.provider", "app.ai.ledger", "app.migrations", "app.seed", "app.core.timeutils"],
}
CHILD = r'''
import importlib, json, os, pathlib, pkgutil, sys, traceback
tree = pathlib.Path(os.getcwd())
sys.path.insert(0, str(tree))
need = json.loads(sys.argv[1])
out = {"sys_executable": sys.executable, "sys_version": sys.version, "needed": {}, "all": {}}
for m in need:
    try:
        mod = importlib.import_module(m)
        out["needed"][m] = {"ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:
        out["needed"][m] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
import app
out["app_file"] = app.__file__
for info in pkgutil.walk_packages(app.__path__, "app."):
    if info.name in out["needed"]:
        continue
    try:
        importlib.import_module(info.name)
        out["all"][info.name] = "ok"
    except BaseException as exc:
        out["all"][info.name] = f"{type(exc).__name__}: {str(exc)[:160]}"
from app.core.config import get_settings
s = get_settings()
out["settings_env_file"] = str((type(s).model_config or {}).get("env_file"))
out["modules_under_merged"] = sorted(n for n, mm in sys.modules.items() if isinstance(getattr(mm, "__file__", None), str)
    and "ep-platform-merged" in mm.__file__.replace("\\", "/") and "/backend/venv/" not in mm.__file__.replace("\\", "/"))
print(json.dumps(out))
'''


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirements(tree: pathlib.Path) -> list:
    out = []
    for ln in (tree / "requirements.txt").read_text(encoding="utf-8").splitlines():
        ln = ln.split("#", 1)[0].strip()
        if not ln:
            continue
        spec, _, marker = ln.partition(";")
        m = re.match(r"([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*==\s*([^\s]+)", spec.strip())
        if m:
            out.append({"name": m.group(1), "pinned": m.group(3), "marker": marker.strip() or None})
    return out


def main(out_path) -> int:
    installed = {norm(d.metadata["Name"]): d.version for d in md.distributions()}
    base = pathlib.Path(sys.base_prefix) / "python.exe"
    res = {"interpreter": {"path": C.PY, "sys_executable": sys.executable.replace("\\", "/"), "sys_version": sys.version, "sha256": C.sha256_file(C.PY),
                           "base_interpreter": base.as_posix(), "base_sha256": C.sha256_file(base) if base.exists() else None,
                           "base_python312_dll_sha256": C.sha256_file(pathlib.Path(sys.base_prefix) / "python312.dll")
                           if (pathlib.Path(sys.base_prefix) / "python312.dll").exists() else None,
                           "distributions": dict(sorted(installed.items()))},
           "trees": {}}
    rec = C.VENV_FREEZE_RECORD.read_text(encoding="utf-8").splitlines() if C.VENV_FREEZE_RECORD.is_file() else []
    recd = {}
    for x in rec:
        m = re.match(r"([A-Za-z0-9_.\-]+)==(\S+)", x.strip())
        if m:
            recd[norm(m.group(1))] = m.group(2)
    res["interpreter"]["freeze_record"] = {"path": C.VENV_FREEZE_RECORD.as_posix(), "sha256": C.sha256_file(C.VENV_FREEZE_RECORD) if rec else None,
                                           "differences": {k: {"record": recd.get(k), "installed": installed.get(k)}
                                                           for k in sorted(set(recd) | set(installed)) if recd.get(k) != installed.get(k)}}
    ok = True
    for name, tree in TREES.items():
        reqs = requirements(tree)
        diffs = []
        for r in reqs:
            have = installed.get(norm(r["name"]))
            if have != r["pinned"]:
                diffs.append({"requirement": r["name"], "pinned": r["pinned"], "installed": have, "marker": r["marker"]})
        root = C.SANDBOX_BASE / f"importcheck-{name}"
        env = SI.sandbox_env(root, ai_enabled=False)
        env["PYTHONPATH"] = str(C.WORK / "guard")
        (root / "db").mkdir(parents=True, exist_ok=True)
        p = subprocess.run([C.PY, "-B", "-c", CHILD, json.dumps(LANE_MODULES[name])], cwd=str(tree), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        try:
            child = json.loads(p.stdout.strip().splitlines()[-1])
        except Exception:  # noqa: BLE001
            child = {"error": p.stderr[-3000:], "returncode": p.returncode}
        needed_ok = all(v.get("ok") for v in (child.get("needed") or {}).values()) and bool(child.get("needed"))
        app_in_tree = str(child.get("app_file") or "").replace("\\", "/").lower().startswith(tree.as_posix().lower())
        failed_all = {k: v for k, v in (child.get("all") or {}).items() if v != "ok"}
        res["trees"][name] = {"tree": tree.as_posix(), "requirements_sha256": C.sha256_file(tree / "requirements.txt"), "requirements": len(reqs),
                              "requirement_differences": diffs, "import_check": child, "needed_modules_import": needed_ok,
                              "app_resolves_to_tree": app_in_tree, "other_modules_failed": failed_all,
                              "modules_under_merged": child.get("modules_under_merged"), "sandbox_root": root.as_posix()}
        ok = ok and needed_ok and app_in_tree and not child.get("modules_under_merged")
    res["trees_requirements_identical"] = C.sha256_file(C.BASELINE_BACKEND / "requirements.txt") == C.sha256_file(C.CANDIDATE_BACKEND / "requirements.txt")
    res["ok"] = ok
    C.write_json(out_path, res)
    print(json.dumps({"ok": ok, "requirement_differences": {k: v["requirement_differences"] for k, v in res["trees"].items()},
                      "other_modules_failed": {k: len(v["other_modules_failed"]) for k, v in res["trees"].items()},
                      "freeze_differences": res["interpreter"]["freeze_record"]["differences"]}, indent=1))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
