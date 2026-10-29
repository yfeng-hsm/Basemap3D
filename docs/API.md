# basemap3d API reference

`basemap3d` is a deliberately small, independent teaching wrapper around CesiumJS. It adopts Folium's map-object workflow without promising Folium API compatibility. Package documentation and errors are English; the included Mainz scenes use German labels and descriptions.

## Map

```python
Map(location=[51.1657, 10.4515], zoom_start=6,
    heading=25, pitch=-45, distance_m=None,
    height=700, title="basemap.de · 3D", tiles="basemap.de", buildings=True)
```

- `location`: **[latitude, longitude]**. GeoJSON uses the opposite order.
- `zoom_start`: 2–20. Converted to an approximate camera distance; this is not a Leaflet zoom level.
- `heading`: camera heading in degrees.
- `pitch`: camera angle in degrees, from −90 to less than 0.
- `distance_m`: optional explicit camera distance, overriding the zoom preset.
- `height`: notebook frame height, 200–2000 pixels.
- `tiles`: currently the `basemap.de` preset.
- `buildings`: set `False` for a thematic map where real LoD2 buildings would obscure the symbols. The default location is Germany-wide, not Mainz.

Basemap, online DGM5 terrain and matching LoD2 buildings are provided by the preset. If terrain initialization fails, the renderer uses the matching flat-ground building variant. Tile-loading errors are shown in the scene.

### Display, export and snapshots

```python
m                         # Display in Jupyter through _repr_html_
m.save("results/map.html") # Export the same scene; returns None
m2 = m.copy()             # Independent snapshot of configuration
m.show()                 # Explicit inline display; m alone also works
m.add_child(layer)        # Alternative to layer.add_to(m); returns m
```

Layer `.add_to(m)` methods modify `m` and return the layer, following the familiar Folium pattern. Map copies retain their existing configuration. When a layer is changed, the rendered document is regenerated. Recreate a map or re-add a layer after editing its input file.

Exported HTML embeds wrapper code, configuration and the stage's vector data. It does not embed or download CesiumJS, official imagery, terrain or building tiles. Internet access remains necessary. Source file paths are omitted from exported configuration.

## WmsTileLayer

```python
WmsTileLayer(
    url="https://geo4.service24.rlp.de/wms/rp_dop20.fcgi",
    layers="rp_dop20", opacity=0.8,
).add_to(m)
```

Adds the course's RLP DOP20 raster overlay. Opacity is 0–1; the scene also provides a live opacity slider and a basemap switch. This is a course preset with RLP bounds and attribution, not a general WMS client. Reusing another service requires adapting its coverage and attribution in the renderer.

## GeoJson

```python
GeoJson("data/parking.geojson", fill_opacity=0.25, popup=False).add_to(m)
```

Reads a **local** non-empty GeoJSON FeatureCollection containing Polygon or MultiPolygon geometry. Inputs use WGS84 `[longitude, latitude]`. Rings must be closed. The basic validator checks coordinate ranges and ring closure; it does not certify topology or detect every self-intersection.

Optional feature properties: `name`, `note`, `color`, `osm_id`, `osm_url`, `access`. Missing names and colours receive defaults. Use `#RRGGBB` colours. Popup text is escaped before HTML formatting. `popup=True` enables attribute popups even without a nearby-building query. Arbitrary point/line layers, remote GeoJSON URLs and Python style callbacks are outside this version's API.

## NearbyBuildings

```python
NearbyBuildings(distance_m=75, popup=True, enabled=True).add_to(m)
NearbyBuildings("my_buildings.geojson", distance_m=75).add_to(m)
```

Requires a polygon `GeoJson` layer and `Map(buildings=True)`. With no `data` argument, it derives geographic API boxes from the **current polygons**, fetches OpenStreetMap building ways/multipolygons, reconstructs holes and prepares 3 m display margins. There are no fixed Mainz query coordinates or fixed-city fallback. A changed study area generates different requests and cache keys.

The UI covers 0–200 m. It fetches candidate footprints for the full 200 m area once; changing the slider then filters locally. Responses are cached for 24 hours in `.basemap3d-cache/`. Requests are limited to 12 small boxes; larger areas require a local file. Download failures abort the query rather than silently returning another area's data. OSM completeness is not guaranteed.

