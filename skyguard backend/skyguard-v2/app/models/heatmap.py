"""SkyGuard V2 — Heatmap Data Models."""
from pydantic import BaseModel
from typing import Optional
class HeatmapPoint(BaseModel):
    lat: float
    lon: float
    intensity: float
class Hotspot(BaseModel):
    zone_id: str
    zone_name: str = ""
    lat: float
    lon: float
    intensity: float
    incident_count: int = 0
class RiskPrediction(BaseModel):
    zone_id: str
    zone_name: str = ""
    risk_score: float
    reasoning: str = ""
    recommended_action: str = ""
class HeatmapData(BaseModel):
    points: list[HeatmapPoint] = []
    hotspots: list[Hotspot] = []
    predictions: list[RiskPrediction] = []
    computed_at: Optional[str] = None
    total_incidents: int = 0
    def to_dict(self) -> dict:
        return {
            "points": [{"lat": p.lat, "lon": p.lon, "intensity": round(p.intensity, 3)} for p in self.points],
            "hotspots": [{"zone_id": h.zone_id, "zone_name": h.zone_name, "lat": h.lat, "lon": h.lon,
                          "intensity": round(h.intensity, 3), "incident_count": h.incident_count} for h in self.hotspots],
            "predictions": [{"zone_id": r.zone_id, "risk_score": round(r.risk_score, 2),
                             "reasoning": r.reasoning, "recommended_action": r.recommended_action} for r in self.predictions],
            "computed_at": self.computed_at,
            "total_incidents": self.total_incidents,
        }
