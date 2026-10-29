from pathlib import Path
import json,struct,math,copy
import numpy as np
from pyproj import Transformer
import trimesh
p=Path(__file__).parent;out=p/'output';rows=json.loads((out/'tree_attributes.json').read_text())
tile_root=out/'mainz-center-trees';tile_root.mkdir(exist_ok=True)
unit=Path('/workspace/sites/mainz-tree-viewer/dist/assets/broadleaf_unit.glb').read_bytes();jl=struct.unpack_from('<I',unit,12)[0];src=json.loads(unit[20:20+jl]);binstart=20+jl+8;binary=unit[binstart:]
types={5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'};sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def readacc(i):
 a=src['accessors'][i];v=src['bufferViews'][a['bufferView']];dt=np.dtype(types[a['componentType']]);w=sizes[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',w*dt.itemsize)
 return np.ndarray((a['count'],w),dtype=dt,buffer=binary,offset=start,strides=(stride,dt.itemsize)).copy()
fine=[]
for mesh in src['meshes']:
 prim=mesh['primitives'][0];fine.append((readacc(prim['attributes']['POSITION']),readacc(prim['attributes']['NORMAL']),readacc(prim['indices']).ravel()))
coarse=[]
crown=trimesh.creation.icosphere(subdivisions=1);crown.apply_scale([.29,.34,.25]);crown.apply_translation([0,.66,0]);trunk=trimesh.creation.cylinder(radius=.014,height=.55,sections=6);trunk.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]));trunk.apply_translation([0,.275,0])
for mesh in [crown,trunk]:coarse.append((np.array(mesh.vertices,dtype='<f4'),np.array(mesh.vertex_normals,dtype='<f4'),np.array(mesh.faces,dtype='<u2').ravel()))
materials=src['materials']
class Writer:
 def __init__(self):self.data=bytearray();self.views=[];self.accessors=[]
 def view(self,raw,target=None):
  while len(self.data)%4:self.data.append(0)
  v={'buffer':0,'byteOffset':len(self.data),'byteLength':len(raw)}
  if target:v['target']=target
  self.views.append(v);self.data.extend(raw);return len(self.views)-1
 def acc(self,a,type,component,target=None,bounds=False):
  a=np.asarray(a);v=self.view(a.tobytes(),target);o={'bufferView':v,'componentType':component,'count':len(a),'type':type}
  if bounds:o.update(min=np.atleast_1d(a.min(axis=0)).tolist(),max=np.atleast_1d(a.max(axis=0)).tolist())
  self.accessors.append(o);return len(self.accessors)-1
 def glb(self,meshes,translations,rotations,heights,group):
  n=len(group);nodes=[];gs=[]
  ta=self.acc(translations.astype('<f4'),'VEC3',5126,34962,True);ra=self.acc(rotations.astype('<f4'),'VEC4',5126,34962);width=max(float(np.ptp(m[0][:,0])) for m in meshes)
  depth=max(float(np.ptp(m[0][:,2])) for m in meshes)
  unit_h=max(float(m[0][:,1].max()) for m in meshes)-min(float(m[0][:,1].min()) for m in meshes)
  diameters=np.array([r['crown_diameter_equivalent_m'] for r in group])
  scales=np.c_[diameters/max(width,depth),heights/unit_h,diameters/max(width,depth)]
  sa=self.acc(scales.astype('<f4'),'VEC3',5126,34962,True);fa=self.acc(np.arange(n,dtype='<u2'),'SCALAR',5123,34962,True)
  for i,(pos,norm,idx) in enumerate(meshes):
   pa=self.acc(pos.astype('<f4'),'VEC3',5126,34962,True);na=self.acc(norm.astype('<f4'),'VEC3',5126,34962);ia=self.acc(idx.astype('<u2'),'SCALAR',5123,34963,True)
   gs.append({'primitives':[{'attributes':{'POSITION':pa,'NORMAL':na},'indices':ia,'material':i,'mode':4}]})
   nodes.append({'mesh':i,'name':'TreeCrown' if i==0 else 'TreeTrunk','extensions':{'EXT_mesh_gpu_instancing':{'attributes':{'TRANSLATION':ta,'ROTATION':ra,'SCALE':sa,'_FEATURE_ID_0':fa}},'EXT_instance_features':{'featureIds':[{'featureCount':n,'attribute':0,'propertyTable':0,'label':'tree'}]}}})
  strings=[r['tree_id'].encode() for r in group];offsets=np.r_[0,np.cumsum([len(s) for s in strings])].astype('<u4');pv={
   'tree_id':{'values':self.view(b''.join(strings)),'stringOffsets':self.view(offsets.tobytes()),'stringOffsetType':'UINT32'}}
  numeric={'model_height_m':heights,'source_height_m':np.array([r['height_m'] for r in group]),'crown_diameter_m':np.array([r['crown_diameter_equivalent_m'] for r in group]),'ground_height_m':np.array([r['ground_height_basemap_m'] for r in group])}
  for k,a in numeric.items():pv[k]={'values':self.view(a.astype('<f4').tobytes())}
  pv['needs_review']={'values':self.view(np.array([r['review_recommended'] for r in group],dtype='u1').tobytes())}
  properties={'tree_id':{'type':'STRING'},**{k:{'type':'SCALAR','componentType':'FLOAT32'} for k in numeric},'needs_review':{'type':'SCALAR','componentType':'UINT8'}}
  while len(self.data)%4:self.data.append(0)
  document={'asset':{'version':'2.0','generator':'Mainz individual-tree pipeline'},'scene':0,'scenes':[{'nodes':[0,1]}],'nodes':nodes,'meshes':gs,'materials':materials,'buffers':[{'byteLength':len(self.data)}],'bufferViews':self.views,'accessors':self.accessors,'extensionsUsed':['EXT_mesh_gpu_instancing','EXT_instance_features','EXT_structural_metadata'],'extensionsRequired':['EXT_mesh_gpu_instancing'],'extensions':{'EXT_structural_metadata':{'schema':{'id':'mainz_tree_schema','classes':{'tree':{'properties':properties}}},'propertyTables':[{'class':'tree','count':n,'properties':pv}]}}}
  j=json.dumps(document,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data=bytes(self.data);return struct.pack('<III',0x46546c67,2,28+len(j)+len(data))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(data),0x004e4942)+data
