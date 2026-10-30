# Open the examples in Google Colab

All notebooks live in [`../notebooks/`](../notebooks/).

- [Open Trier: mesh, buildings and shadows](https://colab.research.google.com/github/yfeng-hsm/Basemap3D/blob/main/notebooks/Trier_Shadow_Building_Preview.ipynb)

- [Open the five-step planning lab](https://colab.research.google.com/github/yfeng-hsm/Basemap3D/blob/main/notebooks/Mainz_3D_5_Tasks.ipynb)
- [Open the population-columns case](https://colab.research.google.com/github/yfeng-hsm/Basemap3D/blob/main/notebooks/Population_3D_Columns.ipynb)

The same links appear as Open in Colab badges in the README and the notebooks in `notebooks/`, and as buttons on the website. They open the GitHub notebook in Colab; they do not execute code without the student's action. A Google sign-in may be required.

- [Open the Mainz tree-layer case](https://colab.research.google.com/github/yfeng-hsm/Basemap3D/blob/main/notebooks/Mainz_Trees_3D.ipynb)

## Run

1. Open a notebook through its button.
2. Run the first setup cell, then the remaining cells in order (or choose Run all).
3. The setup clones this public repository into `/content/basemap3d-course`, installs it with the current runtime's Python and adds the source directory to the current kernel path.
4. The small CSV/GeoJSON examples are available in `data/`. `NearbyBuildings()` obtains OSM footprints for the supplied study polygons instead of depending on a fixed-city file.
5. A final map expression (for example `m`, or explicitly `m.show()`) displays the interactive scene through Colab’s official kernel-port iframe proxy; `save()` writes HTML under `results/` in the Colab file browser. Download the HTML before the runtime is discarded.

The setup is conditional and does nothing in local Jupyter. Existing Colab checkouts are preserved rather than reset; start a fresh runtime if you need a new repository version. No Drive mounting, API key, local GIS installation or GPU runtime is required. Standard Colab compute and network availability still apply.

## Why the Colab display backend is different

CesiumJS needs a working browser document, scripts, workers and WebGL2. A nested `srcdoc` output can behave differently from a normal HTTP page in Colab. Starting with version 0.3.0, a final map expression automatically serves the generated HTML from a small background server inside the Colab runtime and calls Google's official `output.serve_kernel_port_as_iframe`. Students do not start Go Live, run a server command, choose a port or open localhost.

Only registered scene HTML is served from memory; the notebook filesystem is not exposed. Each displayed result has an independent URL. The server stops when the Python runtime exits. This is still a real HTTP rendering environment, managed by the wrapper rather than by students.

The runtime must be connected and the cell must be executed again after reconnecting. These runtime URLs are temporary and should not be shared or embedded on a public site. Use `m.save("results/map.html")` for a durable export. Local Jupyter keeps the existing `srcdoc` iframe backend.

**Updating an already-open Colab:** start a fresh runtime and open the latest notebook through its badge before rerunning setup. An existing clone and already-imported Python module can retain an older wrapper. The setup intentionally preserves existing checkouts.

[Google’s official implementation of the iframe proxy](https://github.com/googlecolab/colabtools/blob/main/google/colab/output/_util.py).

Rendering uses the browser's WebGL2 and internet access to the map/model services. If an output frame is blocked, download its HTML and open it in a supported browser, or inspect the prebuilt website gallery. The scene server, Colab adapter and browser scene can be tested independently. A signed-in Colab runtime has not been exercised by this repository’s automated tests; opening the notebook link alone does not verify that runtime.
