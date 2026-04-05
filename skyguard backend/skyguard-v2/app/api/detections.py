"""SkyGuard V2 — Detection History API Routes."""
from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timedelta, timezone
from app.db import crud

router = APIRouter(prefix="/detections", tags=["detections"])


@router.get("/history")
async def get_detection_history(
    cam_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    class_name: Optional[str] = None,
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get detection history with filtering."""
    sql = """
        SELECT 
            detection_id,
            cam_id,
            zone_id,
            timestamp,
            class_name,
            confidence,
            bbox_x1, bbox_y1, bbox_x2, bbox_y2,
            track_id
        FROM detections
        WHERE timestamp > datetime('now', ? || ' hours')
    """
    params = [f"-{hours}"]
    
    if cam_id:
        sql += " AND cam_id = ?"
        params.append(cam_id)
    
    if zone_id:
        sql += " AND zone_id = ?"
        params.append(zone_id)
    
    if class_name:
        sql += " AND class_name = ?"
        params.append(class_name)
    
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    detections = await crud.fetch_all(sql, tuple(params))
    
    return {
        "detections": detections,
        "count": len(detections),
        "filters": {
            "cam_id": cam_id,
            "zone_id": zone_id,
            "class_name": class_name,
            "hours": hours,
        }
    }


@router.get("/anomalies")
async def get_anomaly_history(
    cam_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    anomaly_type: Optional[str] = None,
    hours: int = Query(default=1, ge=1, le=168),
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Get anomaly detection history with filtering."""
    sql = """
        SELECT 
            anomaly_detection_id,
            cam_id,
            zone_id,
            timestamp,
            anomaly_type,
            confidence,
            description,
            persons_count
        FROM anomaly_detections
        WHERE timestamp > datetime('now', ? || ' hours')
    """
    params = [f"-{hours}"]
    
    if cam_id:
        sql += " AND cam_id = ?"
        params.append(cam_id)
    
    if zone_id:
        sql += " AND zone_id = ?"
        params.append(zone_id)
    
    if anomaly_type:
        sql += " AND anomaly_type = ?"
        params.append(anomaly_type)
    
    sql += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    
    anomalies = await crud.fetch_all(sql, tuple(params))
    
    return {
        "anomalies": anomalies,
        "count": len(anomalies),
        "filters": {
            "cam_id": cam_id,
            "zone_id": zone_id,
            "anomaly_type": anomaly_type,
            "hours": hours,
        }
    }


@router.get("/stats")
async def get_detection_stats(
    hours: int = Query(default=24, ge=1, le=168),
):
    """Get detection statistics."""
    # Total detections
    total_sql = """
        SELECT COUNT(*) as total
        FROM detections
        WHERE timestamp > datetime('now', ? || ' hours')
    """
    total_result = await crud.fetch_one(total_sql, (f"-{hours}",))
    total_detections = total_result.get("total", 0) if total_result else 0
    
    # Detections by class
    class_sql = """
        SELECT class_name, COUNT(*) as count
        FROM detections
        WHERE timestamp > datetime('now', ? || ' hours')
        GROUP BY class_name
        ORDER BY count DESC
    """
    by_class = await crud.fetch_all(class_sql, (f"-{hours}",))
    
    # Detections by camera
    camera_sql = """
        SELECT cam_id, COUNT(*) as count
        FROM detections
        WHERE timestamp > datetime('now', ? || ' hours')
        GROUP BY cam_id
        ORDER BY count DESC
    """
    by_camera = await crud.fetch_all(camera_sql, (f"-{hours}",))
    
    # Anomalies by type
    anomaly_sql = """
        SELECT anomaly_type, COUNT(*) as count
        FROM anomaly_detections
        WHERE timestamp > datetime('now', ? || ' hours')
        GROUP BY anomaly_type
        ORDER BY count DESC
    """
    by_anomaly = await crud.fetch_all(anomaly_sql, (f"-{hours}",))
    
    # Total anomalies
    total_anomaly_sql = """
        SELECT COUNT(*) as total
        FROM anomaly_detections
        WHERE timestamp > datetime('now', ? || ' hours')
    """
    total_anomaly_result = await crud.fetch_one(total_anomaly_sql, (f"-{hours}",))
    total_anomalies = total_anomaly_result.get("total", 0) if total_anomaly_result else 0
    
    return {
        "period_hours": hours,
        "total_detections": total_detections,
        "total_anomalies": total_anomalies,
        "by_class": by_class,
        "by_camera": by_camera,
        "by_anomaly_type": by_anomaly,
    }


@router.get("/timeline")
async def get_detection_timeline(
    cam_id: Optional[str] = None,
    zone_id: Optional[str] = None,
    hours: int = Query(default=24, ge=1, le=168),
    interval_minutes: int = Query(default=60, ge=5, le=1440),
):
    """Get detection timeline (time-series data)."""
    sql = """
        SELECT 
            strftime('%Y-%m-%d %H:', timestamp) || 
            CAST((CAST(strftime('%M', timestamp) AS INTEGER) / ?) * ? AS TEXT) as time_bucket,
            COUNT(*) as count,
            COUNT(DISTINCT class_name) as unique_classes
        FROM detections
        WHERE timestamp > datetime('now', ? || ' hours')
    """
    params = [interval_minutes, interval_minutes, f"-{hours}"]
    
    if cam_id:
        sql += " AND cam_id = ?"
        params.append(cam_id)
    
    if zone_id:
        sql += " AND zone_id = ?"
        params.append(zone_id)
    
    sql += " GROUP BY time_bucket ORDER BY time_bucket"
    
    timeline = await crud.fetch_all(sql, tuple(params))
    
    return {
        "timeline": timeline,
        "interval_minutes": interval_minutes,
        "hours": hours,
    }


@router.delete("/cleanup")
async def cleanup_old_detections(
    days: int = Query(default=7, ge=1, le=30),
):
    """Clean up old detection records (admin only)."""
    # Delete old detections
    detections_sql = """
        DELETE FROM detections
        WHERE timestamp < datetime('now', ? || ' days')
    """
    await crud.execute(detections_sql, (f"-{days}",))
    
    # Delete old anomaly detections
    anomalies_sql = """
        DELETE FROM anomaly_detections
        WHERE timestamp < datetime('now', ? || ' days')
    """
    await crud.execute(anomalies_sql, (f"-{days}",))
    
    return {
        "status": "success",
        "message": f"Deleted detections older than {days} days"
    }
