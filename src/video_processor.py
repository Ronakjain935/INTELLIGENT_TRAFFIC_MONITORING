"""
Video Processing Pipeline Module.
Coordinates YOLO detection, ByteTrack tracking, counting line events,
wrong-way detection, traffic analysis, and visual HUD overlays.
"""

from __future__ import annotations

import time
from typing import Generator, Dict, Any, Tuple, Optional
import cv2
import numpy as np

from src.tracker import VehicleTracker, TrackedVehicle
from src.counter import VehicleCounter, CrossingEvent
from src.wrong_way_detector import DirectionAndWrongWayDetector, WrongWayViolation
from src.traffic_analyzer import TrafficAnalyzer, TrafficState
from src.database import DatabaseManager
from src.utils import CLASS_COLORS, draw_header_badge


class VideoProcessor:
    """
    Core video stream orchestrator integrating all AI vision and analytics modules.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        db_manager: Optional[DatabaseManager] = None,
    ):
        self.config = config
        self.db = db_manager or DatabaseManager(config.get("storage", {}).get("database_path", "data/traffic_system.db"))

        model_cfg = config.get("model", {})
        track_cfg = config.get("tracking", {})
        count_cfg = config.get("counting", {})
        wrong_cfg = config.get("wrong_way", {})
        dens_cfg = config.get("density", {})
        cong_cfg = config.get("congestion", {})
        proc_cfg = config.get("processing", {})

        # 1. Initialize Tracker (which uses YOLO model)
        self.tracker = VehicleTracker(
            model_name=model_cfg.get("name", "yolov8n.pt"),
            confidence=model_cfg.get("confidence", 0.40),
            iou=model_cfg.get("iou", 0.50),
            tracker_type=track_cfg.get("tracker_type", "bytetrack.yaml"),
            history_len=track_cfg.get("track_history_len", 30),
            device=model_cfg.get("device", "auto"),
            target_classes=model_cfg.get("target_classes", [0, 1, 2, 3, 5, 7]),
        )

        # 2. Initialize Counter
        self.counter = VehicleCounter(
            line_ratio_y=count_cfg.get("line_ratio_y", 0.55),
            line_offset=count_cfg.get("line_offset", 12),
        )

        # 3. Initialize Wrong-Way & Direction Detector
        self.wrong_way_detector = DirectionAndWrongWayDetector(
            expected_direction=config.get("traffic", {}).get("expected_direction", "RIGHT"),
            min_movement_pixels=wrong_cfg.get("minimum_movement_pixels", 15.0),
            confirmation_frames=wrong_cfg.get("confirmation_frames", 5),
            enabled=wrong_cfg.get("enabled", True),
        )

        # 4. Initialize Traffic Analyzer
        self.traffic_analyzer = TrafficAnalyzer(
            low_density_threshold=dens_cfg.get("low", 20),
            medium_density_threshold=dens_cfg.get("medium", 50),
            sluggish_speed_px=cong_cfg.get("speed_threshold_px", 4.0),
        )

        # Processing parameters
        self.frame_skip = int(proc_cfg.get("frame_skip", 1))
        self.resize_width = int(proc_cfg.get("resize_width", 1280))
        self.show_trails = bool(proc_cfg.get("show_trails", True))
        self.show_boxes = bool(proc_cfg.get("show_boxes", True))
        self.show_line = bool(proc_cfg.get("show_counting_line", True))

        # Runtime metrics
        self.total_frames_processed = 0
        self.fps = 0.0
        self.last_stat_log_frame = 0

    def reset(self) -> None:
        """Reset all state counters and tracking histories."""
        self.tracker.reset()
        self.counter.reset()
        self.wrong_way_detector.reset()
        self.total_frames_processed = 0
        self.fps = 0.0
        self.last_stat_log_frame = 0

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process a single image frame, annotate detections/HUD, log events,
        and return the annotated frame along with the real-time telemetry payload.
        """
        start_time = time.time()
        self.total_frames_processed += 1

        # Resize for consistent performance if requested
        h, w = frame.shape[:2]
        if self.resize_width > 0 and w != self.resize_width:
            aspect_ratio = h / w
            new_w = self.resize_width
            new_h = int(new_w * aspect_ratio)
            frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            h, w = new_h, new_w

        annotated_frame = frame.copy()

        # Step 1: Track objects
        tracked_vehicles = self.tracker.track(annotated_frame)

        # Step 2: Direction & Wrong-way detection
        directions, new_violations = self.wrong_way_detector.analyze(tracked_vehicles)
        for viol in new_violations:
            self.db.log_event(
                vehicle_id=viol.vehicle_id,
                vehicle_type=viol.vehicle_type,
                direction=viol.detected_direction,
                event_type="WRONG_WAY",
                confidence=viol.confidence,
                timestamp=viol.timestamp,
            )

        # Step 3: Vehicle counting line
        new_crossings = self.counter.update(tracked_vehicles, (h, w), directions)
        for cross in new_crossings:
            self.db.log_event(
                vehicle_id=cross.vehicle_id,
                vehicle_type=cross.vehicle_type,
                direction=cross.direction,
                event_type="CROSSING",
                confidence=cross.confidence,
                timestamp=cross.timestamp,
            )

        # Step 4: Traffic density & congestion analysis
        traffic_state: TrafficState = self.traffic_analyzer.analyze(tracked_vehicles)

        # Step 5: Periodic snapshot to database (on first frame and every 30 frames)
        if self.total_frames_processed == 1 or (self.total_frames_processed - self.last_stat_log_frame >= 30):
            counts = self.counter.get_summary()
            self.db.log_statistics(
                total_vehicles=counts.get("total", 0),
                cars=counts.get("car", 0),
                motorcycles=counts.get("motorcycle", 0),
                buses=counts.get("bus", 0),
                trucks=counts.get("truck", 0),
                density=traffic_state.density_level,
                congestion=traffic_state.congestion_level,
                wrong_way_count=len(self.wrong_way_detector.confirmed_violations),
            )
            self.last_stat_log_frame = self.total_frames_processed

        # Calculate FPS
        elapsed = time.time() - start_time
        if elapsed > 0:
            instant_fps = 1.0 / elapsed
            self.fps = round(0.9 * self.fps + 0.1 * instant_fps, 1) if self.fps > 0 else round(instant_fps, 1)

        # Step 6: Visual Annotations
        self._render_annotations(
            annotated_frame,
            tracked_vehicles,
            directions,
            traffic_state,
            (w, h),
        )

        counts = self.counter.get_summary()
        telemetry = {
            "fps": self.fps,
            "frame_idx": self.total_frames_processed,
            "active_vehicles": traffic_state.vehicle_count,
            "density_level": traffic_state.density_level,
            "congestion_level": traffic_state.congestion_level,
            "average_speed_px": traffic_state.average_speed_px,
            "density_score": traffic_state.density_score,
            "total_counted": counts.get("total", 0),
            "cars": counts.get("car", 0),
            "motorcycles": counts.get("motorcycle", 0),
            "buses": counts.get("bus", 0),
            "trucks": counts.get("truck", 0),
            "bicycles": counts.get("bicycle", 0),
            "pedestrians": counts.get("person", 0),
            "wrong_way_count": len(self.wrong_way_detector.confirmed_violations),
            "active_violations": list(self.wrong_way_detector.current_violating_ids),
        }

        return annotated_frame, telemetry

    def _render_annotations(
        self,
        frame: np.ndarray,
        tracked_vehicles: list[TrackedVehicle],
        directions: Dict[int, str],
        traffic_state: TrafficState,
        dims: Tuple[int, int],
    ) -> None:
        """Render counting line, bounding boxes, motion trails, HUD cards, and warnings."""
        w, h = dims

        # 1. Render Virtual Counting Line
        if self.show_line:
            p1, p2 = self.counter.get_line_coords(w, h)
            # Glowing cyan line
            cv2.line(frame, p1, p2, (255, 230, 0), 2, cv2.LINE_AA)
            cv2.putText(
                frame,
                "--- VIRTUAL COUNTING LINE ---",
                (w // 2 - 140, p1[1] - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 230, 0),
                2,
                cv2.LINE_AA,
            )

        # 2. Render Tracked Vehicles
        for v in tracked_vehicles:
            is_violating = self.wrong_way_detector.is_violating(v.track_id)
            cname = v.class_name.lower()
            box_color = CLASS_COLORS.get("wrong_way" if is_violating else cname, CLASS_COLORS["default"])

            x1, y1, x2, y2 = v.box

            # Render motion trails
            if self.show_trails and len(v.history) > 1:
                pts = np.array(v.history, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(frame, [pts], False, box_color, 2, cv2.LINE_AA)

            # Render bounding box
            if self.show_boxes:
                thickness = 3 if is_violating else 2
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, thickness)

                # Label text: e.g., "Car 0.91 | ID: 12 -> RIGHT"
                dir_label = directions.get(v.track_id, "")
                arrow = ""
                if dir_label == "RIGHT":
                    arrow = "->"
                elif dir_label == "LEFT":
                    arrow = "<-"
                elif dir_label == "UP":
                    arrow = "^"
                elif dir_label == "DOWN":
                    arrow = "v"

                label_text = f"ID:{v.track_id} {v.class_name} {v.confidence:.2f} {arrow}"
                if is_violating:
                    label_text = f"[!] WRONG WAY ID:{v.track_id} {arrow}"

                draw_header_badge(frame, label_text, (x1, y1 - 2), box_color, text_color=(255, 255, 255))

        # 3. Prominent Top-Center Alert if active wrong-way violation exists
        if self.wrong_way_detector.current_violating_ids:
            alert_text = f"WARNING: WRONG-WAY VEHICLE DETECTED (ID: {list(self.wrong_way_detector.current_violating_ids)})"
            # Background banner in red
            cv2.rectangle(frame, (w // 2 - 320, 10), (w // 2 + 320, 50), (0, 0, 200), -1)
            cv2.putText(
                frame,
                alert_text,
                (w // 2 - 300, 38),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

        # 4. Top-Left HUD Info Overlay (Glassmorphism dark style)
        hud_w, hud_h = 280, 110
        overlay = frame.copy()
        cv2.rectangle(overlay, (15, 15), (15 + hud_w, 15 + hud_h), (20, 24, 33), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        cv2.rectangle(frame, (15, 15), (15 + hud_w, 15 + hud_h), (80, 90, 100), 1)

        # Density Color
        dens_col = (46, 204, 113) if traffic_state.density_level == "LOW" else (
            (241, 196, 15) if traffic_state.density_level == "MEDIUM" else (0, 0, 230)
        )
        cong_col = (46, 204, 113) if traffic_state.congestion_level == "NORMAL" else (
            (241, 196, 15) if traffic_state.congestion_level == "MODERATE" else (0, 0, 230)
        )

        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, f"TRAFFIC DENSITY: {traffic_state.density_level}", (25, 42), font, 0.52, dens_col, 2, cv2.LINE_AA)
        cv2.putText(frame, f"CONGESTION: {traffic_state.congestion_level}", (25, 68), font, 0.52, cong_col, 2, cv2.LINE_AA)
        cv2.putText(
            frame,
            f"ACTIVE: {traffic_state.vehicle_count}  |  TOTAL: {self.counter.total_count}  |  FPS: {self.fps}",
            (25, 94),
            font,
            0.45,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )

    def process_video_file(
        self,
        video_path: str,
        output_path: Optional[str] = None,
    ) -> Generator[Tuple[np.ndarray, Dict[str, Any]], None, None]:
        """
        Process a video file generator, yielding (frame, stats) on every processed frame.
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video source at {video_path}")

        writer = None
        if output_path is not None:
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if self.resize_width > 0 and w != self.resize_width:
                h = int(self.resize_width * (h / w))
                w = self.resize_width
            writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

        frame_num = 0
        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret or frame is None:
                    break

                frame_num += 1
                if self.frame_skip > 1 and (frame_num % self.frame_skip != 0):
                    continue

                annotated_frame, stats = self.process_frame(frame)
                if writer is not None:
                    writer.write(annotated_frame)

                yield annotated_frame, stats
        finally:
            cap.release()
            if writer is not None:
                writer.release()
