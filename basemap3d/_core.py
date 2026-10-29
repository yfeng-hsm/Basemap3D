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

    def __init__(self, location=(51.1657, 10.4515), zoom_start=6, *,
                 heading=25, pitch=-45, distance_m=None, height=700,
                 title="basemap.de · 3D", tiles="basemap.de", buildings=True):
        if tiles != "basemap.de":
            raise ValueError("This teaching wrapper currently provides tiles='basemap.de'.")
        if not isinstance(zoom_start, (int, float)) or not math.isfinite(zoom_start) or not 2 <= zoom_start <= 20:
            raise ValueError("zoom_start must be between 2 and 20.")
        if len(location) != 2:
            raise ValueError("location must be [latitude, longitude].")
        distance = distance_m if distance_m is not None else max(200, min(8000000, 900 * 2 ** (16 - zoom_start)))
        self._config = _engine.create_scene(title, (location[1], location[0]), heading, pitch, distance)
        self._config.update(has_raster=False, has_vector=False, query_enabled=False,
                            popup_enabled=False, sun_enabled=False, bars_enabled=False,
                            buildings_enabled=bool(buildings), nearby_max_distance_m=200)
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

    def show(self):
        """Display inline, using Colab's official kernel-port proxy when available.

        Colab requires a connected runtime. The wrapper manages its small HTML
        server automatically; students do not start a server or choose a port.
        """
        import os
        import sys
        if "google.colab" in sys.modules or "COLAB_RELEASE_TAG" in os.environ:
            from . import _colab
            _colab.show(self._render(), self.height)
        else:
            from IPython.display import display
            display({"text/html": self._repr_html_()}, raw=True)

    def _ipython_display_(self):
        """A final map expression uses the appropriate notebook display backend."""
        self.show()

    def _repr_html_(self):
        """Let Jupyter render the map when the map object is the last cell expression."""
        return ('<iframe title="'+html.escape(self._config['title'],quote=True)+'" srcdoc="' + html.escape(self._render(), quote=True)
                + f'" width="100%" height="{self.height}" style="border:1px solid #dce4e7;border-radius:12px"></iframe>')


class WmsTileLayer:
    """Add an independently controlled WMS raster overlay.

    The default is RLP DOP20 imagery. Custom services supply their own layer
    name, attribution and optional geographic bounds (west, south, east, north).
    Services must support WMS 1.1.1 with EPSG:4326 or EPSG:3857 and browser CORS.
    """

    def __init__(self, url="https://geo4.service24.rlp.de/wms/rp_dop20.fcgi",
                 layers="rp_dop20", opacity=0.8, *, name=None, attribution=None,
                 description=None, styles="", format="image/png", transparent=True,
                 version="1.1.1", crs="EPSG:4326", bounds=None, show=True,
                 legend_url=None):
        from urllib.parse import urlsplit
        parsed = urlsplit(str(url))
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password or not layers:
            raise ValueError("Provide an HTTPS WMS URL without credentials and a non-empty layer name.")
        if not math.isfinite(opacity) or not 0 <= opacity <= 1:
            raise ValueError("opacity must be between 0 and 1.")
        if version != "1.1.1" or crs not in ("EPSG:4326", "EPSG:3857"):
            raise ValueError("Use WMS 1.1.1 with crs='EPSG:4326' or 'EPSG:3857'.")
        if bounds is not None:
            if (len(bounds) != 4 or not all(math.isfinite(v) for v in bounds) or
                not -180 <= bounds[0] < bounds[2] <= 180 or
                not -90 <= bounds[1] < bounds[3] <= 90):
                raise ValueError("bounds must be [west, south, east, north] in geographic degrees.")
        if legend_url and not str(legend_url).startswith("https://"):
            raise ValueError("legend_url must use HTTPS.")
        default = url == "https://geo4.service24.rlp.de/wms/rp_dop20.fcgi" and layers == "rp_dop20"
        self.options = dict(url=str(url), layers=str(layers), opacity=opacity,
                            name=str(name or ("Aerial imagery" if default else layers)),
                            attribution=str(attribution if attribution is not None else
                                ("©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0" if default else "")),
                            description=str(description if description is not None else
                                ("DOP20 aerial imagery · LVermGeo Rheinland-Pfalz." if default else "WMS raster layer")),
                            styles=str(styles), format=str(format), transparent=bool(transparent),
                            version=version, crs=crs, bounds=list(bounds) if bounds else None,
                            show=bool(show), legend_url=legend_url)

    def add_to(self, m):
        layers=deepcopy(m._config.get("raster_layers", []))
        layers.append(deepcopy(self.options))
        m._update(2, raster_layers=layers, has_raster=True,
                  raster_url=self.options["url"], raster_layer=self.options["layers"],
                  raster_opacity=self.options["opacity"], basemap="aerial")
        return self


