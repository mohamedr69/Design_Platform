"""M2 review 07 (R7-02): the evidence reader's validation policy .2 -- region-bound literal support, literal and
normalised values kept apart, all readings kept through escalation, decision acceptance with corroboration / actor /
printed legend / target, referenced identities as separate facts, BOQ numeric semantics and separate part / quantity."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\evidence_reader.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


def between(start, end, new):
    global s
    i, j = s.index(start), s.index(end)
    assert i < j
    s = s[:i] + new + s[j:]


sub('READER_VERSION = "evidence-reader-2026-09-29.1"', 'READER_VERSION = "evidence-reader-2026-09-29.2"   # .2: review 07 (validation policy .2, lifecycle, profile)')
sub('EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.1"', 'EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.2"')

VALIDATION = r'''# --- validation policy (evidence-policy-2026-09-29.2, M2 review 07 R7-02) -------------------------------------------
#
# .1 counted a value as supported when its punctuation-stripped form appeared anywhere in the page's text or OCR, or
# one character away in OCR; it validated a decision from one reading with no printed options; and its escalation
# re-validated only the last two readings. .2:
#   * support is literal and **bound to the region** the blind reader saw (the page's text layer inside that crop, or
#     the title-block OCR words inside it), with token boundaries: a value inside a longer identity ("ABC-123" in
#     "ABC-1234") or inside a date ("12" in "12/09/2026") is not support; a one-character near match is a
#     `candidate`, never `validated`;
#   * the literal as read and its normalised key are kept apart; identities / parts compare by literal key (upper
#     case, whitespace ignored, every other character significant: "PT-1S" is not "PT-1S+", "0012" is not "12");
#   * every reading -- discovery, blind, escalated -- takes part in the verdict; a disagreement is a `conflict`;
#   * a decision is `validated` only when discovery and a blind reading agree on a marked option that is one of the
#     options printed on the form, mapped through that printed legend, marked by an evidenced consultant / client
#     (the same one in every reading), against a known target component; receipt stamps / compliance words are no
#     decision.

_ID_BOUNDARY = r"A-Za-z0-9&/._\-"
_DATE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b|\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b|"
                   r"\b\d{1,2}[ -]?(?:JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*[ -]?\d{2,4}\b", re.I)
NOT_A_DECISION = re.compile(r"\b(?:RECEIVED|RECEIPT|COMPL(?:Y|IES|IANT|IANCE)|NOTED FOR RECORD|FOR INFORMATION|ACKNOWLEDGED)\b", re.I)


def literal_key(field: str, value: str | None) -> str:
    """The comparison key of a literal: identities, parts and revisions compare as printed, upper case, whitespace
    ignored -- punctuation, symbols and leading zeros are significant."""
    return re.sub(r"\s+", "", str(value or "")).upper()


def _pattern(field: str, value: str) -> re.Pattern:
    body = r"\s*".join(re.escape(c) for c in re.sub(r"\s+", "", value))
    edge = _ID_BOUNDARY if field == "identity" else r"A-Za-z0-9"
    return re.compile(rf"(?<![{edge}]){body}(?![{edge}])", re.I)


def region_support(field: str, value: str | None, region_texts: list) -> tuple[str | None, str | None]:
    """(support, why not): where the literal is found inside the read region -- 'text' (the page's text layer) or
    'ocr' (the title-block OCR words) -- as a whole token, not inside a longer identity and (for a revision) not
    inside a date. A one-character near match gives (None, reason) -- evidence for a candidate, not support."""
    v = re.sub(r"\s+", "", str(value or ""))
    if len(v) < 1 or not region_texts:
        return None, "no source text for the read region" if not region_texts else "nothing to support"
    pattern = _pattern(field, v)
    near = None
    for source, text in region_texts:
        text = text or ""
        dates = [m.span() for m in _DATE.finditer(text)] if field == "revision" else []
        for m in pattern.finditer(text):
            if not any(a <= m.start() and m.end() <= b for a, b in dates):
                return source, None
        if len(v) >= 5 and near is None:
            for token in re.split(r"[\s,;:|()]+", text):
                if token and abs(len(token) - len(v)) <= 1 and literal_key(field, token) != literal_key(field, v) and \
                        _distance(literal_key(field, token), literal_key(field, v)) <= 1:
                    near = token
    if near is not None:
        return None, f"only a near match in the region ({near!r})"
    return None, "the literal is not in the read region's source text"


def _distance(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def validate_value(field: str, readings: list[dict], region_texts: list, deterministic: str | None) -> dict:
    """The policy for an identity or a revision over **all** readings (discovery, blind, escalated).
    validated = a legible blind reading, every legible reading the same literal, supported in the read region, and
    not contradicted by the deterministic reading; candidate = unsupported, near-only, or discovery only;
    conflict = readings disagree, or disagree with the deterministic value (both kept); unreadable = none legible."""
    legible = [r for r in readings if r.get("legible", True) and literal_key(field, r.get("value"))]
    if not legible:
        return {"state": "unreadable", "value": None, "reasons": ["no legible reading"], "support": None}
    keys = {literal_key(field, r["value"]) for r in legible}
    blind = [r for r in legible if str(r.get("source", "")).startswith("blind")]
    chosen = (blind[0] if blind else legible[0])["value"].strip()
    base = {"value": chosen, "value_literal": chosen, "value_normalized": literal_key(field, chosen),
            "candidates": sorted({r["value"].strip() for r in legible})}
    if len(keys) > 1:
        return {**base, "state": "conflict", "support": None,
                "reasons": ["the readings disagree: " + ", ".join(f"{r['source']}={r['value']!r}" for r in legible)]}
    support, why = region_support(field, chosen, region_texts)
    reasons = []
    if not blind:
        reasons.append("discovery only: no blind reading of the region")
    if support is None:
        reasons.append(why)
    if deterministic and literal_key(field, deterministic) != literal_key(field, chosen):
        return {**base, "state": "conflict", "support": support,
                "reasons": reasons + [f"the deterministic reader read {deterministic!r}"]}
    return {**base, "state": "validated" if not reasons else "candidate", "support": support, "reasons": reasons}


def _legend_entry(marked: str, printed: list[str]) -> str | None:
    """The printed option a marked option names: the same words, or its code ("B", "Code 3", "(A)") at the start
    of a printed legend entry ("B = NO OBJECTION AS NOTED")."""
    key = literal_key("option", marked)
    if not key:
        return None
    for option in printed or []:
        okey = literal_key("option", option)
        if okey == key:
            return option
    for option in printed or []:
        m = re.match(r"^\s*(?:code\s*)?\(?\s*([A-Z0-9]{1,2})\s*\)?\s*(?:[=:.\-)]|\s)", str(option), re.I)
        code = re.sub(r"^(?:CODE)?\(?", "", key).rstrip(")")
        if m and m.group(1).upper() == code:
            return option
    return None


def validate_decision(readings: list[dict], target: str | None = None) -> dict:
    usable = [r for r in readings if r.get("legible", True)]
    marked = [r for r in usable if r.get("marked_option") and r.get("mark_type") in ("tick", "circle", "stamp", "handwriting")]
    if not marked:
        return {"state": "no_decision_marked" if usable else "unreadable", "decision": None, "reasons": [], "target": target}
    mapped = []
    for r in marked:
        entry = _legend_entry(r["marked_option"], r.get("options_printed") or [])
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
        reasons.append("the marked option is not one of the options printed on the form, or its printed legend names no decision")
    sources = {str(r.get("source")) for r in marked}
    if "discovery" not in sources or not any(x.startswith("blind") for x in sources):
        reasons.append("not corroborated: needs the discovery reading and a blind reading of the block to agree")
    actors = {r.get("actor") for r in marked}
    if len(actors) > 1:
        reasons.append("the readings disagree on who marked it: " + ", ".join(sorted(str(a) for a in actors)))
    elif not actors <= {"consultant", "client"}:
        reasons.append("the mark is not evidenced as the consultant's or the client's")
    if not target:
        reasons.append("no target component: the page's own identity is not established")
    return {"state": "candidate" if reasons else "validated", "decision": decision, "target": target, "reasons": reasons,
            "legend": sorted({e for _r, e, _d in mapped if e}), "actor": next(iter(actors)) if len(actors) == 1 else None}


# --- one document -----------------------------------------------------------------------------------------------------


'''
between("# --- validation policy", "# --- one document", VALIDATION)
sub('''# --- one document -----------------------------------------------------------------------------------------------------


# --- one document -----------------------------------------------------------------------------------------------------''',
    '''# --- one document -----------------------------------------------------------------------------------------------------''')

# read_document: title-block OCR boxes for region support
sub('''def read_document(run: EvidenceRun, pdf, *, sha256: str, records: list, observations: list, page_texts: dict | None = None,
                  ocr_texts: dict | None = None) -> tuple[list[dict], dict]:''',
    '''def read_document(run: EvidenceRun, pdf, *, sha256: str, records: list, observations: list, page_texts: dict | None = None,
                  ocr_texts: dict | None = None, ocr_lines: dict | None = None) -> tuple[list[dict], dict]:''')
sub('''        texts = [("text", text), ("ocr", ocr)]
        found = _read_page(run, page, sha256=sha256, number=number, facts=facts, texts=texts, reason=",".join(why))''',
    '''        found = _read_page(run, page, sha256=sha256, number=number, facts=facts, reason=",".join(why),
                           ocr_lines=(ocr_lines or {}).get(index) or [])''')

READ_PAGE = r'''def crop_clip(page, region_display: tuple, *, pad: float = 0.35):
    """The display rectangle `crop_png` renders for a region -- the area the blind reader sees."""
    import pymupdf

    x0, y0, x1, y1 = region_display
    w, h = max(x1 - x0, 1), max(y1 - y0, 1)
    px, py = max(40.0, pad * w + 2 * h), max(40.0, pad * h + 3 * h)
    return pymupdf.Rect(max(0, x0 - px), max(0, y0 - py), min(page.rect.width, x1 + px + 6 * h), min(page.rect.height, y1 + py + 6 * h))


def region_texts(page, region_display: tuple | None, ocr_lines: list, *, pad: float = 0.35) -> list:
    """The source text inside the read region: the page's text layer in the crop, and the title-block OCR words whose
    boxes lie in it. Nothing from elsewhere on the page."""
    if region_display is None:
        return []
    clip = crop_clip(page, region_display, pad=pad)
    out = []
    try:
        text = page.get_text("text", clip=clip)
    except Exception:  # noqa: BLE001 -- a page with no text layer supports nothing by text
        text = ""
    if text.strip():
        out.append(("text", text))
    inside = [str(l[4]) for l in ocr_lines or [] if len(l) >= 5 and clip.x0 <= l[0] and l[2] <= clip.x1 and clip.y0 <= l[1] and l[3] <= clip.y1]
    if inside:
        out.append(("ocr", "\n".join(inside)))
    return out


def _read_page(run: EvidenceRun, page, *, sha256: str, number: int, facts: PageFacts, reason: str, ocr_lines: list | None = None) -> dict:
    """One page: discovery, blind reads of the own identity / revision / decision block, validation over all
    readings. The page's own identity and the identities it references are different facts (component 'own' and
    'refN'); nothing here changes a record."""
    observations = []
    discovered = run.call(sha256=sha256, task="discover_page", page=number, reason=reason,
                          parts=[TextPart("task", DISCOVER_TEXT.format(page=number)), ImagePart("page", page_png(page))],
                          schema=DISCOVER_SCHEMA, max_output=800)
    if discovered is None:
        return {"_outcome": "failed" if not run.exhausted else f"budget: {run.exhausted}", "_observations": []}
    det_identity = facts.identities[0] if facts.identities else None
    det_revision = facts.revisions[0] if facts.revisions else None
    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,
              "variant": run.variant, "profile": run.profile, "page_kind": discovered.get("page_kind")}
    own_identity = None
    fields = (("identity", "read_identity", discovered.get("own_identity"), discovered.get("own_identity_region"), det_identity),
              ("revision", "read_revision", discovered.get("own_revision"), discovered.get("own_revision_region"), det_revision))
    for field, task, disc_value, disc_region, det_value in fields:
        region = _det_region(facts, field) or region_from_norm(page, disc_region)
        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts(page, region, ocr_lines or [])
        if region is not None and (disc_value or det_value):
            blind = run.call(sha256=sha256, task=task, page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                             schema=READ_VALUE_SCHEMA, max_output=400)
            if blind is not None:
                readings.append({"source": "blind_small", "value": blind.get("value", ""), "legible": blind.get("legible", False),
                                 "label": blind.get("label_text")})
            verdict = validate_value(field, readings, texts, det_value)
            if run.variant == "EV2" and verdict["state"] in ("conflict", "candidate") and run.escalations < 2:
                run.escalations += 1
                strong = run.call(sha256=sha256, task=task, page=number, reason=reason + ",escalation", tier="standard",
                                  parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                                  schema=READ_VALUE_SCHEMA, max_output=400)
                if strong is not None:
                    readings.append({"source": "blind_standard", "value": strong.get("value", ""), "legible": strong.get("legible", False)})
                    # every reading stays in the verdict: an escalation that agrees with one side of a disagreement
                    # does not erase the other (R7-02); a role mismatch is kept as a conflict
                    verdict = validate_value(field, readings, texts, det_value)
        else:
            verdict = validate_value(field, readings, texts, det_value)
        if verdict["state"] == "unreadable" and not disc_value:
            continue
        if field == "identity" and verdict["state"] in ("validated", "candidate"):
            own_identity = verdict.get("value")
        roles = [n for n in discovered.get("other_numbers") or [] if det_value and literal_key(field, n.get("literal")) == literal_key(field, det_value)]
        reasons = list(verdict["reasons"]) + ([f"discovery lists the deterministic value as a {roles[0].get('role')}"] if roles else [])
        observations.append({**common, "field": field, "component": "own", "role": "own", "value": verdict.get("value"),
                             "value_literal": verdict.get("value_literal"), "value_normalized": verdict.get("value_normalized"),
                             "candidates": verdict.get("candidates"), "state": verdict["state"], "reasons": reasons,
                             "support": verdict.get("support"), "readings": readings, "region": list(region) if region else None,
                             "deterministic": det_value})
    # identities the page references (a listed drawing, a submitted item, a quoted reference): facts of their own,
    # never the page's own identity
    for i, other in enumerate(discovered.get("other_numbers") or []):
        if other.get("literal"):
            observations.append({**common, "field": "identity", "component": f"ref{i}", "role": other.get("role") or "other",
                                 "value": other["literal"], "value_literal": other["literal"],
                                 "value_normalized": literal_key("identity", other["literal"]), "state": "observed_reference",
                                 "reasons": ["referenced by the page, not its own identity"], "readings": [{"source": "discovery", "value": other["literal"]}]})
    if discovered.get("decision_options_printed") or discovered.get("decision_marked_option"):
        readings = [{"source": "discovery", "options_printed": discovered.get("decision_options_printed") or [],
                     "marked_option": discovered.get("decision_marked_option") or "", "mark_type": discovered.get("decision_mark_type"),
                     "actor": discovered.get("decision_actor"), "legible": True}]
        region = region_from_norm(page, discovered.get("decision_region"))
        if region is not None:
            blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.15))],
                             schema=READ_DECISION_SCHEMA, max_output=400)
            if blind is not None:
                readings.append({"source": "blind_small", **blind})
        target = own_identity or det_identity
        verdict = validate_decision(readings, target)
        observations.append({**common, "field": "decision", "component": "own", "role": "own", "value": verdict.get("decision"),
                             "state": verdict["state"], "reasons": verdict["reasons"], "target": target,
                             "legend": verdict.get("legend"), "actor": verdict.get("actor"), "readings": readings,
                             "region": list(region) if region else None,
                             "deterministic": next((r.get("status") for r in facts.records if r.get("status") not in (None, "UR")), None)})
    outcome = "evidence" if observations else "no_components"
    return {"_outcome": outcome, "_observations": observations}


# --- BOQ rows ---------------------------------------------------------------------------------------------------------


'''
between("def _read_page(", "# --- BOQ rows", READ_PAGE)
sub('''# --- BOQ rows ---------------------------------------------------------------------------------------------------------


# --- BOQ rows ---------------------------------------------------------------------------------------------------------''',
    '''# --- BOQ rows ---------------------------------------------------------------------------------------------------------''')

BOQ = r'''_QTY = re.compile(r"^\s*([+-]?)\s*(\d{1,3}(?:,\d{3})+|\d+)(?:\.(\d+))?\s*([A-Za-z]{1,6}\.?)?\s*$")
_DESCRIPTION_COUNT = re.compile(r"^\s*\(\s*(\d+)\s*\)")


def parse_quantity_literal(text) -> tuple[str, tuple | None]:
    """('empty' | 'ok' | 'unsupported', (sign, digits, decimals, unit)) -- decimals, sign and unit are kept, never
    stripped: "1.5" is not "15"; "1,5" (decimal comma or a thousands slip) and anything with stray marks is
    unsupported, not guessed."""
    t = str(text or "").strip()
    if not t:
        return "empty", None
    m = _QTY.match(t)
    if not m:
        return "unsupported", None
    sign, whole, dec, unit = m.groups()
    whole = whole.replace(",", "")
    return "ok", (sign or "+", str(int(whole)), (dec or "").rstrip("0"), (unit or "").rstrip(".").upper())


def validate_boq_row(row: dict, blind: dict | None) -> dict:
    """Part and quantity verified separately (R7-02 / E): `part` verified | conflict | unverified; `quantity` verified |
    conflict | unverified (the blind reading has no quantity) | unresolved (a form the policy cannot compare). A
    quantity printed as "( n )" in the blind description is a located count of its own (`quantity_source`
    description_count): an empty quantity cell is not a quantity absence. Row state: validated only when both are
    verified; part_verified_quantity_unverified keeps the two apart; conflict when either disagrees."""
    if blind is None:
        return {"state": "unverified", "part": "unverified", "quantity": "unverified", "reasons": ["no reading"]}
    if blind.get("row_is_heading"):
        return {"state": "conflict" if row.get("quantity") else "validated", "part": "unverified", "quantity": "unverified",
                "reasons": ["the reading calls the row a heading"]}
    reasons = []
    rp, bp = row.get("part_number"), blind.get("part_number")
    if not bp and rp:
        part = "unverified"
    elif part_literal(rp) == part_literal(bp):
        part = "verified"
    else:
        part = "conflict"
        reasons.append(f"part: reader {rp!r}, blind {bp!r}")
    bq, source = blind.get("quantity"), "quantity_cell"
    if not str(bq or "").strip():
        m = _DESCRIPTION_COUNT.match(str(blind.get("description") or ""))
        if m:
            bq, source = m.group(1), "description_count"
    rs, rv = parse_quantity_literal(row.get("quantity"))
    bs, bv = parse_quantity_literal(bq)
    if bs == "empty":
        quantity = "unverified"
    elif "unsupported" in (rs, bs):
        quantity = "unresolved"
        reasons.append(f"quantity: a form the policy cannot compare (reader {row.get('quantity')!r}, blind {bq!r})")
    elif rs == "empty":
        quantity = "conflict"
        reasons.append(f"quantity: the reader has none, the blind reading {bq!r}")
    elif rv[:3] == bv[:3] and (not rv[3] or not bv[3] or rv[3] == bv[3]):
        quantity = "verified"
    else:
        quantity = "conflict"
        reasons.append(f"quantity: reader {row.get('quantity')!r}, blind {bq!r}")
    if not blind.get("legible", True):
        part = "unverified" if part == "verified" else part
        quantity = "unverified" if quantity == "verified" else quantity
    state = ("conflict" if "conflict" in (part, quantity) else "validated" if part == quantity == "verified" else
             "part_verified_quantity_unverified" if part == "verified" else "unverified")
    return {"state": state, "part": part, "quantity": quantity, "quantity_source": source, "reasons": reasons,
            "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}


'''
between("def validate_boq_row(", "def verify_boq_rows(", BOQ)
p.write_text(s, encoding="utf-8")
print("ok")
