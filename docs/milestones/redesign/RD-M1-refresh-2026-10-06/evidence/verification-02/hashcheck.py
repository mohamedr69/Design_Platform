import json,subprocess,hashlib,random,sys
P='docs/milestones/redesign/RD-M1-refresh-2026-10-06/'
d=json.load(open(P+'evidence/M2R-SOURCE-HASHES.json'))
files=d['files']
ten=['backend/app/core/config.py','backend/app/compliance/assist.py','backend/app/services/jobs.py','backend/app/ai/provider.py','backend/app/ai/project_policy.py','backend/app/services/project_deletion.py','backend/tests/test_sync_worker.py','backend/app/models.py','backend/tests/conftest.py','backend/tests/test_worker_runtime.py']
def show(p):
    return subprocess.run(['git','show','771001e:'+p],capture_output=True).stdout
bad=[]
for p in ten:
    if p not in files: print('MISSING',p); continue
    b=show(p); ok=hashlib.sha256(b).hexdigest()==files[p]['sha256'] and len(b)==files[p]['bytes']
    print('TEN',p,len(b),ok)
random.seed(20261006)
others=random.sample([p for p in files if p not in ten],10)
for p in others:
    b=show(p); ok=hashlib.sha256(b).hexdigest()==files[p]['sha256'] and len(b)==files[p]['bytes']
    print('RND',p,len(b),ok)
allok=0
for p,v in files.items():
    b=show(p)
    if hashlib.sha256(b).hexdigest()==v['sha256'] and len(b)==v['bytes']: allok+=1
    else: bad.append(p)
print('ALL',allok,len(files),bad, 'file_count',d['file_count'])
print(json.dumps(d['test_output_hashes'],indent=1)[:3000])
for p,v in d['test_output_hashes'].items():
    path=p if p.startswith('docs/') else P+'evidence/tests/'+p.split('/')[-1]
    b=open(path,'rb').read()
    sha=v['sha256'] if isinstance(v,dict) else v
    n=v.get('bytes') if isinstance(v,dict) else None
    # also committed blob
    cb=subprocess.run(['git','show','f4d8ca0:'+path],capture_output=True).stdout
    print('OUT',path, hashlib.sha256(b).hexdigest()==sha, (n is None or n==len(b)), hashlib.sha256(cb).hexdigest()==sha)
