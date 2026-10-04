#!/usr/bin/env bash
# Review 24 evidence chain (no model request), run AFTER the freeze (bindings_r24.py): journal unit tests -> lifecycle probes
# (critical T1..T5b and provider T4/T4b, rerun with v4.2) + regressions -> the eight R22 runner controls + regressions ->
# the provider boundary matrix P1..P6 + regressions (which also read the controls' journals) -> scorer tests -> the
# reviewer's provider-boundary probe on v4.2 (fresh stage + root).
set -u
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
H=/c/t/iso/work/r2x/review24/harness-v4.2
L=/c/t/iso/work/r2x/review24/logs
cd "$H" || exit 9
mkdir -p "$H/logs"
echo "== chain start $(date -u +%FT%TZ)" > "$L/R24-CHAIN.log"
$PY -m pytest -q test_provider_journal.py -p no:cacheprovider --junitxml="$H/logs/PROVIDER-JOURNAL.xml" > "$L/PROVIDER-JOURNAL-TESTS.log" 2>&1; echo "journal unit tests exit $? : $(tail -1 "$L/PROVIDER-JOURNAL-TESTS.log")" >> "$L/R24-CHAIN.log"
$PY lifecycle_probes.py > "$L/LIFECYCLE-PROBES.log" 2>&1; echo "lifecycle probes exit $?" >> "$L/R24-CHAIN.log"
$PY -m pytest -q test_lifecycle_v4_1.py -p no:cacheprovider --junitxml="$H/logs/LIFECYCLE-V4.1.xml" > "$L/LIFECYCLE-TESTS.log" 2>&1; echo "lifecycle tests exit $? : $(tail -1 "$L/LIFECYCLE-TESTS.log")" >> "$L/R24-CHAIN.log"
PILOT_DRY=1 PILOT_DRY_MODE=coherent $PY runner_probes.py > "$L/RUNNER-PROBES.log" 2>&1; echo "runner probes exit $?" >> "$L/R24-CHAIN.log"
$PY -m pytest -q test_runner_v4.py -p no:cacheprovider --junitxml="$H/logs/RUNNER-V4.xml" > "$L/RUNNER-TESTS.log" 2>&1; echo "runner tests exit $? : $(tail -1 "$L/RUNNER-TESTS.log")" >> "$L/R24-CHAIN.log"
$PY provider_boundary_probes.py > "$L/BOUNDARY-PROBES.log" 2>&1; echo "boundary probes exit $?" >> "$L/R24-CHAIN.log"
$PY -m pytest -q test_boundary_v4_2.py -p no:cacheprovider --junitxml="$H/logs/BOUNDARY-V4.2.xml" > "$L/BOUNDARY-TESTS.log" 2>&1; echo "boundary tests exit $? : $(tail -1 "$L/BOUNDARY-TESTS.log")" >> "$L/R24-CHAIN.log"
$PY -m pytest -q test_harness_v4.py -p no:cacheprovider --junitxml="$H/logs/HARNESS-V4.xml" > "$L/HARNESS-TESTS.log" 2>&1; echo "scorer tests exit $? : $(tail -1 "$L/HARNESS-TESTS.log")" >> "$L/R24-CHAIN.log"
(cd /c/t/iso/work/r2x/review24/repro && $PY run_provider_probe.py C:/t/iso/work/r2x/review24/harness-v4.2 C:/t/iso/work/r2x/review24/repro/on-v4.2 C:/t/r2x/dry-runs/r24-repro-v4.2 > "$L/PROVIDER-PROBE-on-v4.2.log" 2>&1; echo "reviewer provider probe on v4.2 exit $? : $(tail -1 "$L/PROVIDER-PROBE-on-v4.2.log")" >> "$L/R24-CHAIN.log")
echo "== done $(date -u +%FT%TZ)" >> "$L/R24-CHAIN.log"
