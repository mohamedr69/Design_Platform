"""Round 2: the staged Word transmittals read with Word itself (COM, read-only, staged copies) for independent
labelling -- the Round 1 pilot's word_text.py method."""
import json
import pathlib

import win32com.client

man = json.loads(pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json").read_text(encoding="utf-8"))
word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
out = {}
for d in man["documents"]:
    if d["extension"] not in (".doc", ".docx"):
        continue
    try:
        doc = word.Documents.Open(d["staged_path"].replace("/", "\\"), ReadOnly=True, AddToRecentFiles=False, Visible=False)
        text = doc.Content.Text
        tables = []
        for t in doc.Tables:
            rows = []
            for r in range(1, t.Rows.Count + 1):
                cells = []
                for c in range(1, t.Columns.Count + 1):
                    try:
                        cells.append(t.Cell(r, c).Range.Text.replace("\r\x07", "").replace("\x07", "").strip())
                    except Exception:  # noqa: BLE001
                        cells.append(None)
                rows.append(cells)
            tables.append(rows)
        doc.Close(False)
        out[d["doc_key"]] = {"sha256": d["sha256"], "text": text[:6000], "tables": tables[:8]}
        print(d["doc_key"][-70:], len(text), "tables", len(tables), flush=True)
    except Exception as exc:  # noqa: BLE001
        out[d["doc_key"]] = {"sha256": d["sha256"], "error": str(exc)[:200]}
        print("ERR", d["doc_key"][-60:], exc)
word.Quit()
json.dump(out, open("C:/t/r2x/renders/WORD-TEXT.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
