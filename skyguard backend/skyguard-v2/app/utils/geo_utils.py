"""SkyGuard V2 — Geospatial utilities using Shapely."""

from typing import Optional
from shapely.geometry import Point, Polygon, LineString


def point_in_polygon(lat: float, lon: float, polygon_coords: list) -> bool:
    """
    Check if a point is inside a polygon.

    Args:
        lat, lon: Point coordinates
        polygon_coords: List of [lat, lon] pairs defining the polygon

    Returns:
        True if point is inside the polygon
    """
    if not polygon_coords or len(polygon_coords) < 3:
        return False
    # Shapely uses (x, y) = (lon, lat)
    point = Point(lon, lat)
    ring = [(c[1], c[0]) for c in polygon_coords]  # [lat,lon] -> (lon,lat)
    poly = Polygon(ring)
    return poly.contains(point)


def polygon_centroid(polygon_coords: list) -> tuple[float, float]:
    """Return (lat, lon) centroid of a polygon."""
    if not polygon_coords or len(polygon_coords) < 3:
        return (0.0, 0.0)
    ring = [(c[1], c[0]) for c in polygon_coords]
    poly = Polygon(ring)
    c = poly.centroid
    return (c.y, c.x)  # (lat, lon)


def polygons_overlap(p1_coords: list, p2_coords: list) -> bool:
    """Check if two polygons overlap."""
    ring1 = [(c[1], c[0]) for c in p1_coords]
    ring2 = [(c[1], c[0]) for c in p2_coords]
    poly1 = Polygon(ring1)
    poly2 = Polygon(ring2)
    return poly1.intersects(poly2)


def edge_intersects_polygon(
    lat1: float, lon1: float, lat2: float, lon2: float, polygon_coords: list
) -> bool:
    """Check if a line segment intersects a polygon."""
    if not polygon_coords or len(polygon_coords) < 3:
        return False
    line = LineString([(lon1, lat1), (lon2, lat2)])
    ring = [(c[1], c[0]) for c in polygon_coords]
    poly = Polygon(ring)
    return line.intersects(poly)


def make_square_polygon(center_lat: float, center_lon: float, side_meters: float = 200) -> list:
    """
    Create a square polygon around a center point.

    Args:
        center_lat, center_lon: Center point
        side_meters: Side length in meters

    Returns:
        List of [lat, lon] pairs defining the square
    """
    # Approximate degrees per meter at this latitude
    import math
    lat_deg = side_meters / 2 / 111_320
    lon_deg = side_meters / 2 / (111_320 * math.cos(math.radians(center_lat)))

    return [
        [center_lat - lat_deg, center_lon - lon_deg],
        [center_lat - lat_deg, center_lon + lon_deg],
        [center_lat + lat_deg, center_lon + lon_deg],
        [center_lat + lat_deg, center_lon - lon_deg],
        [center_lat - lat_deg, center_lon - lon_deg],  # close ring
    ]


def make_circle_polygon(center_lat: float, center_lon: float, radius_meters: float, segments: int = 32) -> list:
    """Create a circular polygon approximation."""
    import math
    coords = []
    for i in range(segments + 1):
        angle = 2 * math.pi * i / segments
        dlat = radius_meters * math.cos(angle) / 111_320
        dlon = radius_meters * math.sin(angle) / (111_320 * math.cos(math.radians(center_lat)))
        coords.append([center_lat + dlat, center_lon + dlon])
    return coords
