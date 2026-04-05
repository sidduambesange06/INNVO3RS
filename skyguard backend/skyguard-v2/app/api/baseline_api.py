"""SkyGuard V2 — Baseline Stats API."""
from fastapi import APIRouter
router = APIRouter(prefix="/baseline", tags=["baseline"])
@router.get("/stats")
async def baseline_stats():
    """Get current anomaly scores for all zones."""
    from app.services.background_tasks import baseline_engine
    if baseline_engine and baseline_engine.is_loaded:
        return {"zones": baseline_engine.get_all_zone_stats()}
    return {"zones": []}