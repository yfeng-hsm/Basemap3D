# Data, attribution and limitations

## Source inventory

| Source | Used for | Storage and terms |
|---|---|---|
| [basemap.de 3D](https://basemap.de/produkte-und-dienste/3d/) / GeoBasis-DE/BKG | LoD2 buildings and matching DGM5 terrain | Online only. No building or terrain tiles are distributed in this repository. |
| [basemap.de raster map](https://basemap.de/produkte-und-dienste/web-raster/) | Map background | Online WMS; attribution stays visible. |
| [LVermGeoRP Open Data](https://lvermgeo.rlp.de/geodaten-geoshop/open-data) | DOP20 aerial-image raster | Online WMS, layer `rp_dop20`; dl-de/by-2-0. |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) | Five parking polygons and surrounding building footprints | Automatic neighbourhood requests or optional local GeoJSON extracts; ODbL. |
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

## Automatic building retrieval

`NearbyBuildings()` now derives OSM API requests from the input polygons, with 200 m coverage and a 24-hour local response cache. It does not read a fixed five-site building file by default. The query projection origin is derived from the data. The downloader limits the number of small requests; supply your own file for larger areas. Failed requests are reported, not replaced with demonstration data.

The following Mainz snapshot is retained only as an explicit offline teaching input. Automatic OSM data can differ from this historical extract because the source changes.

## Optional local planning files

`data/parking.geojson` preserves the five selected OSM polygons and adds German teaching names and descriptions. `data/mainz_buildings_snapshot.geojson` combines surrounding OSM building ways and multipolygon relations, preserving holes where available. It contains 1,101 candidate footprints covering the five original areas and at least their 200 m surroundings. The files are a finite teaching snapshot, not a complete Mainz building database.

Each building feature keeps its original `geometry` for distance calculations. The additional `highlight_geometry` is a 3 m expanded display volume footprint, used only for colour classification. `highlight_margin_m` records that margin. OSM IDs and object types are retained for provenance. The original 3D-building IDs are not joined to these OSM features.

## Interpretation limits

- Whole footprints are selected by minimum approximate planar distance to any study polygon; a single footprint is counted once even if it is near multiple study polygons.
- Visible colour is applied spatially to official model geometry within selected display volumes. Coplanar walls, eaves, source offsets and different building subdivisions can affect coverage. The margin reduces but cannot eliminate mismatch, and may touch an immediately adjacent model part.
- Buildings beyond the camera view are still included in footprint counts; actual 3D tiles are streamed for the current view.
- Sun controls use date, local time and the geographical scene. Models cast ground shadows; self-shadow receiving is disabled to avoid thin-surface artefacts. Trees, weather and facade detail are not simulated.
- Photo shadows remain fixed. The scene is not a certified solar, thermal, traffic, cadastral or legal planning assessment.

## Population grid: Berlin-area case study

The additional CSV uses the official **Zensus 2022 population counts**, reference date **15 May 2022**, from Statistische Ämter des Bundes und der Länder. Source: [official download page](https://www.destatis.de/DE/Themen/Gesellschaft-Umwelt/Bevoelkerung/Zensus2022/_publikationen.html), [original archive](https://www.destatis.de/static/DE/zensus/gitterdaten/Zensus2022_Bevoelkerungszahl.zip), member `Zensus2022_Bevoelkerungszahl_1km-Gitter.csv`.

The archive's data description credits **© Statistische Ämter des Bundes und der Länder, 2024** and specifies **dl-de/by-2-0**. Preserve the credit and modification note. The repository includes a subset, not the national archive.

`data/berlin_population_1km.csv` contains 657 positive published 1-km cells whose centres fall inside `[13.18, 52.40, 13.60, 52.62]` (west, south, east, north). The rectangle is not Berlin's administrative boundary. Its published-count sum is 3,327,130 and its maximum is 24,164 per cell; neither number is a new official city total. Original counts are unchanged. Source EPSG:3035 cell centres were reprojected to EPSG:4326.

`data/berlin_population_1km.metadata.json` records the archive hash, clipping rule, date and transformations. Maintainers can reproduce it with `tools/prepare_population.py --archive ...` after installing `pyproj`; students running the prepared notebook do not need pyproj.

The source uses Cell-Key confidentiality processing, so some published counts are perturbed. Missing cells can reflect non-residential areas or unpublished data and are not measured zeroes. This is a 2022 snapshot, not current population, household addresses or live occupancy.

Each column symbol represents an original equal-area 1-km cell. Its 800 m display width is a graphic choice; population is not divided by that smaller footprint. Colour classes and heights encode counts; the height factor is cartographic, not a physical building height.
