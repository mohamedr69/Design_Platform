"""ORCH-10 (R42PORT-IMPL): the review42 outputs, generated with the PACKAGE harness (PILOT/review42/scripts/harness-r32):
  PROJECT-REQUEST-BOUNDS.json  project_bounds_r32.main over the run set (merged path), window 60 / 86,400 s, elapsed 604,800 s;
                               compared with review39's (99be01fb...): every key equal except run_set.path (Desktop -> merged)
  RESUME-INVOCATIONS-R42.json  resume_invocations_r39.main over the new bounds; compared byte for byte with review39's
  REQUEST-PATHS-STATIC.json    request_paths_r42.main (review39's analysis re-run + the global-provider resolution)
Each is a subprocess under the bound interpreter, cwd the package harness, with the R42 audit guard. Writes argv[1]
(a JSON record of the comparisons) and the three files into PILOT/review42/ (refuses to overwrite)."""
import json
import os
import pathlib
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

ENV = {k: v for k, v in os.environ.items() if not k.startswith(("AI_", "ANTHROPIC", "CLAUDE", "R34_OWNER", "R38_SANDBOX"))
       and k.upper() not in ("PWD", "OLDPWD")} | {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "GIT_OPTIONAL_LOCKS": "0",
                                                "PYTHONPATH": str(C.WORK / "guard")}


def run(args):
    r = subprocess.run([C.PY, "-B", *args], cwd=str(C.HARNESS42), env=ENV, capture_output=True, text=True, encoding="utf-8")
    if r.returncode:
        raise SystemExit(f"failed: {args}: {r.stderr[-2000:]}")
    return r.stdout


def main(record):
    out = {}
    bounds, resume, paths = C.REVIEW42 / "PROJECT-REQUEST-BOUNDS.json", C.REVIEW42 / "RESUME-INVOCATIONS-R42.json", C.REVIEW42 / "REQUEST-PATHS-STATIC.json"
    for p in (bounds, resume, paths):
        if p.exists():
            raise SystemExit(f"refused: {p} exists (written once)")
    run(["project_bounds_r32.py", C.RUN_SET.as_posix(), bounds.as_posix(), "60", "86400", "604800"])
    new, old = json.loads(bounds.read_text(encoding="utf-8")), json.loads(C.BOUNDS39.read_text(encoding="utf-8"))
    diff = sorted(k for k in set(new) | set(old) if new.get(k) != old.get(k))
    rs_new, rs_old = new.get("run_set"), old.get("run_set")
    only_path = diff == ["run_set"] and {k: v for k, v in rs_new.items() if k != "path"} == {k: v for k, v in rs_old.items() if k != "path"} \
        and rs_old["path"].replace(C.DESKTOP_EP, C.MERGED_EP) == rs_new["path"]
    keys = ("projects", "lanes", "compatible_limits", "per_document", "per_page_maximum", "version")
    out["bounds"] = {"path": bounds.as_posix(), "sha256": C.sha256_file(bounds), "review39_sha256": C.sha256_file(C.BOUNDS39),
                     "differing_top_level_keys": diff, "differs_only_in_run_set_path": only_path,
                     "verify_bounds_keys_equal": all(new.get(k) == old.get(k) for k in keys), "verify_bounds_keys": list(keys)}
    run(["resume_invocations_r39.py", bounds.as_posix(), resume.as_posix()])
    r39 = C.REVIEW39 / "RESUME-INVOCATIONS-R39.json"
    out["resume_invocations"] = {"path": resume.as_posix(), "sha256": C.sha256_file(resume), "review39_sha256": C.sha256_file(r39),
                                 "byte_identical_to_review39": resume.read_bytes() == r39.read_bytes()}
    run(["request_paths_r42.py", paths.as_posix()])
    rp = json.loads(paths.read_text(encoding="utf-8"))
    r39p = json.loads((C.REVIEW39 / "REQUEST-PATHS-STATIC.json").read_text(encoding="utf-8"))
    same_sites = {lane: sorted((s["path"], s["line"], s["kind"]) for s in rp["lanes"][lane]["sites_reached"]) ==
                  sorted((s["path"], s["line"], s["kind"]) for s in r39p["lanes"][lane]["sites_reached"]) for lane in ("B", "C", "R")}
    out["request_paths"] = {"path": paths.as_posix(), "sha256": C.sha256_file(paths), "summary": rp["summary"],
                            "reached_sites_equal_to_review39": same_sites, "global": {k: v["global"] for k, v in rp["lanes"].items()}}
    out["ok"] = only_path and out["bounds"]["verify_bounds_keys_equal"] and out["resume_invocations"]["byte_identical_to_review39"] \
        and rp["summary"]["every_lane_installs_before_its_application_entry"] and all(same_sites.values())
    C.write_json(record, out)
    print(json.dumps(out, indent=1))
    return 0 if out["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
