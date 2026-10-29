from point_io import read_points, write_points
"""Apply the selected archived C centre export while retaining extension candidates.
Usage: python tools/trees/apply_c_center.py /path/to/Mainz_Stadtmitte_C_GitHub_update.zip
The archive supplies nine estimated-height tile pairs and their aligned candidates.
"""
from pathlib import Path
import sys,json,zipfile,copy,hashlib,collections
ROOT=Path(__file__).resolve().parents[2];LAYER=ROOT/'docs/layers/mainz-trees'
def run(archive):
 z=zipfile.ZipFile(archive);prefix='docs/layers/mainz-trees/'
 old=read_points(LAYER/'data/tree_points.geojson')
 extension=[f for f in old if not f['properties']['tree_id'].startswith('mainz_center_')]
 center=json.loads(z.read(prefix+'data/tree_points.geojson'))['features']
 assert len(center)==26849 and len(extension)==27165
 for f in center:f['properties']['model_height_m']=f['properties']['height_m']
 features=center+extension
 assert len({f['properties']['tree_id'] for f in features})==len(features)
 write_points(LAYER/'data/tree_points.geojson.gz',features)
 review=[f for f in features if f['properties']['review_recommended']]
 (LAYER/'data/review_points.geojson').write_text(json.dumps(dict(type='FeatureCollection',features=review),separators=(',',':')))
 current=json.loads((LAYER/'tileset-estimated.json').read_text());cset=json.loads(z.read(prefix+'tileset-estimated.json'))
 def key(child):return child.get('content',{}).get('uri','').split('/')[-1].split('_coarse.glb')[0]
 replacements={key(child):child for child in cset['root']['children']}
 assert len(replacements)==9
 for i,child in enumerate(current['root']['children']):
  if key(child) in replacements:
   child=copy.deepcopy(replacements[key(child)]);current['root']['children'][i]=child
   for item in [child,*child.get('children',[])]:
    uri=item['content']['uri'];(LAYER/uri).write_bytes(z.read(prefix+uri));item['content']['uri']=uri+'?v=C20261029'
 current['asset']['tilesetVersion']='2026-10-29-C-center'
 current['asset']['extras'].update(candidate_tree_count=len(features),configuration='C_balanced centre; original extension',center_candidate_count=len(center),extension_candidate_count=len(extension))
 region=current['root']['boundingVolume']['region'];region[4]=min(f['properties']['ground_height_basemap_m'] for f in features)-2;region[5]=max(f['properties']['ground_height_basemap_m']+f['properties']['height_m'] for f in features)+2
 for name in ['tileset.json','tileset-estimated.json']:(LAYER/name).write_text(json.dumps(current,separators=(',',':')))
 summary=json.loads((LAYER/'data/processing_summary.json').read_text());extension_method=summary['method'];cmethod=json.loads(z.read(prefix+'data/processing_summary.json'))['method']
 counts=collections.Counter(f['properties']['tile'] for f in features)
 summary.update(candidate_tree_count=len(features),retained_original_candidates=0,replaced_original_candidates=13317,center_candidate_count=len(center),extension_candidate_count=len(extension),added_candidates=len(extension),height_range_m=[min(f['properties']['height_m'] for f in features),max(f['properties']['height_m'] for f in features)],height_over_30m_review_count=len(review),tile_counts={tile:counts[tile] for tile in summary['tile_counts']},method={'configuration':'mixed_spatial_processing','center':cmethod,'extension':extension_method},limits=['Automatic estimates, not an official tree inventory or field-verified.','Original nine centre cells replaced by the selected C_balanced archive.','Extension cells retained without reprocessing; their stricter original settings still apply.','2023 elevation and 2024 imagery are not simultaneous.'])
 (LAYER/'data/processing_summary.json').write_text(json.dumps(summary,indent=2))
 provenance=json.loads((LAYER/'provenance.json').read_text());provenance.pop('retained_original_candidates',None);provenance.pop('added_candidates',None)
 provenance.update(candidate_count=len(features),center_candidate_count=len(center),retained_extension_candidates=len(extension),configuration='C_balanced centre; original extension',center_archive_sha256=hashlib.sha256(Path(archive).read_bytes()).hexdigest(),center_bounds_epsg25832=[446000,5537000,449000,5540000],crown_scaling='C centre: area-equivalent diameter independent of model height; extension unchanged',center_ids_reassigned=True)
 (LAYER/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2))
 scripts=LAYER/'processing-scripts';scripts.mkdir(exist_ok=True)
 for name in ['process_center.py','build_tiles.py']:(scripts/('c_'+name)).write_bytes(z.read(prefix+'processing-scripts/'+name))
 (scripts/'README.md').write_text('The c_ scripts preserve the selected C archive processing code for provenance. They require the original rasters, OSM inputs and tree template; their original project paths must be adapted before running. To apply the already-generated archive reproducibly, use tools/trees/apply_c_center.py. This migration retains the wider extension dataset without rerunning it.\n')
 print(json.dumps({k:summary[k] for k in ['candidate_tree_count','center_candidate_count','extension_candidate_count','height_range_m','height_over_30m_review_count']}))
if __name__=='__main__':run(sys.argv[1])
