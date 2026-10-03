"""
Direction and Wrong-Way Detection Module.
Calculates motion vectors from centroid histories, compares them against
configured road flow directions, and flags wrong-way vehicle violations.
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from src.tracker import TrackedVehicle


@dataclass
class WrongWayViolation:
    vehicle_id: int
    vehicle_type: str
    detected_direction: str
    expected_direction: str
    timestamp: str
    confidence: float
    box: Tuple[int, int, int, int]
    center: Tuple[int, int]


class DirectionAndWrongWayDetector:
    """
    Analyzes trajectory vectors to determine vehicle motion direction
    and identifies vehicles traveling contrary to designated traffic lanes.
    """

    OPPOSITE_DIRECTIONS = {
        "RIGHT": "LEFT",
        "LEFT": "RIGHT",
        "UP": "DOWN",
        "DOWN": "UP",
    }

    def __init__(
        self,
        expected_direction: str = "RIGHT",
        min_movement_pixels: float = 15.0,
        confirmation_frames: int = 5,
        enabled: bool = True,
    ):
        self.expected_direction = expected_direction.upper()
        self.min_movement_pixels = float(min_movement_pixels)
        self.confirmation_frames = int(confirmation_frames)
        self.enabled = bool(enabled)

        # Counter for consecutive wrong-way frames: {track_id: consecutive_count}
        self.violation_frame_counts: Dict[int, int] = {}
        # Confirmed violations that have been logged: {track_id: WrongWayViolation}
        self.confirmed_violations: Dict[int, WrongWayViolation] = {}
        # Set of active track IDs currently violating in the latest frame
        self.current_violating_ids: Set[int] = set()

    def set_expected_direction(self, direction: str) -> None:
        """Update expected traffic flow direction."""
        self.expected_direction = direction.upper()

    def reset(self) -> None:
        """Reset internal violation states."""
        self.violation_frame_counts.clear()
        self.confirmed_violations.clear()
        self.current_violating_ids.clear()

    def calculate_direction(self, history: List[Tuple[int, int]]) -> str:
        """
        Determine net motion direction from centroid history.
        Requires net displacement >= min_movement_pixels to prevent jitter false alerts.
        """
        if len(history) < 2:
            return "STATIONARY"

        # Compare start of recent window to latest position
        window_size = min(len(history), 15)
        p_start = history[-window_size]
        p_end = history[-1]

        dx = p_end[0] - p_start[0]
        dy = p_end[1] - p_start[1]
        distance = np.hypot(dx, dy)

        if distance < self.min_movement_pixels:
            return "STATIONARY"

        # Dominant axis
        if abs(dx) >= abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        else:
            return "DOWN" if dy > 0 else "UP"

    def analyze(self, tracked_vehicles: List[TrackedVehicle]) -> Tuple[Dict[int, str], List[WrongWayViolation]]:
        """
        Process all active tracked vehicles, calculate their current direction,
        and detect newly confirmed wrong-way violations.

        Returns:
            Tuple of:
              - directions: Dict[track_id, direction_str]
              - new_violations: List[WrongWayViolation] detected in this frame
        """
        directions: Dict[int, str] = {}
        new_violations: List[WrongWayViolation] = []
        self.current_violating_ids.clear()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        opposite = self.OPPOSITE_DIRECTIONS.get(self.expected_direction, "NONE")

        for v in tracked_vehicles:
            dir_str = self.calculate_direction(v.history)
            directions[v.track_id] = dir_str

            if not self.enabled:
                continue

            # Check if moving in opposite direction to flow
            is_wrong_way = (dir_str == opposite)

            if is_wrong_way:
                self.violation_frame_counts[v.track_id] = self.violation_frame_counts.get(v.track_id, 0) + 1
                if self.violation_frame_counts[v.track_id] >= self.confirmation_frames:
                    self.current_violating_ids.add(v.track_id)

                    # Only log as a NEW violation event once per vehicle
                    if v.track_id not in self.confirmed_violations:
                        violation = WrongWayViolation(
                            vehicle_id=v.track_id,
                            vehicle_type=v.class_name,
                            detected_direction=dir_str,
                            expected_direction=self.expected_direction,
                            timestamp=now_str,
                            confidence=v.confidence,
                            box=v.box,
                            center=v.center,
                        )
                        self.confirmed_violations[v.track_id] = violation
                        new_violations.append(violation)
            else:
                # Decrement or reset frame count if heading in legal direction
                if v.track_id in self.violation_frame_counts:
                    self.violation_frame_counts[v.track_id] = max(0, self.violation_frame_counts[v.track_id] - 1)

        return directions, new_violations

    def is_violating(self, track_id: int) -> bool:
        """Check if vehicle is currently confirmed as a wrong-way violator."""
        return track_id in self.current_violating_ids


# Backward compatibility alias
WrongWayDetector = DirectionAndWrongWayDetector
