import json,sys,statistics
from pathlib import Path
rows=lambda p:[json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
if sys.argv[1]=='train':
    Path(sys.argv[3]).write_text(json.dumps({'mean':statistics.fmean(r['y'] for r in rows(sys.argv[2]))}))
else:
    mean=json.loads(Path(sys.argv[3]).read_text())['mean']
    Path(sys.argv[4]).write_text(''.join(json.dumps({'id':r['id'],'prediction':mean})+'\n' for r in rows(sys.argv[2])))
