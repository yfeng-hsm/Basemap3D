# Estimated-height tree expansion

The processing frame is EPSG:25832 [442000, 5537000, 449000, 5541000]. Scripts preserve original candidate IDs beginning `mainz_center_` and add only the 19 extension cells. The Mainz municipality mask is retained; 32_448_5540 is empty and needs no orthophoto. Only estimated-height GLBs are produced.

From the repository root, install requirements into an isolated environment and run these scripts in order: `download_inputs.py`, `get_buildings.py`, `process_new.py`, `align_terrain.py`, `build_tiles.py`, `validate_geography.py`. `BASEMAP3D_TREE_WORK` optionally selects a cache directory (default `work/tree_expansion`). Inputs are cached; remove the relevant cached outputs to intentionally recompute a step. Large imagery inputs total around 1.3 GB for this expansion.

Segmentation uses NDVI ≥0.3, CHM ≥4 m, area ≥16 m², 4 m peak spacing, 1 m building exclusion, and CHM Gaussian sigma 1 m. Tree height is P99(DOM1−DGM1). Ground height uses DGM5 level 16, with Cesium-compatible heightmap triangle interpolation. Crown and trunk mesh geometry is reused from the original instanced model templates; coarse/fine LODs retain metadata and feature selection. Models and candidates are unverified estimates.

Review the outputs in `work/tree_expansion/staging` before replacing the hosted dataset. Regenerate its checksum manifest after updating validation/provenance files. `tools/build_docs.py` creates gallery scenes referencing their adjacent tree tiles, while Python notebook exports keep the public estimated-height endpoint. Publication is a separate operation.

## C centre update, 2026-10-29
The hosted centre has been replaced by C_balanced (26,849 candidates); the 27,165 extension candidates retain the stricter settings above. Do not describe the entire expanded layer as C. Use apply_c_center.py with the archived C update ZIP, then validate_c_upgrade.py and regenerate manifest.sha256.json. Full extension reprocessing requires reacquiring the raw inputs.

`point_io.py` supports legacy GeoJSON and compact gzip exports. The compact C candidate export is not included in this release; existing published GeoJSON remains from the earlier extraction. Supply matching updated candidates before running C validation or rebuilding C models. Browser popups use GLB metadata independently.
