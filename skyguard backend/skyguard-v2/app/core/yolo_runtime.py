"""Resolve YOLO device (GPU vs CPU) from settings."""

from __future__ import annotations

from app.config import settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def resolve_yolo_device_and_half() -> tuple[str, bool]:
    """
    Returns (device_string, use_fp16).

    YOLO_DEVICE / yolo_device:
      - auto | detect | ''  -> cuda:0 if torch.cuda.is_available() else cpu
      - gpu                  -> cuda:0
      - cuda | cuda:0        -> as given if CUDA available
      - cpu                  -> cpu (no FP16)
    FP16 is only enabled when device is CUDA and yolo_half is True.
    """
    raw = (settings.yolo_device or "auto").strip().lower()
    want_half = bool(settings.yolo_half)

    def try_cuda(dev: str) -> tuple[str, bool] | None:
        try:
            import torch
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                logger.info("YOLO using GPU: %s (%s)", dev, name)
                return dev, want_half
        except Exception as e:
            logger.warning("YOLO CUDA check failed: %s", e)
        return None

    if raw in ("auto", "detect", ""):
        got = try_cuda("cuda:0")
        if got:
            return got
        logger.info("YOLO using CPU (no CUDA device available)")
        return "cpu", False

    if raw == "gpu":
        got = try_cuda("cuda:0")
        if got:
            return got
        logger.warning("YOLO_DEVICE=gpu but CUDA unavailable; falling back to CPU")
        return "cpu", False

    if raw.startswith("cuda"):
        dev = raw if ":" in raw else "cuda:0"
        got = try_cuda(dev)
        if got:
            return got
        logger.warning("CUDA requested (%s) but unavailable; falling back to CPU", raw)
        return "cpu", False

    logger.info("YOLO using device: %s", raw)
    return raw, False
