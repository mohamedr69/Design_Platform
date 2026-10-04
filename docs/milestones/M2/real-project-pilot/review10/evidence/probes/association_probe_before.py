"""No source documents or providers: synthetic evidence through real merge, selection and evaluator."""
import copy
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
os.environ['AI_ENABLED']='false'
ROOT=Path('C:/t/iso/frozen-r9/backend')
sys.path.insert(0,str(ROOT))
from app.ai import evidence_reader as er
from scripts import m2_eval5 as ev

SHA='a'*64
OUT=Path('C:/t/iso/work/r10/probes/before')
LABEL={'doc':'synthetic/form.pdf','ep':'test','cohort':'synthetic','stratum':'s','extension':'.pdf','scan_like':False,'confidence':'high'}
def obs(field,value,**kwargs):
    return dict(page=1,component='own',field=field,value=value,state='validated',**kwargs)
def merge(previous,observations,n):
    return er.merge_evidence(copy.deepcopy(previous), {'attempt':n,'outcome':'complete','observations':observations,
        'coverage':{'pages':[{'page':1,'outcome':'evidence','fields':{f'own:{o["field"]}':'completed' for o in observations}}]}},
        sha256=SHA,profile='default',variant='EV1')
def score(ai,ref,rev='00'):
    doc={**LABEL,'labels':{'kind':'shop-drawing cover','reference':ref,'revision':rev,'decision':'approved as noted'}}
    row={'state':'fresh','sha256':SHA,'extracted':{'records':[],'profile':'default','coverage':{'outcome':'complete'},'ai_evidence':ai}}
    result=ev.evaluate({'documents':[doc]},None,{LABEL['doc']:row},ai_context={'variant':'EV1'})
    got=er.evidence_for(ai,sha256=SHA,profile='default',variant='EV1')
    layer=result['documents'][0]['layers']['ai']
    return {'selected':got,'judged_decisions':[j for j in layer['judged'] if j['field']=='decision'],
            'components':layer['components']}

# Review 07 page-envelope schema: profile and bytes known, revision/decision target absent.
legacy_obs=[obs('identity','X-SD-1'),obs('decision','ANN')]
legacy={'envelopes':{'default|EV1':{'profile':'default','variant':'EV1','read_sha256':SHA,
    'pages':{'1':{'observations':legacy_obs,'provenance':{'attempt':1,'read_sha256':SHA,'profile':'default','variant':'EV1'}}},
    'observations':legacy_obs}},'current_key':'default|EV1','attempts':[]}
out={
    'legacy_unchanged_control':score(legacy,'X-SD-1'),
    'legacy_changed_identity':score(merge(legacy,[obs('identity','X-SD-9')],2),'X-SD-9'),
}
explicit=merge(None,[obs('identity','X-SD-1'),obs('decision','ANN',target='X-SD-1')],1)
out['recorded_target_control']=score(merge(explicit,[obs('identity','X-SD-9')],2),'X-SD-9')

# Review 08 actually recorded revisions without targets, with a known profile and source hash.
# This is a supported historical shape, not an invented decision provenance.
legacy_revision=merge(None,[obs('identity','X-SD-1'),obs('revision','02')],1)
revised=merge(legacy_revision,[obs('identity','X-SD-9')],2)
revision_label={**LABEL,'labels':{'kind':'shop-drawing cover','reference':'X-SD-9','revision':'02','decision':'approved as noted'}}
revision_row={'state':'fresh','sha256':SHA,'extracted':{'records':[],'profile':'default','coverage':{'outcome':'complete'},'ai_evidence':revised}}
revision_layer=ev.evaluate({'documents':[revision_label]},None,{LABEL['doc']:revision_row},ai_context={'variant':'EV1'})['documents'][0]['layers']['ai']
out['review08_revision_without_target']={'judged_revisions':[j for j in revision_layer['judged'] if j['field']=='revision'],
    'components':revision_layer['components'], 'selected':er.evidence_for(revised,sha256=SHA,profile='default',variant='EV1')}

# Same target identity, explicit prior revision, no usable AI identity after this attempt.
revision_base=merge(None,[obs('revision','02',target='X-SD-1'),obs('decision','ANN',target='X-SD-1',target_revision='02')],1)
out['known_revision_without_identity']=score(merge(revision_base,[obs('revision','03',target='X-SD-1')],2),'X-SD-1','03')

(OUT/'association-probe-results.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:{**{key:val for key,val in v.items() if key.startswith('judged_')},'components':v['components']} for k,v in out.items()},indent=2))
