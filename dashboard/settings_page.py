"""
System Configuration & Hyperparameters Page.
Displays and safely manages runtime parameters sourced from config.yaml.
"""

from __future__ import annotations
from typing import Dict, Any
import yaml
import streamlit as st

from dashboard.styles import THEME
from dashboard.components import render_section_header


def render_settings_page(config: Dict[str, Any]) -> None:
    """Render the configuration settings management interface."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>System Configuration</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    Active hyperparameters and algorithm configurations loaded from <code>config.yaml</code>
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='hardware-chip'>⚙️ CONFIG.YAML</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div style='background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 12px 16px; margin-bottom: 20px;'>
            <div style='font-size: 13px; color: {THEME["accent_primary"]}; font-weight: 600;'>
                ℹ Configuration loaded from <code>config.yaml</code>
            </div>
            <div style='font-size: 12px; color: {THEME["text_secondary"]}; margin-top: 2px;'>
                Parameters adjusted below will update the active session state. You can also persist these changes back to the root configuration file.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:
        # 1. AI Model Section
        render_section_header("🧠 AI Vision Model", "Ultralytics YOLOv8 detector parameters")
        model_name = st.selectbox(
            "YOLO Model Architecture",
            ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"],
            index=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"].index(config.get("model", {}).get("name", "yolov8n.pt"))
            if config.get("model", {}).get("name", "yolov8n.pt") in ["yolov8n.pt", "yolov8s.pt", "yolov8m.pt"]
            else 0,
        )
        conf_thresh = st.slider(
            "Confidence Threshold",
            0.10, 1.00, float(config.get("model", {}).get("confidence", 0.40)), 0.05
        )
        iou_thresh = st.slider(
            "IoU NMS Threshold",
            0.10, 1.00, float(config.get("model", {}).get("iou", 0.50)), 0.05
        )
        device_opt = st.selectbox(
            "Target Device Acceleration",
            ["auto", "cpu", "cuda"],
            index=["auto", "cpu", "cuda"].index(config.get("model", {}).get("device", "auto")),
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 2. Traffic Flow & Tripwire
        render_section_header("🚦 Traffic Rules & Tripwire", "Virtual counting boundary geometry")
        expected_dir = st.selectbox(
            "Authorized Traffic Flow Direction",
            ["RIGHT", "LEFT", "DOWN", "UP"],
            index=["RIGHT", "LEFT", "DOWN", "UP"].index(config.get("traffic", {}).get("expected_direction", "RIGHT")),
        )
        line_ratio_y = st.slider(
            "Counting Line Vertical Ratio (Y-axis)",
            0.20, 0.85, float(config.get("counting", {}).get("line_ratio_y", 0.55)), 0.05,
            help="Position of the tripwire as a fraction of frame height",
        )
        line_offset = st.number_input(
            "Tripwire Pixel Buffer Offset",
            5, 30, int(config.get("counting", {}).get("line_offset", 12)), 1,
        )

    with c2:
        # 3. Density & Congestion Section
        render_section_header("📊 Traffic Density & Congestion", "Regime thresholds and velocity monitoring")
        low_thresh = st.number_input(
            "Low Density Vehicle Threshold (≤)",
            5, 50, int(config.get("density", {}).get("low", 20)), 5,
        )
        med_thresh = st.number_input(
            "Medium Density Vehicle Threshold (≤)",
            20, 150, int(config.get("density", {}).get("medium", 50)), 5,
        )
        speed_thresh = st.number_input(
            "Sluggish Flow Speed Threshold (px/frame)",
            1.0, 20.0, float(config.get("congestion", {}).get("speed_threshold_px", 4.0)), 0.5,
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 4. Wrong-Way Infraction Detection
        render_section_header("⚠️ Wrong-Way Detection Engine", "Vector analysis and trigger thresholds")
        wrong_way_enabled = st.checkbox(
            "Enable Wrong-Way Violation Detection",
            value=bool(config.get("wrong_way", {}).get("enabled", True)),
        )
        min_mov = st.number_input(
            "Minimum Movement Vector Length (pixels)",
            5, 50, int(config.get("wrong_way", {}).get("minimum_movement_pixels", 15)), 1,
        )
        confirm_frames = st.number_input(
            "Confirmation Consecutive Frames",
            2, 20, int(config.get("wrong_way", {}).get("confirmation_frames", 5)), 1,
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # 5. Pipeline Performance
        render_section_header("⚡ Processing Pipeline", "Resolution and HUD overlays")
        frame_skip = st.select_slider(
            "Inference Frame Skip",
            options=[1, 2, 3],
            value=int(config.get("processing", {}).get("frame_skip", 1)),
        )
        resize_w = st.number_input(
            "Processing Frame Width (px)",
            640, 1920, int(config.get("processing", {}).get("resize_width", 1280)), 160,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Save button
    col_save, _ = st.columns([1.5, 2])
    with col_save:
        if st.button("💾 SAVE CONFIGURATION TO CONFIG.YAML", type="primary", use_container_width=True):
            config["model"]["name"] = model_name
            config["model"]["confidence"] = conf_thresh
            config["model"]["iou"] = iou_thresh
            config["model"]["device"] = device_opt
            config["traffic"]["expected_direction"] = expected_dir
            config["counting"]["line_ratio_y"] = line_ratio_y
            config["counting"]["line_offset"] = line_offset
            config["density"]["low"] = low_thresh
            config["density"]["medium"] = med_thresh
            config["congestion"]["speed_threshold_px"] = speed_thresh
            config["wrong_way"]["enabled"] = wrong_way_enabled
            config["wrong_way"]["minimum_movement_pixels"] = min_mov
            config["wrong_way"]["confirmation_frames"] = confirm_frames
            config["processing"]["frame_skip"] = frame_skip
            config["processing"]["resize_width"] = resize_w

            try:
                with open("config.yaml", "w", encoding="utf-8") as f:
                    yaml.safe_dump(config, f, default_flow_style=False)
                st.success("✅ Configuration saved to config.yaml successfully.")
            except Exception as e:
                st.error(f"Error saving config: {e}")
