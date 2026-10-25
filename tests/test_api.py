"""Tests for the small public API and the teaching-package contract."""
import html
import json
from pathlib import Path
import re
import tempfile
import unittest

from mainz3d import Map, WmsTileLayer, GeoJson, NearbyBuildings, SunShadows

ROOT=Path(__file__).resolve().parents[1]


class TeachingAPITest(unittest.TestCase):
    def test_folium_coordinate_order(self):
        m=Map(location=[50.0063,8.2692],zoom_start=16)
        self.assertEqual(m._config["center"],[8.2692,50.0063])
        self.assertEqual(m._config["distance_m"],900)

    def test_snapshots_do_not_change_previous_task(self):
        m1=Map()
        m2=m1.copy()
        layer=WmsTileLayer()
        self.assertIs(layer.add_to(m2),layer)
        self.assertFalse(m1._config["has_raster"])
        self.assertTrue(m2._config["has_raster"])
        self.assertEqual(m1._config["task"],1)

    def test_vector_and_sun_do_not_require_raster_or_query(self):
        m=Map()
        GeoJson(ROOT/"data/parking.geojson",popup=True).add_to(m)
        SunShadows(date="2026-06-21",hour=10).add_to(m)
        page=m._render()
        self.assertFalse(m._config["has_raster"])
        self.assertFalse(m._config["query_enabled"])
        self.assertTrue(m._config["popup_enabled"])
        self.assertTrue(m._config["sun_enabled"])
        self.assertIn('"has_raster": false',page)

    def test_export_and_notebook_display_share_document(self):
        m=Map()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"map.html"
            self.assertIsNone(m.save(path))
            srcdoc=re.search('srcdoc="(.*?)" width=',m._repr_html_(),re.S).group(1)
            self.assertEqual(html.unescape(srcdoc),path.read_text())

    def test_query_contract_and_private_path_omission(self):
        with self.assertRaises(ValueError):NearbyBuildings(ROOT/"data/buildings.geojson").add_to(Map())
        m=Map()
        GeoJson(ROOT/"data/parking.geojson").add_to(m)
        NearbyBuildings(ROOT/"data/buildings.geojson",distance_m=75).add_to(m)
        page=m._render()
        self.assertTrue(m._config["query_enabled"])
        self.assertNotIn(str(ROOT),page)
        self.assertNotIn('"buildings_file"',page)
        self.assertIn('"highlight_margin_m": 3',page)

    def test_text_cannot_close_the_data_script(self):
        data=json.loads((ROOT/"data/parking.geojson").read_text())
        data["features"][0]["properties"]["name"]="</script><script>unexpected()</script>"
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"features.geojson"
            path.write_text(json.dumps(data))
            m=Map()
            GeoJson(path).add_to(m)
            self.assertNotIn('</script><script>unexpected()',m._render())
            self.assertIn('\\u003c/script\\u003e',m._render())

    def test_input_limits(self):
        for action in (lambda:Map(zoom_start=30),lambda:WmsTileLayer(opacity=2),
                       lambda:NearbyBuildings("x",distance_m=201),lambda:SunShadows(hour=2)):
            with self.assertRaises(ValueError):action()

    def test_notebook_stays_short_and_language_split_is_clean(self):
        notebook=json.loads((ROOT/"Mainz_3D_5_Tasks.ipynb").read_text())
        cells=[c for c in notebook["cells"] if c["cell_type"]=="code"]
        self.assertEqual(len(cells),6)
        for cell in cells:
            source="".join(cell["source"])
            self.assertLessEqual(len(source.splitlines()),7)
            self.assertNotIn('"coordinates"',source)
            self.assertEqual(cell["outputs"],[])
        self.assertIsNone(re.search(r'[\u4e00-\u9fff]',json.dumps(notebook,ensure_ascii=False)))


if __name__=="__main__":
    unittest.main()
