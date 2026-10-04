import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''def verify_boq_rows(run: EvidenceRun, pdf, *, sha256: str, extraction: dict, render_dpi: int) -> list[dict]:''',
    '''def verify_boq_rows(run: EvidenceRun, pdf, *, sha256: str, extraction: dict, render_dpi: int, preselected: bool = False) -> list[dict]:''')
sub('''    values; compared afterwards (`validate_boq_row`). Accepted lines and held rows (issues that kept a row) alike."""''',
    '''    values; compared afterwards (`validate_boq_row`). Accepted lines and held rows (issues that kept a row) alike.
    `preselected`: the caller already chose the rows (by `boq_rows_to_verify`); every row given is read."""''')
sub('''    for row, reason in boq_rows_to_verify(lines, held, variant=run.variant, sha256=sha256):''',
    '''    chosen = ([(r, "preselected") for r in held + lines] if preselected else boq_rows_to_verify(lines, held, variant=run.variant, sha256=sha256))
    for row, reason in chosen:''')
p.write_text(s, encoding="utf-8")
q = pathlib.Path(r"C:/t/iso/work/run_boq_ev.py")
t = q.read_text(encoding="utf-8")
old = '''            for part in work:
                run.budget = open_budget(db, None)
                part_variant = "EV2"   # everything handed over is to be read; the selection was made above
                saved = run.variant
                run.variant = part_variant
                results += er.verify_boq_rows(run, pdf, sha256=sheet["sha256"], extraction={"lines": part["lines"], "issues": part["issues"]},
                                              render_dpi=dse.RENDER_DPI)
                run.variant = saved
                db.commit()'''
new = '''            for part in work:
                run.budget = open_budget(db, None)
                results += er.verify_boq_rows(run, pdf, sha256=sheet["sha256"], extraction={"lines": part["lines"], "issues": part["issues"]},
                                              render_dpi=dse.RENDER_DPI, preselected=True)
                db.commit()'''
assert t.count(old) == 1
t = t.replace(old, new)
q.write_text(t, encoding="utf-8")
print("ok")
