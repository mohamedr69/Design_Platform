# DERIVED from ai-accuracy-pilot/pilot_shares.py by derive_runners.py -- per-arm shares for the continuation's document arms (S, T2)
"""AI accuracy pilot: freeze each project's per-arm share of the cross-track day allowance after the A base and before
S (declared rule): share(ep) = floor((60 - used(ep)) / 3), the same for S, G and T. Written once; never rewritten.

Usage: pilot_shares.py <A_tag> --declaration PILOT-DECLARATION.json --declaration-sha SHA"""
import argparse
import datetime
import hashlib
import json
import pathlib
import sys

a = argparse.ArgumentParser()
a.add_argument("a_tag"); a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
args = a.parse_args()
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
sys.path.insert(0, "C:/t/iso/work/r2x/ai-pilot")
import dry_provider as dry  # noqa: E402

RUNS = pathlib.Path(dry.DRY_RUNS if dry.DRY else "C:/t/r2x/runs")
run = json.loads((RUNS / args.a_tag / "out/RUN.json").read_text(encoding="utf-8"))
assert run["track"] == "A" and run["declaration_sha256"] == args.declaration_sha
sys.path.insert(0, "C:/t/iso/work/r2x/run")
import xtrack  # noqa: E402

if dry.DRY:
    xtrack.PATH = dry.DRY_XTRACK

LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
eps = sorted(e[3:] for e in run["projects"])
used = {ep: xtrack.used(ep) for ep in eps}
out = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "declaration_sha256": args.declaration_sha, "a_tag": args.a_tag,
       "rule": "share(ep) = floor((60 - used(ep)) / n_arms), for each document arm", "arms": sorted(decl["doc_arms"]), "used_after_A": used,
       "shares": {ep: (LIMIT - n) // len(decl["doc_arms"]) for ep, n in used.items()}}
p = (RUNS / "CONT-SHARES.json") if dry.DRY else pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/CONT-SHARES.json")
if p.exists():
    sys.exit("the shares are frozen")
p.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(out["shares"], "sha256", hashlib.sha256(p.read_bytes()).hexdigest())
