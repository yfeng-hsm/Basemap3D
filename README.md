# GISProjekt26 HS Mainz · mainz3d

A five-step urban GIS lab with a **Folium-style Python interface** and a CesiumJS renderer. Students create a map, add layers with `.add_to(m)`, display the map in Jupyter, and save an interactive HTML page. No coordinates, large data literals or JavaScript blocks are pasted into the notebook.

**Package documentation is in English. The Mainz case studies, exercises and viewer interface are in German.** `mainz3d` is an independent teaching wrapper; it is not Folium, a Folium plugin or a complete Folium-compatible API.

## Start here

- [Five-step notebook](Mainz_3D_5_Tasks.ipynb)
- [Live web documentation (English)](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/)
- [Live case studies (German)](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/beispiele.html)
- [Web documentation source](docs/index.html) — open this file locally after downloading the repository.
- [German case-study page](docs/beispiele.html)
- [API reference](docs/API.md), [teaching guide](docs/TEACHING.md), [data and limitations](docs/DATA.md)
- [Download the complete repository as ZIP](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/archive/refs/heads/main.zip)

GitHub's source viewer does not execute interactive notebook or HTML output. Run the notebook locally, open the exported HTML files in a browser, or use the live GitHub Pages links above. Hosting is configured from `main` → `/docs`; maintenance instructions are in [docs/HOSTING.md](docs/HOSTING.md).

## What students need to install

| Requirement | Purpose |
|---|---|
| Python **3.10 or newer**; Python 3.11+ recommended for the course | Runs the small Python wrapper |
| JupyterLab and IPython | Opens and displays the notebook; installed by the command below |
| A current browser with WebGL2 and hardware acceleration | Renders interactive 3D scenes |
| Internet access | Loads CesiumJS, basemap.de, terrain and RLP aerial imagery |

Windows, macOS and Linux can use the same notebook. Students do **not** need to install QGIS, GeoPandas, Shapely, Node.js, Docker or Cesium as a desktop application. Folium itself is not required. The supplied services do not require a student API key or a Cesium ion account in this configuration.

## Install and run

Download and unzip the **whole repository**, or clone it. Keep `mainz3d/`, `data/` and the notebook together. Open a terminal **inside the repository directory**.

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

These commands use the virtual environment directly, so activation and PowerShell execution-policy changes are unnecessary. `python -m pip install -r requirements.txt` is an equivalent installation command when the intended environment is already selected.

In JupyterLab, open **Mainz_3D_5_Tasks.ipynb**, select the installed environment's Python kernel, and run the cells from top to bottom. Trust your own notebook if Jupyter asks before running its HTML/JavaScript output. First loading can take a while because models are streamed online.

## A familiar usage pattern

```python
from mainz3d import Map, GeoJson

m = Map(location=[50.0063, 8.2692], zoom_start=16)
GeoJson("data/parking.geojson", popup=True).add_to(m)
m.save("results/mainz.html")
m
```

The last expression displays the interactive map in Jupyter. `save()` exports the same scene as HTML. In a regular Python script, use `save()` and open the file in a browser.

**Coordinate order matters:** `Map(location=[latitude, longitude])` follows Folium. GeoJSON uses WGS84 `[longitude, latitude]`. `zoom_start` is an approximate camera-distance preset, not an exact Leaflet zoom; use `distance_m` for an explicit camera distance.

## The five tasks and their results

Each task uses a copy of the previous map. Later layers do not change earlier snapshots. Each task contains at most **seven lines of Python**.

| Task | Added capability | German case study | HTML result |
|---|---|---|---|
| 1 | Basemap, matching DGM5 terrain and LoD2 buildings | Stadtmodell am Schloss | [task1_3d.html](docs/examples/task1_3d.html) |
| 2 | WMS raster overlay and opacity control | Luftbild als Rasterebene | [task2_raster.html](docs/examples/task2_raster.html) |
| 3 | GeoJSON polygons, colours and navigation | Fünf Parkplatzflächen | [task3_vector.html](docs/examples/task3_vector.html) |
| 4 | Distance query, gold highlight, result count and popup | Gebäude im Umfeld | [task4_query_popup.html](docs/examples/task4_query_popup.html) |
| 5 | Date and local-time controls for model shadows | Tageszeit und Verschattung | [task5_sun_shadows.html](docs/examples/task5_sun_shadows.html) |

The notebook writes newly generated files to **results/**. The checked-in **docs/examples/** files are prebuilt gallery snapshots, so students can inspect each outcome before running Python. Download these files to open them locally; GitHub's file viewer shows their source.

## Repository layout

```text
Mainz_3D_5_Tasks.ipynb     # Short teaching cells and German exercises
mainz3d/                  # Python wrapper and renderer assets
data/                     # Local GeoJSON inputs, not code literals
docs/index.html           # English web introduction to the wrapper
docs/beispiele.html       # German case-study guide
docs/examples/            # Five prebuilt standalone HTML scenes
docs/API.md               # Supported Python API and conventions
docs/DATA.md              # Provenance, attribution and limitations
docs/TEACHING.md           # Lesson sequence and assessment
tools/build_examples.py   # Rebuild the gallery from the notebook cells
tests/                    # Small API and packaging checks
results/                  # Student outputs; created locally and ignored by Git
```

## Instructor maintenance

From the repository root, with the environment selected:

```bash
python -m unittest discover -s tests -v
python tools/build_examples.py
python -m http.server 8000
```

Open [http://localhost:8000/docs/](http://localhost:8000/docs/) to preview the documentation and gallery. The HTTP server is optional; exported scenes also work when opened as local HTML in browsers that allow the required online requests.

## Data, scope and limitations

- Buildings and terrain come from **basemap.de / GeoBasis-DE/BKG** and remain online services. The repository does not cache their tiles.
- The raster example uses **LVermGeoRP DOP20** under dl-de/by-2-0. It is aerial imagery, not satellite imagery; it does not add facade textures.
- Parking and building footprints come from **© OpenStreetMap contributors**, ODbL, retrieved **2026-10-25**. The bundled building data covers the original five parking sites and their 200 m surroundings. A different study area needs new footprint data.
- Queries measure approximate local planar distance from original building footprints to **any** study polygon. Counts refer to OSM footprints. A separate 3 m display margin reduces uncoloured walls and eaves; it does not change the query distance. Differences from official LoD2 geometry can remain.
- Model shadows follow the sun at the selected date and **Europe/Berlin** local time, including daylight saving. Shadows already present in the aerial photo do not move. This is a teaching visualization, not a certified daylight, thermal or traffic analysis.

See [docs/DATA.md](docs/DATA.md) for full source links, credits and the scope of the bundled data. Preserve the visible source credits in screenshots and shared HTML.

## Troubleshooting

| Symptom | Check |
|---|---|
| `No module named mainz3d` | Run the editable install from this directory; use that environment's Jupyter kernel. |
| Empty output in GitHub | GitHub does not execute this viewer. Run Jupyter locally or open an HTML gallery file. |
| Empty notebook frame | Trust your own notebook and rerun; test the saved HTML separately. |
| Blank map or missing tiles | Check WebGL2/hardware acceleration and access to `cesium.com`, `sgx.geodatenzentrum.de`, and `geo4.service24.rlp.de`. |
| Data file not found | Start from the repository root; keep `data/` with the course. |
| A building is only partly highlighted | OSM and LoD2 may differ. The 3 m display margin helps but is not object-ID matching. |

Original wrapper code is released under [MIT](LICENSE). Third-party data, services and libraries retain their own terms; see [NOTICE.md](NOTICE.md).
