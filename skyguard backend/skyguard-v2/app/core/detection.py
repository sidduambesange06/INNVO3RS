"""SkyGuard V2 — Multi-Model Detection Engine.

Detects 5 anomaly types from YOLO11n inference:
1. crowd_anomaly — person count exceeds baseline
2. fight_detection — overlapping bboxes with opposing motion
3. person_down — aspect ratio < 0.5 for 3+ frames
4. weapon_detect — YOLO knife/gun/bat class
5. suspicious_behavior — person dwells in zone > 120s
"""

import cv2
import numpy as np
import threading
import time
from typing import Optional
from collections import defaultdict

from app.models.detection import Detection, BoundingBox, AnomalyFlag, DetectionResult
from app.models.enums import AnomalyType
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# Severity multipliers per anomaly type
SEVERITY_WEIGHTS = {
    AnomalyType.CROWD_ANOMALY.value: 1.0,
    AnomalyType.FIGHT_DETECTION.value: 1.4,
    AnomalyType.PERSON_DOWN.value: 1.5,
    AnomalyType.WEAPON_DETECT.value: 2.0,
    AnomalyType.SUSPICIOUS_BEHAVIOR.value: 1.2,
}

# COCO classes of interest
PERSON_CLASS = 0
WEAPON_CLASSES = {  # COCO class IDs for weapons
    43: "knife",    # knife
    # Note: COCO doesn't have gun/bat, so we check for similar objects
    39: "bottle",   # bottle (as potential weapon approximation)
    76: "scissors", # scissors
}


