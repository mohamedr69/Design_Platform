"""M2 review 07 (E / B-2): an incomplete / uncertain extracted reference is candidate evidence, never a business key.
Future ingestion: the row mirror is not set from it and log_records does not hand it to the register builders;
existing business rows already filed under such a key are preserved as they are (no delete, rename or false
'missing'), and listed for the owner's adjudication."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\services\document_sync.py")
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('''def depend(db: Session, row: ProjectDocument, dependent_type: str, dependent_id: str, reason: str) -> DocumentDependency:''',
    '''UNCERTAIN_REFERENCE_FLAGS = ("reference_incomplete", "reference_uncertain")


def uncertain_reference(record) -> bool:
    """Whether a record's reference is flagged incomplete / uncertain by the reader (a stored dict or a record)."""
    flags = record.get("flags") if isinstance(record, dict) else getattr(record, "flags", ())
    return bool(set(flags or ()) & set(UNCERTAIN_REFERENCE_FLAGS))


def mirror_from(row: ProjectDocument, records: list) -> list[dict]:
    """Set the row's reference / revision / status mirror from its first record whose reference is not flagged
    incomplete / uncertain (M2 review 07). When every record is flagged, the mirror keeps what it had -- nothing is
    renamed or cleared -- and is not moved to the uncertain value. Returns the flagged readings as pending evidence,
    each under a stable internal key (document, page, record), never under the uncertain reference."""
    pending = [{"key": f"doc:{row.id}:p{getattr(r, 'page', None) or 1}:r{i}", "reference_literal": r.reference,
                "flags": [f for f in (r.flags or ()) if f in UNCERTAIN_REFERENCE_FLAGS], "page": getattr(r, "page", None),
                "printed_revision": getattr(r, "printed_revision", None), "status": r.status}
               for i, r in enumerate(records) if uncertain_reference(r)]
    settled = [r for r in records if not uncertain_reference(r)]
    if settled:
        first = settled[0]
        row.reference, row.revision, row.status = first.reference, first.revision, first.status
        row.system_code = row.system_code or first.system_code
    elif records:
        row.system_code = row.system_code or records[0].system_code
    return pending


def depend(db: Session, row: ProjectDocument, dependent_type: str, dependent_id: str, reason: str) -> DocumentDependency:''')

sub('''            if records:
                first = records[0]
                row.reference, row.revision, row.status = first.reference, first.revision, first.status
                row.system_code = row.system_code or first.system_code
            row.last_processed_at = utc_now()''',
    '''            if records:
                pending = mirror_from(row, list(records))
                if pending:
                    extracted["pending_evidence"] = pending
            row.last_processed_at = utc_now()''')
sub('''    if records:
        first = records[0]
        row.reference, row.revision, row.status = first.reference, first.revision, first.status
        row.system_code = row.system_code or first.system_code
    elif carried:''',
    '''    if records:
        pending = mirror_from(row, list(records))
        if pending:
            extracted["pending_evidence"] = pending
    elif carried:''')

sub('''    ours = system_rules.drawings_in_scope(project)
    records = [
        row for row in records
        if row.category != "drawings" or (ours and document_control.is_shop_drawing(row))
    ]
    return document_control.combine(records), list(dict.fromkeys(warnings))''',
    '''    ours = system_rules.drawings_in_scope(project)
    records = [
        row for row in records
        if row.category != "drawings" or (ours and document_control.is_shop_drawing(row))
    ]
    records, held = hold_uncertain_references(db, project, records)
    if held:
        warnings.append(f"{held} record(s) with an incomplete or uncertain reference are held as evidence, not filed "
                        "under that reference")
    return document_control.combine(records), list(dict.fromkeys(warnings))


def existing_business_keys(db: Session, project: Project) -> set[str]:
    """References business rows are already filed under: shop drawing records and submittals (upper case)."""
    from app.models import ProjectShopDrawing, ProjectSubmittal

    keys = {str(r[0]).upper() for r in db.query(ProjectShopDrawing.drawing_reference).filter(ProjectShopDrawing.project_id == project.id) if r[0]}
    keys |= {str(r[0]).upper() for r in db.query(ProjectSubmittal.reference).filter(ProjectSubmittal.project_id == project.id) if r[0]}
    return keys


def hold_uncertain_references(db: Session, project: Project, records: list) -> tuple[list, int]:
    """(records the register builders may use, how many were held). A record whose reference is flagged incomplete
    / uncertain creates, merges or reconciles no business row under that value -- except where a business row is
    already filed under exactly that reference: that row is preserved as it is (M2 review 07; the owner adjudicates
    it, see `uncertain_reference_cases`)."""
    if not any(uncertain_reference(r) for r in records):
        return records, 0
    existing = existing_business_keys(db, project)
    kept = [r for r in records if not uncertain_reference(r) or str(r.reference or "").upper() in existing]
    return kept, len(records) - len(kept)


def uncertain_reference_cases(db: Session, project: Project) -> list[dict]:
    """Every stored record of the project with an incomplete / uncertain reference: where it is, and whether a
    business row already carries that reference (preserved; for the owner to adjudicate) or not (held as evidence)."""
    existing = existing_business_keys(db, project)
    cases = []
    for row in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state != REMOVED):
        for i, data in enumerate((row.extracted or {}).get("records") or []):
            if uncertain_reference(data):
                ref = str(data.get("reference") or "")
                cases.append({"document_id": row.id, "path": row.relative_path, "page": data.get("page"), "record": i,
                              "key": f"doc:{row.id}:p{data.get('page') or 1}:r{i}", "reference_literal": ref,
                              "flags": [f for f in data.get("flags") or () if f in UNCERTAIN_REFERENCE_FLAGS],
                              "category": data.get("category"), "status": data.get("status"),
                              "mirror": row.reference, "existing_business_row": ref.upper() in existing})
    return cases''')
p.write_text(s, encoding="utf-8")
print("ok")
