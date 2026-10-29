from pathlib import Path
import json,html,sys,os,shutil
r=Path(__file__).resolve().parents[1];d=r/'docs'
sys.path.insert(0,str(r));os.chdir(r)
from basemap3d import Map,WmsTileLayer,GeoJson,NearbyBuildings,TreeLayer,SunShadows
def save_doc_scene(scene, path):
    snapshot=scene.copy()
    for layer in snapshot._config.get("tiles3d_layers", []):
        if layer.get("feature_id_label")=="tree":
            layer["relative_url"]="../layers/mainz-trees/tileset-estimated.json"
    snapshot._html=None
    snapshot.save(path)

tree_scene=Map(location=[49.99892,8.27412],zoom_start=16,title="Mainz · 3D Bäume")
WmsTileLayer(opacity=.7).add_to(tree_scene)
TreeLayer().add_to(tree_scene)
save_doc_scene(tree_scene,d/'examples/mainz_trees.html')
save_doc_scene(tree_scene,d/'examples/mainz_trees_estimated.html')
tree_shadows=tree_scene.copy()
SunShadows(date="2026-06-21",hour=17).add_to(tree_shadows)
save_doc_scene(tree_shadows,d/'examples/mainz_trees_shadows.html')

impervious_url='https://geoserver.geoville.com/geoserver/nvlcc_2024/wms'
impervious_legend=impervious_url+'?service=WMS&request=GetLegendGraphic&version=1.1.1&format=image/png&layer=HRL_NVLCC_IMD_2024_10m'
m=Map(location=[50.0063,8.2692],distance_m=850,title='Mainz · Alle Module')
WmsTileLayer(opacity=.7).add_to(m)
WmsTileLayer(url=impervious_url,layers='HRL_NVLCC_IMD_2024_10m',name='Bodenversiegelung · 2024 · 10 m',opacity=0.8,show=False,
 description='Copernicus IMD · 2024 · 10 m · 0–100 %',
 attribution='© European Union · Copernicus Land Monitoring Service · IMD 2024',
 legend_url=impervious_legend).add_to(m)
GeoJson('data/parking.geojson',popup=True).add_to(m)
TreeLayer().add_to(m);SunShadows(date='2026-06-21',hour=17).add_to(m)
save_doc_scene(m,d/'examples/mainz_complete.html')
# A second WMS service demonstrates replaceable raster modules.
impervious_map=Map(location=[50.0,8.27],distance_m=4000,buildings=False,heading=0,pitch=-70,title='Mainz · Bodenversiegelung')
WmsTileLayer(opacity=0.45).add_to(impervious_map)
WmsTileLayer(url=impervious_url,layers='HRL_NVLCC_IMD_2024_10m',name='Bodenversiegelung · 2024 · 10 m',opacity=0.8,
 description='Copernicus IMD · 2024 · 10 m · 0–100 %',
 attribution='© European Union · Copernicus Land Monitoring Service · IMD 2024',
 legend_url=impervious_legend).add_to(impervious_map)
impervious_map.save(d/'examples/impervious_surface.html')
# Build sequential snapshots with the current controls and identical study area.
base=Map(location=[50.0063,8.2692],distance_m=850,title='Mainz · Stadtmodell')
stages=[('task1_3d.html',None),('task2_raster.html',WmsTileLayer(opacity=.7)),('task3_vector.html',GeoJson('data/parking.geojson',popup=True)),('task4_query_popup.html',NearbyBuildings('data/mainz_buildings_snapshot.geojson',distance_m=75)),('mainz_modules_trees.html',TreeLayer()),('mainz_modules_shadows.html',SunShadows(date='2026-06-21',hour=17))]
for name,layer in stages:
 if name=='mainz_modules_trees.html':
  base=Map(location=[49.99892,8.27412],distance_m=450,title='Mainz · Bäume & Luftbild')
  WmsTileLayer(opacity=.7).add_to(base)
 if layer:layer.add_to(base)
 save_doc_scene(base,d/'examples'/name)
