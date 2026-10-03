"""
AI-Based Intelligent Traffic Monitoring and Violation Detection System.
Professional AI Traffic Command Center Production Dashboard.
"""

from __future__ import annotations

import os
from pathlib import Path
import streamlit as st

from src.utils import load_config, get_device
from src.database import DatabaseManager, TrafficDatabase
from src.detector import VehicleDetector
from src.tracker import VehicleTracker, SimpleCentroidTracker
from src.counter import VehicleCounter
from src.traffic_analyzer import TrafficAnalyzer
from src.wrong_way_detector import DirectionAndWrongWayDetector, WrongWayDetector
from src.statistics import TrafficStatistics, summarize_events
from src.video_processor import VideoProcessor

from dashboard.styles import apply_custom_css
from dashboard.header import render_top_header
from dashboard.sidebar import render_sidebar
from dashboard.dashboard_page import render_dashboard_page
from dashboard.monitoring_page import render_monitoring_page
from dashboard.analytics_page import render_analytics_page
from dashboard.events_page import render_events_page
from dashboard.reports_page import render_reports_page
from dashboard.settings_page import render_settings_page
from dashboard.about_page import render_about_page


# 1. Page Configuration
st.set_page_config(
    page_title="AI Traffic Command Center | Intelligent Traffic Monitoring",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Command Center Design System CSS
apply_custom_css()

# 3. Initialize Persistent Session States
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

# 4. Render Command Center Sidebar & Controls
selected_page, overrides = render_sidebar(st.session_state.config)

# Update runtime configurations from sidebar overrides
if overrides:
    st.session_state.config["model"]["name"] = overrides.get("model_name", st.session_state.config["model"]["name"])
    st.session_state.config["model"]["confidence"] = overrides.get("confidence", st.session_state.config["model"]["confidence"])
    st.session_state.config["model"]["iou"] = overrides.get("iou", st.session_state.config["model"]["iou"])
    st.session_state.config["traffic"]["expected_direction"] = overrides.get("expected_direction", st.session_state.config["traffic"]["expected_direction"])
    st.session_state.config["processing"]["frame_skip"] = overrides.get("frame_skip", st.session_state.config["processing"]["frame_skip"])

# 5. Render Command Center Header Bar
system_status_label = "STREAMING" if st.session_state.is_running else "ONLINE"
device_str = get_device(st.session_state.config.get("model", {}).get("device", "auto")).upper()
model_file = Path(st.session_state.config.get("model", {}).get("name", "yolov8n.pt")).name

render_top_header(
    system_status=system_status_label,
    device_name=device_str,
    model_name=model_file,
)

# 6. Page Router Dispatcher
try:
    if selected_page == "▣ Dashboard":
        render_dashboard_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
            latest_stats=st.session_state.latest_stats,
        )
    elif selected_page == "🎥 Live Monitoring":
        render_monitoring_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
        )
    elif selected_page == "📊 Analytics":
        render_analytics_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
            latest_stats=st.session_state.latest_stats,
        )
    elif selected_page == "⚠️ Events":
        render_events_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
        )
    elif selected_page == "📄 Reports":
        render_reports_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
        )
    elif selected_page == "⚙️ Settings":
        render_settings_page(
            config=st.session_state.config,
        )
    elif selected_page == "ℹ️ About":
        render_about_page()
    else:
        render_dashboard_page(
            config=st.session_state.config,
            db_manager=st.session_state.db,
            latest_stats=st.session_state.latest_stats,
        )
except Exception as e:
    st.markdown(
        f"""
        <div style='background: rgba(239, 68, 68, 0.15); border: 2px solid #EF4444; border-radius: 10px; padding: 20px; margin-top: 16px;'>
            <div style='font-size: 18px; font-weight: 800; color: #FFFFFF; margin-bottom: 8px;'>
                ⚠ SYSTEM OPERATION NOTICE
            </div>
            <div style='font-size: 14px; color: #FECACA; margin-bottom: 12px;'>
                An unexpected event occurred while rendering the command center view.
            </div>
            <div style='font-size: 12px; color: #94A3B8;'>
                Please verify video file integrity, database connection, and configuration parameters.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander("Technical Diagnostic Details"):
        st.exception(e)
