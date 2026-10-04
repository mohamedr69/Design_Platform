"""Derive scripts/m2_eval6.py (evaluator .10, Review 29 C4) from the frozen scripts/m2_eval5.py (.9) by exact, counted
replacements; .9 itself is not touched. Written with LF line endings like its source."""
import pathlib
import sys

B = pathlib.Path("C:/t/iso/cand-r29/backend/scripts")
src = (B / "m2_eval5.py").read_bytes().decode("utf-8")
assert "\r\n" not in src
edits = [
    ('EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.9"   # .9: targetless retained facts held when their context changed (review 10)\n',
     'EVALUATOR_VERSION = "m2-pilot-eval-2026-10-02.10"  # .10: association per fact -- no dependent fact crosses pages (review 29 C4)\n'
     '# m2-pilot-eval-2026-09-29.9: targetless retained facts held when their context changed (review 10)\n', 1),
    ('"""M2 pilot evaluator .5 (M2 review 07, R7-01): every emitted fact is scored.',
     '"""M2 pilot evaluator .10 (M2 review 29, C4): derived from .9 (scripts/m2_eval5.py, unchanged) with ONE change -- association\n'
     'is decided per fact. When a group associates with another page\'s component (cross_page / target_cross_page), only its\n'
     'identity facts take that association (a copy of the document\'s identity on a continuation page, the .6 rule); its\n'
     'dependent facts (revision, decision) are judged on their OWN page: a no-record page makes them false positives when\n'
     'asserted and held_on_negative when held; a page with exactly one component judges them against that component\n'
     '(own_page_component); otherwise they are unassociated. So a fact\'s outcome never depends on whether another fact of\n'
     'its group was asserted. Everything else is .9.\n\n'
     'M2 pilot evaluator .5 (M2 review 07, R7-01): every emitted fact is scored.', 1),
    ('        association[how] += 1\n'
     '        for rec in judge_group(g, e, how, how == "negative_page"):\n'
     '            rec.update(page=g["page"], reader=g["reader"], group=g["component"], layer=g["layer"],\n'
     '                       expected=e["_id"] if e is not None else None)\n'
     '            judged.append(rec)\n',
     '        association[how] += 1\n'
     '        parts = [(g, e, how)]\n'
     '        if how in ("cross_page", "target_cross_page"):\n'
     '            # .10 (C4 A4 / A6): only identity facts cross pages; dependent facts are judged on their own page\n'
     '            ident = [f for f in g["facts"] if f["field"] in ("identity", "referenced_identity")]\n'
     '            deps = [f for f in g["facts"] if f["field"] not in ("identity", "referenced_identity")]\n'
     '            here = exp_by_page.get(g["page"], [])\n'
     '            if negative_page:\n'
     '                e_dep, how_dep = None, "negative_page"\n'
     '            elif len(here) == 1 and not g.get("unassigned_component"):\n'
     '                e_dep, how_dep = here[0], "own_page_component"\n'
     '            else:\n'
     '                e_dep, how_dep = None, "unassociated"\n'
     '            parts = [(dict(g, facts=ident), e, how)] + ([(dict(g, facts=deps), e_dep, how_dep)] if deps else [])\n'
     '            if deps:\n'
     '                association["dependents_on_own_page"] += 1\n'
     '        for gg, ee, hh in parts:\n'
     '            for rec in judge_group(gg, ee, hh, hh == "negative_page"):\n'
     '                rec.update(page=gg["page"], reader=gg["reader"], group=gg["component"], layer=gg["layer"],\n'
     '                           expected=ee["_id"] if ee is not None else None)\n'
     '                judged.append(rec)\n', 1),
]
for a, b, n in edits:
    if src.count(a) != n:
        sys.exit(f"anchor count {src.count(a)} != {n}: {a[:80]!r}")
    src = src.replace(a, b)
out = B / "m2_eval6.py"
assert not out.exists(), "m2_eval6.py exists"
out.write_bytes(src.encode("utf-8"))
print("wrote", out)
