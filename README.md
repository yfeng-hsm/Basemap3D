# Basemap3D · Unofficial Python wrapper for basemap.de

A city-independent, **Folium-style** Python interface to basemap.de's online maps, terrain and LoD2 buildings, rendered with CesiumJS. Create a `Map`, add layers with `.add_to(m)`, display `m` in Jupyter or Colab, and export with `m.save(...)`. The package is independent of the basemap.de providers and Folium; it is not an official SDK or a complete Folium-compatible API.

**Package documentation is English. The case studies, student exercises and viewer labels are German.** Mainz is one planning case; a separate Berlin population example demonstrates a different city and a different data theme.

[![Five-step planning lab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_3D_5_Tasks.ipynb) **Five-step planning lab**
[![Population columns](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Population_3D_Columns.ipynb) **Population columns**

Click a badge to open that notebook in Colab, then run its setup cell and the remaining cells. The setup clones this public repository, installs the wrapper and makes the supplied files available. Colab displays maps through its official runtime iframe proxy; the wrapper manages the small HTML server automatically. Students do not start Go Live or type server commands. A Google sign-in may be required. No local installation or GPU runtime is needed for Colab. It does not start executing merely by opening the link.

## Documentation and examples

- [English website](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/) · [German planning examples](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/beispiele.html) · [German population example](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/population.html)
- [Five-step notebook](Mainz_3D_5_Tasks.ipynb) · [Population notebook](Population_3D_Columns.ipynb)
- [API reference](docs/API.md) · [Colab instructions](docs/COLAB.md) · [data and limitations](docs/DATA.md) · [teaching guide](docs/TEACHING.md)
- [Download the complete repository ZIP](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/archive/refs/heads/main.zip)

The project is named **Basemap3D**; the Python import is `basemap3d`. It was previously named `basemapde`.

## Familiar usage

```python
from basemap3d import Map, GeoJson, NearbyBuildings

m = Map(location=[52.52, 13.405], zoom_start=16)
GeoJson("my_study_area.geojson", popup=True).add_to(m)
NearbyBuildings(distance_m=75).add_to(m)
m.save("results/my_map.html")
m
```

`Map(location=[latitude, longitude])` follows Folium. GeoJSON and CSV coordinates use WGS84 longitude and latitude. `zoom_start` is an approximate 3D camera-distance preset, not an exact Leaflet zoom; `distance_m` provides explicit control. The default map centres on Germany, not a particular city.

## Nearby buildings: no fixed-city dependency

**`NearbyBuildings()` derives its requests from the polygons you actually add.** It retrieves OSM building ways and multipolygon relations, including courtyard holes, around those geometries. Changing the polygon file or study location changes the requests. The local metric reference is also derived from the input, not fixed Mainz coordinates.

- The interactive query covers 0–200 m. Footprints are fetched for that full radius once, then filtering runs in the browser.
- Responses are cached locally for 24 hours in `.basemap3d-cache/`; this is OSM vector data, not an official 3D-tile cache.
- The lightweight downloader limits a request to 12 small API boxes. For larger study areas, use a suitable local building GeoJSON. Network failures are reported; there is no silent fallback to the demonstration sites.
- `NearbyBuildings("my_buildings.geojson", distance_m=75)` explicitly uses your local data instead.
- `data/mainz_buildings_snapshot.geojson` is an **optional offline teaching snapshot**, covering only the original Mainz sites. The main notebook now uses automatic retrieval by default.

Matching is still spatial classification of LoD2 geometry using OSM footprints, not a join on official building IDs. A separate 3 m display margin improves wall/eave coverage without changing selection or counts. Source discrepancies can remain. See [data limitations](docs/DATA.md).

## Population as 3D columns

```python
from basemap3d import Map, BarLayer

m = Map(location=[52.51, 13.39], buildings=False, distance_m=26000)
BarLayer("data/berlin_population_1km.csv", value="population",
         height_scale=0.06, bar_width_m=800).add_to(m)
m.save("results/population.html")
m
```

The Berlin case uses **657 published 1-km cells from Zensus 2022**, reference date **15 May 2022**, from the Statistische Ämter des Bundes und der Länder. Heights and colours encode published counts; these are not simulated numbers or building heights. The viewer provides a height-factor slider, a minimum-value filter, a fixed quantile colour legend and per-column popups.

The CSV is a rectangular Berlin-area extract, not the city boundary; its sum is not the official Berlin population total. Confidentiality perturbation applies, absent cells are not measured zeroes, and the figures are historical. [Provenance metadata](data/berlin_population_1km.metadata.json) records the archive, hash, coordinate conversion and extraction rule.

## Local installation

Use Python **3.10+** (3.11+ recommended), JupyterLab and a modern browser with WebGL2 and hardware acceleration. Download/unzip or clone the entire repository. Open a terminal in its root directory.

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[notebook]"
.venv/bin/python -m jupyterlab
```

### Windows PowerShell

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[notebook]"
.\.venv\Scripts\python.exe -m jupyterlab
```

These commands use the environment directly; no activation or execution-policy change is necessary. Installation includes the small Shapely dependency for automatic footprint display margins. Students do not need a desktop GIS, GeoPandas, Node.js, Docker, Folium or a Cesium ion account. The wrapper is installed from this repository; no PyPI release is implied.

Open either notebook using that environment's Python kernel, trust your own notebook, and run top to bottom. The Colab setup cell does nothing on a local runtime. JavaScript rendering happens in the browser; no GPU notebook runtime is required. Internet access is needed for the online services and automatic OSM retrieval.

## Five-step planning lab

| Task | Added capability | German case | Prebuilt HTML |
|---|---|---|---|
| 1 | Basemap, DGM5 terrain, LoD2 buildings | Stadtmodell am Schloss | [3D](docs/examples/task1_3d.html) |
| 2 | WMS raster and opacity | Luftbild als Rasterebene | [Raster](docs/examples/task2_raster.html) |
| 3 | GeoJSON study polygons | Fünf Parkplatzflächen | [Vector](docs/examples/task3_vector.html) |
| 4 | Automatic nearby-building query and popup | Gebäude im Umfeld | [Query](docs/examples/task4_query_popup.html) |
| 5 | Sun-based shadows | Tageszeit und Verschattung | [Shadows](docs/examples/task5_sun_shadows.html) |

Each task has at most seven lines of Python; the separate Colab setup is eight lines. Inputs stay in files, not in long notebook data literals. `.copy()` preserves earlier results. Student exports go to `results/`; checked-in gallery scenes live in `docs/examples/`.

The additional [population HTML](docs/examples/population_berlin.html) and [population notebook](Population_3D_Columns.ipynb) are independent of the five-step planning sequence.

## Repository layout

```text
basemap3d/                        # General Python wrapper and renderer assets
Mainz_3D_5_Tasks.ipynb             # German planning case; Colab ready
Population_3D_Columns.ipynb        # German Berlin population case; Colab ready
data/parking.geojson              # Planning case's study polygons
data/mainz_buildings_snapshot.geojson # Optional offline case snapshot
data/berlin_population_1km.csv     # Official published census counts
data/berlin_population_1km.metadata.json # Reproducible provenance
docs/                            # English docs, German examples and HTML gallery
tools/                           # Gallery builder; optional population preparation
tests/                           # API, portability and data-contract checks
results/                         # Generated locally; ignored by Git
.basemap3d-cache/                 # OSM response cache; ignored by Git
```

## Maintenance

```bash
python -m unittest discover -s tests -v
python tools/build_examples.py
python -m http.server 8000
```

Gallery rebuilding runs the notebook cells; the planning query may fetch OSM data for its polygons. Open `http://localhost:8000/docs/`. GitHub Pages publishes `main` → `/docs`. Original code is MIT; data and services retain their own terms in [NOTICE.md](NOTICE.md).

## Troubleshooting

- Missing `basemap3d`: install into the notebook's Python environment, or rerun the Colab setup.
- Blank notebook: trust your own output and test its exported HTML. GitHub source previews do not execute 3D code.
- Missing map/tiles: check WebGL2, hardware acceleration, and access to `cesium.com`, `sgx.geodatenzentrum.de`, and the selected raster service.
- Automatic OSM query fails: check access to `api.openstreetmap.org`, retry after a service interruption, reduce the area, or explicitly provide a local building file. No unrelated city data is substituted.
- New location has no matching cached data: automatic retrieval uses location-based cache keys; a manually supplied snapshot must be replaced by an appropriate file.
- Population interpretation: use the reference date and legend, not the visual column footprint, to interpret counts.
