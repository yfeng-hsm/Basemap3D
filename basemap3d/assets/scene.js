
const config = __CONFIG_JSON__;
const geojson = __GEOJSON_JSON__;
const buildingFootprints = __BUILDINGS_JSON__;
const barRows = __BARS_JSON__;
const status = document.getElementById('status');
document.getElementById('title').textContent = config.title;
document.title = config.title;
const available={2:config.has_raster,3:config.has_vector,4:config.query_enabled,5:config.sun_enabled};
document.querySelectorAll('[data-min-task]').forEach(node=>{node.hidden=!available[Number(node.dataset.minTask)];});
document.getElementById('stage-description').textContent=(config.tiles3d_layers?.length && !config.has_vector && !config.bars_enabled)?'Gehostete 3D-Layer · Gelände und Stadtmodell':config.stage_description;
if(!config.has_vector)document.getElementById('overview').textContent=config.bars_enabled?'3D-Säulen':'Gesamtansicht';
if(config.bars_enabled)document.getElementById('top').textContent='2D-Verteilung';
if(!config.has_vector)document.querySelector('.hint').textContent='Ziehen: verschieben · Mausrad: zoomen · Strg + Ziehen: neigen / drehen';

const warnings = [];
function report(){status.textContent = (config.bars_enabled?'Themenkarte bereit.':config.tiles3d_layers?.length?'3D-Szene bereit.':'Task '+config.task+' bereit.')+' Kartendaten werden für die aktuelle Ansicht geladen.' + (warnings.length?'\n'+warnings.join('\n'):'');}
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
   count.textContent='Deaktiviert. Die Auswahl gilt gleichzeitig für alle '+geojson.features.length+' Flächen.';
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
  count.textContent='Alle '+geojson.features.length+' Flächen: '+selected.length+' OSM-Gebäudeumrisse ausgewählt. '+config.query_source_label+'.';
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
 document.getElementById('bar-reading').textContent='Dunkler und höher = mehr '+config.bar_unit+'. Die Draufsicht zeigt das räumliche Muster ohne Überdeckung.';
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
 const format=n=>n.toLocaleString('de-DE',{maximumFractionDigits:2});
 const escape=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const colorFor=value=>palette[Math.min(palette.length-1,breaks.filter(v=>value>v).length)];
 const dataset=new Cesium.CustomDataSource('Thematische Säulen');
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
    '<tr><th>Gitterzelle</th><td>'+escape(row.name)+'</td></tr>'+
    '<tr><th>'+escape(config.bar_legend_title)+'</th><td>'+format(row.value)+' '+escape(config.bar_unit)+'</td></tr>'+
    '<tr><th>Stichtag</th><td>'+escape(row.reference_date || 'Siehe Datenquelle')+'</td></tr>'+
    '<tr><th>Darstellung</th><td>Thematische Säule, keine Gebäudehöhe.</td></tr></tbody></table>'
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
  document.getElementById('bar-height-value').textContent=format(factor)+' m / Einheit';
  document.getElementById('bar-minimum-value').textContent=format(minimum)+' '+config.bar_unit;
  document.getElementById('bar-count').textContent=shown+' von '+barRows.length+' Säulen sichtbar. Farben: feste Quantilklassen des geladenen Datensatzes.';
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
 const labels={tree_id:'Baum-ID',model_height_m:'Modellhöhe (m)',source_height_m:'Geschätzte Baumhöhe (m)',ground_height_m:'Geländehöhe DGM5 (m)',needs_review:'Prüfung empfohlen'};
 const ids=tree?Object.keys(labels):picked.getPropertyIds().slice(0,30);
 const rows=ids.map(id=>{let value=picked.getProperty(id);if(value===undefined)return '';
  if(typeof value==='number')value=value.toLocaleString('de-DE',{maximumFractionDigits:2});
  if(id==='needs_review')value=Boolean(picked.getProperty(id));
  if(typeof value==='boolean')value=value?'Ja':'Nein';
  return '<tr><th>'+esc(labels[id] || id)+'</th><td>'+esc(value)+'</td></tr>';
 }).join('');
 const name=tree?'Baum '+tree:'3D-Objekt';
 viewer.selectedEntity=new Cesium.Entity({name,description:'<table class="cesium-infoBox-defaultTable"><tbody>'+rows+'</tbody></table>'+(tree?'<p>Automatisch erkannter Kandidat; schematisches Modell, keine bestätigte Baumaufnahme.</p>':'')});
 document.getElementById('tiles3d-details').textContent=tree?name+' · Modellhöhe '+Number(picked.getProperty('model_height_m')).toLocaleString('de-DE',{maximumFractionDigits:2})+' m · '+(picked.getProperty('needs_review')?'Bitte manuell prüfen.':'Automatischer Kandidat.'):name;
 return true;
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
  const note=document.createElement('p');note.className='shadow-note';note.textContent=option.note || '';box.append(note);
  let selector;
  if(option.variants){
   selector=document.createElement('select');selector.setAttribute('aria-label',option.name+' · Höhenmodus');
   for(const [value,url] of Object.entries(option.variants)){
    const item=document.createElement('option');item.value=value;item.textContent=value==='uniform'?'Einheitliche Höhe · 15 m':'Geschätzte Baumhöhe';selector.append(item);
   }
   selector.value=option.variant;box.append(selector);
  }
  const fit=document.createElement('button');fit.textContent='Zum Layer';fit.disabled=true;box.append(fit);
  const state=document.createElement('p');state.className='shadow-note';state.textContent='Layer wird geladen …';box.append(state);
  document.getElementById('tiles3d-controls').append(box);
  if(option.require_terrain && !terrainEnabled){
   state.textContent='Nicht geladen: Dieser Layer benötigt basemap.de DGM5-Gelände. Verbindung prüfen und neu laden.';
   visible.disabled=true;if(selector)selector.disabled=true;return;
  }
  let current=null;
  visible.onchange=()=>{if(current)current.show=visible.checked;viewer.scene.requestRender();};
  fit.onclick=()=>{if(current)viewer.camera.flyToBoundingSphere(current.boundingSphere,{duration:0.8,offset:new Cesium.HeadingPitchRange(Cesium.Math.toRadians(25),Cesium.Math.toRadians(-45),0)});};
  async function load(url){
   if(selector)selector.disabled=true;state.textContent='Layer wird geladen …';
   try{
    const settings={maximumScreenSpaceError:option.maximum_screen_space_error};
    if(option.feature_id_label)settings.instanceFeatureIdLabel=option.feature_id_label;
    const next=await Cesium.Cesium3DTileset.fromUrl(url,settings);
    next.show=visible.checked;next.shadows=config.sun_enabled?Cesium.ShadowMode.CAST_ONLY:Cesium.ShadowMode.DISABLED;
    viewer.scene.primitives.add(next);
    if(current)viewer.scene.primitives.remove(current);
    current=next;fit.disabled=false;state.textContent='3D-Layer bereit · sichtbare Kacheln werden geladen.';
    next.allTilesLoaded.addEventListener(()=>{state.textContent='Sichtbare Kacheln geladen.';});
    next.tileFailed.addEventListener(()=>{state.textContent='Eine Kachel fehlt. Netzwerk prüfen und neu laden.';});
    viewer.scene.requestRender();
   }catch(error){state.textContent='Layer konnte nicht geladen werden: '+error.message;}
   finally{if(selector)selector.disabled=false;}
  }
  if(selector)selector.onchange=()=>load(option.variants[selector.value]);
  await load(option.url);
 }));
}

