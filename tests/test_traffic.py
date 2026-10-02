"""
Unit tests for Traffic Analyzer, Wrong-Way Detector, and Config Loader.
"""

import pytest
from src.traffic_analyzer import TrafficAnalyzer
from src.wrong_way_detector import DirectionAndWrongWayDetector
from src.tracker import TrackedVehicle
from src.utils import load_config


def test_density_classification():
    """Verify traffic density tier classification."""
    analyzer = TrafficAnalyzer(low_density_threshold=20, medium_density_threshold=50)

    assert analyzer.classify_density(0) == "LOW"
    assert analyzer.classify_density(10) == "LOW"
    assert analyzer.classify_density(20) == "LOW"
    assert analyzer.classify_density(21) == "MEDIUM"
    assert analyzer.classify_density(50) == "MEDIUM"
    assert analyzer.classify_density(51) == "HIGH"
    assert analyzer.classify_density(100) == "HIGH"


def test_congestion_estimation():
    """Verify congestion heuristics based on density and velocity."""
    analyzer = TrafficAnalyzer(low_density_threshold=20, medium_density_threshold=50, sluggish_speed_px=4.0)

    # Low traffic is always normal
    assert analyzer.estimate_congestion(count=10, avg_speed=1.0) == "NORMAL"

    # Medium traffic with high speed is normal, sluggish speed is moderate
    assert analyzer.estimate_congestion(count=30, avg_speed=12.0) == "NORMAL"
    assert analyzer.estimate_congestion(count=30, avg_speed=2.5) == "MODERATE"

    # High traffic with sluggish speed is congested, moderate if flowing
    assert analyzer.estimate_congestion(count=65, avg_speed=1.5) == "CONGESTED"
    assert analyzer.estimate_congestion(count=65, avg_speed=15.0) == "MODERATE"


def test_direction_calculation():
    """Verify vector motion direction calculation."""
    detector = DirectionAndWrongWayDetector(expected_direction="RIGHT", min_movement_pixels=10.0)

    # Moving right: x increases
    assert detector.calculate_direction([(100, 200), (150, 200)]) == "RIGHT"

    # Moving left: x decreases
    assert detector.calculate_direction([(200, 200), (120, 200)]) == "LEFT"

    # Moving down: y increases
    assert detector.calculate_direction([(100, 100), (100, 160)]) == "DOWN"

    # Moving up: y decreases
    assert detector.calculate_direction([(100, 200), (100, 140)]) == "UP"

    # Insufficient movement -> STATIONARY
    assert detector.calculate_direction([(100, 100), (102, 103)]) == "STATIONARY"


def test_wrong_way_detection_and_confirmation():
    """Verify wrong-way violation flag requires consecutive confirmation frames."""
    detector = DirectionAndWrongWayDetector(
        expected_direction="RIGHT",
        min_movement_pixels=10.0,
        confirmation_frames=3,
        enabled=True,
    )

    # Vehicle moving left (wrong way for RIGHT expected flow)
    v = TrackedVehicle(
        track_id=27,
        class_id=2,
        class_name="car",
        confidence=0.91,
        box=(300, 200, 350, 240),
        center=(325, 220),
        history=[(400, 220), (325, 220)],
    )

    # Frame 1: count=1 (< 3)
    dirs, viols = detector.analyze([v])
    assert dirs[27] == "LEFT"
    assert len(viols) == 0
    assert detector.is_violating(27) is False

    # Frame 2: count=2 (< 3)
    dirs, viols = detector.analyze([v])
    assert len(viols) == 0

    # Frame 3: count=3 (confirmed violation!)
    dirs, viols = detector.analyze([v])
    assert len(viols) == 1
    assert viols[0].vehicle_id == 27
    assert viols[0].detected_direction == "LEFT"
    assert viols[0].expected_direction == "RIGHT"
    assert detector.is_violating(27) is True


def test_config_loader():
    """Verify configuration loading returns standard keys and defaults."""
    cfg = load_config("config.yaml")
    assert "model" in cfg
    assert "tracking" in cfg
    assert "density" in cfg
    assert "wrong_way" in cfg
    assert cfg["density"]["low"] == 20
