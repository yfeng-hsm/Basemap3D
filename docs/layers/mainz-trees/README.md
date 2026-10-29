# Mainz trees · estimated heights · 7 × 4 km

54,014 automatically detected candidate trees. Processing frame: **EPSG:25832 [442000, 5537000, 449000, 5541000]**, 7 km east–west and 4 km north–south. Relative to the original 3 × 3 km frame this adds 4 km west and 1 km north. The existing Mainz municipal mask is retained: 25.2651 km² falls inside that boundary. The northeast cell 32_448_5540 contains no Mainz area and is intentionally empty.

## One height model

Only estimated tree height is distributed. The fixed 15 m version has been removed. `tileset.json` and the backward-compatible `tileset-estimated.json` both load the same estimated-height dataset. There are 28 grid cells, 27 with models, and 54 GLBs (coarse/fine LOD pairs). These are levels of detail, not extra trees. The original nine cells have been replaced with C_balanced models. Centre IDs were reassigned during reprocessing and are not stable matches to the previous version.

```python
from basemap3d import Map, TreeLayer
m = Map(location=[50.0063, 8.2692], zoom_start=16)
TreeLayer().add_to(m)
m
```

`TreeLayer(base_url=...)` supports self-hosting. Keep both relative `tiles/estimated/` and `tiles/C20261029/` directories with the tileset. Package exports use the hosted endpoint; the documentation gallery uses its own adjacent dataset.

## Generation and limitations

RLP DOM1 and DGM1 (2023), RGBI orthophotos (2024), OSM Mainz boundary and building footprints. Height is P99 of pixelwise DOM1−DGM1 within each segmented crown.

| Parameter | Centre: C_balanced (9 cells) | Extension: retained earlier result |
|---|---|---|
| Candidates | 26,849 | 27,165 |
| NDVI threshold | >0.25 | ≥0.30 |
| Initial height mask | >2.5 m; >2 m after closing | ≥4 m |
| Accepted height | 3–40 m | ≥4 m |
| Minimum crown area | 8 m² | 16 m² |
| Peak spacing | 2 m | 4 m |
| Gaussian sigma | 0.6 m | 1 m |
| Extra building exclusion buffer | 0 m | 1 m |

C centre crown diameters are scaled independently from tree height using the segmented area-equivalent diameter. The extension models are unchanged. Combined heights range from 3.00 to 39.22 m; 128 estimates above 30 m are flagged for review. The C archive replaces 13,317 old centre candidates; it does not add a second overlapping centre layer.

Automatic candidates, not a municipal inventory or field-verified measurements. Close crowns can merge or split; dates differ between elevation and imagery. Models are schematic. No fixed-height variant is included.

## Terrain and georeference

Model bases use basemap.de DGM5 level 16. Heights are sampled with Cesium-compatible heightmap triangle interpolation; do not add ground elevation again. GLB instances use local ENU tile frames and standard earth-fixed 3D Tiles transforms. All 54 GLBs were checked against candidate IDs, counts, positions and height metadata in this migration. Full Khronos validation was not rerun; the archived C export reports zero errors in its original validation. See `data/validation_summary.json` for coordinate and height checks, and `data/input_manifest.json` for source URLs and hashes.

## Attribution

©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL. Processing: candidate extraction, crown segmentation, estimated heights, terrain alignment and 3D tiling. Original data terms remain applicable alongside the wrapper's MIT licence.

## Reproducing this update

`tools/trees/apply_c_center.py` applies the archived `Mainz_Stadtmitte_C_GitHub_update.zip` to the expanded dataset. `tools/trees/validate_c_upgrade.py` checks both LODs. Archived C extraction/model scripts are under `processing-scripts/`; their original input files and project paths are required to rerun extraction. The extension raster inputs are not included in this migration.

## Deferred candidate GeoJSON

The C_balanced 3D models contain 54,014 candidates. Candidate and review GeoJSON updates are deferred in this release; the existing GeoJSON files retain the earlier extraction and do not match the updated centre models. The viewer reads GLB metadata and does not require the candidate GeoJSON.

The prepared compact export (54,014 candidates, approximately 1.58 MB gzip) has not been added to this repository. Processing helpers support that format, but reproducing the C validation requires the corresponding updated candidates.
