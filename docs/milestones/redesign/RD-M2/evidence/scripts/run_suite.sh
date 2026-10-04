#!/bin/sh
# usage: run_suite.sh <base|cand>
R="<SCRATCH>/rdm2"
cd "$R/$1/backend" || exit 2
start=$(date +%s)
PYTHONDONTWRITEBYTECODE=1 "<PC-B user profile>/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe" -m pytest -p no:cacheprovider -q -rfEs \
  --deselect tests/test_ifc_boq.py::test_real_dwg_converts_to_the_same_symbols_as_a_hand_saved_dxf \
  --junitxml="$R/work/tests/junit-$1.xml" > "$R/work/tests/full-$1.txt" 2>&1
echo "exit=$? seconds=$(( $(date +%s) - start ))" >> "$R/work/tests/full-$1.txt"
