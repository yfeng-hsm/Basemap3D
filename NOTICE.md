# Third-party notices

The MIT licence in `LICENSE` applies to the original wrapper, documentation and example authoring code in this repository. It does not replace any third-party licence or service conditions.

- **OpenStreetMap extracts:** `data/parking.geojson`, `data/mainz_buildings_snapshot.geojson`, and their embedded copies in exported scenes are derived from OpenStreetMap, © OpenStreetMap contributors, under the [Open Database License](https://www.openstreetmap.org/copyright). German descriptions and display geometries have been added. Preserve attribution and comply with applicable database share-alike requirements when redistributing adapted databases.
- **Official basemap.de buildings, terrain and maps:** online services of GeoBasis-DE/BKG and the participating surveying authorities. The 3D service's linked conditions are documented in `docs/DATA.md`. No official 3D tile cache is included.
- **RLP DOP20:** online LVermGeoRP service, dl-de/by-2-0; keep the required source credit.
- **CesiumJS:** loaded remotely from its official CDN, not bundled. See [CesiumGS/cesium](https://github.com/CesiumGS/cesium) for its Apache-2.0 licence and third-party notices.
- **Folium:** used as an interface-design reference only. No Folium code or runtime is bundled. `basemap3d` is not affiliated with or endorsed by Folium.

- **Population extract:** `data/berlin_population_1km.csv` and its embedded HTML copies derive from the official Zensus 2022 grid, © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0. Modifications: rectangular selection, coordinate conversion and field names; published counts unchanged. See `data/berlin_population_1km.metadata.json`.
- **Shapely:** installed as a dependency for automatic building display margins; it retains its BSD licence and the terms of its GEOS dependency. No separate desktop GIS is required.

## Mainz Stadtmitte tree candidates

The hosted dataset in `docs/layers/mainz-trees/` was imported unchanged from the earlier tree-generation project, with both height variants and all nine spatial tiles. It contains 13,317 unverified candidates; 29 estimates above 30 m are flagged. It is not a municipal tree inventory. Credits: ©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL (boundary/building masks). Source rasters date from 2023/2024. Original data terms remain applicable alongside the wrapper’s MIT licence. See the [dataset README](docs/layers/mainz-trees/README.md) for metadata, transformations, source URLs/hashes and stable endpoints.
