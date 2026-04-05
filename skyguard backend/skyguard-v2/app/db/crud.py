"""SkyGuard V2 — Async CRUD Operations for all tables."""

import json
from datetime import datetime, timezone
from app.db.database import execute, fetch_one, fetch_all, get_db
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# CAMERAS
# =============================================================================

async def create_camera(cam_id: str, name: str, cam_type: str, source_url: str,
                        zone_id: str, lat: float, lon: float, polygon: list = None) -> None:
    polygon_json = json.dumps(polygon) if polygon else None
    await execute(
        """INSERT OR REPLACE INTO cameras (cam_id, name, type, source_url, zone_id, lat, lon, polygon_geojson)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (cam_id, name, cam_type, source_url, zone_id, lat, lon, polygon_json)
    )

async def get_camera(cam_id: str) -> dict | None:
    return await fetch_one("SELECT * FROM cameras WHERE cam_id = ?", (cam_id,))

async def get_all_cameras() -> list[dict]:
    return await fetch_all("SELECT * FROM cameras ORDER BY cam_id")


# =============================================================================
# ZONES
# =============================================================================

async def create_zone(zone_id: str, name: str, cam_id: str, polygon: list,
                      centroid_lat: float, centroid_lon: float,
                      baseline_mean: float = 5.0, baseline_std: float = 2.0) -> None:
    polygon_json = json.dumps(polygon)
    await execute(
        """INSERT OR REPLACE INTO zones (zone_id, name, cam_id, polygon_geojson,
           centroid_lat, centroid_lon, baseline_mean, baseline_std)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (zone_id, name, cam_id, polygon_json, centroid_lat, centroid_lon, baseline_mean, baseline_std)
    )

async def get_zone(zone_id: str) -> dict | None:
    return await fetch_one("SELECT * FROM zones WHERE zone_id = ?", (zone_id,))

async def get_all_zones() -> list[dict]:
    return await fetch_all("SELECT * FROM zones ORDER BY zone_id")


# =============================================================================
# ZONE BASELINES
# =============================================================================

async def upsert_baseline(zone_id: str, hour: int, day_of_week: int,
                          mean: float, std_dev: float, sample_count: int = 0) -> None:
    await execute(
        """INSERT INTO zone_baselines (zone_id, hour, day_of_week, mean, std_dev, sample_count, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
           ON CONFLICT(zone_id, hour, day_of_week)
           DO UPDATE SET mean = ?, std_dev = ?, sample_count = ?, updated_at = datetime('now')""",
        (zone_id, hour, day_of_week, mean, std_dev, sample_count, mean, std_dev, sample_count)
    )

async def get_baseline(zone_id: str, hour: int, day_of_week: int = None) -> dict | None:
    if day_of_week is not None:
        return await fetch_one(
            "SELECT * FROM zone_baselines WHERE zone_id = ? AND hour = ? AND day_of_week = ?",
            (zone_id, hour, day_of_week)
        )
    # Average across all days for this hour
    return await fetch_one(
        "SELECT AVG(mean) as mean, AVG(std_dev) as std_dev FROM zone_baselines WHERE zone_id = ? AND hour = ?",
        (zone_id, hour)
    )

async def get_zone_baselines(zone_id: str) -> list[dict]:
    return await fetch_all(
        "SELECT * FROM zone_baselines WHERE zone_id = ? ORDER BY day_of_week, hour",
        (zone_id,)
    )


# =============================================================================
# DRONES
# =============================================================================

async def create_drone(drone_id: str, home_lat: float, home_lon: float,
                       battery: int = 100, speed_ms: float = 15.0) -> None:
    await execute(
        """INSERT OR REPLACE INTO drones (drone_id, home_lat, home_lon, current_lat, current_lon,
           battery, speed_ms, status, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'IDLE', datetime('now'))""",
        (drone_id, home_lat, home_lon, home_lat, home_lon, battery, speed_ms)
    )

async def get_drone(drone_id: str) -> dict | None:
    return await fetch_one("SELECT * FROM drones WHERE drone_id = ?", (drone_id,))

async def get_all_drones() -> list[dict]:
    return await fetch_all("SELECT * FROM drones ORDER BY drone_id")

