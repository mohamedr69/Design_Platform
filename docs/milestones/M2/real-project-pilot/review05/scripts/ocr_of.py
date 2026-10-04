import sqlite3, json, sys
P = r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot"
fs = json.load(open(P + r"\FROZEN-SAMPLE.json", encoding="utf-8"))
c = sqlite3.connect(r"C:\t\pilot\cache\page-cache.sqlite")
name, page = sys.argv[1], int(sys.argv[2]) - 1
d = next(d for d in fs["documents"] if d["relative_path"].replace("\\", "/").endswith(name))
rows = c.execute("select key, text from ocr where key like ?", (f"{d['sha256']}:{page}:%",)).fetchall()
for k, t in rows:
    print("#####", k[65:]); print(t[: int(sys.argv[3]) if len(sys.argv) > 3 else 3000])
if not rows:
    import pymupdf; print("TEXT LAYER:"); print(pymupdf.open(d["staged_path"])[page].get_text()[:3000])
