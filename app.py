"""
AI-Based Intelligent Traffic Monitoring and Violation Detection System
Streamlit Production Dashboard Application.
"""

from __future__ import annotations

import os
import tempfile
import time
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
    /* Global Reset & Dark Theme */
    html, body, [data-testid="stAppViewContainer"], .main {
        background-color: #0B0F17 !important;
        color: #F8FAFC !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Prevent Sidebar White Strip / Border Glitches */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1E293B !important;
    }
    section[data-testid="stSidebar"] > div {
        background-color: #111827 !important;
    }
    [data-testid="collapsedControl"] {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-radius: 0 8px 8px 0;
        border: 1px solid #334155;
    }

    /* Sleek Translucent Header */
    header[data-testid="stHeader"] {
        background-color: rgba(11, 15, 23, 0.85) !important;
        backdrop-filter: blur(10px);
        border-bottom: 1px solid #1E293B;
    }

    /* High-Contrast Streamlit Metric Cards */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #182030 0%, #111827 100%) !important;
        border: 1px solid #283548 !important;
        border-radius: 12px !important;
        padding: 14px 18px !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35) !important;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    [data-testid="stMetric"]:hover {
        border-color: #00D2D3 !important;
        transform: translateY(-2px);
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #94A3B8 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.6px !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 26px !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        white-space: normal !important;
        word-break: break-word !important;
    }
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
        font-size: 12px !important;
    }

    /* Executive KPI Cards (Tab 4 & Custom Dashboards) */
    .executive-kpi-card {
        background: linear-gradient(135deg, #182030 0%, #111827 100%);
        border: 1px solid #283548;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 14px;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35);
        transition: border-color 0.2s ease, transform 0.2s ease;
    }
    .executive-kpi-card:hover {
        border-color: #00D2D3;
        transform: translateY(-2px);
    }
    .kpi-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
    }
    .kpi-icon {
        font-size: 18px;
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 700;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.6px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1.2;
        margin-bottom: 6px;
        white-space: normal;
        word-break: break-word;
    }
    .kpi-footer {
        font-size: 12px;
        color: #64748B;
    }

    /* Action & Export Module Cards */
    .action-card {
        background: linear-gradient(135deg, #182030 0%, #111827 100%);
        border: 1px solid #283548;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    /* Modern Buttons & Download Buttons */
    div.stButton > button, div.stDownloadButton > button {
        background: linear-gradient(135deg, #1E293B 0%, #151D2A 100%) !important;
        color: #F8FAFC !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
        border-color: #38BDF8 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 14px rgba(2, 132, 199, 0.4) !important;
        transform: translateY(-1px);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #00D2D3 0%, #00A8A9 100%) !important;
        color: #0B0F17 !important;
        border: none !important;
        font-weight: 700 !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #20E3E4 0%, #00BFBF 100%) !important;
        box-shadow: 0 4px 14px rgba(0, 210, 211, 0.45) !important;
    }

    /* Tabs Styling - 100% Width Equal Distribution (Never overflow or scroll off) */
    div[data-baseweb="tab-list"] {
        background-color: #111827 !important;
        border-radius: 12px 12px 0 0 !important;
        padding: 6px !important;
        border-bottom: 2px solid #283548 !important;
        display: flex !important;
        width: 100% !important;
        gap: 6px !important;
    }
    button[data-baseweb="tab"] {
        flex: 1 1 0 !important;
        text-align: center !important;
        background-color: transparent !important;
        border: none !important;
        padding: 12px 6px !important;
        border-radius: 8px !important;
        min-width: 0 !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"] * {
        font-size: 15px !important;
        font-weight: 600 !important;
        color: #E2E8F0 !important; /* Crisp silver white for all inactive tabs */
    }
    button[data-baseweb="tab"]:hover * {
        color: #FFFFFF !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(0, 210, 211, 0.16) !important;
        border-bottom: 3px solid #00F2FE !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] * {
        color: #00F2FE !important; /* Glowing cyan for active tab */
        font-weight: 700 !important;
    }

    /* Header Badges & Hardware Chips - Never Split or Wrap Words */
    .header-badges-container {
        display: flex !important;
        flex-wrap: wrap !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 8px !important;
        padding-top: 14px !important;
    }
    .status-badge-ok, .status-badge-warn, .status-badge-danger {
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 6px 14px !important;
        border-radius: 20px !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
    }
    .status-badge-ok {
        background: linear-gradient(135deg, #059669 0%, #10B981 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(16, 185, 129, 0.35) !important;
    }
    .status-badge-warn {
        background: linear-gradient(135deg, #D97706 0%, #F59E0B 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(245, 158, 11, 0.35) !important;
    }
    .status-badge-danger {
        background: linear-gradient(135deg, #DC2626 0%, #EF4444 100%) !important;
        color: #FFFFFF !important;
        box-shadow: 0 2px 8px rgba(239, 68, 68, 0.35) !important;
    }
    .hardware-chip {
        white-space: nowrap !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        background-color: #1A2234 !important;
        border: 1px solid #2B3A52 !important;
        color: #38BDF8 !important;
        padding: 6px 12px !important;
        border-radius: 8px !important;
        font-size: 12px !important;
        font-family: 'JetBrains Mono', Consolas, monospace !important;
        font-weight: 600 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
    }
    .alert-banner {
        background: linear-gradient(135deg, #7F1D1D 0%, #991B1B 100%);
        border: 2px solid #EF4444;
        color: #FFFFFF;
        padding: 14px 20px;
        border-radius: 10px;
        font-weight: bold;
        margin-bottom: 14px;
        box-shadow: 0 4px 16px rgba(239, 68, 68, 0.3);
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
        # Save uploaded file to temp directory for OpenCV processing
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}")
        tfile.write(uploaded_file.read())
        video_source_path = tfile.name
elif input_option == "Sample Video":
    sample_path = "data/input/sample_traffic.mp4"
    if os.path.exists(sample_path):
        video_source_path = sample_path
    else:
        st.sidebar.warning("Sample video not found locally. Please upload a video.")
elif input_option == "Webcam":
    is_webcam = True
    webcam_index = st.sidebar.number_input("Camera Index", min_value=0, max_value=5, value=0, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Detection & Tracking Settings")

# Model weights selector
available_models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
models_dir = Path("models")
if models_dir.exists():
    for ext in ("*.pt", "*.onnx", "*.engine"):
        for p in models_dir.glob(f"**/{ext}"):
            posix_path = str(p).replace("\\", "/")
            if posix_path not in available_models and p.name not in available_models:
                available_models.append(posix_path)

current_cfg_model = st.session_state.config.get("model", {}).get("name", "yolov8n.pt")
if current_cfg_model not in available_models:
    available_models.insert(0, current_cfg_model)

selected_model = st.sidebar.selectbox(
    "AI Model Weights",
    available_models,
    index=available_models.index(current_cfg_model) if current_cfg_model in available_models else 0,
    help="Select lightweight Nano for maximum FPS/CPU, or Small/Medium/ONNX for enhanced performance.",
)

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
col_start, col_stop = st.sidebar.columns(2)
start_clicked = col_start.button("▶ Start", type="primary", use_container_width=True)
stop_clicked = col_stop.button("⏹ Stop", use_container_width=True)

if start_clicked:
    st.session_state.is_running = True
if stop_clicked:
    st.session_state.is_running = False

# Update runtime configurations
st.session_state.config["model"]["name"] = selected_model
st.session_state.config["model"]["confidence"] = conf_threshold
st.session_state.config["model"]["iou"] = iou_threshold
st.session_state.config["traffic"]["expected_direction"] = traffic_direction
st.session_state.config["wrong_way"]["enabled"] = enable_wrong_way
st.session_state.config["counting"]["line_ratio_y"] = counting_line_ratio
st.session_state.config["processing"]["frame_skip"] = frame_skip

# 5. Top Header & Hardware Badge
device_str = get_device(st.session_state.config.get("model", {}).get("device", "auto"))
hcol1, hcol2 = st.columns([2.0, 1.4])
with hcol1:
    st.title("🚦 Intelligent Traffic Monitoring")
    st.caption("AI Surveillance: Multi-Object Tracking, Line Counting & Wrong-Way Safety Auditing")
with hcol2:
    status_class = "status-badge-ok" if st.session_state.is_running else "status-badge-warn"
    status_label = "STREAMING ACTIVE" if st.session_state.is_running else "MONITORING IDLE"
    model_display = Path(selected_model).name
    st.markdown(
        f"""
        <div class='header-badges-container'>
            <span class='{status_class}'>● {status_label}</span>
            <span class='hardware-chip'>⚡ DEVICE: {device_str.upper()}</span>
            <span class='hardware-chip'>🧠 MODEL: {model_display}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<hr style='margin-top: 5px; margin-bottom: 15px;'>", unsafe_allow_html=True)

# 6. Top KPI Metric Cards
kpi_placeholder = st.empty()
with kpi_placeholder.container():
    render_kpi_metrics(st.session_state.latest_stats)

# 7. Navigation Tabs - Equal Width & Clean High-Contrast Labels
tab_live, tab_charts, tab_violations, tab_reports = st.tabs(
    ["🎥 Live Stream", "📊 Analytics", "⚠️ Violations", "📑 Reports & Export"]
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
                try:
                    annotated_bgr, telemetry = processor.process_frame(frame)
                except Exception as exc:
                    st.error(f"⚠️ Inference Error with model '{selected_model}': {exc}")
                    st.session_state.is_running = False
                    break
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
        with feed_col:
            st.markdown(
                """
                <div style='background: linear-gradient(135deg, #182030 0%, #111827 100%); border: 1px solid #283548; border-radius: 12px; padding: 22px; margin-bottom: 16px;'>
                    <div style='display: flex; align-items: center; justify-content: space-between;'>
                        <div>
                            <h3 style='color: #F8FAFC; margin: 0;'>🎥 Video Surveillance Engine (Ready)</h3>
                            <p style='color: #94A3B8; margin: 4px 0 0 0; font-size: 14px;'>
                                Select your video source below (Upload Video, Live Webcam, or Sample Video) and launch processing.
                            </p>
                        </div>
                        <span class='status-badge-ok'>SYSTEM READY</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # In-Panel Video Source Selector
            c_src1, c_src2 = st.columns([1, 1.5])
            with c_src1:
                in_tab_source = st.radio(
                    "Choose Video Feed Source:",
                    ("🎬 Sample Highway Video", "📁 Upload Video File", "📷 Live Webcam"),
                    index=0 if input_option == "Sample Video" else (1 if input_option == "Upload Video" else 2),
                    key="in_tab_source_radio",
                )

            with c_src2:
                if in_tab_source == "📁 Upload Video File":
                    panel_file = st.file_uploader(
                        "Upload Traffic Video (MP4, AVI, MOV)",
                        type=["mp4", "avi", "mov", "mkv"],
                        key="panel_uploader",
                        help="Upload traffic footage from CCTV, drone, or highway camera",
                    )
                    if panel_file is not None:
                        tfile2 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{panel_file.name}")
                        tfile2.write(panel_file.read())
                        video_source_path = tfile2.name
                        st.success(f"✅ Video ready: `{panel_file.name}`")
                elif in_tab_source == "📷 Live Webcam":
                    panel_cam_idx = st.number_input("Camera Index", min_value=0, max_value=5, value=0, step=1, key="panel_cam_idx")
                    is_webcam = True
                    webcam_index = panel_cam_idx
                    st.info("📹 Ready to capture live camera feed.")
                else:
                    sample_path = "data/input/sample_traffic.mp4"
                    if os.path.exists(sample_path):
                        video_source_path = sample_path
                        st.info("🎬 Preloaded highway traffic footage ready.")
                    else:
                        st.warning("⚠️ Sample video file not found locally. Please use Upload Video.")

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            col_launch, _ = st.columns([1.2, 1])
            with col_launch:
                if st.button("▶ Start AI Surveillance Processing", type="primary", use_container_width=True, key="live_start_btn"):
                    st.session_state.is_running = True
                    st.rerun()

            st.markdown(
                """
                <div style='background: #111827; border: 1px solid #1E293B; border-radius: 10px; padding: 16px; margin-top: 16px;'>
                    <div style='font-weight: 700; color: #F8FAFC; margin-bottom: 10px;'>🔍 Visual Detection Legend & Tripwire Guide:</div>
                    <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; font-size: 13px;'>
                        <div style='color: #10B981;'>🟩 <b>Green Box & ID:</b> Tracked vehicle classified by YOLOv8 + ByteTrack.</div>
                        <div style='color: #38BDF8;'>🟦 <b>Blue Motion Trail:</b> Directional velocity & movement trajectory vector.</div>
                        <div style='color: #FBBF24;'>🟨 <b>Yellow Tripwire:</b> Counting boundary (tallies direction & volume).</div>
                        <div style='color: #EF4444;'>🟥 <b>Red Alert Flash:</b> Wrong-Way infraction against authorized flow.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ----------------- TAB 2: ANALYTICS & VISUALIZATIONS -----------------
with tab_charts:
    col_t2_head, col_t2_ref = st.columns([4, 1])
    with col_t2_head:
        st.subheader("📊 Real-Time Traffic Analytics Dashboard")
        st.caption("Interactive visual charts tracking classification breakdown, surge timelines, directional vectors, and road density.")
    with col_t2_ref:
        if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_analytics_btn"):
            st.rerun()

    stats_df = st.session_state.db.get_statistics_history(limit=100)
    events_df = st.session_state.db.get_recent_events(limit=300)
    summary_data = TrafficStatistics.compute_summary(events_df, stats_df)

    # Use logged historical summary if available, or current live stats
    active_pie_stats = summary_data if summary_data.get("total_vehicles", 0) > 0 else st.session_state.latest_stats

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(
            create_vehicle_distribution_chart(active_pie_stats),
            use_container_width=True,
        )
        st.info("💡 **Chart 1 — Vehicle Classification:** Shows the proportion and count of each vehicle category (Cars, Motorcycles, Buses, Trucks, Bicycles, Pedestrians) detected on the road.")

    with g2:
        st.plotly_chart(
            create_traffic_over_time_chart(stats_df),
            use_container_width=True,
        )
        st.info("💡 **Chart 2 — Traffic Timeline:** The cyan line tracks total active vehicles over time to highlight peak rush hours. The dashed red line marks safety infractions (wrong-way driving).")

    g3, g4 = st.columns(2)
    with g3:
        st.plotly_chart(
            create_direction_chart(summary_data["directional_split"]),
            use_container_width=True,
        )
        st.info("💡 **Chart 3 — Directional Flow:** Counts how many vehicles travelled in each cardinal direction (Right, Left, Up, Down) across the virtual detection boundary.")

    with g4:
        st.plotly_chart(
            create_density_gauge(
                st.session_state.latest_stats.get("density_level", "LOW"),
                st.session_state.latest_stats.get("active_vehicles", 0),
            ),
            use_container_width=True,
        )
        st.info("💡 **Chart 4 — Road Occupancy Gauge:** Real-time speedometer of road congestion. 🟢 Low (0-20 cars), 🟠 Moderate (20-45 cars), 🔴 High Congestion (45+ cars).")

# ----------------- TAB 3: VIOLATIONS & SAFETY LOG -----------------
with tab_violations:
    col_vhead, col_vref = st.columns([4, 1])
    with col_vhead:
        st.subheader("⚠️ Safety Violations & Wrong-Way Audit Log")
        st.caption("Automated audit log identifying vehicles travelling against designated traffic flow directions.")
    with col_vref:
        if st.button("🔄 Refresh Log", use_container_width=True, key="refresh_violations_btn"):
            st.rerun()

    violations_df = st.session_state.db.get_violations(limit=200)

    # Top KPI Cards for Tab 3
    total_viol = len(violations_df) if violations_df is not None else 0
    top_viol_class = (
        violations_df["vehicle_type"].mode().iloc[0].capitalize()
        if (violations_df is not None and not violations_df.empty and "vehicle_type" in violations_df.columns)
        else "None"
    )

    vk1, vk2, vk3 = st.columns(3)
    with vk1:
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'><span class='kpi-icon'>🚨</span><span class='kpi-title'>Total Violations Logged</span></div>
                <div class='kpi-value' style='color: {"#EF4444" if total_viol > 0 else "#10B981"};'>{total_viol}</div>
                <div class='kpi-footer'>Wrong-way crossing incidents recorded</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with vk2:
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'><span class='kpi-icon'>🚗</span><span class='kpi-title'>Frequent Offender Class</span></div>
                <div class='kpi-value' style='color: #F59E0B;'>{top_viol_class}</div>
                <div class='kpi-footer'>Vehicle category with most infractions</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with vk3:
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'><span class='kpi-icon'>🧭</span><span class='kpi-title'>Authorized Direction</span></div>
                <div class='kpi-value' style='color: #38BDF8;'>{traffic_direction}</div>
                <div class='kpi-footer'>Opposite flow triggers automatic alert</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Search & Filter Controls
    if violations_df is not None and not violations_df.empty:
        col_vf1, col_vf2 = st.columns([1, 1])
        with col_vf1:
            unique_classes = ["All"] + sorted([str(x).capitalize() for x in violations_df["vehicle_type"].dropna().unique().tolist()])
            filter_class = st.selectbox("Filter by Vehicle Type", unique_classes, index=0)
        with col_vf2:
            min_conf = st.slider("Minimum Confidence Threshold", 0.0, 1.0, 0.25, 0.05)

        filtered_df = violations_df.copy()
        if filter_class != "All":
            filtered_df = filtered_df[filtered_df["vehicle_type"].str.lower() == filter_class.lower()]
        filtered_df = filtered_df[filtered_df["confidence"] >= min_conf]

        st.markdown(f"**Showing {len(filtered_df)} of {len(violations_df)} logged violations:**")
        st.dataframe(
            filtered_df[["id", "vehicle_id", "vehicle_type", "direction", "confidence", "timestamp"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.markdown(
            """
            <div style='background: #111827; border: 1px solid #1E293B; border-radius: 12px; padding: 24px; text-align: center; margin-top: 14px;'>
                <div style='font-size: 36px; margin-bottom: 8px;'>✅</div>
                <h4 style='color: #10B981; margin-bottom: 6px;'>Zero Violations Recorded</h4>
                <p style='color: #94A3B8; font-size: 13px; max-width: 480px; margin: 0 auto;'>
                    All detected vehicles are currently adhering to the designated flow direction. Any counter-flow movements will be recorded and audited here in real-time.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ----------------- TAB 4: AUDIT REPORTS & DATA EXPORT -----------------
with tab_reports:
    st.subheader("📑 Automated Traffic Audit Reports")
    st.caption("Review aggregated system performance, violation summaries, and generate official compliance documents.")

    all_events_df = st.session_state.db.get_recent_events(limit=500)
    stats_history_df = st.session_state.db.get_statistics_history(limit=200)
    audit_summary = TrafficStatistics.compute_summary(all_events_df, stats_history_df)

    st.markdown("### 📊 Executive Summary Metrics")

    # 6 Modern High-Contrast KPI Cards
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>🚗</span>
                    <span class='kpi-title'>Total Counted Vehicles</span>
                </div>
                <div class='kpi-value'>{audit_summary.get('total_vehicles', 0)}</div>
                <div class='kpi-footer'>Cumulative crossing volume logged</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>⚡</span>
                    <span class='kpi-title'>Flow Rate Throughput</span>
                </div>
                <div class='kpi-value'>{audit_summary.get('vehicles_per_min', 0.0)} <span style='font-size:16px;color:#94A3B8;'>veh/min</span></div>
                <div class='kpi-footer'>Mean vehicle detection cadence</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        viol_count = audit_summary.get("wrong_way_violations", 0)
        viol_badge = "status-badge-danger" if viol_count > 0 else "status-badge-ok"
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>⚠️</span>
                    <span class='kpi-title'>Wrong-Way Violations</span>
                </div>
                <div class='kpi-value' style='color: {"#EF4444" if viol_count > 0 else "#10B981"};'>{viol_count}</div>
                <div class='kpi-footer'><span class='{viol_badge}'>{'Critical Attention Needed' if viol_count > 0 else 'Zero Infractions'}</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>🏆</span>
                    <span class='kpi-title'>Dominant Vehicle Class</span>
                </div>
                <div class='kpi-value' style='color: #38BDF8;'>{audit_summary.get('most_frequent_class', 'N/A')}</div>
                <div class='kpi-footer'>Most prevalent transport category</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        peak_text = audit_summary.get("peak_period", "N/A")
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>⏱️</span>
                    <span class='kpi-title'>Peak Traffic Window</span>
                </div>
                <div class='kpi-value' style='font-size: 21px; word-break: break-word;'>{peak_text}</div>
                <div class='kpi-footer'>Busiest hourly interval detected</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        cong_status = audit_summary.get("congestion_summary", "NORMAL")
        cong_badge = "status-badge-ok" if cong_status == "NORMAL" else ("status-badge-warn" if cong_status == "MODERATE" else "status-badge-danger")
        st.markdown(
            f"""
            <div class='executive-kpi-card'>
                <div class='kpi-header'>
                    <span class='kpi-icon'>🚦</span>
                    <span class='kpi-title'>Predominant Road State</span>
                </div>
                <div class='kpi-value'><span class='{cong_badge}'>{cong_status}</span></div>
                <div class='kpi-footer'>Aggregate highway density regime</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Searchable recent events preview
    with st.expander("🔍 Preview Recent 10 Crossing Events (Data Inspection)", expanded=False):
        if all_events_df is not None and not all_events_df.empty:
            st.dataframe(
                all_events_df.head(10)[["id", "vehicle_id", "vehicle_type", "direction", "confidence", "timestamp"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No recorded vehicle crossing events logged yet.")

    st.markdown("<hr style='margin: 20px 0; border-color: #283548;'>", unsafe_allow_html=True)
    st.markdown("### 📥 Generate & Export Audit Reports")

    col_csv, col_pdf, col_clear = st.columns(3)

    # 1. CSV Report Download
    with col_csv:
        st.markdown(
            """
            <div class='action-card'>
                <div style='font-size: 16px; font-weight: bold; color: #F8FAFC;'>📊 CSV Event Stream</div>
                <div style='font-size: 13px; color: #94A3B8; margin-top: 6px; margin-bottom: 14px;'>Download raw tabular log of every crossing event, tracking ID, timestamp, and confidence.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        csv_data = generate_csv_report(all_events_df)
        st.download_button(
            label="📥 Download CSV Report",
            data=csv_data,
            file_name=f"traffic_events_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    # 2. PDF Report Download
    with col_pdf:
        st.markdown(
            """
            <div class='action-card'>
                <div style='font-size: 16px; font-weight: bold; color: #F8FAFC;'>📄 Official PDF Audit</div>
                <div style='font-size: 13px; color: #94A3B8; margin-top: 6px; margin-bottom: 14px;'>Compile an executive PDF report complete with violation logs, distribution tables, and timestamps.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        violations_for_pdf = st.session_state.db.get_violations(limit=50)
        try:
            pdf_bytes = generate_pdf_report(audit_summary, violations_for_pdf)
            st.download_button(
                label="📄 Download PDF Audit",
                data=pdf_bytes,
                file_name=f"traffic_audit_{time.strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"PDF generation error: {e}")

    # 3. Database Purge / Reset Button
    with col_clear:
        st.markdown(
            """
            <div class='action-card'>
                <div style='font-size: 16px; font-weight: bold; color: #EF4444;'>🗑️ Purge Records</div>
                <div style='font-size: 13px; color: #94A3B8; margin-top: 6px; margin-bottom: 14px;'>Clear local SQLite database tables to reset vehicle counts, timeline stats, and audit logs.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🗑️ Reset Database Records", use_container_width=True):
            st.session_state.db.clear_all()
            st.success("Database records cleared successfully.")
            st.rerun()
