"""SkyGuard V2 — Camera API Routes."""
import asyncio
import time

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse

from app.config import settings
from app.services.background_tasks import (
    annotated_frames,
    camera_manager,
    latest_detection_results,
    preview_frames,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/cameras", tags=["cameras"])

STREAM_FPS = max(1, settings.effective_stream_fps)
STREAM_FRAME_INTERVAL = 1.0 / STREAM_FPS


def _stream_jpeg_for_cam(cam_id: str) -> bytes | None:
    """Prefer high-FPS preview (with drawn boxes); fallback to full YOLO overlay JPEG."""
    p = preview_frames.get(cam_id)
    if p:
        return p
    return annotated_frames.get(cam_id)
@router.get("")
async def list_cameras():
    """Get all 8 camera statuses."""
    if camera_manager:
        return {"cameras": camera_manager.get_all_statuses()}
    return {"cameras": []}
@router.get("/{cam_id}/stream")
async def camera_stream(cam_id: str):
    """MJPEG at a steady 25 FPS: latest annotated frame, or raw preview while detection catches up."""
    if camera_manager and cam_id not in camera_manager.get_all_cam_ids():
        raise HTTPException(status_code=404, detail=f"Unknown camera: {cam_id}")

    async def generate():
        last_sent: bytes | None = None
        while True:
            t0 = time.perf_counter()
            frame_bytes = _stream_jpeg_for_cam(cam_id)
            if frame_bytes:
                last_sent = frame_bytes
            if last_sent:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(last_sent)).encode() + b"\r\n"
                    b"X-Timestamp: " + str(int(time.time() * 1000)).encode() + b"\r\n\r\n"
                    + last_sent
                    + b"\r\n"
                )
            elapsed = time.perf_counter() - t0
            await asyncio.sleep(max(0.0, STREAM_FRAME_INTERVAL - elapsed))

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for real-time
            "Connection": "keep-alive",
        }
    )
@router.get("/{cam_id}/snapshot")
async def camera_snapshot(cam_id: str):
    """Get latest JPEG snapshot from camera."""
    frame_bytes = _stream_jpeg_for_cam(cam_id)
    if frame_bytes:
        return Response(content=frame_bytes, media_type="image/jpeg")
    return Response(status_code=404, content=b"No frame available")
@router.get("/{cam_id}/detections")
async def camera_detections(cam_id: str):
    """Get latest detection result for a camera."""
    result = latest_detection_results.get(cam_id)
    if result:
        return result
    return {"cam_id": cam_id, "detections": [], "anomaly_flags": []}
