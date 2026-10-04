"""M2 review 09: usable reads (R9-01), explicit fact association (R9-02), per-field source identity (R9-03), item
presence against a heading answer (R9-04). evidence-reader / evidence-policy 2026-09-29.4."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
raw = p.read_bytes()
assert b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# --- versions ------------------------------------------------------------------------------------------------------------
sub('READER_VERSION = "evidence-reader-2026-09-29.3"   # .3: review 08 (field-level outcomes and merge, context selection)',
    'READER_VERSION = "evidence-reader-2026-09-29.4"   # .4: review 09 (usable reads, fact association, source identity)\n'
    '# evidence-reader-2026-09-29.3: review 08 (field-level outcomes and merge, context selection)')
sub('EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.3"   # .3: review 08 -- a BOQ heading answer is a non-item outcome',
    'EVIDENCE_POLICY_VERSION = "evidence-policy-2026-09-29.4"   # .4: review 09 -- usable reads; heading only without item evidence\n'
    '# evidence-policy-2026-09-29.3: review 08 -- a BOQ heading answer is a non-item outcome')

# --- R9-01: request completion and field usability are separate ----------------------------------------------------------
sub('''# Every required read of a page has an outcome of its own, recorded in the page's coverage (`fields`):
#   completed            the field's blind read returned (a value, a negative such as "no decision marked", or an
#                        unreadable result) -- the field was read
#   absent_by_discovery  discovery completed and reported no such field; its region was never read''',
    '''# Every required read of a page has an outcome of its own, recorded in the page's coverage (`fields`), and the
# request behind it has one too (`requests`: ok | failed:<kind> | budget | not_attempted). A returned response is not
# a usable read (M2 review 09, R9-01):
#   completed            the field's blind read is usable: for an identity / a revision a legible blind reading with a
#                        value; for a decision block a legible blind reading (a verified negative -- a legible block
#                        with nothing marked -- is completed)
#   unusable:illegible   the request returned, but the blind answer is not legible: nothing was read
#   unusable:empty       the request returned a legible answer with no value for an identity / a revision: there is
#                        no verified absence of an identity or a revision, so nothing was read
#   absent_by_discovery  discovery completed and reported no such field; its region was never read''')
sub('''def _read_outcome(run: EvidenceRun, result) -> str:
    return COMPLETED if result is not None else _call_outcome(run)
''', '''def _request_outcome(run: EvidenceRun, result) -> str:
    """The request's own outcome: 'ok' when a response came back, else the call's failure or budget refusal."""
    return "ok" if result is not None else _call_outcome(run)


def _value_read_outcome(field: str, readings: list[dict], request: str) -> str:
    """The field outcome of an identity / revision read (R9-01): completed only with a legible blind reading that
    carries a value -- the discovery reading alone never completes a field."""
    if request != "ok":
        return request
    blind = [r for r in readings if str(r.get("source", "")).startswith("blind")]
    if any(r.get("legible") and literal_key(field, r.get("value")) for r in blind):
        return COMPLETED
    return "unusable:empty" if any(r.get("legible") for r in blind) else "unusable:illegible"
''')
sub('''    observations = []
    fields: dict = {}
    discovered = run.call(''', '''    observations = []
    fields: dict = {}
    requests: dict = {}
    discovered = run.call(''')
sub('''        return {"_outcome": "budget: " + (run.exhausted or "refused") if outcome == "budget" else "failed",
                "_observations": [], "_fields": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}}}
    fields["discovery"] = "ok"''', '''        return {"_outcome": "budget: " + (run.exhausted or "refused") if outcome == "budget" else "failed",
                "_observations": [], "_fields": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}},
                "_requests": {"discovery": outcome, **{f: "not_attempted" for f in REQUIRED_FIELDS}}}
    fields["discovery"] = requests["discovery"] = "ok"''')
sub('''    own_identity = None
    spec = (''', '''    own_identity = own_revision = None
    spec = (''')
sub('''        if region is None:
            fields[key] = "incomplete:no_region"
            verdict = validate_value(field, readings, texts, det_value)
        else:
            blind = run.call(sha256=sha256, task=task, page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                             schema=READ_VALUE_SCHEMA, max_output=400)
            fields[key] = _read_outcome(run, blind)
            if blind is not None:''', '''        if region is None:
            fields[key], requests[key] = "incomplete:no_region", "not_attempted"
            verdict = validate_value(field, readings, texts, det_value)
        else:
            blind = run.call(sha256=sha256, task=task, page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS[task]), ImagePart("crop", crop_png(page, region))],
                             schema=READ_VALUE_SCHEMA, max_output=400)
            requests[key] = _request_outcome(run, blind)
            if blind is not None:''')
sub('''                else:
                    fields[key + ":escalation"] = _call_outcome(run)
        if verdict["state"] == "unreadable" and not disc_value:
            continue
        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_identity = verdict.get("value")''', '''                else:
                    fields[key + ":escalation"] = _call_outcome(run)
            fields[key] = _value_read_outcome(field, readings, requests[key])
        if verdict["state"] == "unreadable" and not disc_value:
            continue
        if field == "identity" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_identity = verdict.get("value")
        if field == "revision" and verdict["state"] in ("validated", "candidate") and fields[key] == COMPLETED:
            own_revision = verdict.get("value")''')
sub('''                             "support": verdict.get("support"), "readings": readings, "region": list(region) if region else None,
                             "deterministic": det_value, "read": fields[key]})''', '''                             "support": verdict.get("support"), "readings": readings, "region": list(region) if region else None,
                             "deterministic": det_value, "read": fields[key], "request": requests.get(key),
                             # the component identity this revision was read for (R9-02); an identity is its own
                             **({"target": own_identity or det_identity} if field == "revision" else {})})''')
sub('''            blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason,
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
                             "readings": readings, "region": list(region) if region else None, "read": fields["own:decision"],''',
    '''            blind = run.call(sha256=sha256, task="read_decision", page=number, reason=reason,
                             parts=[TextPart("task", READ_TEXTS["read_decision"]), ImagePart("crop", crop_png(page, region, pad=0.15))],
                             schema=READ_DECISION_SCHEMA, max_output=400)
            requests["own:decision"] = _request_outcome(run, blind)
            if blind is not None:
                readings.append({"source": "blind_small", **blind})
            # a decision block is read only by a legible blind reading: its verified negative needs one too (R9-01)
            fields["own:decision"] = (requests["own:decision"] if blind is None else
                                      COMPLETED if blind.get("legible", True) else "unusable:illegible")
        if region is None:
            requests["own:decision"] = "not_attempted"
        target = own_identity or det_identity
        verdict = validate_decision(readings, target)
        reasons = list(verdict["reasons"])
        state = verdict["state"]
        if fields["own:decision"] != COMPLETED:
            reasons.append(f"read not completed ({fields['own:decision']}): unverified")
            # nothing verified: a positive stays a candidate; a negative from discovery alone is no verified absence
            state = "candidate" if state == "validated" else "unverified" if state in ("no_decision_marked", "not_a_decision") else state
        observations.append({**common, "field": "decision", "component": "own", "role": "own", "value": verdict.get("decision"),
                             "state": state, "reasons": reasons, "target": target,
                             # the revision the decision was read with, when this read established one (R9-02)
                             "target_revision": own_revision, "legend": verdict.get("legend"), "actor": verdict.get("actor"),
                             "readings": readings, "region": list(region) if region else None, "read": fields["own:decision"],
                             "request": requests.get("own:decision"),''')
sub('''    else:
        fields["own:decision"] = ABSENT_BY_DISCOVERY
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields}''', '''    else:
        fields["own:decision"] = ABSENT_BY_DISCOVERY
    required = [fields.get(f) for f in REQUIRED_FIELDS]
    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)
    outcome = ("evidence" if observations else "no_components") if complete else "partial"
    return {"_outcome": outcome, "_observations": observations, "_fields": fields, "_requests": requests}''')
sub('''        entry["fields"] = found.pop("_fields", {})
        out.extend(found.pop("_observations"))''', '''        entry["fields"] = found.pop("_fields", {})
        entry["requests"] = found.pop("_requests", {})
        out.extend(found.pop("_observations"))''')

# --- R9-04: item presence against a heading answer ------------------------------------------------------------------------
sub('''def parse_quantity_literal(text) -> tuple[str, tuple | None]:
    """('empty' | 'ok' | 'unsupported', (sign, digits, decimals, unit)) -- decimals, sign and unit are kept, never
    stripped: "1.5" is not "15"; "1,5" (decimal comma or a thousands slip) and anything with stray marks is
    unsupported, not guessed."""
    t = str(text or "").strip()''', '''def quantity_present(value) -> bool:
    """A quantity is present when anything is printed: numeric 0 and "0" are present values; only None and blank text
    are absence (R9-04)."""
    return value is not None and str(value).strip() != ""


def parse_quantity_literal(text) -> tuple[str, tuple | None]:
    """('empty' | 'ok' | 'unsupported', (sign, digits, decimals, unit)) -- decimals, sign and unit are kept, never
    stripped: "1.5" is not "15"; "1,5" (decimal comma or a thousands slip) and anything with stray marks is
    unsupported, not guessed. Zero is a value, never empty."""
    t = str(text).strip() if quantity_present(text) else ""''')
sub('''    if blind.get("row_is_heading"):
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
                "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}''',
    '''    reader = {k: row.get(k) for k in ("part_number", "quantity", "description")}      # the reader's literals, as given
    if blind.get("row_is_heading"):
        # A heading answer is a row-type claim, never validated equipment data (M2 review 08, R8-04). It confirms a
        # non-item only where neither side carries item evidence (R9-04): a part, a present quantity (0 and "0" are
        # present), or a "( n )" count in either description -- the reader's included, which the reading may omit.
        # Any of them against a heading answer is a row-type disagreement -- held. Nothing is removed or inferred.
        if not blind.get("legible", True):
            return {"state": "unverified", "part": "unverified", "quantity": "unverified", "row_type": "unverified",
                    "reasons": ["the reading is not legible"], "reader": reader}
        evidence = [
            f"reader part {row.get('part_number')!r}" if str(row.get("part_number") or "").strip() else "",
            f"reader quantity {row.get('quantity')!r}" if quantity_present(row.get("quantity")) else "",
            f"count {m.group(0).strip()!r} in the reader's description" if (m := _DESCRIPTION_COUNT.match(str(row.get("description") or ""))) else "",
            f"reading part {blind.get('part_number')!r}" if str(blind.get("part_number") or "").strip() else "",
            f"reading quantity {blind.get('quantity')!r}" if quantity_present(blind.get("quantity")) else "",
            f"count {m.group(0).strip()!r} in the reading" if (m := _DESCRIPTION_COUNT.match(str(blind.get("description") or ""))) else ""]
        evidence = [x for x in evidence if x]
        if evidence:
            return {"state": "conflict", "part": "unverified", "quantity": "unverified", "row_type": "disputed",
                    "reasons": ["the reading calls the row a heading, but the row carries item evidence: " + ", ".join(evidence)],
                    "reader": reader, "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}
        return {"state": "not_an_item", "part": "not_applicable", "quantity": "not_applicable", "row_type": "heading_confirmed",
                "reasons": ["neither the reader nor the reading carries item evidence, and the reading confirms a heading"],
                "reader": reader, "blind": {k: blind.get(k) for k in ("part_number", "quantity", "description")}}''')
sub('''    bq, source = blind.get("quantity"), "quantity_cell"
    if not str(bq or "").strip():''', '''    bq, source = blind.get("quantity"), "quantity_cell"
    if not quantity_present(bq):''')
sub('''        verdict = validate_boq_row({"part_number": row.get("catalog_no") or row.get("part_number"), "quantity": row.get("quantity")}, blind)''',
    '''        # the reader's item evidence as it was read -- its description (and any "( n )" count) included (R9-04)
        verdict = validate_boq_row({"part_number": row.get("catalog_no") or row.get("part_number"), "quantity": row.get("quantity"),
                                    "description": row.get("description")}, blind)''')

# --- R9-01 / R9-03: merge keeps unapplied readings as attempt evidence; the envelope never relabels fields -----------
sub('''    env = ai["envelopes"].get(key)
    if env is None or env.get("stale"):
        if env is not None:
            ai["superseded"] = (ai["superseded"] + [{"key": key, **env}])[-4:]
        env = {"profile": profile, "variant": variant, "read_sha256": sha256, "pages": {}, "stale": None}''',
    '''    env = ai["envelopes"].get(key)
    if env is None or env.get("stale"):
        if env is not None:
            ai["superseded"] = (ai["superseded"] + [{"key": key, **env}])[-4:]
        env = {"profile": profile, "variant": variant, "read_sha256": sha256, "pages": {}, "stale": None}
    elif not env.get("read_sha256"):
        # the bytes this envelope was last read from; each field keeps its own source in its provenance, and a field
        # read from unknown bytes stays unknown (R9-03) -- nothing retained is relabelled with this attempt's hash
        env = {**env, "read_sha256": sha256}''')
sub('''    changed = []
    for entry in (attempt.get("coverage") or {}).get("pages") or []:''', '''    changed, unapplied = [], []
    for entry in (attempt.get("coverage") or {}).get("pages") or []:''')
sub('''            elif new and (existing is None or existing.get("status") == "incomplete"):
                page["fields"][fkey] = {"observations": new, "status": "incomplete", "provenance": {**provenance, "read": outcome},
                                        "history": (existing or {}).get("history") or []}
                changed.append(f"{pno}:{fkey} (incomplete)")''', '''            elif new and (existing is None or existing.get("status") == "incomplete"):
                page["fields"][fkey] = {"observations": new, "status": "incomplete", "provenance": {**provenance, "read": outcome},
                                        "history": (existing or {}).get("history") or []}
                changed.append(f"{pno}:{fkey} (incomplete)")
            elif new:
                # read, but not usable against the evidence kept: recorded with the attempt, never applied (R9-01)
                unapplied += [{"page": o.get("page"), "component": o.get("component") or "own", "field": o.get("field"),
                               "value": o.get("value"), "state": o.get("state"), "read": outcome, "target": o.get("target")}
                              for o in new]''')
sub('''    summary.update(key=key, variant=variant, profile=profile, read_sha256=sha256, changed=changed,
                   pages={str(e.get("page")): {"outcome": e.get("outcome"), "fields": e.get("fields")} for e in (attempt.get("coverage") or {}).get("pages") or []},''',
    '''    summary.update(key=key, variant=variant, profile=profile, read_sha256=sha256, changed=changed, unapplied=unapplied,
                   pages={str(e.get("page")): {"outcome": e.get("outcome"), "fields": e.get("fields"), "requests": e.get("requests")}
                          for e in (attempt.get("coverage") or {}).get("pages") or []},''')

# --- R9-03 + R9-02: evidence_for -- per-field source identity; explicit association ------------------------------------
i = s.index("def evidence_for(")
j = s.index("def last_known(")
s = s[:i] + '''def _usable_value(entry: dict | None) -> str | None:
    """A field's current value when it can anchor an association: read (completed, or legacy) and carrying a value."""
    if not entry or entry.get("status") not in (COMPLETED, "legacy"):
        return None
    values = [o.get("value") for o in entry.get("observations") or [] if o.get("value") not in (None, "")]
    return values[0] if values else None


