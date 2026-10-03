"""
Top Header Bar Component for AI Traffic Command Center.
"""

from __future__ import annotations
import streamlit as st
from dashboard.styles import THEME


def render_top_header(
    system_status: str = "ONLINE",
    device_name: str = "CPU",
    model_name: str = "yolov8n.pt",
) -> None:
    """Render the command-center top header banner."""
    is_online = system_status.upper() == "ONLINE"
    dot_class = "status-dot-green" if is_online else "status-dot-red"
    badge_style = "status-badge-online" if is_online else "status-badge-online"

    st.markdown(
        f"""
        <div class='cc-header-container'>
            <div class='cc-header-left'>
                <div class='cc-header-logo'>🚦</div>
                <div>
                    <h1 class='cc-header-title'>AI TRAFFIC COMMAND CENTER</h1>
                    <div class='cc-header-subtitle'>Intelligent Traffic Monitoring & Violation Detection System</div>
                </div>
            </div>
            <div class='cc-header-right'>
                <span class='{badge_style}'>
                    <span class='{dot_class}'></span> SYSTEM {system_status.upper()}
                </span>
                <span class='hardware-chip'>⚡ YOLOv8</span>
                <span class='hardware-chip'>👁️ OpenCV</span>
                <span class='hardware-chip'>📊 AI Analytics</span>
                <span class='hardware-chip'>💾 SQLite</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
