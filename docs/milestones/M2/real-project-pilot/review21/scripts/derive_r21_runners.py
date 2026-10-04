"""Derive the four-arm runners from the continuation runners (dry-run-proven, packaged in ai-pilot-r18-correction) with
exact, asserted string replacements: arm_a.py (common A base), arm_shares.py, arm_ev.py (one document arm per call,
env from the declaration). The originals are not modified."""
import pathlib

SRC = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
DST = pathlib.Path("C:/t/iso/work/r2x/review21")


def derive(src, dst, pairs, header):
    s = (SRC / src).read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) >= 1, (src, old[:90])
        s = s.replace(old, new)
    (DST / dst).write_text(f"# DERIVED from ai-pilot-r18/{src} by derive_r21_runners.py -- {header}\n" + s, encoding="utf-8")


FLAGS = '("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT", "AI_EVIDENCE_SUPPORT", "AI_EVIDENCE_SCHEDULING", "AI_EVIDENCE_DEADLINE", "AI_EVIDENCE_ROI")'
derive("cont_a.py", "arm_a.py", [
    ('for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"):', f'for k in {FLAGS}:'),
    ('xtrack.record(ep, "cont-A", items)', 'xtrack.record(ep, "r21-A", items)'),
], "four-arm A base (accepted app path, AI on, evidence off); every reader switch unset")
derive("cont_shares.py", "arm_shares.py", [
    ('pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/CONT-SHARES.json")', 'pathlib.Path("C:/t/iso/work/r2x/review21/R21-SHARES.json")'),
    ('(RUNS / "CONT-SHARES.json")', '(RUNS / "R21-SHARES.json")'),
], "per-arm project shares for the four document arms")
derive("cont_ev.py", "arm_ev.py", [
    ('PILOT_DIR = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")', 'PILOT_DIR = pathlib.Path("C:/t/iso/work/r2x/review21")'),
    ('for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):', f'for k in {FLAGS}:'),
    ('track = f"cont-{args.arm}"', 'track = f"r21-{args.arm}"'),
], "one document arm (L1..L4) from the declaration's env / identities; the arm's own ledger scope, share, io capture, tripwire")
print("derived arm_a.py arm_shares.py arm_ev.py")
