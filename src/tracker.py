"""
Multi-Object Vehicle Tracker Module.
Uses ByteTrack via Ultralytics YOLO tracking engine with persistent centroid
history management and trajectory analysis.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple, Optional
from collections import deque
from dataclasses import dataclass, field
import numpy as np
from ultralytics import YOLO

from src.utils import COCO_CLASS_MAP, get_device, point_distance


@dataclass
class TrackedVehicle:
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    box: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    center: Tuple[int, int]         # (cx, cy)
    history: List[Tuple[int, int]] = field(default_factory=list)
    speed_px: float = 0.0          # Average movement in pixels/frame
    frames_tracked: int = 1


class VehicleTracker:
    """
    Tracks vehicles across video frames, maintaining persistent IDs and motion trails.
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        confidence: float = 0.40,
        iou: float = 0.50,
        tracker_type: str = "bytetrack.yaml",
        history_len: int = 30,
        device: str = "auto",
        target_classes: Optional[List[int]] = None,
    ):
        self.model_name = model_name
        self.confidence = float(confidence)
        self.iou = float(iou)
        self.tracker_type = tracker_type
        self.history_len = int(history_len)
        self.device = get_device(device)
        self.target_classes = target_classes if target_classes is not None else [0, 1, 2, 3, 5, 7]

        # Centroid history per track ID: {track_id: deque([(cx, cy), ...], maxlen=history_len)}
        self.track_history: Dict[int, deque] = {}
        # Tracking duration per track ID: {track_id: frames_tracked}
        self.track_durations: Dict[int, int] = {}

        try:
            self.model = YOLO(self.model_name)
        except Exception as e:
            print(f"[Tracker] Warning: Could not load '{self.model_name}' ({e}). Falling back to 'yolov8n.pt'")
            self.model = YOLO("yolov8n.pt")

    def update_settings(self, confidence: Optional[float] = None, iou: Optional[float] = None) -> None:
        """Update tracker thresholds dynamically."""
        if confidence is not None:
            self.confidence = float(confidence)
        if iou is not None:
            self.iou = float(iou)

    def reset(self) -> None:
        """Reset all tracking states."""
        self.track_history.clear()
        self.track_durations.clear()

    def track(self, frame: np.ndarray) -> List[TrackedVehicle]:
        """
        Execute tracking on a frame and return active tracked vehicles with histories.
        """
        if frame is None or frame.size == 0:
            return []

        results = self.model.track(
            source=frame,
            conf=self.confidence,
            iou=self.iou,
            device=self.device,
            classes=self.target_classes,
            tracker=self.tracker_type,
            persist=True,
            verbose=False,
        )

        tracked_objects: List[TrackedVehicle] = []
        if not results or len(results) == 0:
            return tracked_objects

        r = results[0]
        if r.boxes is None or len(r.boxes) == 0:
            return tracked_objects

        boxes_xyxy = r.boxes.xyxy.cpu().numpy()
        confs = r.boxes.conf.cpu().numpy()
        classes = r.boxes.cls.cpu().numpy().astype(int)
        track_ids = r.boxes.id.cpu().numpy().astype(int) if r.boxes.id is not None else None

        active_current_ids = set()

        for idx, (box, conf, cls_id) in enumerate(zip(boxes_xyxy, confs, classes)):
            x1, y1, x2, y2 = map(int, box)
            cx = int((x1 + x2) / 2)
            cy = int((y1 + y2) / 2)

            # Assign valid track ID; fallback to synthetic ID if tracker unassigned
            if track_ids is not None and idx < len(track_ids):
                track_id = int(track_ids[idx])
            else:
                track_id = 1000 + idx

            active_current_ids.add(track_id)

            # Update deque history
            if track_id not in self.track_history:
                self.track_history[track_id] = deque(maxlen=self.history_len)
                self.track_durations[track_id] = 1
            else:
                self.track_durations[track_id] = self.track_durations.get(track_id, 0) + 1

            self.track_history[track_id].append((cx, cy))
            hist_list = list(self.track_history[track_id])

            # Calculate average pixel movement across recent frames
            speed_px = 0.0
            if len(hist_list) >= 2:
                recent_points = hist_list[-5:]
                distances = [point_distance(recent_points[i], recent_points[i + 1]) for i in range(len(recent_points) - 1)]
                speed_px = float(np.mean(distances)) if distances else 0.0

            class_name = COCO_CLASS_MAP.get(int(cls_id), self.model.names.get(int(cls_id), f"class_{cls_id}"))
            if class_name in ("motorcycle", "motorbike"):
                class_name = "motorcycle"
            elif class_name in ("bicycle", "bike"):
                class_name = "bicycle"

            tracked_objects.append(
                TrackedVehicle(
                    track_id=track_id,
                    class_id=int(cls_id),
                    class_name=class_name,
                    confidence=float(conf),
                    box=(x1, y1, x2, y2),
                    center=(cx, cy),
                    history=hist_list,
                    speed_px=speed_px,
                    frames_tracked=self.track_durations[track_id],
                )
            )

        # Cleanup tracks that haven't been seen for a long time to prevent memory leakage
        if len(self.track_history) > 500:
            for old_id in list(self.track_history.keys()):
                if old_id not in active_current_ids:
                    del self.track_history[old_id]
                    if old_id in self.track_durations:
                        del self.track_durations[old_id]

        return tracked_objects