async def update_drone(drone_id: str, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [drone_id]
    await execute(f"UPDATE drones SET {sets}, updated_at = datetime('now') WHERE drone_id = ?", tuple(values))


# =============================================================================
# ALERTS
# =============================================================================

async def create_alert(alert_id: str, zone_id: str, cam_id: str, anomaly_type: str,
                       severity: float, current_count: int = 0, baseline_mean: float = 0.0,
                       z_score: float = 0.0, location_lat: float = None, location_lon: float = None,
                       source: str = "camera", gemini_action: str = None,
                       gemini_confidence: float = None) -> None:
    await execute(
        """INSERT OR REPLACE INTO alerts
           (alert_id, zone_id, cam_id, anomaly_type, severity, current_count, baseline_mean,
            z_score, location_lat, location_lon, source, gemini_action, gemini_confidence, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (alert_id, zone_id, cam_id, anomaly_type, round(severity, 2), current_count,
         round(baseline_mean, 2), round(z_score, 2), location_lat, location_lon,
         source, gemini_action, gemini_confidence)
    )

async def get_alert(alert_id: str) -> dict | None:
    return await fetch_one("SELECT * FROM alerts WHERE alert_id = ?", (alert_id,))

async def get_alerts(status: str = None, zone_id: str = None,
                     limit: int = 50, offset: int = 0) -> list[dict]:
    sql = "SELECT * FROM alerts WHERE 1=1"
    params = []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if zone_id:
        sql += " AND zone_id = ?"
        params.append(zone_id)
    sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    return await fetch_all(sql, tuple(params))

async def update_alert(alert_id: str, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [alert_id]
    await execute(f"UPDATE alerts SET {sets} WHERE alert_id = ?", tuple(values))

async def get_active_alert_for_zone(zone_id: str, seconds_ago: int = 30) -> dict | None:
    """Check for recent active alert in a zone (deduplication)."""
    return await fetch_one(
        """SELECT * FROM alerts WHERE zone_id = ? AND status = 'ACTIVE'
           AND created_at > datetime('now', ? || ' seconds')
           ORDER BY created_at DESC LIMIT 1""",
        (zone_id, f"-{seconds_ago}")
    )


# =============================================================================
# SOS EVENTS
# =============================================================================

async def create_sos(sos_id: str, sender_id: str, message: str, lat: float, lon: float,
                     location_type: str = "gps", zone_id: str = None) -> None:
    await execute(
        """INSERT INTO sos_events (sos_id, sender_id, message, lat, lon, location_type, zone_id, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (sos_id, sender_id, message, lat, lon, location_type, zone_id)
    )

async def get_sos(sos_id: str) -> dict | None:
    return await fetch_one("SELECT * FROM sos_events WHERE sos_id = ?", (sos_id,))

async def get_sos_events(status: str = None, limit: int = 50) -> list[dict]:
    if status:
        return await fetch_all(
            "SELECT * FROM sos_events WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        )
    return await fetch_all("SELECT * FROM sos_events ORDER BY created_at DESC LIMIT ?", (limit,))

async def update_sos(sos_id: str, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [sos_id]
    await execute(f"UPDATE sos_events SET {sets} WHERE sos_id = ?", tuple(values))

async def get_recent_sos_from_sender(sender_id: str, seconds_ago: int = 60) -> dict | None:
    return await fetch_one(
        """SELECT * FROM sos_events WHERE sender_id = ? AND status = 'PENDING'
           AND created_at > datetime('now', ? || ' seconds') LIMIT 1""",
        (sender_id, f"-{seconds_ago}")
    )


# =============================================================================
# MISSIONS
# =============================================================================

async def create_mission(mission_id: str, alert_id: str, drone_id: str, role: str,
                         waypoints: list, nfz_avoided: list, algorithm: str,
                         distance_m: float, eta_s: float) -> None:
    await execute(
        """INSERT INTO missions (mission_id, alert_id, drone_id, role, route_waypoints,
           no_fly_zones_avoided, algorithm, total_distance_m, planned_eta_s, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (mission_id, alert_id, drone_id, role, json.dumps(waypoints),
         json.dumps(nfz_avoided), algorithm, round(distance_m, 1), round(eta_s, 1))
    )

async def update_mission(mission_id: str, **kwargs) -> None:
    if not kwargs:
        return
    sets = ", ".join(f"{k} = ?" for k in kwargs.keys())
    values = list(kwargs.values()) + [mission_id]
    await execute(f"UPDATE missions SET {sets} WHERE mission_id = ?", tuple(values))

async def get_drone_missions(drone_id: str, limit: int = 10) -> list[dict]:
    return await fetch_all(
        "SELECT * FROM missions WHERE drone_id = ? ORDER BY created_at DESC LIMIT ?",
        (drone_id, limit)
    )


# =============================================================================
# HEATMAP EVENTS
# =============================================================================

async def create_heatmap_event(lat: float, lon: float, zone_id: str, anomaly_type: str,
                               severity: float, hour: int, day_of_week: int) -> None:
    await execute(
        """INSERT INTO heatmap_events (lat, lon, zone_id, anomaly_type, severity, hour, day_of_week, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (lat, lon, zone_id, anomaly_type, round(severity, 2), hour, day_of_week)
    )

async def get_heatmap_events(hours: int = 168) -> list[dict]:
    return await fetch_all(
        """SELECT * FROM heatmap_events
           WHERE timestamp > datetime('now', ? || ' hours')
           ORDER BY timestamp DESC""",
        (f"-{hours}",)
    )


# =============================================================================
# REALLOCATION LOG
# =============================================================================

async def log_reallocation(drone_id: str, from_alert_id: str, to_alert_id: str,
                           reason: str, old_eta: float, new_eta: float) -> None:
    await execute(
        """INSERT INTO reallocation_log (drone_id, from_alert_id, to_alert_id, reason, old_eta_s, new_eta_s, timestamp)
           VALUES (?, ?, ?, ?, ?, ?, datetime('now'))""",
        (drone_id, from_alert_id, to_alert_id, reason, round(old_eta, 1), round(new_eta, 1))
    )
