"""Independent semantic-corruption probes, actual unchanged v4.2 runner.
Only private synthetic fixture journals are altered; no real request or source.
"""
from pathlib import Path
import json,os,hashlib,sqlite3
R=Path(__file__).parent
s=(R/'lifecycle_probes_adapted.py').read_text()
g={'__file__':str(R/'lifecycle_probes_adapted.py')}
exec(compile(s[:s.index('R = {"lifecycle_contract"')],str(R/'lifecycle_probes_adapted.py'),'exec'),g)
import provider_journal as pj
out={}
for kind in ('budget','cache_hit','none'):
 root,decl,dg=g['make_root']('neutral-'+kind,set())
 first=g['run'](root,decl,dg,[],env={'PILOT_DRY_FAIL_FROM':'1','PILOT_DRY_KILL_AT_STOP':'before_file'},name='failure-kill')
 before=g['snapshot'](root)
 jf=root/'runs/L1/out/PROVIDER-OUTCOMES.jsonl'
 original=jf.read_bytes()
 records=[json.loads(l) for l in original.decode().splitlines()]
 assert first['exit']==98 and [x['outcome'] for x in records if x['type']=='result']==['transport']*3
 assert before['stop_file'] is None
 original_info=pj.load(jf,records[0]['binding'],planned_sha256={x['sha256'] for x in records if x['type']=='attempt'})
 old=records[-1].copy()
 assert old['type']=='result' and old['kind']=='failure'
 records[-1]['kind']=kind
 jf.write_text(''.join(json.dumps(x,sort_keys=True)+'\n' for x in records),encoding='utf-8')
 info=pj.load(jf,records[0]['binding'],planned_sha256={x['sha256'] for x in records if x['type']=='attempt'})
 (R/f'NEUTRAL-{kind}-JOURNAL-BEFORE.jsonl').write_bytes(original)
 (R/f'NEUTRAL-{kind}-JOURNAL-MUTATED.jsonl').write_bytes(jf.read_bytes())
 resumed=g['run'](root,decl,dg,['--resume'],name='resume')
 after=g['snapshot'](root)
 out[kind]={'initial_exit':first['exit'],'initial_sends':before['sends_total_recorded'],'original_load':original_info,
  'alteration':{'from':old,'to':records[-1]},'load_before_resume':info,'resume_exit':resumed['exit'],
  'new_sends':after['sends_total_recorded']-before['sends_total_recorded'],'status':after['status'],
  'stop':after['stop_file'],'sandbox':str(root)}
 (R/'NEUTRAL-KIND-PROBE.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
 print(kind,{k:out[kind][k] for k in ('resume_exit','new_sends','status')},flush=True)
