"""M2 review 11 (R11-01): durable association context and persistent attempt order. evidence-reader 2026-09-29.6.
Selection reads a fact's association context from the fact's own entry (`anchor`, stamped when it is written or,
for evidence stored before .6, reconstructed once from reliably ordered history before anything is pruned); attempt
order comes from a persistent sequence (`attempt_seq`), never from the bounded summary list."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
raw = p.read_bytes()
assert b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('READER_VERSION = "evidence-reader-2026-09-29.5"   # .5: review 10 (association compatibility of retained facts)',
    'READER_VERSION = "evidence-reader-2026-09-29.6"   # .6: review 11 (durable association context, persistent attempt order)\n'
    '# evidence-reader-2026-09-29.5: review 10 (association compatibility of retained facts)')

# --- the stored shape: attempt_seq survives normalisation ------------------------------------------------------------------
sub('''    if previous.get("schema") == AI_EVIDENCE_SCHEMA:
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": dict(previous["envelopes"]), "last_written_key": previous.get("last_written_key"),
                "attempts": list(previous.get("attempts") or []), "superseded": list(previous.get("superseded") or [])}''',
    '''    if previous.get("schema") == AI_EVIDENCE_SCHEMA:
        return {"schema": AI_EVIDENCE_SCHEMA, "envelopes": dict(previous["envelopes"]), "last_written_key": previous.get("last_written_key"),
                "attempts": list(previous.get("attempts") or []), "superseded": list(previous.get("superseded") or []),
                "attempt_seq": previous.get("attempt_seq")}''')

# --- merge: persistent sequence; anchors stamped before pruning, and for what this attempt writes -------------------------
sub('''    ai = _normalise_ai(previous)
    key = envelope_key(profile, variant)
    for k, env in list(ai["envelopes"].items()):''', '''    ai = _normalise_ai(previous)
    # the attempt's place in this row's history: a persistent sequence, never the length of the bounded summary list
    # (review 11, R11-01); a caller's `attempt` number is kept as given for display
    seq = next_attempt_number(ai)
    ai["attempt_seq"] = seq
    key = envelope_key(profile, variant)
    for k, env in list(ai["envelopes"].items()):''')
sub('''    provenance = {"attempt": attempt["attempt"], "version": attempt.get("version"), "policy": attempt.get("policy"),''',
    '''    provenance = {"attempt": attempt["attempt"], "seq": seq, "version": attempt.get("version"), "policy": attempt.get("policy"),''')
sub('''    pages = {k: {"fields": dict(v.get("fields") or {})} for k, v in (env.get("pages") or {}).items()}
    changed, unapplied = [], []''', '''    pages = {k: {"fields": dict(v.get("fields") or {})} for k, v in (env.get("pages") or {}).items()}
    # retained dependent facts stored before .6 get their association context now -- from the history as it stands,
    # before this attempt can prune anything -- and keep it from then on (R11-01)
    for page_fields in pages.values():
        for fkey in DEPENDENT_FIELDS:
            entry = page_fields["fields"].get(fkey)
            if entry is not None and "anchor" not in entry:
                page_fields["fields"][fkey] = {**entry, "anchor": _reconstruct_anchor(ai, page_fields["fields"], fkey, entry)}
    changed, unapplied = [], []''')
sub('''        if not page["fields"]:
            pages.pop(pno)
    env = _flatten({**env, "pages": pages})''', '''        # what this attempt wrote records the context it was read in: the component as it stands after this attempt
        for fkey in DEPENDENT_FIELDS:
            entry = page["fields"].get(fkey)
            if entry is not None and entry["provenance"].get("seq") == seq:
                page["fields"][fkey] = {**entry, "anchor": _read_anchor(ai, page["fields"], fkey, entry, seq)}
        if not page["fields"]:
            pages.pop(pno)
    env = _flatten({**env, "pages": pages})''')
sub('''    summary = {k: attempt.get(k) for k in ("attempt", "at", "outcome", "version", "policy", "error", "models")}''',
    '''    summary = {k: attempt.get(k) for k in ("attempt", "at", "outcome", "version", "policy", "error", "models")}
    summary["seq"] = seq''')

# --- the association contract on durable context ------------------------------------------------------------------------
i = s.index("def _attempt_no(provenance: dict | None) -> int:")
j = s.index("def evidence_for(")
s = s[:i] + '''# Durable association context (M2 review 11, R11-01). A dependent fact's association is decided from context that the
# fact's own entry keeps (`anchor`), never from prunable field history or from attempt numbers that can repeat:
#   anchor = {"source": "read", "seq", "identity", "revision"}   stamped by the merge that wrote the fact: the
#            component's identity, and the revision compatible with its target (or that identity), as they stood
#            right after that attempt;
#          = {"source": "reconstructed", "attempt", "identity", "revision", "revision_known"}   evidence stored before
#            .6, stamped once by the next merge -- before anything is pruned -- from history whose attempt order is
#            reliable (numbers unique and present);
#          = {"source": "unavailable", "reason"}   that history is not reliable (a repeated or missing attempt number,
#            or context that may already have been pruned): the fact is held, never guessed.
# Attempt order is `seq`: a persistent per-row sequence (`attempt_seq`), one more than any attempt number the row has
# ever recorded, never the length of the bounded summary list. It does not reset on restart: it is stored in the row.
# Concurrency: one `process_documents` job runs at a time across every worker (app.services.jobs lane limit 1, claimed
# by compare-and-set); within it the stage reads, merges and commits one row at a time. A row's `ai_evidence` is one
# JSON value rewritten whole, so a stored state is always one consistent chain; two writers that overlapped anyway
# (a job requeued by stale recovery while its worker still ran, or a direct call outside the job system) would lose
# the earlier write, not interleave numbers. Nothing stronger is claimed.
DEPENDENT_FIELDS = ("own:revision", "own:decision")


def _attempt_no(provenance: dict | None) -> int:
    """An attempt number from provenance; review 06 `legacy` (and anything unnumbered) is attempt 0."""
    a = (provenance or {}).get("attempt")
    return a if isinstance(a, int) else int(a) if str(a).isdigit() else 0


def _numbered(value) -> int | None:
    return value if isinstance(value, int) else int(value) if str(value).isdigit() else None


def next_attempt_number(ai: dict | None) -> int:
    """The next attempt's sequence number for this row: one more than the persistent sequence, or -- for evidence
    stored before .6 -- than any attempt number recorded anywhere in it (summaries, field provenance, history)."""
    ai = _normalise_ai(ai) if ai else _normalise_ai(None)
    if ai.get("attempt_seq"):
        return int(ai["attempt_seq"]) + 1
    seen = [_numbered(a.get("attempt")) for a in ai["attempts"]] + [_numbered(a.get("seq")) for a in ai["attempts"]]
    for env in list(ai["envelopes"].values()) + list(ai["superseded"]):
        for page in (env.get("pages") or {}).values():
            for entry in (page.get("fields") or {}).values():
                for e in [entry] + list(entry.get("history") or []):
                    seen += [_numbered((e.get("provenance") or {}).get("attempt")), _numbered((e.get("provenance") or {}).get("seq"))]
    return max([n for n in seen if n is not None] or [0]) + 1


def _entry_value(entry: dict | None) -> str | None:
    values = [o.get("value") for o in (entry or {}).get("observations") or [] if o.get("value") not in (None, "")]
    return values[0] if values else None


def _read_entry(entry: dict | None) -> dict | None:
    """The field's current entry when it is read evidence (completed, or legacy) -- an incomplete field anchors nothing."""
    return entry if entry and entry.get("status") in (COMPLETED, "legacy") else None


