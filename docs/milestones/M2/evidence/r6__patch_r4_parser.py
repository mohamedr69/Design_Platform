"""Review 04, R4-01: the parser that read a carried record is part of its identity. A record retained from a reading made
by another (or an unknown) parser is flagged `carried_other_parser`, its decision is withheld as a candidate, the reading
that carries it is a mixed reading (never current, never copied, selected by the repair tool) until the page is read by
the current parser. Compatibility is explicit: only the current PARSER_VERSION is compatible with itself."""
import pathlib
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend")

p = B / "app/services/document_sync.py"; s = p.read_text(encoding="utf-8")
old = '''CARRIED_OTHER_PROFILE = "carried_other_profile"
CARRY_FLAGS = (CARRIED_UNVISITED, CARRIED_UNVERIFIED, CARRIED_OTHER_PROFILE)
RETAINED_METHOD = "retained"
'''
new = '''CARRIED_OTHER_PROFILE = "carried_other_profile"
CARRIED_OTHER_PARSER = "carried_other_parser"
CARRY_FLAGS = (CARRIED_UNVISITED, CARRIED_UNVERIFIED, CARRIED_OTHER_PROFILE, CARRIED_OTHER_PARSER)
RETAINED_METHOD = "retained"


def parser_compatible(version: str | None) -> bool:
    """Whether a record read under `version` may stand as read by the parser
    as it is now (M2 review 04, R4-01). The contract is explicit and narrow:
    only the current `document_control.PARSER_VERSION` is compatible with
    itself; an earlier or an unknown version is not, whatever it read -- a
    known defect of an earlier parser would otherwise stand for ever on a
    page the current parser never visited. (A future version may name the
    versions whose records it accepts; none does now.)"""
    return version is not None and version == document_control.PARSER_VERSION
'''
assert old in s; s = s.replace(old, new, 1)
old = '''        unverified = retained["source_sha256"] is None or retained["source_sha256"] != sha256
        other_profile = profile is not None and (retained["profile"] is None or retained["profile"] != profile)
        flags = [f for f in (record.get("flags") or []) if f not in CARRY_FLAGS] + [CARRIED_UNVISITED]
        if unverified:
            flags.append(CARRIED_UNVERIFIED)
        if other_profile:
            flags.append(CARRIED_OTHER_PROFILE)
        new = {**record, "flags": flags, "retained": retained}
        candidates = [list(c) for c in (record.get("decision_candidates") or [])]
        held = next((c for c in candidates if len(c) == 3 and c[2] == RETAINED_METHOD), None)
        if unverified or other_profile:
            status = record.get("status")
            if status not in (None, "UR") and held is None:
                why = f"retained from a {retained['profile'] or 'unknown-profile'} reading of " + ("other bytes" if unverified else "these bytes")
                candidates.append([status, why, RETAINED_METHOD])
            new["status"] = "UR"
            new["decision_candidates"] = candidates'''
new = '''        unverified = retained["source_sha256"] is None or retained["source_sha256"] != sha256
        other_profile = profile is not None and (retained["profile"] is None or retained["profile"] != profile)
        other_parser = not parser_compatible(retained.get("parser_version"))
        flags = [f for f in (record.get("flags") or []) if f not in CARRY_FLAGS] + [CARRIED_UNVISITED]
        if unverified:
            flags.append(CARRIED_UNVERIFIED)
        if other_profile:
            flags.append(CARRIED_OTHER_PROFILE)
        if other_parser:
            flags.append(CARRIED_OTHER_PARSER)
        new = {**record, "flags": flags, "retained": retained}
        candidates = [list(c) for c in (record.get("decision_candidates") or [])]
        held = next((c for c in candidates if len(c) == 3 and c[2] == RETAINED_METHOD), None)
        if unverified or other_profile or other_parser:
            status = record.get("status")
            if status not in (None, "UR") and held is None:
                why = (f"retained from a {retained['profile'] or 'unknown-profile'} reading by {retained.get('parser_version') or 'an unknown parser'} of "
                       + ("other bytes" if unverified else "these bytes"))
                candidates.append([status, why, RETAINED_METHOD])
            new["status"] = "UR"
            new["decision_candidates"] = candidates'''
assert old in s; s = s.replace(old, new, 1)
old = '''    unverified_n = sum(1 for r in carried if CARRIED_UNVERIFIED in r["flags"]); other_n = sum(1 for r in carried if CARRIED_OTHER_PROFILE in r["flags"])'''
new = '''    unverified_n = sum(1 for r in carried if CARRIED_UNVERIFIED in r["flags"]); other_n = sum(1 for r in carried if CARRIED_OTHER_PROFILE in r["flags"])
    parser_n = sum(1 for r in carried if CARRIED_OTHER_PARSER in r["flags"])'''
