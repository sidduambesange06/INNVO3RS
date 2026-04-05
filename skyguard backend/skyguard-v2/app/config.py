"""SkyGuard V2 — Configuration via Pydantic Settings."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )
    # Camera / stream (MJPEG and detection scheduling target)
    rtsp_url: str = "rtsp://admin:admin@192.168.1.250:554/cam/realmonitor?channel=1&subtype=0"
    camera_fps_target: int = 25
    stream_min_fps: int = 25
    camera_width: int = 640
    camera_height: int = 360

    # YOLO
    yolo_model_path: str = "data/models/yolo11n.pt"
    yolo_confidence: float = 0.5
    # auto | gpu | cpu | cuda | cuda:0 — auto picks GPU when PyTorch sees CUDA
    yolo_device: str = "auto"
    yolo_imgsz: int = 320
    yolo_half: bool = False
    yolo_max_det: int = 30
    yolo_iou: float = 0.5
    yolo_max_parallel_inferences: int = 2
    stream_preview_jpeg_quality: int = 68
    stream_annotated_jpeg_quality: int = 78
    # Min time between YOLO runs per camera (fair share under CPU load).
    detection_min_interval_ms: int = 85
    # MJPEG shows bounding boxes only while the annotated frame is this fresh (seconds).
    annotated_overlay_ttl_s: float = 0.45
    # Draw last-known boxes on live preview JPEGs (smooth FPS + visible detections).
    stream_overlay_detections_on_preview: bool = True

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    gemini_max_rpm: int = 10

    # Database
    database_path: str = "data/skyguard_v2.db"

    # Drones
    drone_speed_ms: float = 15.0
    drone_min_battery: int = 20
    drone_hover_time_s: int = 30

    # Priority Queue
    reallocation_interval_ms: int = 500
    severity_decay: float = 0.995
    reallocation_threshold: float = 0.15

    # Baseline
    baseline_severity_threshold: float = 0.4

    # SOS
    sos_buffer_seconds: int = 30
    sos_auto_severity: float = 0.90

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    # Windows (run_server.py): stop stale LISTENING process on api_port before bind
    skyguard_free_listen_port: bool = True

    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/backend.log"

    @field_validator("skyguard_free_listen_port", mode="before")
    @classmethod
    def coerce_free_listen_port(cls, v):
        if v is None:
            return True
        if isinstance(v, bool):
            return v
        s = str(v).strip().lower()
        return s in ("1", "true", "yes", "on")

    @field_validator("camera_fps_target", mode="before")
    @classmethod
    def clamp_camera_fps(cls, v):
        if v is None:
            return 25
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 25
        return max(1, min(n, 60))

    @field_validator("stream_min_fps", mode="before")
    @classmethod
    def clamp_stream_min_fps(cls, v):
        if v is None:
            return 25
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 25
        return max(15, min(n, 60))

    @property
    def effective_stream_fps(self) -> int:
        """Streams and detection scheduler aim for at least stream_min_fps (default 25)."""
        return max(self.camera_fps_target, self.stream_min_fps)

    @property
    def detection_min_interval_s(self) -> float:
        return max(0.05, self.detection_min_interval_ms / 1000.0)

    @field_validator("yolo_imgsz", mode="before")
    @classmethod
    def clamp_imgsz(cls, v):
        if v is None:
            return 320
        try:
            n = int(v)
        except (TypeError, ValueError):
            return 320
        allowed = {320, 384, 416, 480, 512, 640}
        if n in allowed:
            return n
        return min(allowed, key=lambda x: abs(x - n))


settings = Settings()
