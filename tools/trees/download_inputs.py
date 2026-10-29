import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import subprocess,json,hashlib,time
ROOT=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")));raw=ROOT/'raw';raw.mkdir(exist_ok=True)
cells=[(x,y) for x in range(442,449) for y in range(5537,5541) if x<446 or y==5540]
jobs=[]
for product in ['dom1','dgm1']:
 for x,y in cells:
  name=f'{product}_32_{x}_{y}_1_rp_2023.tif';jobs.append((product,name,f'https://geobasis-rlp.de/data/{product}/current/tif/{name}'))
for x,y in sorted({(x//2*2,y//2*2) for x,y in cells}):
 # Cell 32_448_5540 is entirely outside the retained Mainz mask.
 if (x,y)==(448,5540):continue
 name=f'dop20rgbi_32_{x}_{y}_2_rp_2024.jp2';jobs.append(('dop20rgbi',name,f'https://geobasis-rlp.de/data/dop20rgbi/current/jp2/{name}'))
def fetch(job):
 product,name,url=job;target=raw/name
 if not target.exists():
  partial=target.with_suffix(target.suffix+'.part')
  subprocess.run(['curl','--fail','--silent','--show-error','--retry','3','--max-time','600','--connect-timeout','20','-L',url,'-o',str(partial)],check=True)
  partial.rename(target)
 sha=hashlib.file_digest(target.open('rb'),'sha256').hexdigest() if hasattr(hashlib,'file_digest') else hashlib.sha256(target.read_bytes()).hexdigest()
 print(f'Downloaded {name} · {target.stat().st_size/1e6:.1f} MB',flush=True)
 return dict(product=product,filename=name,url=url,sha256=sha,bytes=target.stat().st_size)
results=[]
with ThreadPoolExecutor(4) as pool:
 for f in as_completed([pool.submit(fetch,j) for j in jobs]):
  results.append(f.result());(ROOT/'download_manifest.json').write_text(json.dumps(results,indent=2))
print(f'COMPLETE: {len(results)} inputs, {sum(x["bytes"] for x in results)/1e9:.2f} GB',flush=True)
