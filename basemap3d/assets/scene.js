(()=>{
const originalSceneHTML=document.documentElement.outerHTML;

const config = __CONFIG_JSON__;
const geojson = __GEOJSON_JSON__;
geojson.features.forEach((f,i)=>{f.properties._basemap_object_index=i;});
const buildingFootprints = __BUILDINGS_JSON__;
const barRows = __BARS_JSON__;
const status = document.getElementById('status');
document.getElementById('title').textContent = config.title;
document.title = config.title;
const available={2:config.has_raster,3:config.has_vector,4:config.query_enabled,5:config.sun_enabled};
document.querySelectorAll('[data-min-task]').forEach(node=>{node.hidden=!available[Number(node.dataset.minTask)];});
document.getElementById('stage-description').textContent=(config.tiles3d_layers?.length && !config.has_vector && !config.bars_enabled)?'Hosted 3D layers · Terrain and city model':config.stage_description;
if(!config.has_vector)document.getElementById('overview').textContent=config.bars_enabled?'3D columns':'Overview';
if(config.bars_enabled)document.getElementById('top').textContent='2D distribution';
if(!config.has_vector)document.querySelector('.hint').textContent='Drag to pan · Scroll to zoom · Ctrl + drag to tilt / rotate';

// Controls are grouped by capability, independently of teaching-task order.
const panel=document.querySelector('.panel');
document.getElementById('stage-description').hidden=true;
const group=(title)=>{const section=document.createElement('section');section.className='control-group';const h=document.createElement('h2');h.textContent=title;section.append(h);panel.append(section);return section;};
const layersGroup=group('Layers');
const buildingRow=document.createElement('label');buildingRow.className='layer-row';
const buildingCheck=document.createElement('input');buildingCheck.type='checkbox';buildingCheck.checked=config.buildings_enabled;buildingCheck.disabled=true;
buildingRow.append(buildingCheck,document.createTextNode(' 3D buildings'));buildingRow.hidden=!config.buildings_enabled;layersGroup.append(buildingRow);
const buildingHint=document.createElement('p');buildingHint.className='layer-description';buildingHint.hidden=!config.buildings_enabled;buildingHint.textContent='basemap.de · LoD2 building models.';layersGroup.append(buildingHint);
const tilesPanel=document.getElementById('tiles3d-panel');layersGroup.append(tilesPanel);tilesPanel.querySelector('p').hidden=true;
document.getElementById('tiles3d-details').hidden=true;
const wmsControls=document.createElement('div');wmsControls.id='wms-controls';layersGroup.append(wmsControls);
document.getElementById('raster-opacity').parentElement.hidden=true;
document.getElementById('aerial').parentElement.hidden=true;
const fillSection=document.getElementById('fill').closest('section');layersGroup.append(fillSection);
setupPolygonUpload();
const sunSection=document.getElementById('sun-date').closest('section');sunSection.classList.add('control-group');
const sunHeading=document.createElement('h2');sunHeading.textContent='Light & shadows';sunSection.prepend(sunHeading);
const sunRow=document.createElement('label');sunRow.className='layer-row';
const sunCheck=document.createElement('input');sunCheck.type='checkbox';sunCheck.checked=true;
sunRow.append(sunCheck,document.createTextNode(' Show shadows'));sunHeading.after(sunRow);panel.append(sunSection);
const viewGroup=group('View');viewGroup.append(document.getElementById('overview').parentElement);
document.getElementById('toggle').hidden=true;
const querySection=document.getElementById('nearby-toggle').closest('section');panel.append(querySection);
const legendSection=document.getElementById('legend').closest('section');fillSection.append(legendSection);
document.getElementById('details').textContent='';document.getElementById('source-link').hidden=true;
panel.append(document.getElementById('bars-panel'),document.getElementById('status'));
const warnings = [];
function report(){status.textContent=warnings.join('\n');status.hidden=!warnings.length;}
// Implementation detail for the teaching renderer.
function coordinatePairs(coords){return typeof coords[0]==='number'?[coords]:coords.flatMap(coordinatePairs);}
const queryPoints=geojson.features.flatMap(f=>coordinatePairs(f.geometry.coordinates));
const queryLon=queryPoints.length?queryPoints.reduce((v,p)=>v+p[0],0)/queryPoints.length:config.center[0];
const queryLat=queryPoints.length?queryPoints.reduce((v,p)=>v+p[1],0)/queryPoints.length:config.center[1];
const localScaleX=111320*Math.cos(queryLat*Math.PI/180), localScaleY=111320;
function metricPolygon(polygon){return polygon.map(ring=>ring.map(p=>[(p[0]-queryLon)*localScaleX,(p[1]-queryLat)*localScaleY]));}
function polygonParts(geometry){return geometry.type==='Polygon'?[geometry.coordinates]:geometry.coordinates;}
function pointInRing(p,ring){
 let inside=false;
 for(let i=0,j=ring.length-1;i<ring.length;j=i++){
  const a=ring[i],b=ring[j];
  if((a[1]>p[1])!==(b[1]>p[1]) && p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
 }
 return inside;
}
function pointInPolygon(p,polygon){return pointInRing(p,polygon[0])&&!polygon.slice(1).some(hole=>pointInRing(p,hole));}
function pointSegmentDistance(p,a,b){
 const dx=b[0]-a[0],dy=b[1]-a[1];
 const t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));
 return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
}
function cross(a,b,c){return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);}
function segmentDistance(a,b,c,d){
 const ac=cross(a,b,c),ad=cross(a,b,d),ca=cross(c,d,a),cb=cross(c,d,b);
 if(((ac>0&&ad<0)||(ac<0&&ad>0))&&((ca>0&&cb<0)||(ca<0&&cb>0)))return 0;
 return Math.min(pointSegmentDistance(a,c,d),pointSegmentDistance(b,c,d),pointSegmentDistance(c,a,b),pointSegmentDistance(d,a,b));
}
function polygonDistance(a,b){
 if(pointInPolygon(a[0][0],b)||pointInPolygon(b[0][0],a))return 0;
 let best=Infinity;
 for(const ra of a)for(const rb of b)for(let i=0;i<ra.length-1;i++)for(let j=0;j<rb.length-1;j++){
  best=Math.min(best,segmentDistance(ra[i],ra[i+1],rb[j],rb[j+1]));
  if(best<1e-7)return 0;
 }
 return best;
}
function setupNearbyHighlight(viewer,buildings){
 const toggle=document.getElementById('nearby-toggle');
 const slider=document.getElementById('nearby-distance');
 const output=document.getElementById('nearby-value');
 const count=document.getElementById('nearby-count');
 const plots=geojson.features.flatMap(f=>polygonParts(f.geometry).map(metricPolygon));
 const candidates=buildingFootprints.features.map(feature=>{
  const polygons=polygonParts(feature.geometry).map(metricPolygon);
  let distance=Infinity;
  for(const a of polygons)for(const b of plots)distance=Math.min(distance,polygonDistance(a,b));
  return {feature,distance};
 }).filter(x=>x.distance<=config.nearby_max_distance_m);
 let layer=null,lastDistance=-1,timer;
 const gold=Cesium.Color.fromCssColorString('#ffc04d').withAlpha(0.8);
 function hierarchy(polygon){
  const positions=ring=>Cesium.Cartesian3.fromDegreesArray(ring.slice(0,-1).flatMap(p=>p.slice(0,2)));
  return new Cesium.PolygonHierarchy(positions(polygon[0]),polygon.slice(1).map(hole=>new Cesium.PolygonHierarchy(positions(hole))));
 }
 function update(){
  const distance=Number(slider.value);
  output.textContent=distance+' m';
  if(!toggle.checked){
   if(layer)layer.show=false;
   count.textContent='Disabled. The selection applies to all '+geojson.features.length+' Polygons.';
   viewer.scene.requestRender();return;
  }
  const selected=candidates.filter(x=>x.distance<=distance+1e-7);
  if(lastDistance!==distance){
   if(layer){viewer.scene.primitives.remove(layer);layer=null;}
// Implementation detail for the teaching renderer.
   const instances=selected.flatMap(({feature})=>polygonParts(feature.highlight_geometry || feature.geometry).map(polygon=>new Cesium.GeometryInstance({
    geometry:new Cesium.PolygonGeometry({polygonHierarchy:hierarchy(polygon),height:-100,extrudedHeight:1000,
     vertexFormat:Cesium.PerInstanceColorAppearance.VERTEX_FORMAT}),
    attributes:{color:Cesium.ColorGeometryInstanceAttribute.fromColor(gold)}
   })));
   if(instances.length)layer=viewer.scene.primitives.add(new Cesium.ClassificationPrimitive({
    geometryInstances:instances,classificationType:Cesium.ClassificationType.CESIUM_3D_TILE,
    allowPicking:false,asynchronous:true
   }));
   lastDistance=distance;
  }
  if(layer)layer.show=true;
  count.textContent='All '+geojson.features.length+' Polygons: '+selected.length+' OSM building footprints selected. '+config.query_source_label+'.';
  viewer.scene.requestRender();
 }
 toggle.disabled=false;slider.disabled=false;
 toggle.checked=config.highlight_nearby;
 slider.max=String(config.nearby_max_distance_m);
 slider.value=String(config.nearby_distance_m);
 output.textContent=slider.value+' m';
 toggle.addEventListener('change',()=>{clearTimeout(timer);update();});
 slider.addEventListener('input',()=>{output.textContent=slider.value+' m';clearTimeout(timer);timer=setTimeout(update,120);});
// Implementation detail for the teaching renderer.
 update();
}

