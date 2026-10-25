# basemapde API reference

`basemapde` is a deliberately small, independent teaching wrapper around CesiumJS. It adopts Folium's map-object workflow without promising Folium API compatibility. Package documentation and errors are English; the included Mainz scenes use German labels and descriptions.

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

The UI covers 0–200 m. It fetches candidate footprints for the full 200 m area once; changing the slider then filters locally. Responses are cached for 24 hours in `.basemapde-cache/`. Requests are limited to 12 small boxes; larger areas require a local file. Download failures abort the query rather than silently returning another area's data. OSM completeness is not guaranteed.

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

Both notebooks include an Open in Colab badge and a conditional setup cell. It clones the public repository into `/content/basemapde-course`, installs the package, adds its source directory to the current kernel path and changes to the course directory. Existing checkouts are preserved. A fresh Colab runtime gets the current `main` branch. See [COLAB.md](COLAB.md).
