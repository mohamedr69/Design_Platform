"""ORCH-08C (R39HARNESS-IMPL; review38's make_diffs_r38.py with the r39 paths): the harness diff review38 -> review39 and the
per-file hash table.

Usage: make_diffs_r39.py <patch out> <json out>
Reads r39/harness-r38-base (the byte copy of PILOT/review38/scripts/harness-r32, checked against the review38 manifest)
and r39/harness-r32 (the r39 harness); writes a unified diff of every changed or new file and a JSON table
{file: {status, review38_sha256, r39_sha256, lines_added, lines_removed}}. Read-only on both harness folders."""
import difflib
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
BASE = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r38-base")
NEW = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32")
MANIFEST = (PILOT / "review38" / "evidence" / "EVIDENCE-MANIFEST.json", "07c2fb78bedc44c4145f8ff24f2f9c4e4407de4adc2706392b2560afe56b8ce9")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(patch_out, json_out):
    raw = MANIFEST[0].read_bytes()
    if sha(raw) != MANIFEST[1]:
        raise SystemExit("PACKET MISMATCH: review38 manifest")
    man = json.loads(raw.decode("utf-8"))["files"]
    table, patch = {}, []
    for p in sorted(BASE.iterdir()):
        want = man[f"scripts/harness-r32/{p.name}"]["sha256"]
        if sha(p.read_bytes()) != want:
            raise SystemExit(f"PACKET MISMATCH: base copy {p.name}")
    names = sorted({p.name for p in BASE.iterdir()} | {p.name for p in NEW.iterdir()})
    for n in names:
        a = (BASE / n).read_bytes() if (BASE / n).exists() else None
        b = (NEW / n).read_bytes() if (NEW / n).exists() else None
        status = "unchanged" if a == b else "changed" if a and b else "new" if b else "removed"
        rec = {"status": status, "review38_sha256": sha(a) if a else None, "r39_sha256": sha(b) if b else None}
        if status != "unchanged":
            d = list(difflib.unified_diff((a or b"").decode("utf-8").splitlines(), (b or b"").decode("utf-8").splitlines(),
                                          fromfile=f"review38/scripts/harness-r32/{n}" if a else "/dev/null", tofile=f"review39/scripts/harness-r32/{n}",
                                          lineterm=""))
            rec["lines_added"] = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
            rec["lines_removed"] = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
            patch += d
        table[n] = rec
    pathlib.Path(patch_out).write_text("\n".join(patch) + "\n", encoding="utf-8", newline="\n")
    pathlib.Path(json_out).write_text(json.dumps({"base": BASE.as_posix(), "new": NEW.as_posix(), "review38_manifest_sha256": MANIFEST[1], "files": table},
                                                 sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({s: sum(1 for v in table.values() if v["status"] == s) for s in ("unchanged", "changed", "new", "removed")}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
