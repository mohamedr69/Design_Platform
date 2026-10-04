"""Combine the submitted failure and kill devices on the actual unchanged runner.
Read only helper definitions from the adapted lifecycle probe; do not rerun its
top-level scenarios. All fixtures, labels and requests are synthetic/private.
"""
from pathlib import Path
import ast,json
R=Path(__file__).parent
s=(R/'lifecycle_probes_adapted.py').read_text()
# The helper prefix ends before any scenario dispatch.
prefix=s[:s.index('R = {"lifecycle_contract"')]
g={'__file__':str(R/'lifecycle_probes_adapted.py')}
exec(compile(prefix,str(R/'lifecycle_probes_adapted.py'),'exec'),g)
results={}
for point in ('before_file','after_file'):
 root,decl,dg=g['make_root']('provider-'+point,set())
 first=g['run'](root,decl,dg,[],env={'PILOT_DRY_FAIL_FROM':'1','PILOT_DRY_KILL_AT_STOP':point},name='failure-kill')
 before=g['snapshot'](root)
 io=root/'runs/L1/out/io.jsonl'
 entries=[json.loads(l) for l in io.read_text().splitlines()]
 logs=[e for x in entries for e in x['log'] if not e.get('cache_hit')]
 resume=g['run'](root,decl,dg,['--resume'],name='resume')
 after=g['snapshot'](root)
 results[point]={'initial_exit':first['exit'],'initial_recorded_sends':before['sends_total_recorded'],
  'initial_outcomes':[e.get('outcome') for e in logs],
  'stop_file_before_resume':before['stop_file'],'manifest_stop_before_resume':before['stopped'],
  'resume_exit':resume['exit'],'new_sends':after['sends_total_recorded']-before['sends_total_recorded'],
  'resume_status':after['status'],'resume_stop':after['stopped'],'stop_file_after_resume':after['stop_file']}
 (R/f'PROVIDER-{point}-BEFORE.json').write_text(json.dumps(before,indent=2))
 (R/f'PROVIDER-{point}-AFTER.json').write_text(json.dumps(after,indent=2))
(R/'PROVIDER-BOUNDARY-PROBE.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
