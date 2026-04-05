"""SkyGuard V2 — RTSP Camera Handler."""

import cv2
import numpy as np
import threading
import time
from typing import Optional
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RTSPCamera:
    """RTSP camera handler with auto-reconnect and thread-safe frame buffer."""

    def __init__(self, rtsp_url: str, cam_id: str, zone_id: str,
                 width: int = 640, height: int = 360, fps: int = 25):
        self.rtsp_url = rtsp_url
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
        """Connect to RTSP with 5x exponential backoff retry."""
        for attempt in range(1, 6):
            try:
                self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
                # Optimize for real-time streaming
                self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimal buffer for low latency
                self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
                if self._cap.isOpened():
                    ret, frame = self._cap.read()
                    if ret and frame is not None:
                        self._connected = True
                        self._start_thread()
                        logger.info(f"✅ {self.cam_id} RTSP connected (attempt {attempt})")
                        return True
                logger.warning(f"{self.cam_id} RTSP attempt {attempt}/5 failed")
            except Exception as e:
                logger.error(f"{self.cam_id} RTSP error: {e}")
            if self._cap:
                self._cap.release()
            time.sleep(2 ** (attempt - 1))

        # Fallback to webcam
        return self._try_webcam()

    def _try_webcam(self) -> bool:
        try:
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                ret, _ = self._cap.read()
                if ret:
                    self._connected = True
                    self._start_thread()
                    logger.info(f"✅ {self.cam_id} webcam fallback connected")
                    return True
        except Exception:
            pass
        logger.warning(f"{self.cam_id} no camera available, using synthetic frames")
        self._connected = True
        self._start_thread()
        return True

    def _start_thread(self):
        self._running = True
        self._fps_start = time.time()
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        frame_interval = 1.0 / self.target_fps
        while self._running:
            start_time = time.time()
            try:
                if self._cap and self._cap.isOpened():
                    ret, frame = self._cap.read()
                    if ret and frame is not None:
                        resized = cv2.resize(frame, (self.width, self.height))
                        with self._lock:
                            self._frame = resized
                            self._last_frame_time = time.time()
                        self._update_fps()
                    else:
                        self._reconnect()
                else:
                    self._generate_synthetic()
            except Exception as e:
                logger.error(f"{self.cam_id} capture error: {e}")
                time.sleep(1.0)
            
            # Maintain consistent frame rate
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _reconnect(self):
        if self._cap:
            self._cap.release()
        try:
            self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            self._cap.set(cv2.CAP_PROP_FPS, self.target_fps)
            if self._cap.isOpened():
                logger.info(f"{self.cam_id} reconnected")
        except Exception:
            time.sleep(2.0)

    def _generate_synthetic(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        frame[:] = (40, 30, 20)
        cv2.putText(frame, f"SKYGUARD {self.cam_id}", (150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(frame, time.strftime("%H:%M:%S"), (self.width - 110, self.height - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        t = time.time()
        for i in range(3):
            x = int((100 + i * 150 + t * 20 * (i + 1)) % (self.width - 40))
            y = int(120 + i * 50 + 20 * np.sin(t * 2 + i))
            cv2.rectangle(frame, (x, y), (x + 30, y + 70), (0, 200, 255), 2)
        with self._lock:
            self._frame = frame
            self._last_frame_time = time.time()
        self._update_fps()

    def _update_fps(self):
        self._frame_count += 1
        elapsed = time.time() - self._fps_start
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._fps_start = time.time()

    def get_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def is_connected(self) -> bool:
        if not self._connected:
            return False
        return self._last_frame_time > 0 and (time.time() - self._last_frame_time) < 5.0

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
            "type": "rtsp",
            "status": "connected" if self.is_connected() else "disconnected",
            "fps": self.get_fps(),
            "resolution": f"{self.width}x{self.height}",
        }