Passing a local file explicitly disables automatic acquisition. `data/mainz_buildings_snapshot.geojson` is a documented, optional offline snapshot for the original parking case; it is not the package default. Local datasets must cover the desired polygons and distances.

Selection uses minimum local planar distance to any study polygon. Intersection/containment gives zero; holes are respected; duplicates across study areas count once per footprint. The local reference latitude/longitude is derived from the input. This approximation is intended for neighbourhood-scale German examples, not national-distance measurement.

Gold colour is spatial classification of the corresponding LoD2 geometry, not a join on the official building ID. Display margins improve coplanar-wall/eave coverage but can touch adjacent model parts. Counts include matched footprints outside the camera view; models stream for the visible view. `popup` controls polygon attributes, not official building metadata.

## SunShadows

```python
SunShadows(date="2026-10-25", hour=13.0).add_to(m)
```

Adds date and time controls. The UI covers 04:00–22:00 in 15-minute steps; dates cover 1900–2100. `Europe/Berlin` local time is converted to UTC with the browser's time-zone database before Cesium computes the sun direction. The UI is deliberately outside the ambiguous 02:00 clock-change interval.

LoD2 surfaces cast shadows on the ground. They do not receive self-shadowing in this teaching renderer, to avoid artefacts from thin model surfaces. Aerial-photo shadows remain fixed. Leaf-on vegetation, dynamic weather, street-level photorealism and certified solar analysis are not modelled.

## Adding layers independently

Raster and polygon layers can be used independently. `SunShadows` does not require the spatial-query layer. `NearbyBuildings` requires polygons because its distance rule needs a study area. The five-task notebook intentionally introduces these capabilities in a fixed teaching sequence.

## BarLayer

```python
BarLayer("data/berlin_population_1km.csv", value="population",
         height_scale=0.06, bar_width_m=800, opacity=0.9,
         legend_title="Bevölkerung je 1-km-Zelle", unit="Personen",
         attribution="© Statistische Ämter des Bundes und der Länder, 2024 · dl-de/by-2-0").add_to(m)
```

Reads a local CSV with `longitude`, `latitude` and a numeric `value` column. Optional columns: `cell_id`, `name`, `reference_date`. Coordinates must be finite WGS84 degrees; values must be finite and non-negative. No population values are invented or interpolated by the loader.

`height_scale` is metres per value unit; column height is `value × height_scale`. `bar_width_m` is the symbolic display width, not the source area used to compute a rate. Use `Map(buildings=False)` to keep real buildings distinct from thematic columns. Columns are positioned relative to terrain and do not cast physical-model shadows.

The thematic view uses a separate sidebar, a muted grey basemap, blue sequential colours and data-derived framing. “3D-Säulen” and “2D-Verteilung” switch camera views; the latter is a near-vertical view of the same columns, not a separate statistical aggregation. The German UI exposes a height-factor slider, minimum-value filter, fixed data-derived quantile colour classes, visible-column count and per-column popup. Filtering does not recompute the colour breaks. The `attribution` text is shown in the scene and should be supplied for shared maps. Each map currently has one primary CSV bar layer.

## Jupyter and Colab

Both notebooks include an Open in Colab badge and a conditional setup cell. It clones the public repository into `/content/basemap3d-course`, installs the package, adds its source directory to the current kernel path and changes to the course directory. Existing checkouts are preserved. A fresh Colab runtime gets the current `main` branch. See [COLAB.md](COLAB.md).

## Notebook display backends

`m` and `m.show()` use Colab’s official kernel-port iframe proxy when running in Colab. The wrapper starts a scene-only in-memory HTML server automatically; no student server command is needed. A connected runtime is required, and the output must be rerun after a runtime restart. Local Jupyter uses an embedded srcdoc iframe. `m.save(...)` always writes the same standalone scene HTML. See [Colab instructions](COLAB.md).

## Hosted 3D Tiles

```python
Tiles3D(url, name="3D Tiles", show=True, maximum_screen_space_error=12,
        attribution="", popup=True, feature_id_label=None, require_terrain=False)
TreeLayer(show=True, maximum_screen_space_error=12, base_url=None)
```

When sun shadows are enabled, generic hosted tilesets both cast and receive dynamic shadows. The schematic tree preset retains cast-only shadows. Shadows baked into mesh textures remain unchanged. The default LoD2 layer retains cast-only shadows to avoid thin-surface artefacts.

