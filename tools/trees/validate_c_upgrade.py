from point_io import read_points, write_points
"""Check published tree metadata and both LODs against candidate coordinates."""
from pathlib import Path
import json,struct,collections,hashlib,math
import numpy as np
from pyproj import Transformer
ROOT=Path(__file__).resolve().parents[2];L=ROOT/'docs/layers/mainz-trees'
features=read_points(L/'data/tree_points.geojson');byid={f['properties']['tree_id']:f['properties'] for f in features};assert len(byid)==len(features)==54014
bytile=collections.Counter(p['tile'] for p in byid.values());tileset=json.loads((L/'tileset-estimated.json').read_text());assert tileset==json.loads((L/'tileset.json').read_text())
fromecef=Transformer.from_crs(4978,4979,always_xy=True);maxpos=maxground=maxheight=maxdiameter=0;counts=collections.Counter();nfiles=0
for tile in tileset['root']['children']:
 if not tile.get('content'):continue
 matrix=np.array(tile['transform']).reshape(4,4,order='F')
 for node in [tile,*tile.get('children',[])]:
  file=L/node['content']['uri'].split('?')[0];raw=file.read_bytes();magic,version,size=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and version==2 and size==len(raw)
  jl=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+jl]);binary=raw[28+jl:];assert len(binary)>=j['buffers'][0]['byteLength']
  for v in j['bufferViews']:assert v.get('byteOffset',0)+v['byteLength']<=len(binary)
  def view(i):
   v=j['bufferViews'][i];return binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
  def acc(i):
   a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];dtype=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize))
  table=j['extensions']['EXT_structural_metadata']['propertyTables'][0];props=table['properties'];strings=view(props['tree_id']['values']);offsets=np.frombuffer(view(props['tree_id']['stringOffsets']),dtype='<u4');ids=[strings[a:b].decode() for a,b in zip(offsets[:-1],offsets[1:])];assert len(ids)==table['count'] and len(set(ids))==len(ids)
  rows=[byid[i] for i in ids];tilekey=rows[0]['tile'];assert len(rows)==bytile[tilekey] and all(r['tile']==tilekey for r in rows)
  attrs=j['nodes'][0]['extensions']['EXT_mesh_gpu_instancing']['attributes'];translations=acc(attrs['TRANSLATION']);assert len(translations)==len(rows)
  for n in j['nodes']:
   attrs2=n['extensions']['EXT_mesh_gpu_instancing']['attributes'];assert len(acc(attrs2['TRANSLATION']))==len(rows);assert n['extensions']['EXT_instance_features']['featureIds'][0]['featureCount']==len(rows)
  enu=translations[:,[0,2,1]].astype('float64');enu[:,1]*=-1;ecef=enu@matrix[:3,:3].T+matrix[:3,3];lon,lat,ground=fromecef.transform(*ecef.T)
  maxpos=max(maxpos,float(np.max(np.abs(lon-[r['longitude'] for r in rows]))),float(np.max(np.abs(lat-[r['latitude'] for r in rows]))));maxground=max(maxground,float(np.max(np.abs(ground-[r['ground_height_basemap_m'] for r in rows]))))
  for prop,key in [('model_height_m','height_m'),('source_height_m','height_m'),('ground_height_m','ground_height_basemap_m')]:
   values=np.frombuffer(view(props[prop]['values']),dtype='<f4');err=float(np.max(np.abs(values-[r[key] for r in rows])));maxheight=max(maxheight,err)
  if 'crown_diameter_m' in props:
   diameter=np.frombuffer(view(props['crown_diameter_m']['values']),dtype='<f4');maxdiameter=max(maxdiameter,float(np.max(np.abs(diameter-[r['crown_diameter_equivalent_m'] for r in rows]))))
  lod='coarse' if '_coarse.glb' in file.name else 'fine';counts[lod]+=len(rows);nfiles+=1
assert counts==dict(coarse=54014,fine=54014) and nfiles==54
assert maxpos<1e-7 and maxground<.001 and maxheight<.001 and maxdiameter<.001
out=dict(trees=len(features),center_trees=sum(i.startswith('mainz_center_') for i in byid),extension_trees=sum(not i.startswith('mainz_center_') for i in byid),glb_files_checked=nfiles,trees_per_lod=dict(counts),max_position_error_degrees=maxpos,max_ground_height_error_m=maxground,max_metadata_height_error_m=maxheight,max_center_crown_diameter_error_m=maxdiameter,checks=['GLB headers, buffer bounds, unique IDs and candidate references','Per-tile feature counts at both LODs','ECEF georeference and fixed DGM5 bases match candidate points','Source/model heights and C crown diameter metadata match candidates'],browser_render='Not verified in this environment',khronos_validation='Not rerun; source archive reports zero errors for its original exports',configuration='C_balanced centre; extension unchanged')
(L/'data/validation_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
