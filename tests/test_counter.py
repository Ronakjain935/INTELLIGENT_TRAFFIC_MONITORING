"""
Unit tests for VehicleCounter and line crossing detection.
"""

import pytest
from src.counter import VehicleCounter, CrossingEvent
from src.tracker import TrackedVehicle
from src.utils import lines_intersect


def test_lines_intersect_detection():
    """Verify 2D segment intersection detection."""
    # Crossing segments: (0, 5) -> (10, 5) intersected by (5, 0) -> (5, 10)
    assert lines_intersect((0, 5), (10, 5), (5, 0), (5, 10)) is True

    # Parallel non-intersecting lines
    assert lines_intersect((0, 5), (10, 5), (0, 8), (10, 8)) is False


def test_vehicle_counter_crossing_event():
    """Verify that a vehicle moving across the line triggers a crossing event."""
    counter = VehicleCounter(line_ratio_y=0.5)  # Line at y=250 for height 500
    frame_shape = (500, 800, 3)

    # Vehicle 1 starts at y=200 and moves to y=300 (crossing y=250)
    v1 = TrackedVehicle(
        track_id=1,
        class_id=2,
        class_name="car",
        confidence=0.88,
        box=(100, 280, 150, 320),
        center=(125, 300),
        history=[(125, 200), (125, 300)],
        speed_px=100.0,
    )

    events = counter.update([v1], frame_shape)
    assert len(events) == 1
    assert events[0].vehicle_id == 1
    assert events[0].vehicle_type == "car"
    assert counter.total_count == 1
    assert counter.class_counts["car"] == 1


def test_vehicle_counter_no_duplicate_counting():
    """Verify that the same vehicle is not counted multiple times."""
    counter = VehicleCounter(line_ratio_y=0.5)
    frame_shape = (500, 800, 3)

    v1 = TrackedVehicle(
        track_id=10,
        class_id=3,
        class_name="motorcycle",
        confidence=0.92,
        box=(200, 280, 240, 320),
        center=(220, 300),
        history=[(220, 200), (220, 300)],
    )

    # First crossing
    events1 = counter.update([v1], frame_shape)
    assert len(events1) == 1
    assert counter.total_count == 1

    # Next frame - same vehicle moves further
    v1.history.append((220, 350))
    events2 = counter.update([v1], frame_shape)
    assert len(events2) == 0
    assert counter.total_count == 1  # Still 1
