"""
Unit tests for VehicleDetector and DatabaseManager.
"""

import os
import tempfile
import numpy as np
import pytest
from src.detector import VehicleDetector
from src.database import DatabaseManager


def test_detector_initialization():
    """Verify VehicleDetector initializes with fallback or defaults."""
    detector = VehicleDetector(model_name="yolov8n.pt", confidence=0.45, iou=0.55, device="cpu")
    assert detector.confidence == 0.45
    assert detector.iou == 0.55
    assert detector.device == "cpu"

    # Test dynamic threshold update
    detector.update_thresholds(confidence=0.30, iou=0.40)
    assert detector.confidence == 0.30
    assert detector.iou == 0.40


def test_detector_empty_frame():
    """Verify detector handles empty/None frames gracefully without crashing."""
    detector = VehicleDetector(confidence=0.40, device="cpu")
    assert detector.detect(None) == []
    assert detector.detect(np.array([])) == []


def test_database_manager():
    """Verify database initialization, event logging, and queries."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path)

        # Log a crossing event
        event_id = db.log_event(
            vehicle_id=12,
            vehicle_type="car",
            direction="RIGHT",
            event_type="CROSSING",
            confidence=0.94,
        )
        assert event_id > 0

        # Log a wrong-way violation
        viol_id = db.log_event(
            vehicle_id=24,
            vehicle_type="motorcycle",
            direction="LEFT",
            event_type="WRONG_WAY",
            confidence=0.89,
        )
        assert viol_id > 0

        # Log statistics snapshot
        stat_id = db.log_statistics(
            total_vehicles=1,
            cars=1,
            motorcycles=0,
            buses=0,
            trucks=0,
            density="LOW",
            congestion="NORMAL",
            wrong_way_count=1,
        )
        assert stat_id > 0

        # Query events
        events_df = db.get_recent_events(limit=10)
        assert len(events_df) == 2

        # Query violations
        viols_df = db.get_violations(limit=10)
        assert len(viols_df) == 1
        assert viols_df.iloc[0]["vehicle_id"] == 24

        # Query counts
        counts = db.get_aggregate_counts()
        assert counts["car"] == 1
        assert counts["total"] == 1
        assert counts["violations"] == 1

    finally:
        import gc
        gc.collect()
        try:
            if os.path.exists(db_path):
                os.remove(db_path)
        except Exception:
            pass
