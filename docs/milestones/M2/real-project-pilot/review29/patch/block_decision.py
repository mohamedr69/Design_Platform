# --- Review 29, C3: the bounded decision-region path (review29/CONTRACTS.md) -------------------------------------------
#
# Title-block (ROI) discovery gives identity / revision only. Decision blocks are found by the whole-page discovery's
# decision signal, by decision vocabulary in the page's text layer / cached OCR outside the title-block zone, or -- when
# neither gives a region and the page lacks full text coverage, or discovery was a located crop -- by one locate_decision
# request on the whole page. At most DECISION_REGIONS_PER_PAGE regions and DECISION_READS_PER_PAGE reads per page, inside
# the per-document cap. A crop that did not include a possible decision region is unknown, never absent. Acceptance needs
# two readings from distinct sources (one blind) agreeing on the marked option, a printed legend mapping it to a decision,
# a consultant / client actor in every reading and a target established on the page.
DECISION_REGIONS_PER_PAGE = 2
DECISION_READS_PER_PAGE = 3
DECISION_UNKNOWN = "incomplete:decision_unknown"
_DECISION_VOCAB = re.compile(r"APPROVED|NO\s+OBJECTION|REVISE|RESUBMIT|REJECTED|AS\s+NOTED|\bSTATUS\b|\bCODE\s*[:\-]?\s*['\"(]?[A-D1-4]\b|\bREVIEWED\b", re.I)
_MARKS = ["tick", "circle", "stamp", "handwriting", "none", "unclear"]
_ACTORS = ["consultant", "client", "contractor", "unknown"]
LOCATE_DECISION_SCHEMA = {
    "type": "object",
    "properties": {
        "stamps": {"type": "array", "items": {"type": "object", "properties": {
            "region": _REGION, "options_printed": {"type": "array", "items": {"type": "string"}}, "marked_option": {"type": "string"},
            "mark_type": {"type": "string", "enum": _MARKS}, "actor": {"type": "string", "enum": _ACTORS}, "legible": {"type": "boolean"}},
            "required": ["region", "options_printed", "marked_option", "mark_type", "actor", "legible"], "additionalProperties": False}},
        "notes": {"type": "string"},
    },
    "required": ["stamps", "notes"], "additionalProperties": False,
}
LOCATE_DECISION_TEXT = ("Page {page} of a construction document, the whole page. Find every consultant / client REVIEW STAMP or "
                        "review STATUS BLOCK anywhere on the page -- often outside the title block: a stamp, a boxed status "
                        "legend, a handwritten status code -- including ones you cannot read. For each give its region [x0, y0, "
                        "x1, y1] in 0..1000 of the image, the options printed in it, the option that is marked (tick, circle, "
                        "stamp or handwriting) exactly as written, who marked it as far as the block says, and whether it is "
                        "legible. A receipt stamp, a signature or a DRAWN / CHECKED / APPROVED BY sign-off row is not a review "
                        "status. An empty list when there is none.")


def validate_decision_dr(readings: list[dict], target: str | None = None) -> dict:
    """C3.5: as validate_decision, with the printed legend taken from every reading of the same region and the
    corroboration rule: two readings from distinct sources (at least one blind) agree on the marked option."""
    usable = [r for r in readings if r.get("legible", True)]
    marked = [r for r in usable if r.get("marked_option") and r.get("mark_type") in ("tick", "circle", "stamp", "handwriting")]
    if not marked:
        return {"state": "no_decision_marked" if usable else "unreadable", "decision": None, "reasons": [], "target": target}
    legend: list = []
    for r in usable:
        for option in r.get("options_printed") or []:
            if option not in legend:
                legend.append(option)
    mapped = []
    for r in marked:
        entry = _legend_entry(r["marked_option"], legend)
        text = entry if entry is not None else r["marked_option"]
        mapped.append((r, entry, None if NOT_A_DECISION.search(text or "") else (option_decision(entry) if entry is not None else None)))
    if all(NOT_A_DECISION.search((e if e is not None else r["marked_option"]) or "") for r, e, _d in mapped):
        return {"state": "not_a_decision", "decision": None, "target": target,
                "reasons": ["the marked words are a receipt / compliance statement, not a review decision: "
                            + ", ".join(sorted({r["marked_option"] for r in marked}))]}
    decisions = {d for _r, _e, d in mapped}
    if len(decisions) > 1:
        return {"state": "conflict", "decision": None, "target": target,
                "reasons": ["the readings name different decisions: " + ", ".join(f"{r['source']}={r['marked_option']!r}" for r in marked)]}
    decision = decisions.pop()
    reasons = []
    if decision is None:
        reasons.append("the marked option maps to no decision through the printed legend")
    sources = {str(r.get("source")) for r in marked}
    if len(sources) < 2 or not any(s.startswith("blind") for s in sources):
        reasons.append("not corroborated: two readings from distinct sources (one blind) must agree on the marked option")
    actors = {r.get("actor") for r in marked}
    if len(actors) > 1:
        reasons.append("the readings disagree on who marked it: " + ", ".join(sorted(str(a) for a in actors)))
    elif not actors <= {"consultant", "client"}:
        reasons.append("the mark is not evidenced as the consultant's or the client's")
    if not target:
        reasons.append("no target component: the page's own identity is not established")
    return {"state": "candidate" if reasons else "validated", "decision": decision, "target": target, "reasons": reasons,
            "legend": sorted({e for _r, e, _d in mapped if e}), "actor": next(iter(actors)) if len(actors) == 1 else None}


