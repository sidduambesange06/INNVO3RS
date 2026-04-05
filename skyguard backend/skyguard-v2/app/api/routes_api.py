"""SkyGuard V2 — Routing API Routes."""
from fastapi import APIRouter
from pydantic import BaseModel
router = APIRouter(prefix="/routes", tags=["routes"])
class RoutePlanRequest(BaseModel):
    src_lat: float
    src_lon: float
    dst_lat: float
    dst_lon: float
@router.post("/plan")
async def plan_route(req: RoutePlanRequest):
    """Compute CLSP route between two points."""
    from app.services.background_tasks import alert_manager
    graph = alert_manager.airspace_graph if alert_manager else None
    if not graph:
        return {"error": "Airspace graph not loaded"}
    from app.core.routing import clsp_shortest_path
    route = clsp_shortest_path(graph, req.src_lat, req.src_lon, req.dst_lat, req.dst_lon)
    return route
@router.get("/no_fly_zones")
async def no_fly_zones():
    """Get active no-fly zone list."""
    from app.services.background_tasks import alert_manager
    geofence = alert_manager.geofence if alert_manager else None
    if geofence:
        return {"no_fly_zones": geofence.get_active_nfz()}
    return {"no_fly_zones": []}