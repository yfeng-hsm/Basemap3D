"""Fetch building footprints for the input polygons, not for a fixed demonstration city."""
import hashlib
import json
import math
from pathlib import Path
import time
from urllib.request import Request,urlopen

MAX_REQUESTS=12
TILE_SIZE=0.01
CACHE_SECONDS=86400


def _points(coords):
    if isinstance(coords[0],(int,float)):return [coords]
    return [point for part in coords for point in _points(part)]


def request_boxes(polygons,radius_m=200):
    """Cover each supplied feature and its radius. Limit calls instead of returning partial data."""
    boxes=[]
    for feature in polygons['features']:
        pts=_points(feature['geometry']['coordinates'])
        xs=[p[0] for p in pts];ys=[p[1] for p in pts]
        latitude=sum(ys)/len(ys)
        if abs(latitude)>85:raise ValueError('The automatic building fetch supports latitudes within ±85°.')
        dy=(radius_m+10)/111320
        dx=dy/math.cos(math.radians(latitude))
        west,east=min(xs)-dx,max(xs)+dx;south,north=min(ys)-dy,max(ys)+dy
        nx=max(1,math.ceil((east-west)/TILE_SIZE));ny=max(1,math.ceil((north-south)/TILE_SIZE))
        if nx*ny+len(boxes)>MAX_REQUESTS:
            raise ValueError('Study area too large for the lightweight OSM downloader (12 requests). Supply your own building GeoJSON or use a smaller area.')
        for ix in range(nx):
            for iy in range(ny):
                box=tuple(round(x,7) for x in (west+(east-west)*ix/nx,south+(north-south)*iy/ny,
                                               west+(east-west)*(ix+1)/nx,south+(north-south)*(iy+1)/ny))
                if not any(a<=box[0] and b<=box[1] and c>=box[2] and d>=box[3] for a,b,c,d in boxes):boxes.append(box)
    return boxes


def _download(box,cache_dir):
    key=hashlib.sha256(json.dumps(box).encode()).hexdigest()[:20]
    file=cache_dir/(key+'.json')
    if file.exists() and time.time()-file.stat().st_mtime<CACHE_SECONDS:
        return json.loads(file.read_text(encoding='utf-8'))
    url='https://api.openstreetmap.org/api/0.6/map.json?bbox='+','.join(map(str,box))
    request=Request(url,headers={'User-Agent':'basemapde-wrapper/0.2 teaching GIS (+https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz)'})
    try:
        with urlopen(request,timeout=30) as response:data=json.load(response)
    except Exception as exc:
        raise RuntimeError('Could not retrieve OSM buildings for the input polygons. Check network/service availability, retry later, or supply a local building GeoJSON. No fixed-city fallback was used.') from exc
    cache_dir.mkdir(parents=True,exist_ok=True)
    temporary=file.with_suffix('.tmp')
    temporary.write_text(json.dumps(data),encoding='utf-8');temporary.replace(file)
    return data


def _rings(parts,nodes):
    parts=[list(p) for p in parts];rings=[]
    while parts:
        ring=parts.pop()
        while ring[0]!=ring[-1]:
            found=False
            for i,p in enumerate(parts):
                if ring[-1]==p[0]:ring+=p[1:]
                elif ring[-1]==p[-1]:ring+=p[-2::-1]
                elif ring[0]==p[-1]:ring=p[:-1]+ring
                elif ring[0]==p[0]:ring=p[:0:-1]+ring
                else:continue
                parts.pop(i);found=True;break
            if not found:break
        if len(ring)>=4 and ring[0]==ring[-1] and all(n in nodes for n in ring):
            rings.append([[nodes[n]['lon'],nodes[n]['lat']] for n in ring])
    return rings


def from_elements(elements):
    """Reconstruct building ways and multipolygon relations, retaining courtyard holes."""
    from shapely.geometry import shape,mapping,Polygon
    from shapely.affinity import affine_transform
    lookup={(e['type'],e['id']):e for e in elements}
    nodes={i:e for (kind,i),e in lookup.items() if kind=='node'}
    ways={i:e for (kind,i),e in lookup.items() if kind=='way'}
    features=[];members=set()
    for (kind,rid),rel in lookup.items():
        tags=rel.get('tags',{})
        if kind!='relation' or tags.get('type')!='multipolygon' or tags.get('building') in (None,'no'):continue
        outer=[];inner=[]
        for member in rel['members']:
            if member['type']=='way' and member['ref'] in ways:
                (inner if member['role']=='inner' else outer).append(ways[member['ref']]['nodes'])
        rings=_rings(outer,nodes);holes=_rings(inner,nodes)
        if not rings:continue
        polygons=[[ring]+[hole for hole in holes if Polygon(ring).covers(Polygon(hole))] for ring in rings]
        features.append({'type':'Feature','properties':{'osm_id':rid,'osm_type':'relation','name':tags.get('name','')},
                         'geometry':{'type':'MultiPolygon','coordinates':polygons}})
        members.update(m['ref'] for m in rel['members'] if m['type']=='way')
    for wid,way in ways.items():
        tags=way.get('tags',{})
        if wid in members or tags.get('building') in (None,'no'):continue
        rings=_rings([way['nodes']],nodes)
        if rings:features.append({'type':'Feature','properties':{'osm_id':wid,'osm_type':'way','name':tags.get('name','')},
                                  'geometry':{'type':'Polygon','coordinates':[rings[0]]}})
    for feature in features:
        original=shape(feature['geometry'])
        if not original.is_valid:original=original.buffer(0)
        if original.is_empty:continue
        lon,lat=original.centroid.x,original.centroid.y
        sx=111320*math.cos(math.radians(lat));sy=111320
        projected=affine_transform(original,[sx,0,0,sy,-lon*sx,-lat*sy])
        expanded=projected.buffer(3,join_style=2)
        feature['highlight_geometry']=mapping(affine_transform(expanded,[1/sx,0,0,1/sy,lon,lat]))
        feature['highlight_margin_m']=3
    return {'type':'FeatureCollection','features':features,'source':'© OpenStreetMap contributors, ODbL'}


def fetch_around(polygons,radius_m=200,cache_dir=None):
    """Fetch complete requests atomically; cached responses expire after 24 hours."""
    cache_dir=Path(cache_dir) if cache_dir else Path.cwd()/'.basemapde-cache'
    elements=[]
    for box in request_boxes(polygons,radius_m):elements.extend(_download(box,cache_dir).get('elements',[]))
    result=from_elements(elements)
    result['query_scope']='Bounding boxes derived from the supplied polygon locations.'
    return result
