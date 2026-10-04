"""Patch the isolated candidate tree (C:/t/iso/cand-ai, branch ai-pilot-2026-09-30 from 3d5607d) -- evidence_reader.py
only. Keeps the file's line endings. Both changes are OFF unless their environment flag is set, so the candidate with
no flags behaves exactly as the accepted reader (tested). Applied once; re-running refuses."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai/backend/app/ai/evidence_reader.py")
raw = P.read_bytes()
crlf = b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")
assert "AI_EVIDENCE_GUARD" not in s, "already patched"


def sub(old: str, new: str, count: int = 1) -> None:
    global s
    assert s.count(old) == count, (old[:80], s.count(old))
    s = s.replace(old, new)


# 1. flags and versions (after VARIANTS: PROMPTS and the policy version are defined above it)
sub('VARIANTS = ("off", "EV1", "EV2")\n', '''VARIANTS = ("off", "EV1", "EV2")
# --- AI accuracy pilot (2026-09-30), isolated candidate only -----------------------------------------------------------
# G  AI_EVIDENCE_GUARD=1     a bare revision token (Rev.0, REV 01, R1 ...) is never accepted as a document identity
# T  AI_EVIDENCE_TARGETED=1  (requires G) one targeted, independent context read of an own identity / revision that
#                            is not validated, with region-bound support from the rotation-correct text layer or a
#                            local OCR of the read region; acceptance rule (validate_value) unchanged
import os as _os  # noqa: E402

GUARD_ENABLED = _os.environ.get("AI_EVIDENCE_GUARD") == "1"
TARGETED_ENABLED = _os.environ.get("AI_EVIDENCE_TARGETED") == "1"
if TARGETED_ENABLED and not GUARD_ENABLED:
    raise RuntimeError("AI_EVIDENCE_TARGETED requires AI_EVIDENCE_GUARD (T = G + targeted verification)")
if GUARD_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+guard-rev-token-2026-09-30.1"
if TARGETED_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+region-support-2026-09-30.1"
    READER_VERSION = READER_VERSION + "+targeted-2026-09-30.1"
    PROMPTS = {**PROMPTS, "read_field_context": "read-field-context-2026-09-30.1"}
_BARE_REVISION = re.compile(r"^\\s*(?:REV(?:ISION)?\\.?\\s*[-:]?\\s*(?:\\d{1,3}|[A-Z])|R\\.?\\s*\\d{1,2})\\s*$", re.I)


def bare_revision_token(value) -> bool:
    """The WHOLE value is a revision token ('Rev.0', 'REV 01', 'Rev A', 'R1'); identifiers that merely contain one
    ('EP-23091 R1', '...-003-R3', 'REVIEW-001') are not."""
    return bool(_BARE_REVISION.match(str(value or "")))
''')

# 2. G: the guard inside the validation policy
sub('''    if len(keys) > 1:
        return {**base, "state": "conflict", "support": None,''', '''    if GUARD_ENABLED and field == "identity" and bare_revision_token(chosen):
        return {**base, "state": "candidate", "support": None, "guard": "bare_revision_token",
                "reasons": ["a bare revision token is not a document identity (kept as revision evidence, no target)"]}
    if len(keys) > 1:
        return {**base, "state": "conflict", "support": None,''')

# 3. T: rotation-correct region text with local OCR of the read region when it has no source text
sub('''# --- read outcomes (M2 review 08, R8-01)''', '''def _local_ocr(page, clip) -> str:
    """Local Tesseract OCR of the read region (the application's own OCR configuration); '' on any failure."""
    try:
        import io

        import pymupdf
        from PIL import Image

        from app.services import document_control
        pix = page.get_pixmap(matrix=pymupdf.Matrix(300 / 72, 300 / 72), clip=clip)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return document_control._tesseract().image_to_string(img, config="--psm 6", timeout=30) or ""
    except Exception:  # noqa: BLE001 -- no OCR is no support, never a failure of the read
        return ""


def region_texts_v2(page, region_display: tuple | None, ocr_lines: list, *, pad: float = 0.35) -> list:
    """T only. As `region_texts`, but the text layer is clipped in the page's UNROTATED coordinates (a display rectangle
    of a rotated page is mapped through the derotation matrix; `region_texts` clips with the display rectangle and so
    reads the wrong area of a rotated page), and a region with no source text at all is OCR'd locally."""
    if region_display is None:
        return []
    clip = crop_clip(page, region_display, pad=pad)
    out = []
    try:
        text = page.get_text("text", clip=clip * page.derotation_matrix)
    except Exception:  # noqa: BLE001
        text = ""
    if text.strip():
        out.append(("text", text))
    inside = [str(l[4]) for l in ocr_lines or [] if len(l) >= 5 and clip.x0 <= l[0] and l[2] <= clip.x1 and clip.y0 <= l[1] and l[3] <= clip.y1]
    if inside:
        out.append(("ocr", "\\n".join(inside)))
    if not out:
        local = _local_ocr(page, clip)
        if local.strip():
            out.append(("ocr_local", local))
    return out


CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {"value": {"type": "string"}, "printed_label": {"type": "string"},
                   "role": {"type": "string", "enum": ["own_identity", "own_revision", "referenced_identity", "template_or_form_code", "date", "other"]},
                   "region": {"type": "array", "items": {"type": "integer"}}, "legible": {"type": "boolean"}},
    "required": ["value", "printed_label", "role", "region", "legible"], "additionalProperties": False,
}
CONTEXT_TEXT = ("Read one field printed on this image of a construction document (a page, or a part of a page around "
                "its title block or header). The field is: {what}. Give the value EXACTLY as printed (keep every letter, "
                "digit, hyphen, slash, dot and plus sign; do not complete or correct it), the printed label next to it, "
                "and its role: own_identity = the number THIS document or sheet is filed under; own_revision = THIS "
                "document's current revision; referenced_identity = another document's or drawing's number; "
                "template_or_form_code = a form, template, edition or letterhead code; date; other. Give its region "
                "[x0, y0, x1, y1] in 0..1000 of this image. If the field is not present or not legible, set legible to "
                "false and value to an empty string.")