def _decision_vocab_regions(page, ocr_lines: list | None) -> list:
    """C3.3 (b): display rectangles of decision vocabulary in the text layer / cached OCR outside the title-block zone,
    clustered; the largest clusters first. Deterministic; no request."""
    import pymupdf

    from app.services import title_block as tb

    w, h = page.rect.width, page.rect.height
    boxes = []
    try:
        for b in page.get_text("blocks"):
            if len(b) >= 5 and _DECISION_VOCAB.search(str(b[4] or "")):
                boxes.append(pymupdf.Rect(b[:4]) * page.rotation_matrix)
    except Exception:  # noqa: BLE001 -- no text layer: no deterministic candidate
        pass
    for line in ocr_lines or []:
        if len(line) >= 5 and _DECISION_VOCAB.search(str(line[4] or "")):
            boxes.append(pymupdf.Rect(line[:4]))
    try:
        sheet = tb.is_drawing_sheet(page)
    except Exception:  # noqa: BLE001
        sheet = False
    # the title-block zone exists on a drawing sheet only; a form's decision block may sit anywhere on it
    boxes = [r for r in boxes if not r.is_empty and not (sheet and tb._in_zone(tb.Line(r.x0, r.y0, r.x1, r.y1, ""), w, h))]
    clusters: list = []
    for r in boxes:
        for c in clusters:
            if (c[0] + (-30, -30, 30, 30)).intersects(r):
                c[0] |= r
                c[1] += 1
                break
        else:
            clusters.append([pymupdf.Rect(r), 1])
    clusters.sort(key=lambda c: (-c[1], c[0].y0, c[0].x0))
    return [tuple(round(v, 2) for v in c[0]) for c in clusters]


def _full_text_coverage(page) -> bool:
    """C3.6: the page's text layer covers it -- 20 words or more spanning at least 60 % of its width and height."""
    try:
        words = page.get_text("words")
        box = page.cropbox
    except Exception:  # noqa: BLE001
        return False
    if len(words) < 20:
        return False
    xs0, ys0 = min(x[0] for x in words), min(x[1] for x in words)
    xs1, ys1 = max(x[2] for x in words), max(x[3] for x in words)
    return (xs1 - xs0) >= 0.6 * box.width and (ys1 - ys0) >= 0.6 * box.height


