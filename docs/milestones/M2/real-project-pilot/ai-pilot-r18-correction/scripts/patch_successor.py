"""Successor candidate patch (M2 Review 18), applied to C:/t/iso/cand-ai2 (branch ai-pilot-r18-2026-09-30, from e5a0a94).
Only backend/app/ai/evidence_reader.py changes. With every flag unset the module behaves exactly as accepted 3d5607d;
with G only, exactly as e5a0a94 G. Changes:
  T  (.2)  R18-01 completion from usable evidence, R18-02 no targeted read after a failed / refused primary OR escalation
           request, the required-first scheduling contract (document level), wrong-role readings excluded from validation
  E  (new) AI_EVIDENCE_EFFICIENT=1: located discovery for drawing sheets (title-block labels from the text layer / cached
           OCR / bounded local OCR, else the application's title-block strip -- never the full sheet), located-absence
           recorded as incomplete, request / OCR timeouts bounded by the job's remaining time, a minimum-time floor."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai2/backend/app/ai/evidence_reader.py")
raw = P.read_bytes()
assert b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:120])
    s = s.replace(old, new)


# --- flags and identities ---------------------------------------------------------------------------------------------
sub('''TARGETED_ENABLED = _os.environ.get("AI_EVIDENCE_TARGETED") == "1"
if TARGETED_ENABLED and not GUARD_ENABLED:
    raise RuntimeError("AI_EVIDENCE_TARGETED requires AI_EVIDENCE_GUARD (T = G + targeted verification)")
if GUARD_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+guard-rev-token-2026-09-30.1"
if TARGETED_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+region-support-2026-09-30.1"
    READER_VERSION = READER_VERSION + "+targeted-2026-09-30.1"
    PROMPTS = {**PROMPTS, "read_field_context": "read-field-context-2026-09-30.1"}
''', '''TARGETED_ENABLED = _os.environ.get("AI_EVIDENCE_TARGETED") == "1"
# E  AI_EVIDENCE_EFFICIENT=1 (M2 review 18) located discovery for drawing sheets + job-deadline-bound request / OCR
#                            timeouts; independent of G / T (compared on its own)
EFFICIENT_ENABLED = _os.environ.get("AI_EVIDENCE_EFFICIENT") == "1"
if TARGETED_ENABLED and not GUARD_ENABLED:
    raise RuntimeError("AI_EVIDENCE_TARGETED requires AI_EVIDENCE_GUARD (T = G + targeted verification)")
if GUARD_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+guard-rev-token-2026-09-30.1"
if TARGETED_ENABLED:
    # .2 (M2 review 18): completion from usable evidence (R18-01), no targeted read after a failed / refused primary or
    # escalation request (R18-02), required reads of every page before any optional targeted read (R18-03)
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+region-support-2026-09-30.1+targeted-completion-2026-09-30.2"
    READER_VERSION = READER_VERSION + "+targeted-2026-09-30.2"
    PROMPTS = {**PROMPTS, "read_field_context": "read-field-context-2026-09-30.1"}
if EFFICIENT_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+located-discovery-2026-09-30.1"
    READER_VERSION = READER_VERSION + "+located-discovery-2026-09-30.1"
    PROMPTS = {**PROMPTS, "discover_region": "discover-region-2026-09-30.1"}
MIN_REQUEST_S = 20.0            # E: no request is started with less than this left of the job's elapsed budget
LOCATED_LONG_SIDE_PX = 1568     # E: the located discovery crop's long side (the provider's native image size)
''')

# --- E: the request timeout follows the job's remaining time ---------------------------------------------------------
sub('''        if self.exhausted:
            self.log.append({**entry, "cache_hit": False, "outcome": f"budget: {self.exhausted}"})
            return None
        request = AiRequest(task=task, system=SYSTEM, parts=parts, schema=schema, max_output_tokens=max_output,
                            idempotency_key=key, tier=tier)
''', '''        if self.exhausted:
            self.log.append({**entry, "cache_hit": False, "outcome": f"budget: {self.exhausted}"})
            return None
        timeout_s = None
        if EFFICIENT_ENABLED:
            # E: the job's remaining elapsed budget bounds the request (the provider kills the CLI process at its
            # timeout); a request is not started with less than MIN_REQUEST_S left -- a budget stop, not a failure
            remaining = getattr(self.budget, "remaining_s", None)
            remaining = remaining() if callable(remaining) else None
            if remaining is not None:
                if remaining < MIN_REQUEST_S:
                    self.exhausted = "elapsed_time"
                    self.log.append({**entry, "cache_hit": False, "outcome": "budget: elapsed_time (under the minimum request time)"})
                    return None
                timeout_s = min(float(settings.ai_cli_timeout_s), remaining)
                entry["timeout_s"] = round(timeout_s, 1)
        request = AiRequest(task=task, system=SYSTEM, parts=parts, schema=schema, max_output_tokens=max_output,
                            idempotency_key=key, tier=tier, timeout_s=timeout_s)
''')

# --- E: bounded local OCR ----------------------------------------------------------------------------------------------
sub('''def _local_ocr(page, clip) -> str:
    """Local Tesseract OCR of the read region (the application's own OCR configuration); '' on any failure."""
    try:''', '''def _ocr_timeout(run) -> float:
    """E: an OCR run inside a job gets at most 30 s and never the time the next request needs; 30 s otherwise."""
    if not EFFICIENT_ENABLED or run is None:
        return 30.0
    remaining = getattr(getattr(run, "budget", None), "remaining_s", None)
    left = remaining() if callable(remaining) else None
    return 30.0 if left is None else max(0.0, min(30.0, left - MIN_REQUEST_S))


def _local_ocr(page, clip, timeout: float = 30.0) -> str:
    """Local Tesseract OCR of the read region (the application's own OCR configuration); '' on any failure."""
    if timeout <= 0:
        return ""
    try:''')
sub('''        return document_control._tesseract().image_to_string(img, config="--psm 6", timeout=30) or ""''',
    '''        return document_control._tesseract().image_to_string(img, config="--psm 6", timeout=timeout) or ""''')
sub('''def region_texts_v2(page, region_display: tuple | None, ocr_lines: list, *, pad: float = 0.35) -> list:''',
    '''def region_texts_v2(page, region_display: tuple | None, ocr_lines: list, *, pad: float = 0.35, ocr_timeout: float = 30.0) -> list:''')
sub('''        local = _local_ocr(page, clip)
        if local.strip():''', '''        local = _local_ocr(page, clip, ocr_timeout)
        if local.strip():''')

# --- T: targeted read with an optional context clip and bounded OCR -------------------------------------------------
sub('''def _targeted_read(run, page, *, sha256: str, number: int, reason: str, field: str, region, ocr_lines):
    """T only: one independent context read (never shown any proposed value). Returns (reading, region, texts) or None."""
    import pymupdf

    if region is not None:
        clip = crop_clip(page, region, pad=1.5)
        scale = min(300 / 72, 2400 / max(clip.width, clip.height))
        png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip).tobytes("png")
    else:
        clip = page.rect
        png = page_png(page, long_side=2400)''', '''def _targeted_read(run, page, *, sha256: str, number: int, reason: str, field: str, region, ocr_lines, context_clip=None):
    """T only: one independent context read (never shown any proposed value). Returns (reading, region, texts) or None.
    With no region: E's located discovery clip when there is one (never the full drawing sheet), else the page."""
    import pymupdf

    if region is not None or context_clip is not None:
        clip = crop_clip(page, region, pad=1.5) if region is not None else pymupdf.Rect(context_clip)
        scale = min(300 / 72, 2400 / max(clip.width, clip.height))
        png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip).tobytes("png")
    else:
        clip = page.rect
        png = page_png(page, long_side=2400)''')
sub('''    use = new_region or region
    return reading, use, region_texts_v2(page, use, ocr_lines)''', '''    use = new_region or region
    return reading, use, region_texts_v2(page, use, ocr_lines, ocr_timeout=_ocr_timeout(run))''')

# --- original page reader: discovery through _discover, absence through _absent (identical with E off) ----------------
sub('''    if TARGETED_ENABLED and False:
''', '', 0)
sub('''    changes a record."""
    observations = []
    fields: dict = {}
    requests: dict = {}
    discovered = run.call(sha256=sha256, task="discover_page", page=number, reason=reason,
                          parts=[TextPart("task", DISCOVER_TEXT.format(page=number)), ImagePart("page", page_png(page))],
                          schema=DISCOVER_SCHEMA, max_output=800)
    if discovered is None:''', '''    changes a record."""
    if TARGETED_ENABLED:
        ctx = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=reason, ocr_lines=ocr_lines)
        return _finish_page(run, page, ctx) if ctx.get("_pending") else ctx
    observations = []
    fields: dict = {}
    requests: dict = {}
    discovered, located = _discover(run, page, sha256=sha256, number=number, reason=reason, facts=facts, ocr_lines=ocr_lines)
    if discovered is None:''')
sub('''    fields["discovery"] = requests["discovery"] = "ok"
    det_identity = facts.identities[0] if facts.identities else None
    det_revision = facts.revisions[0] if facts.revisions else None
    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,
              "variant": run.variant, "profile": run.profile, "page_kind": discovered.get("page_kind")}
    own_identity = own_revision = None
    spec = (("identity", "read_identity", discovered.get("own_identity"), discovered.get("own_identity_region"), det_identity),
            ("revision", "read_revision", discovered.get("own_revision"), discovered.get("own_revision_region"), det_revision))
    for field, task, disc_value, disc_region, det_value in spec:
        key = f"own:{field}"
        region = _det_region(facts, field) or region_from_norm(page, disc_region)
        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = (region_texts_v2 if TARGETED_ENABLED else region_texts)(page, region, ocr_lines or [])
        if not (disc_value or det_value):
            fields[key] = ABSENT_BY_DISCOVERY
            continue''', '''    fields["discovery"] = requests["discovery"] = "ok"
    if located:
        fields["discovery:route"] = located["route"]
    det_identity = facts.identities[0] if facts.identities else None
    det_revision = facts.revisions[0] if facts.revisions else None
    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,
              "variant": run.variant, "profile": run.profile, "page_kind": discovered.get("page_kind")}
    own_identity = own_revision = None
    spec = (("identity", "read_identity", discovered.get("own_identity"), discovered.get("own_identity_region"), det_identity),
            ("revision", "read_revision", discovered.get("own_revision"), discovered.get("own_revision_region"), det_revision))
    for field, task, disc_value, disc_region, det_value in spec:
        key = f"own:{field}"
        region = _det_region(facts, field) or region_from_norm(page, disc_region)
        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts(page, region, ocr_lines or [])
        if not (disc_value or det_value):
            fields[key] = _absent(located, field, facts)
            continue''')
# the original loop's T block is unreachable now (T has its own reader); remove it so the G path is the e5a0a94 G path
sub('''            fields[key] = _value_read_outcome(field, readings, requests[key])
        if TARGETED_ENABLED and (disc_value or det_value) and verdict["state"] != "validated" and not verdict.get("guard") \\
                and not str(requests.get(key) or "").startswith(("failed", "budget")):
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
        if verdict["state"] == "unreadable" and not disc_value:''', '''            fields[key] = _value_read_outcome(field, readings, requests[key])
        if verdict["state"] == "unreadable" and not disc_value:''')
sub('''                             "request": requests.get("own:decision"),
                             "deterministic": next((r.get("status") for r in facts.records if r.get("status") not in (None, "UR")), None)})
    else:
        fields["own:decision"] = ABSENT_BY_DISCOVERY
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields, "_requests": requests}
''', '''                             "request": requests.get("own:decision"),
                             "deterministic": next((r.get("status") for r in facts.records if r.get("status") not in (None, "UR")), None)})
    else:
        fields["own:decision"] = _absent(located, "decision", facts)
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields, "_requests": requests}


