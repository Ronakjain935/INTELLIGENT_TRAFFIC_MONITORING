"""
Live Video Monitoring and AI Surveillance Execution Page.
Handles video stream ingestion, live YOLOv8 inference, ByteTrack updates,
wrong-way violation triggers, and telemetry telemetry dashboards.
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

from dashboard.styles import THEME
from dashboard.components import (
    render_section_header,
    render_vehicle_type_card,
    render_alert_card,
)
from src.video_processor import VideoProcessor


def render_monitoring_page(
    config: Dict[str, Any],
    db_manager: Any,
) -> None:
    """Render the dedicated Live Traffic Video Monitoring page."""
    st.markdown(
        f"""
        <div style='display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px;'>
            <div>
                <h2 style='margin: 0; font-size: 24px; font-weight: 800; color: {THEME["text_primary"]};'>LIVE TRAFFIC MONITOR</h2>
                <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-top: 3px;'>
                    AI-powered vehicle detection, multi-object tracking, and automated safety auditing
                </div>
            </div>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <span class='status-badge-online'>
                    <span class='{"status-dot-green" if st.session_state.get("is_running") else "status-dot-red"}'></span>
                    {"SURVEILLANCE ACTIVE" if st.session_state.get("is_running") else "SYSTEM STANDBY"}
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    feed_col, telemetry_col = st.columns([2.5, 1.0])

    with feed_col:
        video_placeholder = st.empty()
        telemetry_strip_ph = st.empty()
        alert_placeholder = st.empty()

    with telemetry_col:
        render_section_header("Live Telemetry", "Real-time stream telemetry", badge="METRICS")
        active_veh_ph = st.empty()
        density_ph = st.empty()
        congestion_ph = st.empty()
        speed_ph = st.empty()
        fps_ph = st.empty()

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
        render_section_header("Active Modal Split", "Vehicles tracked in current session")
        modal_split_ph = st.empty()

    # Video Source Setup Container (when stream is stopped)
    if not st.session_state.get("is_running", False):
        with feed_col:
            st.markdown(
                f"""
                <div class='upload-panel'>
                    <div style='font-size: 36px; margin-bottom: 8px;'>🎥</div>
                    <div style='font-size: 18px; font-weight: 700; color: {THEME["text_primary"]}; margin-bottom: 4px;'>
                        UPLOAD TRAFFIC VIDEO FEED
                    </div>
                    <div style='font-size: 13px; color: {THEME["text_secondary"]}; margin-bottom: 14px;'>
                        MP4 • AVI • MOV • MKV (HD / Full HD / 4K Traffic Footage)
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            c_type1, c_type2 = st.columns([1, 1.6])
            with c_type1:
                source_choice = st.radio(
                    "Choose Video Feed Source:",
                    ("🎬 Preloaded Highway Footage", "📁 Upload Video File", "📷 Live Camera Index"),
                    key="monitoring_source_radio",
                )

            selected_video_path: Optional[str] = None
            is_camera = False
            cam_idx = 0

            with c_type2:
                if source_choice == "📁 Upload Video File":
                    uploaded_file = st.file_uploader(
                        "Browse or Drag & Drop Traffic Video",
                        type=["mp4", "avi", "mov", "mkv"],
                        key="monitoring_file_uploader",
                    )
                    if uploaded_file is not None:
                        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}")
                        tfile.write(uploaded_file.read())
                        selected_video_path = tfile.name
                        st.session_state["video_source_path"] = selected_video_path
                        st.session_state["uploaded_file_name"] = uploaded_file.name

                        # Probe resolution
                        cap_probe = cv2.VideoCapture(selected_video_path)
                        probe_w = int(cap_probe.get(cv2.CAP_PROP_FRAME_WIDTH))
                        probe_h = int(cap_probe.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        probe_fps = cap_probe.get(cv2.CAP_PROP_FPS) or 25.0
                        cap_probe.release()

                        st.markdown(
                            f"""
                            <div style='background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34, 197, 94, 0.4); border-radius: 8px; padding: 12px 16px; margin-top: 8px;'>
                                <div style='color: #4ADE80; font-weight: 700; font-size: 13px;'>✓ VIDEO READY FOR PROCESSING</div>
                                <div style='font-size: 12px; color: {THEME["text_primary"]}; margin-top: 4px;'><b>File:</b> {uploaded_file.name}</div>
                                <div style='font-size: 11px; color: {THEME["text_secondary"]}; font-family: monospace;'>Resolution: {probe_w} × {probe_h} | FPS: {probe_fps:.1f} | Format: {uploaded_file.type}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                elif source_choice == "📷 Live Camera Index":
                    cam_idx = st.number_input("Hardware Device Index", 0, 5, 0, 1, key="mon_cam_idx")
                    is_camera = True
                    st.session_state["is_webcam"] = True
                    st.session_state["webcam_index"] = cam_idx
                    st.info(f"Ready to ingest live feed from Camera Device #{cam_idx}")
                else:
                    sample_path = "data/input/sample_traffic.mp4"
                    if os.path.exists(sample_path):
                        selected_video_path = sample_path
                        st.session_state["video_source_path"] = sample_path
                        st.session_state["uploaded_file_name"] = "sample_traffic.mp4"
                        st.markdown(
                            f"""
                            <div style='background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 12px 16px; margin-top: 8px;'>
                                <div style='color: #38BDF8; font-weight: 700; font-size: 13px;'>✓ PRELOADED HIGHWAY FOOTAGE READY</div>
                                <div style='font-size: 12px; color: {THEME["text_primary"]}; margin-top: 4px;'><b>Dataset:</b> Multilane Highway Sample Video</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        st.warning("Sample video file not found locally. Please upload a traffic video.")

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            col_btn, _ = st.columns([1.5, 1])
            with col_btn:
                if st.button("▶ START AI SURVEILLANCE ANALYSIS", type="primary", use_container_width=True, key="mon_start_btn"):
                    st.session_state.is_running = True
                    st.rerun()

            st.markdown(
                f"""
                <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 14px; margin-top: 14px;'>
                    <div style='font-size: 12px; font-weight: 700; color: {THEME["text_primary"]}; margin-bottom: 8px;'>🔍 VISUAL DETECTION OVERLAY GUIDE:</div>
                    <div style='display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; font-size: 12px;'>
                        <div style='color: #22C55E;'>🟩 <b>Green Box & ID:</b> Tracked vehicle classified by YOLOv8</div>
                        <div style='color: #38BDF8;'>🟦 <b>Blue Trail:</b> Directional trajectory vector</div>
                        <div style='color: #F59E0B;'>🟨 <b>Yellow Tripwire:</b> Virtual counting & direction boundary</div>
                        <div style='color: #EF4444;'>🟥 <b>Red Flash:</b> Wrong-Way violation against authorized flow</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Initial render of telemetry panel
        curr_stats = st.session_state.get("latest_stats", {})
        active_veh_ph.markdown(f"**Active Vehicles:** `{curr_stats.get('active_vehicles', 0)}`")
        density_ph.markdown(f"**Traffic Density:** `{curr_stats.get('density_level', 'LOW')}`")
        congestion_ph.markdown(f"**Congestion:** `{curr_stats.get('congestion_level', 'NORMAL')}`")
        speed_ph.markdown(f"**Mean Velocity:** `{curr_stats.get('average_speed_px', 0.0)} px/f`")
        fps_ph.markdown(f"**Pipeline FPS:** `{curr_stats.get('fps', 0.0)}`")

    # ------------------ VIDEO PROCESSING LOOP ------------------
    if st.session_state.get("is_running", False):
        video_path = st.session_state.get("video_source_path", "data/input/sample_traffic.mp4")
        is_webcam = st.session_state.get("is_webcam", False)
        webcam_idx = st.session_state.get("webcam_index", 0)

        # Initialize processor
        processor = VideoProcessor(config, db_manager=db_manager)

        cap = None
        if is_webcam:
            cap = cv2.VideoCapture(int(webcam_idx))
            if not cap.isOpened():
                st.error("⚠️ Webcam device is unavailable. Please upload a traffic video.")
                st.session_state.is_running = False
        else:
            if video_path and os.path.isfile(video_path):
                cap = cv2.VideoCapture(video_path)
            else:
                st.warning("⚠️ No valid video file found. Please upload a video.")
                st.session_state.is_running = False

        if cap is not None and cap.isOpened():
            frame_skip = int(config.get("processing", {}).get("frame_skip", 1))
            traffic_dir = config.get("traffic", {}).get("expected_direction", "RIGHT")
            frame_counter = 0

            while st.session_state.get("is_running", False):
                ret, frame = cap.read()
                if not ret or frame is None:
                    if not is_webcam:
                        # Loop video seamlessly
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        ret, frame = cap.read()
                        if not ret:
                            break
                    else:
                        break

                frame_counter += 1
                if frame_skip > 1 and (frame_counter % frame_skip != 0):
                    continue

                try:
                    annotated_bgr, telemetry = processor.process_frame(frame)
                except Exception as exc:
                    st.error(f"⚠️ Inference Error: {exc}")
                    st.session_state.is_running = False
                    break

                st.session_state.latest_stats = telemetry

                # Display processed frame
                frame_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
                video_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

                # Bottom telemetry strip
                dens = telemetry.get("density_level", "LOW")
                d_color = THEME["success"] if dens == "LOW" else (THEME["warning"] if dens == "MEDIUM" else THEME["danger"])
                viol_count = telemetry.get("wrong_way_count", 0)
                v_color = THEME["danger"] if viol_count > 0 else THEME["success"]

                telemetry_strip_ph.markdown(
                    f"""
                    <div class='telemetry-bar'>
                        <div class='telemetry-item'>
                            <div class='telemetry-label'>Pipeline FPS</div>
                            <div class='telemetry-val' style='color: {THEME["accent_primary"]};'>{telemetry.get("fps", 0.0)}</div>
                        </div>
                        <div class='telemetry-item'>
                            <div class='telemetry-label'>Active Vehicles</div>
                            <div class='telemetry-val'>{telemetry.get("active_vehicles", 0)}</div>
                        </div>
                        <div class='telemetry-item'>
                            <div class='telemetry-label'>Density Regime</div>
                            <div class='telemetry-val' style='color: {d_color};'>{dens}</div>
                        </div>
                        <div class='telemetry-item'>
                            <div class='telemetry-label'>Total Tallied</div>
                            <div class='telemetry-val'>{telemetry.get("total_counted", 0)}</div>
                        </div>
                        <div class='telemetry-item'>
                            <div class='telemetry-label'>Wrong-Way Violations</div>
                            <div class='telemetry-val' style='color: {v_color};'>{viol_count}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # Wrong-Way Alert Banner
                if telemetry.get("active_violations"):
                    alert_placeholder.markdown(
                        f"""
                        <div class='wrong-way-alert'>
                            <div class='wrong-way-alert-title'>
                                <span class='status-dot-red'></span>
                                🚨 ACTIVE WRONG-WAY INFRACTION DETECTED!
                            </div>
                            <div style='font-size: 13px; color: #FFFFFF;'>
                                Vehicle ID(s) <b>{telemetry['active_violations']}</b> traveling contrary to authorized <b>{traffic_dir}</b> flow direction. Event logged to database.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    alert_placeholder.empty()

                # Right column telemetry updates
                active_veh_ph.markdown(f"**Active Vehicles:** `{telemetry.get('active_vehicles', 0)}`")
                density_ph.markdown(f"**Traffic Density:** <span style='color: {d_color}; font-weight: bold;'>{dens}</span>", unsafe_allow_html=True)
                cong = telemetry.get("congestion_level", "NORMAL")
                c_color = THEME["success"] if cong == "NORMAL" else (THEME["warning"] if cong == "MODERATE" else THEME["danger"])
                congestion_ph.markdown(f"**Congestion:** <span style='color: {c_color}; font-weight: bold;'>{cong}</span>", unsafe_allow_html=True)
                speed_ph.markdown(f"**Mean Velocity:** `{telemetry.get('average_speed_px', 0.0)} px/frame`")
                fps_ph.markdown(f"**Pipeline Throughput:** `{telemetry.get('fps', 0.0)} FPS`")

                # Modal Split Breakdown
                tot = max(1, telemetry.get("total_counted", 1))
                cars = telemetry.get("cars", 0)
                motorcycles = telemetry.get("motorcycles", 0)
                buses = telemetry.get("buses", 0)
                trucks = telemetry.get("trucks", 0)

                with modal_split_ph.container():
                    render_vehicle_type_card("Cars", cars, (cars / tot) * 100, "🚗", "#22C55E")
                    render_vehicle_type_card("Motorcycles", motorcycles, (motorcycles / tot) * 100, "🏍️", "#38BDF8")
                    render_vehicle_type_card("Buses", buses, (buses / tot) * 100, "🚌", "#F59E0B")
                    render_vehicle_type_card("Trucks", trucks, (trucks / tot) * 100, "🚛", "#F97316")

                time.sleep(0.01)

            cap.release()
