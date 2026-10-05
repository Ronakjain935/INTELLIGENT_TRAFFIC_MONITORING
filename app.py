"""
AI-Based Intelligent Traffic Monitoring and Violation Detection System
Streamlit Production Dashboard Application.
"""

from __future__ import annotations

import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import cv2
import pandas as pd
import streamlit as st

from src.utils import load_config, get_device
from src.database import DatabaseManager
from src.video_processor import VideoProcessor
from src.statistics import TrafficStatistics
from dashboard.components import (
    render_kpi_metrics,
    create_vehicle_distribution_chart,
    create_traffic_over_time_chart,
    create_direction_chart,
    create_density_gauge,
    generate_csv_report,
    generate_pdf_report,
)

# 1. Page Configuration
st.set_page_config(
    page_title="AI Intelligent Traffic Monitoring System",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Custom CSS styling for modern, high-contrast traffic operations center UI
st.markdown(
    """
    <style>
    .main {
        background-color: #0E1117;
    }
    .metric-card {
        background: #1A1F2C;
        border: 1px solid #2D3748;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .status-badge-ok {
        background-color: #27AE60;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .status-badge-warn {
        background-color: #E67E22;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .status-badge-danger {
        background-color: #C0392B;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 13px;
        font-weight: bold;
    }
    .hardware-chip {
        background-color: #2B3A4A;
        color: #64B5F6;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-family: monospace;
    }
    .alert-banner {
        background-color: #7B1113;
        border: 2px solid #E74C3C;
        color: #FFFFFF;
        padding: 12px 18px;
        border-radius: 8px;
        font-weight: bold;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# 3. Initialize Session States
if "config" not in st.session_state:
    st.session_state.config = load_config("config.yaml")

if "db" not in st.session_state:
    db_path = st.session_state.config.get("storage", {}).get("database_path", "data/traffic_system.db")
    st.session_state.db = DatabaseManager(db_path)

if "is_running" not in st.session_state:
    st.session_state.is_running = False

if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if "active_source_id" not in st.session_state:
    st.session_state.active_source_id = None

if "active_source_name" not in st.session_state:
    st.session_state.active_source_name = "Sample Video"

if "latest_stats" not in st.session_state:
    st.session_state.latest_stats = {
        "fps": 0.0,
        "active_vehicles": 0,
        "density_level": "LOW",
        "congestion_level": "NORMAL",
        "average_speed_px": 0.0,
        "total_counted": 0,
        "cars": 0,
        "motorcycles": 0,
        "buses": 0,
        "trucks": 0,
        "bicycles": 0,
        "pedestrians": 0,
        "wrong_way_count": 0,
        "active_violations": [],
    }

# 4. Sidebar Controls
st.sidebar.image("https://img.icons8.com/color/96/traffic-light.png", width=64)
st.sidebar.title("AI Traffic Monitoring")
st.sidebar.caption("Intelligent Surveillance & Safety Auditing")

st.sidebar.markdown("---")
st.sidebar.subheader("🎥 Input Configuration")

input_option = st.sidebar.radio(
    "Select Video Source",
    ("Sample Video", "Upload Video", "Webcam"),
    index=0,
)

uploaded_file = None
video_source_path: Optional[str] = None
is_webcam = False

if input_option == "Upload Video":
    uploaded_file = st.sidebar.file_uploader(
        "Choose a traffic video file",
        type=["mp4", "avi", "mov", "mkv"],
        help="Upload standard MP4, AVI, MOV, or MKV files",
    )
    if uploaded_file is not None:
        file_key = f"upload_{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.active_source_id != file_key:
            st.session_state.active_source_id = file_key
            st.session_state.active_source_name = uploaded_file.name
            st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.latest_stats = {
                "fps": 0.0,
                "active_vehicles": 0,
                "density_level": "LOW",
                "congestion_level": "NORMAL",
                "average_speed_px": 0.0,
                "total_counted": 0,
                "cars": 0,
                "motorcycles": 0,
                "buses": 0,
                "trucks": 0,
                "bicycles": 0,
                "pedestrians": 0,
                "wrong_way_count": 0,
                "active_violations": [],
            }
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}")
        tfile.write(uploaded_file.read())
        video_source_path = tfile.name
elif input_option == "Sample Video":
    sample_path = "data/input/sample_traffic.mp4"
    if st.session_state.active_source_id != "sample_video":
        st.session_state.active_source_id = "sample_video"
        st.session_state.active_source_name = "sample_traffic.mp4"
        st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if os.path.exists(sample_path):
        video_source_path = sample_path
    else:
        st.sidebar.warning("Sample video not found locally. Please upload a video.")
elif input_option == "Webcam":
    is_webcam = True
    if st.session_state.active_source_id != "webcam":
        st.session_state.active_source_id = "webcam"
        st.session_state.active_source_name = "Live Webcam"
        st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    webcam_index = st.sidebar.number_input("Camera Index", min_value=0, max_value=5, value=0, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Detection & Tracking Settings")

conf_threshold = st.sidebar.slider(
    "Confidence Threshold",
    min_value=0.10,
    max_value=1.00,
    value=float(st.session_state.config.get("model", {}).get("confidence", 0.40)),
    step=0.05,
    help="Higher values reduce false positives; lower values detect distant vehicles.",
)

iou_threshold = st.sidebar.slider(
    "IoU Threshold",
    min_value=0.10,
    max_value=1.00,
    value=float(st.session_state.config.get("model", {}).get("iou", 0.50)),
    step=0.05,
    help="Non-Maximum Suppression threshold for overlapping bounding boxes.",
)

traffic_direction = st.sidebar.selectbox(
    "Authorized Traffic Direction",
    ["RIGHT", "LEFT", "DOWN", "UP"],
    index=["RIGHT", "LEFT", "DOWN", "UP"].index(
        st.session_state.config.get("traffic", {}).get("expected_direction", "RIGHT")
    ),
    help="Designated flow direction for wrong-way violation detection.",
)

enable_wrong_way = st.sidebar.checkbox(
    "Enable Wrong-Way Detection",
    value=bool(st.session_state.config.get("wrong_way", {}).get("enabled", True)),
)

counting_line_ratio = st.sidebar.slider(
    "Counting Line Height Ratio",
    min_value=0.20,
    max_value=0.85,
    value=float(st.session_state.config.get("counting", {}).get("line_ratio_y", 0.55)),
    step=0.05,
    help="Vertical position of virtual tripwire line (0.2=top, 0.8=bottom).",
)

frame_skip = st.sidebar.select_slider(
    "Processing Frame Skip",
    options=[1, 2, 3],
    value=int(st.session_state.config.get("processing", {}).get("frame_skip", 1)),
    help="1 = Full frame-by-frame; 2 = Every 2nd frame (2x faster for CPU).",
)

st.sidebar.markdown("---")
st.sidebar.subheader("📊 Analytics Scope & Session")
data_scope = st.sidebar.radio(
    "Analytics Data Filter",
    ("Current Video / Active Session", "All Stored History"),
    index=0,
    help="Switch between viewing only metrics for the current uploaded video, or all past records stored in the database.",
)

col_rst, col_purge = st.sidebar.columns(2)
if col_rst.button("🔄 Reset Session", use_container_width=True, help="Clear in-memory session counts"):
    st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.latest_stats = {
        "fps": 0.0,
        "active_vehicles": 0,
        "density_level": "LOW",
        "congestion_level": "NORMAL",
        "average_speed_px": 0.0,
        "total_counted": 0,
        "cars": 0,
        "motorcycles": 0,
        "buses": 0,
        "trucks": 0,
        "bicycles": 0,
        "pedestrians": 0,
        "wrong_way_count": 0,
        "active_violations": [],
    }
    st.rerun()

if col_purge.button("🗑️ Clear DB", use_container_width=True, help="Purge all old historical database records"):
    st.session_state.db.clear_all()
    st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.rerun()

st.sidebar.markdown("---")
col_start, col_stop = st.sidebar.columns(2)
start_clicked = col_start.button("▶ Start", type="primary", use_container_width=True)
stop_clicked = col_stop.button("⏹ Stop", use_container_width=True)

if start_clicked:
    st.session_state.is_running = True
    if not st.session_state.get("session_start_time"):
        st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
if stop_clicked:
    st.session_state.is_running = False

# Update runtime configurations
st.session_state.config["model"]["confidence"] = conf_threshold
st.session_state.config["model"]["iou"] = iou_threshold
st.session_state.config["traffic"]["expected_direction"] = traffic_direction
st.session_state.config["wrong_way"]["enabled"] = enable_wrong_way
st.session_state.config["counting"]["line_ratio_y"] = counting_line_ratio
st.session_state.config["processing"]["frame_skip"] = frame_skip

# 5. Top Header & Hardware Badge
device_str = get_device(st.session_state.config.get("model", {}).get("device", "auto"))
hcol1, hcol2 = st.columns([3, 1])
with hcol1:
    st.title("🚦 Intelligent Traffic Monitoring & Violation System")
    st.caption("Real-Time Multi-Object Tracking, Line Counting, Density Estimation & Wrong-Way Detection")
with hcol2:
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    status_class = "status-badge-ok" if st.session_state.is_running else "status-badge-warn"
    status_label = "STREAMING ACTIVE" if st.session_state.is_running else "MONITORING IDLE"
    st.markdown(
        f"<span class='{status_class}'>● {status_label}</span> <span class='hardware-chip'>DEVICE: {device_str.upper()}</span>",
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# 6. Top KPI Metric Cards
kpi_placeholder = st.empty()
with kpi_placeholder.container():
    render_kpi_metrics(st.session_state.latest_stats)

# 7. Navigation Tabs
tab_live, tab_charts, tab_violations, tab_reports = st.tabs(
    ["🎥 Live Surveillance", "📊 Traffic Analytics", "⚠️ Violations & Alerts", "📑 Audit Reports & Export"]
)

# ----------------- TAB 1: LIVE SURVEILLANCE FEED -----------------
with tab_live:
    feed_col, telemetry_col = st.columns([2.5, 1])

    with feed_col:
        video_placeholder = st.empty()
        alert_placeholder = st.empty()

    with telemetry_col:
        st.subheader("Telemetry Status")
        density_metric_ph = st.empty()
        congestion_metric_ph = st.empty()
        speed_metric_ph = st.empty()
        fps_metric_ph = st.empty()

    # If stream running, loop through frames
    if st.session_state.is_running:
        processor = VideoProcessor(st.session_state.config, db_manager=st.session_state.db)

        # Open video source
        cap = None
        if is_webcam:
            cap = cv2.VideoCapture(int(webcam_index))
            if not cap.isOpened():
                st.error("⚠️ Webcam is unavailable or permission denied. Please upload a traffic video instead.")
                st.session_state.is_running = False
        else:
            if video_source_path and os.path.isfile(video_source_path):
                cap = cv2.VideoCapture(video_source_path)
            else:
                st.warning("⚠️ No valid video source selected. Please upload a video or select 'Sample Video'.")
                st.session_state.is_running = False

        if cap is not None and cap.isOpened():
            frame_counter = 0
            while st.session_state.is_running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    # If video reached end, loop sample or terminate
                    if not is_webcam:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        break

                frame_counter += 1
                if frame_skip > 1 and (frame_counter % frame_skip != 0):
                    continue

                # Run AI pipeline
                annotated_bgr, telemetry = processor.process_frame(frame)
                st.session_state.latest_stats = telemetry

                # Display video frame
                frame_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                # Active Violations Alert
                if telemetry.get("active_violations"):
                    alert_placeholder.markdown(
                        f"""
                        <div class='alert-banner'>
                            🚨 <b>WRONG-WAY ALERT DETECTED:</b> Vehicle ID(s) {telemetry['active_violations']} travelling against authorized {traffic_direction} flow!
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    alert_placeholder.empty()

                # Update live telemetry chips
                with kpi_placeholder.container():
                    render_kpi_metrics(telemetry)

                dens = telemetry.get("density_level", "LOW")
                dens_color = "status-badge-ok" if dens == "LOW" else ("status-badge-warn" if dens == "MEDIUM" else "status-badge-danger")
                density_metric_ph.markdown(
                    f"**Traffic Density:** <span class='{dens_color}'>{dens}</span> ({telemetry.get('active_vehicles', 0)} active)",
                    unsafe_allow_html=True,
                )

                cong = telemetry.get("congestion_level", "NORMAL")
                cong_color = "status-badge-ok" if cong == "NORMAL" else ("status-badge-warn" if cong == "MODERATE" else "status-badge-danger")
                congestion_metric_ph.markdown(
                    f"**Congestion State:** <span class='{cong_color}'>{cong}</span>",
                    unsafe_allow_html=True,
                )

                speed_metric_ph.markdown(f"**Mean Pixel Velocity:** `{telemetry.get('average_speed_px', 0.0)} px/frame`")
                fps_metric_ph.markdown(f"**Pipeline Throughput:** `{telemetry.get('fps', 0.0)} FPS`")

                # Small sleep to yield to Streamlit event loop
                time.sleep(0.01)

            cap.release()
    else:
        video_placeholder.info("ℹ️ Monitoring is currently IDLE. Click '▶ Start' in the sidebar to begin processing traffic stream.")

# ----------------- TAB 2: ANALYTICS & VISUALIZATIONS -----------------
with tab_charts:
    st.subheader("Real-Time Analytics Dashboard")

    since_ts = st.session_state.session_start_time if data_scope == "Current Video / Active Session" else None
    source_name = st.session_state.get("active_source_name", "Current Video")

    if data_scope == "Current Video / Active Session":
        st.info(f"📊 **Active Scope:** Showing metrics for `{source_name}` (Session started: `{st.session_state.session_start_time}`). Switch to 'All Stored History' in the sidebar to view all-time records.")
    else:
        st.info("🌐 **Active Scope:** Showing cumulative historical records across all video sessions in the database.")

    stats_df = st.session_state.db.get_statistics_history(limit=100, since_timestamp=since_ts)
    events_df = st.session_state.db.get_recent_events(limit=300, since_timestamp=since_ts)
    summary_data = TrafficStatistics.compute_summary(events_df, stats_df)

    g1, g2 = st.columns(2)
    with g1:
        # Use summary_data from line crossings / detected events, fallback to live telemetry
        donut_data = summary_data if summary_data.get("total_vehicles", 0) > 0 else st.session_state.latest_stats
        st.plotly_chart(
            create_vehicle_distribution_chart(donut_data),
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
        active_cnt = st.session_state.latest_stats.get("active_vehicles", 0)
        dens_lvl = st.session_state.latest_stats.get("density_level") if st.session_state.is_running else summary_data.get("congestion_summary", "LOW")
        st.plotly_chart(
            create_density_gauge(
                dens_lvl,
                active_cnt,
            ),
            use_container_width=True,
        )

# ----------------- TAB 3: VIOLATIONS & SAFETY LOG -----------------
with tab_violations:
    st.subheader("⚠️ Safety Violations & Wrong-Way Audit Log")
    since_ts = st.session_state.session_start_time if data_scope == "Current Video / Active Session" else None
    violations_df = st.session_state.db.get_violations(limit=100, since_timestamp=since_ts)

    if violations_df is not None and not violations_df.empty:
        st.dataframe(
            violations_df[["id", "vehicle_id", "vehicle_type", "direction", "confidence", "timestamp"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.success("✅ No wrong-way violations logged for this session.")

# ----------------- TAB 4: AUDIT REPORTS & DATA EXPORT -----------------
with tab_reports:
    st.subheader("📑 Automated Traffic Audit Reports")
    since_ts = st.session_state.session_start_time if data_scope == "Current Video / Active Session" else None

    all_events_df = st.session_state.db.get_recent_events(limit=500, since_timestamp=since_ts)
    stats_history_df = st.session_state.db.get_statistics_history(limit=200, since_timestamp=since_ts)
    audit_summary = TrafficStatistics.compute_summary(all_events_df, stats_history_df)

    st.markdown("### Executive Summary Metrics")
    c_sum1, c_sum2, c_sum3 = st.columns(3)
    c_sum1.metric("Total Counted Vehicles", audit_summary.get("total_vehicles", 0))
    c_sum1.metric("Flow Rate", f"{audit_summary.get('vehicles_per_min', 0.0)} veh/min")

    c_sum2.metric("Wrong-Way Violations", audit_summary.get("wrong_way_violations", 0))
    c_sum2.metric("Dominant Class", audit_summary.get("most_frequent_class", "N/A"))

    c_sum3.metric("Peak Period Window", audit_summary.get("peak_period", "N/A"))
    c_sum3.metric("Predominant State", audit_summary.get("congestion_summary", "NORMAL"))

    st.markdown("---")
    st.subheader("Generate & Download Reports")

    col_csv, col_pdf, col_clear = st.columns(3)

    # 1. CSV Report Download
    with col_csv:
        csv_data = generate_csv_report(all_events_df)
        st.download_button(
            label="📥 Download CSV Event Report",
            data=csv_data,
            file_name=f"traffic_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 2. PDF Report Download
    with col_pdf:
        violations_for_pdf = st.session_state.db.get_violations(limit=50, since_timestamp=since_ts)
        try:
            pdf_bytes = generate_pdf_report(audit_summary, violations_for_pdf)
            st.download_button(
                label="📄 Download Formal PDF Audit Report",
                data=pdf_bytes,
                file_name=f"traffic_audit_report_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    # 3. Database Purge / Reset Button
    with col_clear:
        if st.button("🗑️ Reset Database Records", use_container_width=True):
            st.session_state.db.clear_all()
            st.session_state.session_start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.success("Database records cleared successfully.")
            st.rerun()

