import pathlib

B = pathlib.Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\backend\app")


def patch(path, pairs):
    p = B / path
    s = p.read_text(encoding="utf-8")
    for old, new in pairs:
        assert s.count(old) == 1, (path, s.count(old), old[:90])
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8")


patch("services/design_sheet_extractor.py", [(
    '''    state: str = "completed"
''', '''    state: str = "completed"
    # False where no reader looked at the sheet at all -- the model switched off or unavailable, the file not
    # there -- as against a sheet read and found unreadable. A read nothing attempted is not a completed read:
    # it is not stamped as the project's BOQ read, and its sheet's lines are not re-read away (M2 review 05).
    attempted: bool = True
''')])

patch("ai/sheet_reader.py", [(
    '''def _not_read(why: str, *, reading_id: int | None = None) -> DesignSheetExtraction:''',
    '''def _not_read(why: str, *, reading_id: int | None = None, attempted: bool = True) -> DesignSheetExtraction:'''), (
    '''    result.state = "failed"
    return result
''', '''    result.state = "failed"
    result.attempted = attempted
    return result
'''), (
    '''    if why_not:
        return _not_read(f"Not read: {why_not}")
    if not path.is_file():
        return _not_read("Not read: the file is not there")''',
    '''    if why_not:
        return _not_read(f"Not read: {why_not}", attempted=False)
    if not path.is_file():
        return _not_read("Not read: the file is not there", attempted=False)''')])

patch("routers/projects.py", [(
    '''        # One transaction: the stamp, the runs with their review rows, the
        # lines and the version are written together or not at all -- the
        # BOQ never shows as extracted with its lines missing.''',
    '''        # No sheet was read at all -- the model switched off or unavailable, the files not there: nothing was
        # attempted, so nothing is stamped. Stamping it made the BOQ "extracted" with no line, and every later
        # open returned that empty BOQ, the model enabled or not (M2 review 05, R5-04). The reasons are
        # returned; the next open tries again. A sheet read and found unreadable is still stamped, as before.
        if reads and not any(getattr(result, "attempted", True) for _sheet, result in reads):
            return BoqEnsureResponse(items=project.boq_items, extracted=False, warnings=warnings, version=project.boq_version)

        # One transaction: the stamp, the runs with their review rows, the
        # lines and the version are written together or not at all -- the
        # BOQ never shows as extracted with its lines missing.''')])

patch("services/boq_candidates.py", [(
    '''    library = boq_provenance.part_library(db)
    for record in new_lines:
        boq_provenance.check_catalog(record, library)
    old_lines = [_old_line(item) for item in project.boq_items]
    changes, unchanged = compare(old_lines, new_lines)''',
    '''    # A sheet this read could not read says nothing about the lines the BOQ took from it: they are not
    # "no longer yielded" -- nobody looked. Offered as removals they could be accepted and the BOQ lose
    # them (M2 review 05, R5-04). They are left out of the comparison and stand as they are; a re-read that
    # read no sheet at all is not a re-read, and fails with the reasons.
    unread = [(sheet, s) for sheet, s in zip(project.design_sheets, sheets) if s["failure"]]
    if sheets and len(unread) == len(sheets):
        raise CandidateError("No Design Sheet could be read, so nothing was compared and the BOQ is unchanged: "
                             + "; ".join(f"{s['document_name']}: {s['failure']}" for _sheet, s in unread))
    unread_paths = {str(sheet.document_path) for sheet, _s in unread}
    run_paths = {run.id: str(run.document_path) for run in db.query(ExtractionRun).filter(ExtractionRun.project_id == project.id)}
    library = boq_provenance.part_library(db)
    for record in new_lines:
        boq_provenance.check_catalog(record, library)
    old_lines, not_reread = [], []
    for item in project.boq_items:
        (not_reread if item.extraction_run_id is not None and run_paths.get(item.extraction_run_id) in unread_paths
         else old_lines).append(_old_line(item))
    changes, unchanged = compare(old_lines, new_lines)'''), (
    '''        "failed_sheets": [s["document_name"] for s in sheets if s["failure"]],
    }''', '''        "failed_sheets": [s["document_name"] for s in sheets if s["failure"]],
        # Lines from those sheets, left as they are: not compared, never offered for removal.
        "not_reread": len(not_reread),
    }''')])
print("ok")
