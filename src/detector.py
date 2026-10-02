"""
YOLO Vehicle Detector Module.
Handles YOLO model loading, inference, confidence/IoU thresholding,
and traffic class filtering.
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from ultralytics import YOLO

from src.utils import COCO_CLASS_MAP, get_device


@dataclass
class Detection:
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    class_id: int
    class_name: str
    confidence: float
    center: Tuple[int, int]         # (cx, cy)


class VehicleDetector:
    """
    Wraps Ultralytics YOLOv8 for vehicle and pedestrian detection in traffic scenes.
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence: float = 0.40,
        iou: float = 0.50,
        device: str = "auto",
        target_classes: Optional[List[int]] = None,
    ):
        self.model_name = model_name
        self.confidence = float(confidence)
        self.iou = float(iou)
        self.device = get_device(device)
        self.target_classes = target_classes if target_classes is not None else [0, 1, 2, 3, 5, 7]

        # Load YOLO model
        try:
            self.model = YOLO(self.model_name)
        except Exception as e:
            # Fallback to standard yolov8n if custom path fails
            print(f"[Detector] Warning: Could not load '{self.model_name}' ({e}). Falling back to 'yolov8n.pt'")
            self.model = YOLO("yolov8n.pt")

    def update_thresholds(self, confidence: Optional[float] = None, iou: Optional[float] = None) -> None:
        """Update detection thresholds dynamically from UI."""
        if confidence is not None:
            self.confidence = float(confidence)
        if iou is not None:
            self.iou = float(iou)

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run inference on a single BGR video frame.
        Returns list of Detection objects filtered by target traffic classes.
        """
        if frame is None or frame.size == 0:
            return []

        results = self.model.predict(
            source=frame,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            classes=self.target_classes,
            verbose=False,
        )

        detections: List[Detection] = []
        if not results or len(results) == 0:
            return detections

        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return detections

        boxes_xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy().astype(int)

        for box, conf, cls_id in zip(boxes_xyxy, confs, classes):
            x1, y1, x2, y2 = map(int, box)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)
            class_name = COCO_CLASS_MAP.get(int(cls_id), self.model.names.get(int(cls_id), f"class_{cls_id}"))

            # Normalize common names
            if class_name in ("motorcycle", "motorbike"):
                class_name = "motorcycle"
            elif class_name in ("bicycle", "bike"):
                class_name = "bicycle"

            detections.append(
                Detection(
                    box=(x1, y1, x2, y2),
                    class_id=int(cls_id),
                    class_name=class_name,
                    confidence=float(conf),
                    center=(cx, cy),
                )
            )

        return detections