# --- E: located discovery (M2 review 18) -------------------------------------------------------------------------------
#
# A full drawing sheet sent as the first request took 95-266 s on the Round 2 A0/A1 sheets and left nothing of the
# 120 s job budget for the reads that verify it. With E, a drawing sheet (the application's own test:
# title_block.is_drawing_sheet) is discovered from its title-block area only:
#   1. the page's horizontal text runs (title_block.page_lines), else the title-block OCR words the deterministic
#      reader cached, else -- bounded by the job's remaining time -- a local OCR of the application's title-block strip;
#   2. the number / revision labels among them (title_block's own label patterns) inside the title-block zone
#      (title_block._in_zone); the located area is their bounding box widened by 12 % of the sheet each way and
#      clamped to at most 45 % of its area;
#   3. no label: the application's title-block strip (right 28 % landscape / bottom 22 % portrait) -- never the full
#      sheet.
# The discovery crop is rendered at 1568 px on its long side; regions come back in the crop's 0..1000 and are mapped
# to the page's. A field the crop does not show is NOT a verified absence: identity / revision absence and a decision
# absence where the page's source text carries decision-block words are recorded `incomplete:located_region_only`.
# Nothing here uses labels, file names, project numbers or expected values. Pages that are not drawing sheets are
# discovered as before.