assert old in s; s = s.replace(old, new, 1)
old = '''            + (f"; {other_n} read under another or unknown extraction profile (decision held)" if other_n else "") + ".")'''
new = '''            + (f"; {other_n} read under another or unknown extraction profile (decision held)" if other_n else "")
            + (f"; {parser_n} read by another or unknown parser (decision held until the page is read again)" if parser_n else "") + ".")'''
assert old in s; s = s.replace(old, new, 1)
old = '''            "other_profile": sum(1 for r in kept if CARRIED_OTHER_PROFILE in r["flags"]),'''
new = '''            "other_profile": sum(1 for r in kept if CARRIED_OTHER_PROFILE in r["flags"]),
            "other_parser": sum(1 for r in kept if CARRIED_OTHER_PARSER in r["flags"]),'''
assert old in s; s = s.replace(old, new, 1)
old = '''    kept = [r for r in records if isinstance(r, dict) and CARRIED_UNVISITED in (r.get("flags") or [])]
    if not kept:
        return None
    return {"records": len(kept), "pages": sorted({r.get("page") for r in kept if r.get("page") is not None}),'''
new = '''    kept = [r for r in records if isinstance(r, dict) and CARRIED_UNVISITED in (r.get("flags") or [])]
    if not kept:
        return None
    return {"records": len(kept), "pages": sorted({r.get("page") for r in kept if r.get("page") is not None}),
            # a mixed reading: some record of it stands under another profile or parser than the envelope's
            "mixed": any(CARRIED_OTHER_PROFILE in r["flags"] or CARRIED_OTHER_PARSER in r["flags"] for r in kept),'''
assert old in s; s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

p = B / "app/services/document_processing.py"; s = p.read_text(encoding="utf-8")
old = '''            # ... and not carrying records read under another or an unknown
            # profile (M2 review 03, R3-02): such a reading is a mixed one,
            # never reused as this profile's; it is read again when the row
            # is next processed or repaired (not on its own: no retry loop).
            and not retained.get("other_profile"))'''
new = '''            # ... and not carrying records read under another or an unknown
            # profile (M2 review 03, R3-02) or by another or an unknown parser
            # (M2 review 04, R4-01): such a reading is a mixed one, never
            # reused as this parser's and profile's; it is read again when the
            # row is next processed or repaired (not on its own: no retry loop).
            and not retained.get("other_profile") and not retained.get("other_parser"))'''
assert old in s; s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

p = B / "scripts/repair_extraction.py"; s = p.read_text(encoding="utf-8")
old = '''        elif "parser-outdated" in selections and ((row.extracted or {}).get("retained") or {}).get("other_profile"):
            reasons.append("carries records read under another or an unknown extraction profile")'''
new = '''        elif "parser-outdated" in selections and ((row.extracted or {}).get("retained") or {}).get("other_profile"):
            reasons.append("carries records read under another or an unknown extraction profile")
        elif "parser-outdated" in selections and ((row.extracted or {}).get("retained") or {}).get("other_parser"):
            reasons.append("carries records read by another or an unknown parser")'''
assert old in s; s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")