Both support `.add_to(m)` and can coexist with other map layers. Additions accumulate without changing previous map copies. `Tiles3D` takes an HTTP(S) root tileset URL, preserves the tileset transforms and streams relative content URLs in the browser. It does not upload or reproject local models. Use `feature_id_label` when the source defines labelled instance features. `require_terrain=True` prevents loading if the scene cannot initialize its basemap.de DGM5 terrain.

`TreeLayer` loads estimated-height trees for the 7 × 4 km Mainz frame (28 cells; one outside-mask cell is empty). Fixed heights and height-mode selection have been removed. The viewer offers visibility, extent and feature selection. `base_url` overrides the dataset directory. `m.save()` embeds hosted model URLs; gallery pages reference their adjacent dataset for self-hosted previews.

Feature popups display source metadata. Generic tilesets must provide supported feature metadata for picking; the tree preset uses the `tree` instance-feature label. The source data's licence and attribution must be supplied for generic services. [Tree dataset and limitations](layers/mainz-trees/README.md).

## GeoJSON CRS and object lists

`GeoJson(path)` accepts WGS84 longitude/latitude coordinates by default. A GeoJSON `crs` declaration (EPSG name/URN, WKT or PROJ definition) is transformed to WGS84 before rendering and spatial queries, using pyproj. The browser replacement upload uses Proj4js; common CRS definitions are included and other EPSG definitions are resolved online. Unsupported declarations fail without replacing the current layer.

The initial parking dataset is a single GeoJSON layer containing five objects. A browser upload replaces all its features and uses the filename as the layer label. Object names are read from common name fields, then ID or an automatic label. All accepted geometry is loaded onto the map; the list starts at 50 entries and Load more appends the next 50. Identically named objects retain independent selection. Browser uploads accept Polygon/MultiPolygon features, up to 5 MB and 20,000 coordinate vertices; the building downloader retains its 4 km² extent limit.

## Independent WMS raster layers

`WmsTileLayer(url, layers, opacity=0.8, *, name=None, attribution=None, description=None, styles="", format="image/png", transparent=True, version="1.1.1", crs="EPSG:4326", bounds=None, show=True, legend_url=None)` adds one independent raster overlay. Multiple calls accumulate layers, each with its own visibility and opacity control. `bounds` is optional and uses [west, south, east, north] in degrees; custom services have no fixed Mainz or RLP extent. Supported request CRS values are EPSG:4326 and EPSG:3857, using WMS 1.1.1. The service must allow cross-origin browser access. Add custom attribution and an optional GetLegendGraphic URL for thematic data. Calling without arguments retains the RLP DOP20 preset.

See the impervious-surface example: `../notebooks/Impervious_Surface.ipynb` and `examples/impervious_surface.html`. This combines DOP20 aerial imagery and the Copernicus Land Monitoring Service IMD 2024 WMS at 10 m resolution. Data values are 0–100% estimated artificial sealing per cell; layer opacity is an independent display setting. The endpoint is `https://geoserver.geoville.com/geoserver/nvlcc_2024/wms`, layer `HRL_NVLCC_IMD_2024_10m`. Source: https://doi.org/10.2909/f0bcb6f0-d775-4218-bec1-13adea01ff8f .

## Interactive building placement

```python
from basemap3d import Map, TreeLayer, HousePlacement
m = Map(location=[50.0063, 8.2692], distance_m=700)
TreeLayer().add_to(m)
HousePlacement().add_to(m)
m
```

`HousePlacement()` adds flat-roof (16 × 12 × 9 m), gable-roof (12 × 9 m, 6 m walls + 3 m roof) hip-roof (14 × 10 m, 6 m walls + 3 m roof) templates, and a green grass patch (12 × 8 m, tufts up to 0.45 m). Buildings are yellow; the grass patch follows terrain, with schematic low tufts. Choose a template, click **Choose location**, then click open ground to preview it. Adjust uniform scale (80–500%) before rotation, then confirm, cancel or undo the last placed building. Click Choose location again to move a preview.

Positions use the currently rendered terrain surface, with local east/north dimensions in metres. Existing buildings and trees remain visible. This is a schematic placement exercise with no collision, ownership or planning checks. Positions are not persisted when the page reloads and are not written back into Python or exported HTML. Terrain must initialize successfully to enable placement.
