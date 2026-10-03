"""
Dashboard UI Components, Reusable Widgets, Plotly Visualizations, and Report Generators.
Includes command-center KPI cards, traffic status panels, telemetry strips, distribution charts,
time-series graphs, and export modules for CSV and PDF reports.
"""

from __future__ import annotations

import io
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from dashboard.styles import THEME


# Plotly Command Center Theme Palette
CHART_THEME = {
    "car": "#22C55E",         # Success green
    "motorcycle": "#38BDF8",  # Sky cyan
    "bus": "#F59E0B",         # Amber gold
    "truck": "#F97316",       # Bright orange
    "bicycle": "#A855F7",     # Purple
    "person": "#06B6D4",      # Cyan
    "wrong_way": "#EF4444",   # Crimson red
    "bg_card": THEME["bg_card"],
    "border": THEME["border"],
    "text": THEME["text_primary"],
    "subtext": THEME["text_secondary"],
}


def render_kpi_card(
    title: str,
    value: Any,
    subtitle: Optional[str] = None,
    icon: Optional[str] = None,
    delta: Optional[str] = None,
    status_color: Optional[str] = None,
) -> None:
    """Render a modern command-center KPI metric card."""
    icon_html = f"<span class='metric-card-icon'>{icon}</span>" if icon else ""
    delta_color = status_color or THEME["accent_primary"]
    delta_html = f"<div class='metric-card-delta' style='color: {delta_color};'>{delta}</div>" if delta else ""
    sub_html = f"<div style='font-size: 11px; color: {THEME['text_secondary']}; margin-top: 4px;'>{subtitle}</div>" if subtitle else ""
    val_color = status_color if status_color else THEME["text_primary"]

    st.markdown(
        f"""
        <div class='metric-card'>
            <div class='metric-card-top'>
                <span class='metric-card-title'>{title}</span>
                {icon_html}
            </div>
            <div class='metric-card-value' style='color: {val_color};'>{value}</div>
            {delta_html}
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_metrics(stats: Dict[str, Any]) -> None:
    """Render the 4 top-level command center KPI cards with real data."""
    c1, c2, c3, c4 = st.columns(4)

    total_val = stats.get("total_counted", stats.get("total_vehicles", 0))
    active_val = stats.get("active_vehicles", 0)
    viol_val = stats.get("wrong_way_count", stats.get("wrong_way_violations", 0))
    density_val = str(stats.get("density_level", "LOW")).upper()

    with c1:
        render_kpi_card(
            title="TOTAL VEHICLES",
            value=f"{total_val:,}" if isinstance(total_val, (int, float)) and total_val > 0 else "0",
            icon="🚦",
            delta=f"Cars: {stats.get('cars', 0)} | Bikes: {stats.get('motorcycles', 0)}",
            status_color=THEME["accent_primary"],
        )

    with c2:
        render_kpi_card(
            title="ACTIVE VEHICLES",
            value=f"{active_val:,}" if isinstance(active_val, (int, float)) else "0",
            icon="🚗",
            delta="● LIVE ON-SCREEN" if active_val > 0 else "IDLE",
            status_color=THEME["success"] if active_val > 0 else THEME["text_secondary"],
        )

    with c3:
        viol_color = THEME["danger"] if viol_val > 0 else THEME["success"]
        render_kpi_card(
            title="WRONG-WAY ALERTS",
            value=f"{viol_val:02d}" if isinstance(viol_val, int) else "00",
            icon="⚠️",
            delta="⚠ ATTENTION REQUIRED" if viol_val > 0 else "✓ NORMAL / SECURE",
            status_color=viol_color,
        )

    with c4:
        d_color = THEME["success"] if density_val == "LOW" else (THEME["warning"] if density_val == "MEDIUM" else THEME["danger"])
        cong = stats.get("congestion_level", "NORMAL")
        render_kpi_card(
            title="TRAFFIC DENSITY",
            value=density_val,
            icon="📊",
            delta=f"● {cong} FLOW",
            status_color=d_color,
        )


def render_status_card(
    density: str,
    active_count: int,
    congestion_status: str,
    expected_direction: str = "RIGHT",
    average_speed_px: float = 0.0,
) -> None:
    """Render a large, professional traffic status card."""
    dens = (density or "LOW").upper()
    pill_class = "status-low" if dens == "LOW" else ("status-medium" if dens == "MEDIUM" else "status-high")
    cong_color = THEME["success"] if congestion_status == "NORMAL" else (THEME["warning"] if congestion_status == "MODERATE" else THEME["danger"])

    st.markdown(
        f"""
        <div class='traffic-status-card'>
            <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;'>
                <div>
                    <div style='font-size: 12px; font-weight: 700; color: {THEME["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.8px;'>
                        CURRENT TRAFFIC REGIME
                    </div>
                    <div style='font-size: 26px; font-weight: 800; color: {THEME["text_primary"]}; margin-top: 4px;'>
                        ROAD STATUS
                    </div>
                </div>
                <span class='traffic-status-pill {pill_class}'>{dens} DENSITY</span>
            </div>

            <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 14px;'>
                <div style='background: {THEME["bg_secondary"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 12px 14px;'>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]}; text-transform: uppercase;'>Active Vehicles</div>
                    <div style='font-size: 22px; font-weight: 800; color: {THEME["accent_primary"]};'>{active_count}</div>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]};'>Tracked in camera frame</div>
                </div>
                <div style='background: {THEME["bg_secondary"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 12px 14px;'>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]}; text-transform: uppercase;'>Congestion State</div>
                    <div style='font-size: 22px; font-weight: 800; color: {cong_color};'>{congestion_status}</div>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]};'>Velocity: {average_speed_px:.1f} px/f</div>
                </div>
                <div style='background: {THEME["bg_secondary"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 12px 14px;'>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]}; text-transform: uppercase;'>Designated Flow</div>
                    <div style='font-size: 22px; font-weight: 800; color: #38BDF8;'>{expected_direction} ➔</div>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]};'>Authorized lane direction</div>
                </div>
                <div style='background: {THEME["bg_secondary"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 12px 14px;'>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]}; text-transform: uppercase;'>Safety Audit</div>
                    <div style='font-size: 22px; font-weight: 800; color: {THEME["success"]};'>ENFORCING</div>
                    <div style='font-size: 11px; color: {THEME["text_secondary"]};'>Real-time tripwire active</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_card(violation: Dict[str, Any]) -> None:
    """Render a prominent red wrong-way alert card."""
    vid = violation.get("vehicle_id", "N/A")
    vtype = str(violation.get("vehicle_type", "Vehicle")).capitalize()
    vdir = violation.get("direction", "N/A")
    exp_dir = violation.get("expected_direction", "RIGHT")
    conf = float(violation.get("confidence", 0.94)) * 100
    ts = violation.get("timestamp", "Just now")

    st.markdown(
        f"""
        <div class='wrong-way-alert'>
            <div class='wrong-way-alert-title'>
                <span class='status-dot-red'></span>
                ⚠ WRONG-WAY VEHICLE DETECTED
                <span style='margin-left: auto; font-size: 12px; background: rgba(239, 68, 68, 0.35); padding: 3px 10px; border-radius: 4px; font-family: monospace;'>
                    STATUS: CRITICAL
                </span>
            </div>
            <div class='wrong-way-alert-grid'>
                <div><b>Vehicle ID:</b> #{vid}</div>
                <div><b>Type:</b> {vtype}</div>
                <div><b>Detected Flow:</b> <span style='color: #EF4444; font-weight: bold;'>{vdir}</span></div>
                <div><b>Authorized:</b> {exp_dir}</div>
                <div><b>Confidence:</b> {conf:.1f}%</div>
                <div><b>Timestamp:</b> {ts}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: Optional[str] = None, badge: Optional[str] = None) -> None:
    """Render a clean command-center section header."""
    badge_html = f"<span class='hardware-chip'>{badge}</span>" if badge else ""
    sub_html = f"<div class='section-subtitle'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class='section-header'>
            <div>
                <h3 class='section-title'>{title}</h3>
                {sub_html}
            </div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_vehicle_type_card(label: str, count: int, percentage: float, icon: str = "🚗", color: Optional[str] = None) -> None:
    """Render a compact vehicle category breakdown card."""
    c_style = f"color: {color};" if color else ""
    st.markdown(
        f"""
        <div class='vehicle-type-card'>
            <div class='vt-left'>
                <span class='vt-icon'>{icon}</span>
                <span class='vt-label'>{label}</span>
            </div>
            <div class='vt-right'>
                <div class='vt-count' style='{c_style}'>{count:,}</div>
                <div class='vt-pct'>{percentage:.1f}%</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state(title: str, message: str, icon: str = "📊") -> None:
    """Render a styled command-center empty state."""
    st.markdown(
        f"""
        <div class='empty-state-card'>
            <div class='empty-state-icon'>{icon}</div>
            <div class='empty-state-title'>{title}</div>
            <div class='empty-state-text'>{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_system_status(
    model_status: str = "ONLINE",
    video_status: str = "READY",
    tracker_status: str = "READY",
    db_status: str = "CONNECTED",
    analytics_status: str = "READY",
) -> None:
    """Render sidebar system status panel."""
    st.markdown(
        f"""
        <div style='background: {THEME["bg_card"]}; border: 1px solid {THEME["border"]}; border-radius: 8px; padding: 14px; margin-top: 14px;'>
            <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;'>
                <span style='font-size: 11px; font-weight: 700; color: {THEME["text_secondary"]}; text-transform: uppercase; letter-spacing: 0.6px;'>SYSTEM STATUS</span>
                <span class='status-badge-online' style='padding: 3px 8px; font-size: 10px;'><span class='status-dot-green'></span> ONLINE</span>
            </div>
            <div style='display: flex; flex-direction: column; gap: 6px; font-size: 11px; font-family: "JetBrains Mono", Consolas, monospace;'>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: {THEME["text_secondary"]};'>YOLO MODEL</span>
                    <span style='color: {THEME["success"]}; font-weight: 700;'>{model_status}</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: {THEME["text_secondary"]};'>VIDEO PROCESSOR</span>
                    <span style='color: {THEME["accent_primary"]}; font-weight: 700;'>{video_status}</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: {THEME["text_secondary"]};'>OBJECT TRACKER</span>
                    <span style='color: {THEME["accent_primary"]}; font-weight: 700;'>{tracker_status}</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: {THEME["text_secondary"]};'>DATABASE (SQLITE)</span>
                    <span style='color: {THEME["success"]}; font-weight: 700;'>{db_status}</span>
                </div>
                <div style='display: flex; justify-content: space-between;'>
                    <span style='color: {THEME["text_secondary"]};'>ANALYTICS ENGINE</span>
                    <span style='color: {THEME["accent_primary"]}; font-weight: 700;'>{analytics_status}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------- PLOTLY VISUALIZATIONS -----------------

def create_vehicle_distribution_chart(stats: Dict[str, Any]) -> go.Figure:
    """Render command center Donut chart showing proportion and counts of each vehicle class."""
    labels = ["Cars", "Motorcycles", "Buses", "Trucks", "Bicycles", "Pedestrians"]
    raw_values = [
        int(stats.get("cars", 0)),
        int(stats.get("motorcycles", 0)),
        int(stats.get("buses", 0)),
        int(stats.get("trucks", 0)),
        int(stats.get("bicycles", 0)),
        int(stats.get("pedestrians", 0)),
    ]
    total_val = sum(raw_values)
    is_empty = total_val == 0

    if is_empty:
        values = [1, 1, 1, 1, 1, 1]
        text_template = "<b>%{label}</b>"
        hover = "No detections logged yet"
    else:
        values = raw_values
        text_template = "<b>%{label}</b><br>%{value} (%{percent})"
        hover = None

    color_seq = [
        CHART_THEME["car"],
        CHART_THEME["motorcycle"],
        CHART_THEME["bus"],
        CHART_THEME["truck"],
        CHART_THEME["bicycle"],
        CHART_THEME["person"],
    ]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.55,
                marker=dict(colors=color_seq, line=dict(color=THEME["bg_card"], width=2.5)),
                texttemplate=text_template,
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", size=12, family="Inter, sans-serif"),
                outsidetextfont=dict(color=THEME["text_primary"], size=12, family="Inter, sans-serif"),
                hoverinfo="label+value+percent" if hover is None else "text",
                hovertext=hover,
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="<b>Vehicle Classification Distribution</b>",
            font=dict(color=THEME["text_primary"], size=14),
        ),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor=THEME["bg_card"],
        plot_bgcolor=THEME["bg_card"],
        showlegend=True,
        legend=dict(
            font=dict(color=THEME["text_primary"], size=11),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        height=320,
    )
    return fig


def create_traffic_over_time_chart(stats_df: pd.DataFrame) -> go.Figure:
    """Area and line chart plotting total vehicle volume and violations over timeline."""
    fig = go.Figure()

    if stats_df is None or stats_df.empty or "total_vehicles" not in stats_df.columns:
        fig.add_annotation(
            text="Waiting for video stream / event snapshots to log timeline statistics...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=13, color=THEME["text_secondary"]),
        )
    else:
        # Plot total vehicles line with gradient area
        fig.add_trace(
            go.Scatter(
                x=stats_df["timestamp"],
                y=stats_df["total_vehicles"],
                mode="lines+markers",
                name="Total Vehicles",
                line=dict(color=THEME["accent_primary"], width=2.5),
                marker=dict(size=5, color=THEME["accent_primary"], symbol="circle"),
                fill="tozeroy",
                fillcolor="rgba(56, 189, 248, 0.12)",
                hovertemplate="<b>%{x}</b><br>Total Vehicles: %{y}<extra></extra>",
            )
        )

        if "wrong_way_count" in stats_df.columns and stats_df["wrong_way_count"].max() > 0:
            fig.add_trace(
                go.Scatter(
                    x=stats_df["timestamp"],
                    y=stats_df["wrong_way_count"],
                    mode="lines+markers",
                    name="⚠️ Wrong-Way Alerts",
                    line=dict(color=THEME["danger"], width=2.0, dash="dash"),
                    marker=dict(size=6, color=THEME["danger"], symbol="diamond"),
                    hovertemplate="<b>%{x}</b><br>Wrong-Way Infractions: %{y}<extra></extra>",
                )
            )

    fig.update_layout(
        title=dict(
            text="<b>Traffic Volume & Violation Timeline</b>",
            font=dict(color=THEME["text_primary"], size=14),
        ),
        template="plotly_dark",
        margin=dict(l=25, r=20, t=45, b=25),
        paper_bgcolor=THEME["bg_card"],
        plot_bgcolor=THEME["bg_card"],
        font=dict(color=THEME["text_primary"]),
        xaxis=dict(
            title=dict(text="<b>Timeline Snapshot</b>", font=dict(color=THEME["text_secondary"], size=11)),
            tickfont=dict(color=THEME["text_secondary"], size=10),
            showgrid=True,
            gridcolor=THEME["border"],
        ),
        yaxis=dict(
            title=dict(text="<b>Vehicle Count</b>", font=dict(color=THEME["text_secondary"], size=11)),
            tickfont=dict(color=THEME["text_secondary"], size=10),
            showgrid=True,
            gridcolor=THEME["border"],
        ),
        legend=dict(
            font=dict(color=THEME["text_primary"], size=11),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
        ),
        height=320,
    )
    return fig


def create_direction_chart(directional_split: Dict[str, int]) -> go.Figure:
    """Bar chart showing vehicle counts across movement directions."""
    display_dirs = ["RIGHT ➔", "LEFT ⬅", "UP ⬆", "DOWN ⬇"]
    keys = ["RIGHT", "LEFT", "UP", "DOWN"]
    vals = [directional_split.get(k, 0) for k in keys]
    colors = [THEME["success"], THEME["danger"], THEME["accent_primary"], THEME["warning"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=display_dirs,
                y=vals,
                marker=dict(
                    color=colors,
                    line=dict(color=THEME["border"], width=1.5),
                ),
                text=[f"<b>{v}</b>" for v in vals],
                textposition="outside",
                textfont=dict(color=THEME["text_primary"], size=13, family="Inter, sans-serif"),
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Count: %{y} vehicles<extra></extra>",
            )
        ]
    )

    max_val = max(vals) if vals and max(vals) > 0 else 10
    fig.update_layout(
        title=dict(
            text="<b>Directional Traffic Distribution</b>",
            font=dict(color=THEME["text_primary"], size=14),
        ),
        template="plotly_dark",
        margin=dict(l=25, r=20, t=45, b=25),
        paper_bgcolor=THEME["bg_card"],
        plot_bgcolor=THEME["bg_card"],
        font=dict(color=THEME["text_primary"]),
        xaxis=dict(
            title=dict(text="<b>Movement Direction</b>", font=dict(color=THEME["text_secondary"], size=11)),
            tickfont=dict(color=THEME["text_primary"], size=12, family="Inter, sans-serif"),
            showgrid=False,
        ),
        yaxis=dict(
            title=dict(text="<b>Vehicles Tallied</b>", font=dict(color=THEME["text_secondary"], size=11)),
            tickfont=dict(color=THEME["text_secondary"], size=10),
            showgrid=True,
            gridcolor=THEME["border"],
            range=[0, max_val * 1.3],
        ),
        height=320,
    )
    return fig


