# --- Review 29 switches (2026-10-02), isolated candidate only (review29/CONTRACTS.md) ---------------------------------
# IG  AI_EVIDENCE_IDGUARD=1         identity role guard (C1), in every reader path
# CA  AI_EVIDENCE_ADJUDICATE=1      conflict adjudication under the written evidence-ordering contract (C2)
# DR  AI_EVIDENCE_DECISION_REGION=1 the bounded decision-region path; title-block discovery gives no decisions (C3)
# PA  AI_EVIDENCE_ASSOC=1           page / target association invariant (C4)
# One switch per behaviour: none implies another, and none implies support, scheduling, deadline, targeted reads or
# ROI. CA, DR and PA run in the required-first path and refuse to start unless AI_EVIDENCE_SCHEDULING=required_first is
# set explicitly. All four off: identities and behaviour are those of 719e8de.
IDGUARD_ENABLED = _os.environ.get("AI_EVIDENCE_IDGUARD") == "1"
ADJUDICATE_ENABLED = _os.environ.get("AI_EVIDENCE_ADJUDICATE") == "1"
DECISION_REGION_ENABLED = _os.environ.get("AI_EVIDENCE_DECISION_REGION") == "1"
ASSOC_ENABLED = _os.environ.get("AI_EVIDENCE_ASSOC") == "1"
for _switch, _on in (("AI_EVIDENCE_ADJUDICATE", ADJUDICATE_ENABLED), ("AI_EVIDENCE_DECISION_REGION", DECISION_REGION_ENABLED),
                     ("AI_EVIDENCE_ASSOC", ASSOC_ENABLED)):
    if _on and not REQUIRED_FIRST:
        raise RuntimeError(f"{_switch} requires AI_EVIDENCE_SCHEDULING=required_first, set explicitly (it is never implied)")
IDGUARD_VERSION = "identity-role-guard-2026-10-02.2"   # C1 revision 2
ADJUDICATE_VERSION = "conflict-adjudication-2026-10-02.2"   # C2 revision 1
DECISION_REGION_VERSION = "decision-region-2026-10-02.1"
ASSOC_VERSION = "page-association-2026-10-02.1"
if IDGUARD_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+" + IDGUARD_VERSION
if ADJUDICATE_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+" + ADJUDICATE_VERSION
if DECISION_REGION_ENABLED:
    READER_VERSION = READER_VERSION + "+" + DECISION_REGION_VERSION
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+" + DECISION_REGION_VERSION
    PROMPTS = {**PROMPTS, "locate_decision": "locate-decision-2026-10-02.1"}
if ASSOC_ENABLED:
    EVIDENCE_POLICY_VERSION = EVIDENCE_POLICY_VERSION + "+" + ASSOC_VERSION