function setupBars(viewer){
 document.getElementById('bars-panel').hidden=false;
 document.getElementById('bars-title').textContent=config.bar_legend_title;
 document.getElementById('bar-reading').textContent='Darker and taller = more '+config.bar_unit+'. The top view shows spatial patterns without overlap.';
 document.getElementById('bar-credit').textContent=config.bar_attribution+' · ';
 const heightSlider=document.getElementById('bar-height');
 const minimumSlider=document.getElementById('bar-minimum');
 heightSlider.min=String(config.bar_height_scale/10);
 heightSlider.step=String(config.bar_height_scale/10);
 heightSlider.max=String(config.bar_height_scale*4);
 heightSlider.value=String(config.bar_height_scale);
 const values=barRows.map(row=>row.value).sort((a,b)=>a-b);
 const maximum=values[values.length-1];
 minimumSlider.max=String(Math.ceil(maximum/100)*100);
 minimumSlider.step=String(Math.max(1,Math.round(maximum/250)));
 const breaks=[...new Set([0.2,0.4,0.6,0.8].map(q=>values[Math.floor(q*(values.length-1))]))];
 const palette=['#c6dbef','#6baed6','#4292c6','#2171b5','#08306b'];
 const format=n=>n.toLocaleString('en-GB',{maximumFractionDigits:2});
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const colorFor=value=>palette[Math.min(palette.length-1,breaks.filter(v=>value>v).length)];
 const dataset=new Cesium.CustomDataSource('Thematic columns');
 viewer.dataSources.add(dataset);
 const columns=barRows.map(row=>{
  const height=Math.max(0.1,row.value*config.bar_height_scale);
  return dataset.entities.add({
   name:row.name,
   position:Cesium.Cartesian3.fromDegrees(row.longitude,row.latitude,height/2),
   properties:{kind:'bar',value:row.value},
   box:{dimensions:new Cesium.Cartesian3(config.bar_width_m,config.bar_width_m,height),
    heightReference:Cesium.HeightReference.RELATIVE_TO_GROUND,
    material:Cesium.Color.fromCssColorString(colorFor(row.value)).withAlpha(config.bar_opacity),
    outline:false,shadows:Cesium.ShadowMode.DISABLED},
   description:'<table class="cesium-infoBox-defaultTable"><tbody>'+
    '<tr><th>Grid cell</th><td>'+escape(row.name)+'</td></tr>'+
    '<tr><th>'+escape(config.bar_legend_title)+'</th><td>'+format(row.value)+' '+escape(config.bar_unit)+'</td></tr>'+
    '<tr><th>Reference date</th><td>'+escape(row.reference_date || 'See data source')+'</td></tr>'+
    '<tr><th>Display</th><td>Thematic column, not building height.</td></tr></tbody></table>'
  });
 });
 const legend=document.getElementById('bar-legend');
 for(let i=0;i<=breaks.length;i++){
  const row=document.createElement('div');row.className='item';
  const dot=document.createElement('span');dot.className='swatch';dot.style.background=palette[i];
  const label=document.createElement('span');
  label.textContent=(i===0?'≤ '+format(breaks[0]):i===breaks.length?'> '+format(breaks[i-1]):'> '+format(breaks[i-1])+' – ≤ '+format(breaks[i]))+' '+config.bar_unit;
  row.append(dot,label);legend.append(row);
 }
 function update(){
  const factor=Number(heightSlider.value),minimum=Number(minimumSlider.value);
  let shown=0;
  columns.forEach((entity,i)=>{
   const row=barRows[i],height=Math.max(0.1,row.value*factor);
   entity.show=row.value>=minimum;
   if(entity.show)shown++;
   entity.position=Cesium.Cartesian3.fromDegrees(row.longitude,row.latitude,height/2);
   entity.box.dimensions=new Cesium.Cartesian3(config.bar_width_m,config.bar_width_m,height);
  });
  document.getElementById('bar-height-value').textContent=format(factor)+' m / unit';
  document.getElementById('bar-minimum-value').textContent=format(minimum)+' '+config.bar_unit;
  document.getElementById('bar-count').textContent=shown+' of '+barRows.length+' columns visible. Colors use fixed quantile classes for the loaded dataset.';
  viewer.scene.requestRender();
 }
 heightSlider.addEventListener('input',update);
 minimumSlider.addEventListener('input',update);
 update();
}