wgs=Transformer.from_crs(25832,4326,always_xy=True);ecef=Transformer.from_crs(4979,4978,always_xy=True)
groups={}
for r in rows:groups.setdefault(r['tile'],[]).append(r)
aoi=json.loads((p/'aoi.geojson').read_text());xs,ys=zip(*aoi['geometry']['coordinates'][0]);minh=min(r['ground_height_basemap_m'] for r in rows);maxh=max(r['ground_height_basemap_m']+r['height_m'] for r in rows)
for variant in ['uniform','estimated']:
 children=[]
 for key,group in sorted(groups.items()):
  _,e,n=key.split('_');lon,lat=wgs.transform(int(e)*1000+500,int(n)*1000+500);lam,phi=math.radians(lon),math.radians(lat);origin=np.array(ecef.transform(lon,lat,0));R=np.array([[-math.sin(lam),-math.sin(phi)*math.cos(lam),math.cos(phi)*math.cos(lam)],[math.cos(lam),-math.sin(phi)*math.sin(lam),math.cos(phi)*math.sin(lam)],[0,math.cos(phi),math.sin(phi)]])
  world=np.array([ecef.transform(r['longitude'],r['latitude'],r['ground_height_basemap_m']) for r in group]);enu=(world-origin)@R;translations=np.c_[enu[:,0],enu[:,2],-enu[:,1]];heights=np.full(len(group),15.) if variant=='uniform' else np.array([r['height_m'] for r in group]);angles=np.array([int(r['tree_id'].split('_')[-1])*2.39996322973 for r in group]);rotations=np.c_[np.zeros(len(group)),np.sin(angles/2),np.zeros(len(group)),np.cos(angles/2)]
  radial_factor=max(max(float(np.linalg.norm(m[0][:,[0,2]],axis=1).max()) for m in lodmesh)/max(max(float(np.ptp(m[0][:,0])),float(np.ptp(m[0][:,2]))) for m in lodmesh) for lodmesh in [fine,coarse])
  radius=np.array([r['crown_diameter_equivalent_m'] for r in group])*radial_factor+.1;low=np.array([np.min(enu[:,0]-radius),np.min(enu[:,1]-radius),np.min(enu[:,2])-.1]);high=np.array([np.max(enu[:,0]+radius),np.max(enu[:,1]+radius),np.max(enu[:,2]+heights)+.1]);center=(low+high)/2;half=(high-low)/2;box=[*center,half[0],0,0,0,half[1],0,0,0,half[2]]
  transform=np.eye(4);transform[:3,:3]=R;transform[:3,3]=origin
  paths={}
  for lod,model in [('coarse',coarse),('fine',fine)]:
   relative=f'tiles/{variant}/{key}_{lod}.glb';dest=tile_root/relative;dest.parent.mkdir(exist_ok=True,parents=True);dest.write_bytes(Writer().glb(model,translations,rotations,heights,group));paths[lod]=relative
  bv={'box':box};children.append({'transform':transform.flatten(order='F').tolist(),'boundingVolume':bv,'geometricError':3,'refine':'REPLACE','content':{'uri':paths['coarse']},'children':[{'boundingVolume':bv,'geometricError':0,'content':{'uri':paths['fine']}}]})
 document={'asset':{'version':'1.1','tilesetVersion':'2026-10-28','extras':{'configuration':'C_balanced','crown_scaling':'area-equivalent diameter independent of height','candidate_tree_count':len(rows),'height_mode':variant,'uniform_height_m':15 if variant=='uniform' else None,'ground_height_source':'basemap.de dgm5_4326_mesh level 16, Cesium interpolation; visually aligned to that terrain service','attribution':'©GeoBasis-DE / LVermGeoRP2026, dl-de/by-2-0; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL (boundary and building masks)'}},'geometricError':100,'root':{'boundingVolume':{'region':[math.radians(min(xs)),math.radians(min(ys)),math.radians(max(xs)),math.radians(max(ys)),minh-1,max(maxh,max(r['ground_height_basemap_m'] for r in rows)+15)+1]},'geometricError':100,'refine':'ADD','children':children}}
 name='tileset.json' if variant=='uniform' else 'tileset-estimated.json';(tile_root/name).write_text(json.dumps(document,separators=(',',':')))
 print(variant,'cells',len(children),'trees',len(rows),flush=True)
print('GLB files',len(list(tile_root.rglob('*.glb'))),'total bytes',sum(f.stat().st_size for f in tile_root.rglob('*') if f.is_file()),flush=True)
