# --- Review 29, C1: identity role guard; C2: conflict adjudication (review29/CONTRACTS.md) -----------------------------
#
# Both decide from the literal, the readings' printed labels, the field region's geometry, discovery's other_numbers and
# the source text of the read regions -- never from a format whitelist, the order of readings, a model's confidence,
# a label file or an expected value.
_OWN_IDENTITY_LABEL = re.compile(
    r"(?:DRAWING|DWG|DRG|DOCUMENT|DOC|SHEET|SUBMITTAL|SUBMISSION|TRANSMITTAL)\s*\.?\s*(?:NO\b|NUMBER\b|NUM\b|#)"
    r"|REVIEW\s*\.?\s*(?:NO\b|NUMBER\b|REF(?:ERENCE)?\b)|\bREFERENCE\s*\.?\s*NO\b|\bREF\s*\.?\s*NO\b", re.I)
_OWN_REVISION_LABEL = re.compile(r"\bREV(?:ISION)?\b(?!\s*HISTORY)", re.I)
_REFERENCE_LABEL = re.compile(
    r"\b(?:DWG|DRAWING|DRG)\s*\.?\s*REF|\bREF(?:ERENCE)?\s*\.?\s*(?:DWG|DRAWING|DRG)\b|\bREFERENCE\s+DRAWING|\bRELATED\s+DRAWING"
    r"|\bPROJECT\s*\.?\s*(?:NO\b|CODE\b|NUMBER\b|#)|\bCONTRACT\s*\.?\s*(?:NO\b|NUMBER\b|#)|\bJOB\s*\.?\s*(?:NO\b|NUMBER\b|#)|\bPLOT\b"
    r"|\bBILL\s*\.?\s*(?:NO\b|NUMBER\b)|\bFORM\s*\.?\s*(?:NO\b|NUMBER\b|#|CODE\b)|\bTEMPLATE\b|\bSPEC(?:IFICATION)?S?\s*\.?\s*(?:REF|SECTION)"
    r"|\bP\s*\.?\s*O\s*\.?\s*(?:NO\b|NUMBER\b)", re.I)
NON_OWN_DISCOVERY_ROLES = frozenset({"referenced_drawing", "listed_item", "form_template", "revision_history", "quoted_reference",
                                     "project_or_contract"})
NON_OWN_TARGETED_ROLES = frozenset({"referenced_identity", "template_or_form_code", "date", "other"})
_CLAUSE = re.compile(r"^\(?\d{1,3}(?:\.\d{1,3})+\)?\.?\s+[A-Za-z]{3,}"
                     r"|^(?:PART|SECTION|CLAUSE|ARTICLE|APPENDIX|ANNEX|CHAPTER)\s+[A-Z0-9][A-Z0-9.\-]{0,7}\s+[A-Za-z]{3,}", re.I)
_PAGE_COUNTER = re.compile(r"^\s*PAGE\s+\d+(?:\s*(?:OF|/)\s*\d+)?\s*$", re.I)
GENERIC_LABELS = frozenset({
    "ARCHITECTURAL", "ARCHITECTURE", "STRUCTURAL", "STRUCTURE", "MECHANICAL", "ELECTRICAL", "PLUMBING", "DRAINAGE", "FIRE", "ALARM",
    "FIGHTING", "PROTECTION", "HVAC", "LIGHTING", "LOW", "CURRENT", "ELV", "MEP", "CIVIL", "LANDSCAPE", "INTERIOR", "INTERIORS",
    "GENERAL", "NOTES", "NOTE", "LEGEND", "DETAILS", "DETAIL", "SCHEDULE", "SCHEDULES", "SPECIFICATION", "SPECIFICATIONS",
    "DATASHEET", "DATA", "SHEET", "DRAWING", "DRAWINGS", "PLAN", "PLANS", "SECTION", "SECTIONS", "ELEVATION", "ELEVATIONS",
    "LAYOUT", "LAYOUTS", "TITLE", "COVER", "INDEX", "CONTENTS", "ACCESSORIES", "SUMMARY", "SCOPE", "APPENDIX", "ATTACHMENT",
    "SHOP", "BUILT", "CONSTRUCTION", "APPROVAL", "REVIEW", "INFORMATION", "SUBMITTAL", "MATERIAL", "TECHNICAL", "PRODUCT",
    "SYSTEM", "SYSTEMS", "DIAGRAM", "RISER", "SCHEMATIC", "TYPICAL", "FLOOR", "GROUND", "ROOF", "BASEMENT"})
