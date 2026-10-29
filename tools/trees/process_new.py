import os
from pathlib import Path
import os,sys,json,time
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.transform import from_origin
from scipy.ndimage import gaussian_filter,label as connected_labels
from skimage.feature import peak_local_max
from skimage.segmentation import watershed
from shapely.geometry import shape,box,mapping
from shapely.ops import transform
from shapely.strtree import STRtree
from pyproj import Transformer
ROOT=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")))
(ROOT/'processing').mkdir(parents=True,exist_ok=True)
REPO=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(REPO))
from basemap3d._osm import from_elements
wgs_to_utm=Transformer.from_crs(4326,25832,always_xy=True);utm_to_wgs=Transformer.from_crs(25832,4326,always_xy=True)
boundary=transform(wgs_to_utm.transform,shape(json.loads((REPO/'docs/layers/mainz-trees/data/mainz_boundary.geojson').read_text())['geometry']))
footprints=from_elements(json.loads((ROOT/'osm_buildings.json').read_text())['elements'])
(ROOT/'new_building_footprints.geojson').write_text(json.dumps(footprints))
buildings=[transform(wgs_to_utm.transform,shape(f['geometry'])).buffer(1) for f in footprints['features']]
index=STRtree(buildings)
print(f'Building exclusion: {len(buildings)} footprints, 1 m buffer',flush=True)
counts={}
for x in range(442,449):
 for y in range(5537,5541):
  if x>=446 and y<5540:continue
  tile=f'32_{x}_{y}';out=ROOT/'processing'/f'{tile}.json'
  if out.exists():counts[tile]=len(json.loads(out.read_text())['features']);continue
  started=time.time();bounds=(x*1000,y*1000,(x+1)*1000,(y+1)*1000);clip=boundary.intersection(box(*bounds))
  if clip.is_empty:
   out.write_text(json.dumps({'type':'FeatureCollection','features':[]}));counts[tile]=0;print(f'{tile}: outside Mainz mask; empty',flush=True);continue
  tf=from_origin(bounds[0],bounds[3],1,1)
  domfile=ROOT/'raw'/f'dom1_{tile}_1_rp_2023.tif';dgmfile=ROOT/'raw'/f'dgm1_{tile}_1_rp_2023.tif'
  with rasterio.open(domfile) as ds:dom=ds.read(1).astype('float32');dom_valid=ds.read_masks(1)>0;assert dom.shape==(1000,1000)
  with rasterio.open(dgmfile) as ds:dgm=ds.read(1).astype('float32');dgm_valid=ds.read_masks(1)>0;assert dgm.shape==dom.shape
  chm=dom-dgm
  jp=ROOT/'raw'/f'dop20rgbi_32_{x//2*2}_{y//2*2}_2_rp_2024.jp2'
  with rasterio.open(jp,num_threads=2) as ds:
   values=ds.read((1,4),window=from_bounds(*bounds,transform=ds.transform),out_shape=(2,1000,1000),resampling=Resampling.average).astype('float32')
  red,nir=values;ndvi=(nir-red)/(nir+red+1e-6)
  city_mask=rasterize([(mapping(clip),1)],out_shape=chm.shape,transform=tf,dtype='uint8')>0
  near=index.query(box(*bounds));building_mask=rasterize([(mapping(buildings[i]),1) for i in near],out_shape=chm.shape,transform=tf,dtype='uint8')>0 if len(near) else np.zeros(chm.shape,dtype=bool)
  mask=city_mask&dom_valid&dgm_valid&(nir+red>0)&(ndvi>=.3)&(chm>=4)&~building_mask
  smooth=gaussian_filter(np.where(dom_valid&dgm_valid,chm,0),sigma=1)
  peaks=peak_local_max(smooth,min_distance=4,labels=mask.astype('uint8'),exclude_border=False)
  markers=np.zeros(mask.shape,dtype='int32');markers[tuple(peaks.T)]=np.arange(1,len(peaks)+1)
  # Components with no peak still need a marker to avoid silently losing crowns.
  components,n=connected_labels(mask)
  present=set(components[tuple(peaks.T)].tolist());next_id=len(peaks)+1
  areas=np.bincount(components.ravel())
  for k in np.flatnonzero(areas>=16):
   if k==0 or k in present:continue
   rr,cc=np.where(components==k)
   if len(rr)>=16:
    best=np.argmax(chm[rr,cc]);markers[rr[best],cc[best]]=next_id;next_id+=1
  labels=watershed(-smooth,markers,mask=mask)
  flat=labels.ravel();order=np.argsort(flat,kind='stable');ordered=flat[order];cuts=np.r_[0,np.flatnonzero(np.diff(ordered))+1,len(order)]
  features=[]
  for a,b in zip(cuts[:-1],cuts[1:]):
   labelid=ordered[a]
   if labelid==0 or b-a<16:continue
   ids=order[a:b];rr,cc=np.unravel_index(ids,mask.shape);h=float(np.percentile(chm[rr,cc],99));peak=np.argmax(smooth[rr,cc]);row,col=int(rr[peak]),int(cc[peak]);e=bounds[0]+col+.5;north=bounds[3]-row-.5;lon,lat=utm_to_wgs.transform(e,north)
   ident=f'mainz_ext_{x}_{y}_{len(features)+1:05}'
   props=dict(tree_id=ident,easting=e,northing=north,longitude=round(lon,8),latitude=round(lat,8),ground_height_dgm1_m=round(float(dgm[row,col]),3),height_m=round(h,2),crown_area_m2=int(len(ids)),crown_diameter_equivalent_m=round(2*np.sqrt(len(ids)/np.pi),2),mean_ndvi=round(float(ndvi[rr,cc].mean()),3),tile=tile,edge_truncated=bool(np.any((rr==0)|(rr==999)|(cc==0)|(cc==999))),review_recommended=h>30,height_method='P99(pixelwise DOM1-DGM1)')
   features.append(dict(type='Feature',id=ident,geometry=dict(type='Point',coordinates=[round(lon,8),round(lat,8)]),properties=props))
  out.write_text(json.dumps(dict(type='FeatureCollection',features=features)));counts[tile]=len(features)
  print(f'{tile}: {len(features)} candidates · {time.time()-started:.1f} s',flush=True)
(ROOT/'new_counts.json').write_text(json.dumps(counts,indent=2));print('COMPLETE',sum(counts.values()),flush=True)
