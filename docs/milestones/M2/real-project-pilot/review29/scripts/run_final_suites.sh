#!/usr/bin/env bash
# After the baseline full suite ends: the full backend suite and the focused suites on the FINAL candidate commit.
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
for k in $(env | grep -o '^AI_EVIDENCE_[A-Z_]*'); do unset $k; done
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
L=/c/t/iso/work/r2x/r29/logs
while [ ! -f $L/FULL-baseline-EXIT.txt ]; do sleep 30; done
cd /c/t/iso/cand-r29/backend
git -C /c/t/iso/cand-r29 rev-parse HEAD > $L/FINAL-candidate-HEAD.txt
git -C /c/t/iso/cand-r29 status --porcelain > $L/FINAL-candidate-status-before.txt
$PY -m pytest -q tests -p no:cacheprovider --junitxml=$L/FULL-final-candidate.xml > $L/FULL-final-candidate.log 2>&1
echo $? > $L/FULL-final-candidate-EXIT.txt
MODS=$(cat $L/FOCUSED-MODULES.txt | sed 's/[^ ]*/tests\/&/g')
$PY -m pytest -q $MODS -p no:cacheprovider --junitxml=$L/FOCUSED-final.xml > $L/FOCUSED-final.log 2>&1
echo $? > $L/FOCUSED-final-EXIT.txt
git -C /c/t/iso/cand-r29 status --porcelain > $L/FINAL-candidate-status-after.txt
