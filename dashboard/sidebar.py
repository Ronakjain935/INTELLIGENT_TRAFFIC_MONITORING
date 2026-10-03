"""
Custom Sidebar Navigation & System Controls for AI Traffic Command Center.
"""

from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import render_system_status
from src.utils import get_device


PAGES = [
    "▣ Dashboard",
    "🎥 Live Monitoring",
    "📊 Analytics",
    "⚠️ Events",
    "📄 Reports",
    "⚙️ Settings",
    "ℹ️ About",
]


def render_sidebar(config: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Render command-center sidebar navigation and runtime controls.
    Returns:
        selected_page: The active navigation page name.
        runtime_overrides: Dictionary of modified parameters.
    """
    st.sidebar.markdown(
        f"""
        <div style='display: flex; align-items: center; gap: 12px; padding: 12px 6px; margin-bottom: 8px;'>
            <div style='font-size: 32px;'>🚦</div>
            <div>
                <div style='font-size: 14px; font-weight: 800; color: {THEME["text_primary"]}; letter-spacing: 0.6px; text-transform: uppercase;'>
                    AI TRAFFIC
                </div>
                <div style='font-size: 11px; font-weight: 600; color: {THEME["accent_primary"]}; letter-spacing: 0.8px;'>
                    COMMAND CENTER
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown(f"<hr style='margin: 4px 0 12px 0; border-color: {THEME['border']};'>", unsafe_allow_html=True)

    # Navigation section
    st.sidebar.markdown(
        f"<div style='font-size: 11px; font-weight: 700; color: {THEME['text_secondary']}; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;'>NAVIGATION</div>",
        unsafe_allow_html=True,
    )

    default_page_idx = 0
    if "current_page" in st.session_state and st.session_state.current_page in PAGES:
        default_page_idx = PAGES.index(st.session_state.current_page)

    selected_page = st.sidebar.radio(
        "Select Operation View",
        PAGES,
        index=default_page_idx,
        label_visibility="collapsed",
        key="sidebar_navigation_radio",
    )
    st.session_state.current_page = selected_page

    st.sidebar.markdown(f"<hr style='margin: 16px 0 12px 0; border-color: {THEME['border']};'>", unsafe_allow_html=True)

    # Runtime Quick Config
    with st.sidebar.expander("⚙️ Quick Stream Controls", expanded=False):
        # Model weights
        available_models = ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
        models_dir = Path("models")
        if models_dir.exists():
            for ext in ("*.pt", "*.onnx", "*.engine"):
                for p in models_dir.glob(f"**/{ext}"):
                    posix_path = str(p).replace("\\", "/")
                    if posix_path not in available_models and p.name not in available_models:
                        available_models.append(posix_path)

        curr_model = config.get("model", {}).get("name", "yolov8n.pt")
        if curr_model not in available_models:
            available_models.insert(0, curr_model)

        selected_model = st.selectbox(
            "AI Model Weights",
            available_models,
            index=available_models.index(curr_model) if curr_model in available_models else 0,
        )

        conf_threshold = st.slider(
            "Confidence Threshold",
            0.10, 1.00, float(config.get("model", {}).get("confidence", 0.40)), 0.05
        )

        iou_threshold = st.slider(
            "IoU Threshold",
            0.10, 1.00, float(config.get("model", {}).get("iou", 0.50)), 0.05
        )

        traffic_dir = st.selectbox(
            "Authorized Traffic Flow",
            ["RIGHT", "LEFT", "DOWN", "UP"],
            index=["RIGHT", "LEFT", "DOWN", "UP"].index(config.get("traffic", {}).get("expected_direction", "RIGHT")),
        )

        frame_skip = st.select_slider(
            "Processing Frame Skip",
            options=[1, 2, 3],
            value=int(config.get("processing", {}).get("frame_skip", 1)),
            help="1 = Full accuracy; 2 = Every 2nd frame (faster inference for CPU)",
        )

    # Live Streaming Action Bar in Sidebar
    st.sidebar.markdown(
        f"<div style='font-size: 11px; font-weight: 700; color: {THEME['text_secondary']}; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 6px;'>SURVEILLANCE ENGINE</div>",
        unsafe_allow_html=True,
    )

    c_start, c_stop = st.sidebar.columns(2)
    start_click = c_start.button("▶ START", type="primary", use_container_width=True, key="sb_start_btn")
    stop_click = c_stop.button("⏹ STOP", use_container_width=True, key="sb_stop_btn")

    if start_click:
        st.session_state.is_running = True
    if stop_click:
        st.session_state.is_running = False

    # Status indicator in sidebar
    model_disp = Path(selected_model).name
    dev_str = get_device(config.get("model", {}).get("device", "auto")).upper()
    render_system_status(
        model_status="ONLINE" if st.session_state.get("is_running") else "READY",
        video_status="STREAMING" if st.session_state.get("is_running") else "STANDBY",
        tracker_status="READY",
        db_status="CONNECTED",
        analytics_status="ACTIVE",
    )

    st.sidebar.markdown(
        f"""
        <div style='font-size: 10px; color: {THEME["text_secondary"]}; text-align: center; margin-top: 16px;'>
            Hardware: <code>{dev_str}</code> | Model: <code>{model_disp}</code>
        </div>
        """,
        unsafe_allow_html=True,
    )

    overrides = {
        "model_name": selected_model,
        "confidence": conf_threshold,
        "iou": iou_threshold,
        "expected_direction": traffic_dir,
        "frame_skip": frame_skip,
    }
    return selected_page, overrides
