"""Freeze of the Review 16 corrected harness (r16.1): hashes of every module / script / test / probe copy, the
identities, and the accepted application's source hashes (tree clean at 3d5607d)."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

H = pathlib.Path("C:/t/iso/work/r2x/r16")
sys.path.insert(0, str(H))
import boq_contract, boq_harness, overlay, replay_core  # noqa: E402

head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
assert head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty
app_files = ["backend/app/ai/evidence_reader.py", "backend/app/ai/budget.py", "backend/app/ai/ledger.py", "backend/app/ai/provider.py",
             "backend/scripts/m2_eval5.py", "backend/scripts/m2_eval4.py", "backend/scripts/m2_boq_eval.py", "backend/app/services/design_sheet_extractor.py",
             "backend/app/services/document_control.py"]
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
files = sorted([p for p in H.glob("*.py") if p.name != "freeze_r16.py"] + list((H / "tests").glob("*.py")) + list((H / "probes").glob("*.py")) + list((H / "dev").glob("*")))
out = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "status": "IMPLEMENTATION FROZEN -- VALIDATION / PACKAGING PENDING",
       "application_baseline": {"commit": head, "clean": True, "changed": False, "source_sha256": {f: sha(pathlib.Path("C:/t/iso/frozen-r12") / f) for f in app_files}},
       "identities": {"boq_contract": boq_contract.CONTRACT_VERSION, "boq_harness": boq_harness.HARNESS_VERSION, "overlay": overlay.OVERLAY_VERSION,
                      "replay_core": replay_core.REPLAY_CORE_VERSION, "evaluator": "m2-pilot-eval-2026-09-29.9 (unchanged)"},
       "unchanged_from_r15": {m: sha(H / m) == sha(pathlib.Path("C:/t/iso/work/r2x/r15") / m) for m in ("boq_harness.py", "overlay.py")},
       "files_sha256": {p.relative_to(H).as_posix(): sha(p) for p in files}}
p = H / "FREEZE-R16.json"
assert not p.exists(), "already frozen"
p.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(len(files), "files frozen; unchanged from r15:", out["unchanged_from_r15"], "; sha256", sha(p))
