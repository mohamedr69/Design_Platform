"""Evaluator .9 (M2 review 10, R10-01): a held retained fact without a target is its own unassociated group; target,
target revision, association and recorded context identity travel into every judgement."""
import pathlib

p = pathlib.Path("C:/t/iso/ep-platform/backend/scripts/m2_eval5.py")
s = p.read_text(encoding="utf-8")
assert "\r\n" not in s


def sub(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


sub('EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.8"   # .8: retained facts judged under their association; source identity (review 09)',
    'EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.9"   # .9: targetless retained facts held when their context changed (review 10)\n'
    '# m2-pilot-eval-2026-09-29.8: retained facts judged under their association; source identity (review 09)')
sub('''    travel with the fact into the judgement; a fact that never recorded a target is grouped as before."""''',
    '''    travel with the fact into the judgement; a fact that never recorded a target is grouped as before.
    Review 10 (R10-01): a held fact that never recorded a target (its component's identity or revision changed since it
    was read) is a group of its own with no association (`unassigned_component`): judged held and unassociated -- no
    target is invented and it is never reassigned. Target revision and recorded context identity travel with it."""''')
sub('''            if status and (status.startswith("held:") or status == "by_target"):
                key = f"ai:{page}:{o.get('component') or 'own'}@{assoc['target']}"''',
    '''            if status and (status.startswith("held:") or status == "by_target"):
                key = (f"ai:{page}:{o.get('component') or 'own'}@{assoc['target']}" if assoc.get("target") else
                       f"ai:{page}:{o.get('component') or 'own'}~unassociated")''')
sub('''            if "@" in key:
                g["association_identity"] = assoc["target"]''', '''            if "@" in key:
                g["association_identity"] = assoc["target"]
            if key.endswith("~unassociated"):
                g["unassigned_component"] = True''')
sub('''            extra = {k: v for k, v in (("target", o.get("target")), ("association", status)) if v}''',
    '''            extra = {k: v for k, v in (("target", o.get("target")), ("target_revision", o.get("target_revision")),
                                       ("association", status), ("context_identity", assoc.get("context_identity"))) if v}''')
sub('''                               **{k: f[k] for k in ("target", "association") if f.get(k)}})''',
    '''                               **{k: f[k] for k in CARRIED if f.get(k)}})''')
sub('''               **{k: f[k] for k in ("target", "association") if f.get(k)}}''',
    '''               **{k: f[k] for k in CARRIED if f.get(k)}}''')
sub('''CRITICAL_OUTCOMES = ("wrong", "fp", "accepted_on_conflict", "wrong_unassociated")''',
    '''CRITICAL_OUTCOMES = ("wrong", "fp", "accepted_on_conflict", "wrong_unassociated")
CARRIED = ("target", "target_revision", "association", "context_identity")   # association metadata kept on judgements''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
