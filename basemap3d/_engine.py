"""Internal renderer. Public teaching API is exported from basemap3d."""
from pathlib import Path
import json
import math
import csv

SUPPORT=Path(__file__).resolve().parent / "assets"
STAGES={1:"Basiskarte, Gelände und 3D-Gebäude",2:"Rasterdaten: Luftbild und Transparenz",3:"Vektordaten: Untersuchungsflächen",4:"Räumliche Abfrage und Attribut-Popup",5:"Sonnenstand und Gebäudeschatten",6:"Bevölkerungsverteilung im 1-km-Gitter"}

def create_scene(title="basemap.de · 3D", center=(10.4515, 51.1657),
                 heading=25, pitch=-45, distance_m=900):
    if not (-180 <= center[0] <= 180 and -90 <= center[1] <= 90):
        raise ValueError("center must use [longitude, latitude].")
    if not -90 <= pitch < 0 or distance_m <= 0:
        raise ValueError("pitch must be in [-90, 0); distance_m must be positive.")
    return dict(task=1, title=title, center=list(center), heading=heading,
                pitch=pitch, distance_m=distance_m, use_terrain=True,
                basemap="map", start_parking=0, opacity=0.25,
                building_color="#eef2f3", roof_color="#91a8b8",
                raster_url="https://geo4.service24.rlp.de/wms/rp_dop20.fcgi",
                raster_layer="rp_dop20", raster_opacity=0.8,
                highlight_nearby=False, nearby_distance_m=75,
                sun_date="2026-10-25", sun_hour=13.0)

def _geojson(path):
    target = Path(path)
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection" or not data.get("features"):
        raise ValueError(f"{target.name} must be a non-empty FeatureCollection.")

    declaration = data.get("crs")
    if declaration:
        from pyproj import CRS, Transformer
        props = declaration.get("properties", {}) if isinstance(declaration, dict) else {}
        source = (declaration if isinstance(declaration, str) else
                  props.get("name") or props.get("href") or props.get("proj4") or props.get("wkt") or
                  ("EPSG:" + str(props["code"]) if "code" in props else None))
        if not source:
            raise ValueError("GeoJSON CRS must declare an EPSG code, WKT or PROJ definition.")
        try:
            transformer = Transformer.from_crs(CRS.from_user_input(source), "EPSG:4326", always_xy=True)
            def convert(coords):
                if isinstance(coords[0], (int, float)):
                    x, y = transformer.transform(coords[0], coords[1], errcheck=True)
                    return [x, y, *coords[2:]]
                return [convert(part) for part in coords]
            for feature in data["features"]:
                feature["geometry"]["coordinates"] = convert(feature["geometry"]["coordinates"])
                feature.pop("bbox", None)
            data.pop("crs", None)
            data.pop("bbox", None)
        except Exception as exc:
            raise ValueError("Could not transform the declared GeoJSON CRS to WGS84.") from exc

    def check_coordinates(coords):
        if not isinstance(coords, list) or not coords:
            raise ValueError("Geometry coordinates must not be empty.")
        if isinstance(coords[0], (int, float)):
            if len(coords) < 2 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in coords):
                raise ValueError("Geometry coordinates must contain finite numbers.")
            if not (-180 <= coords[0] <= 180 and -90 <= coords[1] <= 90):
                raise ValueError("GeoJSON must use WGS84 [longitude, latitude].")
        else:
            for part in coords:
                check_coordinates(part)

    palette = ["#ff7b54", "#21cbb8", "#c3a1ff", "#ffd35c", "#56b6ff"]
    for i, feature in enumerate(data["features"]):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("This teaching renderer supports Polygon and MultiPolygon.")
        check_coordinates(geometry.get("coordinates"))
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        if any(len(ring) < 4 or ring[0] != ring[-1] for polygon in polygons for ring in polygon):
            raise ValueError("Polygon rings must be closed and contain at least four coordinates.")
        props = feature.setdefault("properties", {})
        if props is None:
            props = feature["properties"] = {}
        props.setdefault("name", str(props.get("Name") or props.get("NAME") or props.get("Bezeichnung") or props.get("label") or feature.get("id") or f"Objekt {i + 1}"))
        props.setdefault("color", palette[i % len(palette)])
    return data

def _script_json(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False)
            .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))

def render(config):
    """Build a complete HTML document without downloading official 3D tiles."""
    config=dict(config)
    config["stage_description"]=STAGES[config["task"]]
    empty={"type":"FeatureCollection","features":[]}
    plots=_geojson(config["vector_file"]) if config["has_vector"] else empty
    buildings=empty
    if config["query_enabled"]:
        if config.get("buildings_file"):
            buildings=_geojson(config["buildings_file"])
            config['query_source_label']='Lokale Gebäude-Datei'
        else:
            from ._osm import fetch_around
            buildings=fetch_around(plots,config['nearby_max_distance_m'])
            config['query_source_label']='OSM automatisch für diese Flächen'
    bars=_bars(config['bars_file'],config['bar_value']) if config.get('bars_enabled') else []
    config.pop("vector_file", None)
    config.pop("buildings_file", None)
    config.pop("bars_file",None)
    page=(SUPPORT/"scene.html").read_text(encoding="utf-8")
    page=page.replace("__SCENE_CSS__",(SUPPORT/"scene.css").read_text(encoding="utf-8"))
    page=page.replace("__SCENE_JS__",(SUPPORT/"scene.js").read_text(encoding="utf-8"))
    page=page.replace("__CONFIG_JSON__",_script_json(config))
    page=page.replace("__GEOJSON_JSON__",_script_json(plots))
    page=page.replace("__BUILDINGS_JSON__",_script_json(buildings))
    return page.replace("__BARS_JSON__",_script_json(bars))


def _bars(path,value):
    """Load small thematic CSV data with explicit coordinates; never synthesize population."""
    rows=[]
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not {'longitude','latitude',value}<=set(reader.fieldnames or []):
            raise ValueError('Bar CSV needs longitude, latitude and the selected value column.')
        for number,row in enumerate(reader,2):
            try:lon,lat,val=float(row['longitude']),float(row['latitude']),float(row[value])
            except (TypeError,ValueError) as exc:raise ValueError(f'Invalid bar data at CSV line {number}.') from exc
            if not all(math.isfinite(x) for x in (lon,lat,val)) or not -180<=lon<=180 or not -90<=lat<=90 or val<0:
                raise ValueError(f'Invalid coordinates or negative/non-finite value at CSV line {number}.')
            rows.append(dict(longitude=lon,latitude=lat,value=val,
                             name=row.get('name') or row.get('cell_id') or str(number-1),
                             reference_date=row.get('reference_date','')))
    if not rows:raise ValueError('Bar CSV must contain at least one row.')
    return rows
