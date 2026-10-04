from pathlib import Path
import os,json,hashlib,copy,sys
os.environ['AI_ENABLED']='false'
R=Path('C:\\t\\iso\\work\\r2x\\review22\\repro\\on-r21')
P=Path('C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review21')
sys.path.insert(0,'C:/t/iso/work/r2x/review22/harness-r21')
import coverage_v3 as cv
import score_arms_v3 as scorer
original=P/'dry/R21-DECLARATION.dry.json'
d=json.loads(original.read_text())
args=['--runs','C:/t/r2x/dry-runs','--tags','A=r21dry-A,L1=r21dry-L1,L2=r21dry-L2,L3=r21dry-L3,L4=r21dry-L4']
base=scorer.main(['--declaration',str(original),'--declaration-sha',hashlib.sha256(original.read_bytes()).hexdigest(),*args,'--out',str(R/'score-control')])
for doc in d['sources']['sample']['documents_planned']:
 doc['sha256']='f'*64
modified=R/'SOURCE-MISMATCH-DECLARATION.json'
modified.write_text(json.dumps(d,indent=2))
changed=scorer.main(['--declaration',str(modified),'--declaration-sha',hashlib.sha256(modified.read_bytes()).hexdigest(),*args,'--out',str(R/'score-mismatch')])
ctx={'profile':'default','variant':'EV1','policy':'P'}
plan={'doc':'one-page','pages':1,'sha256':'a'*64,'extension':'.pdf'}
def row(page,policy='P'):
 return {'sha256':'a'*64,'extracted':{'ai_evidence':{'envelopes':{'default|EV1':{'profile':'default','variant':'EV1','pages':{str(page):{'fields':{'own:identity':{'observations':[{'value':'X-3','field':'identity','state':'validated','policy':policy}]}}}}}}}}}
extra={str(p):cv.extra_facts(row(p),plan,ctx,max_pages=4) for p in (1,3,5)}
result={'source_mismatch':{arm:{'coverage':changed['coverage'][arm]['summary']['binding_reasons'],'baseline_accuracy':base['arms'][arm]['recovery_all_planned'],'mismatch_accuracy':changed['arms'][arm]['recovery_all_planned'],'unchanged':base['arms'][arm]['recovery_all_planned']==changed['arms'][arm]['recovery_all_planned']} for arm in ('L1','L2','L3','L4')},'extra_facts_one_page_document':extra}
(R/'INDEPENDENT-PROBES.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
