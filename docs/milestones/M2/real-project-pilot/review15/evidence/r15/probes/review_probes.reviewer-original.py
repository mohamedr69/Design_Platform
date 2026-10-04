"""Independent offline probes. Submitted modules unchanged; no application startup or provider."""
import ast
import copy
from dataclasses import dataclass, field
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

sys.dont_write_bytecode=True
ROOT=Path(__file__).parent
PKG=Path('C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review14')
CODE=PKG/'evidence/r14'

def module(name):
    spec=importlib.util.spec_from_file_location('review_'+name,CODE/(name+'.py'))
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m
bh=module('boq_harness')
bc=module('boq_contract')
ov=module('overlay')

# Compile the unchanged actual budget classes only; omit application/database/settings imports.
budget_path=Path('C:/t/iso/frozen-r12/backend/app/ai/budget.py')
tree=ast.parse(budget_path.read_text(encoding='utf-8-sig'))
classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name in ('Limits','JobBudget','BudgetExceeded')]
ns={'dataclass':dataclass,'field':field,'threading':threading,'time':time,'__name__':__name__}
exec(compile(ast.Module(body=classes,type_ignores=[]),str(budget_path),'exec'),ns)
Limits,JobBudget,BudgetExceeded=[ns[k] for k in ('Limits','JobBudget','BudgetExceeded')]

def open_budget(db,project):
    return JobBudget(Limits(1000,1000,12,60,0,120,2,0,0,0),0)

class DB:
    def commit(self): pass

class ScriptedER:
    def __init__(self,log,crash=False): self.log=Path(log); self.crash=crash; self.sent=0
    def boq_rows_to_verify(self,lines,issues,**kw): return [(l,None) for l in lines]
    def verify_boq_rows(self,run,pdf,*,extraction,**kw):
        result=[]
        for row in extraction['lines']:
            try: run.budget.reserve(1,1)
            except BudgetExceeded as e:
                run.exhausted=e.limit
                result.append({'state':'budget_refused'})
                continue
            self.sent+=1
            with self.log.open('a',encoding='utf-8') as f:
                f.write('scripted_provider_request\n'); f.flush(); os.fsync(f.fileno())
            if self.crash and self.sent==5:
                os._exit(91)  # Stop inside first chunk, before verify_sheet can persist that chunk.
            result.append({'state':'read'})
        return result

def run_sheet(folder,crash=False):
    er=ScriptedER(folder/'provider-log.txt',crash)
    run=SimpleNamespace(exhausted=None,budget=None)
    _,info=bh.verify_sheet(er,run,None,db=DB(),open_budget=open_budget,
        allowance=bh.DocAllowance(str(folder/'allowance.sqlite')),scope='frozen-scope',profile='EV2',
        lines=[{'id':i} for i in range(25)],issues=[],variant='EV2',sha256='same-document-sha',
        max_calls_per_document=12,render_dpi=150)
    return {'sent':er.sent,**info}

if len(sys.argv)>1 and sys.argv[1]=='--crash-child':
    run_sheet(Path(sys.argv[2]),True)
    raise SystemExit('child did not stop')

ROOT.mkdir(parents=True,exist_ok=True)
temp=Path(tempfile.mkdtemp(prefix='probe-',dir=ROOT))
crash=temp/'crash'; crash.mkdir()
child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--crash-child',str(crash)],capture_output=True,text=True)
assert child.returncode==91,(child.returncode,child.stderr)
state=bh.DocAllowance(str(crash/'allowance.sqlite')).load('frozen-scope','EV2','same-document-sha')
resumed=run_sheet(crash)
normal=temp/'normal'; normal.mkdir()
first,second=run_sheet(normal),run_sheet(normal)
budget={'actual_job_budget_classes_used':str(budget_path),'child_exit':child.returncode,
        'persisted_calls_after_crash':state['calls'],'calls_before_crash':5,'resume':resumed,
        'total_scripted_provider_calls':len((crash/'provider-log.txt').read_text().splitlines()),
        'expected_max_total':12,'clean_completion_control':[first,second]}

truth=[{'ordinal':6,'page':1,'part_number':'PRS-CSNKP','quantity':'1','description':'Numeric Keypad'},
       {'ordinal':37,'page':1,'part_number':'PRS-CSNKP','quantity':'2','description':'Numeric Keypad'}]
first_row={'id':'first-physical-row','page':1,'y':980.5,'part_number':'PRS-CSNKP','quantity':'2','description':'Numeric Keypad'}
join_wrong=bc.join_rows([first_row],truth)
unknown=copy.deepcopy(first_row); unknown['quantity']='?'
join_unknown=bc.join_rows([unknown],truth)
join_controls=bc.join_rows([first_row,{**first_row,'id':'second-physical-row','y':2718.5}],truth)

def case(value='00',literal='00',target='COVER-1',field='revision'):
    fact={'page':2,'field':field,'value':value,'state':'validated','reader':'ai:EV1','group':'ai:2:own'}
    result={'documents':[{'doc':'D','layers':{'evidence':{'judged':[fact],'critical':[fact]}}}]}
    labels={'documents':{'D':{'supported_observations':{'2':[{'field':field,'literal':literal,'role':'revision',
                                                            'association_target':'COVER-1','association_state':'proposal_only'}]}}}}
    envelope={'sha256':'CURRENT','pages':{'2':{'fields':{'own:'+field:{'observations':[{'field':field,'value':value,'target':target}],
                                                                       'anchor':{'identity':None}}}}}}
    rows={'D':{'extracted':{'ai_evidence':{'envelopes':{'default|EV1':envelope}}}}}
    return result,labels,rows

r,l,rows=case()
proposal=ov.overlay(r,l,rows)
r,l,rows=case(target=None)
other=copy.deepcopy(rows['D']['extracted']['ai_evidence']['envelopes']['default|EV1'])
other['sha256']='OLD-CONTENT'
other['pages']['2']['fields']['own:revision']['observations'][0]['target']='COVER-1'
active=rows['D']['extracted']['ai_evidence']['envelopes']['default|EV1']
rows['D']['extracted']['ai_evidence']['envelopes']={'promoted|EV2':other,'default|EV1':active}
foreign_first=ov.overlay(r,l,rows)
rows['D']['extracted']['ai_evidence']['envelopes']={'default|EV1':active,'promoted|EV2':other}
active_first=ov.overlay(r,l,rows)
r,l,rows=case(value='1.0',literal='10')
revision_collision=ov.overlay(r,l,rows)
r,l,rows=case(target=None)
no_target_control=ov.overlay(r,l,rows)

results={'budget':budget,'row_join':{'single_misread_duplicate':join_wrong,'same_row_unreadable_quantity':join_unknown,
    'two_row_control':join_controls,'expected':'A quantity being evaluated must not select a different physical truth row; without verified source alignment, hold the sparse duplicate.'},
    'overlay':{'accepted_target_equals_unapproved_proposal':proposal,'wrong_context_inserted_first':foreign_first,
               'active_context_inserted_first':active_first,'revision_1_dot_0_vs_10':revision_collision,
               'no_target_control':no_target_control}}
(ROOT/'PROBE-RESULTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
