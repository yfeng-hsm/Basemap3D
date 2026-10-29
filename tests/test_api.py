"""Tests for the small public API and the teaching-package contract."""
import html
import json
from pathlib import Path
import re
import tempfile
import unittest

from basemap3d import Map, WmsTileLayer, GeoJson, NearbyBuildings, SunShadows, BarLayer
from unittest.mock import patch

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
        with self.assertRaises(ValueError):NearbyBuildings().add_to(Map())
        m=Map()
        GeoJson(ROOT/"data/parking.geojson").add_to(m)
        NearbyBuildings(ROOT/"data/mainz_buildings_snapshot.geojson",distance_m=75).add_to(m)
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
        notebook=json.loads((ROOT/"notebooks/Mainz_3D_5_Tasks.ipynb").read_text())
        cells=[c for c in notebook["cells"] if c["cell_type"]=="code"]
        self.assertEqual(len(cells),7)
        for cell in cells:
            source="".join(cell["source"])
            self.assertLessEqual(len(source.splitlines()),10 if 'colab-setup' in cell['metadata'].get('tags',[]) else 7)
            self.assertNotIn('"coordinates"',source)
            self.assertEqual(cell["outputs"],[])
        self.assertIsNone(re.search(r'[\u4e00-\u9fff]',json.dumps(notebook,ensure_ascii=False)))

    def test_country_defaults_are_not_mainz(self):
        m=Map()
        self.assertEqual(m._config['center'],[10.4515,51.1657])
        self.assertEqual(m._config['title'],'basemap.de · 3D')

    def test_automatic_query_uses_the_supplied_polygons(self):
        m=Map()
        GeoJson(ROOT/'data/parking.geojson').add_to(m)
        NearbyBuildings().add_to(m)
        empty={'type':'FeatureCollection','features':[]}
        with patch('basemap3d._osm.fetch_around',return_value=empty) as fetch:
            m._render()
        self.assertEqual(len(fetch.call_args.args[0]['features']),5)
        self.assertEqual(fetch.call_args.args[1],200)
        self.assertIsNone(m._config['buildings_file'])

    def test_request_boxes_follow_a_different_city(self):
        from basemap3d._osm import request_boxes
        berlin={'type':'FeatureCollection','features':[{'type':'Feature','properties':{},'geometry':{'type':'Polygon','coordinates':[[[13.40,52.51],[13.401,52.51],[13.401,52.511],[13.40,52.511],[13.40,52.51]]]}}]}
        boxes=request_boxes(berlin)
        self.assertTrue(all(13<west<east<14 and 52<south<north<53 for west,south,east,north in boxes))

    def test_population_is_real_prepared_data_and_source_paths_are_removed(self):
        m=Map(location=[52.51,13.39],buildings=False,distance_m=42000)
        BarLayer(ROOT/'data/berlin_population_1km.csv').add_to(m)
        page=m._render()
        self.assertIn('"bars_enabled": true',page)
        self.assertIn('"buildings_enabled": false',page)
        self.assertIn('CRS3035RES1000m',page)
        self.assertNotIn(str(ROOT),page)
        metadata=json.loads((ROOT/'data/berlin_population_1km.metadata.json').read_text())
        self.assertEqual(metadata['cell_count'],657)
        self.assertEqual(metadata['reference_date'],'2022-05-15')

    def test_bar_values_reject_nonfinite_or_negative_inputs(self):
        for value in ('NaN','-1'):
            with tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'bad.csv'
                path.write_text('longitude,latitude,population\n13.4,52.5,'+value+'\n')
                m=Map()
                BarLayer(path).add_to(m)
                with self.assertRaises(ValueError):m._render()


    def test_osm_relations_preserve_courtyard_holes(self):
        from basemap3d._osm import from_elements
        coords=[(13.4,52.5),(13.402,52.5),(13.402,52.502),(13.4,52.502),
                (13.4005,52.5005),(13.4015,52.5005),(13.4015,52.5015),(13.4005,52.5015)]
        elements=[dict(type='node',id=i+1,lon=x,lat=y) for i,(x,y) in enumerate(coords)]
        elements += [dict(type='way',id=10,nodes=[1,2,3,4,1],tags={'building':'yes'}),
                     dict(type='way',id=11,nodes=[5,6,7,8,5]),
                     dict(type='relation',id=20,tags={'type':'multipolygon','building':'yes'},
                          members=[{'type':'way','ref':10,'role':'outer'},{'type':'way','ref':11,'role':'inner'}])]
        features=from_elements(elements)['features']
        self.assertEqual(len(features),1)
        self.assertEqual(len(features[0]['geometry']['coordinates'][0]),2)
        self.assertIn('highlight_geometry',features[0])

    def test_osm_network_failure_does_not_use_a_fixed_snapshot(self):
        from basemap3d._osm import _download
        with tempfile.TemporaryDirectory() as folder:
            with patch('basemap3d._osm.urlopen',side_effect=OSError('offline')):
                with self.assertRaisesRegex(RuntimeError,'No fixed-city fallback'):
                    _download((13.4,52.5,13.401,52.501),Path(folder))


if __name__=="__main__":
    unittest.main()
