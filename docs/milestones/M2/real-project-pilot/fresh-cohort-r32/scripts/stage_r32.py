"""Step 5: copy the frozen pool (FROZEN-SELECTION.json) into the isolated staging area C:/t/r2x/r32-stage/files/<pool id>.pdf.
The OneDrive original is only READ (which downloads an online-only placeholder, as authorised): it is never edited,
renamed, moved or written beside. The bytes are hashed while they are read; the staged copy is re-hashed after writing;
the original's size and modified time are compared before and after. A file that cannot be read is recorded as
'failed' with its error (kept in the accounting, never dropped). Usage: stage_r32.py [pool|extension-1|extension-2]
Writes SOURCE-MANIFEST.json (or SOURCE-MANIFEST.<extension>.json)."""
import datetime
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
part = sys.argv[1] if len(sys.argv) > 1 else "pool"
SEL = json.loads((HERE / "FROZEN-SELECTION.json").read_text(encoding="utf-8"))
items = SEL["pool"] if part == "pool" else json.loads((HERE / f"FROZEN-{part.upper()}.json").read_text(encoding="utf-8"))["documents"]
STAGE = pathlib.Path("C:/t/r2x/r32-stage/files")
STAGE.mkdir(parents=True, exist_ok=True)
OUT = HERE / ("SOURCE-MANIFEST.json" if part == "pool" else f"SOURCE-MANIFEST.{part}.json")
if OUT.exists():
    raise SystemExit(f"{OUT.name} exists: staging is never repeated in place")
LONG = "\\\\?\\"
rows = []
for it in items:
    src = LONG + SEL["project_folders"][it["ep"]] + "\\" + it["relative_path"].replace("/", "\\")
    dst = STAGE / f"{it['pool_id']}.pdf"
    rec = {"pool_id": it["pool_id"], "ep": it["ep"], "relative_path": it["relative_path"], "selected_size": it["size"], "selected_modified_utc": it["modified_utc"]}
    try:
        if dst.exists():
            raise RuntimeError("staged file already exists")
        before = os.stat(src)
        h = hashlib.sha256()
        n = 0
        with open(src, "rb") as f, open(dst, "xb") as g:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
                g.write(chunk)
                n += len(chunk)
        after = os.stat(src)
        staged = hashlib.sha256(dst.read_bytes()).hexdigest()
        rec |= {"state": "staged", "source_sha256": h.hexdigest(), "staged_sha256": staged, "bytes": n, "staged_path": str(dst),
                "source_unchanged": (before.st_size, before.st_mtime) == (after.st_size, after.st_mtime) == (it["size"], before.st_mtime),
                "size_matches_selection": n == it["size"],
                "source_modified_utc": datetime.datetime.fromtimestamp(after.st_mtime, datetime.timezone.utc).isoformat(timespec="seconds"),
                "staged_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
        assert staged == rec["source_sha256"]
    except Exception as e:  # noqa: BLE001 -- recorded, never dropped
        rec |= {"state": "failed", "error": f"{type(e).__name__}: {e}"}
    rows.append(rec)
    print(rec["pool_id"], rec["state"], rec.get("bytes"), rec.get("error", ""), flush=True)
out = {"part": part, "stage_dir": str(STAGE), "selection_sha256": hashlib.sha256((HERE / "FROZEN-SELECTION.json").read_bytes()).hexdigest(),
       "staged": sum(r["state"] == "staged" for r in rows), "failed": sum(r["state"] == "failed" for r in rows), "files": rows}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("staged", out["staged"], "failed", out["failed"], hashlib.sha256(OUT.read_bytes()).hexdigest())