# Preserve the original task 5 endpoint with the latest renderer.
save_doc_scene(base,d/'examples/task5_sun_shadows.html')
css='''*{box-sizing:border-box} :root{--ink:#203a37;--muted:#74817e;--line:#e2e7e3;--accent:#246e59}body{margin:0;background:#f8faf7;color:var(--ink);font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:inherit;text-decoration:none}a:hover{color:var(--accent)}nav{height:76px;display:flex;align-items:center;gap:30px;max-width:1500px;margin:auto;padding:0 40px;border-bottom:1px solid var(--line)}.brand{margin-right:auto;font-size:22px;font-weight:750;letter-spacing:-.8px}.brand span{color:var(--accent)}nav a:not(.brand){font-size:13px;color:#65736e}nav a.active{color:var(--accent);font-weight:650}.shell{max-width:1500px;margin:auto;padding:34px 40px}h1{font-size:44px;line-height:1.1;letter-spacing:-1.7px;margin:12px 0 16px;font-weight:650}h2{font-size:27px;letter-spacing:-.7px;line-height:1.25;margin:14px 0}p{color:#697974;margin:12px 0 20px}.eyebrow{font-size:10px;color:var(--accent);letter-spacing:1.8px;text-transform:uppercase;font-weight:650}.intro{display:flex;justify-content:space-between;align-items:center;gap:40px;margin-bottom:30px}.intro p{max-width:540px;font-size:16px}.button,button{border:1px solid #d2ded7;background:white;border-radius:7px;padding:10px 15px;font-size:12px;color:var(--ink);cursor:pointer;display:inline-block}.primary{background:var(--accent);color:white;border-color:var(--accent)}.actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.workbench{display:grid;grid-template-columns:minmax(330px,.85fr) minmax(0,1.5fr);border:1px solid var(--line);border-radius:14px;overflow:hidden;background:white;min-height:640px}.instructions{padding:28px;min-width:0}.chips{display:flex;gap:6px;flex-wrap:wrap;margin:18px 0}.chip{border-radius:4px;background:#edf3ee;padding:3px 7px;color:#527161;font-size:10px}.codebox{background:#f5f7f4;border:1px solid #e7ece7;border-radius:8px;margin:22px 0 12px}.codehead{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e4eae3;padding:8px 13px;font:10px ui-monospace,monospace;color:#819087}.codehead button{border:0;background:none;padding:0;font-size:11px}pre{margin:0;padding:18px 14px;overflow:auto;white-space:pre;font:11px/1.95 ui-monospace,SFMono-Regular,Consolas,monospace;color:#37594b}.note{font-size:11px;color:#88938c;line-height:1.6}.result{border-left:1px solid var(--line);display:flex;flex-direction:column;background:#eaf0e9;min-width:0}.resultbar{height:44px;background:#fff;display:flex;justify-content:space-between;align-items:center;padding:0 18px;border-bottom:1px solid var(--line);font-size:11px;color:#7c8b80}.live{display:flex;gap:7px;align-items:center}.live:before{content:'';width:6px;height:6px;background:#5b9a6c;border-radius:50%}iframe{border:0;width:100%;height:100%;min-height:610px;flex:1}.sectionbar{display:flex;align-items:center;gap:20px;margin:0 0 25px}.sectionbar select{margin-left:auto;padding:10px 35px 10px 12px;border:1px solid #d5dfd6;border-radius:7px;background:white;color:var(--ink);max-width:100%;font-size:13px}.steps{display:flex;gap:8px;margin:24px 0;flex-wrap:wrap}.steps a{border:1px solid var(--line);background:#fff;padding:9px 13px;border-radius:7px;color:#65776b;font-size:12px}.steps a[aria-current=true]{background:#e8f1e8;border-color:#b9d1bb;color:#2c6244}.below{margin-top:25px;display:flex;justify-content:space-between;gap:20px;font-size:12px;color:#829083}.setup{max-width:760px;margin:60px auto}.setup pre{background:white;border:1px solid var(--line);border-radius:8px;padding:22px}footer{max-width:1500px;margin:30px auto 0;padding:22px 40px;border-top:1px solid var(--line);font-size:10px;color:#8b968d}code{font-family:ui-monospace,monospace}@media(max-width:900px){nav{padding:0 20px;gap:18px}.shell{padding:25px 20px}.intro{display:block}h1{font-size:35px}.workbench{grid-template-columns:1fr}.result{border-left:0;border-top:1px solid var(--line)}iframe{min-height:620px}.sectionbar{flex-wrap:wrap}.sectionbar select{margin-left:0}.below{display:block}}'''
(d/'assets/docs.css').write_text(css)
nav=lambda depth,active:f'''<nav><a class="brand" href="{depth}index.html">Basemap<span>3D</span></a><a class="{'active' if active=='examples' else ''}" href="{depth}examples/">Examples</a><a href="{depth}getting-started.html">Get started</a><a href="https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/docs/API.md">API ↗</a></nav>'''
head=lambda title,depth:f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Basemap3D</title><link rel="stylesheet" href="{depth}assets/docs.css"></head><body>'
footer='<footer>Basemap3D · Unofficial Python wrapper for basemap.de · Python + CesiumJS · Data credits remain in each map.</footer>'
fullcode='from basemap3d import (Map, WmsTileLayer, GeoJson,\n                       TreeLayer, SunShadows)\n\nm = Map(location=[50.0063, 8.2692], zoom_start=16)\nWmsTileLayer(opacity=0.7).add_to(m)\n\nwms = "https://geoserver.geoville.com/geoserver/nvlcc_2024/wms"\nWmsTileLayer(\n    url=wms, layers="HRL_NVLCC_IMD_2024_10m",\n    name="Bodenversiegelung · 2024 · 10 m", opacity=0.8, show=False,\n    description="Copernicus IMD · 2024 · 10 m · 0–100 %",\n    attribution="© European Union · Copernicus Land Monitoring Service",\n    legend_url=wms + "?service=WMS&request=GetLegendGraphic"\n                     "&version=1.1.1&format=image/png"\n                     "&layer=HRL_NVLCC_IMD_2024_10m",\n).add_to(m)\nGeoJson("data/parking.geojson", popup=True).add_to(m)\nTreeLayer().add_to(m)\nSunShadows(date="2026-06-21", hour=17).add_to(m)\nm'
def bench(title,desc,chips,code,url,depth=''):
 return f'''<div class="workbench"><section class="instructions"><div class="eyebrow">MODULES → MAP</div><h2 id="example-title">{title}</h2><p id="example-description">{desc}</p><div class="chips" id="modules">{''.join('<span class="chip">'+x+'</span>' for x in chips)}</div><div class="codebox"><div class="codehead"><span>Python</span><button id="copy">Copy code</button></div><pre id="code">{html.escape(code)}</pre></div><p class="note" id="example-note">Die Vorschau verwendet einen lokalen OSM-Gebäudesnapshot; der Code lädt Gebäude automatisch. Karten und Modelle benötigen Internetzugang.</p></section><section class="result"><div class="resultbar"><span class="live">Interaktive Vorschau</span><a id="result-link" href="{url}" target="_blank" rel="noopener">Vollbild ↗</a></div><iframe id="result" title="Interaktive Beispielkarte" src="{url}" loading="lazy" allow="fullscreen"></iframe></section></div>'''
