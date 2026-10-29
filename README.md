# Basemap3D

**Build interactive 3D maps in Python, display them in Jupyter or Colab, and share them as HTML.**

Combine city meshes, detailed buildings, terrain, trees and your own geospatial data in one CesiumJS viewer. The Python interface follows a familiar pattern: create a `Map`, add layers with `.add_to(m)`, then display or save it.

**[Explore the examples](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/examples/) · [Documentation](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/) · [API reference](docs/API.md)**

## Start with a city model

After installing the package, run this in a notebook:

```python
from basemap3d import Map, Tiles3D

m = Map(location=[50.36, 7.60], distance_m=2500,
        buildings=False, title="Koblenz · 3D mesh")
Tiles3D(
    "https://dz.koblenz.de/assets/mesh_3D_2026/tileset.json",
    name="Koblenz mesh 2026",
    attribution="Stadt Koblenz · GeoPortal Koblenz",
    popup=False,
).add_to(m)
m
```

Replace the tileset URL and map location to use another compatible 3D Tiles service. `buildings=False` turns off the default building layer when displaying a city mesh.

To export the map:

```python
m.save("results/my_map.html")
```

The exported HTML streams its online layers when opened; it does not download the complete city model for offline use.

## What can I add?

| Content | Python interface | Examples |
|---|---|---|
| Photorealistic city meshes | `Tiles3D(url)` | Koblenz, Trier, Hamburg, Potsdam, Cottbus, Nürnberg, Wuppertal |
| Detailed building models | `Tiles3D(url)` | Hamburg LoD3; selected detailed models in Koblenz |
| Background maps, terrain and LoD2 buildings | `Map(...)` | Germany-wide defaults from basemap.de |
| Orthophotos and other WMS layers | `RasterLayer(...)` | Imagery and thematic overlays |
| Your own polygons and attributes | `GeoJson(...)` | Study areas and planning proposals |
| Buildings around your polygons | `NearbyBuildings(...)` | Interactive distance selection using OSM footprints |
| Schematic 3D trees | `TreeLayer()` | Hosted Mainz tree candidates |
| Thematic 3D columns | `BarLayer(...)` | Berlin population from Zensus 2022 |
| Place a yellow building interactively | `HousePlacement()` | Mainz; flat, gable and hip roof templates |
| Sun and shadows | `SunShadows(...)` | Explore different dates and times |

In the [basic examples](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/examples/), choose **Mesh models** or **LoD3 buildings**, then select a city above the Python code. The scene and code update together. Some entries are different views of the same service. Koblenz's detailed models cover selected objects, rather than the whole city.

## Run without local installation

Open a notebook in Google Colab and run its setup cell first, followed by the remaining cells:

| Notebook | Contents | Open |
|---|---|---|
| [Modules](Mainz_Modules.ipynb) | Build up a map layer by layer | [Colab](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_Modules.ipynb) |
| [Planning lab](Mainz_3D_5_Tasks.ipynb) | Five exercises with imagery, polygons, nearby buildings and shadows | [Colab](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_3D_5_Tasks.ipynb) |
| [Trees](Mainz_Trees_3D.ipynb) | Mainz trees and shadows | [Colab](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_Trees_3D.ipynb) |
| [Population](Population_3D_Columns.ipynb) | Berlin population as 3D columns | [Colab](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Population_3D_Columns.ipynb) |

The setup installs the package from this repository. Colab handles the map display through the package; no separate web server or GPU runtime is needed. See [Colab help](docs/COLAB.md).

## Install locally

Use Python **3.10+** and a browser with WebGL2. [Download](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/archive/refs/heads/main.zip) or clone this repository, open a terminal in its root directory, then run:

**macOS / Linux**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[notebook]"
.venv/bin/python -m jupyterlab
```

**Windows PowerShell**

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[notebook]"
.\.venv\Scripts\python.exe -m jupyterlab
```

Open a notebook and use that environment's kernel. The import name is `basemap3d`; installation is from this repository.

## Add your own data

```python
from basemap3d import Map, GeoJson, NearbyBuildings

m = Map(location=[49.999, 8.274], title="My study area")
GeoJson("my_study_area.geojson", popup=True).add_to(m)
NearbyBuildings(distance_m=75).add_to(m)
m
```

`NearbyBuildings` retrieves OSM building footprints around the polygons you add. Change the polygons to change the study area. For larger areas or repeatable offline footprint queries, supply a local building GeoJSON; see the [API reference](docs/API.md).

Map locations use **[latitude, longitude]**. GeoJSON coordinates use **[longitude, latitude]**, in WGS84. `distance_m` controls camera distance; `zoom_start` is an approximate alternative.

## Data and availability

City models are streamed from their providers. Availability, coverage, CORS settings and licences depend on each service. A working endpoint does not itself grant redistribution rights. Keep source attribution and check the provider's terms. The [city catalogue](docs/examples/city_sources.json) records URLs and source notes.

The Mainz tree layer currently contains **54,014 automatic candidates in a 7 × 4 km processing frame**. It uses estimated heights and schematic crowns, not a verified tree inventory. The original 3 × 3 km city centre now uses the selected **C_balanced** result (26,849 candidates). The surrounding extension retains its earlier extraction (27,165 candidates); it has not been reprocessed with C. See [tree data documentation](docs/layers/mainz-trees/README.md) and [processing parameters](docs/layers/mainz-trees/data/processing_summary.json). Tree shadows support qualitative exploration; they do not model foliage transmission or cooling.

The Berlin population example uses historical Zensus 2022 counts, referenced to 15 May 2022. Its rectangular extract is not the administrative city boundary.

Basemap3D uses CesiumJS for rendering and basemap.de for its default background, terrain and LoD2 buildings. It is an independent project. The Python code is MIT-licensed; datasets and external services retain their own terms. See [NOTICE](NOTICE.md) and [data sources and limitations](docs/DATA.md).

## More documentation

- [API reference](docs/API.md)
- [Teaching guide](docs/TEACHING.md)
- [Planning examples](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/beispiele.html)
- [Population example](https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/population.html)

If a scene is blank, check WebGL2 / hardware acceleration and access to the selected data services. GitHub's notebook preview cannot run interactive maps; use Colab, Jupyter or the HTML examples.

## Development

`basemap3d/` contains the Python API and viewer assets; `docs/` contains the website, examples and hosted tree tiles; `tools/` contains data-processing and gallery builders; `tests/` contains the automated checks.

```bash
python -m unittest discover -s tests -v
python tools/build_docs.py
```

GitHub Pages publishes the `docs/` directory from `main`. Some example builders access online services. Student exports belong in `results/`.

GeoJSON publication status (2026-10-29): The C_balanced 3D models contain 54,014 candidates. Candidate and review GeoJSON updates are deferred in this release; the existing GeoJSON files retain the earlier extraction and do not match the updated centre models. The viewer reads GLB metadata and does not require the candidate GeoJSON.
