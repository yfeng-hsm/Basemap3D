import os
import sys,json,subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pyproj import Transformer
r=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")));tf=Transformer.from_crs(25832,4326,always_xy=True)
boxes=[(x,y,min(x+2000,446000),y+2000) for x in (442000,444000) for y in (5537000,5539000)]+[(446000,5540000,448000,5541000),(448000,5540000,449000,5541000)]
def fetch(args):
 i,b=args;p=r/f'osm_{i}.json'
 if not p.exists():
  corners=[tf.transform(x,y) for x in (b[0]-20,b[2]+20) for y in (b[1]-20,b[3]+20)];xs,ys=zip(*corners);bbox=f'{min(xs)},{min(ys)},{max(xs)},{max(ys)}'
  subprocess.run(['curl','--fail','-sS','--retry','2','--max-time','60','https://api.openstreetmap.org/api/0.6/map.json?bbox='+bbox,'-o',str(p)],check=True)
 d=json.loads(p.read_text());print(f'OSM block {i}: {len(d["elements"])} elements',flush=True);return d['elements']
with ThreadPoolExecutor(3) as pool:parts=list(pool.map(fetch,enumerate(boxes)))
all={(e['type'],e['id']):e for part in parts for e in part};(r/'osm_buildings.json').write_text(json.dumps(dict(elements=list(all.values()))));print('COMPLETE',len(all),flush=True)
