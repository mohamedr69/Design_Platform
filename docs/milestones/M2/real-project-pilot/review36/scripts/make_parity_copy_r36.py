"""ORCH-06C (R36HARNESS-IMPL): a copy of the ORCH-06 parity scripts that judges the harness side with the FIXED r36 harness.

Usage: make_parity_copy_r36.py <record json (absolute)>      refuses if the target folder exists
Copies PILOT/evaluator-offline-r32/scripts/common_r35.py and run_evaluator_offline_r32.py (hash-checked against the
evaluator-offline-r32 manifest 86dd81d3...) to C:/t/iso/work/r2x/r36/parity/scripts/ and applies EXACTLY the
substitutions in SUBST (each must occur the stated number of times): the work folder r35 -> r36/parity (the run's only
write root and its never-created database path), the harness folder review34 -> the r36 copy, and the expected
literal_compare_r32 hash ec2221c8... -> the r36 hash. Nothing else changes: the evaluator side, the guards (no network,
no subprocess, provider classes stubbed, audit hook refusing writes outside the work folder) and the comparison logic
are the ORCH-06 code."""
import datetime
import difflib
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "evaluator-offline-r32"
MANIFEST_SHA = "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7"
DST = pathlib.Path("C:/t/iso/work/r2x/r36/parity/scripts")
NEW_LC = "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"
SUBST = {
    "common_r35.py": [
        ('WORK = pathlib.Path("C:/t/iso/work/r2x/r35")', 'WORK = pathlib.Path("C:/t/iso/work/r2x/r36/parity")', 1),
        ('HARNESS_DIR = REVIEW34 / "scripts/harness-r32"', 'HARNESS_DIR = pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32")', 1),
        ('"literal_compare_r32": "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6"', f'"literal_compare_r32": "{NEW_LC}"', 1),
    ],
    "run_evaluator_offline_r32.py": [
        ("C:/t/iso/work/r2x/r35/run/no-database-never-created.db", "C:/t/iso/work/r2x/r36/parity/run/no-database-never-created.db", 2),
    ],
}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main(record):
    record = pathlib.Path(record)
    mraw = (PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    if sha(mraw) != MANIFEST_SHA:
        raise SystemExit("PACKET MISMATCH: evaluator-offline-r32 manifest")
    man = json.loads(mraw.decode("utf-8"))["files"]
    if DST.exists():
        raise SystemExit(f"refused: {DST} exists")
    DST.mkdir(parents=True)
    (DST.parent / "run").mkdir()
    out = {}
    for name, subs in SUBST.items():
        src = PKG / "scripts" / name
        b = src.read_bytes()
        if sha(b) != man[f"scripts/{name}"]["sha256"]:
            raise SystemExit(f"PACKET MISMATCH: {name}")
        t = b.decode("utf-8")
        for old, new, n in subs:
            if t.count(old) != n:
                raise SystemExit(f"{name}: {old!r} occurs {t.count(old)} times, expected {n}")
            t = t.replace(old, new)
        with open(DST / name, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(t)
        diff = list(difflib.unified_diff(b.decode("utf-8").splitlines(), t.splitlines(), f"evaluator-offline-r32/scripts/{name}",
                                         f"r36/parity/scripts/{name}", n=0, lineterm=""))
        out[name] = {"source_sha256": sha(b), "copy_sha256": sha((DST / name).read_bytes()), "substitutions": [[o, n_, c] for o, n_, c in subs],
                     "diff": diff}
    rec = {"kind": "ORCH-06C parity-script copy record", "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "source_package_manifest_sha256": MANIFEST_SHA, "target": DST.as_posix(), "files": out,
           "statement": "only the work folder, the harness folder and the expected literal_compare_r32 hash differ from the ORCH-06 scripts"}
    text = json.dumps(rec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(record, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({k: {"copy_sha256": v["copy_sha256"], "changed_lines": sum(1 for x in v["diff"] if x.startswith("+") and not x.startswith("+++"))}
                      for k, v in out.items()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
