# Teaching guide

## Intended use

This lab introduces a progressively assembled urban planning viewer to students with basic GIS concepts and introductory Python. Package explanations are English; the concrete Mainz tasks and scene interface are German. Plan approximately two to three 90-minute sessions, with additional time for setup and discussion according to students' experience.

## Learning sequence

| Task | Concept | Student change | Observable evidence |
|---|---|---|---|
| 1 | Basemap versus 3D geometry | Change camera heading, pitch or zoom preset | Roof shapes and perspective change while the same location stays visible |
| 2 | Raster overlay | Change initial or live opacity | Photographic detail blends with the basemap |
| 3 | Vector features and attributes | Change polygon opacity; inspect another site | Five coloured areas, legend and navigation |
| 4 | Spatial selection and popup | Compare 75 m and 150 m; select a parking feature | Non-decreasing match count, gold models, attribute table |
| 5 | Time-dependent visualization | Compare three times and two seasons | Sun direction and ground shadows change |

Each task exports one named HTML file. `.copy()` preserves earlier snapshots, so students can compare results side by side. Students should rerun downstream cells after changing an upstream input. Do not paste coordinates or renderer code into teaching cells; replace files in `data/` or use the small public API.

## Suggested German discussion prompts

1. **Raster oder Vektor?** Welche Informationen sind nur im Luftbild sichtbar, welche stehen als Attribute in den Parkplatzflächen?
2. **Abstand wozu?** Warum wird der Abstand zur Polygonfläche und nicht nur zu ihrem Mittelpunkt gemessen?
3. **Was wird gezählt?** Warum ist die Zahl der OSM-Umrisse keine amtliche Anzahl von Gebäuden?
4. **Warum fehlen Teile?** Welche Abweichungen können entstehen, wenn OSM-Umrisse und LoD2-Modelle kombiniert werden?
5. **Schatten im Foto oder im Modell?** Woran erkennen Sie, welcher Schatten mit dem Zeitregler verändert wird?

## Submission

Ask students to submit the edited notebook, all five HTML files, two credited screenshots, and a short explanation of their changes. One screenshot should show Task 3 and one Task 5. A useful extension is a carefully documented alternative study area, with both parking polygons and suitable nearby-building footprints.

Suggested assessment: data and coordinate handling 25%; correct incremental workflow 25%; spatial-query reasoning 25%; clear visual expression, provenance and limitations 25%. Assess the reasoning as well as the appearance.

## Before class

- Test the five prebuilt examples on a classroom computer and network.
- Check access to the three online service domains listed in the README.
- Install the package in the same environment used by Jupyter.
- Start with the provided data; it avoids making data acquisition a prerequisite.
- Discuss provenance and the difference between a visualization, a scenario model and a live digital twin. The exercise has no real-time parking, traffic or sensor feed.

## Maintenance

Run `python -m unittest discover -s tests -v` and `python tools/build_examples.py` after source or input changes. Review the generated HTML visually before teaching. Keep notebook outputs cleared in Git; generated interactive examples live in `docs/examples/`.
