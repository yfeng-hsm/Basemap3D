"""WMS configuration and layer independence, without calling remote services."""
from unittest import TestCase
from basemap3d import Map,WmsTileLayer


class WmsLayersTest(TestCase):
    def test_custom_layers_accumulate_and_keep_independent_settings(self):
        first=Map()
        scene=first.copy()
        WmsTileLayer(opacity=.4).add_to(scene)
        bounds=[-10,35,30,65]
        WmsTileLayer('https://example.org/wms',layers='impervious',name='Sealing',
                     attribution='Example credit',opacity=.8,show=False,
                     bounds=bounds,crs='EPSG:3857').add_to(scene)
        self.assertNotIn('raster_layers',first._config)
        layers=scene._config['raster_layers']
        self.assertEqual(len(layers),2)
        self.assertEqual([x['opacity'] for x in layers],[.4,.8])
        self.assertFalse(layers[1]['show'])
        self.assertEqual(layers[1]['name'],'Sealing')
        self.assertNotIn('LVermGeo',layers[1]['attribution'])
        self.assertIsNone(layers[0]['bounds'])
        bounds[0]=-50
        self.assertEqual(layers[1]['bounds'][0],-10)
        self.assertIn('setupWmsLayers',scene._render())
        self.assertNotIn('Rectangle.fromDegrees(6.03,48.89,8.62,51.01)',scene._render())

    def test_wms_protocol_inputs_are_checked(self):
        for options in ({'opacity':float('nan')},{'bounds':[30,50,10,60]},
                        {'crs':'EPSG:3035'},{'version':'1.3.0'},
                        {'legend_url':'javascript:alert(1)'}):
            with self.assertRaises(ValueError):WmsTileLayer(**options)
