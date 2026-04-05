"""SkyGuard V2 — Detection Data Models."""

from pydantic import BaseModel
from typing import Optional


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float

    def to_list(self) -> list:
        return [self.x1, self.y1, self.x2, self.y2]

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def aspect_ratio(self) -> float:
        return self.width / max(self.height, 1)

    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)

    @property
    def area(self) -> float:
        return self.width * self.height


class Detection(BaseModel):
    bbox: BoundingBox
    confidence: float
    class_name: str  # "person", "knife", "gun", etc.
    track_id: Optional[int] = None  # For tracking across frames
    zone: Optional[str] = None

    def to_ws_dict(self) -> dict:
        return {
            "bbox": self.bbox.to_list(),
            "confidence": round(self.confidence, 2),
            "class": self.class_name,
            "track_id": self.track_id,
            "zone": self.zone,
        }


class AnomalyFlag(BaseModel):
    """A detected anomaly with type and confidence."""
    anomaly_type: str
    confidence: float
    description: str = ""
    involved_detections: list[int] = []  # track_ids involved


class DetectionResult(BaseModel):
    """Complete detection result for a single frame."""
    cam_id: str
    zone_id: str
    persons_count: int = 0
    detections: list[Detection] = []
    anomaly_flags: list[AnomalyFlag] = []
    processing_ms: float = 0.0
    timestamp: Optional[str] = None

    def to_ws_dict(self) -> dict:
        return {
            "cam_id": self.cam_id,
            "zone_id": self.zone_id,
            "persons_count": self.persons_count,
            "detections": [d.to_ws_dict() for d in self.detections],
            "anomaly_flags": [{"type": a.anomaly_type, "confidence": round(a.confidence, 2),
                               "description": a.description} for a in self.anomaly_flags],
            "processing_ms": round(self.processing_ms, 1),
        }