function showTileFeature(viewer, picked){
 if(!picked || typeof picked.getPropertyIds!=='function')return false;
 const esc=value=>String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const tree=picked.getProperty('tree_id');
 const labels={tree_id:'Tree ID',model_height_m:'Model height (m)',source_height_m:'Estimated tree height (m)',ground_height_m:'DGM5 ground height (m)',needs_review:'Review recommended'};
 const ids=tree?Object.keys(labels):picked.getPropertyIds().slice(0,30);
 const rows=ids.map(id=>{let value=picked.getProperty(id);if(value===undefined)return '';
  if(typeof value==='number')value=value.toLocaleString('en-GB',{maximumFractionDigits:2});
  if(id==='needs_review')value=Boolean(picked.getProperty(id));
  if(typeof value==='boolean')value=value?'Ja':'Nein';
  return '<tr><th>'+esc(labels[id] || id)+'</th><td>'+esc(value)+'</td></tr>';
 }).join('');
 const name=tree?'Tree '+tree:'3D object';
 viewer.selectedEntity=new Cesium.Entity({name,description:'<table class="cesium-infoBox-defaultTable"><tbody>'+rows+'</tbody></table>'+(tree?'<p>Automatically detected candidate; schematic model, not a verified tree inventory.</p>':'')});
 document.getElementById('tiles3d-details').textContent=tree?name+' · Model height '+Number(picked.getProperty('model_height_m')).toLocaleString('en-GB',{maximumFractionDigits:2})+' m · '+(picked.getProperty('needs_review')?'Manual review recommended.':'Automatically detected candidate.'):name;
 return true;
}

function setupWmsLayers(viewer){
 const options=config.raster_layers||(config.has_raster?[{url:config.raster_url,layers:config.raster_layer,opacity:config.raster_opacity,name:'Raster',show:true,crs:'EPSG:4326'}]:[]);
 const credits=new Set();
 for(const [index,option] of options.entries()){
  const box=document.createElement('section');box.className='wms-layer';
  const label=document.createElement('label');label.className='layer-row';
  const check=document.createElement('input');check.type='checkbox';check.checked=option.show!==false;
  label.append(check,document.createTextNode(' '+option.name));box.append(label);
  if(option.description){const note=document.createElement('p');note.className='layer-description';note.textContent=option.description;box.append(note);}
  const opacityLabel=document.createElement('label');opacityLabel.htmlFor='wms-opacity-'+index;opacityLabel.textContent='Opacity ';
  const output=document.createElement('output');opacityLabel.append(output);box.append(opacityLabel);
  const slider=document.createElement('input');slider.type='range';slider.id='wms-opacity-'+index;slider.min='0';slider.max='100';slider.step='1';slider.value=String(Math.round(option.opacity*100));slider.setAttribute('aria-label',option.name+' · Opacity');box.append(slider);
  if(option.legend_url){const details=document.createElement('details');const summary=document.createElement('summary');summary.textContent='Legend';const image=document.createElement('img');image.alt=option.name+' · Legend';image.src=option.legend_url;details.append(summary,image);box.append(details);}
  wmsControls.append(box);
  const parameters={version:option.version||'1.1.1',format:option.format||'image/png',transparent:option.transparent!==false,styles:option.styles||''};
  const settings={url:option.url,layers:option.layers,parameters,credit:option.attribution||'',enablePickFeatures:false,
   tilingScheme:option.crs==='EPSG:3857'?new Cesium.WebMercatorTilingScheme():new Cesium.GeographicTilingScheme()};
  if(option.bounds)settings.rectangle=Cesium.Rectangle.fromDegrees(...option.bounds);
  const provider=new Cesium.WebMapServiceImageryProvider(settings);
  const layer=viewer.imageryLayers.addImageryProvider(provider);layer.show=check.checked;
  if(option.attribution)credits.add(option.attribution);
  check.onchange=()=>{layer.show=check.checked;viewer.scene.requestRender();};
  slider.oninput=()=>{layer.alpha=Number(slider.value)/100;output.textContent=slider.value+'%';viewer.scene.requestRender();};slider.oninput();
  let failed=false;provider.errorEvent.addEventListener(()=>{if(!failed){failed=true;warnings.push(option.name+': Raster tiles failed to load. Check the service and extent.');report();}});
 }
 document.getElementById('imagery-credit').textContent=credits.size?[...credits].join(' · ')+' · ':'';
}

