import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/scripts/m2_eval4.py")
s = p.read_text(encoding="utf-8")
old_start = s.index("def ai_facts(row: dict | None) -> list[dict]:")
old_end = s.index("def ai_coverage(row: dict | None) -> dict:")
s = s[:old_start] + '''def ai_facts(row: dict | None) -> list[dict]:
    """The AI evidence reader's observations as facts, one component per page (its identity, revision and decision
    read together): validated = accepted evidence, candidate / conflict = held (a held identity links nothing)."""
    ai = ((row or {}).get("extracted") or {}).get("ai_evidence") or {}
    by_page: dict[int, dict] = {}
    for obs in ai.get("observations") or []:
        value, state, page = obs.get("value"), obs.get("state"), _obs_page(obs)
        if not value:
            continue
        fact = by_page.setdefault(page, {"page": page, "kind": "ai_evidence", "identity": None, "held_identity": None,
                                         "revision": None, "decisions": set()})
        accepted = state == "validated"
        if obs.get("field") == "identity":
            fact["identity" if accepted else "held_identity"] = value
        elif obs.get("field") == "revision" and accepted:
            fact["revision"] = value
        elif obs.get("field") == "decision" and accepted and value in POSITIVE:
            fact["decisions"].add(value)
    return list(by_page.values())


''' + s[old_end:]
p.write_text(s, encoding="utf-8")
print("ok")
