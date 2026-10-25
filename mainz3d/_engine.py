"""Internal renderer. Public teaching API is exported from mainz3d."""
from pathlib import Path
import json
import math

BASE=Path(__file__).resolve().parents[1]
SUPPORT=Path(__file__).resolve().parent / "assets"
STAGES={1:"Basiskarte, Gelände und 3D-Gebäude",2:"Rasterdaten: Luftbild und Transparenz",3:"Vektordaten: fünf Parkplatzflächen",4:"Räumliche Abfrage und Attribut-Popup",5:"Sonnenstand und Gebäudeschatten"}

def create_scene(title="Mainz 3D", center=(8.2692, 50.0063),
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
    if not target.is_absolute():
        target = BASE / target
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection" or not data.get("features"):
        raise ValueError(f"{target.name} must be a non-empty FeatureCollection.")

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
        props.setdefault("name", f"Fläche {i + 1}")
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
    buildings=_geojson(config["buildings_file"]) if config["query_enabled"] else empty
    config.pop("vector_file", None)
    config.pop("buildings_file", None)
    page=(SUPPORT/"scene.html").read_text(encoding="utf-8")
    page=page.replace("__SCENE_CSS__",(SUPPORT/"scene.css").read_text(encoding="utf-8"))
    page=page.replace("__SCENE_JS__",(SUPPORT/"scene.js").read_text(encoding="utf-8"))
    page=page.replace("__CONFIG_JSON__",_script_json(config))
    page=page.replace("__GEOJSON_JSON__",_script_json(plots))
    return page.replace("__BUILDINGS_JSON__",_script_json(buildings))
