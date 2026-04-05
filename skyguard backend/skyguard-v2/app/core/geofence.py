"""SkyGuard V2 — Geofence Module.

Loads and enforces 2 no-fly zones (NFZs) over Pune airspace.
NFZ-01: Pune Airport (18.5822, 73.9197) radius 2000m
NFZ-02: Military Cantonment (18.5200, 73.8700) radius 1500m
"""

import json
import os
from typing import Optional
from shapely.geometry import Point, Polygon
from app.utils.geo_utils import make_circle_polygon
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# NFZ definitions
NFZ_DEFINITIONS = [
    {
        "nfz_id": "NFZ-01",
        "name": "Pune Airport",
        "center_lat": 18.5822,
        "center_lon": 73.9197,
        "radius_m": 2000,
    },
    {
        "nfz_id": "NFZ-02",
        "name": "Military Cantonment",
        "center_lat": 18.5200,
        "center_lon": 73.8700,
        "radius_m": 1500,
    },
]


class NoFlyZone:
    """Represents a single no-fly zone with Shapely polygon."""

    def __init__(self, nfz_id: str, name: str, center_lat: float, center_lon: float,
                 radius_m: float, polygon_coords: list):
        self.nfz_id = nfz_id
        self.name = name
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.radius_m = radius_m
        self.polygon_coords = polygon_coords
        # Shapely polygon (lon, lat)
        ring = [(c[1], c[0]) for c in polygon_coords]
        self._shapely_polygon = Polygon(ring)

    def contains(self, lat: float, lon: float) -> bool:
        return self._shapely_polygon.contains(Point(lon, lat))

    def intersects_line(self, lat1: float, lon1: float, lat2: float, lon2: float) -> bool:
        from shapely.geometry import LineString
        line = LineString([(lon1, lat1), (lon2, lat2)])
        return self._shapely_polygon.intersects(line)

    def get_boundary_waypoints(self, num_points: int = 16) -> list[dict]:
        """Get waypoints around the NFZ boundary for rerouting."""
        import math
        waypoints = []
        # Add 10% margin to radius
        margin_radius = self.radius_m * 1.1
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            dlat = margin_radius * math.cos(angle) / 111_320
            dlon = margin_radius * math.sin(angle) / (111_320 * math.cos(math.radians(self.center_lat)))
            waypoints.append({
                "lat": round(self.center_lat + dlat, 6),
                "lon": round(self.center_lon + dlon, 6),
            })
        return waypoints

    def to_dict(self) -> dict:
        return {
            "nfz_id": self.nfz_id,
            "name": self.name,
            "center": {"lat": self.center_lat, "lon": self.center_lon},
            "radius_m": self.radius_m,
            "polygon": self.polygon_coords,
        }


class GeofenceValidator:
    """Manages no-fly zones and validates points/routes against them."""

    def __init__(self):
        self._nfz_list: list[NoFlyZone] = []
        self._loaded = False

    def load_zones(self, geojson_path: str = "data/geofence/pune_nfz.geojson") -> None:
        """Load NFZs from GeoJSON file, or generate from definitions."""
        # Try loading from file
        if os.path.exists(geojson_path):
            try:
                with open(geojson_path, "r") as f:
                    data = json.load(f)
                for feature in data.get("features", []):
                    props = feature.get("properties", {})
                    geom = feature.get("geometry", {})
                    coords = geom.get("coordinates", [[]])[0]
                    polygon = [[c[1], c[0]] for c in coords]  # [lon,lat] -> [lat,lon]
                    nfz = NoFlyZone(
                        nfz_id=props.get("nfz_id", ""),
                        name=props.get("name", ""),
                        center_lat=props.get("center_lat", 0),
                        center_lon=props.get("center_lon", 0),
                        radius_m=props.get("radius_m", 0),
                        polygon_coords=polygon,
                    )
                    self._nfz_list.append(nfz)
                self._loaded = True
                logger.info(f"✅ Loaded {len(self._nfz_list)} no-fly zones from {geojson_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load NFZ file: {e}")

        # Generate from definitions
        self._generate_and_save(geojson_path)

    def _generate_and_save(self, geojson_path: str) -> None:
        """Generate NFZ polygons from definitions and save to GeoJSON."""
        features = []
        for nfz_def in NFZ_DEFINITIONS:
            polygon_coords = make_circle_polygon(
                nfz_def["center_lat"], nfz_def["center_lon"], nfz_def["radius_m"]
            )
            nfz = NoFlyZone(
                nfz_id=nfz_def["nfz_id"],
                name=nfz_def["name"],
                center_lat=nfz_def["center_lat"],
                center_lon=nfz_def["center_lon"],
                radius_m=nfz_def["radius_m"],
                polygon_coords=polygon_coords,
            )
            self._nfz_list.append(nfz)

            # Build GeoJSON feature
            ring = [[c[1], c[0]] for c in polygon_coords]  # [lat,lon] -> [lon,lat]
            features.append({
                "type": "Feature",
                "properties": {
                    "nfz_id": nfz_def["nfz_id"],
                    "name": nfz_def["name"],
                    "center_lat": nfz_def["center_lat"],
                    "center_lon": nfz_def["center_lon"],
                    "radius_m": nfz_def["radius_m"],
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [ring],
                },
            })

        # Save GeoJSON
        os.makedirs(os.path.dirname(geojson_path), exist_ok=True)
        geojson = {"type": "FeatureCollection", "features": features}
        with open(geojson_path, "w") as f:
            json.dump(geojson, f, indent=2)

        self._loaded = True
        logger.info(f"✅ Generated {len(self._nfz_list)} no-fly zones, saved to {geojson_path}")

    def is_point_in_nfz(self, lat: float, lon: float) -> Optional[str]:
        """Check if a point is inside any NFZ. Returns NFZ id or None."""
        for nfz in self._nfz_list:
            if nfz.contains(lat, lon):
                return nfz.nfz_id
        return None

    def does_edge_cross_nfz(self, lat1: float, lon1: float, lat2: float, lon2: float) -> list[str]:
        """Check which NFZs a line segment crosses."""
        crossed = []
        for nfz in self._nfz_list:
            if nfz.intersects_line(lat1, lon1, lat2, lon2):
                crossed.append(nfz.nfz_id)
        return crossed

    def get_active_nfz(self) -> list[dict]:
        """Get all active no-fly zones as dicts."""
        return [nfz.to_dict() for nfz in self._nfz_list]

    def get_nfz_boundary_waypoints(self, nfz_id: str) -> list[dict]:
        """Get boundary waypoints for rerouting around a specific NFZ."""
        for nfz in self._nfz_list:
            if nfz.nfz_id == nfz_id:
                return nfz.get_boundary_waypoints()
        return []

    def get_nfz_objects(self) -> list[NoFlyZone]:
        """Get raw NFZ objects for routing module."""
        return self._nfz_list

    @property
    def is_loaded(self) -> bool:
        return self._loaded