copyjs="document.getElementById('copy').onclick=async()=>{try{await navigator.clipboard.writeText(document.getElementById('code').textContent);document.getElementById('copy').textContent='Copied';}catch{document.getElementById('copy').textContent='Select code to copy';}};"
(d/'index.html').write_text(head('Simple Python. Interactive 3D maps.','')+nav('','home')+'''<main class="shell"><div class="intro"><div><div class="eyebrow">A small Python API for 3D maps</div><h1>Build a map.<br>Add what you need.</h1><p>Combine imagery, vectors, 3D layers and shadows.<br>A few lines of Python. One interactive scene.</p></div><div class="actions"><a class="button primary" href="examples/">Explore examples →</a><a class="button" href="getting-started.html">Get started</a></div></div>'''+bench('Alle Darstellungsmodule. Eine Karte.','Das vollständige Mainz-Beispiel: Luftbild, Bodenversiegelung (10 m), eigene Flächen, 3D-Bäume und veränderliche Schatten. Die Gebäudeabfrage bleibt ein separates Beispiel.',['Map','WmsTileLayer × 2','GeoJson','TreeLayer','SunShadows'],fullcode,'examples/mainz_complete.html')+'''<div class="below"><span>Neu hier? Die Examples bauen diese Karte Schritt für Schritt auf.</span><a href="examples/">Mit der Basiskarte beginnen →</a></div></main>'''+footer+'<script>'+copyjs+'</script></body></html>')
basecode='from basemap3d import Map\n\nm = Map(location=[50.0063, 8.2692], zoom_start=16)'
items=[]
def add(id,title,desc,modules,code,file,note='Ergänzen Sie das vorherige Beispiel. Mit m.copy() können Sie einen Zwischenstand behalten.'):
 items.append(dict(id=id,title=title,description=desc,modules=modules,code=code,file=file,note=note))