def create_density_gauge(density_level: str, active_count: int) -> go.Figure:
    """Road occupancy gauge with Low / Medium / High zones."""
    dens = (density_level or "LOW").upper()
    status_colors = {
        "LOW": THEME["success"],
        "MEDIUM": THEME["warning"],
        "HIGH": THEME["danger"],
    }
    badge_color = status_colors.get(dens, THEME["success"])

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=active_count,
            number=dict(
                font=dict(color=THEME["accent_primary"], size=40, family="JetBrains Mono, monospace"),
                suffix=" veh",
            ),
            title={
                "text": f"<b>Traffic Density: <span style='color:{badge_color}'>{dens}</span></b>",
                "font": {"color": THEME["text_primary"], "size": 14},
            },
            gauge={
                "axis": {
                    "range": [0, 60],
                    "tickwidth": 1,
                    "tickcolor": THEME["text_secondary"],
                    "tickfont": {"color": THEME["text_secondary"], "size": 10},
                },
                "bar": {"color": "#FFFFFF", "thickness": 0.25},
                "bgcolor": THEME["bg_secondary"],
                "borderwidth": 1,
                "bordercolor": THEME["border"],
                "steps": [
                    {"range": [0, 20], "color": "rgba(34, 197, 94, 0.3)"},
                    {"range": [20, 45], "color": "rgba(245, 158, 11, 0.3)"},
                    {"range": [45, 60], "color": "rgba(239, 68, 68, 0.35)"},
                ],
                "threshold": {
                    "line": {"color": THEME["danger"], "width": 3},
                    "thickness": 0.75,
                    "value": 50,
                },
            },
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=THEME["bg_card"],
        plot_bgcolor=THEME["bg_card"],
        font=dict(color=THEME["text_primary"]),
        margin=dict(l=25, r=25, t=45, b=25),
        height=320,
    )
    return fig