MARGIN_BAND = 0.10          # C1 S4: the top / bottom band of a page that is not a drawing sheet


def _plain_words(text: str) -> list[str]:
    return [t for t in (re.sub(r"[.,:;]+$", "", w) for w in str(text or "").split()) if re.fullmatch(r"[A-Za-z]{3,}", t)]


def _strip_label_word(value: str, labels: list) -> str:
    """The literal without one leading word equal to a single-word printed label ("SECTION 28 20 00" read under the
    label SECTION is "28 20 00")."""
    v = str(value or "").strip()
    for label in labels:
        words = re.findall(r"[A-Za-z]+", str(label or ""))
        if len(words) == 1 and len(words[0]) >= 3:
            m = re.match(rf"^\s*{re.escape(words[0])}\b\.?\s*:?\s+(.+)$", v, re.I)
            if m and m.group(1).strip():
                return m.group(1).strip()
    return v


def identity_structure(value, labels: list | None = None) -> str | None:
    """C1 S1-S3 from the literal and its printed labels: revision_token | generic_label | structural_heading | None."""
    v = str(value or "").strip()
    if not v:
        return None
    if bare_revision_token(v):
        return "revision_token"
    core = _strip_label_word(v, labels or [])
    tokens = [re.sub(r"[.,:;]+$", "", t) for t in core.split()]
    if tokens and all(re.fullmatch(r"[A-Za-z]+", t or "") and t.upper() in GENERIC_LABELS for t in tokens):
        return "generic_label"
    if _PAGE_COUNTER.match(core) or _CLAUSE.match(core) or len(_plain_words(core)) >= 2:
        return "structural_heading"
    return None


def _in_margin_band(page, region) -> bool:
    """C1 S4: the field region lies wholly in the top / bottom MARGIN_BAND of a page that is not a drawing sheet."""
    if page is None or region is None:
        return False
    try:
        from app.services import title_block as tb
        if tb.is_drawing_sheet(page):
            return False
        h = page.rect.height
        return region[3] <= MARGIN_BAND * h or region[1] >= (1 - MARGIN_BAND) * h
    except Exception:  # noqa: BLE001 -- no geometry is no evidence of a header / footer
        return False


def _role_evidence(field: str, value, readings: list, discovered: dict | None) -> dict:
    """What the readings, their printed labels and discovery say about the ROLE of one literal (C1 S5, C2 E2 / (a))."""
    key = literal_key(field, value)
    of_v = [r for r in readings if r.get("legible", True) and key and literal_key(field, r.get("value")) == key]
    own_cue = _OWN_IDENTITY_LABEL if field == "identity" else _OWN_REVISION_LABEL
    reference_labels = sorted({str(r.get("label")) for r in of_v if _REFERENCE_LABEL.search(str(r.get("label") or ""))})
    own_label_sources = sorted({str(r.get("source")) for r in of_v
                                if own_cue.search(str(r.get("label") or "")) and not _REFERENCE_LABEL.search(str(r.get("label") or ""))})
    discovery_roles = sorted({str(n.get("role")) for n in (discovered or {}).get("other_numbers") or []
                              if key and literal_key(field, n.get("literal")) == key and n.get("role") in NON_OWN_DISCOVERY_ROLES})
    targeted_roles = sorted({str(r.get("role")) for r in of_v if r.get("source") == "blind_context" and r.get("role") in NON_OWN_TARGETED_ROLES})
    targeted_own = any(r.get("source") == "blind_context" and r.get("role") == _EXPECTED_ROLE[field] for r in of_v)
    contradiction = bool(reference_labels or discovery_roles or targeted_roles)
    return {"literal": str(value or "").strip(), "sources": sorted({str(r.get("source")) for r in of_v}),
            "reference_labels": reference_labels, "discovery_non_own_roles": discovery_roles, "targeted_non_own_roles": targeted_roles,
            "own_label_sources": own_label_sources, "own_role": (bool(own_label_sources) or targeted_own) and not contradiction,
            "role_contradiction": contradiction}