async function setupTiles3D(viewer, terrainEnabled){
 const layers=config.tiles3d_layers || [];
 if(!layers.length)return;
 document.getElementById('tiles3d-panel').hidden=false;
 document.getElementById('tiles3d-credit').textContent=[...new Set(layers.map(x=>x.attribution).filter(Boolean))].join(' · ')+' · ';
 await Promise.all(layers.map(async option=>{
  const box=document.createElement('div');
  const label=document.createElement('label');
  const visible=document.createElement('input');visible.type='checkbox';visible.checked=option.show;
  label.append(visible,document.createTextNode(' '+option.name));box.append(label);
  box.className='layer-entry';label.className='layer-row';
  let selector;
  if(option.variants){
   selector=document.createElement('select');selector.setAttribute('aria-label',option.name+' · Height mode');
   for(const [value,url] of Object.entries(option.variants)){
    const item=document.createElement('option');item.value=value;item.textContent=value==='uniform'?'Uniform height · 15 m':'Estimated tree height';selector.append(item);
   }
   selector.value=option.variant;box.append(selector);
  }
  const fit=document.createElement('button');fit.textContent='⌖';fit.title='Zoom to layer';fit.setAttribute('aria-label',option.name+' · Zoom to layer');fit.className='layer-fit';fit.disabled=true;const layerHeader=document.createElement('div');layerHeader.className='layer-header';label.replaceWith(layerHeader);layerHeader.append(label,fit);
  if(option.feature_id_label==='tree'){
   const hint=document.createElement('p');hint.className='layer-description';hint.textContent='Estimated trees and heights for visualization; not a precise survey.';layerHeader.after(hint);
  }
  const state=document.createElement('p');state.className='shadow-note';state.textContent='Loading layer …';box.append(state);
  document.getElementById('tiles3d-controls').append(box);
  if(option.require_terrain && !terrainEnabled){
   state.textContent='This layer requires basemap.de DGM5 terrain. Check the connection and reload.';
   visible.disabled=true;if(selector)selector.disabled=true;return;
  }
  let current=null;
  visible.onchange=()=>{if(current)current.show=visible.checked;viewer.scene.requestRender();};
  fit.onclick=()=>{if(current)viewer.camera.flyToBoundingSphere(current.boundingSphere,{duration:0.8,offset:new Cesium.HeadingPitchRange(Cesium.Math.toRadians(25),Cesium.Math.toRadians(-45),0)});};
  async function load(url){
   if(selector)selector.disabled=true;state.textContent='Loading layer …';
   try{
    const settings={maximumScreenSpaceError:option.maximum_screen_space_error};
    if(option.feature_id_label)settings.instanceFeatureIdLabel=option.feature_id_label;
    const next=await Cesium.Cesium3DTileset.fromUrl(url,settings);
    next.show=visible.checked;next.shadows=config.sun_enabled?Cesium.ShadowMode.CAST_ONLY:Cesium.ShadowMode.DISABLED;
    viewer.scene.primitives.add(next);
    if(current)viewer.scene.primitives.remove(current);
    current=next;fit.disabled=false;state.textContent='';
    next.allTilesLoaded.addEventListener(()=>{state.textContent='';});
    next.tileFailed.addEventListener(()=>{state.textContent='A tile is missing. Check the network and reload.';});
    viewer.scene.requestRender();
   }catch(error){state.textContent='Could not load layer: '+error.message;}
   finally{if(selector)selector.disabled=false;}
  }
  if(selector)selector.onchange=()=>load(option.variants[selector.value]);
  await load(option.relative_url && /^https?:$/.test(location.protocol)?new URL(option.relative_url,location.href).href:option.url);
 }));
}


function setupHousePlacement(viewer, terrainEnabled){
 const panel=document.getElementById('house-panel');panel.hidden=false;
 const el=id=>document.getElementById('house-'+id);
 const buildingColor=Cesium.Color.fromCssColorString('#e4b847');
 const templateButtons=panel.querySelectorAll('[data-house-template]');
 const templates={flat:{w:16,d:12,h:9,r:0},gable:{w:12,d:9,h:6,r:3},hip:{w:14,d:10,h:6,r:3},grass:{w:12,d:8,h:.45,r:0}};
 let choosing=false,anchor=null,preview=[],placed=[],serial=0;
 const status=text=>{el('status').textContent=text;};
 const remove=group=>group.forEach(entity=>viewer.entities.remove(entity));
 function controls(){el('confirm').disabled=!anchor;el('cancel').disabled=!choosing&&!anchor;el('undo').disabled=!placed.length;el('start').textContent=choosing?'Click open ground…':'Choose location';}
 function draw(){
  const kind=el('template').value,t=templates[kind],a=Number(el('angle').value)*Math.PI/180,scale=Number(el('scale').value)/100;
  el('scale-value').textContent=Math.round(scale*100)+'%';
  el('dimensions').textContent=(t.w*scale).toFixed(1)+' × '+(t.d*scale).toFixed(1)+' m · height '+((t.h+t.r)*scale).toFixed(2)+' m';
  remove(preview);preview=[];if(!anchor)return;
  const frame=Cesium.Transforms.eastNorthUpToFixedFrame(Cesium.Cartesian3.fromRadians(anchor.longitude,anchor.latitude,anchor.height));
  const point=([x,y,z])=>Cesium.Matrix4.multiplyByPoint(frame,new Cesium.Cartesian3((x*Math.cos(a)-y*Math.sin(a))*scale,(x*Math.sin(a)+y*Math.cos(a))*scale,z*scale),new Cesium.Cartesian3());
  const x=t.w/2,y=t.d/2,h=t.h,top=[[-x,-y,h],[x,-y,h],[x,y,h],[-x,y,h]];
  const face=(coords,color=buildingColor,options={})=>{
   const entity=viewer.entities.add({name:kind==='grass'?'Grass preview':'Building preview',polygon:{hierarchy:coords.map(point),perPositionHeight:true,material:color.withAlpha(.78),outline:true,outlineColor:Cesium.Color.DARKSLATEGRAY,shadows:Cesium.ShadowMode.ENABLED,...options}});
   entity._placementColor=color;preview.push(entity);
  };
  if(kind==='grass'){
   const green=Cesium.Color.fromCssColorString('#69994d');
   face([[-x,-y,0],[x,-y,0],[x,y,0],[-x,y,0]],green,{perPositionHeight:false,heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,classificationType:Cesium.ClassificationType.TERRAIN,outline:false});
   // Crossed triangular tufts show low vegetation; the patch itself follows terrain.
   for(let row=0;row<5;row++)for(let col=0;col<7;col++){
    const cx=-x+(col+.5)*t.w/7,cy=-y+(row+.5)*t.d/5;
    const ground=viewer.scene.globe.getHeight(Cesium.Cartographic.fromCartesian(point([cx,cy,0])));
    const z=Number.isFinite(ground)?(ground-anchor.height)/scale:0;
    const blade=Cesium.Color.fromCssColorString((row+col)%2?'#54833f':'#82ac58');
    const height=t.h*(.7+((row*7+col)%5)*.075);
    face([[cx-.24,cy,z],[cx+.24,cy,z],[cx+.08,cy,z+height]],blade,{outline:false});
    face([[cx,cy-.24,z],[cx,cy+.24,z],[cx-.06,cy,z+height*.9]],blade,{outline:false});
   }
  }else{
  for(let i=0;i<4;i++){const j=(i+1)%4;face([[...top[i].slice(0,2),0],[...top[j].slice(0,2),0],top[j],top[i]]);}
  if(kind==='flat')face(top);
  else{
   const inset=kind==='hip'?t.w*.23:0,L=[-x+inset,0,h+t.r],R=[x-inset,0,h+t.r];
   face([top[0],top[1],R,L]);face([top[2],top[3],L,R]);face([top[3],top[0],L]);face([top[1],top[2],R]);
  }
  }
  viewer.scene.requestRender();controls();
 }
 viewer.placeHouseAt=position=>{
  if(!choosing)return false;
  const ray=viewer.camera.getPickRay(position),hit=ray&&viewer.scene.globe.pick(ray,viewer.scene);
  if(!hit){status('No ground at this point. Click visible ground.');return true;}
  anchor=Cesium.Cartographic.fromCartesian(hit);choosing=false;draw();status('Preview ready. Adjust scale or rotation, then confirm; choose location again to move.');return true;
 };
 el('start').onclick=()=>{
  if(!terrainEnabled){status('Terrain is unavailable. Reload when the terrain service is reachable.');return;}
  choosing=true;controls();status('Click an open space on the map to preview the selected model.');
 };
 templateButtons.forEach(button=>{button.onclick=()=>{
  el('template').value=button.dataset.houseTemplate;
  el('template-current').innerHTML=button.innerHTML;
  templateButtons.forEach(option=>option.setAttribute('aria-pressed',String(option===button)));
  el('picker').open=false;draw();
 };});
 el('template').onchange=draw;
 el('scale').oninput=draw;
 const resize=step=>{el('scale').value=String(Math.max(50,Math.min(200,Number(el('scale').value)+step)));draw();};
 el('smaller').onclick=()=>resize(-5);el('larger').onclick=()=>resize(5);
 el('angle').oninput=()=>{el('angle-value').textContent=el('angle').value+'°';draw();};
 el('confirm').onclick=()=>{
  if(!anchor)return;
  serial++;const label=el('template').value==='grass'?'Grass patch':'Building';preview.forEach(entity=>{entity.name=label+' '+serial;entity.polygon.material=entity._placementColor;});
  placed.push(preview);preview=[];anchor=null;choosing=false;controls();status('Model placed. Choose another location or undo the last placement.');viewer.scene.requestRender();
 };
 el('cancel').onclick=()=>{remove(preview);preview=[];anchor=null;choosing=false;controls();status('Preview cancelled.');viewer.scene.requestRender();};
 el('undo').onclick=()=>{if(placed.length)remove(placed.pop());controls();status('Last placed model removed.');viewer.scene.requestRender();};
 controls();draw();
}

