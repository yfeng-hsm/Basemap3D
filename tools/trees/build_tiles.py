from point_io import read_points, write_points
import os
from pathlib import Path
import json,struct,copy,math,shutil,hashlib
import numpy as np
from pyproj import Transformer
from shapely.geometry import shape,box,mapping
from shapely.ops import transform
from PIL import Image,ImageDraw,ImageFont
R=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")))
REPO=Path(__file__).resolve().parents[2];OLD=REPO/'docs/layers/mainz-trees';OUT=R/'staging'
(OUT/'data').mkdir(parents=True,exist_ok=True);(OUT/'tiles/estimated').mkdir(parents=True,exist_ok=True)
old=[f for f in read_points(OLD/'data/tree_points.geojson') if f['properties']['tree_id'].startswith('mainz_center_')];new=json.loads((R/'new_aligned_points.geojson').read_text())['features'];allpoints=old+new
assert len({f['properties']['tree_id'] for f in allpoints})==len(allpoints)
to_wgs=Transformer.from_crs(25832,4326,always_xy=True);to_utm=Transformer.from_crs(4326,25832,always_xy=True);to_ecef=Transformer.from_crs(4979,4978,always_xy=True)
oldset=json.loads((OLD/'tileset-estimated.json').read_text());oldchildren={c['content']['uri'].split('?')[0].split('/')[-1].replace('_coarse.glb',''):c for c in oldset['root']['children'] if c.get('content') and int(c['content']['uri'].split('/')[-1].split('_')[1])>=446 and int(c['content']['uri'].split('/')[-1].split('_')[2])<5540}
by_tile={f'32_{x}_{y}':[] for x in range(442,449) for y in range(5537,5541)}
for f in allpoints:by_tile[f['properties']['tile']].append(f)
def unpack(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),raw[28+n:]
def pack(j,views,path):
 blob=bytearray();newviews=[]
 for v,b in zip(j['bufferViews'],views):
  while len(blob)%4:blob.append(0)
  newviews.append(dict(v,byteOffset=len(blob),byteLength=len(b)));blob.extend(b)
 while len(blob)%4:blob.append(0)
 j['bufferViews']=newviews;j['buffers']=[{'byteLength':len(blob)}];js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
 raw=struct.pack('<4sII',b'glTF',2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob
 path.write_bytes(raw)
def tileframe(tile):
 _,x,y=tile.split('_');lon,lat=to_wgs.transform((int(x)+.5)*1000,(int(y)+.5)*1000);lo,la=math.radians(lon),math.radians(lat)
 axes=np.array([[-math.sin(lo),-math.sin(la)*math.cos(lo),math.cos(la)*math.cos(lo)],[math.cos(lo),-math.sin(la)*math.sin(lo),math.cos(la)*math.sin(lo)],[0,math.cos(la),math.sin(la)]])
 origin=np.array(to_ecef.transform(lon,lat,0));mat=np.eye(4);mat[:3,:3]=axes;mat[:3,3]=origin
 return axes,origin,mat.flatten(order='F').tolist()
def make_glb(tile,features,lod):
 template=OLD/f'tiles/estimated/32_446_5537_{lod}.glb';j,bin=unpack(template);j=copy.deepcopy(j)
 views=[bin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']] for v in j['bufferViews']]
 axes,origin,matrix=tileframe(tile);n=len(features)
 rows=[f['properties'] for f in features];height=np.array([p['height_m'] for p in rows],dtype='<f4');ground=np.array([p['ground_height_basemap_m'] for p in rows],dtype='<f4')
 lon=np.array([p['longitude'] for p in rows]);lat=np.array([p['latitude'] for p in rows]);ecef=np.column_stack(to_ecef.transform(lon,lat,ground.astype('float64')));enu=(ecef-origin)@axes
 xyz=enu[:,[0,2,1]];xyz[:,2]*=-1;xyz=xyz.astype('<f4');angle=np.arange(n)*2.39996322973;rot=np.column_stack((np.zeros(n),np.sin(angle/2),np.zeros(n),np.cos(angle/2))).astype('<f4');scale=np.repeat(height[:,None],3,axis=1)
 dtype='<u2' if n<=65535 else '<u4';ids=np.arange(n,dtype=dtype)
 for idx,arr in enumerate((xyz,rot,scale,ids)):
  views[idx]=arr.tobytes();acc=j['accessors'][idx];acc['count']=n
  if idx!=1:
   acc['min']=arr.min(axis=0).tolist() if arr.ndim>1 else [int(arr.min())];acc['max']=arr.max(axis=0).tolist() if arr.ndim>1 else [int(arr.max())]
  if idx==3:acc['componentType']=5123 if n<=65535 else 5125
 strings=[p['tree_id'].encode() for p in rows];offsets=np.r_[0,np.cumsum([len(s) for s in strings])].astype('<u4')
 views[10]=b''.join(strings);views[11]=offsets.tobytes();views[12]=height.tobytes();views[13]=height.tobytes();views[14]=ground.tobytes();views[15]=np.array([p['review_recommended'] for p in rows],dtype='u1').tobytes()
 for node in j['nodes']:
  if 'EXT_instance_features' in node.get('extensions',{}):node['extensions']['EXT_instance_features']['featureIds'][0]['featureCount']=n
 j['extensions']['EXT_structural_metadata']['propertyTables'][0]['count']=n;j['asset']['generator']='Basemap3D Mainz estimated-height expansion 2026-10-29'
 path=OUT/f'tiles/estimated/{tile}_{lod}.glb';pack(j,views,path)
 lower=np.min(enu-np.column_stack((height*.45,height*.45,np.zeros(n))),axis=0);upper=np.max(enu+np.column_stack((height*.45,height*.45,height)),axis=0);center=(lower+upper)/2;half=(upper-lower)/2
 return matrix,{'box':[*center.tolist(),float(half[0]),0,0,0,float(half[1]),0,0,0,float(half[2])]}
children=[]
for tile,features in sorted(by_tile.items()):
 if tile in oldchildren:
  children.append(copy.deepcopy(oldchildren[tile]))
  for node in [children[-1], *children[-1].get('children',[])]:
   uri=node['content']['uri'].split('?')[0];destination=OUT/uri;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(OLD/uri,destination)
 elif features:
  matrix,bounds=make_glb(tile,features,'fine');make_glb(tile,features,'coarse')
  children.append(dict(transform=matrix,boundingVolume=bounds,geometricError=3,refine='REPLACE',content={'uri':f'tiles/estimated/{tile}_coarse.glb'},children=[dict(boundingVolume=bounds,geometricError=0,content={'uri':f'tiles/estimated/{tile}_fine.glb'})]))
 else:
  _,xs,ys=tile.split('_');corners=[to_wgs.transform(int(xs)*1000+dx,int(ys)*1000+dy) for dx in (0,1000) for dy in (0,1000)];ls,ps=zip(*corners)
  children.append(dict(boundingVolume={'region':[math.radians(min(ls)),math.radians(min(ps)),math.radians(max(ls)),math.radians(max(ps)),0,500]},geometricError=0,extras={'tile':tile,'candidate_count':0,'reason':'Outside the retained Mainz municipal mask'}))
for f in allpoints:f['properties']['model_height_m']=f['properties']['height_m']
corners=[to_wgs.transform(x,y) for x in (442000,449000) for y in (5537000,5541000)];lons,lats=zip(*corners);minh=min(f['properties']['ground_height_basemap_m'] for f in allpoints)-2;maxh=max(f['properties']['ground_height_basemap_m']+f['properties']['height_m'] for f in allpoints)+2
asset=copy.deepcopy(oldset['asset']);asset['tilesetVersion']='2026-10-29';asset['extras'].update(candidate_tree_count=len(allpoints),spatial_tiles=28,nonempty_spatial_tiles=sum(bool(v) for v in by_tile.values()));asset['extras'].pop('uniform_height_m',None)
root=dict(boundingVolume={'region':[math.radians(min(lons)),math.radians(min(lats)),math.radians(max(lons)),math.radians(max(lats)),minh,maxh]},geometricError=100,refine='ADD',children=children)
for child in children:
 if 'content' not in child:child['boundingVolume']['region'][-2:]=[minh,maxh]
tileset=dict(asset=asset,geometricError=100,root=root)
for name in ('tileset.json','tileset-estimated.json'):(OUT/name).write_text(json.dumps(tileset,ensure_ascii=False,separators=(',',':')))
write_points(OUT/'data/tree_points.geojson.gz',allpoints)
review=[f for f in allpoints if f['properties']['review_recommended']];(OUT/'data/review_points.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=review),separators=(',',':')))
boundarydoc=json.loads((OLD/'data/mainz_boundary.geojson').read_text());boundary=transform(to_utm.transform,shape(boundarydoc['geometry']));area=boundary.intersection(box(442000,5537000,449000,5541000)).area/1e6
shutil.copyfile(OLD/'data/mainz_boundary.geojson',OUT/'data/mainz_boundary.geojson')
poly=[to_wgs.transform(x,y) for x,y in [(442000,5537000),(449000,5537000),(449000,5541000),(442000,5541000),(442000,5537000)]]
(OUT/'data/aoi.geojson').write_text(json.dumps(dict(type='Feature',properties=dict(name='Mainz expanded processing extent',area_km2=28,width_m=7000,height_m=4000,crs_projected='EPSG:25832',bounds_utm=[442000,5537000,449000,5541000],status='selected_processing_extent_not_administrative_boundary'),geometry=dict(type='Polygon',coordinates=[poly])),indent=2))
oldbuildings=json.loads((OLD/'data/building_footprints.geojson').read_text())['features'];newbuildings=json.loads((R/'new_building_footprints.geojson').read_text())['features'];buildings={}
for f in oldbuildings+newbuildings:buildings[(f['properties'].get('osm_type','way'),f['properties'].get('osm_id',json.dumps(f['geometry'])))]=f
(OUT/'data/building_footprints.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=list(buildings.values())),separators=(',',':')))
manifest=json.loads((OLD/'data/input_manifest.json').read_text());seen={x['filename'] for x in manifest}
for p in sorted((R/'raw').glob('*')):
 if p.suffix not in ('.tif','.jp2') or p.name in seen:continue
 product='dop20rgbi' if p.suffix=='.jp2' else p.name.split('_')[0];folder='jp2' if p.suffix=='.jp2' else 'tif'
 manifest.append(dict(filename=p.name,url=f'https://geobasis-rlp.de/data/{product}/current/{folder}/{p.name}',sha256=hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),bytes=p.stat().st_size,product=product))
(OUT/'data/input_manifest.json').write_text(json.dumps(manifest,indent=2))
summary=dict(selected_frame_area_km2=28,mainz_area_inside_frame_km2=round(area,4),candidate_tree_count=len(allpoints),retained_original_candidates=len(old),added_candidates=len(new),height_range_m=[min(f['properties']['height_m'] for f in allpoints),max(f['properties']['height_m'] for f in allpoints)],height_over_30m_review_count=len(review),building_footprints_used=len(buildings),tile_counts={k:len(v) for k,v in by_tile.items()},method=dict(ndvi_min=.3,minimum_height_m=4,minimum_crown_area_m2=16,peak_spacing_m=4,building_exclusion_buffer_m=1,height_estimation='P99(pixelwise DOM1-DGM1)',municipal_mask='OpenStreetMap Mainz relation 62630',expanded_area_segmentation='1 m RGBI band averages; CHM Gaussian sigma 1 m; seeded watershed, 4 m peak spacing'),limits=['Automatic candidates, not field-verified.','Original nine tiles retained without resampling.','Municipal mask retained; northeast cell 32_448_5540 has no Mainz area and is intentionally empty.','2023 elevation and 2024 imagery are not simultaneous.'])
(OUT/'data/processing_summary.json').write_text(json.dumps(summary,indent=2))
provenance=dict(dataset='Mainz estimated-height tree candidates · 7 × 4 km',date='2026-10-29',processing_frame_crs='EPSG:25832',processing_bounds=[442000,5537000,449000,5541000],spatial_tiles=28,candidate_count=len(allpoints),height_mode='estimated',retained_original_candidates=len(old),added_candidates=len(new),terrain_alignment='Fixed model bases aligned to basemap.de DGM5 level 16 using Cesium-compatible triangle interpolation.',source_data='RLP DOM1/DGM1 2023, RGBI orthophotos 2024; OSM building and Mainz municipality masks.',attribution='©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL',original_source_commit='eeb2721591eae19ab4bdafbf1c0f5ebf7e380cce',municipal_mask_retained=True)
(OUT/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
# Projected grid overview. Empty/outside-mask cells are explicit.
W,H=1280,820;image=Image.new('RGB',(W,H),'#f6f8f5');draw=ImageDraw.Draw(image);sx,sy=140,130;scale=140
for tile,features in by_tile.items():
 _,xs,ys=tile.split('_');x=(int(xs)-442)*scale+sx;y=(5540-int(ys))*scale+sy
 draw.rectangle((x,y,x+scale,y+scale),fill='#e1ebdf' if features else '#e9e9e5',outline='#a7b8a4',width=1)
 draw.text((x+8,y+8),f'{xs} / {ys}',fill='#52664d');draw.text((x+8,y+30),f'{len(features):,} trees',fill='#294c35')
 if int(xs)>=446 and int(ys)<5540:draw.rectangle((x+2,y+2,x+scale-2,y+scale-2),outline='#327968',width=3)
draw.text((140,40),'MAINZ · ESTIMATED TREE HEIGHTS · 7 km x 4 km',fill='#204435');draw.text((140,65),f'{len(allpoints):,} candidates | 28 spatial cells | green outline = original 3 x 3 km',fill='#52664d');draw.text((140,730),'UTM 32N (EPSG:25832) | west 442000 / east 449000 | south 5537000 / north 5541000',fill='#52664d');image.save(OUT/'extent-map.png')
print(json.dumps({k:v for k,v in summary.items() if k not in ('tile_counts','method','limits')},indent=2),flush=True)
