"""Actual submitted runner, scripted provider, private sandbox: a critical stop must survive --resume.
Only synthetic label copies intentionally disagree to trigger the real tripwire.
No application or submitted file is edited; no original document or model is used.
"""
from pathlib import Path
import os,json,hashlib,shutil,subprocess,sys

R=Path('C:\\t\\iso\\work\\r2x\\review23\\repro\\on-v4')
W=Path(json.loads((R/'WORKSPACE.json').read_text())['workspace'])/'critical-stop'
P=Path('C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review22')
W.mkdir()
(W/'labels').mkdir()
d=json.loads((P/'dry/R22-DECLARATION.dry.json').read_text())
label_home=Path(d['harness_dir'])/d['labels']['dir']
def changed(value):
    if isinstance(value,dict):
        return {k:changed(v) for k,v in value.items()}
    if isinstance(value,list):
        return [changed(v) for v in value]
    return value.replace('X-DRY-1','X-DRY-9') if isinstance(value,str) else value
for name in d['labels']['files']:
    payload=json.loads((label_home/name).read_text())
    if name in (d['labels']['register'],d['labels']['page']):
        payload=changed(payload)
    target=W/'labels'/name
    target.write_text(json.dumps(payload))
    d['labels']['files'][name]=hashlib.sha256(target.read_bytes()).hexdigest()
d['harness_dir']=W.as_posix()
d['labels']['dir']='labels'
decl=W/'DECLARATION.json'
decl.write_text(json.dumps(d,indent=2))
digest=hashlib.sha256(decl.read_bytes()).hexdigest()
(W/'runs').mkdir()
shutil.copytree('C:/t/r2x/dry-runs/r22/runs/r22dry-A',W/'runs/r22dry-A')
a_file=W/'runs/r22dry-A/out/RUN.json'
a=json.loads(a_file.read_text());a['declaration_sha256']=digest;a_file.write_text(json.dumps(a))
env={**os.environ,'PILOT_DRY':'1','PILOT_DRY_MODE':'coherent','PILOT_DRY_ROOT':W.as_posix(),
     'PYTHONDONTWRITEBYTECODE':'1','PYTHONIOENCODING':'utf-8','TEMP':str(W),'TMP':str(W),
     'GIT_CONFIG_COUNT':'1','GIT_CONFIG_KEY_0':'safe.directory','GIT_CONFIG_VALUE_0':'C:/t/iso/cand-ai4'}
for k in ('PILOT_DRY_KILL_AFTER','PILOT_DRY_LATENCY_S','PILOT_DRY_NEW_TAG_OVERRIDE','XTRACK_FAKE_NOW'):
    env.pop(k,None)
cmd=[sys.executable,str(Path('C:/t/iso/work/r2x/review22/harness-v4')/'arm_ev.py'),'r22dry-A','L1','L1','--declaration',str(decl),'--declaration-sha',digest]
out={}
for label,extra in [('initial',[]),('resume',['--resume'])]:
    with (R/f'CRITICAL-STOP-{label}.log').open('w') as log:
        proc=subprocess.run(cmd+extra,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=180)
    result_path=W/'runs/L1/out/RUN.json'
    if not result_path.exists():
        raise RuntimeError((R/f'CRITICAL-STOP-{label}.log').read_text())
    m=json.loads(result_path.read_text())
    (R/f'CRITICAL-STOP-{label}.json').write_text(json.dumps(m,indent=2))
    out[label]={'exit':proc.returncode,'status':m.get('status'),'stopped':m['runner_state']['stopped'],
                'requests_this_invocation':m['runner_state']['per_ep'],'projects':list(m['projects']),
                'tripwire_errors':[len(t['critical_on_resolved']) for t in m['tripwire']],
                'not_attempted':m['not_attempted']}
(R/'CRITICAL-STOP-PROBE.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
