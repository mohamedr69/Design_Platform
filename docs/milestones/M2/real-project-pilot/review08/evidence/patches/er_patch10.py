"""M2 review 08 (R8-01 merge, R8-02 context): field-level evidence lifecycle and context-bound selection."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\evidence_reader.py")
s = p.read_text(encoding="utf-8")
i, j = s.index("MAX_ATTEMPTS_KEPT = 12"), s.index("def cached_ocr_lines(")
NEW = r'''MAX_ATTEMPTS_KEPT = 12
MAX_FIELD_HISTORY = 4
AI_EVIDENCE_SCHEMA = "ai-evidence-2"   # review 08: field-level pages, context-bound selection
UNKNOWN_PROFILE = "unknown"

# Supersession rule (M2 review 08, R8-01). For one field of one component on one page:
#   * a read whose outcome is `completed` replaces the field's evidence -- including a completed, source-supported
#     negative such as a legible "no decision marked" -- and the replaced evidence goes to the field's history;
#     a completed read that came back only *unreadable* supersedes nothing;
#   * `absent_by_discovery` (discovery saw no such field; its region was never read), `failed:*`, `budget`,
#     `incomplete:*` and a page that was not visited never supersede anything -- last-good evidence stays, with its
#     own provenance, and the unsuccessful attempt is kept in `attempts`;
#   * where a field has no evidence yet, what an unsuccessful read produced (a discovery candidate) is kept with
#     status `incomplete`, never as verified, and is replaced by the first completed read.


def envelope_key(profile: str | None, variant: str | None) -> str:
    return f"{profile or UNKNOWN_PROFILE}|{variant or 'unknown'}"


def _field_key(o: dict) -> str:
    return f"{o.get('component') or 'own'}:{o.get('field')}"


def _legacy_pages(pages_or_obs, provenance: dict) -> dict:
    """Review 06 / 07 pages as field-level pages, status `legacy`: their completeness was never recorded per field."""
    pages: dict = {}
    for o in pages_or_obs:
        page = pages.setdefault(str(o.get("page") or 1), {"fields": {}})
        entry = page["fields"].setdefault(_field_key(o), {"observations": [], "status": "legacy", "provenance": provenance, "history": []})
        entry["observations"].append(o)
    return pages


def _normalise_ai(previous: dict | None) -> dict:
    """The stored `ai_evidence` in the review 08 shape {schema, envelopes, last_written_key, attempts, superseded}.
    A review 06 flat envelope or a review 07 page-level envelope keeps its recorded provenance; a missing profile
    stays `unknown` -- never assumed."""
    if not previous:
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": {}, "last_written_key": None, "attempts": [], "superseded": []}
    if previous.get("schema") == AI_EVIDENCE_SCHEMA:
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": dict(previous["envelopes"]), "last_written_key": previous.get("last_written_key"),
                "attempts": list(previous.get("attempts") or []), "superseded": list(previous.get("superseded") or [])}
    if "envelopes" in previous:                                          # review 07 shape
        envelopes = {}
        for key, env in previous["envelopes"].items():
            pages = {}
            for pno, page in (env.get("pages") or {}).items():
                pages.update(_legacy_pages(page.get("observations") or [], dict(page.get("provenance") or {}, completeness="not recorded (review 07)")))
            envelopes[key] = _flatten({**{k: v for k, v in env.items() if k not in ("pages", "observations")}, "pages": pages})
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": envelopes, "last_written_key": previous.get("current_key"),
                "attempts": list(previous.get("attempts") or []), "superseded": list(previous.get("superseded") or [])}
    provenance = {"attempt": "legacy", "version": previous.get("version"), "policy": previous.get("policy"),     # review 06 flat
                  "variant": previous.get("variant"), "profile": previous.get("profile"), "read_sha256": previous.get("read_sha256"),
                  "completeness": "not recorded (review 06)"}
    key = envelope_key(previous.get("profile"), previous.get("variant"))
    env = {"profile": previous.get("profile"), "variant": previous.get("variant"), "read_sha256": previous.get("read_sha256"),
           "pages": _legacy_pages(previous.get("observations") or [], provenance), "stale": None}
    return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": {key: _flatten(env)}, "last_written_key": key,
            "attempts": [{"attempt": "legacy", "outcome": (previous.get("coverage") or {}).get("outcome"), "calls": previous.get("calls")}],
            "superseded": []}


def _flatten(env: dict) -> dict:
    out = []
    for pno, page in sorted((env.get("pages") or {}).items(), key=lambda kv: int(kv[0])):
        for fkey, entry in sorted(page.get("fields", {}).items()):
            out += [dict(o, provenance=entry["provenance"], field_status=entry["status"]) for o in entry["observations"]]
    env["observations"] = out
    return env


def _supersedes(outcome: str | None, observations: list) -> bool:
    return outcome == COMPLETED and bool(observations) and not all(o.get("state") == "unreadable" for o in observations)


def merge_evidence(previous: dict | None, attempt: dict, *, sha256: str, profile: str, variant: str) -> dict:
    """The row's `ai_evidence` after one attempt, field by field under the supersession rule above. The envelope of
    another profile or variant is never touched; one read from other bytes is marked stale (kept in `superseded`).
    Returns the stored shape; what applies to a requested context is `evidence_for`."""
    ai = _normalise_ai(previous)
    key = envelope_key(profile, variant)
    for k, env in list(ai["envelopes"].items()):
        if env.get("read_sha256") and env.get("read_sha256") != sha256 and not env.get("stale"):
            ai["envelopes"][k] = {**env, "stale": "source bytes changed since this evidence was read"}
    env = ai["envelopes"].get(key)
    if env is None or env.get("stale"):
        if env is not None:
            ai["superseded"] = (ai["superseded"] + [{"key": key, **env}])[-4:]
        env = {"profile": profile, "variant": variant, "read_sha256": sha256, "pages": {}, "stale": None}
    provenance = {"attempt": attempt["attempt"], "version": attempt.get("version"), "policy": attempt.get("policy"),
                  "prompts": attempt.get("prompts"), "models": attempt.get("models"), "variant": variant, "profile": profile,
                  "read_sha256": sha256, "at": attempt.get("at")}
    by_field: dict = {}
    for o in attempt.get("observations") or []:
        by_field.setdefault((str(o.get("page") or 1), _field_key(o)), []).append(o)
    pages = {k: {"fields": dict(v.get("fields") or {})} for k, v in (env.get("pages") or {}).items()}
    changed = []
    for entry in (attempt.get("coverage") or {}).get("pages") or []:
        pno = str(entry.get("page"))
        outcomes = dict(entry.get("fields") or {})
        if not outcomes and entry.get("outcome") in ("evidence", "no_components"):
            # an attempt that recorded no field outcomes (before review 08): only what it produced counts as read
            outcomes = {fk: COMPLETED for (pp, fk) in by_field if pp == pno}
        keys = {fk for fk in outcomes if ":" in fk and not fk.endswith(":escalation")} | {fk for (pp, fk) in by_field if pp == pno}
        page = pages.setdefault(pno, {"fields": {}})
        for fkey in sorted(keys):
            outcome, new = outcomes.get(fkey), by_field.get((pno, fkey), [])
            existing = page["fields"].get(fkey)
            if _supersedes(outcome, new):
                history = ((existing or {}).get("history") or []) + ([{k: v for k, v in existing.items() if k != "history"}] if existing else [])
                page["fields"][fkey] = {"observations": new, "status": "completed", "provenance": {**provenance, "read": outcome},
                                        "history": history[-MAX_FIELD_HISTORY:]}
                changed.append(f"{pno}:{fkey}")
            elif new and (existing is None or existing.get("status") == "incomplete"):
                page["fields"][fkey] = {"observations": new, "status": "incomplete", "provenance": {**provenance, "read": outcome},
                                        "history": (existing or {}).get("history") or []}
                changed.append(f"{pno}:{fkey} (incomplete)")
        if not page["fields"]:
            pages.pop(pno)
    env = _flatten({**env, "pages": pages})
    ai["envelopes"][key] = env
    if changed:
        ai["last_written_key"] = key
    summary = {k: attempt.get(k) for k in ("attempt", "at", "outcome", "version", "policy", "error", "models")}
    summary.update(key=key, variant=variant, profile=profile, read_sha256=sha256, changed=changed,
                   pages={str(e.get("page")): {"outcome": e.get("outcome"), "fields": e.get("fields")} for e in (attempt.get("coverage") or {}).get("pages") or []},
                   calls=attempt.get("calls"))
    ai["attempts"] = (ai["attempts"] + [summary])[-MAX_ATTEMPTS_KEPT:]
    return ai


def evidence_for(ai: dict | None, *, sha256: str | None, profile: str | None, variant: str | None,
                 policies: set | None = None, accept_unknown_profile: bool = False) -> dict:
    """The AI evidence that applies to a requested context -- source hash, extraction profile, verification variant
    and (optionally) compatible policies -- as an explicit state (M2 review 08, R8-02):
      current      evidence read for exactly this context (`envelope`, `observations`; `incomplete` lists fields
                   known only from unsuccessful reads)
      pending      reading was attempted for this context and gave no evidence yet
      unavailable  nothing was read for this context (or none under a compatible policy); `history` names what exists
      stale        evidence for this context exists but was read from other bytes
    Another profile's or variant's evidence is never returned for this one. An unknown legacy profile is used only
    when the caller says so (`accept_unknown_profile`, for a historical run whose manifest declares its profile)."""
    ai = _normalise_ai(ai) if ai else _normalise_ai(None)
    context = {"sha256": sha256, "profile": profile, "variant": variant, "policies": sorted(policies) if policies else None}
    history = sorted(ai["envelopes"])
    key = envelope_key(profile, variant)
    env, via = ai["envelopes"].get(key), None
    if env is None and accept_unknown_profile:
        env, via = ai["envelopes"].get(envelope_key(UNKNOWN_PROFILE, variant)), "unknown legacy profile accepted by the caller"
    if env is None:
        return {"state": "unavailable", "reason": f"no evidence was read for {key}", "context": context, "history": history}
    if env.get("stale") or (sha256 and env.get("read_sha256") and env.get("read_sha256") != sha256):
        return {"state": "stale", "reason": env.get("stale") or "read from other bytes", "context": context, "history": history}
    pages = {}
    for pno, page in (env.get("pages") or {}).items():
        kept = {fk: e for fk, e in page.get("fields", {}).items() if not policies or e["provenance"].get("policy") in policies}
        if kept:
            pages[pno] = {"fields": kept}
    if not pages:
        attempted = any(a.get("key") == key for a in ai["attempts"])
        return {"state": "pending" if attempted and not (policies and env.get("pages")) else "unavailable",
                "reason": ("reading was attempted for this context; no evidence yet" if attempted else "no evidence under a compatible policy"),
                "context": context, "history": history}
    current = _flatten({**{k: v for k, v in env.items() if k not in ("pages", "observations")}, "pages": pages})
    incomplete = sorted(f"{p}:{fk}" for p, page in pages.items() for fk, e in page["fields"].items() if e["status"] == "incomplete")
    return {"state": "current", "context": context, "via": via, "envelope": current, "observations": current["observations"],
            "incomplete": incomplete, "history": history}


def last_known(ai: dict | None) -> dict:
    """History, not current evidence: the envelope written last, whatever its context."""
    ai = _normalise_ai(ai) if ai else _normalise_ai(None)
    key = ai.get("last_written_key")
    return {"state": "history", "key": key, "envelope": ai["envelopes"].get(key) if key else None}


def current_evidence(ai: dict | None, **context) -> dict:
    """Review 07 name, kept for its callers: current evidence now exists only for a requested context
    (`evidence_for`); called without one it says so instead of guessing."""
    if not context:
        return {"state": "context_required", "reason": "name the source hash, profile and variant (evidence_for)"}
    return evidence_for(ai, **context)


'''
s = s[:i] + NEW + s[j:]
p.write_text(s, encoding="utf-8")
print("ok")
