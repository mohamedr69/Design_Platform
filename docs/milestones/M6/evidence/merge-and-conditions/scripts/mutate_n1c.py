"""ORCH-049 C2: the N1c mutation (ORCH-048) must now be caught. Mutates
document_attribution.py in the wt-m6b worktree, runs the C2 tests and the
M6 suite, restores the file byte-for-byte and checks it."""
import hashlib
import json
import os
import pathlib
import subprocess

WT = pathlib.Path("G:/dev (2)/dev/ep-platform-merged/wt-m6b/backend")
PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
ATT = WT / "app/services/document_attribution.py"
OLD = b'_claim(claims, external, "type", "an issued-for-construction drawing: given to us")'
NEW = b'_claim(claims, Attribution.OUR_SCOPE, "type", "an issued-for-construction drawing: given to us")'

original = ATT.read_bytes()
before = hashlib.sha256(original).hexdigest()
assert original.count(OLD) == 1
env = {**os.environ, "TEMP": "C:/t/tmp/m6b/tmp", "TMP": "C:/t/tmp/m6b/tmp"}
try:
    ATT.write_bytes(original.replace(OLD, NEW))
    proc = subprocess.run([PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "--basetemp=C:/t/tmp/m6b/bt", "-q",
                           "-k", "ifc", "tests/test_m6_merge_conditions.py", "tests/test_m6_attribution.py"],
                          cwd=WT, capture_output=True, text=True, env=env)
finally:
    ATT.write_bytes(original)
after = hashlib.sha256(ATT.read_bytes()).hexdigest()
failed = [line.split(" ")[1] for line in proc.stdout.splitlines() if line.startswith("FAILED ")]
summary = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line][-1:]
result = {"mutation": "N1c_our_scope_from_ifc_type_model_answer", "rc": proc.returncode, "failed": failed,
          "summary": summary, "restored_sha256_equal": before == after, "sha256": before}
pathlib.Path("C:/t/tmp/m6b/out/mutation-n1c.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print(json.dumps(result, indent=1))
