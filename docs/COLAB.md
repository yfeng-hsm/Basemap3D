# Open the examples in Google Colab

- [Open the five-step planning lab](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Mainz_3D_5_Tasks.ipynb)
- [Open the population-columns case](https://colab.research.google.com/github/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/Population_3D_Columns.ipynb)

The same links appear as Open in Colab badges in the README and both notebooks, and as buttons on the website. They open the GitHub notebook in Colab; they do not execute code without the student's action. A Google sign-in may be required.

## Run

1. Open a notebook through its button.
2. Run the first setup cell, then the remaining cells in order (or choose Run all).
3. The setup clones this public repository into `/content/basemapde-course`, installs it with the current runtime's Python and adds the source directory to the current kernel path.
4. The small CSV/GeoJSON examples are available in `data/`. `NearbyBuildings()` obtains OSM footprints for the supplied study polygons instead of depending on a fixed-city file.
5. A final map expression displays the interactive iframe; `save()` writes HTML under `results/` in the Colab file browser. Download the HTML before the runtime is discarded.

The setup is conditional and does nothing in local Jupyter. Existing Colab checkouts are preserved rather than reset; start a fresh runtime if you need a new repository version. No Drive mounting, API key, local GIS installation or GPU runtime is required. Standard Colab compute and network availability still apply.

Rendering uses the browser's WebGL2 and internet access to the map/model services. If an output frame is blocked, download its HTML and open it in a supported browser, or inspect the prebuilt website gallery. Notebook links, bootstrap execution in a clean Linux environment and browser HTML rendering can be checked independently; a link opening successfully is not proof that a signed-in Colab runtime has executed it.
