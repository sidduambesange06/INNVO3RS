"""SkyGuard V2 — Database Seed Data.

Seeds 8 cameras, 8 zones, 4 drones, and baseline data for all zones×24 hours×7 days.
"""

import json
import math
import random
from app.db import crud
from app.utils.geo_utils import make_square_polygon
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# =============================================================================
# SEED DATA DEFINITIONS
# =============================================================================

CAMERAS = [
    {"cam_id": "CAM-01", "name": "MG Road",          "type": "rtsp",       "zone_id": "Zone-A", "lat": 18.5204, "lon": 73.8567},
    {"cam_id": "CAM-02", "name": "Shivajinagar",     "type": "video_feed", "zone_id": "Zone-B", "lat": 18.5308, "lon": 73.8474},
    {"cam_id": "CAM-03", "name": "FC Road",           "type": "video_feed", "zone_id": "Zone-C", "lat": 18.5286, "lon": 73.8395},
    {"cam_id": "CAM-04", "name": "Koregaon Park",     "type": "video_feed", "zone_id": "Zone-D", "lat": 18.5362, "lon": 73.8939},
    {"cam_id": "CAM-05", "name": "Hinjewadi",         "type": "video_feed", "zone_id": "Zone-E", "lat": 18.5913, "lon": 73.7390},
    {"cam_id": "CAM-06", "name": "Kothrud",           "type": "video_feed", "zone_id": "Zone-F", "lat": 18.5074, "lon": 73.8077},
    {"cam_id": "CAM-07", "name": "Hadapsar",          "type": "video_feed", "zone_id": "Zone-G", "lat": 18.4956, "lon": 73.9259},
    {"cam_id": "CAM-08", "name": "Wakad",             "type": "video_feed", "zone_id": "Zone-H", "lat": 18.5989, "lon": 73.7601},
]

DRONES = [
    {"drone_id": "DR-01", "home_lat": 18.5204, "home_lon": 73.8567},  # Zone-A
    {"drone_id": "DR-02", "home_lat": 18.5308, "home_lon": 73.8474},  # Zone-B
    {"drone_id": "DR-03", "home_lat": 18.5362, "home_lon": 73.8939},  # Zone-D
    {"drone_id": "DR-04", "home_lat": 18.5913, "home_lon": 73.7390},  # Zone-E
]


def _get_baseline_mean(hour: int) -> tuple[float, float]:
    """Get realistic mean and std for a given hour."""
    if 0 <= hour <= 5:
        mean = random.uniform(2.0, 3.0)
        std = 1.5
    elif 6 <= hour <= 6:
        mean = random.uniform(5.0, 8.0)
        std = 2.0
    elif 7 <= hour <= 10:
        mean = random.uniform(12.0, 18.0)
        std = random.uniform(3.0, 5.0)
    elif 11 <= hour <= 16:
        mean = random.uniform(7.0, 10.0)
        std = random.uniform(2.0, 3.0)
    elif 17 <= hour <= 21:
        mean = random.uniform(15.0, 25.0)
        std = random.uniform(4.0, 6.0)
    else:  # 22-23
        mean = random.uniform(3.0, 5.0)
        std = 2.0
    return (round(mean, 1), round(std, 1))


async def seed_all() -> None:
    """Seed all initial data into the database."""
    logger.info("Seeding database...")

    # Seed cameras + zones
    for cam in CAMERAS:
        polygon = make_square_polygon(cam["lat"], cam["lon"], side_meters=200)
        source_url = ""
        if cam["type"] == "rtsp":
            from app.config import settings
            source_url = settings.rtsp_url
        else:
            source_url = f"data/feeds/{cam['cam_id'].lower()}_feed.mp4"

        await crud.create_camera(
            cam_id=cam["cam_id"],
            name=cam["name"],
            cam_type=cam["type"],
            source_url=source_url,
            zone_id=cam["zone_id"],
            lat=cam["lat"],
            lon=cam["lon"],
            polygon=polygon,
        )

        await crud.create_zone(
            zone_id=cam["zone_id"],
            name=cam["name"],
            cam_id=cam["cam_id"],
            polygon=polygon,
            centroid_lat=cam["lat"],
            centroid_lon=cam["lon"],
        )

    # Seed drones
    for drone in DRONES:
        await crud.create_drone(
            drone_id=drone["drone_id"],
            home_lat=drone["home_lat"],
            home_lon=drone["home_lon"],
            battery=100,
            speed_ms=15.0,
        )

    # Seed baselines: 8 zones × 24 hours × 7 days = 1344 records
    zone_ids = [cam["zone_id"] for cam in CAMERAS]
    for zone_id in zone_ids:
        for day in range(7):
            for hour in range(24):
                mean, std = _get_baseline_mean(hour)
                # Add slight zone variation
                zone_factor = 1.0 + (hash(zone_id) % 5) * 0.1
                mean = round(mean * zone_factor, 1)
                await crud.upsert_baseline(
                    zone_id=zone_id,
                    hour=hour,
                    day_of_week=day,
                    mean=mean,
                    std_dev=std,
                )

    logger.info(f"✅ Seeded: {len(CAMERAS)} cameras, {len(CAMERAS)} zones, "
                f"{len(DRONES)} drones, {len(zone_ids) * 24 * 7} baseline records")
