"""Why the file-level inventory exceeds the frozen metadata: paths over 259 characters (which select_round2.py's
os.walk/os.stat without the extended prefix skipped) and files modified after the freeze."""
import datetime
import json
import pathlib

CUT = datetime.datetime(2026, 9, 28, 23, 30, 45).timestamp() * 1e9
rows = []
for f in sorted(pathlib.Path("C:/t/iso/work/r2x/inventory").glob("inventory-EP-*.json")):
    d = json.loads(f.read_text(encoding="utf-8"))
    p, files = d["project"], d["files"]
    short = [x for x in files if x["path_length"] <= 259]
    rows.append({"ep": p["ep"], "frozen_files": p["vs_frozen_metadata"]["files"], "frozen_pdf": p["vs_frozen_metadata"]["pdf"],
                 "now_files": len(files), "now_pdf": sum(x["extension"] == ".pdf" for x in files),
                 "now_files_path_le_259": len(short), "now_pdf_path_le_259": sum(x["extension"] == ".pdf" for x in short),
                 "modified_after_freeze": sum(x["mtime_ns"] > CUT for x in files)})
json.dump(rows, open("C:/t/iso/work/r2x/inventory/COUNT-RECONCILIATION.json", "w", encoding="utf-8"), indent=1)
for r in rows:
    print(r)
