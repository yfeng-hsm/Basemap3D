"""Public teaching API. Coordinates intentionally follow Folium's convention."""
from copy import deepcopy
from datetime import date as calendar_date
from pathlib import Path
import html
import math

from . import _engine


class Map:
    """Create a 3D scene using location=[latitude, longitude], like Folium.

    zoom_start is an approximate camera-distance preset, not a Leaflet zoom.
    Pass distance_m for an explicit camera distance. Official models stream online.
    """

    def __init__(self, location=(50.0063, 8.2692), zoom_start=16, *,
                 heading=25, pitch=-45, distance_m=None, height=700,
                 title="Mainz 3D", tiles="basemap.de"):
        if tiles != "basemap.de":
            raise ValueError("This teaching wrapper currently provides tiles='basemap.de'.")
        if not isinstance(zoom_start, (int, float)) or not math.isfinite(zoom_start) or not 10 <= zoom_start <= 20:
            raise ValueError("zoom_start must be between 10 and 20.")
        if len(location) != 2:
            raise ValueError("location must be [latitude, longitude].")
        distance = distance_m if distance_m is not None else max(200, min(8000, 900 * 2 ** (16 - zoom_start)))
        self._config = _engine.create_scene(title, (location[1], location[0]), heading, pitch, distance)
        self._config.update(has_raster=False, has_vector=False, query_enabled=False,
                            popup_enabled=False, sun_enabled=False)
        if not isinstance(height, int) or not 200 <= height <= 2000:
            raise ValueError("height must be an integer between 200 and 2000 pixels.")
        self.height = height
        self._html = None

    def add_child(self, layer):
        """Add a layer and return the map for optional chaining."""
        layer.add_to(self)
        return self

    def copy(self):
        """Return an independent snapshot; later layers do not change earlier tasks."""
        return deepcopy(self)

    def _update(self, stage, **options):
        self._config.update(options)
        self._config["task"] = max(stage, self._config["task"])
        self._html = None

    def _render(self):
        if self._html is None:
            self._html = _engine.render(self._config)
        return self._html

    def save(self, outfile):
        """Write standalone HTML relative to the working directory; internet is needed."""
        target = Path(outfile)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._render(), encoding="utf-8")

    def _repr_html_(self):
        """Let Jupyter render the map when the map object is the last cell expression."""
        return ('<iframe title="Mainz 3D" srcdoc="' + html.escape(self._render(), quote=True)
                + f'" width="100%" height="{self.height}" style="border:1px solid #dce4e7;border-radius:12px"></iframe>')


class WmsTileLayer:
    """Add the course's RLP DOP20 WMS raster overlay on top of the basemap."""

    def __init__(self, url="https://geo4.service24.rlp.de/wms/rp_dop20.fcgi",
                 layers="rp_dop20", opacity=0.8):
        if not url.startswith("https://") or not layers:
            raise ValueError("Provide an HTTPS WMS URL and a non-empty layer name.")
        if not 0 <= opacity <= 1:
            raise ValueError("opacity must be between 0 and 1.")
        self.options = dict(raster_url=url, raster_layer=layers, raster_opacity=opacity,
                            basemap="aerial", has_raster=True)

    def add_to(self, m):
        m._update(2, **self.options)
        return self


class GeoJson:
    """Add a local WGS84 polygon file. GeoJSON uses [longitude, latitude]."""

    def __init__(self, data, *, fill_opacity=0.25, popup=False):
        if not 0 <= fill_opacity <= 1:
            raise ValueError("fill_opacity must be between 0 and 1.")
        self.path = str(Path(data).resolve())
        self.opacity = fill_opacity
        self.popup = bool(popup)

    def add_to(self, m):
        m._update(3, vector_file=self.path, has_vector=True, opacity=self.opacity,
                  popup_enabled=self.popup or m._config["popup_enabled"])
        return self


class NearbyBuildings:
    """Select footprints within distance_m of any polygon and enable attribute popups."""

    def __init__(self, data, *, distance_m=75, popup=True, enabled=True):
        if not 0 <= distance_m <= 200:
            raise ValueError("The bundled data supports distance_m between 0 and 200.")
        self.options = dict(buildings_file=str(Path(data).resolve()), query_enabled=True,
                            nearby_distance_m=distance_m, popup_enabled=bool(popup),
                            highlight_nearby=bool(enabled))

    def add_to(self, m):
        if not m._config["has_vector"]:
            raise ValueError("Add a GeoJson polygon layer before NearbyBuildings.")
        m._update(4, **self.options)
        return self


class SunShadows:
    """Add a date and time slider using Europe/Berlin, including daylight saving."""

    def __init__(self, date="2026-10-25", hour=13.0):
        calendar_date.fromisoformat(date)
        if not "1900-01-01" <= date <= "2100-12-31" or not 4 <= hour <= 22:
            raise ValueError("Use a date in 1900–2100 and an hour between 4 and 22.")
        self.options = dict(sun_date=date, sun_hour=hour, sun_enabled=True)

    def add_to(self, m):
        m._update(5, **self.options)
        return self
