"""
Traffic Statistics and Analytics Module.
Calculates vehicle distributions, traffic rates (per minute/hour),
peak traffic intervals, directional splits, and violation ratios.
"""

from __future__ import annotations

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np


class TrafficStatistics:
    """
    Computes analytical aggregations from traffic events and statistics data.
    """

    @staticmethod
    def compute_summary(events_df: pd.DataFrame, stats_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Produce a comprehensive analytical summary dictionary.
        """
        if events_df is None or events_df.empty:
            return {
                "total_vehicles": 0,
                "cars": 0,
                "motorcycles": 0,
                "buses": 0,
                "trucks": 0,
                "bicycles": 0,
                "pedestrians": 0,
                "wrong_way_violations": 0,
                "peak_period": "N/A",
                "vehicles_per_min": 0.0,
                "directional_split": {"RIGHT": 0, "LEFT": 0, "UP": 0, "DOWN": 0},
                "most_frequent_class": "N/A",
                "congestion_summary": "NORMAL",
            }

        # Filter crossing events
        crossing_mask = events_df["event_type"] == "CROSSING"
        crossing_df = events_df[crossing_mask] if crossing_mask.any() else events_df

        total_vehicles = len(crossing_df)
        vtypes = crossing_df["vehicle_type"].str.lower().value_counts().to_dict()

        # Count violations
        violations_count = int((events_df["event_type"] == "WRONG_WAY").sum())

        # Directional split
        dir_counts = crossing_df["direction"].value_counts().to_dict()
        directional_split = {
            "RIGHT": dir_counts.get("RIGHT", 0),
            "LEFT": dir_counts.get("LEFT", 0),
            "UP": dir_counts.get("UP", 0),
            "DOWN": dir_counts.get("DOWN", 0),
        }

        # Vehicles per minute calculation
        vehicles_per_min = 0.0
        peak_period = "N/A"
        try:
            crossing_df_copy = crossing_df.copy()
            crossing_df_copy["dt"] = pd.to_datetime(crossing_df_copy["timestamp"], errors="coerce")
            crossing_df_copy = crossing_df_copy.dropna(subset=["dt"])

            if not crossing_df_copy.empty:
                time_span_seconds = (crossing_df_copy["dt"].max() - crossing_df_copy["dt"].min()).total_seconds()
                duration_minutes = max(1.0, time_span_seconds / 60.0)
                vehicles_per_min = round(total_vehicles / duration_minutes, 2)

                # Group by hour or minute to find peak
                crossing_df_copy["time_bucket"] = crossing_df_copy["dt"].dt.floor("h").dt.strftime("%H:00 - %H:59")
                bucket_counts = crossing_df_copy["time_bucket"].value_counts()
                if not bucket_counts.empty:
                    peak_period = f"{bucket_counts.index[0]} ({bucket_counts.iloc[0]} veh)"
        except Exception:
            vehicles_per_min = float(total_vehicles)

        # Most frequent class
        most_frequent = "N/A"
        if vtypes:
            most_frequent = max(vtypes, key=vtypes.get).capitalize()

        # Congestion status from stats history
        congestion_status = "NORMAL"
        if stats_df is not None and not stats_df.empty and "congestion" in stats_df.columns:
            mode_val = stats_df["congestion"].mode()
            if not mode_val.empty:
                congestion_status = str(mode_val.iloc[0])

        return {
            "total_vehicles": total_vehicles,
            "cars": int(vtypes.get("car", 0)),
            "motorcycles": int(vtypes.get("motorcycle", 0)),
            "buses": int(vtypes.get("bus", 0)),
            "trucks": int(vtypes.get("truck", 0)),
            "bicycles": int(vtypes.get("bicycle", 0)),
            "pedestrians": int(vtypes.get("person", 0)),
            "wrong_way_violations": violations_count,
            "peak_period": peak_period,
            "vehicles_per_min": vehicles_per_min,
            "directional_split": directional_split,
            "most_frequent_class": most_frequent,
            "congestion_summary": congestion_status,
        }


# Backward compatibility alias
summarize_events = TrafficStatistics.compute_summary
