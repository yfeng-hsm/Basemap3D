import fs from 'node:fs';import path from 'node:path';import vm from 'node:vm';import assert from 'node:assert/strict';import * as streams from 'node:stream/web';import {createRequire} from 'node:module';
const require=createRequire(import.meta.url),validator=require('./validation/node_modules/gltf-validator');
const base='/workspace/scratch/abdac7037c05/center-c/output',dir=base+'/mainz-center-trees',rows=JSON.parse(fs.readFileSync(base+'/tree_attributes.json','utf8')),byId=new Map(rows.map(r=>[r.tree_id,r]));
const context={console,setTimeout,clearTimeout,URL,Blob,TextEncoder,TextDecoder,Buffer,atob,btoa,performance,AbortController,fetch,...streams};context.self=context;context.global=context;vm.createContext(context);vm.runInContext(fs.readFileSync('/workspace/sites/mainz-tree-viewer/dist/vendor/cesium/Cesium.js','utf8'),context);const C=context.Cesium;
function parse(b){const n=b.readUInt32LE(12),j=JSON.parse(b.subarray(20,20+n).toString());return {j,bin:b.subarray(28+n)};}
function values(j,bin,index){const a=j.accessors[index],v=j.bufferViews[a.bufferView],o=v.byteOffset+(a.byteOffset||0),types={5126:Float32Array,5123:Uint16Array,5125:Uint32Array},width={SCALAR:1,VEC3:3,VEC4:4}[a.type];return new types[a.componentType](bin.buffer,bin.byteOffset+o,a.count*width);}
let fileCount=0,totalInstances=0,maxHeightError=0,maxPositionError=0,warnings=[];
for(const entry of ['tileset.json','tileset-estimated.json']){
 const t=JSON.parse(fs.readFileSync(dir+'/'+entry,'utf8'));assert.equal(t.asset.version,'1.1');assert.equal(t.root.children.length,9);const seen=new Set();
 for(const child of t.root.children){
  const matrix=C.Matrix4.fromArray(child.transform),files=[child.content.uri,child.children[0].content.uri];
  for(const [lod,file] of files.entries()){
   const b=fs.readFileSync(dir+'/'+file),report=await validator.validateBytes(new Uint8Array(b),{maxIssues:100,ignoredIssues:['UNSUPPORTED_EXTENSION']});
   assert.equal(report.issues.numErrors,0,JSON.stringify({file,messages:report.issues.messages}));fileCount++;
   const {j,bin}=parse(b),ext=j.extensions.EXT_structural_metadata,table=ext.propertyTables[0],props=table.properties,n=table.count;
   const offsetsView=j.bufferViews[props.tree_id.stringOffsets],offsets=new Uint32Array(bin.buffer,bin.byteOffset+offsetsView.byteOffset,n+1),strView=j.bufferViews[props.tree_id.values],strings=bin.subarray(strView.byteOffset,strView.byteOffset+strView.byteLength);
   const attributes=j.nodes[0].extensions.EXT_mesh_gpu_instancing.attributes,translations=values(j,bin,attributes.TRANSLATION),scales=values(j,bin,attributes.SCALE);
   assert.equal(j.accessors[attributes.TRANSLATION].count,n);assert.equal(j.nodes[0].extensions.EXT_instance_features.featureIds[0].propertyTable,0);
   for(let i=0;i<n;i++){
    const id=strings.subarray(offsets[i],offsets[i+1]).toString(),r=byId.get(id);assert.ok(r,id);
    const world=C.Matrix4.multiplyByPoint(matrix,new C.Cartesian3(translations[i*3],-translations[i*3+2],translations[i*3+1]),new C.Cartesian3()),geo=C.Cartographic.fromCartesian(world);
    const err=Math.max(Math.abs(C.Math.toDegrees(geo.longitude)-r.longitude),Math.abs(C.Math.toDegrees(geo.latitude)-r.latitude));maxPositionError=Math.max(maxPositionError,err);maxHeightError=Math.max(maxHeightError,Math.abs(geo.height-r.ground_height_basemap_m));assert.ok(err<1e-8);assert.ok(Math.abs(geo.height-r.ground_height_basemap_m)<.01);const positions=j.meshes.map(m=>values(j,bin,m.primitives[0].attributes.POSITION));
    const width=Math.max(...positions.map(a=>{let lo=Infinity,hi=-Infinity;for(let k=0;k<a.length;k+=3){lo=Math.min(lo,a[k]);hi=Math.max(hi,a[k]);}return hi-lo;}));
    const depth=Math.max(...positions.map(a=>{let lo=Infinity,hi=-Infinity;for(let k=2;k<a.length;k+=3){lo=Math.min(lo,a[k]);hi=Math.max(hi,a[k]);}return hi-lo;}));
    const unitMin=Math.min(...positions.map(a=>{let v=Infinity;for(let k=1;k<a.length;k+=3)v=Math.min(v,a[k]);return v;}));
    const unitMax=Math.max(...positions.map(a=>{let v=-Infinity;for(let k=1;k<a.length;k+=3)v=Math.max(v,a[k]);return v;}));
    assert.ok(Math.abs(scales[i*3]*Math.max(width,depth)-r.crown_diameter_equivalent_m)<1e-4);
    assert.ok(Math.abs(scales[i*3+1]*(unitMax-unitMin)-(entry==='tileset.json'?15:r.height_m))<1e-4);
    assert.ok(Math.abs(scales[i*3+2]-scales[i*3])<1e-6);
    assert.ok(Math.abs(unitMin)<1e-5); 
    if(lod===0)seen.add(id);
   }
   if(lod===0)totalInstances+=n;
  }
 }
 assert.equal(seen.size,rows.length);
}
console.log(JSON.stringify({glb_files_validated:fileCount,trees_per_variant:rows.length,total_instances_two_variants:totalInstances,max_position_error_degrees:maxPositionError,max_ground_height_error_m:maxHeightError,all_gltf_validation_errors:0}));
