"""
SkyGuard V2 — Main Application.

Do not start with plain ``uvicorn app.main:app --port 8000`` if port 8000 may be taken:
Uvicorn runs full startup then exits (WinError 10048). Use instead:

  python run_server.py
  python -m app

Optional: SKYGUARD_FREE_LISTEN_PORT=1 (default in run_server) frees stale listeners on Windows.
"""

import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.config import settings
from app.core.camera_manager import CameraManager
from app.core.detection import MultiModelDetector
from app.core.yolo_runtime import resolve_yolo_device_and_half
from app.core.baseline import BaselineEngine
from app.core.drone_simulator import DroneSimulator
from app.core.priority_queue import DroneDispatchQueue
from app.core.geofence import GeofenceValidator
from app.core.routing import AirspaceGraph
from app.core.heatmap import HeatmapEngine
from app.services.alert_manager import AlertManager
from app.services.websocket import sio
from app.services import background_tasks
from app.db.database import init_db, close_db
from app.db.seed import seed_all
from app.db import crud
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Background asyncio tasks (cancelled on shutdown before DB close).
_background_tasks: list[asyncio.Task] = []

# =============================================================================
# Create FastAPI app
# =============================================================================

fastapi_app = FastAPI(
    title="SkyGuard V2",
    version="2.0.0",
    description="AI Drone Response System for Urban Safety — Pune Police Drone Office",
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
from app.api.health import router as health_router
from app.api.cameras import router as cameras_router
from app.api.zones import router as zones_router
from app.api.alerts import router as alerts_router
from app.api.drones import router as drones_router
from app.api.routes_api import router as routes_router
from app.api.sos import router as sos_router
from app.api.heatmap_api import router as heatmap_router
from app.api.baseline_api import router as baseline_router
from app.api.qgc import router as qgc_router
from app.api.detections import router as detections_router

fastapi_app.include_router(health_router)
fastapi_app.include_router(cameras_router)
fastapi_app.include_router(zones_router)
fastapi_app.include_router(alerts_router)
fastapi_app.include_router(drones_router)
fastapi_app.include_router(routes_router)
fastapi_app.include_router(sos_router)
fastapi_app.include_router(heatmap_router)
fastapi_app.include_router(baseline_router)
fastapi_app.include_router(qgc_router)
fastapi_app.include_router(detections_router)

# =============================================================================
# Backwards Compatibility (V1 Endpoints)
# =============================================================================
from pydantic import BaseModel, ConfigDict
from fastapi.responses import StreamingResponse

class V1ManualAlert(BaseModel):
    model_config = ConfigDict(extra='allow')
    zone_id: str = "Zone-A"
    severity: float = 0.85

@fastapi_app.post("/manual_alert")
async def v1_manual_alert(req: V1ManualAlert):
    if alert_mgr:
        alert = await alert_mgr.create_manual_alert(
            zone_id=req.zone_id, anomaly_type="crowd_anomaly", severity=req.severity
        )
        if alert:
            ws_dict = alert.to_ws_dict()
            ws_dict["assigned_drone"] = ws_dict.get("primary_drone")
            ws_dict["eta"] = ws_dict.get("primary_eta", 0)
            return ws_dict
    from fastapi import HTTPException
    raise HTTPException(400, "Failed to create alert")

@fastapi_app.get("/stream")
async def v1_stream():
    """V1 global stream endpoint (first camera with a frame, TTL-aware like /cameras/.../stream)."""
    async def generate():
        interval = 1.0 / max(1, settings.effective_stream_fps)
        while True:
            from app.api.cameras import _stream_jpeg_for_cam
            from app.services import background_tasks as bt
            if bt.camera_manager:
                for cam_id in sorted(bt.camera_manager.get_all_cam_ids()):
                    frame_bytes = _stream_jpeg_for_cam(cam_id)
                    if frame_bytes:
                        yield (b"--frame\r\n"
                               b"Content-Type: image/jpeg\r\n\r\n"
                               + frame_bytes + b"\r\n")
                        break
            await asyncio.sleep(interval)
    return StreamingResponse(generate(), media_type="multipart/x-mixed-replace; boundary=frame")


# Combined ASGI app: SocketIO wraps FastAPI
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

# =============================================================================
# Global component instances (exported for background_tasks)
# =============================================================================
drone_sim: DroneSimulator = None
baseline_engine: BaselineEngine = None
alert_mgr: AlertManager = None


# =============================================================================
# Startup
# =============================================================================

@fastapi_app.on_event("startup")
async def startup():
    global drone_sim, baseline_engine, alert_mgr

    logger.info("=" * 60)
    logger.info("Starting SkyGuard V2...")
    logger.info("=" * 60)

    # 1. Database
    await init_db(settings.database_path)
    logger.info("✅ Database initialized")

    # 2. Seed data
    existing = await crud.get_all_cameras()
    if not existing:
        await seed_all()
        logger.info("✅ Database seeded")
    else:
        logger.info(f"✅ Database already seeded ({len(existing)} cameras)")

    # 3. Geofence
    geofence = GeofenceValidator()
    geofence.load_zones()
    logger.info("✅ Geofence loaded")

    # 4. Airspace graph
    graph = AirspaceGraph()
    graph_path = "data/airspace/pune_graph.json"
    if not graph.load(graph_path):
        logger.info("Building airspace graph (first run)...")
        graph.build(geofence.get_nfz_objects())
        graph.save(graph_path)
    logger.info("✅ Airspace graph ready")

    # 5. YOLO detector (GPU when YOLO_DEVICE=auto/gpu/cuda and CUDA is available)
    yolo_dev, yolo_fp16 = resolve_yolo_device_and_half()
    detector = MultiModelDetector(
        model_path=settings.yolo_model_path,
        confidence=settings.yolo_confidence,
        device=yolo_dev,
        imgsz=settings.yolo_imgsz,
        half=yolo_fp16,
        max_det=settings.yolo_max_det,
        iou=settings.yolo_iou,
    )
    try:
        detector.load()
    except Exception as e:
        logger.error(f"YOLO load failed (continuing without detection): {e}")
    logger.info("✅ YOLO detector ready")

    # 6. Camera manager
    cam_manager = CameraManager()
    cameras = await crud.get_all_cameras()
    await cam_manager.initialize_from_db(cameras)
    logger.info("✅ Camera manager ready")

    # 7. Baseline engine
    baseline_engine = BaselineEngine()
    await baseline_engine.load_from_db()
    logger.info("✅ Baseline engine ready")

    # 8. Drone simulator
    drone_sim = DroneSimulator(
        speed_ms=settings.drone_speed_ms,
        min_battery=settings.drone_min_battery,
        hover_time_s=settings.drone_hover_time_s,
    )
    await drone_sim.initialize_from_db()
    logger.info("✅ Drone simulator ready")

    # 9. Priority queue
    pq = DroneDispatchQueue(
        severity_decay=settings.severity_decay,
        reallocation_threshold=settings.reallocation_threshold,
    )
    pq.set_drone_simulator(drone_sim)
    pq.set_airspace_graph(graph)
    pq.set_geofence(geofence)
    logger.info("✅ Priority queue ready")

    # 10. Heatmap engine
    heatmap = HeatmapEngine()
    logger.info("✅ Heatmap engine ready")

    # 11. Alert manager
    alert_mgr = AlertManager(
        drone_sim=drone_sim,
        priority_queue=pq,
        baseline_engine=baseline_engine,
        geofence=geofence,
        airspace_graph=graph,
    )
    logger.info("✅ Alert manager ready")

    # 12. Build zone-camera map for detection loop
    zone_cam_map = {}
    for cam in cameras:
        polygon = []
        if cam.get("polygon_geojson"):
            try:
                polygon = json.loads(cam["polygon_geojson"])
            except Exception:
                pass
        zone_cam_map[cam["cam_id"]] = {
            "zone_id": cam.get("zone_id", ""),
            "zone_name": cam.get("name", ""),
            "polygon": polygon,
            "lat": cam.get("lat", 0),
            "lon": cam.get("lon", 0),
        }

    # 13. Wire up background tasks
    background_tasks.camera_manager = cam_manager
    background_tasks.detector = detector
    background_tasks.baseline_engine = baseline_engine
    background_tasks.drone_sim = drone_sim
    background_tasks.priority_queue = pq
    background_tasks.alert_manager = alert_mgr
    background_tasks.heatmap_engine = heatmap
    background_tasks.zone_cam_map = zone_cam_map

    # 14. Start background loops (preview first for fast MJPEG fill)
    global _background_tasks
    background_tasks.shutting_down = False
    _background_tasks = [
        asyncio.create_task(background_tasks.preview_stream_loop()),
        asyncio.create_task(background_tasks.detection_loop()),
        asyncio.create_task(background_tasks.priority_queue_loop()),
        asyncio.create_task(background_tasks.baseline_broadcast_loop()),
        asyncio.create_task(background_tasks.heatmap_loop()),
        asyncio.create_task(background_tasks.camera_health_loop()),
    ]

    logger.info("=" * 60)
    logger.info("✅ SkyGuard V2 fully initialized!")
    logger.info(f"   API:       http://{settings.api_host}:{settings.api_port}")
    logger.info(f"   Health:    http://{settings.api_host}:{settings.api_port}/health")
    logger.info(f"   Cameras:   8 ({sum(1 for c in cam_manager.cameras.values() if c.is_connected())} connected)")
    logger.info(f"   Drones:    {len(drone_sim.drones)}")
    logger.info(f"   NFZs:      {len(geofence.get_active_nfz())}")
    logger.info(f"   WebSocket: ws://{settings.api_host}:{settings.api_port}")
    logger.info("=" * 60)


@fastapi_app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down SkyGuard V2...")
    global _background_tasks
    background_tasks.shutting_down = True
    for t in _background_tasks:
        t.cancel()
    if _background_tasks:
        await asyncio.gather(*_background_tasks, return_exceptions=True)
    _background_tasks.clear()
    if background_tasks.camera_manager:
        background_tasks.camera_manager.disconnect_all()
    await asyncio.sleep(0.05)
    await close_db()
    logger.info("Shutdown complete")
