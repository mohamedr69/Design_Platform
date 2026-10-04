import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''    from app.services.submittal_reader_support import provider_for
''', '''    from app.ai import submittal_reader
''')
sub('''    if variant == "off" or not rows:
        return counts
    provider = provider or provider_for(project)''', '''    if variant == "off" or not rows:
        return counts
    # The same gate as the application's other document reading: AI enabled, the project's policy allows it, a
    # ready provider, the task not switched off by an evaluation.
    blocked = submittal_reader.available(project, provider)
    if blocked is not None:
        counts["not_run"] = blocked
        return counts
    provider = provider or submittal_reader.get_provider()''')
sub('''    for variant in (None, document_control.OCR_REGIONS_VARIANT, document_control.TITLE_BLOCK_OCR_VARIANT):
        try:
            text = page_cache.get_ocr(sha256, index) if variant is None else page_cache.get_ocr(sha256, index, variant)''', '''    for variant in ("", document_control.OCR_REGIONS_VARIANT, document_control.TITLE_BLOCK_OCR_VARIANT):
        try:
            text = page_cache.get_ocr(sha256, index, variant)''')
p.write_text(s, encoding="utf-8")

c = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/core/config.py")
t = c.read_text(encoding="utf-8")
old = "    ai_cache_ttl_days: int = 90\n"
assert t.count(old) == 1
t = t.replace(old, old + '''    # The AI evidence reader (M2 review 06, app.ai.evidence_reader): "off" (default), "EV1" (targeted + a frozen
    # 20 % audit) or "EV2" (broad blind verification). Shadow evidence only: it never changes a record or a status.
    ai_evidence_variant: str = "off"
''')
c.write_text(t, encoding="utf-8")

d = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/services/document_processing.py")
u = d.read_text(encoding="utf-8")
def dsub(old, new):
    global u
    assert u.count(old) == 1, old[:60]
    u = u.replace(old, new)
dsub('''        anything_read = True
        forms_changed = _after_reading(db, project, row, role, relative, now, counts) or forms_changed''', '''        anything_read = True
        if row.state == FRESH and source is None:
            evidence_rows.append((row, path))
        forms_changed = _after_reading(db, project, row, role, relative, now, counts) or forms_changed''')
dsub('''    # What is built from the documents, brought up to the readings once.
    reconcile_started = time.perf_counter()''', '''    # The AI evidence stage (M2 review 06): off unless AI_EVIDENCE_VARIANT names a variant. Shadow evidence on the
    # rows read in this run -- `extracted["ai_evidence"]` only; no record, status or consumer changes.
    from app.ai import evidence_reader

    if evidence_reader.configured_variant() != "off" and evidence_rows:
        evidence_started = time.perf_counter()
        counts["ai_evidence"] = evidence_reader.evidence_stage(db, project, evidence_rows, provider=provider, ctx=ctx)
        telemetry.add("ai_evidence_stage", time.perf_counter() - evidence_started)

    # What is built from the documents, brought up to the readings once.
    reconcile_started = time.perf_counter()''')
p2 = "    deferred_forms"
d.write_text(u, encoding="utf-8")
print("ok")
