"""R43-40 (new): the driver-side redirect of the DRY / demonstration sandbox base, so that every dry run folder of this task
lies inside the task's one work folder C:/t/r2x/r42-sandbox/r43p (the orchestrator's one-folder rule; Verification 43
R43V-12 records that the harness otherwise creates its dry and test folders as siblings at the sandbox base).

The bound harness accepts only C:/t/r2x/r<NN>-sandbox as a sandbox base (preflight_r32._SANDBOX_BASE_RE) and makes a dry run
folder <base>/<stamp>. redirect() widens that pattern IN THE CALLING PROCESS ONLY to also accept exactly one more path,
C.DRY_BASE (C:/t/r2x/r42-sandbox/r43p/sb), and makes it the default dry base of preflight_r32, runner_r32 and
sandbox_ingest_r32. Nothing else changes: the bound files are not edited; live mode is untouched (a live run takes its base
from the declaration, whose run.sandbox_base C:/t/r2x/r42-sandbox still matches the original pattern); the lane processes
receive their sandbox paths from the run configuration. Recorded in V4-BUILD-DIFF.md as substitution S-BASE."""
from __future__ import annotations

import os
import pathlib
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402


def redirect(PF, RN=None, SI=None, base=None) -> dict:
    base = pathlib.Path(base or C.DRY_BASE)
    s = base.as_posix()
    if not s.lower().startswith(C.WORK.as_posix().lower() + "/"):
        raise SystemExit(f"refused: the dry base must lie inside the task's work folder {C.WORK.as_posix()} ({s})")
    original = PF._SANDBOX_BASE_RE.pattern
    PF._SANDBOX_BASE_RE = re.compile(f"(?:{original})|{re.escape(s)}")
    PF.DEFAULT_SANDBOX_BASE = base
    PF.SANDBOX_BASE = base
    os.environ.pop(PF.SANDBOX_BASE_ENV, None)
    if RN is not None:
        RN.SANDBOX_BASE = base
    if SI is not None:
        SI.SANDBOX_BASE = base
    base.mkdir(parents=True, exist_ok=True)
    return {"substitution": "S-BASE", "dry_base": s, "pattern_before": original, "pattern_after": PF._SANDBOX_BASE_RE.pattern,
            "live_base_unchanged": PF._SANDBOX_BASE_RE.fullmatch(C.SANDBOX_BASE.as_posix()) is not None}
