"""Legacy migration boundary: real prior merge -> candidate merge -> full evaluator, synthetic inputs only."""
import copy
import importlib.util
import json
import os
import sys
from pathlib import Path
sys.dont_write_bytecode=True
os.environ['AI_ENABLED']='false'
ROOT=Path('C:/t/iso/frozen-r12/backend')
sys.path.insert(0,str(ROOT))
from app.ai import evidence_reader as er
from scripts import m2_eval5 as ev
spec=importlib.util.spec_from_file_location('old_reader_probe',ROOT/'tests/fixtures/evidence_reader_r10.py')
old=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=old
spec.loader.exec_module(old)
OUT=Path('C:/t/iso/work/r12/probes/legacy_after')
SHA='c'*64
LABEL={'doc':'synthetic/legacy.pdf','ep':'test','cohort':'synthetic','stratum':'s','extension':'.pdf','scan_like':False,'confidence':'high'}
def obs(field,value,**kw):return dict(page=1,component='own',field=field,value=value,state='validated',**kw)
def add(module,ai,n,observations):
    return module.merge_evidence(copy.deepcopy(ai),{'attempt':n,'outcome':'complete','observations':observations,
        'coverage':{'pages':[{'page':1,'outcome':'evidence','fields':{f'own:{o["field"]}':'completed' for o in observations}}]}},
        sha256=SHA,profile='default',variant='EV1')
def summarize(ai,identity='X-SD-1',revision='03'):
    got=er.evidence_for(ai,sha256=SHA,profile='default',variant='EV1')
    doc={**LABEL,'labels':{'kind':'shop-drawing cover','reference':identity,'revision':revision,'decision':'approved as noted'}}
    row={'state':'fresh','sha256':SHA,'extracted':{'records':[],'profile':'default','coverage':{'outcome':'complete'},'ai_evidence':ai}}
    layer=ev.evaluate({'documents':[doc]},None,{LABEL['doc']:row},ai_context={'variant':'EV1'})['documents'][0]['layers']['ai']
    return {'selection':got,'judged':layer['judged'],'recovery':layer['components'][0]['fields'],
            'stored_fields':ai['envelopes']['default|EV1']['pages']['1']['fields']}

initial=add(old,None,1,[obs('identity','X-SD-1'),obs('revision','02',target='X-SD-1'),obs('decision','ANN',target='X-SD-1')])
other=add(old,initial,2,[obs('identity','X-SD-7'),obs('revision','02',target='X-SD-7')])
candidate=add(er,other,3,[obs('identity','X-SD-1'),obs('revision','03',target='X-SD-1')])
# Control: the unrelated revision carries a different literal, so it is not accidentally selected by value.
other_control=add(old,initial,2,[obs('identity','X-SD-7'),obs('revision','09',target='X-SD-7')])
candidate_control=add(er,other_control,3,[obs('identity','X-SD-1'),obs('revision','03',target='X-SD-1')])

# An identity field with unknown ordering must not become attempt zero when anchoring a numbered legacy fact.
missing=add(old,None,1,[obs('identity','X-SD-9'),obs('revision','02')])
missing['envelopes']['default|EV1']['pages']['1']['fields']['own:identity']['provenance']['attempt']=None
res={'same_revision_literal_different_targets':summarize(candidate),
     'different_literal_control':summarize(candidate_control),
     'missing_identity_order':summarize(missing,identity='X-SD-9',revision='02')}
(OUT/'legacy-anchor-probe-results.json').write_text(json.dumps(res,indent=2),encoding='utf-8')
print(json.dumps({k:{'recovery':v['recovery'],'judged':[(j['field'],j['value'],j['state'],j['outcome']) for j in v['judged']],
                    'anchors':{fk:entry.get('anchor') for fk,entry in v['stored_fields'].items()}} for k,v in res.items()},indent=2))