async function main(){
 if(typeof Cesium==='undefined') throw new Error('Could not load CesiumJS. Check internet access and CDN availability.');
 Cesium.Ion.defaultAccessToken = '';
 if(config.bars_enabled)document.body.classList.add('population-mode');
 const viewer = new Cesium.Viewer('scene', {
   baseLayer:false, baseLayerPicker:false, geocoder:false,
   animation:false, timeline:false, homeButton:false, sceneModePicker:false,
   navigationHelpButton:false, fullscreenButton:false, infoBox:config.popup_enabled,
   selectionIndicator:false, shadows:config.sun_enabled, terrainShadows:config.sun_enabled?Cesium.ShadowMode.RECEIVE_ONLY:Cesium.ShadowMode.DISABLED, requestRenderMode:true
 });
 window.viewer = viewer;
 document.getElementById('toggle').hidden=true;
 viewer.clock.shouldAnimate=false;
 viewer.scene.light=new Cesium.SunLight();
 viewer.scene.globe.enableLighting=config.sun_enabled;
 viewer.shadowMap.softShadows=true;
 viewer.shadowMap.darkness=0.35;
 sunCheck.onchange=()=>{viewer.shadows=sunCheck.checked;viewer.scene.globe.enableLighting=sunCheck.checked;viewer.scene.requestRender();};
 const sunSlider=document.getElementById('sun-time');
 const sunDate=document.getElementById('sun-date');
 const berlinClock=new Intl.DateTimeFormat('en-GB',{
  timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',
  hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'
 });
 function updateSun(){
  if(!sunDate.value)return;
  const [year,month,day]=sunDate.value.split('-').map(Number);
  const minutes=Number(sunSlider.value);
  const hour=Math.floor(minutes/60),minute=minutes%60;
  const wallTime=Date.UTC(year,month-1,day,hour,minute);
// Implementation detail for the teaching renderer.
  let utc=wallTime;
  for(let i=0;i<3;i++){
   const p=Object.fromEntries(berlinClock.formatToParts(new Date(utc)).map(x=>[x.type,x.value]));
   const berlinAsUTC=Date.UTC(Number(p.year),Number(p.month)-1,Number(p.day),Number(p.hour),Number(p.minute),Number(p.second));
   utc+=wallTime-berlinAsUTC;
  }
  viewer.clock.currentTime=Cesium.JulianDate.fromDate(new Date(utc));
  document.getElementById('sun-value').textContent=String(hour).padStart(2,'0')+':'+String(minute).padStart(2,'0');
  viewer.scene.requestRender();
 }
 sunDate.value=config.sun_date;
 sunSlider.value=String(Math.round(config.sun_hour*4)*15);
 sunSlider.addEventListener('input',updateSun);
 sunDate.addEventListener('change',updateSun);
 updateSun();
 viewer.scene.globe.baseColor = Cesium.Color.fromCssColorString('#e4eaec');
 viewer.scene.backgroundColor = Cesium.Color.fromCssColorString('#e9f1f5');
 viewer.scene.globe.depthTestAgainstTerrain = false;
 viewer.scene.postProcessStages.fxaa.enabled = true;
 viewer.creditDisplay.addStaticCredit(new Cesium.Credit('© GeoBasis-DE/BKG 2026 · basemap.de | Adaptation: colors and teaching examples',true));
 if(config.bars_enabled)setupBars(viewer);
 const mapLayer=viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
  url:'https://sgx.geodatenzentrum.de/wms_basemapde',layers:'de_basemapde_web_raster_farbe',
  parameters:{version:'1.1.1',format:'image/png',transparent:true},credit:'© GeoBasis-DE/BKG 2026'
 }));
 if(config.bars_enabled){mapLayer.saturation=0;mapLayer.brightness=1.15;mapLayer.contrast=0.65;mapLayer.gamma=1.1;}
 setupWmsLayers(viewer);
 let mapFailed=false;
 mapLayer.imageryProvider.errorEvent.addEventListener(()=>{
  if(!mapFailed){mapFailed=true;warnings.push('Base map tiles failed to load. Check the network.');report();}
 });

