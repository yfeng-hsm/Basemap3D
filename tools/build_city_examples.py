"""Build hosted mesh/LoD3 examples and add them to the basic gallery."""
from pathlib import Path
import json
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from basemap3d import Map, Tiles3D

SOURCES = [
 dict(id='koblenz', kind='mesh', city='Koblenz', location=[50.36,7.60], url='https://dz.koblenz.de/assets/mesh_3D_2026/tileset.json', credit='Stadt Koblenz · GeoPortal Koblenz', note='Photorealistic mesh 2026. Third-party republication permission must be confirmed with Stadt Koblenz.'),
 dict(id='trier', kind='mesh', city='Trier', location=[49.756,6.643], url='https://data.geoportal-trier.de/ma_tiles/mesh2025/3d_tiles/tileset.json', credit='Stadt Trier', note='Photorealistic mesh 2025. Municipal service terms apply; confirm third-party republication permission.'),
 dict(id='hamburg-mesh', kind='mesh', city='Hamburg', location=[53.543,9.991], url='https://www.daten-hamburg.de/gdi3d/datasource-data/3D_Mesh_Cesium_2022/3Dtiles_reduziert-aufgeloest/tileset.json', credit='Freie und Hansestadt Hamburg · Landesbetrieb Geoinformation und Vermessung · dl-de/by-2-0', note='Reduced-resolution photorealistic mesh. Published mesh dataset 2022; source imagery may be older. DL-DE/BY-2.0.'),
 dict(id='hamburg-lod3', kind='lod3', city='Hamburg · City centre', location=[53.55,9.995], url='https://www.daten-hamburg.de/gdi3d/datasource-data/LoD3_tex20cm/tileset.json', credit='Freie und Hansestadt Hamburg · Landesbetrieb Geoinformation und Vermessung · dl-de/by-2-0', note='Official LoD3.0-HH: detailed roof geometry and aerial-image textures. DL-DE/BY-2.0. Not every visible window is modelled geometry.'),
 dict(id='hamburg-harburg', kind='lod3', city='Hamburg · Harburg', location=[53.46,9.983], url='https://www.daten-hamburg.de/gdi3d/datasource-data/LoD3_tex20cm/tileset.json', credit='Freie und Hansestadt Hamburg · Landesbetrieb Geoinformation und Vermessung · dl-de/by-2-0', note='Same LoD3.0-HH service, Harburg viewpoint. DL-DE/BY-2.0.'),
]

def main():
 target=ROOT/'docs/examples'
 variants=[]
 for s in SOURCES:
  code=(f'from basemap3d import Map, Tiles3D\n\nm = Map(location={s["location"]!r}, distance_m=1800,\n        buildings=False, title={s["city"]!r})\nTiles3D(\n    {s["url"]!r},\n    name={s["city"]!r},\n    attribution={s["credit"]!r},\n    popup=False,\n).add_to(m)\nm')
  scope={};exec(code,scope)
  filename='city_'+s['id']+'.html';scope['m'].save(target/filename)
  variants.append(dict(id=s['kind'],city=s['city'],title=('Mesh models' if s['kind']=='mesh' else 'LoD3 buildings')+' · '+s['city'],description='Stream external 3D Tiles with the same Tiles3D interface. Switch the city or viewpoint to update the scene and Python code.',modules=['Map','Tiles3D'],code=code,file=filename,note=s['note']))
 path=target/'index.html';page=path.read_text()
 start=page.index('const examples=')+len('const examples=');items,end=json.JSONDecoder().raw_decode(page[start:]);end+=start
 items=[x for x in items if x['id'] not in ('mesh','lod3')]
 items[1:1]=[next(x for x in variants if x['id']==kind) for kind in ('mesh','lod3')]
 page=page[:start]+json.dumps(items,ensure_ascii=False)+page[end:]
 if 'id="city-select"' not in page:
  page=page.replace('</select></div><div class="steps"','</select><label id="city-label" hidden>City / viewpoint <select id="city-select" aria-label="Choose city or viewpoint"></select></label></div><div class="steps"',1)
  page=page.replace('<option value="imagery">','<option value="mesh">Mesh models</option><option value="lod3">LoD3 buildings</option><option value="imagery">',1)
  page=page.replace('<a href="#imagery"','<a href="#mesh" data-step="mesh">Mesh models</a><a href="#lod3" data-step="lod3">LoD3</a><a href="#imagery"',1)
  page=page.replace('const x=examples.find(e=>e.id===id)||examples[0];','let x=examples.find(e=>e.id===id)||examples[0];const choices=cityVariants.filter(v=>v.id===x.id);const city=document.getElementById("city-select");document.getElementById("city-label").hidden=!choices.length;if(choices.length){const chosen=city.value;city.replaceChildren(...choices.map(v=>{const o=document.createElement("option");o.value=v.file;o.textContent=v.city;return o;}));x=choices.find(v=>v.file===chosen)||choices[0];city.value=x.file;}')
  page=page.replace('window.addEventListener(\'hashchange\',show);','document.getElementById("city-select").onchange=show;window.addEventListener(\'hashchange\',show);')
 if 'const cityVariants=' in page:
  a=page.index('const cityVariants=')+len('const cityVariants=');_,n=json.JSONDecoder().raw_decode(page[a:]);page=page[:a]+json.dumps(variants,ensure_ascii=False)+page[a+n:]
 else:page=page.replace('function show(){','const cityVariants='+json.dumps(variants,ensure_ascii=False)+';\nfunction show(){',1)
 path.write_text(page)
 (target/'city_sources.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2)+'\n')
 print('Built mesh and LoD3 gallery examples.')

if __name__=='__main__':main()