def _same(field: str, a, b) -> bool:
    return literal_key(field, a) == literal_key(field, b)


def _context_identity(fields: dict, entry: dict | None) -> tuple[bool, str | None]:
    """(known, identity) of the component a revision entry was read for: its recorded target, else its anchor."""
    if not entry:
        return False, None
    first = (entry.get("observations") or [{}])[0]
    if first.get("target"):
        return True, first["target"]
    anchor = entry.get("anchor")
    if anchor and anchor.get("source") in ("read", "reconstructed"):
        return True, anchor.get("identity")
    return False, None


def _revision_now(fields: dict, target: str | None) -> tuple[str | None, dict | None]:
    """(value, entry) of the own revision now compatible with component `target`: read for that target (recorded
    target, else its anchor). An unrelated revision -- another component's, or one of unknown context -- is none."""
    entry = _read_entry(fields.get("own:revision"))
    if not target or not entry:
        return None, None
    known, context = _context_identity(fields, entry)
    return (_entry_value(entry), entry) if known and context and _same("identity", context, target) else (None, None)


def _read_anchor(ai: dict, fields: dict, fkey: str, entry: dict, seq: int) -> dict:
    """The context a fact written by attempt `seq` was read in: the component as it stands after that attempt."""
    identity = _entry_value(_read_entry(fields.get("own:identity")))
    anchor = {"source": "read", "seq": seq, "identity": identity}
    if fkey == "own:decision":
        target = (entry.get("observations") or [{}])[0].get("target") or identity
        anchor["revision"] = _revision_now(fields, target)[0]
    return anchor


