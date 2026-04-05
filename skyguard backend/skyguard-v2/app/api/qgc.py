"""SkyGuard V2 — QGC (H12 Controller) API & Overlay."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import os
router = APIRouter(prefix="/qgc", tags=["qgc"])
class QGCDispatchRequest(BaseModel):
    alert_id: str
    drone_ids: list[str] = []
@router.get("/fleet_status")
async def fleet_status():
    """Compact fleet summary for H12 overlay."""
    from app.services.background_tasks import drone_sim
    if not drone_sim:
        return {"drones": []}
    drones = []
    for d in drone_sim.get_all():
        drones.append({
            "id": d.id,
            "status": d.status.value,
            "battery": d.battery,
            "eta": round(d.eta_seconds, 0),
            "lat": d.position["lat"],
            "lon": d.position["lon"],
            "alert": d.assigned_alert_id,
        })
    return {"drones": drones}
@router.post("/dispatch")
async def qgc_dispatch(req: QGCDispatchRequest):
    """Dispatch from H12."""
    from app.services.background_tasks import alert_manager
    if not alert_manager:
        raise HTTPException(500, "Not initialized")
    # Use manual alert flow
    alert = await alert_manager.create_manual_alert(zone_id="Zone-A", severity=0.9)
    if alert:
        return alert.to_ws_dict()
    raise HTTPException(400, "Dispatch failed")
@router.post("/reroute/{drone_id}")
async def qgc_reroute(drone_id: str, lat: float = 18.52, lon: float = 73.85):
    """Reroute from H12."""
    from app.services.background_tasks import drone_sim, alert_manager as am
    if not drone_sim:
        raise HTTPException(500, "Not initialized")
    graph = am.airspace_graph if am else None
    if graph:
        from app.core.routing import clsp_shortest_path
        route = clsp_shortest_path(graph, drone_sim.get_drone(drone_id).position["lat"],
                                   drone_sim.get_drone(drone_id).position["lon"], lat, lon)
        drone_sim.reroute_drone(drone_id, lat, lon, route["waypoints"])
    return {"status": "rerouted"}
@router.post("/rtl/{drone_id}")
async def qgc_rtl(drone_id: str):
    """RTL from H12."""
    from app.services.background_tasks import drone_sim
    if not drone_sim:
        raise HTTPException(500, "Not initialized")
    drone_sim.rtl(drone_id)
    return {"status": "returning"}
@router.post("/emergency_land/{drone_id}")
async def qgc_emergency_land(drone_id: str):
    """Emergency land — immediate hover + RTL."""
    from app.services.background_tasks import drone_sim
    if not drone_sim:
        raise HTTPException(500, "Not initialized")
    drone_sim.rtl(drone_id)
    return {"status": "emergency_landing"}
@router.get("/overlay")
async def qgc_overlay():
    """Serve QGC overlay HTML."""
    overlay_path = os.path.join("static", "qgc_overlay.html")
    if os.path.exists(overlay_path):
        with open(overlay_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>QGC Overlay not found</h1>", status_code=404)