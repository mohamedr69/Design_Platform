#!/usr/bin/env bash
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
for k in $(env | grep -o '^AI_EVIDENCE_[A-Z_]*'); do unset $k; done
cd /c/t/iso/cand-r29/backend
MODS=$(cat /c/t/iso/work/r2x/r29/logs/FOCUSED-MODULES.txt | sed 's/[^ ]*/tests\/&/g')
/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python -m pytest -q $MODS -p no:cacheprovider --junitxml=/c/t/iso/work/r2x/r29/logs/FOCUSED.xml > /c/t/iso/work/r2x/r29/logs/FOCUSED.log 2>&1
echo $? > /c/t/iso/work/r2x/r29/logs/FOCUSED-EXIT.txt
