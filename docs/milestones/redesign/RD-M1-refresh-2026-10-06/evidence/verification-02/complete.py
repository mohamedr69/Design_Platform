import csv,json,re,subprocess
P='docs/milestones/redesign/RD-M1-refresh-2026-10-06/'
files=set(json.load(open(P+'evidence/M2R-SOURCE-HASHES.json'))['files'])
tree=set(subprocess.run(['git','ls-tree','-r','--name-only','771001e','backend','frontend'],capture_output=True,text=True).stdout.split())
cols={'M2R-FINDINGS-DELTA.csv':None,
      'M2R-NEW-SURFACE-INVENTORY.csv':None}
full=re.compile(r'(?:backend|frontend)/[\w./\-]+?\.(?:py|tsx?|json|ini|cfg|toml|js|css|md|txt)')
bare=re.compile(r'(?<![\w/])((?:[\w\-]+/)*[\w\-]+\.(?:py|tsx?))')
unh={}; barehits={}
for fn in cols:
    r=list(csv.reader(open(P+fn,newline='',encoding='utf-8')))
    h=r[0]
    print(fn,h)
    wanted=h[1:]
    print(' scanning',wanted)
    for row in r[1:]:
        for c in wanted:
            if c not in h: continue
            cell=row[h.index(c)]
            for m in full.findall(cell):
                if m not in files: unh.setdefault(m,[]).append((fn,row[0],c, m in tree))
            for m in bare.findall(cell):
                if m.startswith(('backend/','frontend/')): continue
                cands=[t for t in tree if t.endswith('/'+m)]
                hashed=[t for t in cands if t in files]
                if not hashed: barehits.setdefault(m,[]).append((fn,row[0],c,cands[:3]))
print('UNHASHED full paths:'); [print(' ',k,v) for k,v in unh.items()]
print('UNHASHED bare names:'); [print(' ',k,v[:4],len(v)) for k,v in barehits.items()]
