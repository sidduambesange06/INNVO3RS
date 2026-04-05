"""SkyGuard V2 — Video Feed Camera Handler.

Loops an MP4 video file as a simulated camera feed.
If the MP4 doesn't exist, generates a synthetic test video.
"""

import cv2
import numpy as np
import threading
import time
import os
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def generate_test_video(path: str, zone_name: str, duration_s: int = 60,
                        width: int = 640, height: int = 360, fps: int = 25) -> None:
    """Generate a synthetic colored test video with zone name overlay."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, (width, height))

    # Zone-specific color
    colors = {
        "Zone-B": (120, 60, 30), "Zone-C": (30, 80, 60), "Zone-D": (50, 30, 90),
        "Zone-E": (30, 70, 80), "Zone-F": (70, 40, 50), "Zone-G": (40, 60, 70),
        "Zone-H": (60, 50, 40),
    }
    bg_color = colors.get(zone_name, (40, 40, 40))

    total_frames = duration_s * fps
    for f_idx in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = bg_color

        # Grid
        for i in range(0, width, 80):
            cv2.line(frame, (i, 0), (i, height), (bg_color[0]+20, bg_color[1]+20, bg_color[2]+20), 1)
        for j in range(0, height, 60):
            cv2.line(frame, (0, j), (width, j), (bg_color[0]+20, bg_color[1]+20, bg_color[2]+20), 1)

        # Zone name
        cv2.putText(frame, f"SKYGUARD - {zone_name}", (120, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        # Simulated people
        t = f_idx / fps
        for i in range(4):
            x = int((80 + i * 130 + t * 25 * (i + 1)) % (width - 40))
            y = int(100 + i * 50 + 25 * np.sin(t * 1.5 + i * 0.8))
            cv2.rectangle(frame, (x, y), (x + 35, y + 75), (0, 200, 255), 2)
            cv2.putText(frame, "person", (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 200, 255), 1)

        # Timestamp
        ts_text = f"T+{int(t)}s"
        cv2.putText(frame, ts_text, (width - 80, height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        out.write(frame)

    out.release()
    logger.info(f"Generated test video: {path} ({duration_s}s, {total_frames} frames)")


class VideoFeedCamera:
    """Loops an MP4 video file as a simulated camera feed."""

    def __init__(self, video_path: str, cam_id: str, zone_id: str,
                 width: int = 640, height: int = 360, fps: int = 25):
        self.video_path = video_path
        self.cam_id = cam_id
        self.zone_id = zone_id
        self.width = width
        self.height = height
        self.target_fps = fps

        self._cap: Optional[cv2.VideoCapture] = None
        self._frame: Optional[np.ndarray] = None
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._fps = 0.0
        self._frame_count = 0
        self._fps_start = 0.0
        self._last_frame_time = 0.0

    def connect(self) -> bool:
        """Open video file. Generate test video if it doesn't exist."""
        if not os.path.exists(self.video_path):
            logger.info(f"{self.cam_id}: Video not found, generating synthetic: {self.video_path}")
            generate_test_video(self.video_path, self.zone_id)

        self._cap = cv2.VideoCapture(self.video_path)
        if self._cap.isOpened():
            self._connected = True
            self._running = True
            self._fps_start = time.time()
            self._thread = threading.Thread(target=self._loop, daemon=True)
            self._thread.start()
            logger.info(f"✅ {self.cam_id} video feed connected: {self.video_path}")
            return True
        else:
            logger.error(f"{self.cam_id}: Failed to open video: {self.video_path}")
            return False

    def _loop(self):
        frame_interval = 1.0 / self.target_fps
        while self._running:
            start_time = time.time()
            try:
                if self._cap and self._cap.isOpened():
                    ret, frame = self._cap.read()
                    if not ret:
                        # Loop video
                        self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = self._cap.read()
                        if not ret:
                            time.sleep(0.1)
                            continue

                    resized = cv2.resize(frame, (self.width, self.height))
                    with self._lock:
                        self._frame = resized
                        self._last_frame_time = time.time()

                    self._frame_count += 1
                    elapsed = time.time() - self._fps_start
                    if elapsed >= 1.0:
                        self._fps = self._frame_count / elapsed
                        self._frame_count = 0
                        self._fps_start = time.time()
            except Exception as e:
                logger.error(f"{self.cam_id} video error: {e}")

            # Maintain consistent frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def is_connected(self) -> bool:
        return self._connected and self._last_frame_time > 0 and (time.time() - self._last_frame_time) < 5.0

    def get_fps(self) -> float:
        return round(self._fps, 1)

    def disconnect(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        self._connected = False

    def get_status(self) -> dict:
        return {
            "cam_id": self.cam_id,
            "zone_id": self.zone_id,
            "type": "video_feed",
            "status": "connected" if self.is_connected() else "disconnected",
            "fps": self.get_fps(),
            "resolution": f"{self.width}x{self.height}",
        }
