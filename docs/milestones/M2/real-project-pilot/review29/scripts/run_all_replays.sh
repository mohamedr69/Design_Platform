#!/usr/bin/env bash
# All offline replays (no model request): per arm, the flags-off replay with its fidelity check, then each switch set;
# then the changed-fact analysis under evaluators .9 and .10.
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
cd /c/t/iso/work/r2x/r29
for a in L1 L2 L3 L4; do
  $PY replay_arm.py $a off > logs/replay-$a-off.log 2>&1; echo "replay $a off exit $?" >> logs/replay-all.status
  $PY compare_fidelity.py $a >> logs/replay-all.status 2>&1
  for c in IG CA DR PA ALL; do
    $PY replay_arm.py $a $c > logs/replay-$a-$c.log 2>&1; echo "replay $a $c exit $? $(tail -1 logs/replay-$a-$c.log | grep -o '{"served.*')" >> logs/replay-all.status
  done
done
$PY analyze_replays.py > logs/ANALYSIS.log 2>&1; echo "analysis exit $?" >> logs/replay-all.status
echo done >> logs/replay-all.status
