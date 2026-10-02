"""
Vehicle Counter Module.
Detects when tracked vehicles cross a virtual counting line and maintains
deduplicated counts categorized by vehicle class.
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Set, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from src.tracker import TrackedVehicle
from src.utils import lines_intersect


@dataclass
class CrossingEvent:
    vehicle_id: int
    vehicle_type: str
    timestamp: str
    direction: str
    confidence: float
    crossing_point: Tuple[int, int]


class VehicleCounter:
    """
    Counts vehicles crossing a configurable virtual line without double-counting.
    """

    def __init__(
        self,
        line_ratio_y: float = 0.55,
        line_offset: int = 12,
        custom_line: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
    ):
        self.line_ratio_y = float(line_ratio_y)
        self.line_offset = int(line_offset)
        self.custom_line = custom_line

        # Count tracking
        self.counted_ids: Set[int] = set()
        self.class_counts: Dict[str, int] = {
            "car": 0,
            "motorcycle": 0,
            "bus": 0,
            "truck": 0,
            "bicycle": 0,
            "person": 0,
        }
        self.total_count: int = 0
        self.crossing_events: List[CrossingEvent] = []

    def reset(self) -> None:
        """Reset all counters and crossing events."""
        self.counted_ids.clear()
        for k in self.class_counts:
            self.class_counts[k] = 0
        self.total_count = 0
        self.crossing_events.clear()

    def get_line_coords(self, frame_width: int, frame_height: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Compute the start and end coordinates of the counting line."""
        if self.custom_line is not None:
            return self.custom_line
        y = int(frame_height * self.line_ratio_y)
        return ((0, y), (frame_width, y))

    def update(
        self,
        tracked_vehicles: List[TrackedVehicle],
        frame_shape: Tuple[int, int],
        vehicle_directions: Optional[Dict[int, str]] = None,
    ) -> List[CrossingEvent]:
        """
        Check for new line-crossing events among active tracked vehicles.
        Returns list of new crossing events triggered in this frame.
        """
        h, w = frame_shape[:2]
        line_p1, line_p2 = self.get_line_coords(w, h)
        new_events: List[CrossingEvent] = []
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for v in tracked_vehicles:
            # Skip if vehicle already counted
            if v.track_id in self.counted_ids:
                continue

            # Need at least two history points to determine movement segment
            if len(v.history) < 2:
                continue

            prev_pt = v.history[-2]
            curr_pt = v.history[-1]

            # Check if trajectory segment intersects counting line
            has_crossed = lines_intersect(prev_pt, curr_pt, line_p1, line_p2)

            # Fallback proximity check if line is horizontal
            if not has_crossed and line_p1[1] == line_p2[1]:
                line_y = line_p1[1]
                min_y = min(prev_pt[1], curr_pt[1])
                max_y = max(prev_pt[1], curr_pt[1])
                if min_y <= line_y <= max_y:
                    has_crossed = True

            if has_crossed:
                self.counted_ids.add(v.track_id)
                self.total_count += 1

                # Update class count
                cname = v.class_name.lower()
                if cname not in self.class_counts:
                    self.class_counts[cname] = 0
                self.class_counts[cname] += 1

                # Determine direction at crossing
                direction = "UNKNOWN"
                if vehicle_directions and v.track_id in vehicle_directions:
                    direction = vehicle_directions[v.track_id]
                else:
                    # Quick fallback direction from line crossing
                    dy = curr_pt[1] - prev_pt[1]
                    dx = curr_pt[0] - prev_pt[0]
                    if abs(dy) >= abs(dx):
                        direction = "DOWN" if dy > 0 else "UP"
                    else:
                        direction = "RIGHT" if dx > 0 else "LEFT"

                event = CrossingEvent(
                    vehicle_id=v.track_id,
                    vehicle_type=v.class_name,
                    timestamp=now_str,
                    direction=direction,
                    confidence=v.confidence,
                    crossing_point=curr_pt,
                )
                self.crossing_events.append(event)
                new_events.append(event)

        return new_events

    def get_summary(self) -> Dict[str, int]:
        """Return dictionary of current counts."""
        summary = self.class_counts.copy()
        summary["total"] = self.total_count
        return summary