class GeoJson:
    """Add polygons in WGS84, or transform a GeoJSON-declared CRS to WGS84."""

    def __init__(self, data, *, fill_opacity=0.25, popup=False):
        if not 0 <= fill_opacity <= 1:
            raise ValueError("fill_opacity must be between 0 and 1.")
        self.path = str(Path(data).resolve())
        self.opacity = fill_opacity
        self.popup = bool(popup)

    def add_to(self, m):
        m._update(3, vector_file=self.path, vector_layer_name=("Parking areas · GeoJSON" if Path(self.path).name == "parking.geojson" else Path(self.path).name), has_vector=True, opacity=self.opacity,
                  popup_enabled=self.popup or m._config["popup_enabled"])
        return self


class NearbyBuildings:
    """Select footprints within distance_m of any polygon and enable attribute popups."""

    def __init__(self, data=None, *, distance_m=75, popup=True, enabled=True):
        if not 0 <= distance_m <= 200:
            raise ValueError("distance_m must be between 0 and 200 metres.")
        self.options = dict(buildings_file=str(Path(data).resolve()) if data is not None else None, query_enabled=True,
                            nearby_distance_m=distance_m, popup_enabled=bool(popup),
                            highlight_nearby=bool(enabled))

    def add_to(self, m):
        if not m._config["has_vector"]:
            raise ValueError("Add a GeoJson polygon layer before NearbyBuildings.")
        if not m._config["buildings_enabled"]:
            raise ValueError("Enable Map(buildings=True) to highlight 3D buildings.")
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


class BarLayer:
    """Display a CSV of WGS84 centres as thematic 3D columns, not real buildings.

    Required columns: longitude, latitude, and the selected numeric value field.
    Optional columns: cell_id, name, reference_date. Width and height are encodings.
    """

    def __init__(self, data, *, value="population", height_scale=0.08, bar_width_m=700,
                 opacity=0.9, legend_title="Population per 1 km cell", unit="people",
                 attribution=""):
        if not 0 < height_scale <= 10 or not math.isfinite(height_scale):
            raise ValueError("height_scale must be finite, positive and at most 10 metres per unit.")
        if not 1 <= bar_width_m <= 10000 or not 0 <= opacity <= 1:
            raise ValueError("bar_width_m must be 1–10000; opacity must be 0–1.")
        self.options=dict(bars_file=str(Path(data).resolve()), bars_enabled=True,
                          bar_value=value,bar_height_scale=height_scale,bar_width_m=bar_width_m,
                          bar_opacity=opacity,bar_legend_title=legend_title,bar_unit=unit,
                          bar_attribution=attribution,popup_enabled=True)

    def add_to(self,m):
        m._update(6,**self.options)
        return self


class Tiles3D:
    """Add a hosted standard 3D Tiles tileset without changing its georeference."""

    def __init__(self, url, *, name="3D Tiles", show=True, maximum_screen_space_error=12,
                 attribution="", popup=True, feature_id_label=None, require_terrain=False):
        from urllib.parse import urlsplit
        parsed = urlsplit(str(url))
        if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username or parsed.password:
            raise ValueError("Provide an HTTP(S) tileset URL without embedded credentials.")
        if not math.isfinite(maximum_screen_space_error) or maximum_screen_space_error <= 0:
            raise ValueError("maximum_screen_space_error must be finite and positive.")
        self.options = dict(url=str(url), name=str(name), show=bool(show),
                            maximum_screen_space_error=maximum_screen_space_error,
                            attribution=str(attribution), popup=bool(popup),
                            feature_id_label=feature_id_label, require_terrain=bool(require_terrain))

    def add_to(self, m):
        layers=deepcopy(m._config.get("tiles3d_layers", []))
        layers.append(deepcopy(self.options))
        m._update(1, tiles3d_layers=layers,
                  popup_enabled=m._config["popup_enabled"] or self.options["popup"])
        return self


class TreeLayer(Tiles3D):
    """Mainz estimated-height trees: 7 × 4 km, 28 grid cells.

    Automatically detected candidates, not a verified municipal tree inventory.
    Model bases are fixed to basemap.de DGM5 terrain. Fixed heights are removed.
    """

    BASE_URL="https://yfeng-hsm.github.io/GISProjekt26_HS_Mainz/layers/mainz-trees"
    ATTRIBUTION="©GeoBasis-DE / LVermGeoRP 2026, dl-de/by-2-0 [Daten bearbeitet]; © GeoBasis-DE/BKG 2026; © OpenStreetMap contributors, ODbL"

    def __init__(self, *, show=True, maximum_screen_space_error=12, base_url=None):
        base=(self.BASE_URL if base_url is None else str(base_url)).rstrip("/")
        tileset="tileset-C20261029.json" if base_url is None else "tileset-estimated.json"
        super().__init__(base+"/"+tileset, name="3D trees", show=show,
                         maximum_screen_space_error=maximum_screen_space_error,
                         attribution=self.ATTRIBUTION, popup=True, feature_id_label="tree",
                         require_terrain=True)
        if base_url is None:
            self.options["dataset_label"]="C_balanced centre · 54,014 candidates in total"


class HousePlacement:
    """Enable three yellow buildings and a green grass patch with placement controls."""

    def add_to(self, m):
        m._update(1, house_placement_enabled=True)
        return self