add('map','1 · Basiskarte & 3D-Gebäude','Starten Sie mit einer Karte. Gelände und LoD2-Gebäude werden automatisch geladen.',['Map'],basecode+'\nm','task1_3d.html','Map ist die Basis. Alle weiteren Module werden mit .add_to(m) ergänzt.')
add('imagery','2 · Raster über WMS','URL und Layername bestimmen den Rasterinhalt: hier Luftbild, im Extra-Beispiel Bodenversiegelung. Mehrere WMS-Layer lassen sich unabhängig kombinieren.',['Map','WmsTileLayer'],basecode+'\nfrom basemap3d import WmsTileLayer\n\nWmsTileLayer(\n    url="https://geo4.service24.rlp.de/wms/rp_dop20.fcgi",\n    layers="rp_dop20", name="Luftbild",\n    opacity=0.7,\n).add_to(m)\nm','task2_raster.html')
add('vectors','3 · Eigene Flächen','Laden Sie GeoJSON-Polygone aus einer Datei oder ersetzen Sie alle Flächen direkt über den Upload im Viewer. Ein Klick öffnet ihre Attribute.',['Map','WmsTileLayer','GeoJson'],basecode+'\nfrom basemap3d import WmsTileLayer, GeoJson\n\nWmsTileLayer(opacity=0.7).add_to(m)\nGeoJson("data/parking.geojson", popup=True).add_to(m)\nm','task3_vector.html','Ohne CRS-Angabe gilt WGS84 [Längengrad, Breitengrad]. Ein deklariertes CRS wird vor Darstellung und Abfrage transformiert. Die Objektliste lädt jeweils 50 Einträge.')
querycode='''from basemap3d import (Map, WmsTileLayer, GeoJson,
                       NearbyBuildings)

m = Map(location=[50.0063, 8.2692], zoom_start=16)
WmsTileLayer(opacity=0.7).add_to(m)
GeoJson("data/parking.geojson", popup=True).add_to(m)
NearbyBuildings(distance_m=75).add_to(m)'''
add('query','4 · Gebäude räumlich abfragen','Ersetzen Sie die Flächen durch eine eigene GeoJSON-Datei. Die Gebäude werden für den neuen Ausschnitt geladen und anhand des Suchabstands neu ausgewählt.',['Map','WmsTileLayer','GeoJson','NearbyBuildings'],querycode+'\nm','task4_query_popup.html','GeoJson muss vor NearbyBuildings hinzugefügt werden. Die Vorschau nutzt einen lokalen OSM-Snapshot; der Code lädt Gebäude automatisch.')
treecode='from basemap3d import Map, WmsTileLayer, TreeLayer\n\nm = Map(location=[49.99892, 8.27412], distance_m=450)\nWmsTileLayer(opacity=0.7).add_to(m)\nTreeLayer().add_to(m)'
add('trees','5 · Bäume & Luftbild','Kombinieren Sie 3D-Bäume mit einem Luftbild. Dieses Beispiel enthält keine Flächen und keine Gebäudeabfrage.',['Map','WmsTileLayer','TreeLayer'],treecode+'\nm','mainz_modules_trees.html','Automatisch geschätzte Bäume und Höhen. Keine präzise Vermessung.')
add('shadows','6 · Bäume, Luftbild & Schatten','Ergänzen Sie Datum und Uhrzeit zum Baumbeispiel. Ohne Flächen und ohne Gebäudeabfrage.',['Map','WmsTileLayer','TreeLayer','SunShadows'],treecode+'\nfrom basemap3d import SunShadows\n\nSunShadows(date="2026-06-21", hour=17).add_to(m)\nm','mainz_modules_shadows.html','Fotografierte Schatten im Luftbild bleiben unverändert. Blenden Sie das Luftbild zum Vergleich aus.')
add('complete','Komplett · Alle Module','Die vollständige Darstellung mit Luftbild, Bodenversiegelung (10 m), Flächen, Bäumen und Schatten. Die räumliche Abfrage wird separat in Beispiel 4 behandelt.',['Map','WmsTileLayer × 2','GeoJson','TreeLayer','SunShadows'],fullcode,'mainz_complete.html','Die Vorschau nutzt einen lokalen OSM-Gebäudesnapshot. Schatten und geschätzte Baumhöhen dienen der qualitativen Darstellung.')
impervious_code='from basemap3d import Map, WmsTileLayer\n\nm = Map(location=[50.0, 8.27], distance_m=4000,\n        buildings=False, heading=0, pitch=-70)\nWmsTileLayer(opacity=0.45).add_to(m)\n\nwms = "https://geoserver.geoville.com/geoserver/nvlcc_2024/wms"\nWmsTileLayer(\n    url=wms, layers="HRL_NVLCC_IMD_2024_10m",\n    name="Bodenversiegelung · 2024 · 10 m", opacity=0.8,\n    description="Copernicus IMD · 2024 · 10 m · 0–100 %",\n    attribution="© European Union · Copernicus Land Monitoring Service",\n    legend_url=wms + "?service=WMS&request=GetLegendGraphic"\n                     "&version=1.1.1&format=image/png"\n                     "&layer=HRL_NVLCC_IMD_2024_10m",\n).add_to(m)\nm'
add('impervious','Extra · Bodenversiegelung (WMS)','Dasselbe Modul, ein anderer Dienst: Copernicus Imperviousness Density 2024 mit 10-m-Rasterzellen über dem Luftbild. Beide Layer haben eigene Schalter und Deckkraftregler.',['Map','WmsTileLayer × 2'],impervious_code,'impervious_surface.html','Copernicus Land Monitoring Service · IMD 2024 · 10 m. Die Datenwerte beschreiben 0–100 % versiegelte Fläche je Rasterzelle. Die Deckkraft ist ein separater Darstellungsregler. Quelle: https://doi.org/10.2909/f0bcb6f0-d775-4218-bec1-13adea01ff8f')
add('population','Extra · Bevölkerung als 3D-Säulen','Eine andere Kombination: Map und BarLayer visualisieren Zensus-2022-Werte für den Raum Berlin.',['Map','BarLayer'],'''from basemap3d import Map, BarLayer

m = Map(location=[52.51, 13.39], buildings=False,
        distance_m=34000, heading=0, pitch=-65)
BarLayer("data/berlin_population_1km.csv",
         height_scale=0.06, bar_width_m=800).add_to(m)
m''','population_berlin.html','Säulenhöhen sind eine thematische Skalierung. Die Daten und das vollständige Notebook stehen im Repository.')
add('population-context','Extra · Berlin ohne Themenlayer','Die Ausgangskarte des Bevölkerungsbeispiels: ohne Gebäude und ohne Säulen.',['Map'],'''from basemap3d import Map

m = Map(location=[52.51, 13.39], buildings=False,
        distance_m=34000, heading=0, pitch=-65)
m''','population_context.html','Ergänzen Sie BarLayer, um die Bevölkerungswerte einzublenden.')
add('trees-only','Extra · Bäume & Luftbild','Eine kleine Kombination ohne Abfrage: Gebäude, Luftbild und geschätzte 3D-Bäume.',['Map','WmsTileLayer','TreeLayer'],'''from basemap3d import Map, WmsTileLayer, TreeLayer

m = Map(location=[49.99892, 8.27412], zoom_start=16)
WmsTileLayer(opacity=0.7).add_to(m)
TreeLayer().add_to(m)
m''','mainz_trees.html','Automatisch geschätzte Bäume und Höhen. Keine präzise Vermessung.')
(d/'examples/index.html').write_text(head('Examples','../')+nav('../','examples')+'''<main class="shell"><div class="sectionbar"><div><div class="eyebrow">Schritt für Schritt</div><h1 style="font-size:34px;margin-bottom:0">Examples</h1></div><select id="example-select" aria-label="Beispiel auswählen">'''+''.join(f'<option value="{x["id"]}">{html.escape(x["title"])}</option>' for x in items)+'''</select></div><div class="steps" aria-label="Lernfolge">'''+''.join(f'<a href="#{x["id"]}" data-step="{x["id"]}">{i+1} · {name}</a>' for i,(x,name) in enumerate(zip(items[:6],['Map','Raster / WMS','Flächen','Abfrage','Bäume','Schatten'])))+'''<a href="#complete" data-step="complete">Komplett ↗</a></div>'''+bench(items[0]['title'],items[0]['description'],items[0]['modules'],items[0]['code'],items[0]['file'])+'''<div class="below"><span>Jedes Beispiel enthält den vollständigen Code für seine Kombination.</span><a id="notebook" href="https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_3D_5_Tasks.ipynb" target="_blank" rel="noopener">Notebook in Colab ↗</a></div></main>'''+footer+'<script>const examples='+json.dumps(items,ensure_ascii=False)+''';
function show(){const id=location.hash.slice(1)||'map';const x=examples.find(e=>e.id===id)||examples[0];document.getElementById('example-select').value=x.id;document.getElementById('example-title').textContent=x.title;document.getElementById('example-description').textContent=x.description;document.getElementById('example-note').textContent=x.note;document.getElementById('code').textContent=x.code;document.getElementById('modules').replaceChildren(...x.modules.map(m=>{const span=document.createElement('span');span.className='chip';span.textContent=m;return span;}));const f=document.getElementById('result');if(f.getAttribute('src')!==x.file)f.src=x.file;document.getElementById('result-link').href=x.file;document.querySelectorAll('[data-step]').forEach(a=>a.setAttribute('aria-current',String(a.dataset.step===x.id)));document.getElementById('copy').textContent='Copy code';const nb=x.id==='impervious'?'Impervious_Surface.ipynb':x.id.startsWith('population')?'Population_3D_Columns.ipynb':x.id==='trees-only'?'Mainz_Trees_3D.ipynb':'Mainz_Modules.ipynb';document.getElementById('notebook').href='https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/'+nb;}
document.getElementById('example-select').onchange=e=>location.hash=e.target.value;window.addEventListener('hashchange',show);show();'''+copyjs+'</script></body></html>')
(d/'getting-started.html').write_text(head('Get started','')+nav('','setup')+'''<main class="shell setup"><div class="eyebrow">Get started</div><h1>Your first map.</h1><p>Download the repository, then install from its root folder. Python 3.10+ and an internet connection are required.</p><pre>python -m pip install -e ".[notebook]"
python -m jupyterlab</pre><h2>Display or export.</h2><pre>from basemap3d import Map

m = Map(location=[50.0063, 8.2692], zoom_start=16)
m.save("results/map.html")
m</pre><p>In Jupyter, finish a cell with <code>m</code>. To open an exported scene locally, serve the folder with a local web server such as Go Live.</p><details><summary>Use Google Colab</summary><p>Open a notebook from Examples, connect a fresh runtime and run the setup cell first. The wrapper manages the Colab display server automatically.</p></details><div class="actions"><a class="button primary" href="examples/">Follow the examples →</a><a class="button" href="https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz">Repository ↗</a></div></main>'''+footer+'</body></html>')
# Keep previous public entry points as bookmarks into the unified examples.
for name,target in [('beispiele.html','map'),('trees.html','trees-only'),('population.html','population')]:
 (d/name).write_text('<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=examples/#'+target+'"><title>Examples · Basemap3D</title></head><body><a href="examples/#'+target+'">Open example →</a></body></html>')

