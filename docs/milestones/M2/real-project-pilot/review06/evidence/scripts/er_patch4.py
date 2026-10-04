import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_text(encoding="utf-8")
start = s.index("def verify_boq_rows(")
end = s.index("def _brief(row: dict) -> dict:")
s = s[:start] + '''def verify_boq_rows(run: EvidenceRun, pdf, *, sha256: str, extraction: dict, render_dpi: int) -> list[dict]:
    """Blind readings of design-sheet rows: a crop of the whole row across the table (from the deterministic
    reader's own geometry -- the row's bounds or its centre line, and its table's span), read without the reader's
    values; compared afterwards (`validate_boq_row`). Accepted lines and held rows (issues that kept a row) alike."""
    import pymupdf

    lines = [dict(l, _accepted=True) for l in extraction.get("lines") or []]
    spans = {}
    for l in lines:
        if l.get("table_span"):
            spans.setdefault(int(l.get("page") or 1), l["table_span"])
    held = []
    for issue in extraction.get("issues") or []:
        d = issue.get("detail") or {}
        region = issue.get("region")
        if not str(issue.get("target") or "").startswith("boq_line:") or not region:
            continue
        page = int(issue.get("page") or 1)
        held.append({"page": page, "catalog_no": d.get("catalog_no"), "quantity": d.get("quantity") or d.get("raw_quantity"),
                     "description": d.get("description"), "row_bounds": [region[1], region[3]],
                     "table_span": spans.get(page) or [region[0], region[2]], "_accepted": False, "_target": issue.get("target")})
    results = []
    for row, reason in boq_rows_to_verify(lines, held, variant=run.variant, sha256=sha256):
        page_no = int(row.get("page") or 1)
        bounds = row.get("row_bounds") or ([row["y_px"] - 24, row["y_px"] + 24] if row.get("y_px") else None)
        span = row.get("table_span")
        if not bounds or not span or None in (list(bounds) + list(span)):
            results.append({"page": page_no, "reason": reason, "row": _brief(row), "accepted_by_reader": row["_accepted"], "state": "no_geometry"})
            continue
        page = pdf[page_no - 1]
        scale = 72 / render_dpi
        clip = pymupdf.Rect(span[0] * scale, (bounds[0] - 6) * scale, span[1] * scale, (bounds[1] + 6) * scale) & page.rect
        png = page.get_pixmap(matrix=pymupdf.Matrix(CROP_DPI / 72, CROP_DPI / 72), clip=clip).tobytes("png")
        blind = run.call(sha256=sha256, task="read_boq_row", page=page_no, reason=reason,
                         parts=[TextPart("task", READ_TEXTS["read_boq_row"]), ImagePart("row", png)], schema=BOQ_ROW_SCHEMA, max_output=300)
        verdict = validate_boq_row({"part_number": row.get("catalog_no") or row.get("part_number"), "quantity": row.get("quantity")}, blind)
        results.append({"page": page_no, "reason": reason, "row": _brief(row), "accepted_by_reader": row["_accepted"], **verdict})
    return results


''' + s[end:]
s = s.replace('''    return {"part_number": row.get("catalog_no") or row.get("part_number"), "quantity": row.get("quantity"),
            "row_bounds": list(row.get("row_bounds") or []) or None}''', '''    return {"part_number": row.get("catalog_no") or row.get("part_number"), "quantity": row.get("quantity"),
            "description": row.get("description"), "row_bounds": list(row.get("row_bounds") or []) or None, "y_px": row.get("y_px")}''')
p.write_text(s, encoding="utf-8")
print("ok")
