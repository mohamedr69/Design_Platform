#!/usr/bin/env bash
# The accepted baseline's full suite again, after the final candidate suites end: the first baseline run stalled
# (three tests near 7,200 s each, then a 401 and a KeyError after the stall); that run is kept as disclosed evidence.
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
for k in $(env | grep -o '^AI_EVIDENCE_[A-Z_]*'); do unset $k; done
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
L=/c/t/iso/work/r2x/r29/logs
while [ ! -f $L/FOCUSED-final-EXIT.txt ]; do sleep 30; done
cd /c/t/iso/frozen-r12/backend
git -C /c/t/iso/frozen-r12 rev-parse HEAD > $L/FULL-baseline-rerun-HEAD.txt
git -C /c/t/iso/frozen-r12 status --porcelain > $L/FULL-baseline-rerun-status-before.txt
$PY -m pytest -q tests -p no:cacheprovider --junitxml=$L/FULL-baseline-rerun.xml > $L/FULL-baseline-rerun.log 2>&1
echo $? > $L/FULL-baseline-rerun-EXIT.txt
git -C /c/t/iso/frozen-r12 status --porcelain > $L/FULL-baseline-rerun-status-after.txt
