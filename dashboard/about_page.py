"""
About the System & System Architecture Documentation Page.
"""

from __future__ import annotations
import streamlit as st
from dashboard.styles import THEME
from dashboard.components import render_section_header


def render_about_page() -> None:
    """Render the About Page with system architecture and technology cards."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>About the System</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Intelligent Traffic Monitoring & Safety Violation Detection System
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='hardware-chip'>ℹ️ SYSTEM OVERVIEW</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Core Project Narrative
    st.markdown(
        f"""
        <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 10px; padding: 24px; margin-bottom: 20px;'>
            <h3 style='margin-top: 0; color: {THEME["text_primary"]}; font-size: 18px;'>AI Traffic Command Center</h3>
            <p style='color: {THEME["text_secondary"]}; line-height: 1.6; font-size: 14px;'>
                The <b>Intelligent Traffic Monitoring System</b> is an enterprise-grade AI computer vision platform designed to analyze live and recorded roadway video streams. It performs deep multi-object detection, persistent trajectory tracking, automated tripwire vehicle counting, road density classification, wrong-way driving safety auditing, and historical reporting.
            </p>
            <div style='display: flex; gap: 10px; flex-wrap: wrap; margin-top: 14px;'>
                <span class='hardware-chip'>🎯 Vehicle Detection</span>
                <span class='hardware-chip'>🔄 ByteTrack Multi-Object Tracking</span>
                <span class='hardware-chip'>📏 Tripwire Counting Line</span>
                <span class='hardware-chip'>⚠️ Wrong-Way Detection</span>
                <span class='hardware-chip'>📊 Density & Congestion Analysis</span>
                <span class='hardware-chip'>💾 SQLite3 Relational Storage</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Technology Stack Cards
    render_section_header("Core Technology Stack", "Underlying frameworks and algorithms powering the platform")

    tech_stack = [
        {"name": "Ultralytics YOLOv8", "desc": "Deep learning object detection and vehicle classification", "icon": "🧠", "color": "#38BDF8"},
        {"name": "OpenCV", "desc": "Video frame ingestion, matrix transformations, and HUD rendering", "icon": "👁️", "color": "#22C55E"},
        {"name": "ByteTrack Tracker", "desc": "Kalman filter and Hungarian matching for robust multi-object tracking", "icon": "🔄", "color": "#F59E0B"},
        {"name": "Python & NumPy", "desc": "Core computational orchestration and trajectory vector mathematics", "icon": "🐍", "color": "#38BDF8"},
        {"name": "Streamlit", "desc": "Real-time reactive Command Center frontend dashboard", "icon": "🚦", "color": "#EF4444"},
        {"name": "SQLite3", "desc": "Embedded relational persistence for crossing events and telemetry logs", "icon": "💾", "color": "#A855F7"},
        {"name": "Plotly Express", "desc": "High-performance interactive analytical data visualizations", "icon": "📊", "color": "#06B6D4"},
        {"name": "ReportLab", "desc": "Automated PDF compliance audit documentation generator", "icon": "📄", "color": "#F97316"},
    ]

    cols = st.columns(4)
    for idx, tech in enumerate(tech_stack):
        with cols[idx % 4]:
            st.markdown(
                f"""
                <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 16px; min-height: 130px; margin-bottom: 12px;'>
                    <div style='font-size: 24px; margin-bottom: 6px;'>{tech["icon"]}</div>
                    <div style='font-size: 14px; font-weight: 700; color: {tech["color"]};'>{tech["name"]}</div>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]}; margin-top: 4px; line-height: 1.4;'>{tech["desc"]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Pipeline Diagram
    render_section_header("AI Processing Pipeline", "End-to-end data flow from video stream to audit logs")

    st.markdown(
        f"""
        <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 20px; font-family: monospace; font-size: 13px; color: {THEME["text_primary"]}; line-height: 1.8;'>
            <span style='color: {THEME["accent_primary"]};'>[1. Video Source]</span> (Highway MP4 / CCTV / Drone / Webcam)<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[2. YOLOv8 Inference]</span> ➔ Bounding Boxes, Confidence Scores, COCO Class Filter<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[3. ByteTrack Tracker]</span> ➔ Persistent ID Assignment & Centroid History Queue<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[4. Kinematic Analysis]</span> ➔ Direction Vectors, Tripwire Intersection, Sluggish Speed Detection<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[5. Safety & Density Audit]</span> ➔ Wrong-Way Violation Flagging & Density Regime Classification<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[6. Relational Persistence]</span> ➔ SQLite3 Logging (traffic_events & traffic_statistics)<br>
            &nbsp;&nbsp;&nbsp;&nbsp;│<br>
            &nbsp;&nbsp;&nbsp;&nbsp;▼<br>
            <span style='color: {THEME["accent_primary"]};'>[7. Command Center UI]</span> ➔ Streamlit Dashboard, Telemetry HUD, Plotly Analytics, PDF Reports
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style='text-align: center; margin-top: 24px; padding: 16px; color: {THEME["text_secondary"]}; font-size: 12px; border-top: 1px solid {THEME["border"]};'>
            Developed as an AI/ML Computer Vision Project • Intelligent Transportation System
        </div>
        """,
        unsafe_allow_html=True,
    )
