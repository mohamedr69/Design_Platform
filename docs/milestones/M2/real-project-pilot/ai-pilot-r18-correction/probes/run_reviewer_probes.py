"""Run the Review 18 reviewer probes (reviewer-copy/targeted_probes.py, byte copy, sha256 bb79664f...) unchanged in logic
against a chosen candidate tree, writing into THIS package (never the reviewer's folder). Exactly two textual
substitutions are made before execution, and both are recorded in the output:
  1. sys.path 'C:/t/iso/cand-ai/backend'  -> <tree>/backend
  2. R=Path(__file__).parent              -> R=Path(<out_dir>)
Usage: run_reviewer_probes.py <tree> <out_dir>"""
import hashlib
import json
import os
import pathlib
import sys

tree, out_dir = sys.argv[1], pathlib.Path(sys.argv[2])
src_path = pathlib.Path(__file__).parent / "reviewer-copy/targeted_probes.py"
src = src_path.read_text(encoding="utf-8")
assert hashlib.sha256(src_path.read_bytes()).hexdigest() == "bb79664f8c31927892278a7f8c8a2a06707e7be8e4cd29add6c541851b63a5b5"
subs = [("'C:/t/iso/cand-ai/backend'", repr(f"{tree}/backend")), ("R=Path(__file__).parent", f"R=Path({str(out_dir)!r})")]
for a, b in subs:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
out_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("AI_ENABLED", "false")
os.chdir(f"{tree}/backend")
exec(compile(src, str(src_path), "exec"), {"__name__": "__main__", "__file__": str(src_path)})
(out_dir / "PROBE-RUN.json").write_text(json.dumps({"reviewer_source_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(), "tree": tree,
                                                    "substitutions": subs, "output": "TARGETED-PROBES.json"}, indent=1) + "\n", encoding="utf-8")
