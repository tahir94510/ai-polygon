import json,sys
from pathlib import Path

def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def features(x):return [1.0,*x]
def solve(a,b):
    n=len(b)
    for i in range(n):
        k=max(range(i,n),key=lambda j:abs(a[j][i]))
        a[i],a[k]=a[k],a[i];b[i],b[k]=b[k],b[i]
        pivot=a[i][i]
        if abs(pivot)<1e-12:raise RuntimeError('Singular matrix')
        for j in range(i,n):a[i][j]/=pivot
        b[i]/=pivot
        for k in range(n):
            if k==i:continue
            fac=a[k][i]
            for j in range(i,n):a[k][j]-=fac*a[i][j]
            b[k]-=fac*b[i]
    return b
if sys.argv[1]=='train':
    data=rows(sys.argv[2]);d=len(features(data[0]['x']));a=[[0.0]*d for _ in range(d)];b=[0.0]*d
    for r in data:
        f=features(r['x'])
        for i in range(d):
            b[i]+=f[i]*r['y']
            for j in range(d):a[i][j]+=f[i]*f[j]
    for i in range(1,d):a[i][i]+=0.01
    Path(sys.argv[3]).write_text(json.dumps(solve(a,b)))
else:
    w=json.loads(Path(sys.argv[3]).read_text())
    Path(sys.argv[4]).write_text(''.join(json.dumps({'id':r['id'],'prediction':sum(i*j for i,j in zip(w,features(r['x'])))})+'\n' for r in rows(sys.argv[2])))
