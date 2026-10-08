"""R43-42 (review45, new): the self-check of BINDING-MANIFEST-R45-HARNESS.json. Read-only; writes only <out json>.
Checks: 25 fields in the R42 / R43-harness order; supersedes = f35355aa...; every files entry re-hashes equal (0 missing);
harness_files equal the review45 and review43 bytes; the r39_rehash recorded no difference; the R43 log prefix (lines 1..N)
re-hashes equal; the Verification 44, task card and drill bind hashes re-hash equal; preflight_r32.verify_binding passes on
the manifest (imported from the run copy given); declaration-r32-v4 unchanged; r32-v4 absent; no authorization claim.
Usage: <bound python> -B r45_selfcheck.py <manifest> <run copy harness dir> <out json>"""
from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402

ORDER = ["answers", "baseline", "binds", "candidate", "changed_from_review39", "cli_pin", "contract", "files", "global_provider", "harness_files",
         "immutable", "interpreter", "name", "new_in_review42", "not_bound_but_recorded", "r39_rehash", "reference_set", "reference_set_statement",
         "run_set_sha256", "sandbox_base", "statement", "supersedes", "truth_sha256", "unchanged_from_review39", "written_at_utc"]


def main(manifest: str, harness: str, out: str) -> int:
    checks = []

    def ck(name, ok, detail=None):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    raw = pathlib.Path(manifest).read_text(encoding="utf-8")
    m = json.loads(raw)
    ck("25 fields in the R42 order", list(m) == ORDER and len(m) == 25, list(m))
    ck("supersedes the review43 harness manifest", m["supersedes"]["sha256"] == C.BINDING43_SHA and C.sha256_file(m["supersedes"]["file"]) == C.BINDING43_SHA)
    n = 0
    for g, fs in m["files"].items():
        for p, want in fs.items():
            n += 1
            try:
                got = C.sha256_file(p)
            except OSError as exc:
                ck(f"file {g}: {p}", False, f"missing: {exc}")
                continue
            if got != want:
                ck(f"file {g}: {p}", False, {"bound": want, "now": got})
    ck(f"all {n} file entries re-hash equal", not [c for c in checks if c["check"].startswith("file ") and not c["ok"]], n)
    for name, v in m["harness_files"].items():
        a, b = C.REVIEW43 / "scripts/harness-r32" / name, C.REVIEW45 / "scripts/harness-r32" / name
        ck(f"harness_files {name}", (v["r43_sha256"] == (C.sha256_file(a) if a.exists() else None)) and v["r45_sha256"] == C.sha256_file(b))
    ck("r39_rehash recorded no difference", not m["r39_rehash"]["differ"] and not m["r39_rehash"]["missing"], {k: len(v) if isinstance(v, list) else v for k, v in m["r39_rehash"].items() if k != "rule"})
    lp = m["binds"]["r45_session_log_prefix"]
    n_lines = int(lp["lines"].split("-")[1])
    data = C.LOG.read_bytes().split(b"\n")
    prefix = b"\n".join(data[:n_lines]) + b"\n"
    ck(f"R43 log prefix lines {lp['lines']} re-hash equal", C.sha256_bytes(prefix) == lp["sha256"], {"lines_now": len(data) - 1})
    for k, v in m["binds"]["verification44"].items():
        ck(f"verification44 {k}", C.sha256_file(C.MR / "reviews/M2-review-44" / k) == v)
    ck("task card", C.sha256_file(m["binds"]["r45_task_card"]["path"]) == m["binds"]["r45_task_card"]["sha256"])
    for k, v in m["binds"]["r45_drill"].items():
        if isinstance(v, dict) and "path" in v:
            ck(f"drill bind {k}", C.sha256_file(v["path"]) == v["sha256"])
    sys.path.insert(0, harness)
    import preflight_r32 as PF
    try:
        vb = PF.verify_binding(manifest, C.sha256_file(manifest))
        ck("preflight_r32.verify_binding", True, vb)
    except Exception as exc:  # noqa: BLE001
        ck("preflight_r32.verify_binding", False, str(exc)[:500])
    ck("r32-v4 absent", not C.V4_RUN_FOLDER.exists())
    st = m["statement"].lower()
    ck("statement authorizes nothing", "authorizes nothing" in st and "not authorized" in st)
    fails = [c for c in checks if not c["ok"]]
    rec = {"manifest": pathlib.Path(manifest).as_posix(), "manifest_sha256": C.sha256_file(manifest), "checked_local": C.now_local(),
           "checks": len(checks), "failures": len(fails), "failed": fails, "all": checks}
    C.write_json(out, rec)
    print(json.dumps({"checks": len(checks), "failures": len(fails), "manifest_sha256": rec["manifest_sha256"]}))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