# ----------------- REPORT GENERATION -----------------

def generate_csv_report(events_df: pd.DataFrame) -> str:
    """Convert events dataframe to formatted CSV string."""
    if events_df is None or events_df.empty:
        df = pd.DataFrame(columns=["id", "vehicle_id", "vehicle_type", "timestamp", "direction", "event_type", "confidence"])
    else:
        df = events_df.copy()
    return df.to_csv(index=False)


def generate_pdf_report(summary_stats: Dict[str, Any], violations_df: pd.DataFrame) -> bytes:
    """
    Compile a formal PDF Traffic Audit Report using ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0B1120"),
        alignment=1,
    )
    sub_style = ParagraphStyle(
        "DocSub",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#555555"),
        alignment=1,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#172033"),
        spaceBefore=12,
        spaceAfter=6,
    )

    # Header
    elements.append(Paragraph("<b>AI-BASED INTELLIGENT TRAFFIC MONITORING SYSTEM</b>", title_style))
    elements.append(Paragraph("Automated Traffic Intelligence & Safety Audit Report", sub_style))
    elements.append(Spacer(1, 14))

    # Executive Summary Table
    elements.append(Paragraph("1. Executive Traffic Summary", heading_style))
    sum_data = [
        ["Metric", "Value", "Metric", "Value"],
        ["Total Vehicles Detected", str(summary_stats.get("total_vehicles", 0)), "Wrong-Way Violations", str(summary_stats.get("wrong_way_violations", 0))],
        ["Cars Counted", str(summary_stats.get("cars", 0)), "Peak Traffic Window", str(summary_stats.get("peak_period", "N/A"))],
        ["Motorcycles Counted", str(summary_stats.get("motorcycles", 0)), "Flow Rate (veh/min)", str(summary_stats.get("vehicles_per_min", 0.0))],
        ["Heavy Vehicles (Bus/Truck)", str(summary_stats.get("buses", 0) + summary_stats.get("trucks", 0)), "Predominant Congestion", str(summary_stats.get("congestion_summary", "NORMAL"))],
    ]
    t1 = Table(sum_data, colWidths=[130, 130, 140, 130])
    t1.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8F9FA"), colors.white]),
            ]
        )
    )
    elements.append(t1)
    elements.append(Spacer(1, 14))

    # Vehicle Classification Breakdown
    elements.append(Paragraph("2. Vehicle Modal Split", heading_style))
    tot = max(1, summary_stats.get("total_vehicles", 1))
    cls_data = [
        ["Vehicle Category", "Count", "Percentage Split"],
        ["Passenger Cars", str(summary_stats.get("cars", 0)), f"{(summary_stats.get('cars', 0) / tot * 100):.1f}%"],
        ["Motorcycles & Scooters", str(summary_stats.get("motorcycles", 0)), f"{(summary_stats.get('motorcycles', 0) / tot * 100):.1f}%"],
        ["Buses & Public Transit", str(summary_stats.get("buses", 0)), f"{(summary_stats.get('buses', 0) / tot * 100):.1f}%"],
        ["Commercial Trucks", str(summary_stats.get("trucks", 0)), f"{(summary_stats.get('trucks', 0) / tot * 100):.1f}%"],
        ["Bicycles & Micro-mobility", str(summary_stats.get("bicycles", 0)), f"{(summary_stats.get('bicycles', 0) / tot * 100):.1f}%"],
        ["Pedestrians", str(summary_stats.get("pedestrians", 0)), f"{(summary_stats.get('pedestrians', 0) / tot * 100):.1f}%"],
    ]
    t2 = Table(cls_data, colWidths=[200, 160, 170])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#263247")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8F9FA"), colors.white]),
            ]
        )
    )
    elements.append(t2)
    elements.append(Spacer(1, 14))

    # Violations Log Section
    elements.append(Paragraph("3. Traffic Safety & Wrong-Way Violations Log", heading_style))
    viol_rows = [["ID", "Vehicle Type", "Timestamp", "Direction Detected", "Confidence"]]
    if violations_df is not None and not violations_df.empty:
        for _, row in violations_df.head(10).iterrows():
            viol_rows.append(
                [
                    str(row.get("vehicle_id", "-")),
                    str(row.get("vehicle_type", "-")),
                    str(row.get("timestamp", "-")),
                    str(row.get("direction", "-")),
                    f"{float(row.get('confidence', 0.0)):.2f}",
                ]
            )
    else:
        viol_rows.append(["None", "No safety violations registered during this monitoring period", "-", "-", "-"])

    t3 = Table(viol_rows, colWidths=[50, 110, 150, 120, 100])
    t3.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EF4444")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BDC3C7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FDEDEC"), colors.white]),
            ]
        )
    )
    elements.append(t3)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph("<i>Report compiled by AI Traffic Command Center. YOLOv8 + ByteTrack + SQLite.</i>", sub_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