DISCOVER_REGION_TEXT = ("This image is the title-block / header area of page {page} of a construction drawing (not the "
                        "whole sheet). " + DISCOVER_TEXT.split(". ", 1)[1].replace("of the image", "of THIS image"))
_DECISION_BLOCK_CUES = re.compile(r"NO\\s+OBJECTION|APPROVED\\s+AS\\s+NOTED|REVISE\\s+(?:AND|&)\\s+RESUBMIT|\\bREJECTED\\b|NOT\\s+APPROVED|"
                                  r"\\bAPPROVED\\b(?!\\s+(?:BY|FOR))|\\bCODE\\s+[A-D]\\b", re.I)
LOCATED_ABSENCE = "incomplete:located_region_only"


def _absent(located: dict | None, field: str, facts) -> str:
    """The outcome of a field discovery did not report: a verified absence only when discovery saw the whole page, or
    (a decision) when the page's source text carries no decision-block words."""
    if not located or not located.get("located"):
        return ABSENT_BY_DISCOVERY
    if field == "decision" and len((facts.text or "").strip()) >= 80 and not _DECISION_BLOCK_CUES.search(facts.text or ""):
        return ABSENT_BY_DISCOVERY
    return LOCATED_ABSENCE


def locate_title_block(page, ocr_lines: list | None = None, *, ocr_timeout: float = 20.0) -> tuple:
    """(display rect, route) of a drawing sheet's title-block area; (None, 'not_a_drawing_sheet') otherwise."""
    import pymupdf

    from app.services import title_block as tb

    if not tb.is_drawing_sheet(page):
        return None, "not_a_drawing_sheet"
    w, h = page.rect.width, page.rect.height
    lines, source = tb.page_lines(page), "text"
    if len(lines) < 5 and ocr_lines:
        lines, source = [tb.Line(*l[:5]) for l in ocr_lines if len(l) >= 5], "ocr_cached"
    if len(lines) < 5 and ocr_timeout > 0:
        try:
            from functools import partial

            from app.services.document_control import _tesseract
            lines = tb.ocr_word_lines(page, tb.title_block_strip(page), dpi=150,
                                      image_to_data=partial(_tesseract().image_to_data, timeout=ocr_timeout))
            source = "ocr_local"
        except Exception:  # noqa: BLE001 -- no OCR: the strip, never the full sheet
            lines = []
    labels = [l for l in lines if tb._in_zone(l, w, h) and (tb._NUMBER_LABEL.match(l.text) or tb._REV_LABEL.match(l.text))]
    if labels:
        x0, y0 = min(l.x0 for l in labels) - 0.12 * w, min(l.y0 for l in labels) - 0.12 * h
        x1, y1 = max(l.x1 for l in labels) + 0.12 * w, max(l.y1 for l in labels) + 0.12 * h
        rect = pymupdf.Rect(max(0, x0), max(0, y0), min(w, x1), min(h, y1))
        if rect.width * rect.height <= 0.45 * w * h:
            return rect, f"located:labels:{source}"
    return tb.title_block_strip(page), f"located:strip:{source if lines else 'none'}"