def identity_role_guard(value, readings: list, discovered: dict | None, texts: list, *, page=None, region=None) -> dict | None:
    """C1: None when the literal may be the page's own identity; else {guard, reason, evidence}. S2-S5 are lifted only by
    two readings from distinct sources carrying an own-identity printed label, the literal source-bound, and no role
    contradiction; a model's role claim never lifts. S1 (a bare revision token) is never lifted."""
    labels = [r.get("label") for r in readings if r.get("label")]
    cls = identity_structure(value, labels)
    evidence = _role_evidence("identity", value, readings, discovered)
    if cls is None and _in_margin_band(page, region):
        cls = "running_header_footer"
    if cls is None and evidence["role_contradiction"]:
        cls = "reference_role"
    if cls is None:
        return None
    support, _why = region_support("identity", value, texts)
    evidence = {**evidence, "class": cls, "source_bound": support}
    if cls != "revision_token" and len(evidence["own_label_sources"]) >= 2 and support is not None and not evidence["role_contradiction"]:
        return None
    reasons = {"revision_token": "a bare revision token is a revision, not the document's own identity",
               "generic_label": "a generic discipline / document-type label, not an identity",
               "structural_heading": "a section heading, clause title or page counter, not an identity",
               "running_header_footer": "a running header / footer value of a page that is not a drawing sheet",
               "reference_role": "the evidence names another role for this literal (a reference label, discovery's role or the targeted read's role)"}
    return {"guard": f"identity_role:{cls}", "reason": "identity role guard: " + reasons[cls] +
            " -- held; no independent evidence establishes it as the page's own identity", "evidence": evidence}


def _guard_verdict(field: str, verdict: dict, readings: list, texts: list, discovered, page, region) -> dict:
    # C1 revision 2: a conflict is already held (it keeps its readings and its targeted read); the guard applies to a
    # single-literal verdict -- the field's final verdict after the targeted read and after any C2 resolution
    if not (IDGUARD_ENABLED and field == "identity" and verdict.get("value")) or verdict.get("guard") or verdict.get("state") == "conflict":
        return verdict
    g = identity_role_guard(verdict["value"], readings, discovered, texts, page=page, region=region)
    if g is None:
        return verdict
    return {**verdict, "state": "candidate" if verdict["state"] in ("validated", "candidate") else verdict["state"],
            "guard": g["guard"], "guard_evidence": g["evidence"], "reasons": list(verdict.get("reasons") or []) + [g["reason"]]}


def _value_verdict(field: str, readings: list, texts: list, deterministic, *, discovered=None, page=None, region=None) -> dict:
    """validate_value, then (IG) the identity role guard. With IG off this IS validate_value."""
    return _guard_verdict(field, validate_value(field, readings, texts, deterministic), readings, texts, discovered, page, region)