// Implementation detail for the teaching renderer.
 const source = await Cesium.GeoJsonDataSource.load(geojson,{clampToGround:true});
 viewer.dataSources.add(source);
 for(const entity of source.entities.values){
  const props=entity.properties.getValue(viewer.clock.currentTime);
  const color=Cesium.Color.fromCssColorString(props.color);
  entity.polygon.material=color.withAlpha(config.opacity);
  entity.polygon.outline=false;
  entity.polygon.classificationType=Cesium.ClassificationType.TERRAIN;
  entity.name=props.name;
  const esc=value=>String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  entity.description='<table class="cesium-infoBox-defaultTable"><tbody>'+[
   ['Name',props.name],['OSM ID',props.osm_id || 'User data'],['Access (OSM)',props.access || 'Not specified'],['Description',props.note || 'User polygon']
  ].map(([key,value])=>'<tr><th>'+esc(key)+'</th><td>'+esc(value)+'</td></tr>').join('')+'</tbody></table>';
 }
 for(const feature of geojson.features){
  const color=Cesium.Color.fromCssColorString(feature.properties.color);
// Implementation detail for the teaching renderer.
  const rings=feature.geometry.type==='Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
  for(const polygon of rings) for(const ring of polygon){
    viewer.entities.add({polyline:{positions:Cesium.Cartesian3.fromDegreesArray(ring.flatMap(p=>p.slice(0,2))),
      width:3,clampToGround:true,classificationType:Cesium.ClassificationType.TERRAIN,material:color}});
  }
 }
 function allPoints(coords){return typeof coords[0]==='number'?[coords]:coords.flatMap(allPoints);}
 const points=geojson.features.flatMap(f=>allPoints(f.geometry.coordinates));
 if(config.bars_enabled)points.push(...barRows.map(row=>[row.longitude,row.latitude]));
 const sphereFor=feature=>Cesium.BoundingSphere.fromPoints(allPoints(feature.geometry.coordinates).map(p=>Cesium.Cartesian3.fromDegrees(p[0],p[1])));
 const startSphere=new Cesium.BoundingSphere(Cesium.Cartesian3.fromDegrees(config.center[0],config.center[1]),100);
 const allSphere=points.length?Cesium.BoundingSphere.fromPoints(points.map(p=>Cesium.Cartesian3.fromDegrees(p[0],p[1]))):startSphere;
 let currentSphere=geojson.features.length?sphereFor(geojson.features[config.start_parking] || geojson.features[0]):(config.bars_enabled?allSphere:startSphere);
 function go(top=false){
  const target=Cesium.Cartographic.fromCartesian(currentSphere.center);
  target.height=viewer.scene.globe.getHeight(target) || (config.use_terrain?100:0);
  const center=Cesium.Cartographic.toCartesian(target);
  viewer.camera.lookAt(center,new Cesium.HeadingPitchRange(
   Cesium.Math.toRadians(config.heading),Cesium.Math.toRadians(top?-89:config.pitch),Math.max(config.distance_m,currentSphere.radius*(config.bars_enabled?2.1:3))));
  viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);viewer.scene.requestRender();
 }
 function showDetails(feature){
  document.getElementById('details').textContent=feature.properties.name+': '+(feature.properties.note || 'User polygon');
  const link=document.getElementById('source-link');
  const url=feature.properties.osm_url || '';
  link.hidden=!/^https:\/\/www\.openstreetmap\.org\/way\/\d+$/.test(url);
  if(!link.hidden)link.href=url;
  if(config.popup_enabled){
   const selected=source.entities.values.find(e=>e.properties?._basemap_object_index?.getValue(viewer.clock.currentTime)===feature.properties._basemap_object_index);
   if(selected)viewer.selectedEntity=selected;
  }
 }
 function focusFeature(feature){currentSphere=sphereFor(feature);showDetails(feature);go();}
 if(geojson.features.length){currentSphere=allSphere;go();}else go();
 viewer.selectedEntity=undefined;
 document.getElementById('overview').disabled=false;
 document.getElementById('top').disabled=false;
 document.getElementById('overview').onclick=()=>{currentSphere=allSphere;go();};
 document.getElementById('top').onclick=()=>go(true);
 document.getElementById('fill').onchange=event=>{
  source.entities.values.forEach(entity=>{entity.polygon.show=event.target.checked;});viewer.scene.requestRender();
 };
 const legend=document.getElementById('legend');
 let shown=0;
 const objectSummary=document.createElement('p');objectSummary.className='object-summary';legend.before(objectSummary);
 const more=document.createElement('button');more.className='load-more';more.textContent='Load more';legend.after(more);
 function appendObjects(){
  const end=Math.min(shown+50,geojson.features.length);
  for(let i=shown;i<end;i++){
   const f=geojson.features[i],row=document.createElement('div');row.className='item';
   const dot=document.createElement('span');dot.className='swatch';dot.style.background=f.properties.color;
   const button=document.createElement('button');button.textContent=f.properties.name;button.title=f.properties.name;button.onclick=()=>focusFeature(f);
   row.append(dot,button);legend.append(row);
  }
  shown=end;objectSummary.textContent=shown+' / '+geojson.features.length+' objects';more.hidden=shown>=geojson.features.length;
 }
 more.onclick=appendObjects;appendObjects();
 viewer.screenSpaceEventHandler.setInputAction(click=>{
  if(viewer.placeHouseAt && viewer.placeHouseAt(click.position))return;
  const picked=viewer.scene.pick(click.position);
  const entity=picked && picked.id;
  if((config.tiles3d_layers || []).some(layer=>layer.popup) && showTileFeature(viewer,picked))return;
  if(config.popup_enabled && entity?.properties?.kind?.getValue(viewer.clock.currentTime)==='bar')viewer.selectedEntity=entity;
  if(entity && source.entities.contains(entity)){
   document.getElementById('details').textContent=entity.name;
   if(config.popup_enabled)viewer.selectedEntity=entity;
  }
 },Cesium.ScreenSpaceEventType.LEFT_CLICK);
 report();

 let terrainEnabled=false;
 if(config.use_terrain){
  status.textContent='Polygons ready; loading DGM5 terrain …';
  try{
   viewer.terrainProvider=await Cesium.CesiumTerrainProvider.fromUrl('https://sgx.geodatenzentrum.de/gdz_basemapde_3d_gelaende/dgm5_4326_mesh/');
   terrainEnabled=true;
   let failed=false;
   viewer.terrainProvider.errorEvent.addEventListener(()=>{if(!failed){failed=true;warnings.push('Some terrain tiles are missing. Check the internet connection.');report();}});
  }catch(error){warnings.push('Terrain unavailable: using a flat view and matching building variant.');}
 }
 if(config.buildings_enabled){
 try{
  const suffix=terrainEnabled?'dgm5':'null';
  const buildings=await Cesium.Cesium3DTileset.fromUrl('https://sgx.geodatenzentrum.de/gdz_basemapde_3d_gebaeude/lod2_4326_'+suffix+'.json',{maximumScreenSpaceError:12});
// Implementation detail for the teaching renderer.
  buildings.colorBlendMode=Cesium.Cesium3DTileColorBlendMode.REPLACE;
  buildings.style=new Cesium.Cesium3DTileStyle({color:{conditions:[
   ["${surface} === 'roof'",'color("'+config.roof_color+'")'],
   ["${surface} === 'bridge'",'color("#708693")'],
   ['true','color("'+config.building_color+'")']
  ]}});
// Implementation detail for the teaching renderer.
  buildings.shadows=Cesium.ShadowMode.CAST_ONLY;
  viewer.scene.primitives.add(buildings);
  if(config.query_enabled)setupNearbyHighlight(viewer,buildings);
  let failed=false;
  buildings.tileFailed.addEventListener(()=>{if(!failed){failed=true;warnings.push('Some building tiles are missing. Check the network and reload.');report();}});
  const toggle=document.getElementById('toggle');toggle.disabled=false;
  toggle.onclick=()=>{buildings.show=!buildings.show;toggle.textContent=buildings.show?'Hide buildings':'Show buildings';viewer.scene.requestRender();};
  buildingCheck.disabled=false;buildingCheck.onchange=()=>{buildings.show=buildingCheck.checked;viewer.scene.requestRender();};
  window.buildings=buildings;
 }catch(error){warnings.push('Building service unavailable. Polygons and base map remain visible. Check the network and reload.');console.error(error);}
 }
 await setupTiles3D(viewer,terrainEnabled);
 if(config.house_placement_enabled)setupHousePlacement(viewer,terrainEnabled);
 go();report();viewer.scene.requestRender();
}
main().catch(error=>{status.textContent='Could not start the scene: '+error.message+'\nOpen the exported HTML file or check WebGL2 and hardware acceleration.';console.error(error);});
// Browser-local GeoJSON replacement; query data is refreshed for the new extent.
function validateUploadedPolygons(data){
 if(data.type==='Feature')data={type:'FeatureCollection',features:[data]};
 if(data.type!=='FeatureCollection'||!Array.isArray(data.features)||!data.features.length)throw Error('A nonempty FeatureCollection of polygons is required.');

 const palette=['#ff7b54','#21cbb8','#c3a1ff','#ffd35c','#56b6ff'];
 data.features.forEach((f,i)=>{
  if(!f||f.type!=='Feature'||!['Polygon','MultiPolygon'].includes(f.geometry?.type))throw Error('Only Polygon and MultiPolygon are supported.');
  const polygons=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;
  if(!Array.isArray(polygons)||!polygons.length)throw Error('Empty geometry.');
  for(const poly of polygons){
   if(!Array.isArray(poly)||!poly.length)throw Error('Empty polygon.');
   for(const ring of poly){
    if(!Array.isArray(ring)||ring.length<4)throw Error('A ring requires at least four coordinates.');
    for(const p of ring)if(!Array.isArray(p)||p.length<2||!p.every(Number.isFinite)||Math.abs(p[0])>180||Math.abs(p[1])>90)throw Error('WGS84 coordinates [longitude, latitude] within ±90 degrees latitude are required.');
    if(ring[0][0]!==ring[ring.length-1][0]||ring[0][1]!==ring[ring.length-1][1])throw Error('Polygon rings must be closed.');
   }
  }
  const props=f.properties||{};f.properties={...props,name:String(props.name??props.Name??props.NAME??props.Bezeichnung??props.bezeichnung??props.title??props.label??props.id??f.id??('Object '+(i+1))),_basemap_object_index:i,note:String(props.note||''),color:palette[i%palette.length]};
  f.id='object-'+i;
 });
 if(data.features.flatMap(f=>coordinatePairs(f.geometry.coordinates)).length>20000)throw Error('Simplify the geometry (maximum 20,000 points).');
 return data;
}
function osmBuildingFeatures(elements){
 const nodes=new Map(elements.filter(e=>e.type==='node').map(e=>[e.id,[e.lon,e.lat]]));
 const ways=new Map(elements.filter(e=>e.type==='way').map(e=>[e.id,e]));
 const features=[],members=new Set();
 function rings(parts){
  const pending=parts.map(p=>p.slice()),result=[];
  while(pending.length){let ring=pending.pop();while(ring[0]!==ring[ring.length-1]){
   const i=pending.findIndex(p=>p[0]===ring[0]||p[p.length-1]===ring[0]||p[0]===ring[ring.length-1]||p[p.length-1]===ring[ring.length-1]);
   if(i<0)throw Error('Incomplete OSM building relation. Try a smaller extent.');
   let part=pending.splice(i,1)[0];
   if(ring[ring.length-1]===part[0])ring.push(...part.slice(1));
   else if(ring[ring.length-1]===part[part.length-1])ring.push(...part.reverse().slice(1));
   else if(ring[0]===part[part.length-1])ring=part.slice(0,-1).concat(ring);
   else ring=part.reverse().slice(0,-1).concat(ring);
  }
  if(ring.length>=4){if(!ring.every(id=>nodes.has(id)))throw Error('OSM buildings were not fully loaded.');result.push(ring.map(id=>nodes.get(id)));}}
  return result;
 }
 for(const rel of elements.filter(e=>e.type==='relation'&&e.tags?.type==='multipolygon'&&e.tags?.building&&e.tags.building!=='no')){
  const outer=[],inner=[];
  for(const m of rel.members||[])if(m.type==='way'){
   if(!ways.has(m.ref))throw Error('OSM relation extends beyond the extent. Please retry.');
   (m.role==='inner'?inner:outer).push(ways.get(m.ref).nodes);members.add(m.ref);
  }
  const shells=rings(outer),holes=rings(inner);
  if(shells.length)features.push({type:'Feature',properties:{osm_id:rel.id},geometry:{type:'MultiPolygon',coordinates:shells.map(r=>[r,...holes.filter(h=>pointInRing(h[0],r))])}});
 }
 for(const way of ways.values())if(!members.has(way.id)&&way.tags?.building&&way.tags.building!=='no'&&way.nodes[0]===way.nodes[way.nodes.length-1]){
  const coords=rings([way.nodes]);if(coords.length)features.push({type:'Feature',properties:{osm_id:way.id},geometry:{type:'Polygon',coordinates:[coords[0]]}});
 }
 return {type:'FeatureCollection',features};
}
async function uploadedBuildings(polygons){
 const pts=polygons.features.flatMap(f=>coordinatePairs(f.geometry.coordinates));
 if(pts.some(p=>Math.abs(p[1])>85))throw Error('Building queries support latitudes up to ±85 degrees.');
 const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]),lat=(Math.min(...ys)+Math.max(...ys))/2;
 const dy=(config.nearby_max_distance_m+100)/111320,dx=dy/Math.cos(lat*Math.PI/180);
 const box=[Math.min(...xs)-dx,Math.min(...ys)-dy,Math.max(...xs)+dx,Math.max(...ys)+dy];
 if((box[2]-box[0])*111320*Math.cos(lat*Math.PI/180)*(box[3]-box[1])*111320>4000000)throw Error('Use an extent up to 4 square kilometers for automatic queries.');
 const response=await fetch('https://api.openstreetmap.org/api/0.6/map.json?bbox='+box.join(','),{signal:AbortSignal.timeout(45000)});
 if(!response.ok)throw Error('Could not load OSM buildings ('+response.status+'). The existing polygons are retained.');
 const payload=await response.json();
 const all=new Map(payload.elements.map(e=>[e.type+'/'+e.id,e]));
 const incomplete=payload.elements.filter(e=>e.type==='relation'&&e.tags?.type==='multipolygon'&&e.tags?.building&&e.tags.building!=='no'&&(e.members||[]).some(m=>m.type==='way'&&!all.has('way/'+m.ref)));
 if(incomplete.length>8)throw Error('Too many complex building relations. Choose a smaller extent.');
 await Promise.all(incomplete.map(async rel=>{
  const full=await fetch('https://api.openstreetmap.org/api/0.6/relation/'+rel.id+'/full.json',{signal:AbortSignal.timeout(30000)});
  if(!full.ok)throw Error('Could not fully load the building relation.');
  for(const item of (await full.json()).elements)all.set(item.type+'/'+item.id,item);
 }));
 return osmBuildingFeatures([...all.values()]);
}
function setupPolygonUpload(){
 if(!config.has_vector)return;
 const section=document.getElementById('fill').closest('section');
 const layerTitle=document.createElement('div');layerTitle.className='vector-layer-title';layerTitle.textContent=config.vector_layer_name||'Parking areas · GeoJSON';section.prepend(layerTitle);
 const input=document.createElement('input');input.type='file';input.accept='.geojson,.json,application/geo+json,application/json';input.id='polygon-upload';input.setAttribute('aria-label','Replace GeoJSON polygons');
 const label=document.createElement('label');label.className='upload-label';label.textContent='Replace GeoJSON';label.htmlFor=input.id;
 const note=document.createElement('p');note.className='layer-description';note.style.marginLeft='0';note.textContent=config.query_enabled?'Replaces all polygons. The new extent is sent to OpenStreetMap to load buildings (up to 4 square kilometers).':'Replaces all polygons · WGS84 or a declared CRS.';
 const message=document.createElement('p');message.className='upload-message';message.setAttribute('role','status');
 section.append(label,input,note,message);
 input.onchange=async()=>{
  const file=input.files[0];if(!file)return;input.disabled=true;
  try{
   if(file.size>5000000)throw Error('File too large (maximum 5 MB).');
   message.textContent='Checking coordinate system …';
   const polygons=validateUploadedPolygons(await normalizeUploadedCRS(JSON.parse(await file.text())));
   message.textContent=config.query_enabled?'Loading new OSM buildings …':'Replacing polygons …';
   const footprints=config.query_enabled?await uploadedBuildings(polygons):{type:'FeatureCollection',features:[]};
   const nextConfig={...config,vector_layer_name:file.name,start_parking:0,query_source_label:'OSM for uploaded polygons',nearby_distance_m:Number(document.getElementById('nearby-distance').value)||config.nearby_distance_m};
   const safe=value=>JSON.stringify(value).replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/&/g,'\\u0026');
   const page=originalSceneHTML.replace(/^const config = .*;$/m,()=> 'const config = '+safe(nextConfig)+';').replace(/^const geojson = .*;$/m,()=> 'const geojson = '+safe(polygons)+';').replace(/^const buildingFootprints = .*;$/m,()=> 'const buildingFootprints = '+safe(footprints)+';');
   // Rebuild the scene to reset features, outlines, distances, legend and popups together.
   if(window.viewer&&!window.viewer.isDestroyed())window.viewer.destroy();
   document.open();document.write('<!doctype html>'+page);document.close();
  }catch(error){message.textContent='Not replaced: '+error.message;input.disabled=false;input.value='';}
 };
}

