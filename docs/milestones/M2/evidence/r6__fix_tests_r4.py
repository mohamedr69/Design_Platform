import pathlib
B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend")
p = B / "tests/test_extraction_m2_review03.py"; s = p.read_text(encoding="utf-8")
reps = [
    ('''    assert row.extracted["read_sha256"] == changed_sha and row.extracted["retained"] == {"records": 1, "pages": [13], "unverified": 1, "other_profile": 0,
                                                                                         "sources": row.extracted["retained"]["sources"]}''',
     '''    assert row.extracted["read_sha256"] == changed_sha and row.extracted["retained"] == {"records": 1, "pages": [13], "mixed": False, "unverified": 1, "other_profile": 0,
                                                                                         "other_parser": 0, "sources": row.extracted["retained"]["sources"]}'''),
    ('''    assert set(record["flags"]) == {"carried_unvisited", "carried_unverified", "carried_other_profile"}
    assert record["retained"] == {"source_sha256": None, "parser_version": None, "profile": None, "read_at": None}, "unknown stays unknown"
    assert record["status"] == "UR" and ["approved", "retained from a unknown-profile reading of other bytes", "retained"] in record["decision_candidates"]''',
     '''    assert set(record["flags"]) == {"carried_unvisited", "carried_unverified", "carried_other_profile", "carried_other_parser"}
    assert record["retained"] == {"source_sha256": None, "parser_version": None, "profile": None, "read_at": None}, "unknown stays unknown"
    assert record["status"] == "UR" and ["approved", "retained from a unknown-profile reading by an unknown parser of other bytes", "retained"] in record["decision_candidates"]'''),
    ('''                         "retained": {"source_sha256": "original", "parser_version": "p1", "profile": "default", "read_at": "t0"},''',
     '''                         "retained": {"source_sha256": "original", "parser_version": dc.PARSER_VERSION, "profile": "default", "read_at": "t0"},'''),
    ('''    assert record["status"] == "UR" and ["rejected", "retained from a promoted reading of these bytes", "retained"] in record["decision_candidates"]''',
     '''    assert record["status"] == "UR" and ["rejected", f"retained from a promoted reading by {dc.PARSER_VERSION} of these bytes", "retained"] in record["decision_candidates"]'''),
    ('''    assert record["status"] == "UR" and row.status == "UR" and ["approved", "retained from a default reading of these bytes", "retained"] in record["decision_candidates"]''',
     '''    assert record["status"] == "UR" and row.status == "UR" and ["approved", f"retained from a default reading by {dc.PARSER_VERSION} of these bytes", "retained"] in record["decision_candidates"]'''),
    ('''    assert twin.extracted.get("retained") is None and twin.status == "UR", "read on its own (page 13 unvisited: no record), not copied"''',
     '''    assert twin.extracted.get("retained") is None and twin.extracted["records"] == [] and not twin.status, "read on its own (page 13 unvisited: no record), not copied"'''),
]
for old, new in reps:
    assert old in s, old[:80]
    s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
p = B / "tests/test_extraction_m2_review02.py"; s = p.read_text(encoding="utf-8")
old = '''    kept = {"records": [{"reference": "A", "page": 1}, {"reference": "B", "page": 13}, {"reference": "C"}], "read_sha256": "same"}'''
new = '''    kept = {"records": [{"reference": "A", "page": 1}, {"reference": "B", "page": 13}, {"reference": "C"}], "read_sha256": "same", "parser_version": dc.PARSER_VERSION, "profile": "default"}'''
assert old in s; s = s.replace(old, new, 1)
old = '''    carried, note = document_sync.carry_unvisited(kept, coverage, "same")
    assert [(r["reference"], r["flags"]) for r in carried] == [("B", ["carried_unvisited"]), ("C", ["carried_unvisited"])]
    assert "2 records" in note and "unverified" not in note
    carried, note = document_sync.carry_unvisited(kept, coverage, "other")
    assert all(r["flags"] == ["carried_unvisited", "carried_unverified"] for r in carried) and "unverified" in note
    carried, note = document_sync.carry_unvisited({"records": kept["records"]}, coverage, "same")
    assert all("carried_unverified" in r["flags"] for r in carried), "unknown source identity: unverified"'''
new = '''    carried, note = document_sync.carry_unvisited(kept, coverage, "same", "default")
    assert [(r["reference"], r["flags"]) for r in carried] == [("B", ["carried_unvisited"]), ("C", ["carried_unvisited"])]
    assert "2 records" in note and "unverified" not in note
    carried, note = document_sync.carry_unvisited(kept, coverage, "other", "default")
    assert all(r["flags"] == ["carried_unvisited", "carried_unverified"] for r in carried) and "unverified" in note
    carried, note = document_sync.carry_unvisited({"records": kept["records"]}, coverage, "same", "default")
    assert all("carried_unverified" in r["flags"] and "carried_other_parser" in r["flags"] for r in carried), "unknown source identity and parser: unverified, held"'''
assert old in s; s = s.replace(old, new, 1)
p.write_text(s, encoding="utf-8")
print("tests fixed")
