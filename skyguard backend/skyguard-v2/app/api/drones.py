"""SkyGuard V2 — Drone API Routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.db import crud
router = APIRouter(prefix="/drones", tags=["drones"])
class DispatchRequest(BaseModel):
    lat: float
    lon: float
    zone_id: str = ""
class RerouteRequest(BaseModel):
    lat: float
    lon: float
    alert_id: Optional[str] = None
@router.get("")
async def list_drones():
    """Get all drone states."""
    from app.services.background_tasks import drone_sim
    if drone_sim:
        return {"drones": drone_sim.get_all_api()}
    return {"drones": []}
@router.get("/{drone_id}")
async def get_drone(drone_id: str):
    """Get single drone state."""
    from app.services.background_tasks import drone_sim
    if drone_sim:
        d = drone_sim.get_drone(drone_id)
        if d:
            return d.to_api_dict()
    raise HTTPException(404, f"Drone {drone_id} not found")
@router.post("/{drone_id}/dispatch")
async def dispatch_drone(drone_id: str, req: DispatchRequest):
    """Manual dispatch to a location."""
    from app.services.background_tasks import drone_sim, alert_manager
    if not drone_sim:
        raise HTTPException(500, "Drone simulator not initialized")
    from app.core.routing import clsp_shortest_path
    from app.services.background_tasks import alert_manager as am
    drone = drone_sim.get_drone(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    # Get airspace graph
    graph = am.airspace_graph if am else None
    if graph:
        route = clsp_shortest_path(graph, drone.position["lat"], drone.position["lon"], req.lat, req.lon)
    else:
        route = {"waypoints": [{"lat": req.lat, "lon": req.lon}], "total_distance_m": 0, "estimated_time_s": 0}
    ok = drone_sim.dispatch_drone(drone_id, f"MANUAL-{drone_id}", req.zone_id, req.lat, req.lon, route["waypoints"])
    if not ok:
        raise HTTPException(400, f"Cannot dispatch {drone_id}")
    return {"status": "dispatched", "drone_id": drone_id, "route": route}
@router.post("/{drone_id}/rtl")
async def rtl_drone(drone_id: str):
    """Return to launch."""
    from app.services.background_tasks import drone_sim
    if not drone_sim:
        raise HTTPException(500, "Drone simulator not initialized")
    ok = drone_sim.rtl(drone_id)
    if not ok:
        raise HTTPException(400, f"Cannot RTL {drone_id}")
    return {"status": "returning", "drone_id": drone_id}
@router.post("/{drone_id}/reroute")
async def reroute_drone(drone_id: str, req: RerouteRequest):
    """Reroute to new target."""
    from app.services.background_tasks import drone_sim, alert_manager as am
    if not drone_sim:
        raise HTTPException(500, "Drone simulator not initialized")
    drone = drone_sim.get_drone(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    graph = am.airspace_graph if am else None
    if graph:
        from app.core.routing import clsp_shortest_path
        route = clsp_shortest_path(graph, drone.position["lat"], drone.position["lon"], req.lat, req.lon)
    else:
        route = {"waypoints": [{"lat": req.lat, "lon": req.lon}]}
    ok = drone_sim.reroute_drone(drone_id, req.lat, req.lon, route.get("waypoints", []), req.alert_id)
    if not ok:
        raise HTTPException(400, f"Cannot reroute {drone_id}")
    return {"status": "rerouted", "drone_id": drone_id, "route": route}
@router.get("/{drone_id}/history")
async def drone_history(drone_id: str):
    """Get past missions for a drone."""
    missions = await crud.get_drone_missions(drone_id)
    return {"drone_id": drone_id, "missions": missions}