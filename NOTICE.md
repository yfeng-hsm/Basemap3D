# Third-party notices

The MIT licence in `LICENSE` applies to the original wrapper, documentation and example authoring code in this repository. It does not replace any third-party licence or service conditions.

- **OpenStreetMap extracts:** `data/parking.geojson`, `data/mainz_buildings_snapshot.geojson`, and their embedded copies in exported scenes are derived from OpenStreetMap, © OpenStreetMap contributors, under the [Open Database License](https://www.openstreetmap.org/copyright). German descriptions and display geometries have been added. Preserve attribution and comply with applicable database share-alike requirements when redistributing adapted databases.
- **Official basemap.de buildings, terrain and maps:** online services of GeoBasis-DE/BKG and the participating surveying authorities. The 3D service's linked conditions are documented in `docs/DATA.md`. No official 3D tile cache is included.
- **RLP DOP20:** online LVermGeoRP service, dl-de/by-2-0; keep the required source credit.
- **CesiumJS:** loaded remotely from its official CDN, not bundled. See [CesiumGS/cesium](https://github.com/CesiumGS/cesium) for its Apache-2.0 licence and third-party notices.
- **Folium:** used as an interface-design reference only. No Folium code or runtime is bundled. `basemapde` is not affiliated with or endorsed by Folium.

- **Population extract:** `data/berlin_population_1km.csv` and its embedded HTML copies derive from the official Zensus 2022 grid, © Statistische Ämter des Bundes und der Länder, 2024, dl-de/by-2-0. Modifications: rectangular selection, coordinate conversion and field names; published counts unchanged. See `data/berlin_population_1km.metadata.json`.
- **Shapely:** installed as a dependency for automatic building display margins; it retains its BSD licence and the terms of its GEOS dependency. No separate desktop GIS is required.