def _norm_to_page(page, clip, box):
    """A region in 0..1000 of a crop, as 0..1000 of the page (region_from_norm's frame); None when invalid."""
    if not box or len(box) != 4:
        return None
    try:
        b = [float(v) for v in box]
    except (TypeError, ValueError):
        return None
    if not (0 <= b[0] < b[2] <= 1000 and 0 <= b[1] < b[3] <= 1000):
        return None
    w, h = page.rect.width, page.rect.height
    return [round((clip.x0 + b[0] / 1000 * clip.width) / w * 1000, 2), round((clip.y0 + b[1] / 1000 * clip.height) / h * 1000, 2),
            round((clip.x0 + b[2] / 1000 * clip.width) / w * 1000, 2), round((clip.y0 + b[3] / 1000 * clip.height) / h * 1000, 2)]


def _discover(run, page, *, sha256: str, number: int, reason: str, facts, ocr_lines):
    """(discovered, located) -- `located` None when the page was discovered whole (always with E off)."""
    if EFFICIENT_ENABLED:
        import pymupdf

        clip, route = locate_title_block(page, ocr_lines, ocr_timeout=_ocr_timeout(run))
        if clip is not None:
            scale = min(300 / 72, LOCATED_LONG_SIDE_PX / max(clip.width, clip.height))
            png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip).tobytes("png")
            got = run.call(sha256=sha256, task="discover_region", page=number, reason=reason,
                           parts=[TextPart("task", DISCOVER_REGION_TEXT.format(page=number)), ImagePart("title_block", png)],
                           schema=DISCOVER_SCHEMA, max_output=800)
            located = {"located": True, "route": route, "clip": [round(v, 2) for v in clip]}
            if got is not None:
                got = dict(got)
                for k in ("own_identity_region", "own_revision_region", "decision_region"):
                    got[k] = _norm_to_page(page, clip, got.get(k))
            return got, located
    discovered = run.call(sha256=sha256, task="discover_page", page=number, reason=reason,
                          parts=[TextPart("task", DISCOVER_TEXT.format(page=number)), ImagePart("page", page_png(page))],
                          schema=DISCOVER_SCHEMA, max_output=800)
    return discovered, ({"located": False, "route": "full_page"} if EFFICIENT_ENABLED else None)


