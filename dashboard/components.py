"""
Dashboard UI Components, Plotly Visualizations, and Report Generators.
Includes KPI cards, distribution charts, time-series graphs,
and export modules for CSV and PDF reports.
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


# Theme color palette
# Theme color palette - Modern, vibrant, accessible high-contrast colors
CHART_THEME = {
    "car": "#10B981",         # Vivid Emerald Green
    "motorcycle": "#06B6D4",  # Vivid Cyan
    "bus": "#F59E0B",         # Bright Amber / Gold
    "truck": "#F97316",       # Bright Orange
    "bicycle": "#A855F7",     # Vivid Purple
    "person": "#38BDF8",      # Sky Blue
    "wrong_way": "#EF4444",   # Neon Crimson Red
    "background": "#181E29",  # Slate Card Background
    "paper": "#181E29",
    "text": "#F8FAFC",        # Crisp White
    "subtext": "#94A3B8",     # Slate 400
    "grid": "#2A3447",        # Visible Slate Grid
}


def render_kpi_metrics(stats: Dict[str, Any]) -> None:
    """Render modern top-level metric KPI cards."""
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            label="🚗 Total Cars",
            value=stats.get("cars", 0),
            delta=f"{stats.get('cars', 0)} logged",
        )
    with c2:
        st.metric(
            label="🏍️ Motorcycles",
            value=stats.get("motorcycles", 0),
            delta=f"{stats.get('motorcycles', 0)} logged",
        )
    with c3:
        st.metric(
            label="🚦 Total Vehicles",
            value=stats.get("total_counted", stats.get("total_vehicles", 0)),
            delta=f"Active: {stats.get('active_vehicles', 0)}",
        )
    with c4:
        viol = stats.get("wrong_way_count", stats.get("wrong_way_violations", 0))
        st.metric(
            label="⚠️ Violations",
            value=viol,
            delta="Wrong-way" if viol > 0 else "Clear",
            delta_color="inverse" if viol > 0 else "normal",
        )


def create_vehicle_distribution_chart(stats: Dict[str, Any]) -> go.Figure:
    """Render high-contrast Donut chart showing proportion and counts of each vehicle class."""
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
                hole=0.52,
                marker=dict(colors=color_seq, line=dict(color="#0F172A", width=2.5)),
                texttemplate=text_template,
                textposition="inside",
                insidetextfont=dict(color="#FFFFFF", size=13, family="Segoe UI, sans-serif"),
                outsidetextfont=dict(color="#F8FAFC", size=13, family="Segoe UI, sans-serif"),
                hoverinfo="label+value+percent" if hover is None else "text",
                hovertext=hover,
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="<b>🚗 Vehicle Classification Breakdown</b><br><span style='font-size:12px;color:#94A3B8'>Distribution across detected vehicle categories</span>",
            font=dict(color="#F8FAFC", size=15),
        ),
        template="plotly_dark",
        margin=dict(l=20, r=20, t=55, b=20),
        paper_bgcolor="#181E29",
        plot_bgcolor="#181E29",
        showlegend=True,
        legend=dict(
            font=dict(color="#F8FAFC", size=12),
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
        ),
        height=340,
    )
    return fig


def create_traffic_over_time_chart(stats_df: pd.DataFrame) -> go.Figure:
    """Line graph plotting total vehicle count and violations over time."""
    fig = go.Figure()

    if stats_df is None or stats_df.empty or "total_vehicles" not in stats_df.columns:
        fig.add_annotation(
            text="⏳ Waiting for video stream to log timeline statistics...",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=14, color="#94A3B8"),
        )
    else:
        # Plot total vehicles line with gradient area
        fig.add_trace(
            go.Scatter(
                x=stats_df["timestamp"],
                y=stats_df["total_vehicles"],
                mode="lines+markers",
                name="Total Vehicles",
                line=dict(color="#00F2FE", width=3.5),
                marker=dict(size=6, color="#00F2FE", symbol="circle"),
                fill="tozeroy",
                fillcolor="rgba(0, 242, 254, 0.15)",
                hovertemplate="<b>%{x}</b><br>Total Vehicles: %{y}<extra></extra>",
            )
        )

        if "wrong_way_count" in stats_df.columns and stats_df["wrong_way_count"].max() > 0:
            fig.add_trace(
                go.Scatter(
                    x=stats_df["timestamp"],
                    y=stats_df["wrong_way_count"],
                    mode="lines+markers",
                    name="⚠️ Violations",
                    line=dict(color="#FF3366", width=2.5, dash="dash"),
                    marker=dict(size=5, color="#FF3366", symbol="diamond"),
                    hovertemplate="<b>%{x}</b><br>Wrong-Way Violations: %{y}<extra></extra>",
                )
            )

    fig.update_layout(
        title=dict(
            text="<b>📈 Traffic Volume & Violations Over Time</b><br><span style='font-size:12px;color:#94A3B8'>Surge detection & safety infractions</span>",
            font=dict(color="#F8FAFC", size=15),
        ),
        template="plotly_dark",
        margin=dict(l=25, r=20, t=55, b=25),
        paper_bgcolor="#181E29",
        plot_bgcolor="#181E29",
        font=dict(color="#F8FAFC"),
        xaxis=dict(
            title=dict(text="<b>Timeline (Time of Day)</b>", font=dict(color="#E2E8F0", size=13)),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="#2A3447",
        ),
        yaxis=dict(
            title=dict(text="<b>Vehicle Count</b>", font=dict(color="#E2E8F0", size=13)),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="#2A3447",
        ),
        legend=dict(
            font=dict(color="#F8FAFC", size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1.0,
        ),
        height=340,
    )
    return fig


def create_direction_chart(directional_split: Dict[str, int]) -> go.Figure:
    """Bar chart showing vehicle counts across movement directions."""
    display_dirs = ["RIGHT ➡️", "LEFT ⬅️", "UP ⬆️", "DOWN ⬇️"]
    keys = ["RIGHT", "LEFT", "UP", "DOWN"]
    vals = [directional_split.get(k, 0) for k in keys]
    colors = ["#10B981", "#EF4444", "#38BDF8", "#F59E0B"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=display_dirs,
                y=vals,
                marker=dict(
                    color=colors,
                    line=dict(color="#0F172A", width=2),
                ),
                text=[f"<b>{v}</b>" for v in vals],
                textposition="outside",
                textfont=dict(color="#FFFFFF", size=15, family="Segoe UI, sans-serif"),
                cliponaxis=False,
                hovertemplate="<b>%{x}</b><br>Count: %{y} vehicles<extra></extra>",
            )
        ]
    )

    max_val = max(vals) if vals and max(vals) > 0 else 10
    fig.update_layout(
        title=dict(
            text="<b>🧭 Directional Traffic Flow</b><br><span style='font-size:12px;color:#94A3B8'>Total vehicles moving per cardinal direction</span>",
            font=dict(color="#F8FAFC", size=15),
        ),
        template="plotly_dark",
        margin=dict(l=25, r=20, t=55, b=25),
        paper_bgcolor="#181E29",
        plot_bgcolor="#181E29",
        font=dict(color="#F8FAFC"),
        xaxis=dict(
            title=dict(text="<b>Flow Direction</b>", font=dict(color="#E2E8F0", size=13)),
            tickfont=dict(color="#FFFFFF", size=13, family="Segoe UI, sans-serif"),
            showgrid=False,
        ),
        yaxis=dict(
            title=dict(text="<b>Vehicles Counted</b>", font=dict(color="#E2E8F0", size=13)),
            tickfont=dict(color="#CBD5E1", size=11),
            showgrid=True,
            gridcolor="#2A3447",
            range=[0, max_val * 1.3],
        ),
        height=340,
    )
    return fig


def create_density_gauge(density_level: str, active_count: int) -> go.Figure:
    """Gauge showing real-time road occupancy level (LOW, MEDIUM, HIGH)."""
    dens = (density_level or "LOW").upper()
    status_colors = {
        "LOW": "#10B981",     # Emerald Green
        "MEDIUM": "#F59E0B",  # Vibrant Amber
        "HIGH": "#EF4444",    # Crimson Red
    }
    badge_color = status_colors.get(dens, "#10B981")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=active_count,
            number=dict(
                font=dict(color="#00F2FE", size=46, family="Segoe UI, sans-serif"),
                suffix=" cars",
            ),
            title={
                "text": f"<b>Road Density: <span style='color:{badge_color}'>{dens}</span></b><br><span style='font-size:12px;color:#94A3B8'>Active On-Screen Vehicles</span>",
                "font": {"color": "#F8FAFC", "size": 16},
            },
            gauge={
                "axis": {
                    "range": [0, 60],
                    "tickwidth": 2,
                    "tickcolor": "#CBD5E1",
                    "tickfont": {"color": "#E2E8F0", "size": 12},
                },
                "bar": {"color": "#FFFFFF", "thickness": 0.28},
                "bgcolor": "#1E293B",
                "borderwidth": 2,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 20], "color": "#065F46"},    # Dark Green (0-20 Low)
                    {"range": [20, 45], "color": "#92400E"},   # Dark Amber (20-45 Med)
                    {"range": [45, 60], "color": "#991B1B"},   # Dark Red (45-60 High)
                ],
                "threshold": {
                    "line": {"color": "#EF4444", "width": 4},
                    "thickness": 0.75,
                    "value": 50,
                },
            },
        )
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#181E29",
        plot_bgcolor="#181E29",
        font=dict(color="#F8FAFC"),
        margin=dict(l=25, r=25, t=55, b=25),
        height=340,
    )
    return fig


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
        textColor=colors.HexColor("#1A252C"),
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
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["Normal"]

    # Header
    elements.append(Paragraph("<b>AI-BASED INTELLIGENT TRAFFIC MONITORING SYSTEM</b>", title_style))
    elements.append(Paragraph("Automated Traffic Analytics and Safety Violation Audit Report", sub_style))
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
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
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
    cls_data = [
        ["Vehicle Category", "Count", "Percentage Split"],
        ["Passenger Cars", str(summary_stats.get("cars", 0)), f"{(summary_stats.get('cars', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
        ["Motorcycles & Scooters", str(summary_stats.get("motorcycles", 0)), f"{(summary_stats.get('motorcycles', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
        ["Buses & Public Transit", str(summary_stats.get("buses", 0)), f"{(summary_stats.get('buses', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
        ["Commercial Trucks", str(summary_stats.get("trucks", 0)), f"{(summary_stats.get('trucks', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
        ["Bicycles & Micro-mobility", str(summary_stats.get("bicycles", 0)), f"{(summary_stats.get('bicycles', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
        ["Pedestrians", str(summary_stats.get("pedestrians", 0)), f"{(summary_stats.get('pedestrians', 0) / max(1, summary_stats.get('total_vehicles', 1)) * 100):.1f}%"],
    ]
    t2 = Table(cls_data, colWidths=[200, 160, 170])
    t2.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495E")),
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
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C0392B")),
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

    elements.append(Paragraph("<i>Report generated automatically by AI Traffic Monitoring Engine. CPU/GPU accelerated.</i>", sub_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
