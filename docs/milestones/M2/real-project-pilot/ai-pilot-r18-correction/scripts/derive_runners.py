"""Derive the continuation runners from the ai-accuracy-pilot runners (dry-run-proven, packaged) with exact, asserted
string replacements, so the review sees precisely what changed. Writes cont_stage.py, cont_a.py, cont_shares.py,
cont_ev.py, cont_boq.py next to this script; the pilot originals are not modified."""
import pathlib

SRC = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
DST = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")


def derive(src, dst, pairs, header):
    s = (SRC / src).read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) >= 1, (src, old[:90])
        s = s.replace(old, new)
    (DST / dst).write_text(f'# DERIVED from ai-accuracy-pilot/{src} by derive_runners.py -- {header}\n' + s, encoding="utf-8")


PD = ('pathlib.Path("C:/t/iso/work/r2x/ai-pilot")', 'pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")')
DRY = ('sys.path.insert(0, str(pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")))\nimport dry_provider as dry',
       'sys.path.insert(0, "C:/t/iso/work/r2x/ai-pilot")\nimport dry_provider as dry')

# --- the stage ----------------------------------------------------------------------------------------------------------
derive("make_pilot_stage.py", "cont_stage.py", [
    ('A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")', 'A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")'),
    ('SAMPLE_SHA = "3822df9ef792e6c6277e0bec3271dcee06dcdc6a15291a3e03ab0b25b6bf1917"', 'SAMPLE_SHA = "ddbceb3f75ee2d44a654a68d6a54b41875cc37f0f26899d4806239cfd3e3c7f3"'),
    ('(A / "PILOT-SAMPLE.json")', '(A / "CONTINUATION-SAMPLE.json")'),
    ('DST = pathlib.Path("C:/t/r2x/pilot-stage")', 'DST = pathlib.Path("C:/t/r2x/cont-stage")'),
    ('(DST / "PILOT-STAGE.json")', '(DST / "CONT-STAGE.json")'),
], "the continuation stage C:/t/r2x/cont-stage (7 documents)")

# --- A base -------------------------------------------------------------------------------------------------------------
derive("pilot_a.py", "cont_a.py", [PD, DRY,
    ('(STAGE / "PILOT-STAGE.json")', '(STAGE / decl["stage"]["manifest"])'),
    ('xtrack.record(ep, "pilot-A", items)', 'xtrack.record(ep, "cont-A", items)'),
], "continuation A base (accepted app path, AI on, evidence off); stage manifest name from the declaration; track cont-A")

# --- shares -------------------------------------------------------------------------------------------------------------
derive("pilot_shares.py", "cont_shares.py", [PD, DRY,
    ('"rule": "share(ep) = floor((60 - used(ep)) / 3), for each of S, G, T"', '"rule": "share(ep) = floor((60 - used(ep)) / n_arms), for each document arm", "arms": sorted(decl["doc_arms"])'),
    ('"shares": {ep: (LIMIT - n) // 3 for ep, n in used.items()}}', '"shares": {ep: (LIMIT - n) // len(decl["doc_arms"]) for ep, n in used.items()}}'),
    ('pathlib.Path("C:/t/iso/work/r2x/ai-pilot/PILOT-SHARES.json")', 'pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/CONT-SHARES.json")'),
    ('(RUNS / "PILOT-SHARES.json")', '(RUNS / "CONT-SHARES.json")'),
], "per-arm shares for the continuation's document arms (S, T2)")

# --- the evidence arms --------------------------------------------------------------------------------------------------
derive("pilot_ev.py", "cont_ev.py", [PD, DRY,
    ('assert args.arm in ("S", "G", "T")\n', ''),
    ('arm = decl["arms"][args.arm]\n', 'assert args.arm in decl["doc_arms"], args.arm\narm = decl["arms"][args.arm]\n'),
    ('for n, h in decl["labels"]["files"].items():\n    assert hashlib.sha256((PILOT_DIR / "labels" / n).read_bytes()).hexdigest() == h, f"label file {n} changed"',
     'for n, h in decl["labels"]["files"].items():\n    assert hashlib.sha256((PILOT_DIR / decl["labels"]["dir"] / n).read_bytes()).hexdigest() == h, f"label file {n} changed"'),
    ('track = f"pilot-{args.arm}"', 'track = f"cont-{args.arm}"'),
    ('REG = json.loads((PILOT_DIR / "labels/PILOT-REGISTER-LABELS.json").read_text(encoding="utf-8"))',
     'REG = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["register"]).read_text(encoding="utf-8"))'),
    ('PAGE = json.loads((PILOT_DIR / "labels/PILOT-PAGE-LABELS.json").read_text(encoding="utf-8"))',
     'PAGE = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["page"]).read_text(encoding="utf-8"))'),
    ('UNC = json.loads((PILOT_DIR / "labels/PILOT-UNCERTAINTY-AND-EXPOSURE.json").read_text(encoding="utf-8"))',
     'UNC = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["uncertainty"]).read_text(encoding="utf-8"))'),
    ('for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED"):\n    os.environ.pop(k, None)',
     'for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT"):\n    os.environ.pop(k, None)'),
], "document arms S / T2 of the continuation; labels and track names from the declaration")

# --- H-06 BOQ control ---------------------------------------------------------------------------------------------------
derive("pilot_boq.py", "cont_boq.py", [PD, DRY,
    ('ext_file = PILOT_DIR / decl["sources"]["boq_extraction_A"]["file"]', 'ext_file = pathlib.Path(decl["sources"]["boq_extraction_A"]["file"])'),
    ('assert hashlib.sha256((PILOT_DIR / "boq_queue.py").read_bytes()).hexdigest() == decl["code"]["pilot_scripts"]["boq_queue.py"]',
     'assert hashlib.sha256(pathlib.Path("C:/t/iso/work/r2x/ai-pilot/boq_queue.py").read_bytes()).hexdigest() == decl["code"]["boq_queue_sha256"]'),
    ('sys.path.insert(0, str(PILOT_DIR))\nimport xtrack', 'sys.path.insert(0, "C:/t/iso/work/r2x/ai-pilot")\nimport xtrack'),
    ('track = f"pilot-BOQ-{args.arm}"', 'track = f"cont-H06-{args.arm}"'),
    ('extraction = json.loads(ext_file.read_text(encoding="utf-8"))[sheet["doc_key"]]',
     'extraction = [v for k, v in json.loads(ext_file.read_text(encoding="utf-8")).items() if k.replace("\\\\", "/") == sheet["doc_key"]][0]\n'
     'if not dry.DRY and LIMIT - xtrack.used(EP) < st.ai_max_calls_per_document:\n'
     '    sys.exit(f"EP-{EP} rolling-24-hour allowance cannot fit this arm now ({xtrack.used(EP)}/{LIMIT} used): the H-06 control stays pending")'),
    ('allowance = bh.DocAllowance(dry.DRY_ALLOWANCE if dry.DRY else "C:/t/r2x/ledger/ai-pilot-boq-allowance.sqlite")',
     'allowance = bh.DocAllowance(dry.DRY_ALLOWANCE if dry.DRY else "C:/t/r2x/ledger/ai-pilot-r18-h06-allowance.sqlite")'),
    ('cap = st.ai_max_calls_per_document\n', 'cap = st.ai_max_calls_per_document\nassert cap == 12\n'),
], "the H-06 detection control (EP-8430 exposed sheet), BOQ-S / BOQ-T, refuses to start while EP-8430 cannot fit 12")
print("derived: cont_stage.py cont_a.py cont_shares.py cont_ev.py cont_boq.py")
