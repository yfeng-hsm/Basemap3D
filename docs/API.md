# mainz3d API reference

`mainz3d` is a deliberately small, independent teaching wrapper around CesiumJS. It adopts Folium's map-object workflow without promising Folium API compatibility. Package documentation and errors are English; the included Mainz scenes use German labels and descriptions.

## Map

```python
Map(location=[50.0063, 8.2692], zoom_start=16,
    heading=25, pitch=-45, distance_m=None,
    height=700, title="Mainz 3D", tiles="basemap.de")
```

- `location`: **[latitude, longitude]**. GeoJSON uses the opposite order.
- `zoom_start`: 10–20. Converted to an approximate camera distance; this is not a Leaflet zoom level.
- `heading`: camera heading in degrees.
- `pitch`: camera angle in degrees, from −90 to less than 0.
- `distance_m`: optional explicit camera distance, overriding the zoom preset.
- `height`: notebook frame height, 200–2000 pixels.
- `tiles`: currently the `basemap.de` preset.

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
NearbyBuildings("data/buildings.geojson", distance_m=75,
                popup=True, enabled=True).add_to(m)
```

Requires a polygon `GeoJson` layer first. `distance_m` is 0–200 for the supplied data. `enabled` controls initial gold highlighting; the UI can change it later. `popup` enables parking attributes, not per-building metadata popups.

The query finds the minimum local planar distance between each original OSM footprint and any study polygon. Intersection and containment produce distance 0; holes are respected. The union of matches across study polygons is counted once per footprint. The count includes matched footprints beyond the current camera view, while 3D models stream for the visible view.

Selected footprints define classification volumes for colouring visible LoD2 geometry. `highlight_geometry` contains a precomputed 3 m visual margin; `geometry` remains the query input. The margin addresses coincident walls, eaves and small offsets. This is **not** a join on the official model's building ID; larger source discrepancies or missing OSM footprints can remain. The bundled data contains 1,101 candidate footprints, not 1,101 guaranteed selectable official buildings.

## SunShadows

```python
SunShadows(date="2026-10-25", hour=13.0).add_to(m)
```

Adds date and time controls. The UI covers 04:00–22:00 in 15-minute steps; dates cover 1900–2100. `Europe/Berlin` local time is converted to UTC with the browser's time-zone database before Cesium computes the sun direction. The UI is deliberately outside the ambiguous 02:00 clock-change interval.

LoD2 surfaces cast shadows on the ground. They do not receive self-shadowing in this teaching renderer, to avoid artefacts from thin model surfaces. Aerial-photo shadows remain fixed. Leaf-on vegetation, dynamic weather, street-level photorealism and certified solar analysis are not modelled.

## Adding layers independently

Raster and polygon layers can be used independently. `SunShadows` does not require the spatial-query layer. `NearbyBuildings` requires polygons because its distance rule needs a study area. The five-task notebook intentionally introduces these capabilities in a fixed teaching sequence.