t = B / "tests/test_extraction_m2_review03.py"; ts = t.read_text(encoding="utf-8")
ts += '''

# --- R4-01 (review 04): the parser that read a carried record is part of its identity -------------


def test_a_record_read_by_an_older_parser_is_held_by_a_bounded_reading_until_its_page_is_read_again(client, db_session, tmp_path, inline, monkeypatch):
    """Same bytes, same profile, an older parser: a formerly authoritative
    decision on the skipped page is retained with its parser, its decision
    withheld, the reading not current and not reused; the repair tool
    selects it; a wider read by the current parser clears it."""
    from scripts import repair_extraction as tool

    folder = tmp_path / "EP-30925"
    with pymupdf.open() as document:
        _page(document, SEPARATOR)
        for _ in range(11):
            _page(document, SEPARATOR)
        _page(document, FA_COVER + "Review status: (A) Approved\\n")
        path = folder / "05- Drawings" / "package.pdf"
        path.parent.mkdir(parents=True)
        path.write_bytes(document.tobytes())
    monkeypatch.setattr(dc, "PAGE_SCAN_LIMIT", 20)
    project_id = _project(client, folder, ep="30925")
    _sync(client, project_id)
    row = _row(db_session, project_id)
    assert row.status == "approved" and _carried(row)["page"] == 13
    # the reading as an older parser left it: the same bytes, the same profile, another parser version
    older = dict(row.extracted)
    older["parser_version"] = "parse-older-defective"
    row.extracted = older
    db_session.commit()
    assert document_processing.parser_current(row) is False

    # the current parser, narrower budget, unchanged bytes: it must read the file (no reuse) and hold page 13
    monkeypatch.setattr(dc, "PAGE_SCAN_LIMIT", 12)
    _touch(path)
    result = _sync(client, project_id)
    db_session.refresh(row)
    assert _processed(client, result)["unchanged_after_hash"] == 0
    record = _carried(row)
    assert set(record["flags"]) == {"carried_unvisited", "carried_other_parser"}
    assert record["retained"]["parser_version"] == "parse-older-defective" and record["retained"]["source_sha256"] == row.sha256
    assert record["status"] == "UR" and ["approved", "retained from a default reading by parse-older-defective of these bytes", "retained"] in record["decision_candidates"]
    assert row.status == "UR", "an old parser's decision is not certified by the new envelope"
    assert row.extracted["parser_version"] == dc.PARSER_VERSION and row.extracted["retained"]["other_parser"] == 1 and row.extracted["retained"]["mixed"] is True
    assert document_processing.parser_current(row) is False and document_processing._previous_sha(row) is None
    reloaded = _reload(row.id)
    assert _carried(reloaded)["status"] == "UR" and reloaded.status == "UR"

    # repeated bounded runs (the repair tool twice) and reload: the old parser stays in the record's provenance
    monkeypatch.setattr(tool, "root_of", lambda r: str(folder))
    selected = dict((r.id, reasons) for r, reasons in tool.select_rows(db_session, db_session.get(Project, project_id), {"parser-outdated"}, []))
    assert any(reason.startswith("carries records read by another") for reason in selected.get(row.id, []))
    for _ in range(2):
        entry = tool.preview(db_session, row, selected[row.id], False)
        tool.apply_row(db_session, row, entry)
        db_session.refresh(row)
        record = _carried(row)
        assert record["retained"]["parser_version"] == "parse-older-defective" and "carried_other_parser" in record["flags"] and record["status"] == "UR"
    assert _carried(_reload(row.id))["retained"]["parser_version"] == "parse-older-defective"

    # a duplicate of the same bytes is not given the mixed reading
    copy = folder / "05- Drawings" / "Archive" / "package.pdf"
    copy.parent.mkdir(parents=True)
    copy.write_bytes(path.read_bytes())
    result = _sync(client, project_id)
    twin = db_session.query(ProjectDocument).filter(ProjectDocument.project_id == project_id, ProjectDocument.relative_path == "05- Drawings/Archive/package.pdf").one()
    assert twin.extracted.get("retained") is None and twin.status == "UR", "read on its own (page 13 unvisited: no record), not copied"

    # a missing retained parser identity: unknown is not compatible
    stripped = dict(row.extracted)
    stripped["records"] = [{**r, "retained": {**r["retained"], "parser_version": None}} for r in stripped["records"]]
    row.extracted = stripped
    db_session.commit()
    entry = tool.preview(db_session, row, ["selected by id"], False)
    tool.apply_row(db_session, row, entry)
    db_session.refresh(row)
    assert "carried_other_parser" in _carried(row)["flags"] and _carried(row)["retained"]["parser_version"] is None and row.status == "UR"

    # the current parser reaches page 13: read afresh, current, idempotent
    monkeypatch.setattr(dc, "PAGE_SCAN_LIMIT", 20)
    _touch(path)
    _sync(client, project_id)
    db_session.refresh(row)
    record = _carried(row)
    assert record["flags"] == [] and record.get("retained") is None and record["status"] == "approved" and row.status == "approved"
    assert "retained" not in row.extracted and document_processing.parser_current(row) is True and document_processing._previous_sha(row) == row.sha256
    _touch(path)
    result = _sync(client, project_id)
    assert _processed(client, result)["unchanged_after_hash"] >= 1


def test_parser_compatibility_is_explicit_and_narrow():
    assert document_sync.parser_compatible(dc.PARSER_VERSION) is True
    assert document_sync.parser_compatible("parse-2026-09-28.3") is False and document_sync.parser_compatible(None) is False
    kept = {"records": [{"reference": "A", "page": 13, "status": "approved", "flags": []}], "read_sha256": "same", "parser_version": "older", "profile": "default", "read_at": "t0"}
    coverage = {"pages_skipped": [{"page": 13, "reason": "page scan limit"}]}
    [carried], note = document_sync.carry_unvisited(kept, coverage, "same", "default")
    assert set(carried["flags"]) == {"carried_unvisited", "carried_other_parser"} and carried["status"] == "UR" and "another or unknown parser" in note
    kept["parser_version"] = dc.PARSER_VERSION
    [carried], _ = document_sync.carry_unvisited(kept, coverage, "same", "default")
    assert carried["flags"] == ["carried_unvisited"] and carried["status"] == "approved"
'''
t.write_text(ts, encoding="utf-8")
print("R4-01 patched")