CONTEXT_WHAT = {"identity": "this document's OWN identity (document / drawing / sheet / reference number)",
                "revision": "this document's OWN current revision"}
_EXPECTED_ROLE = {"identity": "own_identity", "revision": "own_revision"}


def _targeted_read(run, page, *, sha256: str, number: int, reason: str, field: str, region, ocr_lines):
    """T only: one independent context read (never shown any proposed value). Returns (reading, region, texts) or None."""
    import pymupdf

    if region is not None:
        clip = crop_clip(page, region, pad=1.5)
        scale = min(300 / 72, 2400 / max(clip.width, clip.height))
        png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip).tobytes("png")
    else:
        clip = page.rect
        png = page_png(page, long_side=2400)
    got = run.call(sha256=sha256, task="read_field_context", page=number, reason=reason + ",targeted",
                   parts=[TextPart("task", CONTEXT_TEXT.format(what=CONTEXT_WHAT[field])), ImagePart("context", png)],
                   schema=CONTEXT_SCHEMA, max_output=400)
    if got is None:
        return None
    new_region = None
    box = got.get("region") or []
    if len(box) == 4 and all(isinstance(v, (int, float)) for v in box) and 0 <= box[0] < box[2] <= 1000 and 0 <= box[1] < box[3] <= 1000:
        new_region = (clip.x0 + box[0] / 1000 * clip.width, clip.y0 + box[1] / 1000 * clip.height,
                      clip.x0 + box[2] / 1000 * clip.width, clip.y0 + box[3] / 1000 * clip.height)
    reading = {"source": "blind_context", "value": got.get("value", ""), "legible": bool(got.get("legible", False)),
               "label": got.get("printed_label"), "role": got.get("role")}
    use = new_region or region
    return reading, use, region_texts_v2(page, use, ocr_lines)


# --- read outcomes (M2 review 08, R8-01)''')

# 4. T in the page reader: support from region_texts_v2, and the targeted read when a value is not validated
sub('''        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts(page, region, ocr_lines or [])''', '''        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = (region_texts_v2 if TARGETED_ENABLED else region_texts)(page, region, ocr_lines or [])''')
sub('''            fields[key] = _value_read_outcome(field, readings, requests[key])
        if verdict["state"] == "unreadable" and not disc_value:''', '''            fields[key] = _value_read_outcome(field, readings, requests[key])
        if TARGETED_ENABLED and (disc_value or det_value) and verdict["state"] != "validated" and not verdict.get("guard"):
            got = _targeted_read(run, page, sha256=sha256, number=number, reason=reason, field=field, region=region, ocr_lines=ocr_lines or [])
            requests[key + ":targeted"] = _request_outcome(run, got[0] if got else None)
            if got is not None:
                reading, t_region, t_texts = got
                readings.append(reading)
                region, texts = t_region or region, t_texts or texts
                verdict = validate_value(field, readings, texts, det_value)
                if verdict["state"] == "validated" and reading.get("legible") and reading.get("role") != _EXPECTED_ROLE[field]:
                    verdict = {**verdict, "state": "candidate",
                               "reasons": verdict["reasons"] + [f"the targeted read gives the role {reading.get('role')!r}, not {_EXPECTED_ROLE[field]!r}"]}
                if fields.get(key) in ("incomplete:no_region", None) or requests.get(key) == "not_attempted":
                    fields[key] = _value_read_outcome(field, readings, requests[key + ":targeted"])
        if verdict["state"] == "unreadable" and not disc_value:''')

# 5. G: a guard-rejected identity never becomes the revision's target; its token is kept as raw revision evidence
sub('''        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_identity = verdict.get("value")''', '''        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED and not verdict.get("guard"):
            own_identity = verdict.get("value")''')
sub('''    # identities the page references: facts of their own, read by discovery (completed with it)''', '''    for o in [o for o in observations if o.get("field") == "identity" and "a bare revision token is not a document identity" in " ".join(o.get("reasons") or [])]:
        observations.append({**common, "field": "revision", "component": "revtok", "role": "revision_token", "value": o.get("value"),
                             "value_literal": o.get("value_literal"), "value_normalized": o.get("value_normalized"), "state": "observed_reference",
                             "reasons": ["a revision token read in the identity position: raw revision evidence, no target"], "read": COMPLETED,
                             "readings": o.get("readings")})
    # identities the page references: facts of their own, read by discovery (completed with it)''')

out = s.replace("\n", "\r\n") if crlf else s
P.write_bytes(out.encode("utf-8"))
print("patched; crlf", crlf)
