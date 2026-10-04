"""M2 Round 2 exploration, step 1: metadata inventory of the 10 frozen EXPLORATION projects only (names and stat
metadata; no content read). The project list comes from the frozen ROUND2-SELECTION.json (hash-checked); sealed
entries are refused before any path is touched. Same walker as the Round 1 pilot (outputs/scripts/inventory.py)."""
import collections
import datetime
import hashlib
import json
import os
import pathlib

SEL = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review06/evidence/round2/ROUND2-SELECTION.json")
SEL_SHA = "5437e16449ece38c8b169dc26416521bb5ed576c953d56df76317fe0694ca3a7"
OUT = pathlib.Path("C:/t/iso/work/r2x/inventory")
ATTR_OFFLINE, ATTR_RECALL_ON_OPEN, ATTR_RECALL_ON_DATA, ATTR_REPARSE = 0x1000, 0x40000, 0x400000, 0x400
PREFIX = "\\\\?\\"

assert hashlib.sha256(SEL.read_bytes()).hexdigest() == SEL_SHA, "the frozen selection changed"
sel = json.loads(SEL.read_text(encoding="utf-8"))
exploration = [p for p in sel["projects"] if "exploration" in str(p.get("cohort", ""))]
assert len(exploration) == 10 and not any("sealed" in str(p.get("cohort", "")) for p in exploration)


def walk(root: str):
    out, errors, stack, seen = [], [], [root], set()
    while stack:
        d = stack.pop()
        try:
            with os.scandir(d if d.startswith(PREFIX) else PREFIX + d) as it:
                for e in it:
                    try:
                        st = e.stat(follow_symlinks=False)
                    except OSError as exc:
                        errors.append({"path": e.path.replace(PREFIX, ""), "error": f"{type(exc).__name__}: {exc}"[:160]})
                        continue
                    attrs = getattr(st, "st_file_attributes", 0)
                    if e.is_dir(follow_symlinks=False):
                        if attrs & ATTR_REPARSE:
                            errors.append({"path": e.path.replace(PREFIX, ""), "error": "reparse point directory not followed"})
                            continue
                        key = os.path.normcase(e.path.replace(PREFIX, ""))
                        if key not in seen:
                            seen.add(key)
                            stack.append(e.path)
                    elif e.is_file(follow_symlinks=False):
                        rel = os.path.relpath(e.path.replace(PREFIX, ""), root)
                        out.append({"relative_path": rel, "extension": os.path.splitext(rel)[1].lower(), "size": st.st_size, "mtime_ns": st.st_mtime_ns,
                                    "offline": bool(attrs & ATTR_OFFLINE), "recall_on_data_access": bool(attrs & ATTR_RECALL_ON_DATA),
                                    "recall_on_open": bool(attrs & ATTR_RECALL_ON_OPEN), "path_length": len(e.path.replace(PREFIX, ""))})
        except OSError as exc:
            errors.append({"path": d.replace(PREFIX, ""), "error": f"{type(exc).__name__}: {exc}"[:160]})
    return out, errors


OUT.mkdir(parents=True, exist_ok=True)
report = {"at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "selection": str(SEL), "selection_sha256": SEL_SHA,
          "content_read": "none (names and stat metadata only)", "projects": []}
for p in exploration:
    files = []
    errors = []
    for folder in p["folders"]:
        got, errs = walk(folder)
        tag = pathlib.Path(folder).name
        files += [{**f, "folder": folder, "folder_name": tag} for f in got]
        errors += errs
    ext = collections.Counter(f["extension"] for f in files)
    entry = {"ep": p["ep"], "contractor": p["contractor"], "cohort": p["cohort"], "folders": p["folders"], "file_count": len(files),
             "pdf_count": ext.get(".pdf", 0), "bytes": sum(f["size"] for f in files), "extensions": dict(ext.most_common()),
             "placeholders_recall_on_data_access": sum(1 for f in files if f["recall_on_data_access"]),
             "paths_over_259": sum(1 for f in files if f["path_length"] > 259), "errors": errors,
             "vs_frozen_metadata": {"files": p.get("files"), "pdf": p.get("pdf"), "word": p.get("word")}}
    json.dump({"project": entry, "files": files}, open(OUT / f"inventory-EP-{p['ep']}.json", "w", encoding="utf-8"), indent=1)
    report["projects"].append(entry)
    print(p["ep"], "files", len(files), "pdf", ext.get(".pdf", 0), "doc/docx", ext.get(".doc", 0) + ext.get(".docx", 0), "errors", len(errors),
          "| frozen metadata files/pdf:", p.get("files"), p.get("pdf"), flush=True)
json.dump(report, open(OUT / "EXPLORATION-INVENTORY.json", "w", encoding="utf-8"), indent=1)
