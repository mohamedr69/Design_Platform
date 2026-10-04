"""ORCH-06C (R36HARNESS-IMPL): the TEST-RUN TWIN of the bound r36 harness copy (never bound, never packaged as code).

Why: the review34 test suite hard-codes the sandbox base C:/t/r2x/r34-sandbox (preflight_r32.SANDBOX_BASE, the
sandbox child's path assertion, test helpers and test assertions), and test_runner_r32 / test_sandbox_ingest_r32 create
sandboxes there. ORCH-06C allows sandboxes only under C:/t/r2x/r36-sandbox/ and allows no change to any module other
than literal_compare_r32.norm_revision. So the whole suite runs from a twin that differs from the bound copy ONLY by the
literal string SUBST_FROM -> SUBST_TO; every other byte is equal (checked here and by the package check).

Usage: make_suite_twin_r36.py <record json (absolute)>      refuses if the twin folder exists (never reused)
twin_bytes(name, data) is the whole transformation (imported by the package check)."""
import datetime
import hashlib
import json
import pathlib
import sys

BOUND = pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32")
TWIN = pathlib.Path("C:/t/iso/work/r2x/r36/harness-r32-suite-twin")
SUBST_FROM = b"C:/t/r2x/r34-sandbox"
SUBST_TO = b"C:/t/r2x/r36-sandbox"


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def twin_bytes(name: str, data: bytes) -> bytes:
    return data.replace(SUBST_FROM, SUBST_TO)


def main(record):
    record = pathlib.Path(record)
    assert record.is_absolute()
    if TWIN.exists():
        raise SystemExit(f"refused: {TWIN} exists")
    TWIN.mkdir(parents=True)
    files = {}
    for p in sorted(BOUND.iterdir()):
        if not p.is_file():
            continue
        b = p.read_bytes()
        t = twin_bytes(p.name, b)
        with open(TWIN / p.name, "xb") as fh:
            fh.write(t)
        n = b.count(SUBST_FROM)
        lines = [i + 1 for i, line in enumerate(b.split(b"\n")) if SUBST_FROM in line]
        files[p.name] = {"bound_sha256": sha(b), "twin_sha256": sha((TWIN / p.name).read_bytes()), "substitutions": n,
                         "lines": lines, "identical": n == 0}
    rec = {"kind": "ORCH-06C test-run twin record", "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "bound_copy": BOUND.as_posix(), "twin": TWIN.as_posix(), "substitution": [SUBST_FROM.decode(), SUBST_TO.decode()],
           "files": files, "file_count": len(files), "files_with_substitutions": sorted(k for k, v in files.items() if v["substitutions"]),
           "substitutions_total": sum(v["substitutions"] for v in files.values()),
           "statement": "the twin is the bound copy with only the sandbox-base string substituted; it is used only to run the test "
                        "suite with sandboxes under C:/t/r2x/r36-sandbox/; it is not bound and not packaged as harness code"}
    text = json.dumps(rec, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(record, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(json.dumps({k: rec[k] for k in ("file_count", "files_with_substitutions", "substitutions_total")}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
