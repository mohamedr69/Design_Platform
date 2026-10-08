"""R43-40 (new): run the bound review43 runner (runner_r32.main, unchanged) in DRY mode with the dry base redirected into the
task's work folder (r43p_base.redirect, substitution S-BASE). The harness is imported from C.HARNESS42 (the bound folder,
or the byte copy named by R43_HARNESS_RUN), checked first against BINDING-MANIFEST-R43-HARNESS (C.check_run_copy).
Usage (cwd: the harness folder it imports from): <bound python> -B runner_r43p.py <runner_r32 arguments>
Refuses '--mode live' (this wrapper exists for dry runs only)."""
from __future__ import annotations

import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402
import r43p_base as B  # noqa: E402

if "live" in sys.argv[1:]:
    raise SystemExit("refused: runner_r43p.py runs dry mode only")
C.check_run_copy()
sys.path.insert(0, str(C.HARNESS42))
import preflight_r32 as PF  # noqa: E402
import runner_r32 as RN  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402

B.redirect(PF, RN, SI)
sys.exit(RN.main(sys.argv[1:]))
