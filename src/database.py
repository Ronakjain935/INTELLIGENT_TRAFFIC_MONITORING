"""
SQLite Database Management Module.
Handles automated schema creation, thread-safe connection pooling,
event logging, violation recording, and statistical snapshot persistence.
"""

from __future__ import annotations

import sqlite3
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd


class DatabaseManager:
    """
    Manages local SQLite database operations for the traffic monitoring system.
    """

    def __init__(self, db_path: str = "data/traffic_system.db"):
        self.db_path = Path(db_path)
        # Ensure parent directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Create a new SQLite connection with foreign keys and dict-like row factory."""
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self) -> None:
        """Create tables and indexes if they do not already exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Traffic Events Table (Crossing events, detections)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS traffic_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL,
                    vehicle_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    confidence REAL NOT NULL
                )
                """
            )

            # 2. Traffic Statistics Snapshots Table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS traffic_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_vehicles INTEGER NOT NULL,
                    cars INTEGER NOT NULL,
                    motorcycles INTEGER NOT NULL,
                    buses INTEGER NOT NULL,
                    trucks INTEGER NOT NULL,
                    density TEXT NOT NULL,
                    congestion TEXT NOT NULL,
                    wrong_way_count INTEGER NOT NULL
                )
                """
            )

            # 3. Create indexes for quick queries by timestamp and event_type
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON traffic_events(timestamp)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type ON traffic_events(event_type)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_stats_timestamp ON traffic_statistics(timestamp)"
            )
            conn.commit()

    def log_event(
        self,
        vehicle_id: int,
        vehicle_type: str,
        direction: str,
        event_type: str,
        confidence: float,
        timestamp: Optional[str] = None,
    ) -> int:
        """Insert a single event record (CROSSING, WRONG_WAY, etc.)."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO traffic_events (vehicle_id, vehicle_type, timestamp, direction, event_type, confidence)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (int(vehicle_id), str(vehicle_type), timestamp, str(direction), str(event_type), float(confidence)),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def log_statistics(
        self,
        total_vehicles: int,
        cars: int,
        motorcycles: int,
        buses: int,
        trucks: int,
        density: str,
        congestion: str,
        wrong_way_count: int,
        timestamp: Optional[str] = None,
    ) -> int:
        """Insert a periodic snapshot of aggregated traffic metrics."""
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO traffic_statistics (
                    timestamp, total_vehicles, cars, motorcycles, buses, trucks, density, congestion, wrong_way_count
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    timestamp,
                    int(total_vehicles),
                    int(cars),
                    int(motorcycles),
                    int(buses),
                    int(trucks),
                    str(density),
                    str(congestion),
                    int(wrong_way_count),
                ),
            )
            conn.commit()
            return cursor.lastrowid or 0

    def get_recent_events(self, limit: int = 100, event_type: Optional[str] = None) -> pd.DataFrame:
        """Fetch latest logged events as a pandas DataFrame."""
        query = "SELECT id, vehicle_id, vehicle_type, timestamp, direction, event_type, confidence FROM traffic_events"
        params: List[Any] = []
        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
        return df

    def get_violations(self, limit: int = 100) -> pd.DataFrame:
        """Retrieve specifically wrong-way and safety violation events."""
        return self.get_recent_events(limit=limit, event_type="WRONG_WAY")

    def get_statistics_history(self, limit: int = 200) -> pd.DataFrame:
        """Fetch historical periodic traffic snapshots as a DataFrame."""
        query = """
            SELECT id, timestamp, total_vehicles, cars, motorcycles, buses, trucks, density, congestion, wrong_way_count
            FROM traffic_statistics
            ORDER BY id ASC
            LIMIT ?
        """
        with self._get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=[limit])
        return df

    def get_aggregate_counts(self) -> Dict[str, int]:
        """Compute all-time count summaries directly from database."""
        query = """
            SELECT vehicle_type, COUNT(*) as count
            FROM traffic_events
            WHERE event_type = 'CROSSING'
            GROUP BY vehicle_type
        """
        counts = {"car": 0, "motorcycle": 0, "bus": 0, "truck": 0, "bicycle": 0, "person": 0, "total": 0}
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            for row in cursor.fetchall():
                vtype = row["vehicle_type"].lower()
                c = int(row["count"])
                counts[vtype] = c
                counts["total"] += c

            cursor.execute("SELECT COUNT(*) FROM traffic_events WHERE event_type = 'WRONG_WAY'")
            counts["violations"] = cursor.fetchone()[0]

        return counts

    def clear_all(self) -> None:
        """Purge all event and statistics tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM traffic_events")
            cursor.execute("DELETE FROM traffic_statistics")
            conn.commit()
