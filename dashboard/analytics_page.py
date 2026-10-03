"""
Traffic Analytics and Historical Trends Page.
Renders interactive Plotly visual charts, dynamic data filters,
and time-series traffic density insights.
"""

from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import (
    render_section_header,
    render_empty_state,
    create_vehicle_distribution_chart,
    create_traffic_over_time_chart,
    create_direction_chart,
    create_density_gauge,
)
from src.statistics import TrafficStatistics


def render_analytics_page(
    config: Dict[str, Any],
    db_manager: Any,
    latest_stats: Dict[str, Any],
) -> None:
    """Render the dedicated Traffic Analytics & Trends page."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>Traffic Analytics</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Historical traffic intelligence, modal split, and multi-dimensional trend analytics
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='hardware-chip'>📈 PLOTLY ENGINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 1. Filters Card
    with st.container():
        st.markdown(
            f"""
            <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 14px 18px; margin-bottom: 18px;'>
                <div style='font-size: 11px; font-weight: 700; color: {THEME["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px;'>
                    FILTER HISTORICAL DATASET
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            record_limit = st.selectbox("Max Events Loaded", [50, 100, 250, 500, 1000], index=2)
        with f2:
            event_type_filter = st.selectbox("Event Category", ["All Events", "CROSSING", "WRONG_WAY"], index=0)
        with f3:
            vehicle_filter = st.selectbox(
                "Vehicle Classification",
                ["All Classes", "Car", "Motorcycle", "Bus", "Truck", "Bicycle", "Person"],
                index=0,
            )
        with f4:
            direction_filter = st.selectbox("Flow Direction", ["All Directions", "RIGHT", "LEFT", "UP", "DOWN"], index=0)

    # Query database
    events_df = db_manager.get_recent_events(limit=record_limit)
    stats_df = db_manager.get_statistics_history(limit=record_limit)

    # Apply filters
    filtered_events = events_df.copy() if events_df is not None and not events_df.empty else pd.DataFrame()
    if not filtered_events.empty:
        if event_type_filter != "All Events":
            filtered_events = filtered_events[filtered_events["event_type"] == event_type_filter]
        if vehicle_filter != "All Classes":
            filtered_events = filtered_events[filtered_events["vehicle_type"].str.lower() == vehicle_filter.lower()]
        if direction_filter != "All Directions":
            filtered_events = filtered_events[filtered_events["direction"] == direction_filter]

    # Compute statistics summary
    summary_data = TrafficStatistics.compute_summary(filtered_events, stats_df)

    # 2. Charts Grid
    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            create_vehicle_distribution_chart(summary_data if summary_data["total_vehicles"] > 0 else latest_stats),
            use_container_width=True,
        )
    with g2:
        st.plotly_chart(
            create_traffic_over_time_chart(stats_df),
            use_container_width=True,
        )

    g3, g4 = st.columns(2)
    with g3:
        st.plotly_chart(
            create_direction_chart(summary_data["directional_split"]),
            use_container_width=True,
        )
    with g4:
        st.plotly_chart(
            create_density_gauge(
                latest_stats.get("density_level", summary_data.get("congestion_summary", "LOW")),
                latest_stats.get("active_vehicles", 0),
            ),
            use_container_width=True,
        )

    # 3. Filtered Records Data Table
    render_section_header("Historical Record Log", f"Showing {len(filtered_events)} filtered event records from SQLite database")

    if not filtered_events.empty:
        st.dataframe(
            filtered_events[["id", "vehicle_id", "vehicle_type", "event_type", "direction", "confidence", "timestamp"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        render_empty_state(
            "NO ANALYTICS DATA",
            "No traffic events match the active filter criteria or no video has been processed yet.",
            icon="📊",
        )