async function normalizeUploadedCRS(data){
 const declaration=data.crs;
 const properties=declaration?.properties||{};
 const raw=typeof declaration==='string'?declaration:properties.name||properties.href||(properties.code?'EPSG:'+properties.code:null)||properties.proj4||properties.wkt;
 if(declaration&&!raw)throw Error('Could not read the CRS. Provide an EPSG code or a WKT/PROJ definition.');
 let source=raw||'EPSG:4326';
 if(/CRS:?84$/i.test(source)||/^WGS\s?84$/i.test(source))source='EPSG:4326';
 const epsg=String(source).match(/EPSG.*?(\d+)$/i);if(epsg)source='EPSG:'+epsg[1];
 if(source!=='EPSG:4326'){
  if(!window.proj4){
   await new Promise((resolve,reject)=>{const script=document.createElement('script');script.src='https://cdn.jsdelivr.net/npm/proj4@2.22.0/dist/proj4.js';script.onload=resolve;script.onerror=()=>reject(Error('Could not load coordinate transformation.'));document.head.append(script);});
  }
  const common={
   'EPSG:25832':'+proj=utm +zone=32 +ellps=GRS80 +units=m +no_defs',
   'EPSG:25833':'+proj=utm +zone=33 +ellps=GRS80 +units=m +no_defs',
   'EPSG:3035':'+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs'
  };
  for(const [key,value] of Object.entries(common))proj4.defs(key,value);
  if(source.startsWith('EPSG:')&&!proj4.defs(source)){
   const response=await fetch('https://epsg.io/'+source.slice(5)+'.proj4',{signal:AbortSignal.timeout(15000)});
   if(!response.ok)throw Error('Unknown coordinate system '+source+'.');
   const definition=(await response.text()).trim();if(!definition.startsWith('+proj='))throw Error('No usable projection for '+source+'.');
   proj4.defs(source,definition);
  }
  let transform;try{transform=proj4(source,'EPSG:4326');}catch{throw Error('Unsupported declared coordinate system: '+source);}
  function coordinates(value){
   if(!Array.isArray(value)||!value.length)throw Error('Invalid coordinates.');
   if(typeof value[0]==='number'){
    if(value.length<2||!value.every(Number.isFinite))throw Error('Invalid coordinates.');
    const xy=transform.forward(value.slice(0,2));return [...xy,...value.slice(2)];
   }
   return value.map(coordinates);
  }
  const features=data.type==='Feature'?[data]:data.features;
  if(!Array.isArray(features))throw Error('FeatureCollection or Feature required.');
  for(const feature of features){if(!feature.geometry)throw Error('Missing geometry.');feature.geometry.coordinates=coordinates(feature.geometry.coordinates);delete feature.bbox;}
 }
 delete data.crs;delete data.bbox;
 return data;
}

})();
