"""R43-42 (review45, new): run the harness test suite from the RUN COPY with build/run_tests_r42.py UNCHANGED (imported, not
edited); this wrapper only sets its two module constants and the guard's environment (recorded substitutions):
  S-T1  run_tests_r42.GUARD     = <run copy>/r45/guard          (the review45 guard: the v4 guard + three recorded changes)
  S-T2  run_tests_r42.GUARD_LOG = C:/t/r2x/r42-sandbox/r45p/guard-log
  S-T3  environment: R43_GUARD_ROOTS=C:/t/r2x/r42-sandbox, R45_GUARD_TEST_BASE=1 (the suite creates its sandboxes as siblings
        at the sandbox base, by design), R43_GUARD_LOG=<S-T2>; the deny list (r32-v<N>, owner records, ledger, trees, frozen
        packages) still applies first
  --new-only  runs ONLY test_dry_baseline_drill_r45 (it imports run_control_r38, so it runs like test_global_provider_r42:
        cwd C:/t/iso/cand-r30n/backend, PYTHONPATH <harness>;<guard>, AI_ENABLED=false); without it, the 26 modules of
        run_tests_r42 exactly (MODULES and CANDIDATE_CWD_MODULES unchanged: the existing 549 tests).
Usage: <bound python> -B r45_run_tests.py <junit dir (new)> <basetemp (new, under C:/t/r2x/r42-sandbox)> <harness dir> [--new-only]"""
from __future__ import annotations

import os
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "build"))
import r45common as C  # noqa: E402
import run_tests_r42 as RT  # noqa: E402

NEW = "test_dry_baseline_drill_r45"


def main(argv) -> int:
    new_only = "--new-only" in argv
    argv = [a for a in argv if a != "--new-only"]
    RT.GUARD = HERE / "guard"
    RT.GUARD_LOG = C.WORK / "guard-log"
    os.environ["R43_GUARD_ROOTS"] = C.SANDBOX_BASE.as_posix()
    os.environ["R45_GUARD_TEST_BASE"] = "1"
    os.environ["R43_GUARD_LOG"] = str(RT.GUARD_LOG)
    if new_only:
        RT.MODULES = []
        RT.CANDIDATE_CWD_MODULES = [NEW]
    s = RT.main(argv)
    return 0 if s["all_passed"] and not s["guard_refusals"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
