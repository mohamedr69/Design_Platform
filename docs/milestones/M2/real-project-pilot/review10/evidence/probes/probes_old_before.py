"""Independent pure-function probes; no application imports, provider calls or live data writes."""
import ast
import copy
import json
import re
from pathlib import Path
from types import SimpleNamespace

ROOT = Path('C:/t/iso/frozen-r9/backend')
OUT = Path('C:/t/iso/work/r10/probes/old_before')
src = ROOT / 'app/ai/evidence_reader.py'
tree = ast.parse(src.read_text(encoding='utf-8'))
nodes = [n for n in tree.body if isinstance(n, (ast.Assign, ast.FunctionDef))]
g = {'re': re}
exec(compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body + nodes, type_ignores=[])), str(src), 'exec'), g)
g.update(TextPart=lambda *a:a, ImagePart=lambda *a:a, page_png=lambda p:b'', crop_png=lambda *a,**k:b'',
         _det_region=lambda *a:None, region_from_norm=lambda *a:(0,0,10,10), region_texts=lambda *a:[('text','X-SD-1 X-SD-9')])

def attempt(n, obs, fields, outcome='evidence'):
    return dict(attempt=n, version='reader-test', policy='policy-test', observations=obs, outcome='complete',
                coverage={'pages':[dict(page=1,outcome=outcome,fields=fields)]})

def merge(previous, att):
    return g['merge_evidence'](copy.deepcopy(previous), att, sha256='same',profile='default',variant='EV1')

def selected(ai, **extra):
    return g['evidence_for'](ai,sha256='same',profile='default',variant='EV1',**extra)

old = [dict(page=1,component='own',field='identity',value='X-SD-1',state='validated'),
       dict(page=1,component='own',field='decision',value='ANN',target='X-SD-1',state='validated')]
base = merge(None,attempt(1,old,{'own:identity':'completed','own:decision':'completed'}))

def page(answers):
    answers = iter(answers)
    log=[]
    def call(**kw):
        answer=next(answers)
        log.append({'outcome':'ok' if answer is not None else 'timeout'})
        return answer
    run=SimpleNamespace(call=call,variant='EV1',profile='default',escalations=0,exhausted=None,log=log)
    return g['_read_page'](run,None,sha256='same',number=1,facts=SimpleNamespace(identities=[],revisions=[],records=[]),reason='probe')

def apply_page(found):
    ai=merge(base,attempt(2,found['_observations'],found['_fields'],found['_outcome']))
    return {'page_outcome':found['_outcome'],'field_outcomes':found['_fields'],
            'selected':selected(ai),'stored':ai}

results={}
results['timeout_control']=apply_page(page([{'own_identity':'X-SD-9','own_identity_region':[1,1,9,9]},None]))
results['illegible_identity']=apply_page(page([{'own_identity':'X-SD-9','own_identity_region':[1,1,9,9]},
                                              {'value':'','legible':False}]))
results['illegible_negative_decision']=apply_page(page([
    {'decision_options_printed':['A = APPROVED','B = APPROVED AS NOTED'],'decision_marked_option':'',
     'decision_mark_type':'none','decision_actor':'consultant','decision_region':[1,1,9,9]},
    {'options_printed':[],'marked_option':'','mark_type':'unclear','actor':'unknown','legible':False}]))
results['changed_identity_retained_decision']=apply_page(page([{'own_identity':'X-SD-9','own_identity_region':[1,1,9,9]},
                                                              {'value':'X-SD-9','legible':True}]))
unknown=copy.deepcopy(base)
unknown['envelopes']['default|EV1']['read_sha256']=None
for field in unknown['envelopes']['default|EV1']['pages']['1']['fields'].values():
    field['provenance']['read_sha256']=None
results['missing_source_hash']=selected(unknown)
results['wrong_profile_control']=g['evidence_for'](base,sha256='same',profile='promoted',variant='EV1')
results['heading']={
    'part_control':g['validate_boq_row']({'part_number':'P-1','quantity':None},{'row_is_heading':True,'legible':True}),
    'source_description_count':g['validate_boq_row']({'part_number':None,'quantity':None,'description':'( 2 ) Dual Input Module'},
                                                   {'row_is_heading':True,'legible':True,'description':'Dual Input Module'}),
    'numeric_zero':g['validate_boq_row']({'part_number':None,'quantity':0},{'row_is_heading':True,'legible':True}),
    'string_zero':g['validate_boq_row']({'part_number':None,'quantity':'0'},{'row_is_heading':True,'legible':True})}

# The real evaluator grouping body, with pure data helper functions, exposes target loss.
esrc=ROOT/'scripts/m2_eval5.py'
etree=ast.parse(esrc.read_text(encoding='utf-8'))
import collections
eg={'collections':collections,'ev4':SimpleNamespace(_obs_page=lambda o:o.get('page',1))}
for name in ['_fact','_group','ai_groups']:
    node=next(n for n in etree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.fix_missing_locations(ast.Module(body=ast.parse('from __future__ import annotations').body+[node],type_ignores=[])),str(esrc),'exec'),eg)
eg['ai_envelope']=lambda row,ctx,doc=None:(results['changed_identity_retained_decision']['selected']['envelope'],'current')
results['changed_identity_evaluator_groups']=eg['ai_groups']({}, {})
(OUT/'probe-results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print(json.dumps({
    'timeout_identity':[o.get('value') for o in results['timeout_control']['selected']['observations'] if o['field']=='identity'],
    'illegible_identity':[(o['field'],o.get('value'),o['state']) for o in results['illegible_identity']['selected']['observations']],
    'illegible_decision':[(o['field'],o.get('value'),o['state']) for o in results['illegible_negative_decision']['selected']['observations']],
    'missing_hash_state':results['missing_source_hash']['state'],
    'wrong_profile_state':results['wrong_profile_control']['state'],
    'heading':results['heading'],
    'grouped_changed_identity':results['changed_identity_evaluator_groups']},indent=2))
