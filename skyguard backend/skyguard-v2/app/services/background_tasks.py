"""SkyGuard V2 — Background Task Loops.

Includes a high-FPS preview encoder (smooth MJPEG) separate from YOLO inference.
"""

import asyncio
import time
from datetime import datetime, timezone

import cv2
import numpy as np

from app.db.database import is_db_open
from app.services.websocket import (
    emit_drone_update, emit_baseline_update, emit_heatmap_update,
    emit_camera_offline, emit_camera_online, emit_detection_stream,
    emit_drone_reallocated, emit_system_error,
)
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Limit parallel YOLO runs so the event loop (and MJPEG streams) stay responsive.
_inference_semaphore: asyncio.Semaphore | None = None


def _get_inference_semaphore() -> asyncio.Semaphore:
    global _inference_semaphore
    if _inference_semaphore is None:
        n = max(1, min(8, settings.yolo_max_parallel_inferences))
        _inference_semaphore = asyncio.Semaphore(n)
    return _inference_semaphore

# These will be set by main.py
camera_manager = None
detector = None
baseline_engine = None
drone_sim = None
priority_queue = None
alert_manager = None
heatmap_engine = None
zone_cam_map = {}  # cam_id -> {"zone_id": str, "zone_name": str, "polygon": list, "lat": float, "lon": float}

# Per-camera latest annotated frame (for MJPEG stream)
annotated_frames: dict[str, bytes] = {}
# Raw JPEG from camera source at stream FPS (smooth video independent of YOLO speed).
preview_frames: dict[str, bytes] = {}
# Wall-clock time when annotated_frames[cam_id] was last updated (for stream TTL logic).
annotated_frame_ts: dict[str, float] = {}
latest_detection_results: dict[str, dict] = {}

# Set True in main.shutdown before canceling tasks / closing DB.
shutting_down: bool = False


def _encode_jpeg_preview(frame: np.ndarray, quality: int) -> bytes:
    _, buf = cv2.imencode(
        ".jpg",
        frame,
        [cv2.IMWRITE_JPEG_QUALITY, quality, cv2.IMWRITE_JPEG_OPTIMIZE, 0],
    )
    return buf.tobytes()


