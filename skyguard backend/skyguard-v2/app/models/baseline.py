"""
SkyGuard Backend - Baseline Data Models
Defines anomaly calculation results.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
@dataclass
class BaselineResult:
    """
    Result of Poisson baseline anomaly calculation.
    Contains all metrics needed for alert creation and WebSocket broadcast.
    """
    zone_id: str
    current_count: int
    baseline_mean: float
    baseline_std: float
    z_score: float
    anomaly_score: float
    severity: float  # pre–anomaly-type weight (0..1)
    final_severity: float  # weighted and capped for alerts / UI
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_ws_dict(self) -> dict:
        """Serialize for WebSocket baseline_update event."""
        return {
            "zone_id": self.zone_id,
            "current": self.current_count,
            "mean": round(self.baseline_mean, 2),
            "std_dev": round(self.baseline_std, 2),
            "anomaly_score": round(self.anomaly_score, 2),
            "severity": round(self.final_severity, 2),
        }
