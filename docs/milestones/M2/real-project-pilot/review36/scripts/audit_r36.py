"""ORCH-06C (R36HARNESS-IMPL): append one line to the work command and audit log (UTC).
Usage: audit_r36.py "<what was run>" ["<result>"]"""
import datetime
import sys

LOG = "C:/t/iso/work/r2x/r36/COMMANDS-AND-AUDIT-LOG.work.md"
now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
what = sys.argv[1] if len(sys.argv) > 1 else ""
result = sys.argv[2] if len(sys.argv) > 2 else ""
with open(LOG, "a", encoding="utf-8", newline="\n") as fh:
    fh.write(f"| {now} | {what} | {result} |\n")
