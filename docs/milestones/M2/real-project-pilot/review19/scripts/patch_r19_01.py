"""R19-01 (applied to C:/t/iso/cand-ai3, branch ai-pilot-r19-2026-09-30, from c216206): a located (cropped) discovery
never establishes a field's absence outside what it inspected -- the text-silence inference for a decision is removed.
Only a whole-page discovery (not located, or a located area covering the whole page) records `absent_by_discovery`;
otherwise the outcome is `incomplete:located_region_only`. A genuine completed decision read keeps its own contract;
nothing here adds a request, a fallback or a status. E's identities move to .2 (the absence semantics changed)."""
import pathlib

P = pathlib.Path("C:/t/iso/cand-ai3/backend/app/ai/evidence_reader.py")
s = P.read_bytes().decode("utf-8").replace("\r\n", "\n")
pairs = [
    ('''    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+located-discovery-2026-09-30.1"
    READER_VERSION = READER_VERSION + "+located-discovery-2026-09-30.1"''',
     '''    # .2 (M2 review 19, R19-01): a cropped discovery never establishes absence outside what it inspected
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+located-discovery-2026-09-30.2"
    READER_VERSION = READER_VERSION + "+located-discovery-2026-09-30.2"'''),
    ('''# to the page's. A field the crop does not show is NOT a verified absence: identity / revision absence and a decision
# absence where the page's source text carries decision-block words are recorded `incomplete:located_region_only`.''',
     '''# to the page's. A field the crop does not show is NOT a verified absence: every field discovery did not report on a
# located (cropped) page is recorded `incomplete:located_region_only` -- the page's text layer being silent about a
# decision is no evidence about a raster stamp, a mark or an annotation outside the crop (M2 review 19, R19-01).'''),
    ('''_DECISION_BLOCK_CUES = re.compile(r"NO\\s+OBJECTION|APPROVED\\s+AS\\s+NOTED|REVISE\\s+(?:AND|&)\\s+RESUBMIT|\\bREJECTED\\b|NOT\\s+APPROVED|"
                                  r"\\bAPPROVED\\b(?!\\s+(?:BY|FOR))|\\bCODE\\s+[A-D]\\b", re.I)
''', ''),
    ('''def _absent(located: dict | None, field: str, facts) -> str:
    """The outcome of a field discovery did not report: a verified absence only when discovery saw the whole page, or
    (a decision) when the page's source text carries no decision-block words."""
    if not located or not located.get("located") or located.get("whole_page"):
        return ABSENT_BY_DISCOVERY
    if field == "decision" and len((facts.text or "").strip()) >= 80 and not _DECISION_BLOCK_CUES.search(facts.text or ""):
        return ABSENT_BY_DISCOVERY
    return LOCATED_ABSENCE''',
     '''def _absent(located: dict | None, field: str, facts) -> str:
    """The outcome of a field discovery did not report: a verified absence (`absent_by_discovery`) only when discovery
    saw the whole page; on a located crop it is `incomplete:located_region_only` for every field -- identity, revision
    and decision alike (R19-01: text-layer silence outside the crop is not negative evidence)."""
    if not located or not located.get("located") or located.get("whole_page"):
        return ABSENT_BY_DISCOVERY
    return LOCATED_ABSENCE'''),
]
for o, n in pairs:
    assert s.count(o) == 1, o[:100]
    s = s.replace(o, n)
assert "_DECISION_BLOCK_CUES" not in s
P.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("R19-01 patched")