def _overlaps(a, b) -> bool:
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def _decision_region_read(run, page, *, sha256: str, number: int, reason: str, discovered: dict, located, ocr_lines, fields: dict,
                          requests: dict) -> dict | None:
    """C3 for one page, in the required-first path. Returns the page's decision context ({readings, region, dr}) or None
    (no candidate region; the outcome is then recorded as absent only under C3.6, else unknown)."""
    whole = not (located and located.get("located") and not located.get("whole_page"))
    info = {"rule": DECISION_REGION_VERSION, "whole_page_discovery": whole, "candidates": [], "locator": None}
    candidates = []
    signal = False
    if whole:
        signal = bool(discovered.get("decision_options_printed") or discovered.get("decision_marked_option") or discovered.get("decision_region")
                      or discovered.get("decision_mark_type") not in (None, "", "none"))
        if signal:
            region = region_from_norm(page, discovered.get("decision_region"))
            reading = {"source": "discovery", "options_printed": discovered.get("decision_options_printed") or [],
                       "marked_option": discovered.get("decision_marked_option") or "", "mark_type": discovered.get("decision_mark_type"),
                       "actor": discovered.get("decision_actor"), "legible": True}
            if region is not None:
                candidates.append((tuple(region), [reading], "discovery"))
            else:
                info["discovery_signal_without_region"] = True
    info["discovery_signal"] = signal
    for region in _decision_vocab_regions(page, ocr_lines):
        if len(candidates) >= DECISION_REGIONS_PER_PAGE:
            break
        if not any(_overlaps(region, c[0]) for c in candidates):
            candidates.append((region, [], "text"))
    full_text = _full_text_coverage(page)
    info["full_text_coverage"] = full_text
    if not candidates and (not whole or not full_text or info.get("discovery_signal_without_region")):
        got = run.call(sha256=sha256, task="locate_decision", page=number, reason=reason + ",decision_region",
                       parts=[TextPart("task", LOCATE_DECISION_TEXT.format(page=number)), ImagePart("page", page_png(page))],
                       schema=LOCATE_DECISION_SCHEMA, max_output=600)
        info["locator"] = _request_outcome(run, got)
        for stamp in ((got or {}).get("stamps") or [])[:DECISION_REGIONS_PER_PAGE]:
            region = region_from_norm(page, stamp.get("region"))
            if region is None:
                continue
            candidates.append((tuple(region), [{"source": "locator", "options_printed": stamp.get("options_printed") or [],
                                                "marked_option": stamp.get("marked_option") or "", "mark_type": stamp.get("mark_type"),
                                                "actor": stamp.get("actor"), "legible": bool(stamp.get("legible", True))}], "locator"))
    fields["decision:route"] = "decision-region:" + (",".join(sorted({c[2] for c in candidates})) or "none")
    if not candidates:
        absent = whole and not signal and full_text and info["locator"] is None
        fields["own:decision"] = ABSENT_BY_DISCOVERY if absent else DECISION_UNKNOWN
        requests["own:decision"] = "not_attempted" if info["locator"] is None else info["locator"]
        info["outcome"] = fields["own:decision"]
        return None
    reads, chosen, first = 0, [], None
    for region, base, origin in candidates:
        if reads >= DECISION_READS_PER_PAGE:
            info["candidates"].append({"origin": origin, "region": [round(v, 2) for v in region], "read": "not_attempted:reads_per_page"})
            continue
        blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason + ",decision_region",
                         parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.15))],
                         schema=READ_DECISION_SCHEMA, max_output=400)
        reads += 1
        entry = {"origin": origin, "region": [round(v, 2) for v in region], "read": _request_outcome(run, blind)}
        readings = list(base)
        if blind is not None:
            readings.append({"source": "blind_small", **blind})
            if blind.get("legible", True) and blind.get("marked_option") and reads < DECISION_READS_PER_PAGE:
                wide = run.call(sha256=sha256, task="read_decision", page=number, reason=reason + ",decision_region,wide",
                                parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.35))],
                                schema=READ_DECISION_SCHEMA, max_output=400)
                reads += 1
                entry["wide"] = _request_outcome(run, wide)
                if wide is not None:
                    readings.append({"source": "blind_wide", **wide})
        info["candidates"].append(entry)
        if first is None:
            first = (region, readings, entry["read"], blind)
        if blind is not None and blind.get("legible", True) and blind.get("marked_option"):
            chosen.append((region, readings))
    if chosen:
        region = chosen[0][0]
        readings = [r for _reg, rs in chosen for r in rs]
        fields["own:decision"] = COMPLETED
        requests["own:decision"] = "ok"
    else:
        region, readings, outcome, blind = first
        requests["own:decision"] = outcome
        fields["own:decision"] = (outcome if blind is None else COMPLETED if blind.get("legible", True) else "unusable:illegible")
    info["outcome"] = fields["own:decision"]
    return {"readings": readings, "region": region, "dr": info}


# --- Review 29, C4: page / target association invariant (reader side) ----------------------------------------------------


def _page_target(state: dict, fields: dict, det_identity) -> str | None:
    """C4 A2: the identity a dependent fact of this page may bind to -- established on this page, else this page's
    deterministic identity; never another page's."""
    if _identity_established(state, fields):
        return (state["identity"]["verdict"] or {}).get("value")
    return det_identity or None


def _apply_page_association(observations: list, *, number: int, state: dict, fields: dict, det_identity) -> None:
    target = _page_target(state, fields, det_identity)
    basis = ("own_page_identity" if _identity_established(state, fields) else "deterministic_page_identity" if det_identity else None)
    sti = state.get("identity") or {}
    candidates = sorted({str(r.get("value")).strip() for r in sti.get("readings") or [] if r.get("legible", True) and str(r.get("value") or "").strip()})
    for o in observations:
        if o.get("component") != "own":
            continue
        o["page_binding"] = {"page": number, "basis": basis, "rule": ASSOC_VERSION}
        if o.get("field") not in ("revision", "decision"):
            continue
        if target:
            o["target"] = target
            continue
        o.pop("target", None)
        if o.get("state") == "validated":
            o["state"] = "candidate"
        o["association"] = {"status": "held:no_page_target", "candidates": candidates, "rule": ASSOC_VERSION,
                            "reason": "no identity is established on this page; a dependent fact never binds to another page's identity"}
        o["reasons"] = list(o.get("reasons") or []) + ["held: no target established on its own page (page association invariant)"]
