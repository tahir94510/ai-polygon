import json,sys
from pathlib import Path
rows=lambda p:[json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
if sys.argv[1]=='train':
    data=rows(sys.argv[2]); label=int(sum(r['y'] for r in data)*2 >= len(data))
    Path(sys.argv[3]).write_text(json.dumps(label))
else:
    label=json.loads(Path(sys.argv[3]).read_text())
    Path(sys.argv[4]).write_text(''.join(json.dumps({'id':r['id'],'prediction':label})+'\n' for r in rows(sys.argv[2])))
