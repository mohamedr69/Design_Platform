"""M2 review 08 (R8-01, R8-02, R8-04): field-level read outcomes and merge; evidence selected by requested context;
BOQ heading is a non-item outcome, never a validated row."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\evidence_reader.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new)


def between(start, end, new):
    global s
    i, j = s.index(start), s.index(end)
    assert i < j
    s = s[:i] + new + s[j:]


sub('READER_VERSION = "evidence-reader-2026-09-29.2"   # .2: review 07 (validation policy .2, lifecycle, profile)',
    'READER_VERSION = "evidence-reader-2026-09-29.3"   # .3: review 08 (field-level outcomes and merge, context selection)\n'
    '# evidence-reader-2026-09-29.2: review 07 (validation policy .2, lifecycle, profile)')
sub('EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.2"',
    'EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.3"   # .3: review 08 -- a BOQ heading answer is a non-item outcome\n'
    '# evidence-policy-2026-09-29.2: review 07 (region-bound literal support, decision corroboration, numeric semantics)')

# --- read_document: page outcome from field outcomes -----------------------------------------------------------------
sub('''        entry["calls"] = run.calls - before
        entry["outcome"] = found.pop("_outcome")
        out.extend(found.pop("_observations"))
        coverage["pages"].append(entry)
    coverage["calls"] = run.calls - calls_before
    outcomes = [str(e.get("outcome")) for e in coverage["pages"]]
    coverage["outcome"] = ("budget" if run.exhausted else
                           "partial" if any(o == "failed" or o.startswith("budget") for o in outcomes) else "complete")
    return out, coverage''',
    '''        entry["calls"] = run.calls - before
        entry["outcome"] = found.pop("_outcome")
        entry["fields"] = found.pop("_fields", {})
        out.extend(found.pop("_observations"))
        coverage["pages"].append(entry)
    coverage["calls"] = run.calls - calls_before
    outcomes = [str(e.get("outcome")) for e in coverage["pages"]]
    coverage["outcome"] = ("budget" if run.exhausted else
                           "partial" if any(o in ("failed", "partial") or o.startswith("budget") for o in outcomes) else "complete")
    return out, coverage''')

READ_PAGE = r'''# --- read outcomes (M2 review 08, R8-01) ------------------------------------------------------------------------------
#
# Every required read of a page has an outcome of its own, recorded in the page's coverage (`fields`):
#   completed            the field's blind read returned (a value, a negative such as "no decision marked", or an
#                        unreadable result) -- the field was read
#   absent_by_discovery  discovery completed and reported no such field; its region was never read
#   incomplete:no_region discovery named the field but gave no readable region: nothing was read
#   failed:<kind>        the read's request failed (timeout, transport, invalid response, ...)
#   budget               the read was refused by a budget or the ledger
# The page outcome is `evidence` only when every required read is `completed` or `absent_by_discovery`; any other
# field outcome makes it `partial`. Discovery failing makes the page `failed` / `budget`.

REQUIRED_FIELDS = ("own:identity", "own:revision", "own:decision")
COMPLETED = "completed"
ABSENT_BY_DISCOVERY = "absent_by_discovery"


def _call_outcome(run: EvidenceRun) -> str:
    """The outcome of the call `run.call` just made (from its log): 'ok', 'budget' or 'failed:<kind>'."""
    last = (run.log[-1] if run.log else {}) or {}
    outcome = str(last.get("outcome") or "")
    if outcome == "ok":
        return "ok"
    if outcome.startswith("budget") or run.exhausted:
        return "budget"
    return "failed:" + (outcome or "unknown")


def _read_outcome(run: EvidenceRun, result) -> str:
    return COMPLETED if result is not None else _call_outcome(run)


def _read_page(run: EvidenceRun, page, *, sha256: str, number: int, facts: PageFacts, reason: str, ocr_lines: list | None = None) -> dict:
    """One page: discovery, blind reads of the own identity / revision / decision block, validation over all
    readings. Every read's outcome is recorded (`_fields`); the page outcome follows from them. The page's own
    identity and the identities it references are different facts (component 'own' and 'refN'); nothing here
    changes a record."""
    observations = []
    fields: dict = {}
    discovered = run.call(sha256=sha256, task="discover_page", page=number, reason=reason,
                          parts=[TextPart("task", DISCOVER_TEXT.format(page=number)), ImagePart("page", page_png(page))],
                          schema=DISCOVER_SCHEMA, max_output=800)
    if discovered is None:
        outcome = _call_outcome(run)
        return {"_outcome": "budget: " + (run.exhausted or "refused") if outcome == "budget" else "failed",
                "_observations": [], "_fields": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}}}
    fields["discovery"] = "ok"
    det_identity = facts.identities[0] if facts.identities else None
    det_revision = facts.revisions[0] if facts.revisions else None
    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,
              "variant": run.variant, "profile": run.profile, "page_kind": discovered.get("page_kind")}
    own_identity = None
    spec = (("identity", "read_identity", discovered.get("own_identity"), discovered.get("own_identity_region"), det_identity),
            ("revision", "read_revision", discovered.get("own_revision"), discovered.get("own_revision_region"), det_revision))
    for field, task, disc_value, disc_region, det_value in spec:
        key = f"own:{field}"
        region = _det_region(facts, field) or region_from_norm(page, disc_region)
        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts(page, region, ocr_lines or [])
        if not (disc_value or det_value):
            fields[key] = ABSENT_BY_DISCOVERY
            continue
        if region is None:
            fields[key] = "incomplete:no_region"
            verdict = validate_value(field, readings, texts, det_value)
        else:
            blind = run.call(sha256=sha256, task=task, page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                             schema=READ_VALUE_SCHEMA, max_output=400)
            fields[key] = _read_outcome(run, blind)
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
        if verdict["state"] == "unreadable" and not disc_value:
            continue
        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_identity = verdict.get("value")
        roles = [n for n in discovered.get("other_numbers") or [] if det_value and literal_key(field, n.get("literal")) == literal_key(field, det_value)]
        reasons = list(verdict["reasons"]) + ([f"discovery lists the deterministic value as a {roles[0].get('role')}"] if roles else [])
        if fields[key] != COMPLETED:
            reasons.append(f"read not completed ({fields[key]}): unverified")
        observations.append({**common, "field": field, "component": "own", "role": "own", "value": verdict.get("value"),
                             "value_literal": verdict.get("value_literal"), "value_normalized": verdict.get("value_normalized"),
                             "candidates": verdict.get("candidates"), "state": verdict["state"], "reasons": reasons,
                             "support": verdict.get("support"), "readings": readings, "region": list(region) if region else None,
                             "deterministic": det_value, "read": fields[key]})
    # identities the page references: facts of their own, read by discovery (completed with it)
    for i, other in enumerate(discovered.get("other_numbers") or []):
        if other.get("literal"):
            fields[f"ref{i}:identity"] = COMPLETED
            observations.append({**common, "field": "identity", "component": f"ref{i}", "role": other.get("role") or "other",
                                 "value": other["literal"], "value_literal": other["literal"],
                                 "value_normalized": literal_key("identity", other["literal"]), "state": "observed_reference",
                                 "reasons": ["referenced by the page, not its own identity"], "read": COMPLETED,
                                 "readings": [{"source": "discovery", "value": other["literal"]}]})
    if discovered.get("decision_options_printed") or discovered.get("decision_marked_option"):
        readings = [{"source": "discovery", "options_printed": discovered.get("decision_options_printed") or [],
                     "marked_option": discovered.get("decision_marked_option") or "", "mark_type": discovered.get("decision_mark_type"),
                     "actor": discovered.get("decision_actor"), "legible": True}]
        region = region_from_norm(page, discovered.get("decision_region"))
        if region is None:
            fields["own:decision"] = "incomplete:no_region"
        else:
            blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.15))],
                             schema=READ_DECISION_SCHEMA, max_output=400)
            fields["own:decision"] = _read_outcome(run, blind)
            if blind is not None:
                readings.append({"source": "blind_small", **blind})
        target = own_identity or det_identity
        verdict = validate_decision(readings, target)
        reasons = list(verdict["reasons"])
        if fields["own:decision"] != COMPLETED:
            reasons.append(f"read not completed ({fields['own:decision']}): unverified")
        observations.append({**common, "field": "decision", "component": "own", "role": "own", "value": verdict.get("decision"),
                             "state": verdict["state"] if fields["own:decision"] == COMPLETED or verdict["state"] != "validated" else "candidate",
                             "reasons": reasons, "target": target, "legend": verdict.get("legend"), "actor": verdict.get("actor"),
                             "readings": readings, "region": list(region) if region else None, "read": fields["own:decision"],
                             "deterministic": next((r.get("status") for r in facts.records if r.get("status") not in (None, "UR")), None)})
    else:
        fields["own:decision"] = ABSENT_BY_DISCOVERY
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields}


# --- BOQ rows ---------------------------------------------------------------------------------------------------------


'''
between("def _read_page(", "# --- BOQ rows", READ_PAGE)
sub('''# --- BOQ rows ---------------------------------------------------------------------------------------------------------


# --- BOQ rows ---------------------------------------------------------------------------------------------------------''',
    '''# --- BOQ rows ---------------------------------------------------------------------------------------------------------''')

# --- R8-04: heading ---------------------------------------------------------------------------------------------------
sub('''    if blind.get("row_is_heading"):
        return {"state": "conflict" if row.get("quantity") else "validated", "part": "unverified", "quantity": "unverified",
                "reasons": ["the reading calls the row a heading"]}''',
    '''    if blind.get("row_is_heading"):
        # A heading answer is a row-type claim, never validated equipment data (M2 review 08, R8-04). It confirms a
        # non-item only where the reader has no item either (no part, no quantity) and the reading carries no count;
        # a reader part or quantity, or a "( n )" count in the reading, is a row-type disagreement -- held.
        count = _DESCRIPTION_COUNT.match(str(blind.get("description") or ""))
        if not blind.get("legible", True):
            return {"state": "unverified", "part": "unverified", "quantity": "unverified", "row_type": "unverified",
                    "reasons": ["the reading is not legible"]}
        if row.get("part_number") or row.get("quantity") or count or blind.get("part_number") or str(blind.get("quantity") or "").strip():
            return {"state": "conflict", "part": "unverified", "quantity": "unverified", "row_type": "disputed",
                    "reasons": ["the reading calls the row a heading, but the row carries item data: "
                                + ", ".join(x for x in (f"reader part {row.get('part_number')!r}" if row.get("part_number") else "",
                                                        f"reader quantity {row.get('quantity')!r}" if row.get("quantity") else "",
                                                        f"count {count.group(0)!r} in the reading" if count else "",
                                                        f"reading part {blind.get('part_number')!r}" if blind.get("part_number") else "") if x)],
                    "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}
        return {"state": "not_an_item", "part": "not_applicable", "quantity": "not_applicable", "row_type": "heading_confirmed",
                "reasons": ["the reader has no item data and the reading confirms a heading"],
                "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}''')
p.write_text(s, encoding="utf-8")
print("ok")
