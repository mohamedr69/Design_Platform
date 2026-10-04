"""Evaluator .7 (M2 review 08, R8-02): AI evidence is selected for the evaluated run's declared context."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\scripts\m2_eval5.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.6"', 'EVALUATOR_VERSION = "m2-pilot-eval-2026-09-29.7"   # .7: AI evidence selected for the run\'s declared context (review 08)\n# m2-pilot-eval-2026-09-29.6')
i, j = s.index("def ai_envelope(row: dict | None) -> dict:"), s.index("def ai_groups(row: dict | None) -> list[dict]:")
s = s[:i] + '''def ai_envelope(row: dict | None, ai_context: dict | None) -> tuple[dict, str]:
    """(envelope, state) of the AI evidence that applies to the evaluated run's declared context -- its variant,
    its extraction profile (default: the row's own) and optionally the compatible policies -- through
    `evidence_reader.evidence_for`. No context, no AI evidence: another run's envelope is never scored for this one
    (review 08, R8-02). A historical run whose stored envelopes carry no profile is scored only when its context
    declares `accept_unknown_profile` (from the run manifest)."""
    if ai_context is None:
        return {}, "no_context"
    from app.ai import evidence_reader

    row = row or {}
    ai = (row.get("extracted") or {}).get("ai_evidence") or {}
    if not ai:
        return {}, "none"
    profile = ai_context.get("profile", (row.get("extracted") or {}).get("profile"))
    got = evidence_reader.evidence_for(ai, sha256=row.get("sha256"), profile=profile, variant=ai_context.get("variant"),
                                       policies=ai_context.get("policies"), accept_unknown_profile=bool(ai_context.get("accept_unknown_profile")))
    return (got.get("envelope") or {}) if got["state"] == "current" else {}, got["state"]


''' + s[j:]
sub('''def ai_groups(row: dict | None) -> list[dict]:''', '''def ai_groups(row: dict | None, ai_context: dict | None = None) -> list[dict]:''')
sub('''    env = ai_envelope(row)''', '''    env, _state = ai_envelope(row, ai_context)''')
sub('''def evaluate(labels: dict, page_labels: dict | None, rows: dict, corrections: list[dict] | None = None) -> dict:''',
    '''def evaluate(labels: dict, page_labels: dict | None, rows: dict, corrections: list[dict] | None = None,
             ai_context: dict | None = None) -> dict:''')
sub('''        ai = ai_groups(row)''', '''        ai = ai_groups(row, ai_context)
        ai_state = ai_envelope(row, ai_context)[1]''')
p.write_text(s, encoding="utf-8")
print("ok")
