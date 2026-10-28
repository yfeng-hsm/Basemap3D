"""Hosted layer API, imported tile hierarchy and binary/data integrity."""
import hashlib
import json
import struct
from pathlib import Path
from unittest import TestCase
from basemap3d import Map, Tiles3D, TreeLayer

DATA=Path(__file__).resolve().parents[1]/'docs/layers/mainz-trees'


class HostedTilesTest(TestCase):
    def test_layers_accumulate_and_map_copies_are_independent(self):
        first=Map()
        second=first.copy()
        TreeLayer().add_to(second)
        Tiles3D('https://example.org/layer/tileset.json',name='Other').add_to(second)
        self.assertNotIn('tiles3d_layers',first._config)
        self.assertEqual(len(second._config['tiles3d_layers']),2)
        self.assertTrue(second._config['popup_enabled'])
        self.assertIn('setupTiles3D',second._render())
        self.assertIn(TreeLayer.BASE_URL,second._render())
        self.assertNotIn(str(DATA),second._render())

    def test_presets_and_input_validation(self):
        self.assertTrue(TreeLayer(variant='estimated').options['url'].endswith('/tileset-estimated.json'))
        self.assertTrue(TreeLayer().options['require_terrain'])
        self.assertEqual(TreeLayer().options['feature_id_label'],'tree')
        for bad in ('file:///tmp/model.glb','data:text/html,hello','https://secret:password@example.org/tileset.json'):
            with self.assertRaises(ValueError):Tiles3D(bad)
        with self.assertRaises(ValueError):TreeLayer(variant='unknown')
        with self.assertRaises(ValueError):Tiles3D('https://example.org/tileset.json',maximum_screen_space_error=float('nan'))

    def test_imported_files_match_the_source_checksums(self):
        checks=json.loads((DATA/'manifest.sha256.json').read_text())
        for name,sha in checks.items():
            self.assertEqual(hashlib.sha256((DATA/name).read_bytes()).hexdigest(),sha,name)

    def test_both_variants_have_nine_complete_georeferenced_tiles(self):
        for filename,variant in [('tileset.json','uniform'),('tileset-estimated.json','estimated')]:
            tileset=json.loads((DATA/filename).read_text())
            self.assertEqual(tileset['asset']['version'],'1.1')
            self.assertEqual(tileset['asset']['extras']['candidate_tree_count'],13317)
            self.assertEqual(len(tileset['root']['children']),9)
            for tile in tileset['root']['children']:
                self.assertEqual(len(tile['transform']),16)
                self.assertEqual(tile['refine'],'REPLACE')
                for lod in [tile,*tile['children']]:
                    self.assertIn('/'+variant+'/',lod['content']['uri'])
                    raw=(DATA/lod['content']['uri']).read_bytes()
                    magic,version,size=struct.unpack_from('<4sII',raw)
                    self.assertEqual((magic,version,size),(b'glTF',2,len(raw)))
                    length,kind=struct.unpack_from('<II',raw,12)
                    self.assertEqual(kind,0x4E4F534A)
                    gltf=json.loads(raw[20:20+length])
                    self.assertIn('EXT_mesh_gpu_instancing',gltf['extensionsUsed'])
                    self.assertIn('EXT_instance_features',gltf['extensionsUsed'])

    def test_candidates_are_unique_and_review_flags_are_preserved(self):
        features=json.loads((DATA/'data/tree_points.geojson').read_text())['features']
        self.assertEqual(len(features),13317)
        self.assertEqual(len({f['properties']['tree_id'] for f in features}),13317)
        summary=json.loads((DATA/'data/processing_summary.json').read_text())
        self.assertEqual(len(summary['tile_counts']),9)
        self.assertEqual(sum(summary['tile_counts'].values()),13317)
        review=json.loads((DATA/'data/review_points.geojson').read_text())['features']
        self.assertEqual(len(review),29)
