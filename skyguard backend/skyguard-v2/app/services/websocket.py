"""SkyGuard V2 — WebSocket Service.
All 14 real-time events via python-socketio.
"""
import socketio
from app.utils.logger import setup_logger
logger = setup_logger(__name__)
# Async Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=False,
    engineio_logger=False,
)
socket_app = socketio.ASGIApp(sio)
# --- Connection handlers ---
@sio.event
async def connect(sid, environ):
    await sio.enter_room(sid, "all_clients")
    logger.info(f"WebSocket connected: {sid}")
    # Send state snapshot on reconnect
    from app.services import _state_snapshot
    snapshot = _state_snapshot()
    if snapshot:
        await sio.emit("state_snapshot", {"data": snapshot}, to=sid)
@sio.event
async def disconnect(sid):
    logger.info(f"WebSocket disconnected: {sid}")
@sio.on("subscribe_camera")
async def on_subscribe_camera(sid, data):
    cam_id = data.get("cam_id", "") if isinstance(data, dict) else ""
    room = f"cam_{cam_id}"
    await sio.enter_room(sid, room)
    logger.info(f"{sid} subscribed to {room}")
# --- Emit functions ---
async def emit_drone_update(drones: list[dict]) -> None:
    await sio.emit("drone_update", {"data": {"drones": drones}}, room="all_clients")
async def emit_alert_created(alert: dict) -> None:
    await sio.emit("alert_created", {"data": alert}, room="all_clients")
async def emit_alert_updated(alert: dict) -> None:
    await sio.emit("alert_updated", {"data": alert}, room="all_clients")
async def emit_baseline_update(zones: list[dict]) -> None:
    await sio.emit("baseline_update", {"data": {"zones": zones}}, room="all_clients")
async def emit_heatmap_update(heatmap: dict) -> None:
    await sio.emit("heatmap_update", {"data": heatmap}, room="all_clients")
async def emit_sos_received(sos: dict) -> None:
    await sio.emit("sos_received", {"data": sos}, room="all_clients")
async def emit_sos_countdown(sos_id: str, seconds: int) -> None:
    await sio.emit("sos_countdown", {"data": {"sos_id": sos_id, "seconds_remaining": seconds}}, room="all_clients")
async def emit_sos_dispatched(sos: dict, alert: dict) -> None:
    await sio.emit("sos_dispatched", {"data": {"sos": sos, "alert": alert}}, room="all_clients")
async def emit_sos_cancelled(sos: dict) -> None:
    await sio.emit("sos_cancelled", {"data": sos}, room="all_clients")
async def emit_drone_reallocated(event: dict) -> None:
    await sio.emit("drone_reallocated", {"data": event}, room="all_clients")
async def emit_camera_offline(cam_id: str) -> None:
    await sio.emit("camera_offline", {"data": {"cam_id": cam_id}}, room="all_clients")
async def emit_camera_online(cam_id: str) -> None:
    await sio.emit("camera_online", {"data": {"cam_id": cam_id}}, room="all_clients")
async def emit_detection_stream(cam_id: str, result: dict) -> None:
    await sio.emit("detection_stream", {"data": result}, room=f"cam_{cam_id}")
async def emit_system_error(message: str) -> None:
    await sio.emit("system_error", {"data": {"message": message}}, room="all_clients")