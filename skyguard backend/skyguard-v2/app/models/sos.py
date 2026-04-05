"""SkyGuard V2 — SOS Event Data Models."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from app.models.enums import SOSStatus
from pydantic import BaseModel, ConfigDict
class SOSCreate(BaseModel):
    model_config = ConfigDict(extra='allow')
    sender_id: str = "unknown"
    message: str = "Emergency SOS Request"
    lat: float = 18.52
    lon: float = 73.85
    location_type: str = "gps"  # gps | zone | manual
    zone_id: Optional[str] = None
class SOSEvent(BaseModel):
    sos_id: str
    sender_id: str
    message: str = ""
    location: dict = {}  # {"lat": float, "lon": float}
    location_type: str = "gps"
    zone_id: Optional[str] = None
    status: SOSStatus = SOSStatus.PENDING
    buffer_seconds: int = 30
    seconds_remaining: int = 30
    alert_id: Optional[str] = None
    created_at: Optional[datetime] = None
    def to_ws_dict(self) -> dict:
        return {
            "sos_id": self.sos_id,
            "sender_id": self.sender_id,
            "message": self.message,
            "location": self.location,
            "location_type": self.location_type,
            "zone_id": self.zone_id,
            "status": self.status.value,
            "buffer_seconds": self.buffer_seconds,
            "seconds_remaining": self.seconds_remaining,
            "alert_id": self.alert_id,
            "timestamp": self.created_at.isoformat() + "Z" if self.created_at else None,
        }
class SOSResponse(BaseModel):
    sos_id: str
    status: str
    confirmation_deadline: str
    buffer_seconds: int
    message: str