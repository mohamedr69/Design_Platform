#!/bin/sh
# ORCH-039 evidence runs on the committed implementation, one after the other.
E="G:/dev (2)/dev/ep-platform-merged/wt-m5/docs/milestones/M5/evidence/safe-apply"
PY="G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
cd "G:/dev (2)/dev/ep-platform-merged/wt-m5/backend" || exit 1
rm -f "$E/targeted.start" "$E/targeted.end" "$E/targeted.xml" "$E/targeted.log"
echo "head $(git rev-parse HEAD)" > "$E/runs.txt"
echo "targeted_start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$E/runs.txt"
"$PY" -B -m pytest -p no:cacheprovider --basetemp=C:/t/tmp/m5/bt tests/test_redesign_apply.py tests/test_redesign.py tests/test_drawing_prep.py tests/test_prep_readiness.py --junitxml="$E/targeted.xml" -q > "$E/targeted.log" 2>&1
echo "targeted_exit $?" >> "$E/runs.txt"
echo "targeted_end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$E/runs.txt"
echo "full_start $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$E/runs.txt"
AI_ENABLED=false DATA_ROOT= "$PY" -B -m pytest tests -q -rs -p no:cacheprovider --basetemp=C:/t/tmp/m5/bt --junitxml="$E/full-suite.xml" > "$E/full-suite.log" 2>&1
echo "full_exit $?" >> "$E/runs.txt"
echo "full_end $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$E/runs.txt"
echo done
