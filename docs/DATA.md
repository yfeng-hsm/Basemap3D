# Data, attribution and limitations

## Source inventory

| Source | Used for | Storage and terms |
|---|---|---|
| [basemap.de 3D](https://basemap.de/produkte-und-dienste/3d/) / GeoBasis-DE/BKG | LoD2 buildings and matching DGM5 terrain | Online only. No building or terrain tiles are distributed in this repository. |
| [basemap.de raster map](https://basemap.de/produkte-und-dienste/web-raster/) | Map background | Online WMS; attribution stays visible. |
| [LVermGeoRP Open Data](https://lvermgeo.rlp.de/geodaten-geoshop/open-data) | DOP20 aerial-image raster | Online WMS, layer `rp_dop20`; dl-de/by-2-0. |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Five parking polygons and surrounding building footprints | Local GeoJSON extracts, retrieved 2026-10-25; ODbL. |
| [CesiumJS](https://cesium.com/platform/cesiumjs/) | Browser rendering library | Loaded from the official Cesium CDN; version 1.146 is fixed by the package. |

The BKG site currently links a [3D-Beta service licence](https://basemap.de/data/produkte/3d/lizenzen/lizenz_basemapde_3D-Beta.pdf). It permits test integration and presentation output but restricts extracting or retaining service data outside runtime use. This package therefore uses online streams rather than downloading official 3D tiles. Review the service's current conditions before a new publication or a use beyond this teaching example.

## Source credits

- basemap.de: `© GeoBasis-DE/BKG 2026`, with a modification note for the combined presentation.
- DOP20: `©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0, www.lvermgeo.rlp.de`.
- Local vector extracts: `© OpenStreetMap contributors`, ODbL, with links to [copyright and licence information](https://www.openstreetmap.org/copyright).

Keep source credits visible in HTML, screenshots and presentations. The read year 2026 does not imply that all imagery, building models and OSM features were acquired in the same year. DOP20's 20 cm pixel size is not a guarantee of positional accuracy or currency.

## Parkplatz-Fallbeispiele

| ID | Bezeichnung | OSM-Objekt | Hinweis |
|---|---|---|---|
| P1 | Schloss | [way 24317089](https://www.openstreetmap.org/way/24317089) | Offener Parkplatz am Schloss |
| P2 | Parken am Kaisertor | [way 44719298](https://www.openstreetmap.org/way/44719298) | Offener Parkplatz am Kaisertor |
| P3 | Bruchwegstadion (Südseite) | [way 19527749](https://www.openstreetmap.org/way/19527749) | Beschreibender Name nach benachbartem Ort |
| P4 | Dalheimer Weg | [way 4427008](https://www.openstreetmap.org/way/4427008) | Laut OSM privater Campusparkplatz für Studierende/Beschäftigte |
| P5 | Volkspark (Westseite) | [way 28226187](https://www.openstreetmap.org/way/28226187) | Beschreibender Name nach benachbartem Ort |

Die Flächen dienen der räumlichen Untersuchung, nicht der Parkplatznavigation. Sie sind keine Flurstücksgrenzen und belegen weder heutige Öffnung noch aktuelle Nutzungsrechte.

## Local files

`data/parking.geojson` preserves the five selected OSM polygons and adds German teaching names and descriptions. `data/buildings.geojson` combines surrounding OSM building ways and multipolygon relations, preserving holes where available. It contains 1,101 candidate footprints covering the five original areas and at least their 200 m surroundings. The files are a finite teaching snapshot, not a complete Mainz building database.

Each building feature keeps its original `geometry` for distance calculations. The additional `highlight_geometry` is a 3 m expanded display volume footprint, used only for colour classification. `highlight_margin_m` records that margin. OSM IDs and object types are retained for provenance. The original 3D-building IDs are not joined to these OSM features.

## Interpretation limits

- Whole footprints are selected by minimum approximate planar distance to any study polygon; a single footprint is counted once even if it is near multiple study polygons.
- Visible colour is applied spatially to official model geometry within selected display volumes. Coplanar walls, eaves, source offsets and different building subdivisions can affect coverage. The margin reduces but cannot eliminate mismatch, and may touch an immediately adjacent model part.
- Buildings beyond the camera view are still included in footprint counts; actual 3D tiles are streamed for the current view.
- Sun controls use date, local time and the geographical scene. Models cast ground shadows; self-shadow receiving is disabled to avoid thin-surface artefacts. Trees, weather and facade detail are not simulated.
- Photo shadows remain fixed. The scene is not a certified solar, thermal, traffic, cadastral or legal planning assessment.
