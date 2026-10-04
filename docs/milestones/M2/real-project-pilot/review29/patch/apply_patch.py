"""Apply the Review 29 changes to C:/t/iso/cand-r29/backend/app/ai/evidence_reader.py with exact, counted anchors.
Every replacement asserts how many times its anchor occurs; nothing is applied when any count differs."""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
F = pathlib.Path("C:/t/iso/cand-r29/backend/app/ai/evidence_reader.py")
src = F.read_text(encoding="utf-8")
assert "IDGUARD_ENABLED" not in src, "already patched"
block = lambda n: (HERE / n).read_text(encoding="utf-8")

edits = []   # (anchor, replacement, expected count)

# 1. switches and identities: before MIN_REQUEST_S
a = "MIN_REQUEST_S = 20.0            # E: no request is started with less than this left of the job's elapsed budget"
edits.append((a, block("block_flags.py") + a, 1))

# 2. C1 / C2 / C3 / C4 functions: before _legend_entry (C1, C2) and before the one-document section (C3, C4)
a = "def _legend_entry(marked: str, printed: list[str]) -> str | None:"
edits.append((a, block("block_guard.py") + "\n\n" + a, 1))
a = "# --- one document -----------------------------------------------------------------------------------------------------"
edits.append((a, block("block_decision.py") + "\n\n" + a, 1))

# 3. discovery readings carry discovery's printed label under IG / CA (both reader paths)
a = 'readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]'
edits.append((a, "readings = [_discovery_reading(discovered, field, disc_value)]", 2))

# 4. every identity / revision verdict goes through _value_verdict (IG off: validate_value itself)
a = "verdict = validate_value(field, readings, texts, det_value)"
edits.append((a, "verdict = _value_verdict(field, readings, texts, det_value, discovered=discovered, page=page, region=region)", 6))
a = 'st["verdict"] = validate_value(field, [r for r in st["readings"] if not r.get("excluded")], st["texts"], st["det"])'
b = ('st["verdict"] = _value_verdict(field, [r for r in st["readings"] if not r.get("excluded")], st["texts"], st["det"],\n'
     '                                     discovered=discovered, page=page, region=st["region"])')
edits.append((a, b, 1))

# 5. CA: the source text of each reading's region
a = '        st = state[field] = {"key": key, "region": region, "readings": readings, "texts": texts, "disc": disc_value, "det": det_value}\n'
b = a + ('        if ADJUDICATE_ENABLED:      # C2: each reading is weighed against the source text of the region it was made from\n'
         '            st["texts_by_source"] = {"discovery": texts, "blind_small": texts, "blind_standard": texts}\n')
edits.append((a, b, 1))
a = "        reading, t_region, t_texts = got\n"
b = a + ('        if ADJUDICATE_ENABLED:\n'
         '            st.setdefault("texts_by_source", {})["blind_context"] = t_texts\n')
edits.append((a, b, 1))

# 6. CA: adjudicate after every reading of the page exists (after the targeted reads), before the observations
a = ('                                     discovered=discovered, page=page, region=st["region"])\n'
     '    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,\n')
b = ('                                     discovered=discovered, page=page, region=st["region"])\n'
     '    if ADJUDICATE_ENABLED:\n'
     '        _adjudicate_page(state, fields, discovered, page)\n'
     '    common = {"page": number, "kind": "ai_evidence", "version": READER_VERSION, "policy": EVIDENCE_POLICY_VERSION,\n')
edits.append((a, b, 1))

# 7. DR: the decision-region path replaces the discovery-only decision block in the required-first path
a = '    decision = None\n    if discovered.get("decision_options_printed") or discovered.get("decision_marked_option"):\n'
b = ('    decision = None\n'
     '    if DECISION_REGION_ENABLED:\n'
     '        decision = _decision_region_read(run, page, sha256=sha256, number=number, reason=reason, discovered=discovered, located=located,\n'
     '                                         ocr_lines=ocr_lines, fields=fields, requests=requests)\n'
     '    elif discovered.get("decision_options_printed") or discovered.get("decision_marked_option"):\n')
edits.append((a, b, 1))

# 8. the decision verdict of the required-first path: DR's corroboration rule; PA's page target
a = ('        target = own_identity or det_identity\n'
     '        verdict = validate_decision(decision["readings"], target)\n')
b = ('        target = _page_target(state, fields, det_identity) if ASSOC_ENABLED else own_identity or det_identity\n'
     '        verdict = (validate_decision_dr(decision["readings"], target) if decision.get("dr") is not None else\n'
     '                   validate_decision(decision["readings"], target))\n')
edits.append((a, b, 1))

# 9. end of _finish_page: decision path record, adjudication record, page association
a = ('    required = [fields.get(f) for f in REQUIRED_FIELDS]\n'
     '    complete = all(o in (COMPLETED, ABSENT_BY_DISCOVERY) for o in required)\n'
     '    outcome = ("evidence" if observations else "no_components") if complete else "partial"\n'
     '    return {"_outcome": outcome, "_observations": observations, "_fields": fields, "_requests": requests}\n'
     '\n\n# --- BOQ rows')
b = ('    if decision is not None and decision.get("dr") is not None:\n'
     '        for o in observations:\n'
     '            if o.get("field") == "decision" and o.get("component") == "own":\n'
     '                o["decision_path"] = decision["dr"]\n'
     '    if ADJUDICATE_ENABLED:\n'
     '        for o in observations:\n'
     '            st = ctx["state"].get(o.get("field")) if o.get("component") == "own" else None   # `state` is rebound above\n'
     '            if st and st.get("adjudication"):\n'
     '                o["adjudication"] = st["adjudication"]\n'
     '                if (st.get("verdict") or {}).get("superseded"):\n'
     '                    o["superseded"] = st["verdict"]["superseded"]\n'
     '    if ASSOC_ENABLED:\n'
     '        _apply_page_association(observations, number=number, state=ctx["state"], fields=fields, det_identity=det_identity)\n' + a)
edits.append((a, b, 1))

# 10. association_of keeps a PA hold (data-driven: only observations that PA wrote carry page_binding)
a = ('    if o.get("field") not in ("decision", "revision") or not _field_key(o).startswith("own:"):\n'
     '        return None\n'
     '    ai = _normalise_ai(ai) if ai else _normalise_ai(None)\n')
b = ('    if o.get("field") not in ("decision", "revision") or not _field_key(o).startswith("own:"):\n'
     '        return None\n'
     '    held = o.get("association") or {}\n'
     '    if o.get("page_binding") is not None and str(held.get("status", "")) == "held:no_page_target":\n'
     '        return held          # C4 A2: no target established on its own page; never reattached to another identity\n'
     '    ai = _normalise_ai(ai) if ai else _normalise_ai(None)\n')
edits.append((a, b, 1))

for anchor, repl, n in edits:          # sequential: each count is checked on the text as it is when the edit applies
    got = src.count(anchor)
    if got != n:
        sys.exit(f"anchor count {got} != {n}: {anchor[:90]!r} (nothing written)")
    src = src.replace(anchor, repl)
F.write_text(src, encoding="utf-8")
print("applied", len(edits), "edits")
