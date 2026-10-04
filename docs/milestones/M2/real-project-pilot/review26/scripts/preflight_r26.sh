#!/usr/bin/env bash
# Scripted-provider preflight of the FINAL binding (no model / provider request; PILOT_DRY=1 redirects runs, ledger,
# rolling counter and allowance into a NEW disposable root C:/t/r2x/dry-runs/r26-preflight). Runs the reviewed v4.3
# runners over the real frozen R21 stage (hash-checked staged copies of the authorized, non-sealed sample) and the v4
# scorer against the frozen R26 labels.
set -u
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp PILOT_DRY=1 PILOT_DRY_MODE=coherent PILOT_DRY_ROOT=C:/t/r2x/dry-runs/r26-preflight
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
H=/c/t/iso/work/r2x/review25/harness-v4.3
W=/c/t/iso/work/r2x/r26
L=$W/preflight
D=C:/t/r2x/dry-runs/r26-preflight
test -e /c/t/r2x/dry-runs/r26-preflight && { echo "preflight root exists: refusing to reuse"; exit 9; }
mkdir -p "$L"
echo "== preflight start $(date -u +%FT%TZ)" > "$L/PREFLIGHT.log"
$PY $W/declare_final.py > "$L/declare-dry.log" 2>&1; echo "dry declaration exit $?" >> "$L/PREFLIGHT.log"
SHA=$(sha256sum /c/t/r2x/dry-runs/r26-preflight/FINAL-DECLARATION.dry.json | cut -d' ' -f1); echo "$SHA" > "$L/DRY-DECL.sha"
cd "$H" || exit 9
$PY arm_a.py r26dry-A --declaration $D/FINAL-DECLARATION.dry.json --declaration-sha "$SHA" > "$L/A.log" 2>&1; echo "A exit $?" >> "$L/PREFLIGHT.log"
for arm in L1 L2 L3 L4; do
  $PY arm_ev.py r26dry-A r26dry-$arm $arm --declaration $D/FINAL-DECLARATION.dry.json --declaration-sha "$SHA" > "$L/$arm.log" 2>&1; echo "$arm exit $?" >> "$L/PREFLIGHT.log"
done
AI_ENABLED=false $PY score_arms_v4.py --declaration $D/FINAL-DECLARATION.dry.json --declaration-sha "$SHA" --runs $D/runs --tags A=r26dry-A,L1=r26dry-L1,L2=r26dry-L2,L3=r26dry-L3,L4=r26dry-L4 --out $W/preflight/score > "$L/score.log" 2>&1; echo "score exit $?" >> "$L/PREFLIGHT.log"
echo "== done $(date -u +%FT%TZ)" >> "$L/PREFLIGHT.log"
