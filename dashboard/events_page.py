"""
Traffic Safety Events & Audit Log Page.
Displays real-time and historical safety infractions, wrong-way detection cards,
and categorized event tables.
"""

from __future__ import annotations
from typing import Dict, Any
import pandas as pd
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import (
    render_alert_card,
    render_section_header,
    render_empty_state,
    render_kpi_card,
)


def render_events_page(
    config: Dict[str, Any],
    db_manager: Any,
) -> None:
    """Render the dedicated Security & Safety Events page."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>Traffic Events</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Real-time security monitoring, wrong-way infraction triggers, and incident audit log
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='hardware-chip'>🛡️ SAFETY AUDIT</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    violations_df = db_manager.get_violations(limit=100)
    all_events_df = db_manager.get_recent_events(limit=300)
    stats_history_df = db_manager.get_statistics_history(limit=100)

    # 1. Prominent Wrong-Way Alerts if any exist
    if violations_df is not None and not violations_df.empty:
        latest_viol = violations_df.iloc[0].to_dict()
        latest_viol["expected_direction"] = config.get("traffic", {}).get("expected_direction", "RIGHT")
        render_alert_card(latest_viol)

    # Summary KPI row
    total_events = len(all_events_df) if all_events_df is not None else 0
    total_violations = len(violations_df) if violations_df is not None else 0
    crossing_count = total_events - total_violations

    c1, c2, c3 = st.columns(3)
    with c1:
        render_kpi_card("TOTAL AUDIT EVENTS", f"{total_events:,}", delta="Cumulative events logged", icon="📋")
    with c2:
        render_kpi_card("VEHICLE CROSSINGS", f"{crossing_count:,}", delta="Tripwire boundary crossings", icon="🚦")
    with c3:
        render_kpi_card(
            "WRONG-WAY INFRACTIONS",
            f"{total_violations:,}",
            delta="Violations recorded" if total_violations > 0 else "Zero violations",
            icon="⚠️",
            status_color=THEME["danger"] if total_violations > 0 else THEME["success"],
        )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # 2. Categorized Event Tabs
    tab_all, tab_crossings, tab_violations, tab_snapshots = st.tabs(
        ["📋 ALL EVENTS", "🚗 VEHICLE COUNT", "⚠️ WRONG-WAY ALERTS", "📊 CONGESTION SNAPSHOTS"]
    )

    with tab_all:
        if all_events_df is not None and not all_events_df.empty:
            st.dataframe(
                all_events_df[["id", "vehicle_id", "vehicle_type", "event_type", "direction", "confidence", "timestamp"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            render_empty_state("NO TRAFFIC EVENTS", "No traffic events have been recorded yet. Upload and process a video to begin.", "📋")

    with tab_crossings:
        if all_events_df is not None and not all_events_df.empty:
            cross_df = all_events_df[all_events_df["event_type"] == "CROSSING"]
            if not cross_df.empty:
                st.dataframe(
                    cross_df[["id", "vehicle_id", "vehicle_type", "direction", "confidence", "timestamp"]],
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                render_empty_state("NO CROSSING EVENTS", "No vehicle boundary crossing events logged yet.", "🚗")
        else:
            render_empty_state("NO EVENTS AVAILABLE", "No events logged.", "🚗")

    with tab_violations:
        if violations_df is not None and not violations_df.empty:
            st.dataframe(
                violations_df[["id", "vehicle_id", "vehicle_type", "direction", "confidence", "timestamp"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            render_empty_state(
                "ZERO WRONG-WAY VIOLATIONS",
                "All detected vehicles adhered to authorized flow lanes. No counter-flow violations detected.",
                "✓",
            )

    with tab_snapshots:
        if stats_history_df is not None and not stats_history_df.empty:
            st.dataframe(
                stats_history_df[["id", "timestamp", "total_vehicles", "cars", "motorcycles", "buses", "trucks", "density", "congestion", "wrong_way_count"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            render_empty_state("NO PERIODIC SNAPSHOTS", "Periodic traffic state snapshots will appear here during stream analysis.", "📊")
