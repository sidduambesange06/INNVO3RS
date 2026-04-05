"""SkyGuard V2 — Alert API Routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db import crud
router = APIRouter(prefix="/alerts", tags=["alerts"])
from pydantic import BaseModel, ConfigDict
class ManualAlertRequest(BaseModel):
    model_config = ConfigDict(extra='allow')
    zone_id: Optional[str] = "Zone-A"
    anomaly_type: str = "crowd_anomaly"
    severity: float = 0.85
@router.get("")
async def list_alerts(status: Optional[str] = None, zone_id: Optional[str] = None,
                      limit: int = 50, offset: int = 0):
    """List alerts with optional filtering."""
    alerts = await crud.get_alerts(status=status, zone_id=zone_id, limit=limit, offset=offset)
    return {"alerts": alerts, "count": len(alerts)}
@router.post("/manual")
@router.post("/manual_alert")
async def create_manual_alert(req: ManualAlertRequest):
    """Create a manual alert and trigger dispatch."""
    from app.services.background_tasks import alert_manager
    if not alert_manager:
        raise HTTPException(500, "Alert manager not initialized")
    alert = await alert_manager.create_manual_alert(
        zone_id=req.zone_id,
        anomaly_type=req.anomaly_type,
        severity=req.severity,
    )
    if not alert:
        raise HTTPException(404, f"Zone {req.zone_id} not found or alert deduplicated")
    ws_dict = alert.to_ws_dict()
    # Backwards compatibility fields for V1 script
    ws_dict["assigned_drone"] = ws_dict.get("primary_drone")
    ws_dict["eta"] = ws_dict.get("primary_eta", 0)
    
    return ws_dict
@router.get("/{alert_id}")
async def get_alert(alert_id: str):
    """Get single alert detail."""
    alert = await crud.get_alert(alert_id)
    if not alert:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return alert
@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    from app.services.background_tasks import alert_manager
    if not alert_manager:
        raise HTTPException(500, "Alert manager not initialized")
    alert = await alert_manager.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(404, f"Alert {alert_id} not found")
    return alert.to_ws_dict()
