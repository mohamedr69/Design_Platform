"""ORCH-10 (R42PORT-IMPL): the DRY CLI-version case under the corrected runner -- Verification 41's dead-end (R41-09 case A)
no longer exists. Dry mode never runs a CLI, so the version refusal is injected IN-PROCESS by replacing
model_identity_r38.check_version (the comparison the runner now makes BEFORE it creates anything) with a function raising the
same IdentityRefused the live check raises; the bound files are not changed. Then, without the injection, the SAME 'run'
finishes. Usage: <bound python> -B cli_version_drill_r42.py <stamp> <out json>
Writes only under C:/t/r2x/r42-sandbox/<stamp> (the dry run folder) and <out json>. No CLI, no provider, no model."""
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

C.check_run_copy()                                  # R43-40: the review43 harness (run copy checked against its binding)
sys.path.insert(0, str(C.HARNESS42))
import model_identity_r38 as MI  # noqa: E402
import runner_r32 as RN  # noqa: E402
import preflight_r32 as PF  # noqa: E402  (R43-40)
import sandbox_ingest_r32 as SI  # noqa: E402  (R43-40)
import r43p_base as B  # noqa: E402  (R43-40: substitution S-BASE, the dry base inside the work folder)

B.redirect(PF, RN, SI)

stamp, out = sys.argv[1], pathlib.Path(sys.argv[2])
folder = C.DRY_BASE / stamp                         # R43-40: dry base C:/t/r2x/r42-sandbox/r43p/sb; the review43 harness manifest
args = ["--mode", "dry", "--stamp", stamp, "--sandbox-base", C.DRY_BASE.as_posix(), "--run-set", C.RUN_SET.as_posix(), "--binding", C.BINDING43.as_posix(),
        "--binding-sha", C.sha256_file(C.BINDING43)]
steps = []
original = MI.check_version


def refusing(run_folder, pins, version):
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
MI.check_version = refusing
steps.append(call("run") | {"injected": "CLI version refusal at invocation 1"})
MI.check_version = original
after_refusal = {"run_folder_exists": folder.exists()}
steps.append(call("run") | {"injected": None})
st = json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8")) if (folder / "RUN-STATE.json").exists() else {}
after = C.ledger_counts()
res = {"name": "CLI-version case under the corrected runner (dry)", "stamp": stamp, "run_folder": folder.as_posix(), "steps": steps,
       "after_the_refusal": after_refusal, "final_invocations": [{k: i.get(k) for k in ("n", "kind", "status", "run_state")} for i in st.get("invocations", [])],
       "ai_ledger_before": before, "ai_ledger_after": after, "ai_ledger_unchanged": before == after, "model_requests": 0,
       "reading": ("the runner now compares the CLI version line BEFORE it creates the run folder: a refusal at invocation 1 creates nothing (and, in "
                   "live mode, consumes no authorization); the same 'run' command then starts the run normally -- the dead-end of Verification 41 "
                   "(R41-09 case A) no longer exists")}
res["ok"] = [s["result"] for s in steps] == ["refused", "finished"] and not after_refusal["run_folder_exists"] and res["ai_ledger_unchanged"] \
    and [i["kind"] for i in res["final_invocations"]] == ["fresh"]
out.write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"ok": res["ok"], "steps": [(s["command"], s["result"]) for s in steps]}))
sys.exit(0 if res["ok"] else 1)
