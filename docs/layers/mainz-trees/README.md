# Mainz Stadtmitte trees · hosted 3D Tiles

This static dataset contains **13,317 automatically detected candidate trees**, covering a 3 × 3 km processing frame split into **nine 1-km² tiles**. The Mainz municipal mask retains approximately 8.039 km² of that frame. This is not a verified municipal tree inventory.

## Stable endpoints

- Uniform 15 m height: `https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees/tileset.json`
- Estimated height: `https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees/tileset-estimated.json`
- Metadata: `https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees/provenance.json`

Both variants use the same positions, candidate IDs and nine spatial tiles. Each tile has a coarse and fine GLB, selected by Cesium's level-of-detail rendering: 18 GLBs per variant, 36 total. Counts are not doubled when switching LOD or height variant. Keep the relative `tiles/` directory with both tileset files when self-hosting.

## Python

```python
from basemap3d import Map, TreeLayer

m = Map(location=[49.99892, 8.27412], zoom_start=16)
TreeLayer(variant="uniform").add_to(m)
m
```

The German viewer provides a visibility toggle, height-mode selector, layer extent button and feature popup. The selector replaces the old tileset rather than drawing both variants together.

Use any compatible hosted dataset through the general interface:

```python
from basemap3d import Tiles3D
Tiles3D("https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees/tileset.json",
        name="Mainz trees", feature_id_label="tree", require_terrain=True,
        attribution=TreeLayer.ATTRIBUTION).add_to(m)
```

## Direct Cesium use

```javascript
const trees = await Cesium.Cesium3DTileset.fromUrl(
  "https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees/tileset.json",
  { instanceFeatureIdLabel: "tree", maximumScreenSpaceError: 12 }
);
viewer.scene.primitives.add(trees);
```

No API key or custom backend is required. HTTPS access and WebGL are required. The public endpoint is usable from other websites subject to the host's normal availability and usage limits. The wrapper streams the models; it does not bundle this dataset into the Python wheel or HTML export.

## Coordinates, heights and quality

Preserve the tileset transforms. They convert the local instanced GLBs into earth-fixed coordinates; loading a GLB alone as an unreferenced model does not place it correctly. Base elevations are fixed to the basemap.de DGM5 terrain used during generation. Use that terrain service for the intended alignment; the preset refuses to load on the flat fallback if terrain initialization fails. Do not add the terrain elevation again or apply per-tree clamping.

Uniform mode is a schematic **15 m** above each model base. Estimated mode uses the source height estimates **4.02–38.33 m**; **29 estimates above 30 m are flagged for review**. Trees are schematic models, not measured crown meshes. Both variants retain source-height metadata so changing their visual height does not change the observations. Automatic detection can miss, merge or split crowns and can confuse buildings or other vegetation with trees.

Feature metadata includes `tree_id`, `model_height_m`, `source_height_m`, `ground_height_m` and `needs_review`. Candidate points, review points, processing frame, OSM masks, input URLs/hashes and original processing/validation summaries are in `data/`. The original validation summary describes source-generation checks; it is not proof of a new browser render in every environment. `manifest.sha256.json` records the unmodified imported source files, and `provenance.json` records this migration.

## Attribution and source rights

**©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL (municipal boundary and building masks).**

Source rasters: RLP DOM1/DGM1 2023 and RGBI orthophotography 2024. Modification: automatic crown candidate extraction, height estimation, masking, schematic tree model generation, DGM5 alignment and spatial/LOD tiling. Preserve attribution and the modification note when redistributing. The wrapper's MIT licence does not replace the source-data terms. See `data/input_manifest.json`, `data/processing_summary.json` and the project [data documentation](https://github.com/yfeng-hsm/GISProjekt26_HS_Mainz/blob/main/docs/DATA.md).