def _draw_ws_detections_on_frame(frame: np.ndarray, ws: dict | None) -> np.ndarray:
    """Lightweight overlay from latest_detection_results (WebSocket-shaped dict)."""
    out = frame
    if not ws or not settings.stream_overlay_detections_on_preview:
        return out
    out = frame.copy()
    for det in ws.get("detections") or []:
        bb = det.get("bbox")
        if not bb or len(bb) < 4:
            continue
        x1, y1, x2, y2 = int(bb[0]), int(bb[1]), int(bb[2]), int(bb[3])
        cls = str(det.get("class", ""))
        conf = det.get("confidence", 0)
        color = (0, 0, 255) if cls not in ("person",) else (0, 255, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            out,
            f"{cls} {conf:.2f}",
            (x1, max(12, y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            color,
            1,
            cv2.LINE_AA,
        )
    y0 = 22
    for flag in ws.get("anomaly_flags") or []:
        t = str(flag.get("type", ""))[:28]
        cv2.putText(
            out,
            t,
            (8, y0),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 255),
            1,
            cv2.LINE_AA,
        )
        y0 += 18
    return out


def _batch_encode_preview_frames(
    pending: list[tuple[str, np.ndarray]],
    quality: int,
    det_snap: dict[str, dict],
) -> None:
    """One worker call: draw + JPEG for all cameras (avoids 8× asyncio thread hops)."""
    for cid, frame in pending:
        vis = _draw_ws_detections_on_frame(frame, det_snap.get(cid))
        preview_frames[cid] = _encode_jpeg_preview(vis, quality)


async def preview_stream_loop():
    """Encode live camera frames at stream FPS so MJPEG stays smooth while YOLO catches up."""
    logger.info("Preview stream loop started")
    interval = 1.0 / max(1, settings.effective_stream_fps)
    while True:
        if shutting_down:
            return
        try:
            if not camera_manager:
                await asyncio.sleep(0.15)
                continue
            t0 = time.perf_counter()
            q = settings.stream_preview_jpeg_quality
            pending: list[tuple[str, np.ndarray]] = []
            for cid in camera_manager.get_all_cam_ids():
                fr = camera_manager.get_frame(cid)
                if fr is not None:
                    pending.append((cid, fr))
            if pending:
                det_snap = dict(latest_detection_results)
                await asyncio.to_thread(
                    _batch_encode_preview_frames,
                    pending,
                    q,
                    det_snap,
                )
            elapsed = time.perf_counter() - t0
            await asyncio.sleep(max(0.0, interval - elapsed))
        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Preview stream loop error: {e}")
            await asyncio.sleep(0.1)


async def detection_loop():
    """Fair round-robin YOLO: limited parallelism + min gap per camera (CPU-friendly)."""
    logger.info("Detection loop started")
    last_infer: dict[str, float] = {}
    min_gap = settings.detection_min_interval_s
    max_parallel = max(1, min(8, settings.yolo_max_parallel_inferences))

    while True:
        if shutting_down:
            return
        try:
            if not camera_manager or not detector or not detector.is_loaded:
                await asyncio.sleep(0.5)
                continue

            now = time.time()
            cam_ids = sorted(
                camera_manager.get_all_cam_ids(),
                key=lambda c: last_infer.get(c, 0.0),
            )
            tasks: list[asyncio.Task] = []
            for cam_id in cam_ids:
                if len(tasks) >= max_parallel:
                    break
                if now - last_infer.get(cam_id, 0.0) >= min_gap:
                    last_infer[cam_id] = now
                    tasks.append(asyncio.create_task(process_camera_frame(cam_id)))
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

        except asyncio.CancelledError:
            return
        except Exception as e:
            logger.error(f"Detection loop error: {e}")
            try:
                await emit_system_error(f"Detection error: {str(e)}")
            except Exception:
                pass

        await asyncio.sleep(0.005)


async def process_camera_frame(cam_id: str):
    """Process a single camera frame with detection and storage."""
    try:
        frame = camera_manager.get_frame(cam_id)
        if frame is None:
            return

        zone_info = zone_cam_map.get(cam_id, {})
        zone_id = zone_info.get("zone_id", "")
        zone_name = zone_info.get("zone_name", "")
        zone_polygon = zone_info.get("polygon", [])

        async with _get_inference_semaphore():
            result, annotated_jpeg = await asyncio.to_thread(
                detector.detect_and_encode_annotated,
                frame,
                cam_id,
                zone_polygon,
                settings.stream_annotated_jpeg_quality,
            )
        result.zone_id = zone_id
        result.timestamp = datetime.now(timezone.utc).isoformat() + "Z"

        # Store latest result in memory
        latest_detection_results[cam_id] = result.to_ws_dict()

        # Store detection in database (async, non-blocking)
        if result.detections or result.anomaly_flags:
            asyncio.create_task(store_detection_to_db(cam_id, zone_id, result))

        annotated_frames[cam_id] = annotated_jpeg
        annotated_frame_ts[cam_id] = time.time()

        # Emit detection stream to subscribed clients (real-time)
        await emit_detection_stream(cam_id, result.to_ws_dict())

        # Baseline check and alert creation
        if baseline_engine and baseline_engine.is_loaded and result.persons_count > 0:
            # Determine primary anomaly type
            primary_anomaly = "crowd_anomaly"
            for flag in result.anomaly_flags:
                if flag.anomaly_type in ("weapon_detect", "person_down", "fight_detection"):
                    primary_anomaly = flag.anomaly_type
                    break

            bl_result = baseline_engine.calculate(zone_id, result.persons_count, primary_anomaly)

            if is_db_open():
                await baseline_engine.update_baseline(zone_id, datetime.now().hour, result.persons_count)

            # Create alert if threshold exceeded
            if (
                is_db_open()
                and bl_result.final_severity > settings.baseline_severity_threshold
                and alert_manager
            ):
                await alert_manager.create_from_detection(
                    cam_id=cam_id,
                    zone_id=zone_id,
                    zone_name=zone_name,
                    anomaly_type=primary_anomaly,
                    severity=bl_result.final_severity,
                    current_count=bl_result.current_count,
                    baseline_mean=bl_result.baseline_mean,
                    z_score=bl_result.z_score,
                    location_lat=zone_info.get("lat", 0),
                    location_lon=zone_info.get("lon", 0),
                )

    except Exception as e:
        logger.error(f"Error processing camera {cam_id}: {e}")


async def store_detection_to_db(cam_id: str, zone_id: str, result):
    """Store detection results to database asynchronously."""
    try:
        if shutting_down or not is_db_open():
            return
        from app.db import crud
        from datetime import datetime, timezone
        
        # Store each detection
        for detection in result.detections:
            await crud.execute(
                """INSERT INTO detections 
                   (cam_id, zone_id, timestamp, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2, track_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    cam_id,
                    zone_id,
                    datetime.now(timezone.utc).isoformat(),
                    detection.class_name,
                    detection.confidence,
                    detection.bbox.x1,
                    detection.bbox.y1,
                    detection.bbox.x2,
                    detection.bbox.y2,
                    detection.track_id,
                )
            )
        
        # Store anomaly flags
        for flag in result.anomaly_flags:
            await crud.execute(
                """INSERT INTO anomaly_detections 
                   (cam_id, zone_id, timestamp, anomaly_type, confidence, description, persons_count)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    cam_id,
                    zone_id,
                    datetime.now(timezone.utc).isoformat(),
                    flag.anomaly_type,
                    flag.confidence,
                    flag.description,
                    result.persons_count,
                )
            )
        
        logger.debug(f"Stored {len(result.detections)} detections and {len(result.anomaly_flags)} anomalies for {cam_id}")
        
    except Exception as e:
        logger.error(f"Error storing detection to DB for {cam_id}: {e}")


