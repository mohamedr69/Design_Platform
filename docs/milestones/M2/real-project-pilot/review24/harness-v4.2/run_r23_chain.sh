#!/usr/bin/env bash
# Review 23 evidence chain (no model request): lifecycle probes (T1..T5) -> lifecycle regressions -> the eight R22 runner
# scenarios rerun with the v4.1 runner (positive controls) -> runner regressions -> the reviewer's resume-stop probe on v4.1.
set -u
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
H=/c/t/iso/work/r2x/review23/harness-v4.1
L=/c/t/iso/work/r2x/review23/logs
cd "$H" || exit 9
echo "== chain start $(date -u +%FT%TZ)" > "$L/R23-CHAIN.log"
$PY lifecycle_probes.py > "$L/LIFECYCLE-PROBES.log" 2>&1; echo "lifecycle probes exit $?" >> "$L/R23-CHAIN.log"
$PY -m pytest -q test_lifecycle_v4_1.py -p no:cacheprovider --junitxml="$H/logs/LIFECYCLE-V4.1.xml" > "$L/LIFECYCLE-TESTS.log" 2>&1; echo "lifecycle tests exit $? : $(tail -1 "$L/LIFECYCLE-TESTS.log")" >> "$L/R23-CHAIN.log"
PILOT_DRY=1 PILOT_DRY_MODE=coherent $PY runner_probes.py > "$L/RUNNER-PROBES.log" 2>&1; echo "runner probes exit $?" >> "$L/R23-CHAIN.log"
$PY -m pytest -q test_runner_v4.py -p no:cacheprovider --junitxml="$H/logs/RUNNER-V4.xml" > "$L/RUNNER-TESTS.log" 2>&1; echo "runner tests exit $? : $(tail -1 "$L/RUNNER-TESTS.log")" >> "$L/R23-CHAIN.log"
$PY -m pytest -q test_harness_v4.py -p no:cacheprovider --junitxml="$H/logs/HARNESS-V4.xml" > "$L/HARNESS-TESTS.log" 2>&1; echo "harness tests exit $? : $(tail -1 "$L/HARNESS-TESTS.log")" >> "$L/R23-CHAIN.log"
rm -rf /c/t/iso/work/r2x/review23/repro/on-v4.1 /c/t/r2x/dry-runs/r23-repro-v4.1
(cd /c/t/iso/work/r2x/review23/repro && $PY run_stop_probe.py C:/t/iso/work/r2x/review23/harness-v4.1 C:/t/iso/work/r2x/review23/repro/on-v4.1 C:/t/r2x/dry-runs/r23-repro-v4.1 > "$L/STOP-PROBE-on-v4.1.log" 2>&1; echo "reviewer stop probe on v4.1 exit $? : $(tail -1 "$L/STOP-PROBE-on-v4.1.log")" >> "$L/R23-CHAIN.log")
echo "== done $(date -u +%FT%TZ)" >> "$L/R23-CHAIN.log"
