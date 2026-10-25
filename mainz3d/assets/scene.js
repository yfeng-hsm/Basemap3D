
const config = __CONFIG_JSON__;
const geojson = __GEOJSON_JSON__;
const buildingFootprints = __BUILDINGS_JSON__;
const status = document.getElementById('status');
document.getElementById('title').textContent = config.title;
document.title = config.title;
const available={2:config.has_raster,3:config.has_vector,4:config.query_enabled,5:config.sun_enabled};
document.querySelectorAll('[data-min-task]').forEach(node=>{node.hidden=!available[Number(node.dataset.minTask)];});
document.getElementById('stage-description').textContent=config.stage_description;
if(!config.has_vector)document.querySelector('.hint').textContent='Ziehen: verschieben · Mausrad: zoomen · Strg + Ziehen: neigen / drehen';

const warnings = [];
function report(){status.textContent = 'Task '+config.task+' bereit. Karten und Gebäude werden für die aktuelle Ansicht geladen.' + (warnings.length?'\n'+warnings.join('\n'):'');}
// Implementation detail for the teaching renderer.
const localScaleX=111320*Math.cos(50*Math.PI/180), localScaleY=111320;
function metricPolygon(polygon){return polygon.map(ring=>ring.map(p=>[(p[0]-8.26)*localScaleX,(p[1]-50)*localScaleY]));}
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
 }).filter(x=>x.distance<=200);
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
  count.textContent='Alle '+geojson.features.length+' Flächen: '+selected.length+' OSM-Gebäudeumrisse ausgewählt. 3D-Modelle werden ansichtsabhängig geladen.';
  viewer.scene.requestRender();
 }
 toggle.disabled=false;slider.disabled=false;
 toggle.checked=config.highlight_nearby;
 slider.value=String(config.nearby_distance_m);
 output.textContent=slider.value+' m';
 toggle.addEventListener('change',()=>{clearTimeout(timer);update();});
 slider.addEventListener('input',()=>{output.textContent=slider.value+' m';clearTimeout(timer);timer=setTimeout(update,120);});
// Implementation detail for the teaching renderer.
 update();
}

async function main(){
 if(typeof Cesium==='undefined') throw new Error('CesiumJS konnte nicht geladen werden. Internetverbindung und CDN-Zugriff prüfen.');
 Cesium.Ion.defaultAccessToken = '';
 const viewer = new Cesium.Viewer('scene', {
   baseLayer:false, baseLayerPicker:false, geocoder:false,
   animation:false, timeline:false, homeButton:false, sceneModePicker:false,
   navigationHelpButton:false, fullscreenButton:false, infoBox:config.popup_enabled,
   selectionIndicator:false, shadows:config.sun_enabled, terrainShadows:config.sun_enabled?Cesium.ShadowMode.RECEIVE_ONLY:Cesium.ShadowMode.DISABLED, requestRenderMode:true
 });
 window.viewer = viewer;
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
 const imageryCredit = '©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0, www.lvermgeo.rlp.de';
 const mapLayer=viewer.imageryLayers.addImageryProvider(new Cesium.WebMapServiceImageryProvider({
  url:'https://sgx.geodatenzentrum.de/wms_basemapde',layers:'de_basemapde_web_raster_farbe',
  parameters:{version:'1.1.1',format:'image/png',transparent:true},credit:'© GeoBasis-DE/BKG 2026'
 }));
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
 const sphereFor=feature=>Cesium.BoundingSphere.fromPoints(allPoints(feature.geometry.coordinates).map(p=>Cesium.Cartesian3.fromDegrees(p[0],p[1])));
 const startSphere=new Cesium.BoundingSphere(Cesium.Cartesian3.fromDegrees(config.center[0],config.center[1]),100);
 const allSphere=points.length?Cesium.BoundingSphere.fromPoints(points.map(p=>Cesium.Cartesian3.fromDegrees(p[0],p[1]))):startSphere;
 let currentSphere=geojson.features.length?sphereFor(geojson.features[config.start_parking] || geojson.features[0]):startSphere;
 function go(top=false){
  const target=Cesium.Cartographic.fromCartesian(currentSphere.center);
  target.height=viewer.scene.globe.getHeight(target) || (config.use_terrain?100:0);
  const center=Cesium.Cartographic.toCartesian(target);
  viewer.camera.lookAt(center,new Cesium.HeadingPitchRange(
   Cesium.Math.toRadians(config.heading),Cesium.Math.toRadians(top?-89:config.pitch),Math.max(config.distance_m,currentSphere.radius*3)));
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
 go();report();viewer.scene.requestRender();
}
main().catch(error=>{status.textContent='Szene konnte nicht gestartet werden: '+error.message+'\nDie exportierte HTML-Datei öffnen oder WebGL2 / Hardwarebeschleunigung prüfen.';console.error(error);});