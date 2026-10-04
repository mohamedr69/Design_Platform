import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/scripts/m2_eval4.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''   register record, and a register-ineligible truth record is never counted missing from the register.
''', '''   register record, and a register-ineligible truth record is never counted missing from the register.
7. The *evidence* layer = the raw layer + the AI evidence reader's observations (`extracted["ai_evidence"]`): a
   `validated` reading counts as accepted evidence (and is wrong / critical like any other when it disagrees with the
   truth); `candidate` and `conflict` readings count as held, never as recovered. It is reported apart from the raw
   layer, so what the model added -- and what it got wrong -- is visible (`evidence_introduced_errors`).
''')
sub('''def raw_facts(row: dict | None) -> list[dict]:''', '''def ai_facts(row: dict | None) -> list[dict]:
    """The AI evidence reader's observations as facts: validated = accepted evidence, candidate / conflict = held."""
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    facts = []
    for obs in ai.get("observations") or []:
        value, state, page = obs.get("value"), obs.get("state"), _obs_page(obs)
        if not value:
            continue
        accepted = state == "validated"
        if obs.get("field") == "identity":
            facts.append({"page": page, "kind": "ai_evidence", "identity": value if accepted else None,
                          "held_identity": None if accepted else value})
        elif obs.get("field") == "revision" and accepted:
            facts.append({"page": page, "kind": "ai_evidence", "revision": value})
        elif obs.get("field") == "decision" and accepted and value in POSITIVE:
            facts.append({"page": page, "kind": "ai_evidence", "decisions": {value}})
    return facts


def ai_coverage(row: dict | None) -> dict:
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    if not ai:
        return {}
    pages = (ai.get("coverage") or {}).get("pages") or []
    return {"variant": ai.get("variant"), "outcome": (ai.get("coverage") or {}).get("outcome"),
            "pages_read": sum(1 for p in pages if p.get("calls")), "page_outcomes": dict(collections.Counter(str(p.get("outcome")) for p in pages)),
            "calls": sum(1 for c in ai.get("calls") or [] if not c.get("cache_hit") and not str(c.get("outcome", "")).startswith("budget")),
            "cache_hits": sum(1 for c in ai.get("calls") or [] if c.get("cache_hit")),
            "states": dict(collections.Counter(f"{o.get('field')}:{o.get('state')}" for o in ai.get("observations") or []))}


def raw_facts(row: dict | None) -> list[dict]:''')
sub('''                 "records": [], "emissions": [], "unvalidated": [], "raw": []}''',
    '''                 "records": [], "emissions": [], "unvalidated": [], "raw": [], "evidence": [], "ai": ai_coverage(row)}''')
sub('''        facts = raw_facts(row)
        for e in exp:''', '''        facts = raw_facts(row)
        evidence_facts = facts + ai_facts(row)
        for e in exp:''')
sub('''            entry["raw"].append({"page": e["page"], "register": register, "fields": judge_raw(e, facts)})''',
    '''            entry["raw"].append({"page": e["page"], "register": register, "fields": judge_raw(e, facts)})
            entry["evidence"].append({"page": e["page"], "register": register, "fields": judge_raw(e, evidence_facts),
                                      "expected": {k: e.get(k) for k in ("component", "reference", "printed_revision", "decision")}})''')
sub('''    raw = collections.defaultdict(collections.Counter)
    how = collections.Counter()''', '''    raw = collections.defaultdict(collections.Counter)
    evidence = collections.defaultdict(collections.Counter)
    introduced = []
    ai_states, ai_outcomes = collections.Counter(), collections.Counter()
    ai_calls = ai_hits = ai_docs = 0
    how = collections.Counter()''')
sub('''        for r in d["raw"]:
            for f, s in r["fields"].items():
                raw[f][s] += 1
''', '''        for r in d["raw"]:
            for f, s in r["fields"].items():
                raw[f][s] += 1
        for r, base in zip(d.get("evidence") or [], d["raw"]):
            for f, s in r["fields"].items():
                evidence[f][s] += 1
                if s in ("wrong", "fp") and base["fields"].get(f) not in ("wrong", "fp"):
                    introduced.append({"kind": f"{f}: {s}", "doc": d["doc"], "page": r["page"], "expected": r.get("expected")})
        ai = d.get("ai") or {}
        if ai:
            ai_docs += 1
            ai_calls += ai.get("calls", 0)
            ai_hits += ai.get("cache_hits", 0)
            ai_states.update(ai.get("states") or {})
            ai_outcomes.update(ai.get("page_outcomes") or {})
''')
sub('''            "register": {f: rates(c) for f, c in reg.items()}, "raw": {f: rates(c) for f, c in raw.items()}, "critical": critical}''',
    '''            "register": {f: rates(c) for f, c in reg.items()}, "raw": {f: rates(c) for f, c in raw.items()}, "critical": critical,
            "evidence": {f: rates(c) for f, c in evidence.items()}, "evidence_introduced_errors": introduced,
            "ai": {"documents": ai_docs, "calls": ai_calls, "cache_hits": ai_hits, "states": dict(ai_states),
                   "page_outcomes": dict(ai_outcomes)}}''')
p.write_text(s, encoding="utf-8")
print("ok")
