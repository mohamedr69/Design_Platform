"""ORCH-09 (R40DECL-IMPL): a DRY demonstration of what happens when the runner's own CLI-version check refuses the FIRST
invocation (runner_r32.main records `claude --version` after creating the run folder and before consuming the owner's
authorization). Dry mode never runs a CLI, so the refusal is injected IN-PROCESS by replacing
model_identity_r38.record_invocation with a function that raises the same IdentityRefused the live check raises; the bound
files are not changed. Then, without the injection: 'run' again and 'resume'.

Usage: <venv python> -B cli_version_deadend_r40.py <stamp> <out json>
Writes only under C:/t/r2x/r40-sandbox/<stamp> (the dry run folder) and <out json>. No CLI, no provider, no model."""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r40common as C  # noqa: E402

C.harness_import_path()
import model_identity_r38 as MI  # noqa: E402
import runner_r32 as RN  # noqa: E402

stamp, out = sys.argv[1], pathlib.Path(sys.argv[2])
folder = C.SANDBOX_BASE / stamp
args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.SANDBOX_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING.as_posix(),
        "--binding-sha", C.BINDING_SHA]
steps = []
original = MI.record_invocation


def refusing(run_folder, invocation, pins, version, *, mode):
    raise MI.IdentityRefused("refused: CLI version '9.9.9 (Claude Code)' differs from the declared '2.1.263 (Claude Code)' "
                             "[dry drill: the live check's refusal injected in-process]")


def call(cmd):
    try:
        RN.main([cmd, *args])
        return {"command": cmd, "result": "finished"}
    except RN.Refused as exc:
        return {"command": cmd, "result": "refused", "why": str(exc)}
    except Exception as exc:  # noqa: BLE001
        return {"command": cmd, "result": "error", "why": f"{type(exc).__name__}: {exc}"}


before = C.ledger_counts()
MI.record_invocation = refusing
steps.append(call("run") | {"injected": "CLI version refusal at invocation 1"})
MI.record_invocation = original
state = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8")) if (folder / "RUN-STATE.json").exists() else None
listing = sorted(p.relative_to(folder).as_posix() for p in folder.rglob("*") if p.is_file()) if folder.exists() else []
steps.append(call("run") | {"injected": None})
steps.append(call("resume") | {"injected": None})
after = C.ledger_counts()
res = {"name": "CLI-version dead-end drill (dry)", "stamp": stamp, "run_folder": folder.as_posix(), "steps": steps,
       "after_first_invocation": {"run_folder_exists": folder.exists(), "files": listing,
                                  "allowance_exists": (folder / "allowance.sqlite").exists(), "capture_store_exists": (folder / "capture.sqlite").exists(),
                                  "invocations": (state or {}).get("invocations")},
       "ai_ledger_before": before, "ai_ledger_after": after, "ai_ledger_unchanged": before == after, "model_requests": 0,
       "reading": ("a refusal of the runner's own CLI-version check at invocation 1 leaves a run folder (RUN-STATE.json, WRITER lock removed, the "
                   "invocation recorded 'refused') WITHOUT an allowance or a capture store: 'run' is refused because the folder exists and "
                   "'resume' is refused because the allowance is missing; with the declared stamp the run could not continue and a new "
                   "declaration (new stamp, new hash) would be needed. The owner's authorization is NOT consumed (the consumption comes after the "
                   "version check). Mitigation: the owner confirms `claude --version` prints exactly '2.1.263 (Claude Code)' before invocation 1.")}
out.write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"steps": [(s["command"], s["result"], (s.get("why") or "")[:160]) for s in steps], "allowance_exists": res["after_first_invocation"]["allowance_exists"],
                  "ai_ledger_unchanged": res["ai_ledger_unchanged"]}, indent=1))
