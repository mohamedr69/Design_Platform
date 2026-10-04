"""Pilot step 1: refresh the metadata inventory of the ten selected project folders with extended Windows paths
(no content read), record cloud-placeholder / offline attributes and every error, and diff against the reviewer's
per-project inventories. Names and stat metadata only."""
import json, os, sys, pathlib, datetime, stat, collections

S = pathlib.Path(sys.argv[1]); R = pathlib.Path(sys.argv[2])
sel = json.load(open(R / "pilot_selection.json", encoding="utf-8"))
ATTR_OFFLINE = 0x1000; ATTR_RECALL_ON_OPEN = 0x40000; ATTR_RECALL_ON_DATA = 0x400000; ATTR_REPARSE = 0x400
PREFIX = "\\\\?\\"


def walk(root: str):
    """Every file under root by extended path; symlinks/reparse directories are not followed."""
    out, errors = [], []
    stack = [root]
    seen_dirs = set()
    while stack:
        d = stack.pop()
        try:
            with os.scandir(PREFIX + d if not d.startswith(PREFIX) else d) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                    except OSError as exc:
                        errors.append({"path": e.path.replace(PREFIX, ""), "error": f"{type(exc).__name__}: {exc}"[:160]}); continue
                    attrs = getattr(st, "st_file_attributes", 0)
                    if e.is_dir(follow_symlinks=False):
                        if attrs & ATTR_REPARSE:
                            errors.append({"path": e.path.replace(PREFIX, ""), "error": "reparse point directory not followed"}); continue
                        key = os.path.normcase(e.path.replace(PREFIX, ""))
                        if key in seen_dirs:
                            continue
                        seen_dirs.add(key); stack.append(e.path)
                    elif e.is_file(follow_symlinks=False):
                        rel = os.path.relpath(e.path.replace(PREFIX, ""), root)
                        out.append({"relative_path": rel, "extension": os.path.splitext(rel)[1].lower(), "size": st.st_size, "mtime_ns": st.st_mtime_ns,
                                    "attributes": attrs, "offline": bool(attrs & ATTR_OFFLINE), "recall_on_data_access": bool(attrs & ATTR_RECALL_ON_DATA),
                                    "recall_on_open": bool(attrs & ATTR_RECALL_ON_OPEN), "path_length": len(e.path.replace(PREFIX, ""))})
                    else:
                        errors.append({"path": e.path.replace(PREFIX, ""), "error": "neither file nor directory (link?)"})
        except OSError as exc:
            errors.append({"path": d.replace(PREFIX, ""), "error": f"{type(exc).__name__}: {exc}"[:160]})
    return out, errors


report = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "root": sel.get("root"), "projects": []}
for p in sel["projects"]:
    files, errors = walk(p["path"])
    prior = json.load(open(R / f"EP-{p['ep']}-file-inventory.json", encoding="utf-8"))["files"]
    prior_paths = {f["relative_path"]: f for f in prior}; now_paths = {f["relative_path"]: f for f in files}
    added = sorted(set(now_paths) - set(prior_paths)); removed = sorted(set(prior_paths) - set(now_paths))
    changed = sorted(k for k in set(now_paths) & set(prior_paths) if (now_paths[k]["size"], now_paths[k]["mtime_ns"]) != (prior_paths[k]["size"], prior_paths[k]["mtime_ns"]))
    ext = collections.Counter(f["extension"] for f in files)
    entry = {"ep": p["ep"], "folder": p["folder"], "contractor": p["contractor"], "path": p["path"], "cohort": p["cohort"],
             "file_count": len(files), "pdf_count": ext.get(".pdf", 0), "bytes": sum(f["size"] for f in files), "extensions": dict(ext.most_common()),
             "placeholders": {"offline": sum(1 for f in files if f["offline"]), "recall_on_data_access": sum(1 for f in files if f["recall_on_data_access"]),
                              "pdf_recall_on_data_access": sum(1 for f in files if f["recall_on_data_access"] and f["extension"] == ".pdf")},
             "longest_path": max((f["path_length"] for f in files), default=0), "paths_over_259": sum(1 for f in files if f["path_length"] > 259),
             "errors": errors, "diff_vs_reviewer_inventory": {"reviewer_count": len(prior), "added": len(added), "removed": len(removed), "changed_stat": len(changed),
                                                              "added_examples": added[:5], "removed_examples": removed[:5]}}
    json.dump({"project": entry, "files": files}, open(S / f"inventory-EP-{p['ep']}.json", "w", encoding="utf-8"), indent=1)
    report["projects"].append(entry)
    print(p["ep"], p["cohort"], "files", len(files), "pdf", ext.get(".pdf", 0), "errors", len(errors), "placeholders(recall)", entry["placeholders"]["recall_on_data_access"], "diff +", len(added), "-", len(removed), "~", len(changed), flush=True)
report["totals"] = {"files": sum(p["file_count"] for p in report["projects"]), "pdf": sum(p["pdf_count"] for p in report["projects"]), "errors": sum(len(p["errors"]) for p in report["projects"])}
json.dump(report, open(S / "PROJECT-INVENTORY.json", "w", encoding="utf-8"), indent=1)
print("totals", report["totals"])
