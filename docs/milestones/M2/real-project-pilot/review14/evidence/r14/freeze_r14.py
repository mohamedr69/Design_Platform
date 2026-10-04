"""Freeze of the corrected Round 2 evaluation harness (Review 14 correction). Hashes every harness / evaluator / helper
file and records their version identities; the accepted application tree is unchanged (commit and cleanliness checked)."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

H = pathlib.Path("C:/t/iso/work/r2x/r14")
sys.path.insert(0, str(H))
import boq_contract, boq_harness, overlay  # noqa: E402

head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
assert head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty
files = sorted([p for p in H.glob("*.py") if p.name != "freeze_r14.py"] + list((H / "tests").glob("*.py")))
out = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "application_baseline": {"commit": head, "clean": True, "changed": False},
       "identities": {"boq_contract": boq_contract.CONTRACT_VERSION, "boq_harness": boq_harness.HARNESS_VERSION, "overlay": overlay.OVERLAY_VERSION,
                      "evaluator": "m2-pilot-eval-2026-09-29.9 (unchanged)", "labels": "r14.1"},
       "files_sha256": {p.relative_to(H).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
p = H / "FREEZE-R14.json"
assert not p.exists(), "already frozen"
p.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(len(files), "files frozen; sha256", hashlib.sha256(p.read_bytes()).hexdigest())
