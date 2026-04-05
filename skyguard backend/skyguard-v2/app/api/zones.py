"""SkyGuard V2 — Zone API Routes."""
import json
from fastapi import APIRouter
from app.db import crud
router = APIRouter(prefix="/zones", tags=["zones"])
@router.get("")
async def list_zones():
    """Get all zones with current stats."""
    from app.services.background_tasks import baseline_engine
    zones = await crud.get_all_zones()
    result = []
    for z in zones:
        zone_dict = dict(z)
        if zone_dict.get("polygon_geojson"):
            try:
                zone_dict["polygon"] = json.loads(zone_dict["polygon_geojson"])
            except Exception:
                zone_dict["polygon"] = []
        del zone_dict["polygon_geojson"]
        # Attach latest baseline
        if baseline_engine:
            stats = baseline_engine.get_all_zone_stats()
            for s in stats:
                if s.get("zone_id") == z["zone_id"]:
                    zone_dict["current_stats"] = s
                    break
        result.append(zone_dict)
    return {"zones": result}
@router.get("/{zone_id}/baseline")
async def zone_baseline(zone_id: str):
    """Get hourly baseline profile for a zone."""
    baselines = await crud.get_zone_baselines(zone_id)
    return {"zone_id": zone_id, "baselines": baselines}