async function main(){
 if(typeof Cesium==='undefined') throw new Error('CesiumJS konnte nicht geladen werden. Internetverbindung und CDN-Zugriff prüfen.');
 Cesium.Ion.defaultAccessToken = '';
 if(config.bars_enabled)document.body.classList.add('population-mode');
 const viewer = new Cesium.Viewer('scene', {
   baseLayer:false, baseLayerPicker:false, geocoder:false,
   animation:false, timeline:false, homeButton:false, sceneModePicker:false,
   navigationHelpButton:false, fullscreenButton:false, infoBox:config.popup_enabled,
   selectionIndicator:false, shadows:config.sun_enabled, terrainShadows:config.sun_enabled?Cesium.ShadowMode.RECEIVE_ONLY:Cesium.ShadowMode.DISABLED, requestRenderMode:true
 });
 window.viewer = viewer;
 document.getElementById('toggle').hidden=!config.buildings_enabled;
 viewer.clock.shouldAnimate=false;
 viewer.scene.light=new Cesium.SunLight();
 viewer.scene.globe.enableLighting=config.sun_enabled;
 viewer.shadowMap.softShadows=true;
 viewer.shadowMap.darkness=0.35;
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
 viewer.creditDisplay.addStaticCredit(new Cesium.Credit('© GeoBasis-DE/BKG 2026 · basemap.de | Bearbeitung: Farben und Lehrbeispiele',true));
 if(config.bars_enabled)setupBars(viewer);
 const imageryCredit = '©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0, www.lvermgeo.rlp.de';
 const mapLayer=viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
  url:'https://sgx.geodatenzentrum.de/wms_basemapde',layers:'de_basemapde_web_raster_farbe',
  parameters:{version:'1.1.1',format:'image/png',transparent:true},credit:'© GeoBasis-DE/BKG 2026'
 }));
 if(config.bars_enabled){mapLayer.saturation=0;mapLayer.brightness=1.15;mapLayer.contrast=0.65;mapLayer.gamma=1.1;}
 const aerialLayer=viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
  url:config.raster_url,layers:config.raster_layer,
  parameters:{version:'1.1.1',format:'image/png',transparent:true},
  rectangle:Cesium.Rectangle.fromDegrees(6.03,48.89,8.62,51.01),maximumLevel:20,
  credit:imageryCredit
 }));
 function switchBasemap(name){
  aerialLayer.show=config.has_raster && name==='aerial';
  document.getElementById('aerial').setAttribute('aria-pressed',String(aerialLayer.show));
  document.getElementById('map').setAttribute('aria-pressed',String(!aerialLayer.show));
  document.getElementById('imagery-credit').textContent=aerialLayer.show?imageryCredit+' · ':'';
  viewer.scene.requestRender();
 }
 document.getElementById('aerial').onclick=()=>switchBasemap('aerial');
 document.getElementById('map').onclick=()=>switchBasemap('map');
 switchBasemap(config.basemap);
 const opacitySlider=document.getElementById('raster-opacity');
 function updateRasterOpacity(){aerialLayer.alpha=Number(opacitySlider.value)/100;document.getElementById('raster-value').textContent=opacitySlider.value+'%';viewer.scene.requestRender();}
 opacitySlider.value=String(Math.round(config.raster_opacity*100));
 opacitySlider.addEventListener('input',updateRasterOpacity);updateRasterOpacity();
 let aerialFailed=false,mapFailed=false;
 aerialLayer.imageryProvider.errorEvent.addEventListener(()=>{
  if(!aerialFailed){aerialFailed=true;warnings.push('Luftbildkacheln konnten nicht geladen werden. Zur Basiskarte wechseln und erneut versuchen.');report();}
 });
 mapLayer.imageryProvider.errorEvent.addEventListener(()=>{
  if(!mapFailed){mapFailed=true;warnings.push('Basiskartenkacheln konnten nicht geladen werden. Netzwerk prüfen.');report();}
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
   ['Name',props.name],['OSM ID',props.osm_id || 'Eigene Daten'],['Zugang (OSM)',props.access || 'Keine Angabe'],['Beschreibung',props.note || 'Eigene Fläche']
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
  document.getElementById('details').textContent=feature.properties.name+': '+(feature.properties.note || 'Eigene Fläche');
  const link=document.getElementById('source-link');
  const url=feature.properties.osm_url || '';
  link.hidden=!/^https:\/\/www\.openstreetmap\.org\/way\/\d+$/.test(url);
  if(!link.hidden)link.href=url;
  if(config.popup_enabled){
   const selected=source.entities.values.find(e=>e.name===feature.properties.name);
   if(selected)viewer.selectedEntity=selected;
  }
 }
 function focusFeature(feature){currentSphere=sphereFor(feature);showDetails(feature);go();}
 if(geojson.features.length)focusFeature(geojson.features[config.start_parking] || geojson.features[0]);else go();
 document.getElementById('overview').disabled=false;
 document.getElementById('top').disabled=false;
 document.getElementById('overview').onclick=()=>{currentSphere=allSphere;go();};
 document.getElementById('top').onclick=()=>go(true);
 document.getElementById('fill').onchange=event=>{
  source.entities.values.forEach(entity=>{entity.polygon.show=event.target.checked;});viewer.scene.requestRender();
 };
 const legend=document.getElementById('legend');
 geojson.features.forEach(f=>{
  const row=document.createElement('div');row.className='item';
  const dot=document.createElement('span');dot.className='swatch';dot.style.background=f.properties.color;
  const button=document.createElement('button');button.textContent=f.properties.name;button.onclick=()=>focusFeature(f);
  row.append(dot,button);legend.append(row);
 });
 viewer.screenSpaceEventHandler.setInputAction(click=>{
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
  status.textContent='Flächen bereit; DGM5-Gelände wird geladen …';
  try{
   viewer.terrainProvider=await Cesium.CesiumTerrainProvider.fromUrl('https://sgx.geodatenzentrum.de/gdz_basemapde_3d_gelaende/dgm5_4326_mesh/');
   terrainEnabled=true;
   let failed=false;
   viewer.terrainProvider.errorEvent.addEventListener(()=>{if(!failed){failed=true;warnings.push('Einige Geländekacheln fehlen. Internetverbindung prüfen.');report();}});
  }catch(error){warnings.push('Gelände nicht verfügbar: flache Darstellung mit passender Gebäudevariante.');}
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
  buildings.tileFailed.addEventListener(()=>{if(!failed){failed=true;warnings.push('Einige Gebäudekacheln fehlen. Netzwerk prüfen und neu laden.');report();}});
  const toggle=document.getElementById('toggle');toggle.disabled=false;
  toggle.onclick=()=>{buildings.show=!buildings.show;toggle.textContent=buildings.show?'Gebäude ausblenden':'Gebäude einblenden';viewer.scene.requestRender();};
  window.buildings=buildings;
 }catch(error){warnings.push('Gebäudedienst nicht verfügbar. Flächen und Karte bleiben sichtbar. Netzwerk prüfen und neu laden.');console.error(error);}
 }
 await setupTiles3D(viewer,terrainEnabled);
 go();report();viewer.scene.requestRender();
}
main().catch(error=>{status.textContent='Szene konnte nicht gestartet werden: '+error.message+'\nDie exportierte HTML-Datei öffnen oder WebGL2 / Hardwarebeschleunigung prüfen.';console.error(error);});