"""Compact candidate storage; expand legacy names only inside processing code."""
from pathlib import Path
import gzip,json
FIELDS={'height_m':'height','crown_area_m2':'crown_area','crown_diameter_equivalent_m':'crown_diam','ground_height_dgm1_m':'z_dgm1','ground_height_basemap_m':'z_base','mean_ndvi':'ndvi','edge_truncated':'edge','review_recommended':'review','tile':'tile'}
METHOD='P99(pixelwise DOM1-DGM1)'
def read_points(path):
 path=Path(path)
 if not path.exists() and path.suffix!='.gz':path=Path(str(path)+'.gz')
 raw=path.read_bytes();data=json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)
 for f in data['features']:
  p=f['properties']
  if 'height' in p:
   f['properties']=p={old:p[new] for old,new in FIELDS.items()}
   p.update(tree_id=f['id'],longitude=f['geometry']['coordinates'][0],latitude=f['geometry']['coordinates'][1],height_method=data.get('metadata',{}).get('height_method',METHOD))
   p['model_height_m']=p['height_m'];p['ground_difference_m']=p['ground_height_basemap_m']-p['ground_height_dgm1_m']
 return data['features']
def write_points(path,features):
 methods={f['properties'].get('height_method',METHOD) for f in features}
 if len(methods)>1:raise ValueError('Mixed height methods require per-feature method codes')
 metadata={'feature_count':len(features),'height_method':next(iter(methods),METHOD),'fields':{new:{'original_field':old,'unit':'m' if new in ('height','crown_diam','z_dgm1','z_base') else 'm2' if new=='crown_area' else None} for old,new in FIELDS.items()},'id_field':'Feature.id','coordinates':'Original GeoJSON geometry; no rounding'}
 result=[]
 for f in features:
  p=f['properties'];ident=f.get('id',p.get('tree_id'))
  if not ident:raise ValueError('Missing candidate ID')
  if p.get('model_height_m',p['height_m'])!=p['height_m']:raise ValueError('Model and source heights differ')
  result.append({'type':'Feature','id':ident,'geometry':f['geometry'],'properties':{new:p[old] for old,new in FIELDS.items()}})
 raw=json.dumps({'type':'FeatureCollection','metadata':metadata,'features':result},ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()
 path=Path(path);path.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0) if path.suffix=='.gz' else raw)
