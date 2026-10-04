#!/usr/bin/env bash
# Review 25 evidence chain (no model request), run AFTER the freeze (bindings_r25.py):
#  1. evidence for the submitted 62-test set on the frozen successor: lifecycle probes, runner probes, boundary probes
#  2. the submitted 62-test set in ONE pytest run (journal 23, scorer 19, runner 8, lifecycle 5, boundary 7)
#  3. R25-01: the mutation probes (control + three mutations), the legacy recheck and the new regressions
#  4. the reviewer's neutral-kind probe + regressions on v4.3, and the original R24 before/after-stop-file probe on v4.3
set -u
export PYTHONIOENCODING=utf-8 TEMP=C:/t/iso/tmp TMP=C:/t/iso/tmp
PY=/c/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python
H=/c/t/iso/work/r2x/review25/harness-v4.3
L=/c/t/iso/work/r2x/review25/logs
cd "$H" || exit 9
mkdir -p "$H/logs"
echo "== chain start $(date -u +%FT%TZ)" > "$L/R25-CHAIN.log"
$PY lifecycle_probes.py > "$L/LIFECYCLE-PROBES.log" 2>&1; echo "lifecycle probes exit $?" >> "$L/R25-CHAIN.log"
PILOT_DRY=1 PILOT_DRY_MODE=coherent $PY runner_probes.py > "$L/RUNNER-PROBES.log" 2>&1; echo "runner probes exit $?" >> "$L/R25-CHAIN.log"
$PY provider_boundary_probes.py > "$L/BOUNDARY-PROBES.log" 2>&1; echo "boundary probes exit $?" >> "$L/R25-CHAIN.log"
$PY -m pytest -q test_provider_journal.py test_harness_v4.py test_runner_v4.py test_lifecycle_v4_1.py test_boundary_v4_2.py -p no:cacheprovider --junitxml="$H/logs/SUBMITTED-62.xml" > "$L/SUBMITTED-62.log" 2>&1; rc=$?; echo "$rc" > "$L/SUBMITTED-62.exit"; echo "submitted 62-test set pytest exit $rc : $(tail -1 "$L/SUBMITTED-62.log")" >> "$L/R25-CHAIN.log"
$PY neutral_mutation_probes.py > "$L/NEUTRAL-PROBES.log" 2>&1; echo "neutral mutation probes exit $?" >> "$L/R25-CHAIN.log"
$PY legacy_journal_recheck.py > "$L/LEGACY-RECHECK.log" 2>&1; echo "legacy recheck exit $? : $(tail -1 "$L/LEGACY-RECHECK.log")" >> "$L/R25-CHAIN.log"
$PY -m pytest -q test_neutral_v4_3.py -p no:cacheprovider --junitxml="$H/logs/NEUTRAL-V4.3.xml" > "$L/NEUTRAL-TESTS.log" 2>&1; rc=$?; echo "$rc" > "$L/NEUTRAL-TESTS.exit"; echo "R25 regressions pytest exit $rc : $(tail -1 "$L/NEUTRAL-TESTS.log")" >> "$L/R25-CHAIN.log"
(cd /c/t/iso/work/r2x/review25/repro && $PY run_neutral_probe.py C:/t/iso/work/r2x/review25/harness-v4.3 C:/t/iso/work/r2x/review25/repro/on-v4.3 C:/t/r2x/dry-runs/r25-repro-v4.3 > "$L/REVIEWER-NEUTRAL-on-v4.3.log" 2>&1; echo "reviewer neutral probe on v4.3 exit $? : $(tail -1 "$L/REVIEWER-NEUTRAL-on-v4.3.log")" >> "$L/R25-CHAIN.log")
$PY /c/t/iso/work/r2x/review24/repro/run_provider_probe.py C:/t/iso/work/r2x/review25/harness-v4.3 C:/t/iso/work/r2x/review25/repro/r24-provider-probe-on-v4.3 C:/t/r2x/dry-runs/r25-r24probe-v4.3 > "$L/R24-PROVIDER-PROBE-on-v4.3.log" 2>&1; echo "original R24 provider probe on v4.3 exit $? : $(tail -1 "$L/R24-PROVIDER-PROBE-on-v4.3.log")" >> "$L/R25-CHAIN.log"
echo "== done $(date -u +%FT%TZ)" >> "$L/R25-CHAIN.log"
