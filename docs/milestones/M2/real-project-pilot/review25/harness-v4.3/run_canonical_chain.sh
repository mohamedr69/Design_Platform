#!/usr/bin/env bash
# The canonical r22 dry chain (review 22): stage -> dry labels -> dry declaration -> A base -> L1..L4 -> L4 resumed on the
# next simulated rolling window (fake clock, dry only) -> v4 scorer; then the eight runner probes. No model request.
set -u
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp PILOT_DRY=1 PILOT_DRY_MODE=coherent
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
H=/c/t/iso/work/r2x/review22/harness-v4
L=$H/logs
D=C:/t/r2x/dry-runs/r22
cd "$H" || exit 9
echo "== chain start $(date -u +%FT%TZ)" > "$L/CANONICAL-CHAIN.log"
rm -rf /c/t/r2x/dry-runs/r22-stage /c/t/r2x/dry-runs/r22
$PY make_dry_stage_r22.py >> "$L/CANONICAL-CHAIN.log" 2>&1; echo "stage exit $?" >> "$L/CANONICAL-CHAIN.log"
$PY dry_labels_r22.py >> "$L/CANONICAL-CHAIN.log" 2>&1; echo "labels exit $?" >> "$L/CANONICAL-CHAIN.log"
$PY declare_r22.py >> "$L/CANONICAL-CHAIN.log" 2>&1; echo "declaration exit $?" >> "$L/CANONICAL-CHAIN.log"
SHA=$(sha256sum /c/t/r2x/dry-runs/r22/R22-DECLARATION.dry.json | cut -d' ' -f1)
echo "$SHA" > /c/t/r2x/dry-runs/r22/DECL.sha
$PY arm_a.py r22dry-A --declaration $D/R22-DECLARATION.dry.json --declaration-sha "$SHA" > "$L/canonical-A.log" 2>&1; echo "A exit $?" >> "$L/CANONICAL-CHAIN.log"
for arm in L1 L2 L3 L4; do
  $PY arm_ev.py r22dry-A r22dry-$arm $arm --declaration $D/R22-DECLARATION.dry.json --declaration-sha "$SHA" > "$L/canonical-$arm.log" 2>&1; echo "$arm exit $?" >> "$L/CANONICAL-CHAIN.log"
done
NOW=$($PY -c "import time;print(time.time()+86401)")
for arm in L1 L2 L3 L4; do
  if grep -q "DEFERRED" "$L/canonical-$arm.log"; then
    XTRACK_FAKE_NOW=$NOW $PY arm_ev.py r22dry-A r22dry-$arm $arm --resume --declaration $D/R22-DECLARATION.dry.json --declaration-sha "$SHA" > "$L/canonical-$arm-resume.log" 2>&1; echo "$arm resume (fake clock +24h+1s) exit $?" >> "$L/CANONICAL-CHAIN.log"
  fi
done
AI_ENABLED=false $PY score_arms_v4.py --declaration $D/R22-DECLARATION.dry.json --declaration-sha "$SHA" --runs $D/runs --tags A=r22dry-A,L1=r22dry-L1,L2=r22dry-L2,L3=r22dry-L3,L4=r22dry-L4 --out $D/score > "$L/canonical-score.log" 2>&1; echo "score exit $?" >> "$L/CANONICAL-CHAIN.log"
echo "== probes start $(date -u +%FT%TZ)" >> "$L/CANONICAL-CHAIN.log"
$PY runner_probes.py > "$L/RUNNER-PROBES.log" 2>&1; echo "exit $?" >> "$L/RUNNER-PROBES.log"; echo "probes exit $(tail -1 "$L/RUNNER-PROBES.log")" >> "$L/CANONICAL-CHAIN.log"
echo "== done $(date -u +%FT%TZ)" >> "$L/CANONICAL-CHAIN.log"