# --- T .2: the targeted page reader (M2 review 18) ---------------------------------------------------------------------
#
# Scheduling contract (required-first, document level): for every triggered page of a document, discovery and every
# REQUIRED primary read (identity blind read [+ EV2 escalation], revision blind read [+ escalation], decision blind read)
# happen first, in page order (`_read_page_required`); only then, page by page, the OPTIONAL targeted context reads
# (identity before revision) and the page's observations (`_finish_page`). An optional read is made only while the run
# is not exhausted and the document is below MAX_CALLS_PER_DOCUMENT; the job budget / ledger refuse it like any other
# request. So an optional read never takes a call or time a required read of the same document needed.
#
# Gate (R18-02): no targeted read for a field whose primary OR escalation request failed, was refused or was refused by
# a budget (`own:<f>:targeted` = not_attempted:after_failure), or after a guard hold; exhaustion is never cleared.
#
# Completion (R18-01): after a targeted read the field's outcome is recomputed from usable evidence -- `completed` when
# the targeted reading is legible, carries a value and reports the field's own role (a model's success response alone
# never completes a field). The primary outcome is kept in `own:<f>:primary`, the targeted one in `own:<f>:targeted`
# (completed | unusable:illegible | unusable:empty | unusable:wrong_role | failed:<kind> | budget |
# not_attempted:<why>); requests keep `own:<f>` and `own:<f>:targeted` apart. A wrong-role reading is kept on the
# observation but excluded from validation. Validation itself is validate_value, unchanged.