def _attempt_reliable(ai: dict, fields: dict, attempt) -> tuple[bool, str]:
    """Whether a pre-.6 attempt number can order history: present, and recorded for one attempt only."""
    if attempt == "legacy":
        return True, ""                                   # review 06: the single flat reading of its envelope
    n = _numbered(attempt)
    if n is None:
        return False, "the fact records no attempt order"
    if sum(1 for a in ai["attempts"] if _numbered(a.get("attempt")) == n and a.get("seq") is None) > 1:
        return False, f"attempt number {n} was recorded for more than one attempt"
    stamps = set()
    for entry in fields.values():
        for e in [entry] + list(entry.get("history") or []):
            prov = e.get("provenance") or {}
            if prov.get("seq") is None and _numbered(prov.get("attempt")) == n and prov.get("at"):
                stamps.add(prov["at"])
    if len(stamps) > 1:
        return False, f"attempt number {n} was recorded at different times"
    return True, ""


def _value_at(entry: dict | None, n: int) -> tuple[bool, str | None]:
    """(determinate, value) of a field in effect at pre-.6 attempt `n`, from its current entry and history. Entries
    written by .6 or later (with a `seq`) are later than any pre-.6 attempt. Not determinate when the entry that was in
    effect may already have been pruned (a full history whose oldest retained entry is later than `n`)."""
    if entry is None:
        return True, None
    chain = [entry] + list(entry.get("history") or [])
    best = None
    for e in chain:
        prov = e.get("provenance") or {}
        if e.get("status") not in (COMPLETED, "legacy") or prov.get("seq") is not None:
            continue
        m = _attempt_no(prov)
        if m <= n and (best is None or m >= _attempt_no(best.get("provenance"))):
            best = e
    if best is not None:
        return True, _entry_value(best)
    pruned = len(entry.get("history") or []) >= MAX_FIELD_HISTORY
    return (not pruned), None


def _reconstruct_anchor(ai: dict, fields: dict, fkey: str, entry: dict) -> dict:
    """The context of a fact stored before .6, from its recorded history -- only when that history is reliably ordered."""
    prov = entry.get("provenance") or {}
    ok, why = _attempt_reliable(ai, fields, prov.get("attempt"))
    if not ok:
        return {"source": "unavailable", "reason": why}
    n = _attempt_no(prov)
    determinate, identity = _value_at(fields.get("own:identity"), n)
    if not determinate:
        return {"source": "unavailable", "reason": "the identity it was read with may no longer be in the retained history"}
    anchor = {"source": "reconstructed", "attempt": prov.get("attempt"), "identity": identity}
    if fkey == "own:decision":
        target = (entry.get("observations") or [{}])[0].get("target") or identity
        rev = fields.get("own:revision")
        known, value = _value_at(rev, n)
        if known and value is not None and rev is not None:
            # the revision in effect then counts only if it was read for the same component
            then = next((e for e in [rev] + list(rev.get("history") or []) if _entry_value(e) == value), None)
            first = ((then or {}).get("observations") or [{}])[0]
            if first.get("target") and target and not _same("identity", first["target"], target):
                value = None
        anchor.update(revision=value, revision_known=known)
    return anchor


def _anchor_of(ai: dict, fields: dict, fkey: str, entry: dict | None) -> dict:
    if not entry:
        return {"source": "unavailable", "reason": "no retained entry"}
    return entry.get("anchor") or _reconstruct_anchor(ai, fields, fkey, entry)


def _later(entry: dict | None, than: dict | None) -> bool:
    """Whether `entry` was read after `than` -- True when that cannot be established (the safe direction)."""
    a, b = (entry or {}).get("provenance") or {}, (than or {}).get("provenance") or {}
    if a.get("seq") is not None and b.get("seq") is not None:
        return a["seq"] > b["seq"]
    if a.get("seq") is not None:
        return True                                        # a .6 read is later than any pre-.6 one
    if b.get("seq") is not None:
        return False
    x, y = _numbered(a.get("attempt")), _numbered(b.get("attempt"))
    return True if x is None or y is None else x > y


