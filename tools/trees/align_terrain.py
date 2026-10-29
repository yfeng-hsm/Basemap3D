from point_io import read_points, write_points
import os
from pathlib import Path
import json,math,subprocess,time
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
R=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")));terrain=R/'terrain';terrain.mkdir(exist_ok=True)
REPO=Path(__file__).resolve().parents[2]
old=read_points(REPO/'docs/layers/mainz-trees/data/tree_points.geojson');new=[]
for p in sorted((R/'processing').glob('32*.json')):new+=json.loads(p.read_text())['features']
z=16
key=lambda f:(int(math.floor((f['geometry']['coordinates'][0]+180)*2**(z+1)/360)),int(math.floor((f['geometry']['coordinates'][1]+90)*2**z/180)))
keys=sorted(set(key(f) for f in new+old[:30]))
def get(pair):
 x,y=pair;p=terrain/f'{z}_{x}_{y}.bin'
 if not p.exists():subprocess.run(['curl','--fail','--silent','--show-error','--retry','2','--max-time','45',f'https://sgx.geodatenzentrum.de/gdz_basemapde_3d_gelaende/dgm5_4326_mesh/{z}/{x}/{y}.terrain?v=1.1.0','-o',str(p)],check=True)
 raw=p.read_bytes();assert len(raw)>=8450
 return pair,np.frombuffer(raw[:8450],dtype='<u2').astype('float64').reshape(65,65)*.2-1000
cache={}
with ThreadPoolExecutor(8) as pool:
 for f in as_completed([pool.submit(get,k) for k in keys]):
  k,h=f.result();cache[k]=h
  if len(cache)%50==0:print(f'Terrain {len(cache)}/{len(keys)} tiles',flush=True)
def sample(f):
 lon,lat=f['geometry']['coordinates'];x,y=key(f);h=cache[(x,y)]
 xx=(lon-(-180+x*360/2**(z+1)))/(360/2**(z+1))*64;yy=(lat-(-90+y*180/2**z))/(180/2**z)*64
 i,j=min(63,int(xx)),min(63,int(yy));u,v=xx-i,yy-j
 sw,se,nw,ne=h[64-j,i],h[64-j,i+1],h[63-j,i],h[63-j,i+1]
 return float(sw+u*(se-sw)+v*(ne-se) if v<u else sw+u*(ne-nw)+v*(nw-sw))
error=max(abs(sample(f)-f['properties']['ground_height_basemap_m']) for f in old[:30]);assert error<.002,error
for f in new:
 h=sample(f);f['properties']['ground_height_basemap_m']=round(h,3);f['properties']['ground_difference_m']=round(h-f['properties']['ground_height_dgm1_m'],3)
(R/'new_aligned_points.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=new)))
(R/'terrain_validation.json').write_text(json.dumps(dict(terrain_tiles=len(cache),level=z,sample_count=len(new),original_reference_check_max_error_m=error,method='Cesium-compatible heightmap-1.0 triangle interpolation; heightScale=0.2, heightOffset=-1000'),indent=2))
print(f'COMPLETE: aligned {len(new)} trees; original reference error {error:.6f} m',flush=True)