def _read_page_required(run, page, *, sha256: str, number: int, facts, reason: str, ocr_lines=None) -> dict:
    fields: dict = {}
    requests: dict = {}
    discovered, located = _discover(run, page, sha256=sha256, number=number, reason=reason, facts=facts, ocr_lines=ocr_lines)
    if discovered is None:
        outcome = _call_outcome(run)
        return {"_outcome": "budget: " + (run.exhausted or "refused") if outcome == "budget" else "failed",
                "_observations": [], "_fields": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}},
                "_requests": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}}}
    fields["discovery"] = requests["discovery"] = "ok"
    if located:
        fields["discovery:route"] = located["route"]
    det_identity = facts.identities[0] if facts.identities else None
    det_revision = facts.revisions[0] if facts.revisions else None
    state = {}
    spec = (("identity", "read_identity", discovered.get("own_identity"), discovered.get("own_identity_region"), det_identity),
            ("revision", "read_revision", discovered.get("own_revision"), discovered.get("own_revision_region"), det_revision))
    for field, task, disc_value, disc_region, det_value in spec:
        key = f"own:{field}"
        region = _det_region(facts, field) or region_from_norm(page, disc_region)
        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts_v2(page, region, ocr_lines or [], ocr_timeout=_ocr_timeout(run))
        st = state[field] = {"key": key, "region": region, "readings": readings, "texts": texts, "disc": disc_value, "det": det_value}
        if not (disc_value or det_value):
            fields[key] = _absent(located, field, facts)
            st["absent"] = True
            continue
        if region is None:
            fields[key], requests[key] = "incomplete:no_region", "not_attempted"
            verdict = validate_value(field, readings, texts, det_value)
        else:
            blind = run.call(sha256=sha256, task=task, page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                             schema=READ_VALUE_SCHEMA, max_output=400)
            requests[key] = _request_outcome(run, blind)
            if blind is not None:
                readings.append({"source": "blind_small", "value": blind.get("value", ""), "legible": blind.get("legible", False),
                                 "label": blind.get("label_text")})
            verdict = validate_value(field, readings, texts, det_value)
            if blind is not None and run.variant == "EV2" and verdict["state"] in ("conflict", "candidate") and run.escalations < 2:
                run.escalations += 1
                strong = run.call(sha256=sha256, task=task, page=number, reason=reason + ",escalation", tier="standard",
                                  parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                                  schema=READ_VALUE_SCHEMA, max_output=400)
                if strong is not None:
                    readings.append({"source": "blind_standard", "value": strong.get("value", ""), "legible": strong.get("legible", False)})
                    verdict = validate_value(field, readings, texts, det_value)
                else:
                    fields[key + ":escalation"] = _call_outcome(run)
            fields[key] = _value_read_outcome(field, readings, requests[key])
        st["verdict"] = verdict
    decision = None
    if discovered.get("decision_options_printed") or discovered.get("decision_marked_option"):
        readings = [{"source": "discovery", "options_printed": discovered.get("decision_options_printed") or [],
                     "marked_option": discovered.get("decision_marked_option") or "", "mark_type": discovered.get("decision_mark_type"),
                     "actor": discovered.get("decision_actor"), "legible": True}]
        region = region_from_norm(page, discovered.get("decision_region"))
        if region is None:
            fields["own:decision"] = "incomplete:no_region"
            requests["own:decision"] = "not_attempted"
        else:
            blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.15))],
                             schema=READ_DECISION_SCHEMA, max_output=400)
            requests["own:decision"] = _request_outcome(run, blind)
            if blind is not None:
                readings.append({"source": "blind_small", **blind})
            fields["own:decision"] = (requests["own:decision"] if blind is None else
                                      COMPLETED if blind.get("legible", True) else "unusable:illegible")
        decision = {"readings": readings, "region": region}
    else:
        fields["own:decision"] = _absent(located, "decision", facts)
    return {"_pending": True, "number": number, "sha256": sha256, "reason": reason, "facts": facts, "ocr_lines": ocr_lines or [],
            "discovered": discovered, "located": located, "fields": fields, "requests": requests, "state": state, "decision": decision,
            "det_identity": det_identity}


