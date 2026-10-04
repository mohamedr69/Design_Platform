"""R21 prerequisite switches (applied to C:/t/iso/cand-ai4, branch ai-pilot-r21-2026-09-30, from 69ee759). Only
backend/app/ai/evidence_reader.py changes. Every behaviour that the four-arm design must hold common or vary gets its
OWN switch; flags-off behaviour and the reviewed legacy configurations (G, T, E) keep their identities byte-for-byte.

  AI_EVIDENCE_GUARD=1                   G      bare revision token never an identity           policy +guard-rev-token-2026-09-30.1
  AI_EVIDENCE_SUPPORT=v2                Rsup   rotation-correct clip + bounded local OCR support in EVERY read path
                                               (before: selected only through the targeted branch)  policy +region-support-2026-09-30.1
  AI_EVIDENCE_SCHEDULING=required_first Sched  the required-first reader path for every page, with or without optional
                                               reads                                             reader +required-first-2026-09-30.1 (when no X)
  AI_EVIDENCE_DEADLINE=1                D      request timeout = min(provider timeout, remaining job time); MIN_REQUEST_S
                                               floor; OCR bounded by the remaining time            reader +deadline-2026-09-30.1
  AI_EVIDENCE_ROI=1                     ROI    located title-block discovery for drawing sheets (R19-01 absence rule)
                                                                                                policy+reader +roi-discovery-2026-09-30.1
  AI_EVIDENCE_TARGETED=1                X      optional targeted context reads (requires G; implies Rsup + Sched as reviewed)
                                                                                                policy +targeted-completion-2026-09-30.2, reader +targeted-2026-09-30.2
  AI_EVIDENCE_EFFICIENT=1               E      legacy: ROI + D together, identity +located-discovery-2026-09-30.2 (unchanged)

Arms: L1 = G+Rsup+Sched+D; L2 = L1+ROI; L3 = L1+X; L4 = L2+X. Every arm has a distinct reader / policy identity, so the
result cache (keyed by policy, reader, prompt versions) never crosses arms."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai4/backend/app/ai/evidence_reader.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")


def sub(old, new, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('''GUARD_ENABLED = _os.environ.get("AI_EVIDENCE_GUARD") == "1"
TARGETED_ENABLED = _os.environ.get("AI_EVIDENCE_TARGETED") == "1"
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
    # .2 (M2 review 19, R19-01): a cropped discovery never establishes absence outside what it inspected
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+located-discovery-2026-09-30.2"
    READER_VERSION = READER_VERSION + "+located-discovery-2026-09-30.2"
    PROMPTS = {**PROMPTS, "discover_region": "discover-region-2026-09-30.1"}
''', '''GUARD_ENABLED = _os.environ.get("AI_EVIDENCE_GUARD") == "1"
TARGETED_ENABLED = _os.environ.get("AI_EVIDENCE_TARGETED") == "1"
# E  AI_EVIDENCE_EFFICIENT=1 (M2 review 18) legacy: located discovery for drawing sheets + job-deadline-bound request /
#                            OCR timeouts together (identity unchanged)
EFFICIENT_ENABLED = _os.environ.get("AI_EVIDENCE_EFFICIENT") == "1"
# --- R21 prerequisite switches (2026-09-30): one switch per behaviour the four-arm design holds common or varies ------
# Rsup  AI_EVIDENCE_SUPPORT=v2                rotation-correct clip + bounded local OCR support in EVERY read path
# Sched AI_EVIDENCE_SCHEDULING=required_first the required-first reader path, with or without optional reads
# D     AI_EVIDENCE_DEADLINE=1                request timeout follows the job's remaining time; MIN_REQUEST_S floor; OCR bound
# ROI   AI_EVIDENCE_ROI=1                     located title-block discovery (R19-01 absence rule), without the deadline
# X = TARGETED (optional targeted reads; as reviewed it implies Rsup and Sched). E = ROI + D (legacy identity kept).
SUPPORT_V2 = _os.environ.get("AI_EVIDENCE_SUPPORT") == "v2" or TARGETED_ENABLED
REQUIRED_FIRST = _os.environ.get("AI_EVIDENCE_SCHEDULING") == "required_first" or TARGETED_ENABLED
DEADLINE_ENABLED = _os.environ.get("AI_EVIDENCE_DEADLINE") == "1" or EFFICIENT_ENABLED
ROI_ENABLED = _os.environ.get("AI_EVIDENCE_ROI") == "1" or EFFICIENT_ENABLED
if TARGETED_ENABLED and not GUARD_ENABLED:
    raise RuntimeError("AI_EVIDENCE_TARGETED requires AI_EVIDENCE_GUARD (T = G + targeted verification)")
if GUARD_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+guard-rev-token-2026-09-30.1"
if SUPPORT_V2:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+region-support-2026-09-30.1"
if TARGETED_ENABLED:
    # .2 (M2 review 18): completion from usable evidence (R18-01), no targeted read after a failed / refused primary or
    # escalation request (R18-02), required reads of every page before any optional targeted read (R18-03)
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+targeted-completion-2026-09-30.2"
    READER_VERSION = READER_VERSION + "+targeted-2026-09-30.2"
    PROMPTS = {**PROMPTS, "read_field_context": "read-field-context-2026-09-30.1"}
elif REQUIRED_FIRST:
    READER_VERSION = READER_VERSION + "+required-first-2026-09-30.1"
if EFFICIENT_ENABLED:
    # .2 (M2 review 19, R19-01): a cropped discovery never establishes absence outside what it inspected
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+located-discovery-2026-09-30.2"
    READER_VERSION = READER_VERSION + "+located-discovery-2026-09-30.2"
    PROMPTS = {**PROMPTS, "discover_region": "discover-region-2026-09-30.1"}
else:
    if ROI_ENABLED:
        EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+roi-discovery-2026-09-30.1"
        READER_VERSION = READER_VERSION + "+roi-discovery-2026-09-30.1"
        PROMPTS = {**PROMPTS, "discover_region": "discover-region-2026-09-30.1"}
    if DEADLINE_ENABLED:
        READER_VERSION = READER_VERSION + "+deadline-2026-09-30.1"
''')
sub('''        timeout_s = None
        if EFFICIENT_ENABLED:
            # E: the job's remaining elapsed budget bounds the request''', '''        timeout_s = None
        if DEADLINE_ENABLED:
            # D: the job's remaining elapsed budget bounds the request''')
sub('''def _ocr_timeout(run) -> float:
    """E: an OCR run inside a job gets at most 30 s and never the time the next request needs; 30 s otherwise."""
    if not EFFICIENT_ENABLED or run is None:''', '''def _region_texts(page, region, ocr_lines, run=None) -> list:
    """The support policy in force: Rsup (rotation-correct clip + bounded local OCR) or the accepted region text."""
    if SUPPORT_V2:
        return region_texts_v2(page, region, ocr_lines or [], ocr_timeout=_ocr_timeout(run))
    return region_texts(page, region, ocr_lines or [])


def _ocr_timeout(run) -> float:
    """D: an OCR run inside a job gets at most 30 s and never the time the next request needs; 30 s otherwise."""
    if not DEADLINE_ENABLED or run is None:''')
sub('''        before = run.calls
        if TARGETED_ENABLED:
            found = _read_page_required(''', '''        before = run.calls
        if REQUIRED_FIRST:
            found = _read_page_required(''')
sub('''    if TARGETED_ENABLED:
        ctx = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=reason, ocr_lines=ocr_lines)
        return _finish_page(run, page, ctx) if ctx.get("_pending") else ctx''', '''    if REQUIRED_FIRST:
        ctx = _read_page_required(run, page, sha256=sha256, number=number, facts=facts, reason=reason, ocr_lines=ocr_lines)
        return _finish_page(run, page, ctx) if ctx.get("_pending") else ctx''')
sub('''        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = region_texts(page, region, ocr_lines or [])
        if not (disc_value or det_value):
            fields[key] = _absent(located, field, facts)
            continue''', '''        readings = [{"source": "discovery", "value": disc_value or "", "legible": bool(disc_value)}]
        texts = _region_texts(page, region, ocr_lines, run)
        if not (disc_value or det_value):
            fields[key] = _absent(located, field, facts)
            continue''')
sub('''    """(discovered, located) -- `located` None when the page was discovered whole (always with E off)."""
    if EFFICIENT_ENABLED:''', '''    """(discovered, located) -- `located` None when the page was discovered whole (always with ROI off)."""
    if ROI_ENABLED:''')
sub('''    return discovered, ({"located": False, "route": "full_page"} if EFFICIENT_ENABLED else None)''',
    '''    return discovered, ({"located": False, "route": "full_page"} if ROI_ENABLED else None)''')
sub('''        texts = region_texts_v2(page, region, ocr_lines or [], ocr_timeout=_ocr_timeout(run))
        st = state[field] = {"key": key, "region": region, "readings": readings, "texts": texts, "disc": disc_value, "det": det_value}''',
    '''        texts = _region_texts(page, region, ocr_lines, run)
        st = state[field] = {"key": key, "region": region, "readings": readings, "texts": texts, "disc": disc_value, "det": det_value}''')
sub('''    use = new_region or region
    return reading, use, region_texts_v2(page, use, ocr_lines, ocr_timeout=_ocr_timeout(run))''',
    '''    use = new_region or region
    return reading, use, _region_texts(page, use, ocr_lines, run)''')
sub('''    context_clip = located.get("clip") if located and located.get("located") else None
    for field in ("identity", "revision"):
        st = state.get(field)
        if not st or st.get("absent"):
            continue
        key, verdict = st["key"], st["verdict"]
        if verdict["state"] == "validated" or verdict.get("guard"):
            continue''', '''    context_clip = located.get("clip") if located and located.get("located") else None
    for field in ("identity", "revision") if TARGETED_ENABLED else ():     # X off: no optional read, same required path
        st = state.get(field)
        if not st or st.get("absent"):
            continue
        key, verdict = st["key"], st["verdict"]
        if verdict["state"] == "validated" or verdict.get("guard"):
            continue''')
assert "EFFICIENT_ENABLED:" not in s.replace("if EFFICIENT_ENABLED:\n    # .2 (M2 review 19", ""), "a legacy E gate remains"
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("R21 patched")
