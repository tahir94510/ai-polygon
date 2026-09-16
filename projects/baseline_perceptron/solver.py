import json,sys
from pathlib import Path
rows=lambda p:[json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
if sys.argv[1]=='train':
    data=rows(sys.argv[2]); w=[0.,0.,0.]
    for _ in range(20):
        for r in data:
            x=[1.,*r['x']]; predicted=int(sum(a*b for a,b in zip(w,x))>=0)
            update=r['y']-predicted
            w=[a+0.1*update*b for a,b in zip(w,x)]
    Path(sys.argv[3]).write_text(json.dumps(w))
else:
    w=json.loads(Path(sys.argv[3]).read_text())
    Path(sys.argv[4]).write_text(''.join(json.dumps({'id':r['id'],'prediction':int(sum(a*b for a,b in zip(w,[1.,*r['x']]))>=0)})+'\n' for r in rows(sys.argv[2])))