def _finish_page(run, page, ctx: dict, *, may_call=None) -> dict:
    """The optional targeted reads of one page (after every required read -- see the contract above), then its
    observations. `may_call()`: the document still admits a call (read_document's per-document limit)."""
    fields, requests, state, facts = ctx["fields"], ctx["requests"], ctx["state"], ctx["facts"]
    number, sha256, reason, discovered, located = ctx["number"], ctx["sha256"], ctx["reason"], ctx["discovered"], ctx["located"]
    det_identity = ctx["det_identity"]
    context_clip = located.get("clip") if located and located.get("located") else None
    for field in ("identity", "revision"):
        st = state.get(field)
        if not st or st.get("absent"):
            continue
        key, verdict = st["key"], st["verdict"]
        if verdict["state"] == "validated" or verdict.get("guard"):
            continue
        failed = [o for o in (requests.get(key), fields.get(key + ":escalation")) if str(o or "").startswith(("failed", "budget"))]
        if failed:
            fields[key + ":targeted"] = "not_attempted:after_failure"
            continue
        if run.exhausted or (may_call is not None and not may_call()):
            fields[key + ":targeted"] = "not_attempted:budget"
            continue
        fields[key + ":primary"] = fields[key]
        got = _targeted_read(run, page, sha256=sha256, number=number, reason=reason, field=field, region=st["region"],
                             ocr_lines=ctx["ocr_lines"], context_clip=context_clip)
        requests[key + ":targeted"] = _request_outcome(run, got[0] if got else None)
        if got is None:
            fields[key + ":targeted"] = requests[key + ":targeted"]       # failed / budget: nothing changes
            continue
        reading, t_region, t_texts = got
        usable = bool(reading.get("legible")) and bool(literal_key(field, reading.get("value")))
        own_role = reading.get("role") == _EXPECTED_ROLE[field]
        if usable and not own_role:
            reading = {**reading, "excluded": f"role {reading.get('role')!r}, not {_EXPECTED_ROLE[field]!r}"}
        st["readings"].append(reading)
        fields[key + ":targeted"] = (COMPLETED if usable and own_role else "unusable:wrong_role" if usable else
                                     "unusable:empty" if reading.get("legible") else "unusable:illegible")
        if usable and own_role:
            st["region"], st["texts"] = t_region or st["region"], t_texts or st["texts"]
            fields[key] = COMPLETED
        st["verdict"] = validate_value(field, [r for r in st["readings"] if not r.get("excluded")], st["texts"], st["det"])
    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,
              "variant": run.variant, "profile": run.profile, "page_kind": discovered.get("page_kind")}
    observations = []
    own_identity = own_revision = None
    for field in ("identity", "revision"):
        st = state.get(field)
        if not st or st.get("absent"):
            continue
        key, verdict, readings, region, det_value = st["key"], st["verdict"], st["readings"], st["region"], st["det"]
        if verdict["state"] == "unreadable" and not st["disc"]:
            continue
        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED and not verdict.get("guard"):
            own_identity = verdict.get("value")
        if field == "revision" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_revision = verdict.get("value")
        roles = [n for n in discovered.get("other_numbers") or [] if det_value and literal_key(field, n.get("literal")) == literal_key(field, det_value)]
        reasons = list(verdict["reasons"]) + ([f"discovery lists the deterministic value as a {roles[0].get('role')}"] if roles else [])
        if fields[key] != COMPLETED:
            reasons.append(f"read not completed ({fields[key]}): unverified")
        observations.append({**common, "field": field, "component": "own", "role": "own", "value": verdict.get("value"),
                             "value_literal": verdict.get("value_literal"), "value_normalized": verdict.get("value_normalized"),
                             "candidates": verdict.get("candidates"), "state": verdict["state"], "reasons": reasons,
                             "support": verdict.get("support"), "readings": readings, "region": list(region) if region else None,
                             "deterministic": det_value, "read": fields[key], "request": requests.get(key),
                             "targeted": fields.get(key + ":targeted"),
                             # the component identity this revision was read for (R9-02): the page's final own identity
                             **({"target": own_identity or det_identity} if field == "revision" else {})})
    for o in [o for o in observations if o.get("field") == "identity" and "a bare revision token is not a document identity" in " ".join(o.get("reasons") or [])]:
        observations.append({**common, "field": "revision", "component": "revtok", "role": "revision_token", "value": o.get("value"),
                             "value_literal": o.get("value_literal"), "value_normalized": o.get("value_normalized"), "state": "observed_reference",
                             "reasons": ["a revision token read in the identity position: raw revision evidence, no target"], "read": COMPLETED,
                             "readings": o.get("readings")})
    for i, other in enumerate(discovered.get("other_numbers") or []):
        if other.get("literal"):
            fields[f"ref{i}:identity"] = COMPLETED
            observations.append({**common, "field": "identity", "component": f"ref{i}", "role": other.get("role") or "other",
                                 "value": other["literal"], "value_literal": other["literal"],
                                 "value_normalized": literal_key("identity", other["literal"]), "state": "observed_reference",
                                 "reasons": ["referenced by the page, not its own identity"], "read": COMPLETED,
                                 "readings": [{"source": "discovery", "value": other["literal"]}]})
    decision = ctx["decision"]
    if decision is not None:
        target = own_identity or det_identity
        verdict = validate_decision(decision["readings"], target)
        reasons = list(verdict["reasons"])
        state = verdict["state"]
        if fields["own:decision"] != COMPLETED:
            reasons.append(f"read not completed ({fields['own:decision']}): unverified")
            state = "candidate" if state == "validated" else "unverified" if state in ("no_decision_marked", "not_a_decision") else state
        region = decision["region"]
        observations.append({**common, "field": "decision", "component": "own", "role": "own", "value": verdict.get("decision"),
                             "state": state, "reasons": reasons, "target": target, "target_revision": own_revision,
                             "legend": verdict.get("legend"), "actor": verdict.get("actor"), "readings": decision["readings"],
                             "region": list(region) if region else None, "read": fields["own:decision"],
                             "request": requests.get("own:decision"),
                             "deterministic": next((r.get("status") for r in facts.records if r.get("status") not in (None, "UR")), None)})
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields, "_requests": requests}
''')

# --- read_document: T reads every page's required reads first, then the optional reads --------------------------------
sub('''        before = run.calls
        found = _read_page(run, page, sha256=sha256, number=number, facts=facts, reason=",".join(why),
                           ocr_lines=(ocr_lines or {}).get(index) or [])
        entry["calls"] = run.calls - before
        entry["outcome"] = found.pop("_outcome")
        entry["fields"] = found.pop("_fields", {})
        entry["requests"] = found.pop("_requests", {})
        out.extend(found.pop("_observations"))
        coverage["pages"].append(entry)
    coverage["calls"] = run.calls - calls_before''', '''        before = run.calls
        if TARGETED_ENABLED:
            found = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=",".join(why),
                                        ocr_lines=(ocr_lines or {}).get(index) or [])
            entry["calls"] = run.calls - before
            coverage["pages"].append(entry)
            if found.get("_pending"):
                pending.append((entry, page, found))
                continue
        else:
            found = _read_page(run, page, sha256=sha256, number=number, facts=facts, reason=",".join(why),
                               ocr_lines=(ocr_lines or {}).get(index) or [])
            entry["calls"] = run.calls - before
            coverage["pages"].append(entry)
        entry["outcome"] = found.pop("_outcome")
        entry["fields"] = found.pop("_fields", {})
        entry["requests"] = found.pop("_requests", {})
        out.extend(found.pop("_observations"))
    for entry, page, ctx in pending:          # T: the optional reads, after every page's required reads
        before = run.calls
        found = _finish_page(run, page, ctx, may_call=lambda: run.calls - calls_before < MAX_CALLS_PER_DOCUMENT)
        entry["calls"] += run.calls - before
        entry["outcome"] = found.pop("_outcome")
        entry["fields"] = found.pop("_fields", {})
        entry["requests"] = found.pop("_requests", {})
        out.extend(found.pop("_observations"))
    coverage["calls"] = run.calls - calls_before''')
sub('''    calls_before = run.calls
    for index in range(min(pdf.page_count, MAX_PAGES_PER_DOCUMENT)):''', '''    calls_before = run.calls
    pending = []
    for index in range(min(pdf.page_count, MAX_PAGES_PER_DOCUMENT)):''')

P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("patched")
