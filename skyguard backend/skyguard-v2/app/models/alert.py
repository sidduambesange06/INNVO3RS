"""SkyGuard V2 — Alert Data Models."""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.models.enums import AlertStatus, AnomalyType


class Alert(BaseModel):
    alert_id: str
    zone_id: str
    zone_name: str = ""
    cam_id: str = ""
    anomaly_type: str
    severity: float
    current_count: int = 0
    baseline_mean: float = 0.0
    z_score: float = 0.0
    location: dict = {}  # {"lat": float, "lon": float}
    primary_drone: Optional[str] = None
    secondary_drone: Optional[str] = None
    primary_eta: Optional[float] = None
    secondary_eta: Optional[float] = None
    status: AlertStatus = AlertStatus.ACTIVE
    gemini_action: Optional[str] = None
    gemini_confidence: Optional[float] = None
    gemini_reasoning: Optional[str] = None
    source: str = "camera"
    polygon: list = []
    routes: list = []  # List of route dicts for primary/secondary drones
    created_at: Optional[datetime] = None

    def model_post_init(self, __context) -> None:
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)

    def to_ws_dict(self) -> dict:
        return {
            "alert_id": self.alert_id,
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "cam_id": self.cam_id,
            "anomaly_type": self.anomaly_type,
            "severity": round(self.severity, 2),
            "current_count": self.current_count,
            "baseline_mean": round(self.baseline_mean, 2),
            "z_score": round(self.z_score, 2),
            "location": self.location,
            "primary_drone": self.primary_drone,
            "secondary_drone": self.secondary_drone,
            "primary_eta": round(self.primary_eta, 1) if self.primary_eta is not None else None,
            "secondary_eta": round(self.secondary_eta, 1) if self.secondary_eta is not None else None,
            "status": self.status.value,
            "gemini_action": self.gemini_action,
            "gemini_confidence": self.gemini_confidence,
            "gemini_reasoning": self.gemini_reasoning,
            "source": self.source,
            "timestamp": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
