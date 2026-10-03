"""
Dashboard UI Components, Styling, and Page Modules Package.
"""

from dashboard.styles import THEME, apply_custom_css
from dashboard.components import (
    render_kpi_card,
    render_kpi_metrics,
    render_status_card,
    render_alert_card,
    render_section_header,
    render_vehicle_type_card,
    render_empty_state,
    render_system_status,
    create_vehicle_distribution_chart,
    create_traffic_over_time_chart,
    create_direction_chart,
    create_density_gauge,
    generate_csv_report,
    generate_pdf_report,
)
from dashboard.header import render_top_header
from dashboard.sidebar import render_sidebar
from dashboard.dashboard_page import render_dashboard_page
from dashboard.monitoring_page import render_monitoring_page
from dashboard.analytics_page import render_analytics_page
from dashboard.events_page import render_events_page
from dashboard.reports_page import render_reports_page
from dashboard.settings_page import render_settings_page
from dashboard.about_page import render_about_page

__all__ = [
    "THEME",
    "apply_custom_css",
    "render_kpi_card",
    "render_kpi_metrics",
    "render_status_card",
    "render_alert_card",
    "render_section_header",
    "render_vehicle_type_card",
    "render_empty_state",
    "render_system_status",
    "create_vehicle_distribution_chart",
    "create_traffic_over_time_chart",
    "create_direction_chart",
    "create_density_gauge",
    "generate_csv_report",
    "generate_pdf_report",
    "render_top_header",
    "render_sidebar",
    "render_dashboard_page",
    "render_monitoring_page",
    "render_analytics_page",
    "render_events_page",
    "render_reports_page",
    "render_settings_page",
    "render_about_page",
]
