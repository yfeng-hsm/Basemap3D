// Run with node tests/house_placement_state.cjs. Exercise placement controls without WebGL.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('basemap3d/assets/scene.js','utf8');
const code=source.slice(source.indexOf('function setupHousePlacement('),source.indexOf('async function main(){'));
const elements=new Map();
const document={getElementById(id){if(!elements.has(id))elements.set(id,{value:id==='house-template'?'flat':'0'});return elements.get(id);}};
const C={Cartesian3:class {constructor(x,y,z){Object.assign(this,{x,y,z});}static fromRadians(){return {}; }},
 Transforms:{eastNorthUpToFixedFrame:()=>({})},Matrix4:{multiplyByPoint:(_,p)=>p},
 Cartographic:{fromCartesian:p=>p},Color:{CYAN:{withAlpha:()=> 'preview'},WHITE:'white',DARKSLATEGRAY:'outline'},ShadowMode:{ENABLED:1}};
const context={document,Cesium:C};vm.createContext(context);vm.runInContext(code,context);
let entities=new Set(),hit={longitude:.1,latitude:.8,height:100};
const viewer={entities:{add:e=>(entities.add(e),e),remove:e=>entities.delete(e)},camera:{getPickRay:()=>({})},scene:{globe:{pick:()=>hit},requestRender(){}}};
context.setupHousePlacement(viewer,true);
const el=id=>document.getElementById('house-'+id);
assert.equal(viewer.placeHouseAt({}),false);
el('start').onclick();hit=null;assert.equal(viewer.placeHouseAt({}),true);assert.equal(entities.size,0);
hit={longitude:.1,latitude:.8,height:100};viewer.placeHouseAt({});assert.equal(entities.size,5);
el('template').value='gable';el('template').onchange();assert.equal(entities.size,8);
el('angle').value='90';el('angle').oninput();assert.equal(entities.size,8);
el('confirm').onclick();assert([...entities].every(e=>e.polygon.material==='white'));
for(const type of ['flat','hip']){el('template').value=type;el('start').onclick();viewer.placeHouseAt({});el('confirm').onclick();}
assert.equal(entities.size,21);el('undo').onclick();assert.equal(entities.size,13);
el('start').onclick();viewer.placeHouseAt({});el('cancel').onclick();assert.equal(entities.size,13);
el('undo').onclick();el('undo').onclick();assert.equal(entities.size,0);assert.equal(el('undo').disabled,true);
context.setupHousePlacement(viewer,false);el('start').onclick();assert.equal(viewer.placeHouseAt({}),false);
console.log('Placement state checks passed: three templates, rotation, confirm, cancel, undo, missed ground and unavailable terrain.');
