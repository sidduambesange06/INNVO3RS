"""SkyGuard V2 — Enums for the entire system."""

from enum import Enum


class DroneStatus(str, Enum):
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    REROUTING = "REROUTING"
    HOVERING = "HOVERING"
    RETURNING = "RETURNING"


class AnomalyType(str, Enum):
    CROWD_ANOMALY = "crowd_anomaly"
    FIGHT_DETECTION = "fight_detection"
    PERSON_DOWN = "person_down"
    WEAPON_DETECT = "weapon_detect"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"


class AlertStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"
    PARTIAL_RESPONSE = "PARTIAL_RESPONSE"
    ROUTE_BLOCKED = "ROUTE_BLOCKED"


class SOSStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    DISPATCHED = "DISPATCHED"


class GeminiAction(str, Enum):
    DISPATCH = "DISPATCH"
    MONITOR = "MONITOR"
    DISMISS = "DISMISS"
