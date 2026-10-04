"""Evaluator .8 (M2 review 09): retained facts are judged under their explicit association (R9-02); unknown source
bytes are scored only under a declared, manifest-backed historical binding (R9-03)."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/scripts/m2_eval5.py")
s = p.read_text(encoding="utf-8")
assert "\r\n" not in s


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.7"   # .7: AI evidence selected for the run\'s declared context (review 08)',
    'EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.8"   # .8: retained facts judged under their association; source identity (review 09)\n'
    '# m2-pilot-eval-2026-09-29.7: AI evidence selected for the run\'s declared context (review 08)')
sub('''def ai_envelope(row: dict | None, ai_context: dict | None) -> tuple[dict, str]:''',
    '''def ai_envelope(row: dict | None, ai_context: dict | None, doc: str | None = None) -> tuple[dict, str]:''')
sub('''    declares `accept_unknown_profile` (from the run manifest)."""''', '''    declares `accept_unknown_profile` (from the run manifest). Evidence that records no source hash is scored only
    under a declared historical binding -- `historical_source` {"manifest", "sha256_by_doc"} from a run manifest --
    and only for the bytes that manifest names for this document (review 09, R9-03)."""''')
sub('''    profile = ai_context.get("profile", (row.get("extracted") or {}).get("profile"))
    got = evidence_reader.evidence_for(ai, sha256=row.get("sha256"), profile=profile, variant=ai_context.get("variant"),
                                       policies=ai_context.get("policies"), accept_unknown_profile=bool(ai_context.get("accept_unknown_profile")))''',
    '''    profile = ai_context.get("profile", (row.get("extracted") or {}).get("profile"))
    hs = ai_context.get("historical_source") or None
    binding = ({"manifest": hs.get("manifest"), "sha256": (hs.get("sha256_by_doc") or {}).get(doc)} if hs and doc else None)
    got = evidence_reader.evidence_for(ai, sha256=row.get("sha256"), profile=profile, variant=ai_context.get("variant"),
                                       policies=ai_context.get("policies"), accept_unknown_profile=bool(ai_context.get("accept_unknown_profile")),
                                       historical_source=binding)''')
sub('''def ai_groups(row: dict | None, ai_context: dict | None = None) -> list[dict]:
    """One group per AI component read. Review 07 observations carry a `component` key; review 06 observations do
    not, so their page's single own-identity read is one component -- and where a page has several AI identity
    observations, each is its own group and that page's revision / decision observations stay unassociated with any
    of them (`component: None`), never merged into one."""
    env, _state = ai_envelope(row, ai_context)''', '''def ai_groups(row: dict | None, ai_context: dict | None = None, doc: str | None = None) -> list[dict]:
    """One group per AI component read. Review 07 observations carry a `component` key; review 06 observations do
    not, so their page's single own-identity read is one component -- and where a page has several AI identity
    observations, each is its own group and that page's revision / decision observations stay unassociated with any
    of them (`component: None`), never merged into one.
    Review 09 (R9-02): a dependent fact keeps its explicit association (`evidence_reader.association_of`). One whose
    target is not the component's current identity -- `held:*` (held) or `by_target` (its own state) -- is a group of
    its own, associated by its target (`association_identity`), never beside another identity. Target and association
    travel with the fact into the judgement; a fact that never recorded a target is grouped as before."""
    env, _state = ai_envelope(row, ai_context, doc)''')
sub('''            if o.get("component") is not None:
                key = f"ai:{page}:{o['component']}"''', '''            assoc = o.get("association") or {}
            status = assoc.get("status")
            if status and (status.startswith("held:") or status == "by_target"):
                key = f"ai:{page}:{o.get('component') or 'own'}@{assoc['target']}"
            elif o.get("component") is not None:
                key = f"ai:{page}:{o['component']}"''')
sub('''            g = groups.setdefault(key, _group(page, "ai", "ai_evidence", f"ai:{o.get('variant') or env.get('variant')}", key, [],
                                              {"version": o.get("version"), "policy": o.get("policy"), "profile": env.get("profile")}))
            if role != "own" and o.get("field") == "identity":
                g["facts"].append(_fact("referenced_identity", o["value"], "observed_reference", role=role))
                continue
            g["facts"].append(_fact(o.get("field"), o["value"], state_of(o), ai_state=o.get("state")))''',
    '''            g = groups.setdefault(key, _group(page, "ai", "ai_evidence", f"ai:{o.get('variant') or env.get('variant')}", key, [],
                                              {"version": o.get("version"), "policy": o.get("policy"), "profile": env.get("profile")}))
            if "@" in key:
                g["association_identity"] = assoc["target"]
            if role != "own" and o.get("field") == "identity":
                g["facts"].append(_fact("referenced_identity", o["value"], "observed_reference", role=role))
                continue
            state = "held" if status and status.startswith("held:") else state_of(o)
            extra = {k: v for k, v in (("target", o.get("target")), ("association", status)) if v}
            g["facts"].append(_fact(o.get("field"), o["value"], state, ai_state=o.get("state"), **extra))''')
sub('''    unassociated | no_component. Only asserted identities associate by value."""
    here = exp_by_page.get(g["page"], [])''', '''    unassociated | no_component. Only asserted identities associate by value. A group of retained facts whose
    association is their own recorded target (`association_identity`, review 09) associates by that target only:
    target | target_cross_page | target_unmatched -- never by the page's other component."""
    here = exp_by_page.get(g["page"], [])
    if g.get("association_identity"):
        target = g["association_identity"]
        for strength in ("exact", "suffix"):
            for e in here:
                if ev4.reference_truth(e.get("reference"))[0] == "readable" and v3.same_identity(v3.literal(e["reference"]), target) == strength:
                    return e, "target"
        for e in exp_all:
            if e["page"] != g["page"] and ev4.reference_truth(e.get("reference"))[0] == "readable" and \\
                    v3.same_identity(v3.literal(e["reference"]), target) in ("exact", "suffix"):
                return e, "target_cross_page"
        return None, "target_unmatched"''')
sub('''        rec = {"field": field, "value": f["value"], "state": state, "how": how}''',
    '''        rec = {"field": field, "value": f["value"], "state": state, "how": how,
               **{k: f[k] for k in ("target", "association") if f.get(k)}}''')
sub('''        if negative_page and how != "cross_page":''', '''        if negative_page and how not in ("cross_page", "target_cross_page"):''')
sub('''        ai = ai_groups(row, ai_context)
        ai_state = ai_envelope(row, ai_context)[1]''', '''        ai = ai_groups(row, ai_context, key)
        ai_state = ai_envelope(row, ai_context, key)[1]''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
