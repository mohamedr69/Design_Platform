"""M2 review 12 (R12-01): legacy anchor reconstruction carries the exact historical entry and requires reliable order
for every context entry it uses; anchors reconstructed by reader .6 are re-derived from recorded history or held.
evidence-reader 2026-09-29.7 (reconstruction only)."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
raw = p.read_bytes()
assert b"\r\n" in raw
s = raw.decode("utf-8").replace("\r\n", "\n")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('READER_VERSION = "evidence-reader-2026-09-29.6"   # .6: review 11 (durable association context, persistent attempt order)',
    'READER_VERSION = "evidence-reader-2026-09-29.7"   # .7: review 12 (legacy anchor reconstruction: exact entries, reliable order)\n'
    '# evidence-reader-2026-09-29.6: review 11 (durable association context, persistent attempt order)')

# --- merge: stamp missing anchors, and re-derive anchors reader .6 reconstructed, before anything is pruned ------------
sub('''            entry = page_fields["fields"].get(fkey)
            if entry is not None and "anchor" not in entry:
                page_fields["fields"][fkey] = {**entry, "anchor": _reconstruct_anchor(ai, page_fields["fields"], fkey, entry)}''',
    '''            entry = page_fields["fields"].get(fkey)
            if entry is not None and _needs_anchor(entry):
                page_fields["fields"][fkey] = {**entry, "anchor": _anchor_of(ai, page_fields["fields"], fkey, entry)}''')

# --- the reconstruction ------------------------------------------------------------------------------------------------
i = s.index("def _context_identity(fields: dict, entry: dict | None) -> tuple[bool, str | None]:")
j = s.index("def _later(entry: dict | None, than: dict | None) -> bool:")
k0 = s.index("def _attempt_reliable(", i)
k1 = s.index("def _value_at(", k0)
attempt_reliable = s[k0:k1]              # kept unchanged
assert "def _reconstruct_anchor" in s[i:j] and "def _anchor_of" in s[i:j] and "def _value_at" in s[i:j]
s = s[:i] + attempt_reliable + '''# Reconstruction of pre-.6 context (M2 review 12, R12-01). The anchor of a fact stored before .6 is rebuilt from the
# EXACT historical entries in effect at the fact's attempt -- selected by their recorded order, never looked up again
# by printed value -- and records them (`identity_entry`, `revision_entry`: value, target, attempt / seq). Every entry
# used needs a reliable order: `seq` (reader .6+, later than any pre-.6 attempt), a unique numbered attempt, or the
# explicit flat review 06 `legacy` reading (one reading, before every numbered attempt). A missing or non-numeric order
# is never attempt 0, and two different entries with one order are ambiguous: the context is then `unavailable`.
# Four outcomes stay distinct -- found, established absence (nothing at or before the attempt, and the field's history
# below its bound, so nothing can have been pruned), incompatible (the revision then in effect was read for another
# component) and unavailable -- and only the first two are known: an incompatible or unavailable revision context is
# `revision_known: false`, never an absence. Anchors .6 reconstructed carry no `rule`; they are re-derived by this rule
# from recorded history (never from current context), the original kept as `replaced_anchor`, and held when that is
# not determinate. Read-time anchors and .6 `unavailable` anchors are kept as they are.
RECONSTRUCTION_RULE = "reconstruct-2"


def _order_of(ai: dict, fields: dict, provenance: dict | None) -> tuple | None:
    """A comparable, reliable order for an entry, or None: (0, 0) the flat `legacy` reading; (1, n) a unique numbered
    pre-.6 attempt; (2, seq) a .6+ attempt."""
    prov = provenance or {}
    if prov.get("seq") is not None:
        return (2, int(prov["seq"]))
    if prov.get("attempt") == "legacy":
        return (0, 0)
    ok, _why = _attempt_reliable(ai, fields, prov.get("attempt"))
    return (1, _numbered(prov["attempt"])) if ok else None


def _brief(entry: dict | None) -> dict | None:
    if not entry:
        return None
    prov = entry.get("provenance") or {}
    first = (entry.get("observations") or [{}])[0]
    return {"value": _entry_value(entry), "target": first.get("target"), "attempt": prov.get("attempt"), "seq": prov.get("seq"),
            "at": prov.get("at")}


def _entry_in_effect(ai: dict, fields: dict, field_entry: dict | None, at: tuple, name: str) -> dict:
    """{"status": "found", "entry", "order"} | {"status": "absent"} | {"status": "unavailable", "reason"}: the exact
    entry of a field (current or in history) in effect at order `at`."""
    if field_entry is None:
        return {"status": "absent"}
    ordered = []
    for e in [field_entry] + list(field_entry.get("history") or []):
        if e.get("status") not in (COMPLETED, "legacy"):
            continue
        order = _order_of(ai, fields, e.get("provenance"))
        if order is None:
            return {"status": "unavailable", "reason": f"a {name} entry has no reliable recorded order"}
        ordered.append((order, e))
    eligible = [(o, e) for o, e in ordered if o <= at]
    if eligible:
        top = max(o for o, _e in eligible)
        tops = [e for o, e in eligible if o == top]
        if len({json.dumps(_brief(e) and {k: _brief(e)[k] for k in ("value", "target")}, sort_keys=True) for e in tops}) > 1:
            return {"status": "unavailable", "reason": f"two different {name} entries are recorded with the same order"}
        return {"status": "found", "entry": tops[0], "order": top}
    if len(field_entry.get("history") or []) >= MAX_FIELD_HISTORY:
        return {"status": "unavailable", "reason": f"the {name} entry in effect then may have been pruned"}
    return {"status": "absent"}


def _reconstruct_anchor(ai: dict, fields: dict, fkey: str, entry: dict) -> dict:
    """The anchor of a fact stored before .6, from the exact, reliably ordered historical entries in effect then."""
    prov = entry.get("provenance") or {}
    ok, why = _attempt_reliable(ai, fields, prov.get("attempt"))
    if not ok:
        return {"source": "unavailable", "rule": RECONSTRUCTION_RULE, "reason": why}
    at = _order_of(ai, fields, prov)
    ident = _entry_in_effect(ai, fields, fields.get("own:identity"), at, "identity")
    if ident["status"] == "unavailable":
        return {"source": "unavailable", "rule": RECONSTRUCTION_RULE, "reason": ident["reason"]}
    anchor = {"source": "reconstructed", "rule": RECONSTRUCTION_RULE, "attempt": prov.get("attempt"),
              "identity": _entry_value(ident.get("entry")), "identity_status": ident["status"], "identity_entry": _brief(ident.get("entry"))}
    if fkey != "own:decision":
        return anchor
    target = (entry.get("observations") or [{}])[0].get("target") or anchor["identity"]
    rev = _entry_in_effect(ai, fields, fields.get("own:revision"), at, "revision")
    if rev["status"] == "absent":
        return {**anchor, "revision": None, "revision_known": True, "revision_status": "absent"}
    if rev["status"] == "unavailable":
        return {**anchor, "revision": None, "revision_known": False, "revision_status": "unavailable", "revision_reason": rev["reason"]}
    found = rev["entry"]
    first = (found.get("observations") or [{}])[0]
    if first.get("target"):
        compatible = bool(target) and _same("identity", first["target"], target)
    else:
        context = _entry_in_effect(ai, fields, fields.get("own:identity"), rev["order"], "identity")
        if context["status"] != "found" or not target:
            return {**anchor, "revision": None, "revision_known": False, "revision_status": "unavailable", "revision_entry": _brief(found),
                    "revision_reason": "the component the revision then in effect was read for cannot be established"}
        compatible = _same("identity", _entry_value(context["entry"]), target)
    if not compatible:
        return {**anchor, "revision": None, "revision_known": False, "revision_status": "incompatible", "revision_entry": _brief(found),
                "revision_reason": "the revision then in effect was read for another component"}
    return {**anchor, "revision": _entry_value(found), "revision_known": True, "revision_status": "found", "revision_entry": _brief(found)}


def _needs_anchor(entry: dict) -> bool:
    """No anchor yet, or one reader .6 reconstructed (no `rule`): it may have been selected by value (R12-01A)."""
    a = entry.get("anchor")
    return a is None or (a.get("source") == "reconstructed" and a.get("rule") != RECONSTRUCTION_RULE)


def _anchor_of(ai: dict, fields: dict, fkey: str, entry: dict | None) -> dict:
    """The anchor selection uses: a read-time anchor, a current-rule reconstruction or any `unavailable` anchor as
    stored; otherwise reconstructed now -- a .6 reconstruction re-derived from recorded history, its original kept."""
    if not entry:
        return {"source": "unavailable", "reason": "no retained entry"}
    a = entry.get("anchor")
    if a is not None and not _needs_anchor(entry):
        return a
    new = _reconstruct_anchor(ai, fields, fkey, entry)
    return {**new, "replaced_anchor": a} if a is not None else new


def _context_identity(ai: dict, fields: dict, entry: dict | None, fkey: str = "own:revision") -> tuple[bool, str | None]:
    """(known, identity) of the component a revision entry was read for: its recorded target, else its anchor."""
    if not entry:
        return False, None
    first = (entry.get("observations") or [{}])[0]
    if first.get("target"):
        return True, first["target"]
    anchor = _anchor_of(ai, fields, fkey, entry)
    if anchor.get("source") in ("read", "reconstructed"):
        return True, anchor.get("identity")
    return False, None


def _revision_now(ai: dict, fields: dict, target: str | None) -> tuple[str | None, dict | None]:
    """(value, entry) of the own revision now compatible with component `target`: read for that target (recorded
    target, else its anchor). An unrelated revision -- another component's, or one of unknown context -- is none."""
    entry = _read_entry(fields.get("own:revision"))
    if not target or not entry:
        return None, None
    known, context = _context_identity(ai, fields, entry)
    return (_entry_value(entry), entry) if known and context and _same("identity", context, target) else (None, None)


def _read_anchor(ai: dict, fields: dict, fkey: str, entry: dict, seq: int) -> dict:
    """The context a fact written by attempt `seq` was read in: the component as it stands after that attempt."""
    identity = _entry_value(_read_entry(fields.get("own:identity")))
    anchor = {"source": "read", "seq": seq, "identity": identity}
    if fkey == "own:decision":
        target = (entry.get("observations") or [{}])[0].get("target") or identity
        anchor["revision"] = _revision_now(ai, fields, target)[0]
    return anchor


''' + s[j:]
# callers of the helpers whose signatures gained `ai`
sub('''            now, now_entry = _revision_now(fields, target)''', '''            now, now_entry = _revision_now(ai, fields, target)''')
sub('''        now, now_entry = _revision_now(fields, context)''', '''        now, now_entry = _revision_now(ai, fields, context)''')
if "import json" not in s.split("\n\n", 3)[0] + s[:3000]:
    pass
p.write_bytes(s.replace("\n", "\r\n").encode("utf-8"))
print("ok")
