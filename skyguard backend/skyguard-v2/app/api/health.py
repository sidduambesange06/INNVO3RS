"""SkyGuard V2 — Health & Metrics API."""
import psutil
import time
from collections import Counter
from fastapi import APIRouter
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()
_start_time = time.time()


@router.get("/health")
async def health():
    """Full system health check."""
    from app.services.background_tasks import camera_manager, detector, baseline_engine, drone_sim, priority_queue

    uptime = round(time.time() - _start_time, 1)

    # Accurate drone status counts
    drone_statuses = Counter()
    if drone_sim:
        for d in drone_sim.get_all():
            drone_statuses[d.status.value] += 1

    return {
        "status": "healthy",
        "version": "2.0.0",
        "uptime_seconds": uptime,
        "components": {
            "database": "connected",
            "yolo": detector.get_status() if detector else {"status": "not_loaded"},
            "cameras": {
                "total": len(camera_manager.cameras) if camera_manager else 0,
                "connected": sum(1 for c in camera_manager.cameras.values() if c.is_connected()) if camera_manager else 0,
            },
            "drones": {
                "total": len(drone_sim.drones) if drone_sim else 0,
                "available": drone_sim.get_available_count() if drone_sim else 0,
                "statuses": dict(drone_statuses),
            },
            "baseline": "loaded" if baseline_engine and baseline_engine.is_loaded else "not_loaded",
            "queue": {
                "depth": len(priority_queue.get_queue_snapshot()) if priority_queue else 0,
                "assigned": sum(1 for i in (priority_queue.get_queue_snapshot() if priority_queue else []) if i.get("assigned")),
            },
        },
    }


@router.get("/metrics")
async def metrics():
    """System performance metrics."""
    from app.services.background_tasks import camera_manager, detector, priority_queue

    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    camera_fps = {}
    if camera_manager:
        for cam_id, cam in camera_manager.cameras.items():
            camera_fps[cam_id] = cam.get_fps()
    return {
        "cpu_percent": cpu,
        "memory_percent": mem.percent,
        "memory_used_mb": round(mem.used / 1024 / 1024, 1),
        "per_camera_fps": camera_fps,
        "detector_fps": detector.get_fps() if detector else 0,
        "queue_depth": len(priority_queue.get_queue_snapshot()) if priority_queue else 0,
    }


@router.get("/queue")
async def queue_snapshot():
    """Get priority queue state for debugging/dashboard."""
    from app.services.background_tasks import priority_queue
    if not priority_queue:
        return {"queue": []}
    return {"queue": priority_queue.get_queue_snapshot()}