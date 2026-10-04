"""ORCH-08 (R38HARNESS-IMPL): the harness diff review36 -> review38 and the per-file hash table.

Usage: make_diffs_r38.py <patch out> <json out>
Reads r38/harness-r36-base (the byte copy of PILOT/review36/scripts/harness-r32, checked against the review36 manifest)
and r38/harness-r32 (the r38 harness); writes a unified diff of every changed or new file and a JSON table
{file: {status, review36_sha256, r38_sha256, lines_added, lines_removed}}. Read-only on both harness folders."""
import difflib
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
BASE = pathlib.Path("C:/t/iso/work/r2x/r38/harness-r36-base")
NEW = pathlib.Path("C:/t/iso/work/r2x/r38/harness-r32")
MANIFEST = (PILOT / "review36" / "evidence" / "EVIDENCE-MANIFEST.json", "5e9508136663a1dac096bcc697345a527726705ad6c96e46c52839371c9de9d0")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main(patch_out, json_out):
    raw = MANIFEST[0].read_bytes()
    if sha(raw) != MANIFEST[1]:
        raise SystemExit("PACKET MISMATCH: review36 manifest")
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
        rec = {"status": status, "review36_sha256": sha(a) if a else None, "r38_sha256": sha(b) if b else None}
        if status != "unchanged":
            d = list(difflib.unified_diff((a or b"").decode("utf-8").splitlines(), (b or b"").decode("utf-8").splitlines(),
                                          fromfile=f"review36/scripts/harness-r32/{n}" if a else "/dev/null", tofile=f"review38/scripts/harness-r32/{n}",
                                          lineterm=""))
            rec["lines_added"] = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
            rec["lines_removed"] = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
            patch += d
        table[n] = rec
    pathlib.Path(patch_out).write_text("\n".join(patch) + "\n", encoding="utf-8", newline="\n")
    pathlib.Path(json_out).write_text(json.dumps({"base": BASE.as_posix(), "new": NEW.as_posix(), "review36_manifest_sha256": MANIFEST[1], "files": table},
                                                 sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({s: sum(1 for v in table.values() if v["status"] == s) for s in ("unchanged", "changed", "new", "removed")}))


if __name__ == "__main__":
    main(*sys.argv[1:3])
