"""SkyGuard V2 — Heatmap API Routes."""
from fastapi import APIRouter
from typing import Optional
router = APIRouter(prefix="/heatmap", tags=["heatmap"])
@router.get("")
async def get_heatmap():
    """Get current KDE heatmap."""
    from app.services.background_tasks import heatmap_engine
    if heatmap_engine:
        data = await heatmap_engine.compute_realtime_heatmap()
        return data.to_dict()
    return {"points": [], "hotspots": [], "total_incidents": 0}
@router.get("/predict")
async def predict_heatmap(hour: Optional[int] = None):
    """Gemini risk predictions for next 2 hours."""
    from datetime import datetime
    from app.services import gemini_service
    from app.services.background_tasks import heatmap_engine
    if hour is None:
        hour = datetime.now().hour
    zone_stats = []
    if heatmap_engine:
        heatmap = await heatmap_engine.compute_realtime_heatmap()
        zone_stats = [{"zone_id": h.zone_id, "incident_count": h.incident_count}
                      for h in heatmap.hotspots]
    predictions = await gemini_service.predict_risk_zones(zone_stats, hour)
    return {"hour": hour, "predictions": predictions}
@router.get("/history")
async def heatmap_history(zone_id: Optional[str] = None, days: int = 7):
    """Historical incident counts."""
    from app.services.background_tasks import heatmap_engine
    if heatmap_engine:
        history = await heatmap_engine.get_history(zone_id=zone_id, days=days)
        return {"history": history}
    return {"history": []}