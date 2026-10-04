"""M2 review 10 (R10-01): association compatibility of retained dependent facts. evidence-reader 2026-09-29.5
(selection only; evidence-policy .4 -- the validation rules -- is unchanged)."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
raw = p.read_bytes()
assert b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('READER_VERSION = "evidence-reader-2026-09-29.4"   # .4: review 09 (usable reads, fact association, source identity)',
    'READER_VERSION = "evidence-reader-2026-09-29.5"   # .5: review 10 (association compatibility of retained facts)\n'
    '# evidence-reader-2026-09-29.4: review 09 (usable reads, fact association, source identity)')

i = s.index("def _usable_value(entry: dict | None) -> str | None:")
j = s.index("def evidence_for(")
s = s[:i] + '''def _attempt_no(provenance: dict | None) -> int:
    """An attempt number from provenance; review 06 `legacy` (and anything unnumbered) is attempt 0."""
    a = (provenance or {}).get("attempt")
    return a if isinstance(a, int) else int(a) if str(a).isdigit() else 0


def _entry_value(entry: dict | None) -> str | None:
    values = [o.get("value") for o in (entry or {}).get("observations") or [] if o.get("value") not in (None, "")]
    return values[0] if values else None


def _read_entry(entry: dict | None) -> dict | None:
    """The field's current entry when it is read evidence (completed, or legacy) -- an incomplete field anchors nothing."""
    return entry if entry and entry.get("status") in (COMPLETED, "legacy") else None


def _entry_at(entry: dict | None, attempt: int) -> dict | None:
    """The field's read entry -- current or in its history -- in effect at `attempt`: the latest one read no later."""
    best = None
    for e in ([entry] + list(entry.get("history") or [])) if entry else []:
        if e.get("status") not in (COMPLETED, "legacy"):
            continue
        n = _attempt_no(e.get("provenance"))
        if n <= attempt and (best is None or n >= _attempt_no(best.get("provenance"))):
            best = e
    return best


def _same(field: str, a, b) -> bool:
    return literal_key(field, a) == literal_key(field, b)


def _revision_for(fields: dict, target: str | None, at: int | None = None) -> str | None:
    """The own revision compatible with component `target` -- now, or at attempt `at`: one whose recorded target is
    `target`, or, with no target recorded, whose identity at its own attempt was `target`. Any other revision (another
    component's, or one of unknown context) is unrelated and supplies no anchor."""
    if not target:
        return None
    rev = fields.get("own:revision")
    e = _read_entry(rev) if at is None else _entry_at(rev, at)
    if not e:
        return None
    first = (e.get("observations") or [{}])[0]
    if first.get("target"):
        compatible = _same("identity", first["target"], target)
    else:
        context = _entry_value(_entry_at(fields.get("own:identity"), _attempt_no(e.get("provenance"))))
        compatible = bool(context) and _same("identity", context, target)
    return _entry_value(e) if compatible else None


def association_of(o: dict, fields: dict) -> dict | None:
    """The association of a dependent fact (a revision or a decision of the page's own component) with the component
    as it is read now (M2 review 09, R9-02; review 10, R10-01). The rules are review10/COMPATIBILITY.md; every known
    constraint is checked before a fact is associated, and nothing is ever reattached or given an invented target.
    With a recorded `target`:
      held:target_changed   the component's current identity (established or not) is another one
      held:revision_changed a decision whose revision anchor (`target_revision`, else the compatible revision at its
                            own attempt) differs from the revision now compatible with its target -- with or without
                            a current identity
      current               the identity is established (validated) as its target
      by_target             no established identity: associated only by its own target
    Without one (review 06 / 07 decisions, revisions before reader .4) -- the component it was read with is the identity
    in effect at its own attempt (retained provenance / history), recorded context, never a target:
      not_recorded          that context is the component's current identity, or the component has no identity
                            (the supported, unchanged grouping); `context_identity` names it
      held:context_changed  the component now reads another identity
      held:context_unknown  no identity was known when it was read; one has been read since
      held:revision_changed a decision whose component's compatible revision changed since"""
    if o.get("field") not in ("decision", "revision") or not _field_key(o).startswith("own:"):
        return None
    attempt = _attempt_no(o.get("provenance"))
    ident = fields.get("own:identity")
    current_entry = _read_entry(ident)
    current_id = _entry_value(current_entry)
    established = current_id if current_id and (current_entry.get("observations") or [{}])[0].get("state") == "validated" else None
    target = o.get("target")
    if target:
        base = {"target": target, "current_identity": current_id}
        if current_id and not _same("identity", target, current_id):
            return {"status": "held:target_changed", **base, "reason": f"read for {target!r}; the component now reads {current_id!r}"}
        if o.get("field") == "decision":
            anchor = o.get("target_revision") or _revision_for(fields, target, at=attempt)
            now = _revision_for(fields, target)
            if anchor and now and not _same("revision", anchor, now):
                return {"status": "held:revision_changed", **base, "target_revision": anchor, "current_revision": now,
                        "reason": f"read with revision {anchor!r} of {target!r}; that component now reads {now!r}"}
        if established:
            return {"status": "current", **base}
        return {"status": "by_target", **base, "reason": "no established current identity: associated only by its recorded target"}
    if current_id is None:
        return {"status": "not_recorded", "context_identity": None}
    context = _entry_value(_entry_at(ident, attempt))
    if context is None:
        return {"status": "held:context_unknown", "context_identity": None, "current_identity": current_id,
                "reason": "no identity was known when it was read; one has been read since"}
    base = {"context_identity": context, "current_identity": current_id}
    if not _same("identity", context, current_id):
        return {"status": "held:context_changed", **base, "reason": f"read with {context!r}; the component now reads {current_id!r}"}
    if o.get("field") == "decision":
        then, now = _revision_for(fields, context, at=attempt), _revision_for(fields, context)
        if then and now and not _same("revision", then, now):
            return {"status": "held:revision_changed", **base, "context_revision": then, "current_revision": now,
                    "reason": f"read with revision {then!r}; the component now reads {now!r}"}
    return {"status": "not_recorded", **base}


''' + s[j:]
sub('''    for o in current["observations"]:
        page = pages[str(o.get("page") or 1)]["fields"]
        assoc = association_of(o, _usable_value(page.get("own:identity")), _usable_value(page.get("own:revision")))''',
    '''    for o in current["observations"]:
        assoc = association_of(o, pages[str(o.get("page") or 1)]["fields"])''')
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
