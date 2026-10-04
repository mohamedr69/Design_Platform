"""Synthetic repeat-read sequences through candidate merge, selection and full evaluator. No providers/documents."""
import copy
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode=True
os.environ['AI_ENABLED']='false'
ROOT=Path('C:/t/iso/frozen-r11/backend')
sys.path.insert(0,str(ROOT))
from app.ai import evidence_reader as er
from scripts import m2_eval5 as ev
OUT=Path('C:/t/iso/work/r11/probes/after')
SHA='b'*64
LABEL={'doc':'synthetic/repeated.pdf','ep':'test','cohort':'synthetic','stratum':'s','extension':'.pdf','scan_like':False,'confidence':'high'}

def obs(field,value,**kw):
    return dict(page=1,component='own',field=field,value=value,state='validated',**kw)

def add(ai,observations,number=None):
    # Exact allocation expression in evidence_stage, not a novel numbering convention.
    n=len(er._normalise_ai(ai)['attempts'])+1 if number is None else number
    attempt={'attempt':n,'outcome':'complete','observations':observations,
             'coverage':{'pages':[{'page':1,'outcome':'evidence','fields':{f'own:{o["field"]}':'completed' for o in observations}}]}}
    return er.merge_evidence(copy.deepcopy(ai),attempt,sha256=SHA,profile='default',variant='EV1')

def summarize(ai,identity,revision,field):
    selected=er.evidence_for(ai,sha256=SHA,profile='default',variant='EV1')
    fact=next(o for o in selected['observations'] if o['field']==field)
    doc={**LABEL,'labels':{'kind':'shop-drawing cover','reference':identity,'revision':revision,'decision':'approved as noted'}}
    row={'state':'fresh','sha256':SHA,'extracted':{'records':[],'profile':'default','coverage':{'outcome':'complete'},'ai_evidence':ai}}
    layer=ev.evaluate({'documents':[doc]},None,{LABEL['doc']:row},ai_context={'variant':'EV1'})['documents'][0]['layers']['ai']
    return {'last_attempt_number':ai['attempts'][-1]['attempt'],'fact_attempt':fact['provenance']['attempt'],
            'association':fact.get('association'),'judged':[j for j in layer['judged'] if j['field']==field],
            'recovery':layer['components'][0]['fields'][field]}

# Before reader .4, decisions had target identity but no target_revision. Their paired revision was recorded.
base=add(None,[obs('identity','X-SD-1'),obs('revision','02',target='X-SD-1'),obs('decision','ANN',target='X-SD-1')])
timeline=[]
ai=base
for actual in range(2,8):
    ai=add(ai,[obs('revision','03',target='X-SD-1')])
    timeline.append({'actual_read':actual,**summarize(ai,'X-SD-1','03','decision')})

# Control: explicit decision revision survives pruning.
control=add(None,[obs('identity','X-SD-1'),obs('revision','02',target='X-SD-1'),obs('decision','ANN',target='X-SD-1',target_revision='02')])
for _ in range(6):control=add(control,[obs('revision','03',target='X-SD-1')])

# Legacy targetless revision at stored attempt 13; stage numbering repeats 13 after the 12-entry cap.
ai=None
for _ in range(13):ai=add(ai,[obs('identity','X-SD-1'),obs('revision','02')])
collision=[]
for actual in range(14,21):
    ai=add(ai,[obs('identity','X-SD-9')])
    collision.append({'actual_read':actual,**summarize(ai,'X-SD-9','02','revision')})

result={'revision_history_pruning':timeline,'explicit_revision_control':summarize(control,'X-SD-1','03','decision'),
        'attempt_number_collision':collision,'bounds':{'attempts':er.MAX_ATTEMPTS_KEPT,'field_history':er.MAX_FIELD_HISTORY}}
(OUT/'retention-probe-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:[{'actual_read':r['actual_read'],'stored_attempt':r['last_attempt_number'],
                    'association':r['association']['status'],'recovery':r['recovery']} for r in result[k]]
                  for k in ('revision_history_pruning','attempt_number_collision')},indent=2))
print('Explicit revision control:',result['explicit_revision_control']['association']['status'],result['explicit_revision_control']['recovery'])
