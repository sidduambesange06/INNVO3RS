"""SkyGuard V2 — Camera Manager.

Orchestrates 8 cameras: 1 RTSP (CAM-01) + 7 video feeds (CAM-02 to CAM-08).
"""

from typing import Optional
import numpy as np
from app.core.camera_rtsp import RTSPCamera
from app.core.camera_video import VideoFeedCamera
from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class CameraManager:
    """Manages all 8 cameras."""

    def __init__(self):
        self.cameras: dict[str, RTSPCamera | VideoFeedCamera] = {}

    async def initialize_from_db(self, camera_rows: list[dict]) -> None:
        """Initialize cameras from database seed data."""
        for row in camera_rows:
            cam_id = row["cam_id"]
            zone_id = row.get("zone_id", "")
            source = row.get("source_url", "")
            cam_type = row.get("type", "video_feed")

            if cam_type == "rtsp":
                camera = RTSPCamera(
                    rtsp_url=settings.rtsp_url,
                    cam_id=cam_id,
                    zone_id=zone_id,
                    width=settings.camera_width,
                    height=settings.camera_height,
                    fps=settings.camera_fps_target,
                )
            else:
                camera = VideoFeedCamera(
                    video_path=source,
                    cam_id=cam_id,
                    zone_id=zone_id,
                    width=settings.camera_width,
                    height=settings.camera_height,
                    fps=settings.camera_fps_target,
                )

            camera.connect()
            self.cameras[cam_id] = camera

        logger.info(f"✅ CameraManager: {len(self.cameras)} cameras initialized")

    def get_frame(self, cam_id: str) -> Optional[np.ndarray]:
        camera = self.cameras.get(cam_id)
        if camera:
            return camera.get_frame()
        return None

    def get_camera(self, cam_id: str) -> Optional[RTSPCamera | VideoFeedCamera]:
        return self.cameras.get(cam_id)

    def get_all_statuses(self) -> list[dict]:
        return [cam.get_status() for cam in self.cameras.values()]

    def get_all_cam_ids(self) -> list[str]:
        return list(self.cameras.keys())

    def disconnect_all(self) -> None:
        for cam in self.cameras.values():
            cam.disconnect()
        logger.info("All cameras disconnected")