def association_of(o: dict, current_identity: str | None, current_revision: str | None) -> dict | None:
    """The association of a dependent fact (a revision or a decision of the page's own component) with the component
    as it is read now (M2 review 09, R9-02). A fact keeps the target it was read for; it is never reattached:
      current               its target is the component's current identity (and, for a decision, its revision)
      held:target_changed   the component's current identity is another one: the fact stays with its own target
      held:revision_changed a decision read with a known revision the component no longer carries
      by_target             no usable current identity: associated only by its own recorded target
      not_recorded          a fact that never recorded a target (review 06 evidence): none is invented"""
    if o.get("field") not in ("decision", "revision") or not _field_key(o).startswith("own:"):
        return None
    target = o.get("target")
    if not target:
        return {"status": "not_recorded"}
    base = {"target": target, "current_identity": current_identity}
    if current_identity is None:
        return {"status": "by_target", **base, "reason": "no usable current identity: associated only by its recorded target"}
    if literal_key("identity", target) != literal_key("identity", current_identity):
        return {"status": "held:target_changed", **base, "reason": f"read for {target!r}; the component now reads {current_identity!r}"}
    tr = o.get("target_revision") if o.get("field") == "decision" else None
    if tr and current_revision and literal_key("revision", tr) != literal_key("revision", current_revision):
        return {"status": "held:revision_changed", **base, "target_revision": tr, "current_revision": current_revision,
                "reason": f"read with revision {tr!r}; the component now reads {current_revision!r}"}
    return {"status": "current", **base}


