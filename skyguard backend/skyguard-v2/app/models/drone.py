"""SkyGuard V2 — Drone Data Models."""

from pydantic import BaseModel
from typing import Optional
from app.models.enums import DroneStatus


class Waypoint(BaseModel):
    lat: float
    lon: float
    alt: float = 50.0


class DroneState(BaseModel):
    id: str
    position: dict  # {"lat": float, "lon": float, "alt": float}
    home_base: dict  # {"lat": float, "lon": float}
    battery: int
    status: DroneStatus
    target_zone: Optional[str] = None
    target_location: Optional[dict] = None  # {"lat": float, "lon": float}
    current_route: list[Waypoint] = []
    route_index: int = 0  # Current waypoint index in route
    eta_seconds: float = 0.0
    speed_ms: float = 15.0
    distance_remaining_m: float = 0.0
    rtl_time_seconds: float = 0.0
    rtl_distance_m: float = 0.0
    mission_id: Optional[str] = None
    assigned_alert_id: Optional[str] = None
    score: float = 0.0
    can_be_reassigned: bool = True
    hover_timer: float = 0.0  # Seconds remaining in hover

    def to_api_dict(self) -> dict:
        return {
            "drone_id": self.id,
            "position": self.position,
            "home_base": self.home_base,
            "battery": self.battery,
            "status": self.status.value,
            "target_zone": self.target_zone,
            "target_location": self.target_location,
            "eta_seconds": round(self.eta_seconds, 1),
            "speed_ms": self.speed_ms,
            "distance_remaining_m": round(self.distance_remaining_m, 1),
            "rtl_time_seconds": round(self.rtl_time_seconds, 1),
            "rtl_distance_m": round(self.rtl_distance_m, 1),
            "hover_timer": round(self.hover_timer, 1),
            "mission_id": self.mission_id,
            "assigned_alert_id": self.assigned_alert_id,
            "can_be_reassigned": self.can_be_reassigned,
        }

    def to_ws_dict(self) -> dict:
        return self.to_api_dict()
