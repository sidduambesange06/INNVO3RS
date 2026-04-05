"""SkyGuard V2 — SOS API Routes."""
from fastapi import APIRouter, HTTPException
from app.models.sos import SOSCreate
from app.utils.logger import setup_logger
logger = setup_logger(__name__)
router = APIRouter(prefix="/sos", tags=["sos"])
@router.post("")
async def create_sos(req: SOSCreate):
    """Create SOS event with 30s buffer countdown."""
    from app.services.background_tasks import alert_manager
    if not alert_manager:
        raise HTTPException(500, "Alert manager not initialized")
    sos = await alert_manager.create_from_sos(req)
    from datetime import datetime, timezone, timedelta
    deadline = datetime.now(timezone.utc) + timedelta(seconds=30)
    return {
        "sos_id": sos.sos_id,
        "status": sos.status.value if hasattr(sos.status, 'value') else sos.status,
        "confirmation_deadline": deadline.isoformat() + "Z",
        "buffer_seconds": 30,
        "message": "SOS received. Cancel within 30 seconds to abort dispatch.",
    }
@router.post("/{sos_id}/cancel")
async def cancel_sos(sos_id: str, reason: str = "User cancelled"):
    """Cancel SOS within buffer window."""
    from app.services.background_tasks import alert_manager
    if not alert_manager:
        raise HTTPException(500, "Alert manager not initialized")
    success = await alert_manager.cancel_sos(sos_id, reason)
    if not success:
        raise HTTPException(409, "SOS already dispatched or not found")
    return {"sos_id": sos_id, "status": "CANCELLED", "reason": reason}
@router.get("")
async def list_sos(status: str = None, limit: int = 50):
    """List SOS events."""
    from app.db import crud
    events = await crud.get_sos_events(status=status, limit=limit)
    return {"sos_events": events, "count": len(events)}
@router.get("/{sos_id}")
async def get_sos(sos_id: str):
    """Get single SOS event."""
    from app.services.background_tasks import alert_manager
    if alert_manager:
        sos = alert_manager.get_sos_event(sos_id)
        if sos:
            return sos.to_ws_dict()
    from app.db import crud
    sos = await crud.get_sos(sos_id)
    if not sos:
        raise HTTPException(404, f"SOS {sos_id} not found")
    return sos