"""Freeze of the Review 15 corrected harness (r15.1). Hashes every r15 module, script and test (the development patch
helpers under dev/ are recorded separately), records identities, and checks the accepted application tree."""
import datetime
import hashlib
import json
import pathlib
import subprocess
import sys

H = pathlib.Path("C:/t/iso/work/r2x/r15")
sys.path.insert(0, str(H))
import boq_contract, boq_harness, overlay  # noqa: E402

head = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
assert head == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not dirty
app_files = ["backend/app/ai/evidence_reader.py", "backend/app/ai/budget.py", "backend/app/ai/ledger.py", "backend/app/ai/provider.py",
             "backend/scripts/m2_eval5.py", "backend/scripts/m2_eval4.py", "backend/scripts/m2_boq_eval.py", "backend/app/services/design_sheet_extractor.py",
             "backend/app/services/document_control.py"]
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
files = sorted([p for p in H.glob("*.py") if p.name != "freeze_r15.py"] + list((H / "tests").glob("*.py")))
out = {"frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "application_baseline": {"commit": head, "clean": True, "changed": False, "source_sha256": {f: sha(pathlib.Path("C:/t/iso/frozen-r12") / f) for f in app_files}},
       "identities": {"boq_contract": boq_contract.CONTRACT_VERSION, "boq_harness": boq_harness.HARNESS_VERSION, "overlay": overlay.OVERLAY_VERSION,
                      "evaluator": "m2-pilot-eval-2026-09-29.9 (unchanged)", "labels": "r14.1 (unchanged) + r15.1 explicit states"},
       "files_sha256": {p.relative_to(H).as_posix(): sha(p) for p in files},
       "dev_helpers_not_part_of_the_harness": {p.relative_to(H).as_posix(): sha(p) for p in sorted((H / "dev").glob("*"))}}
p = H / "FREEZE-R15.json"
assert not p.exists(), "already frozen"
p.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(len(files), "files frozen; sha256", sha(p))
