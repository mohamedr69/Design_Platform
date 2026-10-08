"""ORCH-046: the code's own read-back converter (convert.convert_dwg_to_dxf,
used by service._readback / _source_readback) run against the TrueView
console on the GC-01 copy. Records what it returns or raises."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import m5cad as H  # noqa: E402

from app.ifc.dxf import convert  # noqa: E402

import subprocess as _sp  # noqa: E402
import types  # noqa: E402

ISSUED = []


def _run(args, **kw):
    # the dedicated profile (OD-16 c): `/isolate` appended to the code's own arguments
    args = list(args) + (["/isolate", "m5cad", str(H.PROFILE)] if args and args[0] == H.EXE else [])
    ISSUED.append(args)
    return _sp.run(args, **kw)


convert.subprocess = types.SimpleNamespace(run=_run, TimeoutExpired=_sp.TimeoutExpired,
                                           CREATE_NO_WINDOW=getattr(_sp, "CREATE_NO_WINDOW", 0))
conv = convert.find_converter()
out = H.ROOT / "results" / "s9-readback.dxf"
t0 = time.monotonic()
data = {"at": H.now(), "converter": vars(conv) if conv else None, "input": str(H.SRC_COPY),
        "input_sha256": H.sha(H.SRC_COPY)}
try:
    r = convert.convert_dwg_to_dxf(H.SRC_COPY, out, conv)
    data["result"] = vars(r)
except Exception as exc:  # noqa: BLE001
    data["raised"] = f"{type(exc).__name__}: {exc}"
data["seconds"] = round(time.monotonic() - t0, 2)
data["dxf_exists"] = out.exists()
data["issued"] = ISSUED
data["note"] = ("convert's subprocess.run wrapped by the harness only to append /isolate (the code's own arguments "
                "kept); TEMP redirected to C:/t/tmp/m5cad/tmp")
H.write("s9-readback-converter", data)
