"""The Review 16 association probe (association_probe.reviewer-original.py), with ONLY its code / output folders made
parameters (PROBE_CODE, PROBE_OUT) and, for R16-02, the consumer taken from what the harness under test actually
ships: replay_boq_r15.py's `classify` fed by the r15 pair lookup (as the reviewer did) when that file exists, or the
r16 reporting path `replay_core.replay_sheet` when it exists. Inputs are the reviewer's, unchanged."""
from pathlib import Path
import ast, importlib.util, json, os

R = Path(os.environ["PROBE_OUT"]); R.mkdir(parents=True, exist_ok=True)
S = Path(os.environ["PROBE_CODE"])
spec = importlib.util.spec_from_file_location('bc', S / 'boq_contract.py'); bc = importlib.util.module_from_spec(spec); spec.loader.exec_module(bc)
def e(id, y, description, part, qty): return dict(id=id, page=1, y=y, description=description, part_number=part, quantity=qty)
def t(n, description, part, qty, y=None):
    d = dict(ordinal=n, page=1, description=description, part_number=part, quantity=qty)
    if y is not None: d['y'] = y
    return d
truth = [t(1, 'Manual call point', 'MCP', 1), t(2, 'Control panel', 'PANEL', 1, 200), t(3, 'Manual call point with cover', 'MCP', 2)]
emitted = [e('anchor', 200, 'Control panel', 'PANEL', 1), e('below-anchor', 300, 'Manual call point', 'MCP', 1)]
r = bc.join_rows(emitted, truth)
wrong = [p for p in r['pairs'] if p[0] == 'below-anchor' and p[1] == 1 and p[2].startswith('matched')]
r_no_anchor = bc.join_rows([emitted[1]], truth)
wrong_no_anchor = [p for p in r_no_anchor['pairs'] if p[0] == 'below-anchor' and p[1] == 1 and p[2].startswith('matched')]
control = bc.join_rows([e('above-anchor', 100, 'Manual call point', 'MCP', 1), emitted[0]], truth)
amb_t = [t(6, 'Speaker', 'PT-1S', 1, 100)]
amb_e = [e('a', 95, 'Speaker', 'PT-1S', 1), e('b', 105, 'Speaker', 'PT-1S', 1)]
amb = bc.join_rows(amb_e, amb_t)
if (S / 'replay_boq_r15.py').exists():
    tree = ast.parse((S / 'replay_boq_r15.py').read_text(encoding='utf-8'))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'classify')
    ns = {}; exec(compile(ast.Module(body=[fn], type_ignores=[]), 'replay_boq_r15.py', 'exec'), ns)
    pair_of = {ei: (ti, st) for ei, ti, st in amb['pairs']}
    replayed = {ei: ns['classify']({'accepted_by_reader': True, 'state': 'validated'}, None, pair_of.get(ei, (None, None))[1], None, None) for ei in ('a', 'b')}
    consumer = 'replay_boq_r15.classify with the r15 pair lookup'
else:
    spec = importlib.util.spec_from_file_location('rc', S / 'replay_core.py'); rc = importlib.util.module_from_spec(spec); spec.loader.exec_module(rc)
    ext = {'lines': [{'page': 1, 'y_px': x['y'], 'catalog_no': x['part_number'], 'description': x['description'], 'quantity': x['quantity']} for x in amb_e], 'issues': []}
    stored = [{'page': 1, 'row': {'part_number': x['part_number'], 'quantity': x['quantity'], 'description': x['description'], 'row_bounds': None, 'y_px': x['y']},
               'accepted_by_reader': True, 'state': 'validated'} for x in amb_e]
    res = rc.replay_sheet(stored, rc.build_emitted(ext), amb_t, bc)
    replayed = {x['id']: row['outcome'] for x, row in zip(amb_e, res['rows'])}
    consumer = 'replay_core.replay_sheet (the r16 reporting path)'
out = {'code': str(S), 'mixed_geometry': {'join': r, 'crossed_verified_anchor': bool(wrong), 'join_without_anchor_emitted': r_no_anchor,
                                          'crossed_without_anchor_emitted': bool(wrong_no_anchor), 'above_anchor_control': control},
       'geometry_ambiguity': {'join': amb, 'consumer': consumer, 'replay_outcomes': replayed}}
(R / 'ADDITIONAL-PROBES.json').write_text(json.dumps(out, indent=2) + '\n')
print(json.dumps({'crossed': out['mixed_geometry']['crossed_verified_anchor'], 'crossed_without_anchor': out['mixed_geometry']['crossed_without_anchor_emitted'],
                  'held_replay': replayed, 'consumer': consumer}, indent=1))