old=json.loads((r/'Mainz_Trees_3D.ipynb').read_text());cells=old['cells'][:2]
cells[0]['source']=['# Basemap3D · Module und Kombinationen\n','Beispiele 1–4: Karte, Luftbild, Flächen und Gebäudeabfrage. Beispiele 5–6: Bäume, Luftbild und Schatten ohne Flächenabfrage.\n']
for x in items[:7]:
 cells.extend([{'cell_type':'markdown','metadata':{},'source':[f'## {x["title"]}\n',x['description']+'\n']},{'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':x['code'].splitlines(keepends=True)}])
old['cells']=cells;(r/'Mainz_Modules.ipynb').write_text(json.dumps(old,ensure_ascii=False,indent=1)+'\n')
print('Built module examples, documentation and notebook.')

extra=json.loads((r/'Mainz_Modules.ipynb').read_text());extra['cells']=extra['cells'][:2]+[
 {'cell_type':'markdown','metadata':{},'source':['# Bodenversiegelung als WMS-Layer\n','Zwei unabhängige Rasterlayer: Luftbild und Copernicus Imperviousness Density 2024 (10 m; Werte 0–100 %).\n']},
 {'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':impervious_code.splitlines(keepends=True)}]
(r/'Impervious_Surface.ipynb').write_text(json.dumps(extra,ensure_ascii=False,indent=1)+'\n')
