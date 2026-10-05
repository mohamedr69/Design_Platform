import os,sys,json,ast
from pathlib import Path
os.environ['AI_ENABLED']='false'
os.environ['AI_EVIDENCE_GUARD']='1'
os.environ['AI_EVIDENCE_TARGETED']='1'
os.environ['AI_EVIDENCE_EFFICIENT']='1'
sys.path.insert(0,'C:/t/iso/cand-ai2/backend')
import pymupdf as fitz
from app.ai import evidence_reader as er
R=Path(__file__).parent
PKG=Path('C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-pilot-r18-correction')
class Run:
 profile='default';variant='EV1';escalations=0;exhausted=None
 def __init__(self,answer):self.answer=answer;self.log=[];self.requests=[]
 def call(self,**kw):
  self.requests.append(kw['task']);self.log.append({'outcome':'ok'})
  return self.answer if kw['task'].startswith('discover') else {'value':'X-SD-1','legible':True,'label_text':'Drawing No'}
def sheet(stamp):
 d=fitz.open();p=d.new_page(width=1684,height=1190)
 for i,t in enumerate(['PROJECT EXAMPLE TOWER','CLIENT EXAMPLE COMPANY','SCALE 1:100','DRAWN AB ENGINEER','CHECKED CD ENGINEER','DRAWING NO X-SD-1']):
  p.insert_text((1300,1000+i*20),t,fontsize=9)
 if stamp:
  q=fitz.open();z=q.new_page(width=300,height=80);z.insert_text((10,25),'CONSULTANT - CODE B',fontsize=14);z.insert_text((10,50),'APPROVED AS NOTED',fontsize=14)
  p.insert_image(fitz.Rect(100,100,700,260),stream=z.get_pixmap().tobytes('png'))
 return d,p
results={}
for stamp in (False,True):
 doc,p=sheet(stamp);clip,route=er.locate_title_block(p,ocr_timeout=0)
 box=er._norm_to_page(p,clip,[0,0,1000,1000])
 answer={'page_kind':'drawing_sheet','own_identity':'X-SD-1','own_identity_region':[0,0,1000,1000],'own_revision':'','own_revision_region':[],'decision_options_printed':[],'other_numbers':[]}
 run=Run(answer);out=er._read_page(run,p,sha256='a'*64,number=1,facts=er.PageFacts(1,p.get_text(),[],[]),reason='review19')
 results['raster_stamp' if stamp else 'text_only_control']={'text_length':len(p.get_text()),'clip':list(clip),'stamp_outside':not clip.intersects(fitz.Rect(100,100,700,260)),'outcome':out['_outcome'],'fields':out['_fields'],'requests':run.requests}
 if stamp:
  doc.save(R/'SYNTHETIC-RASTER-STAMP.pdf');p.get_pixmap(matrix=fitz.Matrix(.7,.7)).save(R/'SYNTHETIC-RASTER-STAMP.png')
# Verify actual crop response mapping / support at all PDF rotations; real locator, no shim.
rot=[]
for angle in (0,90,180,270):
 d=fitz.open();p=d.new_page(width=1684,height=1190);p.set_rotation(angle)
 # put the six horizontal text runs in displayed title block coordinates, using inverse rotation
 for i,t in enumerate(['PROJECT EXAMPLE TOWER','CLIENT EXAMPLE','SCALE 1:100','DRAWN AB','CHECKED CD','DRAWING NO X-SD-1']):
  loc=fitz.Point(p.rect.width*.8,p.rect.height*.8+20*i)*p.derotation_matrix
  p.insert_text(loc,t,fontsize=8,rotate=angle)
 clip,route=er.locate_title_block(p,ocr_timeout=0)
 words=[w for w in p.get_text('words') if w[4]=='X-SD-1'];rect=fitz.Rect(words[0][:4])*p.rotation_matrix
 b=[(rect.x0-clip.x0)/clip.width*1000,(rect.y0-clip.y0)/clip.height*1000,(rect.x1-clip.x0)/clip.width*1000,(rect.y1-clip.y0)/clip.height*1000]
 normalized=er._norm_to_page(p,clip,b)
 restored=er.region_from_norm(p,normalized)
 texts=er.region_texts_v2(p,restored,[],ocr_timeout=0)
 rot.append({'rotation':angle,'route':route,'contains':clip.contains(rect),'source_supported':any('X-SD-1' in s for _,s in texts)})
results['actual_locator_rotation_controls']=rot
# Replay exact submitted stop_of with successful request but incomplete field.
src=ast.parse((PKG/'scripts/score_cont.py').read_text())
f=next(n for n in src.body if isinstance(n,ast.FunctionDef) and n.name=='stop_of');ns={};exec(compile(ast.Module(body=[f],type_ignores=[]),'submitted-stop-of','exec'),ns)
att={'calls':[{'outcome':'ok'}],'pages':{'1':{'outcome':'partial','fields':{'own:identity':'incomplete:no_region'}}}}
results['transport_only_completion']={'result':ns['stop_of'](att),'input':att}
m=json.loads((PKG/'results/CONT-METRICS.json').read_text())
results['matched_with_incomplete_fields']={d:m['coverage_planned'][d] for d in m['matched_completed'] if any(str(v).startswith(('incomplete','unusable','not_attempted')) for arm in ('S','T2') for fs in m['coverage_planned'][d][arm]['fields'].values() for k,v in fs.items() if k in ('own:identity','own:revision','own:decision'))}
(R/'INDEPENDENT-E-PROBES.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
