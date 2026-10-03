"""
Command Center Dashboard Overview Page.
Provides executive KPI metrics, live traffic status, operational feed, and vehicle breakdown.
"""

from __future__ import annotations
import time
from typing import Dict, Any
import pandas as pd
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import (
    render_kpi_metrics,
    render_status_card,
    render_alert_card,
    render_section_header,
    render_vehicle_type_card,
    create_vehicle_distribution_chart,
    create_traffic_over_time_chart,
)
from src.statistics import TrafficStatistics


def render_dashboard_page(
    config: Dict[str, Any],
    db_manager: Any,
    latest_stats: Dict[str, Any],
) -> None:
    """Render the primary Traffic Command Center Overview dashboard."""
    # Header with live timestamp
    curr_time = time.strftime("%H:%M:%S")
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>Traffic Command Center</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Real-time AI-powered traffic intelligence and automated surveillance audit
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='status-badge-online'>
                    <span class='status-dot-green'></span> LIVE MONITORING
                </span>
                <span class='hardware-chip'>🕒 {curr_time}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Fetch real data from DB
    events_df = db_manager.get_recent_events(limit=500)
    stats_df = db_manager.get_statistics_history(limit=200)
    summary = TrafficStatistics.compute_summary(events_df, stats_df)

    # Merge database cumulative data with live runtime stats
    merged_stats = dict(latest_stats)
    if summary.get("total_vehicles", 0) > 0:
        merged_stats["total_vehicles"] = summary["total_vehicles"]
        merged_stats["total_counted"] = summary["total_vehicles"]
        merged_stats["cars"] = max(merged_stats.get("cars", 0), summary.get("cars", 0))
        merged_stats["motorcycles"] = max(merged_stats.get("motorcycles", 0), summary.get("motorcycles", 0))
        merged_stats["buses"] = max(merged_stats.get("buses", 0), summary.get("buses", 0))
        merged_stats["trucks"] = max(merged_stats.get("trucks", 0), summary.get("trucks", 0))
        merged_stats["bicycles"] = max(merged_stats.get("bicycles", 0), summary.get("bicycles", 0))
        merged_stats["pedestrians"] = max(merged_stats.get("pedestrians", 0), summary.get("pedestrians", 0))
        merged_stats["wrong_way_count"] = max(merged_stats.get("wrong_way_count", 0), summary.get("wrong_way_violations", 0))

    # 1. Top 4 Large KPI Cards
    render_kpi_metrics(merged_stats)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 2. Main Center Grid: Video / Stream Card (Left) & Traffic Status Card (Right)
    col_left, col_right = st.columns([1.6, 1.0])

    with col_left:
        render_section_header("Operational Video Surveillance", "Live camera feed & multi-object detection tracking", badge="YOLOv8 + ByteTrack")

        # Container for video / status
        if st.session_state.get("is_running", False):
            st.info("Surveillance engine active! Switch to 'Live Monitoring' view for full video telemetry, or control processing from sidebar.")
        else:
            st.markdown(
                f"""
                <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 10px; padding: 28px; text-align: center;'>
                    <div style='font-size: 42px; margin-bottom: 8px;'>🎥</div>
                    <div style='font-size: 16px; font-weight: 700; color: {THEME["text_primary"]}; margin-bottom: 4px;'>
                        SURVEILLANCE ENGINE STANDBY
                    </div>
                    <div style='font-size: 13px; color: {THEME["text_secondary"]}; max-width: 480px; margin: 0 auto 16px auto;'>
                        Ready to process camera streams or uploaded footage. Switch to <b>Live Monitoring</b> to upload a highway video and launch AI analysis.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Active violations banner if present
        if merged_stats.get("wrong_way_count", 0) > 0:
            violations_df = db_manager.get_violations(limit=1)
            if violations_df is not None and not violations_df.empty:
                viol_row = violations_df.iloc[0].to_dict()
                render_alert_card(viol_row)

    with col_right:
        render_section_header("Highway Telemetry Status", "Regime classification & congestion auditing", badge="REAL-TIME")
        render_status_card(
            density=merged_stats.get("density_level", summary.get("congestion_summary", "LOW")),
            active_count=merged_stats.get("active_vehicles", 0),
            congestion_status=merged_stats.get("congestion_level", summary.get("congestion_summary", "NORMAL")),
            expected_direction=config.get("traffic", {}).get("expected_direction", "RIGHT"),
            average_speed_px=merged_stats.get("average_speed_px", 0.0),
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 3. Bottom Grid: Vehicle Modal Split (Left) & Traffic Analytics Chart (Right)
    col_b1, col_b2 = st.columns([1.1, 1.5])

    with col_b1:
        render_section_header("Vehicle Classification", "Modal split tallied by counting boundary")

        tot = max(1, merged_stats.get("total_counted", 0))
        cars = merged_stats.get("cars", 0)
        motorcycles = merged_stats.get("motorcycles", 0)
        buses = merged_stats.get("buses", 0)
        trucks = merged_stats.get("trucks", 0)
        bicycles = merged_stats.get("bicycles", 0)

        render_vehicle_type_card("Passenger Cars", cars, (cars / tot) * 100 if tot > 0 else 0, "🚗", "#22C55E")
        render_vehicle_type_card("Motorcycles & Scooters", motorcycles, (motorcycles / tot) * 100 if tot > 0 else 0, "🏍️", "#38BDF8")
        render_vehicle_type_card("Buses & Public Transit", buses, (buses / tot) * 100 if tot > 0 else 0, "🚌", "#F59E0B")
        render_vehicle_type_card("Commercial Trucks", trucks, (trucks / tot) * 100 if tot > 0 else 0, "🚛", "#F97316")
        render_vehicle_type_card("Bicycles & Micro-mobility", bicycles, (bicycles / tot) * 100 if tot > 0 else 0, "🚲", "#A855F7")

    with col_b2:
        render_section_header("Traffic Volume Distribution", "Modal proportions & peak traffic trends")
        chart = create_vehicle_distribution_chart(merged_stats)
        st.plotly_chart(chart, use_container_width=True)
