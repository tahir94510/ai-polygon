# A deliberately simple experimental gate, not a claim of state-of-the-art AI.
import json,sys
from pathlib import Path
rows=lambda p:[json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def feat(x,mode):return [1.0,*x] if mode=='linear' else [1.0,*x,x[2]**2,x[0]*x[1]]
def fit(data,mode):
 d=len(feat(data[0]['x'],mode));a=[[0.0]*d for _ in range(d)];b=[0.0]*d
 for r in data:
  f=feat(r['x'],mode)
  for i in range(d):
   b[i]+=f[i]*r['y']
   for j in range(d):a[i][j]+=f[i]*f[j]
 for i in range(1,d):a[i][i]+=.01
 for i in range(d):
  k=max(range(i,d),key=lambda j:abs(a[j][i]));a[i],a[k]=a[k],a[i];b[i],b[k]=b[k],b[i];z=a[i][i]
  for j in range(i,d):a[i][j]/=z
  b[i]/=z
  for k in range(d):
   if i==k:continue
   z=a[k][i]
   for j in range(i,d):a[k][j]-=z*a[i][j]
   b[k]-=z*b[i]
 return b
if sys.argv[1]=='train':
 d=rows(sys.argv[2]);m={}
 for mode in ('linear','nonlinear'):
  w=fit(d,mode);err=sum((sum(a*b for a,b in zip(w,feat(r['x'],mode)))-r['y'])**2 for r in d)/len(d)
  m[mode]={'w':w,'mse':err}
 # Simple complexity penalty. A research project can replace this rule or architecture entirely.
 m['choice']='nonlinear' if m['nonlinear']['mse']+.0005<m['linear']['mse'] else 'linear'
 Path(sys.argv[3]).write_text(json.dumps(m))
else:
 m=json.loads(Path(sys.argv[3]).read_text());mode=m['choice'];w=m[mode]['w']
 Path(sys.argv[4]).write_text(''.join(json.dumps({'id':r['id'],'prediction':sum(a*b for a,b in zip(w,feat(r['x'],mode)))})+'\n' for r in rows(sys.argv[2])))
