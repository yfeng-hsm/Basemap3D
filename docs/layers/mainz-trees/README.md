# Mainz trees · estimated heights · 7 × 4 km

40,482 automatically detected candidate trees. Processing frame: **EPSG:25832 [442000, 5537000, 449000, 5541000]**, 7 km east–west and 4 km north–south. Relative to the original 3 × 3 km frame this adds 4 km west and 1 km north. The existing Mainz municipal mask is retained: 25.2651 km² falls inside that boundary. The northeast cell 32_448_5540 contains no Mainz area and is intentionally empty.

## One height model

Only estimated tree height is distributed. The fixed 15 m version has been removed. `tileset.json` and the backward-compatible `tileset-estimated.json` both load the same estimated-height dataset. There are 28 grid cells, 27 with models, and 54 GLBs (coarse/fine LOD pairs). These are levels of detail, not extra trees. IDs and models in the original nine cells remain unchanged.

```python
from basemap3d import Map, TreeLayer
m = Map(location=[50.0063, 8.2692], zoom_start=16)
TreeLayer().add_to(m)
m
```

`TreeLayer(base_url=...)` supports self-hosting. Keep the relative `tiles/estimated/` directory with the tileset. Package exports use the hosted endpoint; the documentation gallery uses its own adjacent dataset.

## Generation and limitations

RLP DOM1 and DGM1 (2023), RGBI orthophotos (2024), OSM Mainz boundary and building footprints. NDVI ≥0.3, CHM ≥4 m, crown area ≥16 m², 4 m peak spacing, approximately 1 m building exclusion buffer. The added area uses CHM-seeded watershed at 1 m. Height is P99 of pixelwise DOM1−DGM1 within each crown. The original 13,317 candidates are retained; 27,165 are added. Heights range from 4.02 to 38.33 m; 109 estimates above 30 m are flagged for review.

Automatic candidates, not a municipal inventory or field-verified measurements. Close crowns can merge or split; dates differ between elevation and imagery. Models are schematic. No fixed-height variant is included.

## Terrain and georeference

Model bases use basemap.de DGM5 level 16. Heights are sampled with Cesium-compatible heightmap triangle interpolation; do not add ground elevation again. GLB instances use local ENU tile frames and standard earth-fixed 3D Tiles transforms. The 54 GLBs pass Khronos validation with no errors or warnings. See `data/validation_summary.json` for coordinate and height checks, and `data/input_manifest.json` for source URLs and hashes.

## Attribution

©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL. Processing: candidate extraction, crown segmentation, estimated heights, terrain alignment and 3D tiling. Original data terms remain applicable alongside the wrapper's MIT licence.
