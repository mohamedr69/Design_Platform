"""R43-42 (review45, new): the ONE evidence run of the dry baseline-facts drill, from the run copy, under the review45 guard
(roots C:/t/r2x/r42-sandbox/r45p only). runner_r32 and drill_r45 are imported from the run copy UNCHANGED; the only
substitution is the driver-side sandbox base (S-BASE, as R43-40's r43p_base.redirect): preflight_r32's base pattern is
widened IN THIS PROCESS ONLY to also accept exactly C:/t/r2x/r42-sandbox/r45p/sb, so the drill folder
r45p/sb/r32-drill-<stamp> lies inside the task's one work folder; nothing else changes, and live mode is untouched.
Usage: <bound python> -B r45_drill_run.py <run copy harness dir> <spec json> <binding json> <stamp> <record json>
Records: the AI ledger (mode=ro) and the pip freeze before and after, the argv, the substitution, the exit, the times."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import sys
import traceback

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402

DRY_BASE = C.WORK / "sb"
RUN_SET = (C.PILOT / "review34/RUN-SET-PROPOSAL.json").as_posix()


def main(harness, spec, binding, stamp, record) -> int:
    sys.path.insert(0, harness)
    import preflight_r32 as PF
    import runner_r32 as RN

    assert pathlib.Path(RN.__file__).resolve().parent == pathlib.Path(harness).resolve(), RN.__file__
    rec = {"started_local": C.now_local(), "harness": harness, "ledger_before": C.ledger_state(), "pip_freeze_before": C.pip_freeze()}
    original = PF._SANDBOX_BASE_RE.pattern
    PF._SANDBOX_BASE_RE = re.compile(f"(?:{original})|{re.escape(DRY_BASE.as_posix())}")
    DRY_BASE.mkdir(parents=True, exist_ok=True)
    rec["substitution"] = {"id": "S-BASE", "pattern_before": original, "pattern_after": PF._SANDBOX_BASE_RE.pattern, "dry_base": DRY_BASE.as_posix(),
                           "scope": "this process only; no file edited"}
    bsha = hashlib.sha256(pathlib.Path(binding).read_bytes()).hexdigest()
    argv = ["run", "--mode", "dry", "--dry-baseline-facts", spec, "--stamp", stamp, "--run-set", RUN_SET, "--binding", binding, "--binding-sha", bsha,
            "--sandbox-base", DRY_BASE.as_posix()]
    rec["argv"] = argv
    try:
        rec["exit"] = RN.main(argv)
    except BaseException as exc:  # noqa: BLE001 -- recorded, then re-raised after the after-state is read
        rec["exit"] = None
        rec["error"] = f"{type(exc).__name__}: {exc}"
        rec["traceback"] = traceback.format_exc()[-4000:]
    rec["ledger_after"] = C.ledger_state()
    rec["pip_freeze_after"] = C.pip_freeze()
    rec["ledger_unchanged"] = rec["ledger_before"] == rec["ledger_after"]
    rec["finished_local"] = C.now_local()
    rec["drill_folder"] = (DRY_BASE / f"r32-drill-{stamp}").as_posix()
    C.write_json(record, rec)
    print(json.dumps({k: rec.get(k) for k in ("exit", "error", "ledger_unchanged", "drill_folder")}))
    return 0 if rec.get("exit") == 0 and rec["ledger_unchanged"] else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:6]))
