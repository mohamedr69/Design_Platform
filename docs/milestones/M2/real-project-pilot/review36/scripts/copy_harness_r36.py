"""ORCH-06C (R36HARNESS-IMPL): copy PILOT/review34/scripts/harness-r32/ to C:/t/iso/work/r2x/r36/harness-r32/ byte for byte.
Usage: copy_harness_r36.py <copy record json (absolute)>
Every source file is re-hashed and must equal its entry in the review34 evidence manifest (64d5ba0d...); the review34
manifest itself must hash to 64d5ba0d... ("PACKET MISMATCH" otherwise). Each copy is re-hashed after writing and must equal
its source. Refuses if the target folder exists (never reused). Reads review34 only; writes only the target folder and
the record."""
import datetime
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
R34PKG = PILOT / "review34"
R34_MANIFEST_SHA = "64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86"
SRC = R34PKG / "scripts" / "harness-r32"
DST = pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main(record_path):
    record_path = pathlib.Path(record_path)
    assert record_path.is_absolute()
    mraw = (R34PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    if sha(mraw) != R34_MANIFEST_SHA:
        raise SystemExit(f"PACKET MISMATCH: review34 manifest {sha(mraw)}")
    man = json.loads(mraw.decode("utf-8"))["files"]
    if DST.exists():
        raise SystemExit(f"refused: {DST} exists (never reused)")
    files = sorted(p for p in SRC.iterdir() if p.is_file())
    listed = sorted(k for k in man if k.startswith("scripts/harness-r32/"))
    if [f"scripts/harness-r32/{p.name}" for p in files] != listed:
        raise SystemExit("PACKET MISMATCH: the review34 harness folder differs from its manifest listing")
    DST.mkdir(parents=True)
    out = {}
    for p in files:
        b = p.read_bytes()
        want = man[f"scripts/harness-r32/{p.name}"]["sha256"]
        if sha(b) != want or len(b) != man[f"scripts/harness-r32/{p.name}"]["bytes"]:
            raise SystemExit(f"PACKET MISMATCH: {p.name}")
        q = DST / p.name
        with open(q, "xb") as fh:
            fh.write(b)
        got = sha(q.read_bytes())
        if got != want:
            raise SystemExit(f"copy differs: {p.name}")
        out[p.name] = {"source": p.as_posix(), "source_sha256": want, "copy": q.as_posix(), "copy_sha256": got, "bytes": len(b)}
    rec = {"kind": "ORCH-06C harness copy record", "copied_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "source_folder": SRC.as_posix(), "target_folder": DST.as_posix(), "review34_manifest_sha256": R34_MANIFEST_SHA,
           "files": out, "file_count": len(out), "all_equal": all(v["source_sha256"] == v["copy_sha256"] for v in out.values())}
    text = json.dumps(rec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(record_path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({"files": len(out), "all_equal": rec["all_equal"], "record_sha256": sha(text.encode("utf-8"))}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