async def priority_queue_loop():
    """500ms loop: update drone positions + re-evaluate queue."""
    logger.info("Priority queue loop started")

    while True:
        if shutting_down:
            return
        try:
            if drone_sim and priority_queue:
                # Re-evaluate (this also updates drone positions)
                reallocations = await priority_queue.re_evaluate()

                # Emit reallocation events
                for realloc in reallocations:
                    await emit_drone_reallocated(realloc)

                # Emit drone update
                drones = drone_sim.get_all_api()
                await emit_drone_update(drones)

                if is_db_open():
                    from app.db import crud
                    for d in drone_sim.get_all():
                        await crud.update_drone(
                            drone_id=d.id,
                            status=d.status.value if hasattr(d.status, 'value') else d.status,
                            current_lat=d.position["lat"],
                            current_lon=d.position["lon"],
                            battery=d.battery
                        )

        except asyncio.CancelledError:
            return
        except Exception as e:
            if not shutting_down and is_db_open():
                logger.error(f"Priority queue loop error: {e}")

        await asyncio.sleep(max(0.05, settings.reallocation_interval_ms / 1000.0))


async def baseline_broadcast_loop():
    """5s loop: broadcast baseline stats."""
    logger.info("Baseline broadcast loop started")

    while True:
        if shutting_down:
            return
        try:
            if baseline_engine and baseline_engine.is_loaded:
                stats = baseline_engine.get_all_zone_stats()
                await emit_baseline_update(stats)
        except asyncio.CancelledError:
            return
        except Exception as e:
            if not shutting_down:
                logger.error(f"Baseline broadcast error: {e}")

        await asyncio.sleep(5)


async def heatmap_loop():
    """30s loop: compute KDE heatmap."""
    logger.info("Heatmap loop started")

    while True:
        if shutting_down:
            return
        try:
            if heatmap_engine and is_db_open():
                heatmap = await heatmap_engine.compute_realtime_heatmap()
                await emit_heatmap_update(heatmap.to_dict())
        except asyncio.CancelledError:
            return
        except Exception as e:
            if not shutting_down and is_db_open():
                logger.error(f"Heatmap loop error: {e}")

        await asyncio.sleep(30)


async def camera_health_loop():
    """10s loop: check camera connectivity."""
    logger.info("Camera health loop started")
    last_status: dict[str, bool] = {}

    while True:
        if shutting_down:
            return
        try:
            if camera_manager:
                for cam_id in camera_manager.get_all_cam_ids():
                    cam = camera_manager.get_camera(cam_id)
                    if cam:
                        connected = cam.is_connected()
                        prev = last_status.get(cam_id, True)
                        if prev and not connected:
                            await emit_camera_offline(cam_id)
                            logger.warning(f"📷 {cam_id} went offline")
                        elif not prev and connected:
                            await emit_camera_online(cam_id)
                            logger.info(f"📷 {cam_id} back online")
                        last_status[cam_id] = connected
        except asyncio.CancelledError:
            return
        except Exception as e:
            if not shutting_down:
                logger.error(f"Camera health error: {e}")

        await asyncio.sleep(10)
