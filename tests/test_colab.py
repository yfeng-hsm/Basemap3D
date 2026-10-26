"""Colab display routing and the restricted scene server, without a Google login."""
import os
import sys
from pathlib import Path
from types import ModuleType
from unittest import TestCase
from unittest.mock import Mock, patch
from urllib.error import HTTPError
from urllib.request import urlopen

from basemap3d import Map
from basemap3d import _colab


class ColabDisplayTest(TestCase):
    def tearDown(self):
        _colab._stop()

    def test_server_serves_only_registered_immutable_scenes(self):
        port, path = _colab.scene_url('<!doctype html><p>First · Karte</p>')
        same_port, second = _colab.scene_url('<!doctype html><p>Second</p>')
        self.assertEqual(port, same_port)
        self.assertNotEqual(path, second)
        with urlopen(f'http://127.0.0.1:{port}{path}') as response:
            self.assertEqual(response.read().decode(), '<!doctype html><p>First · Karte</p>')
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
        for route in ('/', '/README.md', '/../../etc/passwd'):
            with self.assertRaises(HTTPError) as failure:
                urlopen(f'http://127.0.0.1:{port}{route}')
            self.assertEqual(failure.exception.code, 404)

    def test_official_colab_proxy_receives_a_complete_scene(self):
        google = ModuleType('google')
        colab = ModuleType('google.colab')
        colab.output = Mock()
        google.colab = colab
        m = Map(buildings=False)
        with patch.dict(sys.modules, {'google': google, 'google.colab': colab}):
            m._ipython_display_()
        call = colab.output.serve_kernel_port_as_iframe.call_args
        self.assertEqual(call.kwargs['height'], str(m.height))
        self.assertFalse(call.kwargs['cache_in_notebook'])
        with urlopen(f'http://127.0.0.1:{call.args[0]}{call.kwargs["path"]}') as response:
            self.assertEqual(response.read().decode(), m._render())

    def test_local_jupyter_keeps_srcdoc_without_starting_a_server(self):
        with patch.dict(os.environ, {}, clear=True):
            modules = {key: value for key, value in sys.modules.items() if key != 'google.colab'}
            with patch.dict(sys.modules, modules, clear=True):
                with patch('IPython.display.display') as display:
                    Map().show()
        self.assertIn('srcdoc=', display.call_args.args[0]['text/html'])
        self.assertIsNone(_colab._server)

    def test_ipython_final_expression_invokes_the_display_backend(self):
        from IPython.core.interactiveshell import InteractiveShell
        m = Map()
        with patch.object(m, 'show') as show:
            bundle, metadata = InteractiveShell.instance().display_formatter.format(m)
        show.assert_called_once_with()
        self.assertEqual(bundle, {})
