"""
Automated Traffic Audit Reports & Data Export Page.
Facilitates executive reporting, CSV data exports, PDF compliance documentation,
and database record lifecycle management.
"""

from __future__ import annotations
import time
from typing import Dict, Any
import pandas as pd
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import (
    render_section_header,
    render_kpi_card,
    generate_csv_report,
    generate_pdf_report,
)
from src.statistics import TrafficStatistics


def render_reports_page(
    config: Dict[str, Any],
    db_manager: Any,
) -> None:
    """Render the dedicated Audit Reports and Export page."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>TRAFFIC AUDIT REPORT</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Automated traffic compliance summary, violation audits, and tabular dataset exports
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='hardware-chip'>📄 REPORT ENGINE</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    all_events_df = db_manager.get_recent_events(limit=1000)
    stats_history_df = db_manager.get_statistics_history(limit=500)
    summary = TrafficStatistics.compute_summary(all_events_df, stats_history_df)

    # 1. Executive Summary Cards
    render_section_header("Executive Analysis Summary", "Aggregated highway surveillance metrics")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_kpi_card("TOTAL VEHICLES", f"{summary.get('total_vehicles', 0):,}", delta="Cumulative volume", icon="🚗")
    with c2:
        render_kpi_card("FLOW CADENCE", f"{summary.get('vehicles_per_min', 0.0):.1f} veh/min", delta="Mean flow velocity", icon="⚡")
    with c3:
        v_count = summary.get("wrong_way_violations", 0)
        render_kpi_card(
            "WRONG-WAY INFRACTIONS",
            f"{v_count:02d}",
            delta="Critical attention" if v_count > 0 else "Compliant",
            icon="⚠️",
            status_color=THEME["danger"] if v_count > 0 else THEME["success"],
        )
    with c4:
        cong = summary.get("congestion_summary", "NORMAL")
        cong_color = THEME["success"] if cong == "NORMAL" else (THEME["warning"] if cong == "MODERATE" else THEME["danger"])
        render_kpi_card(
            "PREDOMINANT REGIME",
            cong,
            delta="Highway density state",
            icon="🚦",
            status_color=cong_color,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Detailed modal breakdown table
    r_col1, r_col2 = st.columns([1.2, 1])
    with r_col1:
        render_section_header("Vehicle Classification Breakdown", "Modal share distribution")
        tot = max(1, summary.get("total_vehicles", 1))
        breakdown_data = [
            {"Category": "Passenger Cars", "Count": summary.get("cars", 0), "Share": f"{(summary.get('cars', 0) / tot * 100):.1f}%"},
            {"Category": "Motorcycles & Scooters", "Count": summary.get("motorcycles", 0), "Share": f"{(summary.get('motorcycles', 0) / tot * 100):.1f}%"},
            {"Category": "Buses & Public Transit", "Count": summary.get("buses", 0), "Share": f"{(summary.get('buses', 0) / tot * 100):.1f}%"},
            {"Category": "Commercial Trucks", "Count": summary.get("trucks", 0), "Share": f"{(summary.get('trucks', 0) / tot * 100):.1f}%"},
            {"Category": "Bicycles & Micro-mobility", "Count": summary.get("bicycles", 0), "Share": f"{(summary.get('bicycles', 0) / tot * 100):.1f}%"},
            {"Category": "Pedestrians", "Count": summary.get("pedestrians", 0), "Share": f"{(summary.get('pedestrians', 0) / tot * 100):.1f}%"},
        ]
        st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

    with r_col2:
        render_section_header("Surveillance Operational Attributes", "Pipeline and site characteristics")
        st.markdown(
            f"""
            <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 16px;'>
                <div style='display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid {THEME["border"]}; font-size: 13px;'>
                    <span style='color: {THEME["text_secondary"]};'>Authorized Flow Direction</span>
                    <span style='color: {THEME["accent_primary"]}; font-weight: 700;'>{config.get("traffic", {}).get("expected_direction", "RIGHT")} ➔</span>
                </div>
                <div style='display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid {THEME["border"]}; font-size: 13px;'>
                    <span style='color: {THEME["text_secondary"]};'>Peak Traffic Window</span>
                    <span style='color: {THEME["text_primary"]}; font-weight: 700;'>{summary.get("peak_period", "N/A")}</span>
                </div>
                <div style='display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid {THEME["border"]}; font-size: 13px;'>
                    <span style='color: {THEME["text_secondary"]};'>Dominant Vehicle Category</span>
                    <span style='color: {THEME["text_primary"]}; font-weight: 700;'>{summary.get("most_frequent_class", "N/A")}</span>
                </div>
                <div style='display: flex; justify-content: space-between; padding: 6px 0; font-size: 13px;'>
                    <span style='color: {THEME["text_secondary"]};'>Database Storage Backend</span>
                    <span style='color: {THEME["success"]}; font-weight: 700;'>SQLite3 (Local Persistent)</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # 2. Action Download Cards
    render_section_header("Export & Database Management", "Generate compliance documents and manage system records")

    col_csv, col_pdf, col_reset = st.columns(3)

    with col_csv:
        st.markdown(
            f"""
            <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 18px; margin-bottom: 10px;'>
                <div style='font-size: 15px; font-weight: 700; color: {THEME["text_primary"]};'>📊 CSV Event Dataset</div>
                <div style='font-size: 12px; color: {THEME["text_secondary"]}; margin-top: 4px; margin-bottom: 12px;'>
                    Download tabular log of vehicle timestamps, classes, tripwire coordinates, and confidence values.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        csv_bytes = generate_csv_report(all_events_df)
        st.download_button(
            label="📥 DOWNLOAD CSV REPORT",
            data=csv_bytes,
            file_name=f"traffic_events_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_pdf:
        st.markdown(
            f"""
            <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 18px; margin-bottom: 10px;'>
                <div style='font-size: 15px; font-weight: 700; color: {THEME["text_primary"]};'>📄 Official PDF Audit</div>
                <div style='font-size: 12px; color: {THEME["text_secondary"]}; margin-top: 4px; margin-bottom: 12px;'>
                    Compile executive compliance document with formatted violation tables and traffic breakdown.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        viol_for_pdf = db_manager.get_violations(limit=50)
        try:
            pdf_bytes = generate_pdf_report(summary, viol_for_pdf)
            st.download_button(
                label="📄 DOWNLOAD PDF AUDIT",
                data=pdf_bytes,
                file_name=f"traffic_audit_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    with col_reset:
        st.markdown(
            f"""
            <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 18px; margin-bottom: 10px;'>
                <div style='font-size: 15px; font-weight: 700; color: {THEME["danger"]};'>🗑️ Purge Records</div>
                <div style='font-size: 12px; color: {THEME["text_secondary"]}; margin-top: 4px; margin-bottom: 12px;'>
                    Clear local SQLite event and telemetry records to reset counters for a new observation trial.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🗑️ RESET DATABASE RECORDS", use_container_width=True):
            db_manager.clear_all()
            st.success("Database records successfully purged.")
            st.rerun()
