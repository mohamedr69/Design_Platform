from pathlib import Path
import json,os,sys
os.environ['AI_EVIDENCE_GUARD']='1';os.environ['AI_EVIDENCE_TARGETED']='1'
sys.path.insert(0,'C:/t/iso/cand-ai/backend')
import pymupdf
from app.ai import evidence_reader as er
R=Path(__file__).parent
class Run:
 profile='default';escalations=0;exhausted=None
 def __init__(self,variant,answers):self.variant=variant;self.answers=answers;self.log=[];self.requests=[]
 def call(self,**kw):
  key=(kw['task'],kw.get('tier','small'));self.requests.append(key)
  a=self.answers[key];a=a.pop(0) if isinstance(a,list) else a
  self.log.append({'outcome':'timeout' if a is None else 'ok'})
  return a

def go(mode):
 doc=pymupdf.open();p=doc.new_page(width=1684,height=1190);p.insert_text((1300,1100),'Drawing No X-SD-1 X-SD-2',fontsize=9)
 d={'page_kind':'drawing_sheet','own_identity':'X-SD-1','own_identity_region':[760,900,900,950], 'own_revision':'','own_revision_region':[], 'decision_options_printed':[], 'other_numbers':[]}
 answers={('discover_page','small'):d,('read_identity','small'):{'value':'' if mode in ('rescue','empty') else 'X-SD-2','legible':mode!='rescue'},('read_identity','standard'):None,('read_field_context','small'):{'value':'X-SD-1','legible':True,'role':'own_identity','printed_label':'Drawing No','region':[0,0,1000,1000]}}
 if mode=='primary_timeout':answers[('read_identity','small')]=None
 run=Run('EV2' if mode=='escalation' else 'EV1',answers)
 out=er._read_page(run,p,sha256='a'*64,number=1,facts=er.PageFacts(1,p.get_text(),[],[]),reason='independent_probe')
 obs=next(o for o in out['_observations'] if o.get('field')=='identity' and o.get('component')=='own')
 return {'requests':run.requests,'outcome':out['_outcome'],'fields':out['_fields'],'request_outcomes':out['_requests'],'identity':obs}
result={'targeted_rescue_after_illegible_blind':go('rescue'),'targeted_after_failed_escalation':go('escalation'),'targeted_rescue_after_empty_blind':go('empty'),'primary_timeout_control':go('primary_timeout')}
(R/'TARGETED-PROBES.json').write_text(json.dumps(result,indent=2)+'\n')
for k,v in result.items():print(k,json.dumps({'requests':v['requests'],'fields':v['fields'],'state':v['identity']['state'],'read':v['identity']['read']}))
