"""Parse the TrueView Core Console's LIST output into entities.

usage: python listparse.py <list log> <out json>
Each entity block starts with a line naming its type and layer
("BLOCK REFERENCE  Layer: ..."); the handle, space, block name and
insertion point follow."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

HEAD = re.compile(r"^\s*([A-Z][A-Z0-9 ]+?)\s+Layer:\s*\"?(.*?)\"?\s*$")


def parse(text: str) -> list[dict]:
    ents: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        m = HEAD.match(line)
        if m:
            cur = {"type": m.group(1).strip(), "layer": m.group(2).strip()}
            ents.append(cur)
            continue
        if cur is None:
            continue
        if "Handle =" in line:
            cur["handle"] = line.split("Handle =")[1].strip().upper()
        if "Space:" in line:
            cur["space"] = line.split("Space:")[1].strip()
        bm = re.search(r'Block Name:\s*"(.*?)"', line)
        if bm:
            cur["block"] = bm.group(1)
        pm = re.search(r"at point,\s*X=\s*([-0-9.Ee+]+)\s+Y=\s*([-0-9.Ee+]+)", line)
        if pm and "x" not in cur:
            cur["x"], cur["y"] = float(pm.group(1)), float(pm.group(2))
    return ents


def main() -> None:
    text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    ents = parse(text)
    summary = {"entities": len(ents), "by_type": Counter(e["type"] for e in ents),
               "with_handle": sum(1 for e in ents if e.get("handle")),
               "inserts_by_block": Counter(e.get("block") for e in ents if e["type"] == "BLOCK REFERENCE"),
               "spaces": Counter(e.get("space") for e in ents)}
    Path(sys.argv[2]).write_text(json.dumps({"summary": summary, "entities": ents}, indent=0), encoding="utf-8")
    print(json.dumps(summary, indent=1)[:4000])


if __name__ == "__main__":
    main()
