"""Print a summary of ISO/iso/evidence/autocad-validation.json (paths shortened)."""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ISO = os.path.abspath(os.path.join(HERE, ".."))
r = json.load(open(os.path.join(ISO, "iso", "evidence", "autocad-validation.json"), encoding="utf-8"))
short = lambda s: s.replace(ISO.replace("\\", "/"), "<RDM2>").replace(ISO, "<RDM2>")  # noqa: E731
print("started", r["started"], "finished", r["finished"])
print("source before", r["before"]["live_source_sha256"][:16], r["before"]["iso_source_sha256"][:16],
      "after", r["after"]["live_source_sha256"][:16], r["after"]["iso_source_sha256"][:16])
print("library_dir", short(r["library_dir"]))
for k, v in r["scenarios"].items():
    print("==", k, v["outcome"], v["seconds"], "s; row", v["row"])
    print("  run", v.get("run_folder"), "files", v.get("run_files"))
    print("  libs", [(c, short(p)) for c, p in v.get("script_library_refs", [])])
    print("  other-pc path in script", v.get("script_has_other_pc_path"), "| drawn with stored other-pc lib", v.get("stored_library_paths_other_pc"))
    print("  work copy sha", (v.get("work_copy_sha256") or "")[:16], "equals source", v.get("work_copy_equals_source"))
    print("  problems", (v.get("verification") or {}).get("problems"))
print("temp new", r["temp_new_entries"])
print("temp changed", r["temp_changed_entries"])
print("iso uploads new entries", len([k for k in r["after"]["iso_uploads"] if k not in r["before"]["iso_uploads"]]))