def _discovery_reading(discovered: dict, field: str, disc_value) -> dict:
    reading = {"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}
    if IDGUARD_ENABLED or ADJUDICATE_ENABLED:      # C1 / C2 weigh the printed label discovery gave (never with both off)
        reading["label"] = (discovered or {}).get(f"own_{field}_label") or ""
    return reading


def adjudicate_conflict(field: str, st: dict, discovered: dict | None, *, identity_established: bool = True) -> dict:
    """C2 over one page field's readings (st: the reader's per-field state). Returns {"record", "verdict"?, "texts"?}.
    A literal V resolves the conflict only when it meets E1-E4 (E5 for a revision), every other literal -- the
    deterministic one included -- is disqualified by a role contradiction or by not being source-bound anywhere while V
    is, and no other literal also meets E1-E4. The verdict is then validate_value over V's readings alone."""
    readings = [r for r in st.get("readings") or [] if not r.get("excluded")]
    by_source = st.get("texts_by_source") or {}
    texts_of = lambda r: by_source.get(str(r.get("source")), st.get("texts") or [])
    all_texts = [t for ts in by_source.values() for t in ts] or list(st.get("texts") or [])
    groups: dict = {}
    for r in readings:
        if r.get("legible", True) and literal_key(field, r.get("value")):
            groups.setdefault(literal_key(field, r["value"]), []).append(r)
    det = st.get("det")
    if det and literal_key(field, det) not in groups:
        groups[literal_key(field, det)] = []
    literals = {}
    for k, rs in groups.items():
        value = rs[0]["value"].strip() if rs else str(det).strip()
        ev = _role_evidence(field, value, readings, discovered)
        bound = [r for r in rs if region_support(field, value, texts_of(r))[0] is not None]
        sources = {str(r.get("source")) for r in rs}
        e = {"value": value, "readings": sorted(sources), "deterministic": bool(det) and literal_key(field, det) == k,
             "E1_legible": bool(rs), "E2_own_role": ev["own_role"], "E3_source_bound": bool(bound),
             "E4_independent_supports": sorted(sources),
             "role_contradiction": ev["role_contradiction"], "role_evidence": ev,
             "source_bound_anywhere": region_support(field, value, all_texts)[0] is not None}
        # E4 (revision 1): two distinct MODEL readings, one blind; the source text is E3, never a support of its own
        e["E4_met"] = len(sources) >= 2 and any(s.startswith("blind") for s in sources)
        e["meets"] = bool(e["E1_legible"] and e["E2_own_role"] and e["E3_source_bound"] and e["E4_met"] and (field == "identity" or identity_established))
        literals[k] = e
    record = {"rule": ADJUDICATE_VERSION, "field": field, "literals": literals, "identity_established": identity_established, "resolved": False}
    winners = [k for k, e in literals.items() if e["meets"]]
    if len(winners) != 1:
        record["why"] = ("no literal meets E1-E4" + ("" if field == "identity" else " and E5")) if not winners else "more than one literal meets E1-E4"
        return {"record": record}
    v = winners[0]
    disq = {}
    for k, e in literals.items():
        if k == v:
            continue
        disq[k] = ("role_contradiction" if e["role_contradiction"] else
                   "not_source_bound" if not e["source_bound_anywhere"] and literals[v]["E3_source_bound"] else None)
    if any(d is None for d in disq.values()):
        record["why"] = "a competing literal is not disqualified: " + ", ".join(literals[k]["value"] for k, d in disq.items() if d is None)
        return {"record": record}
    v_readings = groups[v]
    bound = [r for r in v_readings if region_support(field, literals[v]["value"], texts_of(r))[0] is not None]
    v_texts = texts_of(bound[0])
    verdict = validate_value(field, v_readings, v_texts, det if (det and literal_key(field, det) == v) else None)
    superseded = [{"source": r.get("source"), "value": r.get("value"), "disqualified_by": disq[literal_key(field, r.get("value"))]}
                  for r in readings if r.get("legible", True) and literal_key(field, r.get("value")) in disq]
    if det and literal_key(field, det) in disq:
        superseded.append({"source": "deterministic", "value": det, "disqualified_by": disq[literal_key(field, det)]})
    record.update(resolved=True, value=literals[v]["value"], disqualified=disq)
    verdict = {**verdict, "adjudication": record, "superseded": superseded, "candidates": sorted({e["value"] for e in literals.values()})}
    return {"record": record, "verdict": verdict, "texts": v_texts}


def _identity_established(state: dict, fields: dict) -> bool:
    """The page's own identity is established ON THIS PAGE: a validated, unguarded own identity read here (C2 E5, C4)."""
    sti = state.get("identity") or {}
    verdict = sti.get("verdict") or {}
    return bool(sti and not sti.get("absent") and verdict.get("state") == "validated" and not verdict.get("guard")
                and fields.get(sti.get("key")) == COMPLETED)


def _adjudicate_page(state: dict, fields: dict, discovered: dict, page) -> None:
    for field in ("identity", "revision"):
        st = state.get(field)
        if not st or st.get("absent") or (st.get("verdict") or {}).get("state") != "conflict":
            continue
        res = adjudicate_conflict(field, st, discovered, identity_established=field == "identity" or _identity_established(state, fields))
        st["adjudication"] = res["record"]
        if res.get("verdict") is not None:
            st["verdict"] = _guard_verdict(field, res["verdict"], [r for r in st["readings"] if not r.get("excluded")], res["texts"],
                                           discovered, page, st.get("region"))
