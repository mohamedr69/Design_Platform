"""ORCH-046 item 7: the code's own placing functions (service._stage,
_finalize, _into_archive, _copy_exclusive) on this PC's real volumes.

Payload: the unchanged GC-01 copy (no verified Apply copy exists: the
TrueView console cannot make one). Same volume: platform staging under
C:/t/tmp/m5cad/uploads -> C:/t/tmp/m5cad/uploads (Apply's _finalize) and
-> C:/t/tmp/m5cad/archive (publish's _into_archive). Second volume: an
isolated folder G:/t/tmp/m5cad-vol2/archive, removed afterwards. Which
branch was taken is read from the files: a hard link leaves the staged
copy in place with a link count of 2; a rename consumes it; an exclusive
copy leaves it with a link count of 1. Each placing is repeated onto the
now-taken name, which must be refused with nothing overwritten."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

sys.argv = [sys.argv[0], "noop"]
sys.path.insert(0, str(Path(__file__).parent))
import m5cad as H  # noqa: E402  (sets the isolated environment)

R = H.R
PAYLOAD = H.SRC_COPY
VOL2 = Path(r"G:\t\tmp\m5cad-vol2")


def info(p: Path) -> dict:
    if not p.exists():
        return {"exists": False}
    st = os.stat(p)
    return {"exists": True, "bytes": st.st_size, "nlink": st.st_nlink, "sha256": H.sha(p)}


def branch(part_before: dict, part_after: dict, dest: dict) -> str:
    if not dest.get("exists"):
        return "none"
    if not part_after.get("exists"):
        return "rename"
    return "hard link" if dest.get("nlink", 1) >= 2 else "exclusive copy"


def trial(label: str, fn, staging: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = R._stage(PAYLOAD, staging / dest.name)
    pb = info(part)
    out: dict = {"label": label, "function": fn.__name__, "part": str(part), "dest": str(dest),
                 "volumes": [os.path.splitdrive(str(part))[0], os.path.splitdrive(str(dest))[0]]}
    try:
        fn(part, dest)
        out["raised"] = None
    except Exception as exc:  # noqa: BLE001
        out["raised"] = f"{type(exc).__name__}: {exc}"
    pa, d = info(part), info(dest)
    out.update({"part_before": pb, "part_after": pa, "dest_after": d, "branch": branch(pb, pa, d),
                "dest_equals_payload": d.get("sha256") == H.sha(PAYLOAD)})
    part.unlink(missing_ok=True)
    # the name is now taken: placing again must refuse and overwrite nothing
    other = staging / ("other-" + dest.name)
    other.write_bytes(b"A DIFFERENT FILE")
    part2 = R._stage(other, staging / ("again-" + dest.name))
    try:
        fn(part2, dest)
        out["second_raised"] = None
    except Exception as exc:  # noqa: BLE001
        out["second_raised"] = f"{type(exc).__name__}: {exc}"
    out["dest_after_second"] = info(dest)
    out["unchanged_after_second"] = out["dest_after_second"].get("sha256") == d.get("sha256")
    part2.unlink(missing_ok=True)
    other.unlink(missing_ok=True)
    return out


def main() -> None:
    staging = (H.UPLOADS / f"EP-{H.EP}" / "redesign" / "vol-test-staging").resolve()
    stem = "GC-01 FA LAYOUT R0 - Redesign volume trial"
    results = [
        trial("Apply: platform copy, same volume (C:)", R._finalize, staging,
              (H.UPLOADS / f"EP-{H.EP}" / "redesign" / "vol-test" / f"{stem} A.dwg").resolve()),
        trial("Publish: archive on the same volume (C:)", R._into_archive, staging,
              (H.ARCHIVE / "vol-test archive (same volume)" / "03- Drawings" / "Redesign" / f"{stem} B.dwg").resolve()),
        trial("Publish: archive on a second volume (G:)", R._into_archive, staging,
              VOL2 / "archive (second volume)" / "03- Drawings" / "Redesign" / f"{stem} C.dwg"),
        trial("Apply's _finalize across volumes (C: -> G:), for the record", R._finalize, staging,
              VOL2 / "finalize cross-volume" / f"{stem} D.dwg"),
    ]
    probe = {}
    a = staging / "link-probe-src.bin"
    a.write_bytes(b"x")
    for label, target in (("same volume", staging / "link-probe-dst.bin"), ("second volume", VOL2 / "link-probe-dst.bin")):
        try:
            os.link(a, target)
            probe[label] = "os.link ok"
        except OSError as exc:
            probe[label] = f"os.link {type(exc).__name__} winerror={getattr(exc, 'winerror', None)}: {exc}"
        try:
            target.unlink()
        except OSError:
            pass
    a.unlink()
    data = {"at": H.now(), "payload": str(PAYLOAD), "payload_sha256": H.sha(PAYLOAD), "trials": results,
            "raw_link_probe": probe}
    H.write("s8-volumes", data)
    shutil.rmtree(staging, ignore_errors=True)
    shutil.rmtree(H.UPLOADS / f"EP-{H.EP}" / "redesign" / "vol-test", ignore_errors=True)
    shutil.rmtree(H.ARCHIVE / "vol-test archive (same volume)", ignore_errors=True)
    shutil.rmtree(VOL2, ignore_errors=True)
    print("second volume folder removed:", not VOL2.exists())


if __name__ == "__main__":
    main()
