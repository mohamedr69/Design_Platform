import pathlib
import re

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/tests/test_m2_review08.py")
s = p.read_text(encoding="utf-8")


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)


ADAPTERS = '''

# --- what a consumer gets ----------------------------------------------------------------------------------------------
# The review 07 code had one accessor, `current_evidence(ai)`, which ignores the requested context; its consumers (the
# evaluator, the API) used it. These adapters call it on a prior candidate so that, run there, the tests fail on
# behaviour rather than on a missing name.


def select(ai, *, sha256, profile, variant, **kw):
    if hasattr(er, "evidence_for"):
        return er.evidence_for(ai, sha256=sha256, profile=profile, variant=variant, **kw)
    env = er.current_evidence(ai)
    if not env:
        return {"state": "unavailable"}
    pages = {}
    for pno, page in (env.get("pages") or {}).items():
        by = {}
        for o in page.get("observations") or []:
            by.setdefault(f"{o.get('component') or 'own'}:{o['field']}", {"observations": [], "status": "completed",
                                                                         "provenance": page.get("provenance") or {}, "history": []})["observations"].append(o)
        pages[pno] = {"fields": by}
    return {"state": "current", "envelope": {**env, "pages": pages}, "observations": env.get("observations") or [], "incomplete": []}


def last_known(ai):
    return er.last_known(ai) if hasattr(er, "last_known") else {"key": ai.get("current_key")}


def attempt_page(ai, n=-1, page="1"):
    got = ai["attempts"][n]["pages"].get(page)
    return got if isinstance(got, dict) else {"outcome": got, "fields": {}}


MISMATCH = getattr(L, "LedgerConfigMismatch", L.LedgerRefused)
'''
sub('''APPROVAL = {"options": LEGEND, "marked": "B = APPROVED AS NOTED", "mark": "tick", "actor": "consultant"}
''', '''APPROVAL = {"options": LEGEND, "marked": "B = APPROVED AS NOTED", "mark": "tick", "actor": "consultant"}
''' + ADAPTERS)
s = s.replace("er.evidence_for(", "select(").replace("er.last_known(", "last_known(")
s = s.replace('ai["attempts"][-1]["pages"]["1"]["fields"]', 'attempt_page(ai)["fields"]')
s = s.replace('ai["attempts"][-1]["pages"]["1"]', 'attempt_page(ai)')
s = s.replace('["changed"] == []', '.get("changed") == []')
s = s.replace('[a["pages"]["1"]["outcome"] for a in ai["attempts"]]', '[attempt_page(ai, n)["outcome"] for n in range(len(ai["attempts"]))]')
s = s.replace('got["row_type"]', 'got.get("row_type")')

# test 1: the retained values first, then the recorded read outcomes
sub('''    ai = stage(doc_row, [discover("X-SD-1"), timeout()])
    page = attempt_page(ai)
    assert page["outcome"] == "partial" and page["fields"]["own:identity"] == "failed:timeout"
    assert page["fields"]["own:decision"] == "absent_by_discovery"
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed")
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed"), "the old decision survives"''',
    '''    ai = stage(doc_row, [discover("X-SD-1"), timeout()])
    assert value(ai, "own:decision") == ("ANN", "validated", 1, "completed"), "the old decision survives"
    assert value(ai, "own:identity") == ("X-SD-1", "validated", 1, "completed")
    page = attempt_page(ai)
    assert page["outcome"] == "partial" and page["fields"]["own:identity"] == "failed:timeout"
    assert page["fields"]["own:decision"] == "absent_by_discovery"''')
sub('''    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:revision"] == "failed:timeout" and f["own:decision"] == "budget"
    assert value(ai, "own:identity")[0] == "X-SD-9" and value(ai, "own:identity")[2] == 2, "the completed read replaces"
    assert value(ai, "own:revision") == ("02", "validated", 1, "completed"), "the timed-out read replaces nothing"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1), "the refused read replaces nothing"''',
    '''    assert value(ai, "own:revision") == ("02", "validated", 1, "completed"), "the timed-out read replaces nothing"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1), "the refused read replaces nothing"
    assert value(ai, "own:identity")[0] == "X-SD-9" and value(ai, "own:identity")[2] == 2, "the completed read replaces"
    f = attempt_page(ai)["fields"]
    assert f["own:identity"] == "completed" and f["own:revision"] == "failed:timeout" and f["own:decision"] == "budget"''')
sub('''    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    assert attempt_page(ai)["fields"]["own:decision"] == "absent_by_discovery"
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1)''',
    '''    ai = stage(doc_row, [discover("X-SD-1"), read("X-SD-1")])
    assert value(ai, "own:decision")[:3] == ("ANN", "validated", 1)
    assert attempt_page(ai)["fields"]["own:decision"] == "absent_by_discovery"''')

# evaluator: a prior evaluator has no context parameter -- it is called the way its runs called it
sub('''    promoted = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})''',
    '''    import inspect

    if "ai_context" not in inspect.signature(ev.evaluate).parameters:
        before = ev.evaluate({"documents": [doc]}, None, rows)
        assert before["totals"]["introduced_ai_errors"] == [], "the promoted run is scored with the default profile's evidence"
    promoted = ev.evaluate({"documents": [doc]}, None, rows, ai_context={"variant": "EV1"})''')

# ledger: the reviewer's case without naming the new exception first
sub('''    first.settle(first.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    with pytest.raises(L.LedgerConfigMismatch):
        L.Ledger(path, "fixed", L.Limits(requests=2))
    reopened''', '''    first.settle(first.reserve("t", 1, 1), input_tokens=1, output_tokens=1)
    with pytest.raises((MISMATCH, L.LedgerRefused)):
        L.Ledger(path, "fixed", L.Limits(requests=2)).reserve("t", 1, 1)       # no silent second reservation
    with pytest.raises(MISMATCH):
        L.Ledger(path, "fixed", L.Limits(requests=2))
    reopened''')
s = s.replace("pytest.raises(L.LedgerConfigMismatch)", "pytest.raises(MISMATCH)").replace("except L.LedgerConfigMismatch:", "except MISMATCH:")
p.write_text(s, encoding="utf-8", newline="\n")
print("ok", s.count("select("), s.count("MISMATCH"))
