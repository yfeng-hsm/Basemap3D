"""Coordinate normalization must happen before rendering and distance queries."""
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from basemap3d._engine import _geojson


class GeoJsonCRSTest(TestCase):
    def read(self, data):
        with TemporaryDirectory() as folder:
            path = Path(folder) / 'input.geojson'
            path.write_text(json.dumps(data))
            return _geojson(path)

    def fixture(self, coordinates):
        return {'type': 'FeatureCollection', 'features': [
            {'type': 'Feature', 'properties': {'Name': 'Custom area'},
             'geometry': {'type': 'Polygon', 'coordinates': [coordinates]}}]}

    def test_mercator_urn_becomes_longitude_latitude_and_preserves_name(self):
        ring = [[8.26,50.0],[8.27,50.0],[8.27,50.01],[8.26,50.0]]
        projected = [[6378137 * math.radians(x),
                      6378137 * math.log(math.tan(math.pi/4 + math.radians(y)/2))]
                     for x,y in ring]
        data = self.fixture(projected)
        data['crs'] = {'type':'name', 'properties':{'name':'urn:ogc:def:crs:EPSG::3857'}}
        result = self.read(data)
        actual = result['features'][0]['geometry']['coordinates'][0]
        for expected,point in zip(ring,actual):
            self.assertAlmostEqual(expected[0],point[0],places=7)
            self.assertAlmostEqual(expected[1],point[1],places=7)
        self.assertEqual(result['features'][0]['properties']['name'],'Custom area')
        self.assertNotIn('crs',result)

    def test_undeclared_coordinates_are_wgs84_and_unknown_crs_is_rejected(self):
        ring = [[8,50],[8.01,50],[8,50.01],[8,50]]
        self.assertEqual(self.read(self.fixture(ring))['features'][0]['geometry']['coordinates'][0],ring)
        data = self.fixture(ring)
        data['crs']={'type':'name','properties':{'name':'EPSG:999999999'}}
        with self.assertRaisesRegex(ValueError,'transform'):
            self.read(data)