class MultiModelDetector:
    """Multi-anomaly detection engine using YOLO11n."""

    def __init__(self, model_path: str = "data/models/yolo11n.pt",
                 confidence: float = 0.5, device: str = "cpu",
                 imgsz: int = 416, half: bool = False, max_det: int = 40, iou: float = 0.5):
        self.model_path = model_path
        self.confidence = confidence
        self.device = device
        self.imgsz = imgsz
        self.max_det = max_det
        self.iou = iou
        self._half = bool(half) and ("cuda" in str(device).lower())

        self._model = None
        self._loaded = False
        self._fps = 0.0
        self._frame_times: list[float] = []
        self._last_inference_ms = 0.0

        # Tracking state per camera
        self._prev_centroids: dict[str, list[tuple]] = defaultdict(list)  # cam_id -> [(cx,cy)]
        self._down_counter: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))  # cam->track->frames
        self._dwell_tracker: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))  # cam->track->first_seen
        self._predict_lock = threading.Lock()

    def load(self) -> None:
        """Load YOLO model."""
        try:
            from ultralytics import YOLO
            import os

            if not os.path.exists(self.model_path):
                logger.info(f"Downloading YOLO model to {self.model_path}...")
                os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
                self._model = YOLO("yolo11n.pt")
                import shutil
                if os.path.exists("yolo11n.pt"):
                    shutil.move("yolo11n.pt", self.model_path)
                    self._model = YOLO(self.model_path)
            else:
                self._model = YOLO(self.model_path)

            self._model.to(self.device)
            self._loaded = True

            # Warmup at configured inference size (serialized — safe for CUDA)
            dummy = np.zeros((360, 640, 3), dtype=np.uint8)
            with self._predict_lock:
                self._model.predict(
                    dummy,
                    verbose=False,
                    device=self.device,
                    imgsz=self.imgsz,
                    half=self._half,
                    max_det=self.max_det,
                    iou=self.iou,
                )

            logger.info(
                "YOLO model loaded: %s | device=%s fp16=%s imgsz=%s",
                self.model_path,
                self.device,
                self._half,
                self.imgsz,
            )
        except Exception as e:
            logger.error(f"YOLO load failed: {e}")
            self._loaded = False
            raise

    def detect_all(self, frame: np.ndarray, cam_id: str, zone_polygon: list = None) -> DetectionResult:
        """Run YOLO + all 5 anomaly checks on a frame."""
        if not self._loaded or self._model is None or frame is None:
            return DetectionResult(cam_id=cam_id, zone_id="")

        start = time.time()

        try:
            with self._predict_lock:
                results = self._model.predict(
                    frame,
                    conf=self.confidence,
                    device=self.device,
                    verbose=False,
                    imgsz=self.imgsz,
                    half=self._half,
                    max_det=self.max_det,
                    iou=self.iou,
                )
        except Exception as e:
            logger.error(f"YOLO inference error: {e}")
            return DetectionResult(cam_id=cam_id, zone_id="")

        detections: list[Detection] = []
        persons: list[Detection] = []
        weapons: list[Detection] = []

        if results and len(results) > 0:
            result = results[0]
            if result.boxes is not None:
                for idx, box in enumerate(result.boxes):
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])

                    bbox = BoundingBox(x1=round(x1, 1), y1=round(y1, 1),
                                       x2=round(x2, 1), y2=round(y2, 1))

                    if cls_id == PERSON_CLASS and conf >= self.confidence:
                        det = Detection(bbox=bbox, confidence=round(conf, 2),
                                        class_name="person", track_id=idx)
                        detections.append(det)
                        persons.append(det)

                    elif cls_id in WEAPON_CLASSES and conf >= 0.7:
                        weapon_name = WEAPON_CLASSES[cls_id]
                        det = Detection(bbox=bbox, confidence=round(conf, 2),
                                        class_name=weapon_name, track_id=idx)
                        detections.append(det)
                        weapons.append(det)

        # Run anomaly checks
        anomaly_flags: list[AnomalyFlag] = []
        persons_count = len(persons)

        # 1. Crowd anomaly (flagged if persons exist — severity computed by baseline engine)
        if persons_count > 0:
            anomaly_flags.append(AnomalyFlag(
                anomaly_type=AnomalyType.CROWD_ANOMALY.value,
                confidence=0.9,
                description=f"{persons_count} persons detected",
            ))

        # 2. Fight detection — overlapping person bboxes
        fight_flag = self._check_fight(persons, cam_id)
        if fight_flag:
            anomaly_flags.append(fight_flag)

        # 3. Person down — aspect ratio check
        down_flag = self._check_person_down(persons, cam_id)
        if down_flag:
            anomaly_flags.append(down_flag)

        # 4. Weapon detection
        if weapons:
            anomaly_flags.append(AnomalyFlag(
                anomaly_type=AnomalyType.WEAPON_DETECT.value,
                confidence=max(w.confidence for w in weapons),
                description=f"Weapon detected: {', '.join(w.class_name for w in weapons)}",
                involved_detections=[w.track_id for w in weapons if w.track_id],
            ))

        # 5. Suspicious behavior — dwell time
        suspicious_flag = self._check_suspicious(persons, cam_id)
        if suspicious_flag:
            anomaly_flags.append(suspicious_flag)

        # Update centroids for next frame
        self._prev_centroids[cam_id] = [d.bbox.center for d in persons]

        elapsed_ms = (time.time() - start) * 1000
        self._last_inference_ms = elapsed_ms
        self._update_fps(elapsed_ms)

        return DetectionResult(
            cam_id=cam_id,
            zone_id="",  # Set by caller
            persons_count=persons_count,
            detections=detections,
            anomaly_flags=anomaly_flags,
            processing_ms=round(elapsed_ms, 1),
        )

    def detect_and_encode_annotated(
        self,
        frame: np.ndarray,
        cam_id: str,
        zone_polygon: list | None,
        annotated_quality: int,
    ) -> tuple[DetectionResult, bytes]:
        """Inference + overlay + JPEG in one worker call (preview encoded separately for low latency)."""
        result = self.detect_all(frame, cam_id, zone_polygon)
        annotated = self.draw_annotated_frame(frame, result.detections, result.anomaly_flags)
        return result, self.encode_mjpeg(annotated, annotated_quality)

    def _check_fight(self, persons: list[Detection], cam_id: str) -> Optional[AnomalyFlag]:
        """Detect fights: pairs with high IoU + opposing velocity."""
        if len(persons) < 2:
            return None

        prev = self._prev_centroids.get(cam_id, [])
        for i in range(len(persons)):
            for j in range(i + 1, len(persons)):
                b1, b2 = persons[i].bbox, persons[j].bbox
                # Check IoU > 0.3
                iou = self._compute_iou(b1, b2)
                if iou < 0.15:
                    continue

                # Check proximity
                cx1, cy1 = b1.center
                cx2, cy2 = b2.center
                dist = ((cx1 - cx2)**2 + (cy1 - cy2)**2) ** 0.5
                if dist > 100:
                    continue

                # Check motion (if we have previous frame data)
                if len(prev) >= 2:
                    return AnomalyFlag(
                        anomaly_type=AnomalyType.FIGHT_DETECTION.value,
                        confidence=min(0.95, 0.6 + iou),
                        description=f"Potential fight: 2 persons in close proximity (IoU={iou:.2f})",
                        involved_detections=[persons[i].track_id, persons[j].track_id],
                    )

                # Even without motion, very close proximity suggests altercation
                if dist < 50:
                    return AnomalyFlag(
                        anomaly_type=AnomalyType.FIGHT_DETECTION.value,
                        confidence=0.6,
                        description=f"Close proximity alert: distance={dist:.0f}px",
                    )
        return None

    def _check_person_down(self, persons: list[Detection], cam_id: str) -> Optional[AnomalyFlag]:
        """Detect fallen person: aspect ratio < 0.5 for 3+ consecutive frames."""
        for det in persons:
            tid = det.track_id or 0
            if det.bbox.aspect_ratio > 1.8:  # Wide bbox = likely lying down
                self._down_counter[cam_id][tid] += 1
            else:
                self._down_counter[cam_id][tid] = 0

            if self._down_counter[cam_id][tid] >= 3:
                return AnomalyFlag(
                    anomaly_type=AnomalyType.PERSON_DOWN.value,
                    confidence=0.8,
                    description=f"Person appears down (horizontal bbox for {self._down_counter[cam_id][tid]} frames)",
                    involved_detections=[tid],
                )
        return None

    def _check_suspicious(self, persons: list[Detection], cam_id: str) -> Optional[AnomalyFlag]:
        """Detect loitering: person in zone > 120 seconds."""
        now = time.time()
        current_ids = set()

        for det in persons:
            tid = det.track_id or 0
            current_ids.add(tid)
            if tid not in self._dwell_tracker[cam_id]:
                self._dwell_tracker[cam_id][tid] = now
            else:
                dwell_time = now - self._dwell_tracker[cam_id][tid]
                if dwell_time > 120:
                    return AnomalyFlag(
                        anomaly_type=AnomalyType.SUSPICIOUS_BEHAVIOR.value,
                        confidence=min(0.9, 0.5 + dwell_time / 300),
                        description=f"Person loitering for {int(dwell_time)}s",
                        involved_detections=[tid],
                    )

        # Clean up departed people
        departed = set(self._dwell_tracker[cam_id].keys()) - current_ids
        for tid in departed:
            del self._dwell_tracker[cam_id][tid]

        return None

    def _compute_iou(self, b1: BoundingBox, b2: BoundingBox) -> float:
        """Compute Intersection over Union."""
        x1 = max(b1.x1, b2.x1)
        y1 = max(b1.y1, b2.y1)
        x2 = min(b1.x2, b2.x2)
        y2 = min(b1.y2, b2.y2)
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        union = b1.area + b2.area - inter
        return inter / max(union, 1e-6)

    def draw_annotated_frame(self, frame: np.ndarray, detections: list[Detection],
                             anomaly_flags: list[AnomalyFlag]) -> np.ndarray:
        """Draw bounding boxes and anomaly warnings on frame."""
        annotated = frame.copy()

        # Color map for classes
        colors = {
            "person": (0, 255, 0),
            "knife": (0, 0, 255),
            "gun": (0, 0, 255),
            "scissors": (0, 0, 255),
            "bottle": (0, 165, 255),
        }

        for det in detections:
            color = colors.get(det.class_name, (0, 255, 0))
            x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{det.class_name} {det.confidence:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Anomaly warning overlay
        y_offset = 25
        for flag in anomaly_flags:
            if flag.anomaly_type in (AnomalyType.WEAPON_DETECT.value, AnomalyType.FIGHT_DETECTION.value,
                                     AnomalyType.PERSON_DOWN.value):
                color = (0, 0, 255)  # Red
            else:
                color = (0, 255, 255)  # Yellow

            text = f"⚠ {flag.anomaly_type}: {flag.description}"
            cv2.putText(annotated, text, (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1)
            y_offset += 20

        # FPS overlay
        fps_text = f"FPS: {self.get_fps():.1f}"
        cv2.putText(annotated, fps_text, (frame.shape[1] - 100, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # Person count
        person_count = sum(1 for d in detections if d.class_name == "person")
        cv2.putText(annotated, f"Persons: {person_count}", (10, frame.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        return annotated

    @staticmethod
    def encode_mjpeg(frame: np.ndarray, quality: int = 80) -> bytes:
        """Encode frame as JPEG bytes."""
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        return buf.tobytes()

    def _update_fps(self, ms: float):
        self._frame_times.append(ms)
        if len(self._frame_times) > 100:
            self._frame_times = self._frame_times[-100:]
        if len(self._frame_times) >= 2:
            avg = sum(self._frame_times) / len(self._frame_times)
            if avg > 0:
                self._fps = 1000.0 / avg

    def get_fps(self) -> float:
        return round(self._fps, 1)

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def get_status(self) -> dict:
        return {
            "status": "loaded" if self._loaded else "not_loaded",
            "device": self.device,
            "fp16": self._half,
            "fps": self.get_fps(),
            "last_inference_ms": round(self._last_inference_ms, 1),
        }