def evidence_for(ai: dict | None, *, sha256: str | None, profile: str | None, variant: str | None,
                 policies: set | None = None, accept_unknown_profile: bool = False, historical_source: dict | None = None) -> dict:
    """The AI evidence that applies to a requested context -- source hash, extraction profile, verification variant
    and (optionally) compatible policies -- as an explicit state (M2 review 08, R8-02; review 09, R9-03):
      current         evidence read for exactly this context (`envelope`, `observations`; `incomplete` lists fields
                      known only from unsuccessful reads; `withheld` lists fields of this envelope that are not)
      pending         reading was attempted for this context and gave no evidence yet
      unavailable     nothing was read for this context (or none under a compatible policy); `history` names what exists
      stale           the evidence for this context was read from other bytes
      unknown_source  the evidence for this context records no source hash: it is not exact-file evidence
      source_required the request names no source hash: exact-file evidence cannot be selected without one
    Source identity is decided per field, by the hash in the field's own provenance: a retained field keeps the bytes it
    was read from, whatever a later attempt read. Another profile's or variant's evidence is never returned for this
    one. An unknown legacy *profile* is used only when the caller says so (`accept_unknown_profile`); that says nothing
    about the bytes. `historical_source` -- {"manifest": <run manifest>, "sha256": <the hash it binds this document
    to>} -- is a separate, explicit historical mode: fields with *no* recorded hash count as read from the manifest's
    bytes when those are the requested bytes; a known mismatch never does. Operational callers never pass it.
    Each dependent fact carries its `association` with the component as read now (`association_of`)."""
    ai = _normalise_ai(ai) if ai else _normalise_ai(None)
    context = {"sha256": sha256, "profile": profile, "variant": variant, "policies": sorted(policies) if policies else None}
    history = sorted(ai["envelopes"])
    if not sha256:
        return {"state": "source_required", "reason": "the request names no source hash: exact-file evidence needs one",
                "context": context, "history": history}
    key = envelope_key(profile, variant)
    env, via = ai["envelopes"].get(key), None
    if env is None and accept_unknown_profile:
        env, via = ai["envelopes"].get(envelope_key(UNKNOWN_PROFILE, variant)), "unknown legacy profile accepted by the caller"
    if env is None:
        attempted = any(a.get("key") == key for a in ai["attempts"])
        return {"state": "pending" if attempted else "unavailable",
                "reason": f"reading was attempted for {key} and gave no evidence yet" if attempted else f"no evidence was read for {key}",
                "context": context, "history": history}
    if env.get("stale") or (env.get("read_sha256") and env.get("read_sha256") != sha256):
        return {"state": "stale", "reason": env.get("stale") or "read from other bytes", "context": context, "history": history}
    binding = None
    if historical_source and historical_source.get("manifest") and historical_source.get("sha256") == sha256:
        binding = f"historical:{historical_source['manifest']}"
    pages, withheld = {}, {}
    for pno, page in (env.get("pages") or {}).items():
        kept = {}
        for fk, e in page.get("fields", {}).items():
            if policies and e["provenance"].get("policy") not in policies:
                continue
            source = e["provenance"].get("read_sha256")
            if source == sha256:
                kept[fk] = e
            elif not source and binding:
                kept[fk] = {**e, "source_binding": binding}
            else:
                withheld[f"{pno}:{fk}"] = "unknown_source" if not source else "stale"
        if kept:
            pages[pno] = {"fields": kept}
    if not pages:
        if withheld:
            state = "stale" if "stale" in withheld.values() else "unknown_source"
            return {"state": state, "reason": ("read from other bytes" if state == "stale" else
                                               "the evidence records no source hash: it is not exact-file evidence"),
                    "context": context, "history": history, "withheld": withheld}
        # an envelope exists only because an attempt for this context was merged into it
        incompatible = bool(policies and env.get("pages"))
        return {"state": "unavailable" if incompatible else "pending",
                "reason": "no evidence under a compatible policy" if incompatible else "reading was attempted for this context; no evidence yet",
                "context": context, "history": history}
    current = _flatten({**{k: v for k, v in env.items() if k not in ("pages", "observations")}, "pages": pages})
    for o in current["observations"]:
        page = pages[str(o.get("page") or 1)]["fields"]
        assoc = association_of(o, _usable_value(page.get("own:identity")), _usable_value(page.get("own:revision")))
        if assoc is not None:
            o["association"] = assoc
    incomplete = sorted(f"{p}:{fk}" for p, page in pages.items() for fk, e in page["fields"].items() if e["status"] == "incomplete")
    return {"state": "current", "context": context, "via": via, "mode": "historical" if binding and any(
                e.get("source_binding") for page in pages.values() for e in page["fields"].values()) else "operational",
            "envelope": current, "observations": current["observations"], "incomplete": incomplete, "withheld": withheld,
            "history": history}


''' + s[j:]
sub('''            out += [dict(o, provenance=entry["provenance"], field_status=entry["status"]) for o in entry["observations"]]''',
    '''            out += [dict(o, provenance=entry["provenance"], field_status=entry["status"],
                         **({"source_binding": entry["source_binding"]} if entry.get("source_binding") else {}))
                    for o in entry["observations"]]''')
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
