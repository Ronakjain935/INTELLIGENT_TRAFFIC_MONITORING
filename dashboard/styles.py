"""
Custom UI Styling and Command Center Theme for Intelligent Traffic Monitoring System.
Implements dark command-center aesthetic, bespoke cards, telemetry HUDs, and responsive layouts.
"""

from __future__ import annotations
import streamlit as st

# Command Center Color Tokens
THEME = {
    "bg_primary": "#0B1120",
    "bg_secondary": "#111827",
    "bg_card": "#172033",
    "border": "#263247",
    "accent_primary": "#38BDF8",
    "success": "#22C55E",
    "warning": "#F59E0B",
    "danger": "#EF4444",
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
}


def apply_custom_css() -> None:
    """Inject custom CSS rules into the Streamlit app."""
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap');

        /* Global Theme Reset */
        html, body, [data-testid="stAppViewContainer"], .main {{
            background-color: {THEME["bg_primary"]} !important;
            color: {THEME["text_primary"]} !important;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }}

        /* App container padding */
        .block-container {{
            padding-top: 1.5rem !important;
            padding-bottom: 2.5rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }}

        /* Sidebar Styling */
        section[data-testid="stSidebar"] {{
            background-color: {THEME["bg_secondary"]} !important;
            border-right: 1px solid {THEME["border"]} !important;
        }}
        section[data-testid="stSidebar"] > div {{
            background-color: {THEME["bg_secondary"]} !important;
        }}
        [data-testid="collapsedControl"] {{
            background-color: {THEME["bg_card"]} !important;
            color: {THEME["text_primary"]} !important;
            border: 1px solid {THEME["border"]} !important;
            border-radius: 0 8px 8px 0;
        }}

        /* Translucent Top Header */
        header[data-testid="stHeader"] {{
            background-color: rgba(11, 17, 32, 0.88) !important;
            backdrop-filter: blur(12px) !important;
            border-bottom: 1px solid {THEME["border"]} !important;
        }}

        /* Typography Defaults */
        h1, h2, h3, h4, h5, h6 {{
            color: {THEME["text_primary"]} !important;
            font-family: 'Inter', sans-serif !important;
            font-weight: 700 !important;
            letter-spacing: -0.02em !important;
        }}
        p, span, label, div {{
            color: {THEME["text_primary"]};
        }}

        /* Custom Command Center Top Header */
        .cc-header-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, {THEME["bg_card"]} 0%, {THEME["bg_secondary"]} 100%);
            border: 1px solid {THEME["border"]};
            border-radius: 12px;
            padding: 16px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
        }}
        .cc-header-left {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}
        .cc-header-logo {{
            font-size: 36px;
            line-height: 1;
        }}
        .cc-header-title {{
            font-size: 22px;
            font-weight: 800;
            color: {THEME["text_primary"]};
            letter-spacing: 0.5px;
            margin: 0;
            text-transform: uppercase;
        }}
        .cc-header-subtitle {{
            font-size: 13px;
            color: {THEME["text_secondary"]};
            margin: 3px 0 0 0;
            letter-spacing: 0.3px;
        }}
        .cc-header-right {{
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}

        /* System Status Badges & Pulse Animation */
        @keyframes pulse-green {{
            0% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.5); }}
            70% {{ box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }}
        }}
        @keyframes pulse-red {{
            0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.6); }}
            70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}

        .status-badge-online {{
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(34, 197, 94, 0.12);
            border: 1px solid rgba(34, 197, 94, 0.4);
            color: #4ADE80;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.6px;
            text-transform: uppercase;
        }}
        .status-dot-green {{
            width: 8px;
            height: 8px;
            background-color: {THEME["success"]};
            border-radius: 50%;
            display: inline-block;
            animation: pulse-green 2s infinite;
        }}
        .status-dot-red {{
            width: 8px;
            height: 8px;
            background-color: {THEME["danger"]};
            border-radius: 50%;
            display: inline-block;
            animation: pulse-red 1.5s infinite;
        }}

        .hardware-chip {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background-color: rgba(56, 189, 248, 0.08);
            border: 1px solid rgba(56, 189, 248, 0.25);
            color: {THEME["accent_primary"]};
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 11px;
            font-family: 'JetBrains Mono', Consolas, monospace;
            font-weight: 600;
            letter-spacing: 0.4px;
        }}

        /* Modern KPI Cards */
        .metric-card {{
            background: {THEME["bg_card"]};
            border: 1px solid {THEME["border"]};
            border-radius: 10px;
            padding: 18px 20px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        }}
        .metric-card:hover {{
            border-color: {THEME["accent_primary"]};
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(56, 189, 248, 0.15);
        }}
        .metric-card-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
        }}
        .metric-card-title {{
            font-size: 12px;
            font-weight: 700;
            color: {THEME["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.6px;
        }}
        .metric-card-icon {{
            font-size: 18px;
        }}
        .metric-card-value {{
            font-size: 32px;
            font-weight: 800;
            color: {THEME["text_primary"]};
            line-height: 1.1;
            margin-bottom: 6px;
            font-feature-settings: "tnum";
            font-variant-numeric: tabular-nums;
        }}
        .metric-card-delta {{
            font-size: 12px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 4px;
        }}

        /* Professional Traffic Status Card */
        .traffic-status-card {{
            background: {THEME["bg_card"]};
            border: 1px solid {THEME["border"]};
            border-radius: 10px;
            padding: 22px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
        }}
        .traffic-status-pill {{
            display: inline-block;
            padding: 6px 16px;
            border-radius: 6px;
            font-weight: 800;
            font-size: 14px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }}
        .status-low {{
            background: rgba(34, 197, 94, 0.15);
            color: #4ADE80;
            border: 1px solid rgba(34, 197, 94, 0.4);
        }}
        .status-medium {{
            background: rgba(245, 158, 11, 0.15);
            color: #FBBF24;
            border: 1px solid rgba(245, 158, 11, 0.4);
        }}
        .status-high {{
            background: rgba(239, 68, 68, 0.18);
            color: #F87171;
            border: 1px solid rgba(239, 68, 68, 0.5);
            animation: pulse-red 2s infinite;
        }}

        /* Wrong-Way Alert Banner Card */
        .wrong-way-alert {{
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.22) 0%, rgba(127, 29, 29, 0.4) 100%);
            border: 2px solid {THEME["danger"]};
            border-radius: 10px;
            padding: 16px 20px;
            margin-bottom: 16px;
            box-shadow: 0 4px 20px rgba(239, 68, 68, 0.35);
        }}
        .wrong-way-alert-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 16px;
            font-weight: 800;
            color: #FFFFFF;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .wrong-way-alert-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 10px;
            font-size: 13px;
            color: #FECACA;
        }}

        /* Modern Command Center Buttons */
        div.stButton > button, div.stDownloadButton > button {{
            background: {THEME["bg_card"]} !important;
            color: {THEME["text_primary"]} !important;
            border: 1px solid {THEME["border"]} !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            font-size: 13px !important;
            padding: 8px 18px !important;
            transition: all 0.2s ease !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
        }}
        div.stButton > button:hover, div.stDownloadButton > button:hover {{
            background: #1E2B45 !important;
            border-color: {THEME["accent_primary"]} !important;
            color: #FFFFFF !important;
            transform: translateY(-1px);
        }}
        div.stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #0284C7 0%, #0369A1 100%) !important;
            color: #FFFFFF !important;
            border: 1px solid {THEME["accent_primary"]} !important;
            font-weight: 700 !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #0EA5E9 0%, #0284C7 100%) !important;
            box-shadow: 0 4px 16px rgba(14, 165, 233, 0.4) !important;
        }}

        /* Navigation Radio styling in Sidebar */
        div[data-testid="stSidebar"] div[role="radiogroup"] > label {{
            background-color: transparent !important;
            padding: 8px 14px !important;
            border-radius: 8px !important;
            margin-bottom: 4px !important;
            border: 1px solid transparent !important;
            transition: all 0.15s ease !important;
        }}
        div[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {{
            background-color: {THEME["bg_card"]} !important;
            border-color: {THEME["border"]} !important;
        }}
        div[data-testid="stSidebar"] div[role="radiogroup"] > label[data-checked="true"] {{
            background-color: rgba(56, 189, 248, 0.12) !important;
            border-color: {THEME["accent_primary"]} !important;
        }}

        /* Custom File Uploader Panel */
        .upload-panel {{
            background: {THEME["bg_card"]};
            border: 2px dashed {THEME["border"]};
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            transition: border-color 0.2s ease;
            margin-bottom: 16px;
        }}
        .upload-panel:hover {{
            border-color: {THEME["accent_primary"]};
        }}

        /* Telemetry Status Bar below Video */
        .telemetry-bar {{
            display: flex;
            align-items: center;
            justify-content: space-around;
            background: {THEME["bg_card"]};
            border: 1px solid {THEME["border"]};
            border-radius: 8px;
            padding: 12px 16px;
            margin-top: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
        }}
        .telemetry-item {{
            text-align: center;
        }}
        .telemetry-label {{
            font-size: 11px;
            font-weight: 700;
            color: {THEME["text_secondary"]};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .telemetry-val {{
            font-size: 18px;
            font-weight: 800;
            color: {THEME["text_primary"]};
            font-family: 'JetBrains Mono', Consolas, monospace;
        }}

        /* Custom Section Header */
        .section-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
            border-bottom: 1px solid {THEME["border"]};
            padding-bottom: 8px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
            color: {THEME["text_primary"]};
            letter-spacing: 0.2px;
            margin: 0;
        }}
        .section-subtitle {{
            font-size: 12px;
            color: {THEME["text_secondary"]};
            margin: 2px 0 0 0;
        }}

        /* Empty State Card */
        .empty-state-card {{
            background: {THEME["bg_card"]};
            border: 1px dashed {THEME["border"]};
            border-radius: 12px;
            padding: 36px 24px;
            text-align: center;
            margin: 16px 0;
        }}
        .empty-state-icon {{
            font-size: 40px;
            margin-bottom: 10px;
        }}
        .empty-state-title {{
            font-size: 16px;
            font-weight: 700;
            color: {THEME["text_primary"]};
            margin-bottom: 6px;
        }}
        .empty-state-text {{
            font-size: 13px;
            color: {THEME["text_secondary"]};
            max-width: 440px;
            margin: 0 auto;
        }}

        /* Table & Dataframe Dark Overrides */
        [data-testid="stDataFrame"] {{
            border: 1px solid {THEME["border"]} !important;
            border-radius: 8px !important;
            overflow: hidden;
        }}

        /* Tabs Styling */
        div[data-baseweb="tab-list"] {{
            background-color: {THEME["bg_secondary"]} !important;
            border-radius: 10px !important;
            padding: 5px !important;
            border: 1px solid {THEME["border"]} !important;
            gap: 4px !important;
        }}
        button[data-baseweb="tab"] {{
            background-color: transparent !important;
            border-radius: 7px !important;
            padding: 8px 16px !important;
            border: none !important;
            transition: all 0.2s ease !important;
        }}
        button[data-baseweb="tab"] * {{
            font-size: 14px !important;
            font-weight: 600 !important;
            color: {THEME["text_secondary"]} !important;
        }}
        button[data-baseweb="tab"]:hover * {{
            color: {THEME["text_primary"]} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] {{
            background: {THEME["bg_card"]} !important;
            border: 1px solid {THEME["border"]} !important;
        }}
        button[data-baseweb="tab"][aria-selected="true"] * {{
            color: {THEME["accent_primary"]} !important;
            font-weight: 700 !important;
        }}

        /* Vehicle Modal Split Compact Cards */
        .vehicle-type-card {{
            background: {THEME["bg_card"]};
            border: 1px solid {THEME["border"]};
            border-radius: 8px;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 8px;
            transition: border-color 0.2s ease;
        }}
        .vehicle-type-card:hover {{
            border-color: {THEME["accent_primary"]};
        }}
        .vt-left {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .vt-icon {{
            font-size: 20px;
        }}
        .vt-label {{
            font-size: 13px;
            font-weight: 600;
            color: {THEME["text_primary"]};
        }}
        .vt-right {{
            text-align: right;
        }}
        .vt-count {{
            font-size: 16px;
            font-weight: 800;
            color: {THEME["text_primary"]};
            font-family: 'JetBrains Mono', Consolas, monospace;
        }}
        .vt-pct {{
            font-size: 11px;
            color: {THEME["text_secondary"]};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
