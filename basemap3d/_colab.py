"""Colab-only HTML hosting through the official output proxy.

Only generated scene documents are served, never the notebook's filesystem.
"""
import atexit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
from urllib.parse import urlsplit
from uuid import uuid4

_pages = {}
_server = None
_lock = threading.RLock()


class _SceneHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond(body=True)

    def do_HEAD(self):
        self._respond(body=False)

    def _respond(self, body):
        with _lock:
            page = _pages.get(urlsplit(self.path).path)
        if page is None:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(page)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        if body:
            self.wfile.write(page)

    def log_message(self, *args):
        pass


def _stop():
    global _server
    with _lock:
        server, _server = _server, None
        _pages.clear()
    if server is not None:
        server.shutdown()
        server.server_close()


def scene_url(page):
    """Register an immutable scene and return its private kernel port and path."""
    global _server
    with _lock:
        if _server is None:
            _server = ThreadingHTTPServer(('127.0.0.1', 0), _SceneHandler)
            threading.Thread(target=_server.serve_forever, daemon=True).start()
        path = '/scene-' + uuid4().hex + '.html'
        _pages[path] = page.encode('utf-8')
        return _server.server_port, path


def show(page, height):
    from google.colab import output
    port, path = scene_url(page)
    output.serve_kernel_port_as_iframe(
        port, path=path, width='100%', height=str(height),
        cache_in_notebook=False,
    )


atexit.register(_stop)
