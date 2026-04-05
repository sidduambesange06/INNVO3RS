"""SkyGuard V2 — KDE Heatmap Engine.

Computes Gaussian KDE heatmap from incident events with time-decay weighting.
"""

import math
import time
from datetime import datetime, timezone
from typing import Optional

import numpy as np

from app.db import crud
from app.models.heatmap import HeatmapData, HeatmapPoint, Hotspot
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Pune grid bounds
LAT_MIN, LAT_MAX = 18.45, 18.65
LON_MIN, LON_MAX = 73.75, 73.95
GRID_STEP = 0.002  # ~220m per grid point
KERNEL_BANDWIDTH = 0.005  # ~500m


class HeatmapEngine:
    """KDE-based predictive heatmap engine."""

    def __init__(self):
        self._cache: Optional[HeatmapData] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 30.0  # Recompute every 30s

    async def compute_realtime_heatmap(self) -> HeatmapData:
        """Compute KDE heatmap from last 7 days of events."""
        now = time.time()
        if self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        events = await crud.get_heatmap_events(hours=168)

        if not events:
            empty = HeatmapData(computed_at=datetime.now(timezone.utc).isoformat())
            self._cache = empty
            self._cache_time = now
            return empty

        # Build grid
        lat_points = np.arange(LAT_MIN, LAT_MAX, GRID_STEP)
        lon_points = np.arange(LON_MIN, LON_MAX, GRID_STEP)
        intensity_grid = np.zeros((len(lat_points), len(lon_points)))

        # Weight each event
        now_ts = datetime.now(timezone.utc)
        event_data = []
        for ev in events:
            lat, lon = ev["lat"], ev["lon"]
            severity = ev.get("severity", 0.5)
            # Parse timestamp
            try:
                ts = datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))
                age_hours = (now_ts - ts).total_seconds() / 3600
            except Exception:
                age_hours = 0

            weight = severity * math.exp(-age_hours / 24)  # Half-life 24h
            event_data.append((lat, lon, weight))

        # Gaussian KDE
        for ei_lat, ei_lon, weight in event_data:
            for i, glat in enumerate(lat_points):
                for j, glon in enumerate(lon_points):
                    dist_deg = math.sqrt((glat - ei_lat)**2 + (glon - ei_lon)**2)
                    kernel = math.exp(-0.5 * (dist_deg / KERNEL_BANDWIDTH)**2)
                    intensity_grid[i, j] += weight * kernel

        # Normalize to 0-1
        max_val = intensity_grid.max()
        if max_val > 0:
            intensity_grid /= max_val

        # Extract non-zero points (threshold > 0.01)
        points = []
        for i, glat in enumerate(lat_points):
            for j, glon in enumerate(lon_points):
                val = intensity_grid[i, j]
                if val > 0.01:
                    points.append(HeatmapPoint(
                        lat=round(float(glat), 4),
                        lon=round(float(glon), 4),
                        intensity=round(float(val), 3),
                    ))

        # Extract hotspots (intensity > 0.7)
        hotspots = []
        for p in points:
            if p.intensity > 0.7:
                hotspots.append(Hotspot(
                    zone_id="",  # Will be resolved later
                    lat=p.lat, lon=p.lon,
                    intensity=p.intensity,
                ))

        result = HeatmapData(
            points=points,
            hotspots=hotspots,
            computed_at=datetime.now(timezone.utc).isoformat(),
            total_incidents=len(events),
        )

        self._cache = result
        self._cache_time = now
        return result

    async def get_hotspots(self, threshold: float = 0.7) -> list[Hotspot]:
        heatmap = await self.compute_realtime_heatmap()
        return [h for h in heatmap.hotspots if h.intensity >= threshold]

    async def get_history(self, zone_id: str = None, days: int = 7) -> list[dict]:
        """Get historical incident counts."""
        events = await crud.get_heatmap_events(hours=days * 24)
        if zone_id:
            events = [e for e in events if e.get("zone_id") == zone_id]

        # Group by day
        daily = {}
        for ev in events:
            try:
                ts = ev["timestamp"][:10]
                daily[ts] = daily.get(ts, 0) + 1
            except Exception:
                pass

        return [{"date": k, "count": v} for k, v in sorted(daily.items())]
