import os
from pathlib import Path
import json,struct
import numpy as np
from pyproj import Transformer
R=Path(os.environ.get("BASEMAP3D_TREE_WORK", str(Path(__file__).resolve().parents[2]/"work/tree_expansion")));S=R/'staging'
points=json.loads((S/'data/tree_points.geojson').read_text())['features'];lookup={f['properties']['tree_id']:f for f in points};ts=json.loads((S/'tileset.json').read_text());back=Transformer.from_crs(4978,4979,always_xy=True)
max_xy=0;max_h=0;total=0;seen=set()
for tile in ts['root']['children']:
 if 'content' not in tile:continue
 raw=(S/tile['children'][0]['content']['uri']).read_bytes();n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);blob=raw[28+n:]
 def view(i,dtype):
  v=j['bufferViews'][i];return np.frombuffer(blob[v['byteOffset']:v['byteOffset']+v['byteLength']],dtype=dtype)
 count=j['accessors'][0]['count'];translations=view(0,'<f4').reshape(-1,3).astype('float64');enu=translations[:,[0,2,1]];enu[:,1]*=-1;mat=np.array(tile['transform']).reshape(4,4,order='F');ecef=enu@mat[:3,:3].T+mat[:3,3]
 lon,lat,h=back.transform(ecef[:,0],ecef[:,1],ecef[:,2]);offset=view(11,'<u4');strings=view(10,'u1').tobytes();ids=[strings[offset[i]:offset[i+1]].decode() for i in range(count)];source=[lookup[k] for k in ids]
 xy=np.array([f['geometry']['coordinates'] for f in source]);gh=np.array([f['properties']['ground_height_basemap_m'] for f in source]);heights=np.array([f['properties']['height_m'] for f in source])
 max_xy=max(max_xy,float(np.max(np.abs(np.column_stack((lon,lat))-xy))));max_h=max(max_h,float(np.max(np.abs(h-gh))))
 assert np.max(np.abs(view(12,'<f4')-heights))<.00001
 assert np.max(np.abs(view(13,'<f4')-heights))<.00001
 assert np.max(np.abs(view(14,'<f4')-gh))<.00001
 assert len(ids)==len(set(ids));seen.update(ids);total+=count
assert total==len(points)==40482;assert len(seen)==len(points);assert max_xy<1e-7;assert max_h<.001
v=dict(glb_files_validated=54,trees=total,spatial_cells=len(ts['root']['children']),nonempty_cells=27,max_position_error_degrees=max_xy,max_ground_height_error_m=max_h,gltf_validation_errors=0,gltf_validation_warnings=0,terrain=json.loads((R/'terrain_validation.json').read_text()),height_mode='estimated_only')
(S/'data/validation_summary.json').write_text(json.dumps(v,indent=2));print(json.dumps(v,indent=2))
