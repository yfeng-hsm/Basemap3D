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
 dict(id='potsdam-mesh', kind='mesh', city='Potsdam', location=[52.399,13.057], url='https://isk.geobasis-bb.de/geodienste/lgb/3d_sentinel/3dmeshes/potsdam10d/3d_tiles/tileset.json', credit='© GeoBasis-DE/LGB · dl-de/by-2-0', note='Photogrammetric mesh from the official Brandenburg 3D Tiles service. DL-DE/BY-2.0. Acquisition dates vary by survey block.'),
 dict(id='cottbus-mesh', kind='mesh', city='Cottbus', location=[51.76,14.334], url='https://isk.geobasis-bb.de/geodienste/lgb/3d_sentinel/3dmeshes/cottbus20d/3d_tiles/tileset.json', credit='© GeoBasis-DE/LGB · dl-de/by-2-0', note='Photogrammetric mesh from the official Brandenburg 3D Tiles service. DL-DE/BY-2.0. Acquisition dates vary by survey block.'),
 dict(id='hamburg-lod3-plain', kind='lod3', city='Hamburg · Untextured LoD3', location=[53.55,9.995], url='https://www.daten-hamburg.de/gdi3d/datasource-data/LoD3_untexturiert/tileset.json', credit='Freie und Hansestadt Hamburg · Landesbetrieb Geoinformation und Vermessung · dl-de/by-2-0', note='Official untextured LoD3.0-HH, for comparing detailed geometry with the textured service. DL-DE/BY-2.0.'),
 dict(id='koblenz-lod3', kind='lod3', city='Koblenz · Detailed models', location=[50.36,7.60], url='https://dz.koblenz.de/assets/tileset_lod3_3d/tileset.json', credit='Stadt Koblenz · GeoPortal Koblenz', note='Selected detailed models from the official viewer layer labelled LoD3; not a complete citywide LoD3 dataset. Third-party republication permission must be confirmed.'),

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
 items=[x for x in items if x['id'] not in ('mesh','lod3','population-context','trees-only')]
 items[1:1]=[next(x for x in variants if x['id']==kind) for kind in ('mesh','lod3')]
 numbers={'map':1,'mesh':2,'lod3':3,'imagery':4,'vectors':5,'query':6,'trees':7,'shadows':8}
 import re
 for item in items:
  if item['id'] in numbers:item['title']=str(numbers[item['id']])+' · '+re.sub(r'^\d+ · ', '',item['title'])
 for item in variants:item['title']=str(numbers[item['id']])+' · '+re.sub(r'^(?:\d+ · )+', '',item['title'])
 page=page[:start]+json.dumps(items,ensure_ascii=False)+page[end:]
 if 'id="city-select"' not in page:
  page=page.replace('<div class="codebox">','<label id="city-label" hidden>City / viewpoint <select id="city-select" aria-label="Choose city or viewpoint"></select></label><div class="codebox">',1)
  page=page.replace('<option value="imagery">','<option value="mesh">Mesh models</option><option value="lod3">LoD3 buildings</option><option value="imagery">',1)
  page=page.replace('<a href="#imagery"','<a href="#mesh" data-step="mesh">Mesh models</a><a href="#lod3" data-step="lod3">LoD3</a><a href="#imagery"',1)
  page=page.replace('const x=examples.find(e=>e.id===id)||examples[0];','let x=examples.find(e=>e.id===id)||examples[0];const choices=cityVariants.filter(v=>v.id===x.id);const city=document.getElementById("city-select");document.getElementById("city-label").hidden=!choices.length;if(choices.length){const chosen=city.value;city.replaceChildren(...choices.map(v=>{const o=document.createElement("option");o.value=v.file;o.textContent=v.city;return o;}));x=choices.find(v=>v.file===chosen)||choices[0];city.value=x.file;}')
  page=page.replace('window.addEventListener(\'hashchange\',show);','document.getElementById("city-select").onchange=show;window.addEventListener(\'hashchange\',show);')
 if 'const cityVariants=' in page:
  a=page.index('const cityVariants=')+len('const cityVariants=');_,n=json.JSONDecoder().raw_decode(page[a:]);page=page[:a]+json.dumps(variants,ensure_ascii=False)+page[a+n:]
 else:page=page.replace('function show(){','const cityVariants='+json.dumps(variants,ensure_ascii=False)+';\nfunction show(){',1)
 # Migrate galleries generated before the city picker moved into instructions.
 import re
 match=re.search(r'<label id="city-label"[^>]*>.*?</label>',page)
 if match:
  picker=match.group();page=page[:match.start()]+page[match.end():]
  page=page.replace('<div class="codebox">',picker+'<div class="codebox">',1)
 page=page.replace('</head>','<style>#city-label:not([hidden]){display:block;margin:18px 0 10px;font-size:12px;color:#527161}#city-select{display:block;width:100%;margin-top:6px;padding:10px 12px;border:1px solid #d5dfd6;border-radius:7px;background:white;color:#203a37;font:inherit}</style></head>',1) if '#city-label:not([hidden])' not in page else page
 for key,number in numbers.items():
  page=re.sub(r'(<option value="'+key+r'">)(.*?)(</option>)',lambda m:m[1]+str(number)+' · '+re.sub(r'^\d+ · ', '',m[2])+m[3],page)
  page=re.sub(r'(<a href="#'+key+r'"[^>]*>)(.*?)(</a>)',lambda m:m[1]+str(number)+' · '+re.sub(r'^\d+ · ', '',m[2])+m[3],page)
 path.write_text(page)
 (target/'city_sources.json').write_text(json.dumps(SOURCES,ensure_ascii=False,indent=2)+'\n')
 print('Built mesh and LoD3 gallery examples.')

if __name__=='__main__':main()
