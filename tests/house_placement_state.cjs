// Run with node tests/house_placement_state.cjs. Exercise placement controls without WebGL.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const source=fs.readFileSync('basemap3d/assets/scene.js','utf8');
const code=source.slice(source.indexOf('function setupHousePlacement('),source.indexOf('async function main(){'));
const elements=new Map();
const templateButtons=['flat','gable','hip','grass'].map(kind=>({dataset:{houseTemplate:kind},innerHTML:kind,attrs:{},setAttribute(key,value){this.attrs[key]=value;}}));
const document={getElementById(id){if(!elements.has(id))elements.set(id,{value:id==='house-template'?'flat':id==='house-scale'?'100':'0',querySelectorAll:()=>templateButtons});return elements.get(id);}};
const C={Cartesian3:class {constructor(x,y,z){Object.assign(this,{x,y,z});}static fromRadians(){return {}; }},
 Transforms:{eastNorthUpToFixedFrame:()=>({})},Matrix4:{multiplyByPoint:(_,p)=>p},
 Cartographic:{fromCartesian:p=>p},Color:{fromCssColorString:color=>({color,withAlpha:alpha=>({color,alpha})}),DARKSLATEGRAY:'outline'},ShadowMode:{ENABLED:1},HeightReference:{CLAMP_TO_GROUND:1},ClassificationType:{TERRAIN:1}};
const context={document,Cesium:C};vm.createContext(context);vm.runInContext(code,context);
let entities=new Set(),hit={longitude:.1,latitude:.8,height:100};
const viewer={entities:{add:e=>(entities.add(e),e),remove:e=>entities.delete(e)},camera:{getPickRay:()=>({})},scene:{globe:{pick:()=>hit,getHeight:()=>100},requestRender(){}}};
context.setupHousePlacement(viewer,true);
const el=id=>document.getElementById('house-'+id);
assert.equal(viewer.placeHouseAt({}),false);
el('start').onclick();hit=null;assert.equal(viewer.placeHouseAt({}),true);assert.equal(entities.size,0);
hit={longitude:.1,latitude:.8,height:100};viewer.placeHouseAt({});assert.equal(entities.size,5);
const extent=()=>{const coords=[...entities].flatMap(e=>e.polygon.hierarchy);return {x:Math.max(...coords.map(p=>p.x))-Math.min(...coords.map(p=>p.x)),y:Math.max(...coords.map(p=>p.y))-Math.min(...coords.map(p=>p.y)),z:Math.max(...coords.map(p=>p.z))};};
assert.deepEqual(extent(),{x:16,y:12,z:9});
el('scale').value='150';el('scale').oninput();assert.deepEqual(extent(),{x:24,y:18,z:13.5});
el('angle').value='90';el('angle').oninput();assert(Math.abs(extent().x-18)<1e-8);assert(Math.abs(extent().y-24)<1e-8);
el('angle').value='0';el('angle').oninput();el('scale').value='100';el('scale').oninput();
templateButtons[1].onclick();assert.equal(el('template').value,'gable');assert.equal(el('picker').open,false);assert.equal(templateButtons[1].attrs['aria-pressed'],'true');assert.equal(templateButtons[0].attrs['aria-pressed'],'false');assert.equal(entities.size,8);
el('angle').value='90';el('angle').oninput();assert.equal(entities.size,8);
el('confirm').onclick();assert([...entities].every(e=>e.polygon.material.color==='#e4b847'));
for(const type of ['flat','hip']){el('template').value=type;el('start').onclick();viewer.placeHouseAt({});el('confirm').onclick();}
assert.equal(entities.size,21);el('undo').onclick();assert.equal(entities.size,13);
el('start').onclick();viewer.placeHouseAt({});el('cancel').onclick();assert.equal(entities.size,13);
el('undo').onclick();el('undo').onclick();assert.equal(entities.size,0);assert.equal(el('undo').disabled,true);
templateButtons[3].onclick();el('angle').value='0';el('start').onclick();viewer.placeHouseAt({});
assert.equal(entities.size,75);assert.deepEqual(extent(),{x:12,y:8,z:.75});
const patch=[...entities][0];assert.equal(patch.polygon.perPositionHeight,true);assert(patch.polygon.hierarchy.every(p=>p.z===.3));
el('scale').value='150';el('scale').oninput();assert.equal(extent().x,18);assert.equal(extent().y,12);
el('angle').value='90';el('angle').oninput();assert(Math.abs(extent().x-12)<1e-8);assert(Math.abs(extent().y-18)<1e-8);
el('confirm').onclick();assert([...entities].every(e=>e.polygon.material.color!=='#e4b847'));assert.equal([...entities][0].polygon.material.color,'#69994d');
// Switching back to a building must not recolor the confirmed grass.
templateButtons[0].onclick();assert.equal([...entities][0].polygon.material.color,'#69994d');
el('undo').onclick();assert.equal(entities.size,0);
el('scale').value='500';el('larger').onclick();assert.equal(el('scale').value,'500');
el('scale').value='80';el('smaller').onclick();assert.equal(el('scale').value,'80');
context.setupHousePlacement(viewer,false);el('start').onclick();assert.equal(viewer.placeHouseAt({}),false);
console.log('Placement state checks passed: pictured building/grass picker, raised turf base, terrain sampling and preserved colors, scale bounds, scale-before-rotation geometry, confirm, cancel, undo, missed ground and unavailable terrain.');