def association_of(o: dict, fields: dict, entry: dict | None = None, ai: dict | None = None) -> dict | None:
    """The association of a dependent fact (a revision or a decision of the page's own component) with the component
    as it is read now (review 09 R9-02, review 10 R10-01, review 11 R11-01; rules in review10/COMPATIBILITY.md and
    review11/CONTRACT.md). Every known constraint is checked before a fact is associated; the context it was read in is
    its durable `anchor`, never prunable history; nothing is reattached and no target is invented.
    With a recorded `target`:
      held:target_changed       the component's current identity (established or not) is another one
      held:revision_changed     a decision whose revision anchor (`target_revision`, else its anchor's revision)
                                differs from the revision now compatible with its target
      held:revision_unverifiable a decision whose revision anchor is not known (unreliable pre-.6 history) while a
                                compatible revision has been read since
      current                   the identity is established (validated) as its target
      by_target                 no established identity: associated only by its own target
    Without one (review 06 / 07 decisions, revisions before reader .4) -- context is the anchor's identity:
      not_recorded              that context is the component's current identity, or the component has no identity
      held:context_changed      the component now reads another identity
      held:context_unknown      no identity was known when it was read; one has been read since
      held:context_unavailable  its context cannot be established from reliable recorded evidence
      held:revision_changed     a decision whose component's compatible revision changed since"""
    if o.get("field") not in ("decision", "revision") or not _field_key(o).startswith("own:"):
        return None
    ai = _normalise_ai(ai) if ai else _normalise_ai(None)
    fkey = _field_key(o)
    anchor = _anchor_of(ai, fields, fkey, entry)
    ident = fields.get("own:identity")
    current_entry = _read_entry(ident)
    current_id = _entry_value(current_entry)
    established = current_id if current_id and (current_entry.get("observations") or [{}])[0].get("state") == "validated" else None
    target = o.get("target")
    source = {"anchor": anchor.get("source")}
    if target:
        base = {"target": target, "current_identity": current_id, **source}
        if current_id and not _same("identity", target, current_id):
            return {"status": "held:target_changed", **base, "reason": f"read for {target!r}; the component now reads {current_id!r}"}
        if o.get("field") == "decision":
            now, now_entry = _revision_now(fields, target)
            if o.get("target_revision"):
                then, known = o["target_revision"], True
            elif anchor.get("source") in ("read", "reconstructed"):
                then, known = anchor.get("revision"), anchor.get("revision_known", True)
            else:
                then, known = None, False
            if then and now and not _same("revision", then, now):
                return {"status": "held:revision_changed", **base, "target_revision": then, "current_revision": now,
                        "reason": f"read with revision {then!r} of {target!r}; that component now reads {now!r}"}
            if not known and now and _later(now_entry, entry):
                return {"status": "held:revision_unverifiable", **base, "current_revision": now,
                        "reason": anchor.get("reason") or "the revision it was read with is not recorded reliably"}
        if established:
            return {"status": "current", **base}
        return {"status": "by_target", **base, "reason": "no established current identity: associated only by its recorded target"}
    if current_id is None:
        return {"status": "not_recorded", "context_identity": None, **source}
    if anchor.get("source") not in ("read", "reconstructed"):
        return {"status": "held:context_unavailable", "context_identity": None, "current_identity": current_id, **source,
                "reason": anchor.get("reason") or "its context cannot be established from recorded evidence"}
    context = anchor.get("identity")
    if context is None:
        return {"status": "held:context_unknown", "context_identity": None, "current_identity": current_id, **source,
                "reason": "no identity was known when it was read; one has been read since"}
    base = {"context_identity": context, "current_identity": current_id, **source}
    if not _same("identity", context, current_id):
        return {"status": "held:context_changed", **base, "reason": f"read with {context!r}; the component now reads {current_id!r}"}
    if o.get("field") == "decision":
        then = anchor.get("revision")
        now, now_entry = _revision_now(fields, context)
        if then and now and not _same("revision", then, now):
            return {"status": "held:revision_changed", **base, "context_revision": then, "current_revision": now,
                    "reason": f"read with revision {then!r}; the component now reads {now!r}"}
        if not anchor.get("revision_known", True) and now and _later(now_entry, entry):
            return {"status": "held:revision_unverifiable", **base, "current_revision": now,
                    "reason": "the revision it was read with may no longer be in the retained history"}
    return {"status": "not_recorded", **base}


''' + s[j:]
sub('''    for o in current["observations"]:
        assoc = association_of(o, pages[str(o.get("page") or 1)]["fields"])''',
    '''    for o in current["observations"]:
        page_fields = pages[str(o.get("page") or 1)]["fields"]
        assoc = association_of(o, page_fields, page_fields.get(_field_key(o)), ai)''')
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
