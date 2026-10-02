"""
Traffic Density and Congestion Analysis Module.
Calculates real-time road density classification (LOW / MEDIUM / HIGH)
and estimates traffic congestion level based on vehicle counts and mean velocity.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import numpy as np

from src.tracker import TrackedVehicle


@dataclass
class TrafficState:
    vehicle_count: int
    density_level: str          # "LOW", "MEDIUM", "HIGH"
    congestion_level: str       # "NORMAL", "MODERATE", "CONGESTED"
    average_speed_px: float     # Average movement in px/frame
    density_score: float        # Normalized ratio between 0.0 and 1.0


class TrafficAnalyzer:
    """
    Evaluates real-time traffic density and estimates road congestion heuristics.
    
    NOTE: Congestion classification is an AI-estimated heuristic based on visual
    vehicle counts and apparent pixel speeds in camera perspective, not an official
    inductive loop sensor measurement.
    """

    def __init__(
        self,
        low_density_threshold: int = 20,
        medium_density_threshold: int = 50,
        sluggish_speed_px: float = 4.0,
    ):
        self.low_thresh = int(low_density_threshold)
        self.med_thresh = int(medium_density_threshold)
        self.sluggish_speed = float(sluggish_speed_px)

    def update_thresholds(
        self,
        low_thresh: int | None = None,
        med_thresh: int | None = None,
        sluggish_speed: float | None = None,
    ) -> None:
        """Update density and speed thresholds dynamically."""
        if low_thresh is not None:
            self.low_thresh = int(low_thresh)
        if med_thresh is not None:
            self.med_thresh = int(med_thresh)
        if sluggish_speed is not None:
            self.sluggish_speed = float(sluggish_speed)

    def classify_density(self, count: int) -> str:
        """
        Classify vehicle count into density tier:
        - 0 to low_thresh: LOW
        - (low_thresh + 1) to med_thresh: MEDIUM
        - > med_thresh: HIGH
        """
        if count <= self.low_thresh:
            return "LOW"
        elif count <= self.med_thresh:
            return "MEDIUM"
        else:
            return "HIGH"

    def estimate_congestion(self, count: int, avg_speed: float) -> str:
        """
        Heuristic congestion estimator combining density tier and movement velocity:
        - Low vehicle count: NORMAL
        - Medium vehicle count:
            - If vehicles moving well: NORMAL
            - If vehicles sluggish: MODERATE
        - High vehicle count:
            - If vehicles sluggish: CONGESTED
            - If moving fast: MODERATE
        """
        density = self.classify_density(count)

        if density == "LOW":
            return "NORMAL"
        elif density == "MEDIUM":
            if avg_speed < self.sluggish_speed:
                return "MODERATE"
            return "NORMAL"
        else:  # HIGH
            if avg_speed < self.sluggish_speed:
                return "CONGESTED"
            return "MODERATE"

    def analyze(self, tracked_vehicles: List[TrackedVehicle]) -> TrafficState:
        """
        Analyze current frame's tracked vehicles to determine density and congestion.
        """
        active_count = len(tracked_vehicles)
        speeds = [v.speed_px for v in tracked_vehicles if v.speed_px > 0]
        avg_speed = float(np.mean(speeds)) if speeds else 0.0

        density_tier = self.classify_density(active_count)
        congestion_tier = self.estimate_congestion(active_count, avg_speed)

        # Normalized density score (0.0 to 1.0 clamped)
        max_reference = max(self.med_thresh * 1.5, 60.0)
        density_score = min(1.0, active_count / max_reference)

        return TrafficState(
            vehicle_count=active_count,
            density_level=density_tier,
            congestion_level=congestion_tier,
            average_speed_px=round(avg_speed, 2),
            density_score=round(density_score, 3),
        )
