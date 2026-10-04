#!/usr/bin/env bash
# re-run every replay on the final candidate commit (wall-clock job limit lifted in the replay sandbox); old outputs removed by literal paths
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
cd /c/t/iso/work/r2x/r29
git -C /c/t/iso/cand-r29 rev-parse HEAD > logs/REPLAY-CANDIDATE-HEAD.txt
rm -rf /c/t/r2x/r29-replay/L1-off
rm -rf /c/t/r2x/r29-replay/L1-IG
rm -rf /c/t/r2x/r29-replay/L1-CA
rm -rf /c/t/r2x/r29-replay/L1-DR
rm -rf /c/t/r2x/r29-replay/L1-PA
rm -rf /c/t/r2x/r29-replay/L1-ALL
rm -rf /c/t/r2x/r29-replay/L2-off
rm -rf /c/t/r2x/r29-replay/L2-IG
rm -rf /c/t/r2x/r29-replay/L2-CA
rm -rf /c/t/r2x/r29-replay/L2-DR
rm -rf /c/t/r2x/r29-replay/L2-PA
rm -rf /c/t/r2x/r29-replay/L2-ALL
rm -rf /c/t/r2x/r29-replay/L3-off
rm -rf /c/t/r2x/r29-replay/L3-IG
rm -rf /c/t/r2x/r29-replay/L3-CA
rm -rf /c/t/r2x/r29-replay/L3-DR
rm -rf /c/t/r2x/r29-replay/L3-PA
rm -rf /c/t/r2x/r29-replay/L3-ALL
rm -rf /c/t/r2x/r29-replay/L4-off
rm -rf /c/t/r2x/r29-replay/L4-IG
rm -rf /c/t/r2x/r29-replay/L4-CA
rm -rf /c/t/r2x/r29-replay/L4-DR
rm -rf /c/t/r2x/r29-replay/L4-PA
rm -rf /c/t/r2x/r29-replay/L4-ALL
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/ALL-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/CA-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/DR-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/IG-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/off-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/PA-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L1.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L1.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L2.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L2.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L3.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L3.e9.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L4.e10.json
rm -f /c/t/iso/work/r2x/r29/scores/stored-L4.e9.json
rm -f /c/t/iso/work/r2x/r29/logs/replay-all.status
bash /c/t/iso/work/r2x/r29/run_all_replays.sh
$PY new_acceptances.py > logs/NEW-ACCEPTANCES.log 2>&1
echo final-done >> logs/replay-all.status
