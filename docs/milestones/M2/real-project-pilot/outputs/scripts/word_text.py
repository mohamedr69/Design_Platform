"""The ten sampled .doc transmittals, read with Word itself (COM automation, read-only, from the staged copies) so their
header fields can be labelled from the document text independently of the application's transmittal reader."""
import json, sys, pathlib
import win32com.client

S = pathlib.Path(sys.argv[1]); frozen = json.load(open(S / "FROZEN-SAMPLE.json", encoding="utf-8"))
word = win32com.client.Dispatch("Word.Application"); word.Visible = False; word.DisplayAlerts = 0
out = {}
for d in frozen["documents"]:
    if d["extension"] != ".doc": continue
    key = f"EP-{d['ep']}/{d['relative_path']}"
    try:
        doc = word.Documents.Open(d["staged_path"], ReadOnly=True, AddToRecentFiles=False, Visible=False)
        text = doc.Content.Text; tables = []
        for t in doc.Tables:
            rows = []
            for r in range(1, t.Rows.Count + 1):
                cells = []
                for c in range(1, t.Columns.Count + 1):
                    try: cells.append(t.Cell(r, c).Range.Text.replace("\r\x07", "").replace("\x07", "").strip())
                    except Exception: cells.append(None)
                rows.append(cells)
            tables.append(rows)
        doc.Close(False)
        out[key] = {"text": text[:4000], "tables": tables[:6]}
        print(key[-70:], len(text), "tables", len(tables), flush=True)
    except Exception as exc:  # noqa: BLE001
        out[key] = {"error": str(exc)[:200]}; print("ERR", key[-60:], exc)
word.Quit()
json.dump(out, open(S / "word_text.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
