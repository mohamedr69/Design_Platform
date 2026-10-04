#!/usr/bin/env bash
# The full backend suite once on the frozen candidate (flags off) and once on the accepted baseline 3d5607d, for a
# by-name-and-message comparison of failures. No model request (the suites use scripted providers).
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
for k in $(env | grep -o '^AI_EVIDENCE_[A-Z_]*'); do unset $k; done
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
L=/c/t/iso/work/r2x/r29/logs
cd /c/t/iso/cand-r29/backend
git -C /c/t/iso/cand-r29 rev-parse HEAD > $L/FULL-candidate-HEAD.txt
$PY -m pytest -q tests -p no:cacheprovider --junitxml=$L/FULL-candidate.xml > $L/FULL-candidate.log 2>&1
echo $? > $L/FULL-candidate-EXIT.txt
cd /c/t/iso/frozen-r12/backend
git -C /c/t/iso/frozen-r12 rev-parse HEAD > $L/FULL-baseline-HEAD.txt
$PY -m pytest -q tests -p no:cacheprovider --junitxml=$L/FULL-baseline.xml > $L/FULL-baseline.log 2>&1
echo $? > $L/FULL-baseline-EXIT.txt
git -C /c/t/iso/frozen-r12 status --porcelain > $L/FULL-baseline-status-after.txt
git -C /c/t/iso/cand-r29 status --porcelain > $L/FULL-candidate-status-after.txt
