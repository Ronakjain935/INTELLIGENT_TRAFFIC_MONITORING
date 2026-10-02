"""
Utility functions and helpers for AI Intelligent Traffic Monitoring System.
Includes configuration loading, device detection, geometric crossing logic,
and OpenCV rendering utilities.
"""

from __future__ import annotations

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import cv2
import torch


# Default configuration fallback
DEFAULT_CONFIG: Dict[str, Any] = {
    "model": {
        "name": "yolov8n.pt",
        "confidence": 0.40,
        "iou": 0.50,
        "device": "auto",
        "target_classes": [0, 1, 2, 3, 5, 7],
    },
    "tracking": {
        "tracker_type": "bytetrack.yaml",
        "track_history_len": 30,
        "track_retention_frames": 60,
    },
    "counting": {
        "line_ratio_y": 0.55,
        "line_offset": 12,
        "cooldown_frames": 15,
    },
    "traffic": {
        "expected_direction": "RIGHT",
    },
    "density": {
        "low": 20,
        "medium": 50,
    },
    "congestion": {
        "speed_threshold_px": 4.0,
        "speed_history_window": 10,
    },
    "wrong_way": {
        "enabled": True,
        "minimum_movement_pixels": 15,
        "confirmation_frames": 5,
        "warning_display_seconds": 3.0,
    },
    "processing": {
        "frame_skip": 1,
        "resize_width": 1280,
        "show_trails": True,
        "show_boxes": True,
        "show_counting_line": True,
    },
    "storage": {
        "database_path": "data/traffic_system.db",
        "database_url": "sqlite:///data/traffic_system.db",
        "reports_dir": "data/reports",
        "output_video_dir": "data/output",
        "sample_videos_dir": "data/input",
    },
}

# Standard COCO class names for traffic objects
COCO_CLASS_MAP = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

# Color palette in BGR for visual rendering
CLASS_COLORS = {
    "car": (46, 204, 113),         # Emerald Green
    "motorcycle": (255, 191, 0),   # Deep Sky Blue
    "bus": (241, 196, 15),         # Sunflower Yellow
    "truck": (230, 126, 34),       # Carrot Orange
    "bicycle": (155, 89, 182),     # Amethyst Purple
    "person": (52, 152, 219),      # River Blue
    "wrong_way": (0, 0, 230),      # Bright Crimson Red
    "default": (189, 195, 199),    # Silver Gray
}


def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Safely load system configuration from YAML file, overlaid with environment variables from .env.
    Falls back gracefully to DEFAULT_CONFIG if file is missing or invalid.
    """
    # 1. Native zero-dependency .env loader (prevents missing-import linter warnings)
    env_file = Path(".env")
    if env_file.is_file():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    k, v = key.strip(), val.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass

    # 2. Also invoke python-dotenv dynamically if present in the environment
    try:
        import importlib
        dotenv_mod = importlib.import_module("dotenv")
        if hasattr(dotenv_mod, "load_dotenv"):
            dotenv_mod.load_dotenv(override=False)
    except Exception:
        pass

    path = Path(config_path)
    merged = DEFAULT_CONFIG.copy()
    if path.is_file():
        try:
            with open(path, "r", encoding="utf-8") as f:
                user_config = yaml.safe_load(f)
                if isinstance(user_config, dict):
                    for key, val in user_config.items():
                        if isinstance(val, dict) and key in merged and isinstance(merged[key], dict):
                            merged[key] = {**merged[key], **val}
                        else:
                            merged[key] = val
        except Exception:
            pass

    # Overlay environment variables from .env if present
    if os.getenv("MODEL_NAME"):
        merged.setdefault("model", {})["name"] = os.getenv("MODEL_NAME")
    if os.getenv("MODEL_CONFIDENCE"):
        try:
            merged.setdefault("model", {})["confidence"] = float(os.getenv("MODEL_CONFIDENCE"))
        except ValueError:
            pass
    if os.getenv("MODEL_IOU"):
        try:
            merged.setdefault("model", {})["iou"] = float(os.getenv("MODEL_IOU"))
        except ValueError:
            pass
    if os.getenv("MODEL_DEVICE"):
        merged.setdefault("model", {})["device"] = os.getenv("MODEL_DEVICE")

    if os.getenv("SQLITE_DB_PATH"):
        merged.setdefault("storage", {})["database_path"] = os.getenv("SQLITE_DB_PATH")
    if os.getenv("DATABASE_URL"):
        merged.setdefault("storage", {})["database_url"] = os.getenv("DATABASE_URL")
    if os.getenv("REPORTS_DIR"):
        merged.setdefault("storage", {})["reports_dir"] = os.getenv("REPORTS_DIR")
    if os.getenv("OUTPUT_VIDEO_DIR"):
        merged.setdefault("storage", {})["output_video_dir"] = os.getenv("OUTPUT_VIDEO_DIR")
    if os.getenv("SAMPLE_VIDEOS_DIR"):
        merged.setdefault("storage", {})["sample_videos_dir"] = os.getenv("SAMPLE_VIDEOS_DIR")

    return merged


def get_device(preference: str = "auto") -> str:
    """
    Determine whether to run on CUDA or CPU.
    """
    if preference == "cpu":
        return "cpu"
    if preference in ("cuda", "auto") and torch.cuda.is_available():
        return "cuda:0"
    return "cpu"


def lines_intersect(p1: Tuple[float, float], p2: Tuple[float, float],
                    p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
    """
    Check if line segment p1-p2 intersects line segment p3-p4.
    Used for virtual counting line crossings.
    """
    def ccw(A, B, C):
        return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

    return (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))


def point_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Euclidean distance between two 2D coordinates."""
    return float(np.hypot(p2[0] - p1[0], p2[1] - p1[1]))


def draw_header_badge(image: np.ndarray, text: str, pt: Tuple[int, int],
                      bg_color: Tuple[int, int, int], text_color: Tuple[int, int, int] = (255, 255, 255),
                      font_scale: float = 0.5, thickness: int = 1) -> None:
    """Draw a clean filled badge header above or inside a bounding box."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pt
    # Keep badge inside frame bounds
    x1 = max(0, x)
    y1 = max(text_h + 8, y)
    y0 = y1 - text_h - 6
    x2 = min(image.shape[1] - 1, x1 + text_w + 8)

    cv2.rectangle(image, (x1, y0), (x2, y1), bg_color, -1)
    cv2.putText(image, text, (x1 + 4, y1 - 4), font, font_scale, text_color, thickness, cv2.LINE_AA)
