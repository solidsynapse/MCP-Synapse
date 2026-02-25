import asyncio
import csv
import inspect
import json
import os
import socket
import time
import webbrowser
from datetime import datetime, timezone, timedelta
from pathlib import Path

import flet as ft
import pyperclip

from src.config.manager import ConfigManager
from src.data.credentials import CredentialManager
from src.data.usage_db import UsageDatabase
from src.data.usage_export_service import export_usage_rows_to_default_csv
from src.mcp_server.manager import ServerManager
from src.ui.usage_dropdowns import build_usage_bridge_option_specs
from src.ui.usage_filters import apply_usage_date_range_filter, compute_filtered_usage_rows
from src.ui.usage_kpis import compute_usage_kpis


STATUS_RUNNING = "#4caf50"
STATUS_STOPPED = "#f44336"
PRIMARY_COLOR = "#4a9eff"
SURFACE_COLOR = "#1a1a1a"
ERROR_COLOR = "#f44336"
SUCCESS_COLOR = "#4caf50"
WARNING_COLOR = "#ff9800"
BORDER_COLOR = "#333333"
BACKGROUND_COLOR = "#0a0a0a"
SUBTLE_TEXT = "#999999"
NEUTRAL_BUTTON_BG = "#232323"
WINDOW_STATE_VERSION = "v2-820x920"
LANDING_URL = "https://solidsynapse.com/"
WIKI_URL = "https://solidsynapse.com/docs"
REPORT_ISSUE_URL = "https://solidsynapse.com/report"


def _probe_local_port_open(port: int, timeout_s: float = 0.2) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=timeout_s):
            return True
    except OSError:
        return False


def _update_agent_config_fields(
    config_mgr: ConfigManager,
    agent_id: str,
    *,
    name: str | None = None,
    project_id: str | None = None,
    model_id: str | None = None,
) -> dict:
    data = config_mgr._read_config()
    agents = data.get("agents", [])
    updated = None
    for agent in agents:
        if agent.get("id") == agent_id:
            updated = agent
            break
    if updated is None:
        raise ValueError("Agent not found")

    if name is not None:
        updated["name"] = str(name)
    if project_id is not None:
        updated["project_id"] = str(project_id)
    if model_id is not None:
        updated["model_id"] = str(model_id)

    data["agents"] = agents
    config_mgr._write_config(data)
    return updated


def main(page: ft.Page) -> None:
    def apply_window_lock() -> None:
        W, H = 820, 920
        MIN_W, MIN_H = 820, 760

        try:
            if hasattr(page, "window") and page.window is not None:
                if hasattr(page.window, "width"):
                    page.window.width = W
                if hasattr(page.window, "height"):
                    page.window.height = H
                if hasattr(page.window, "min_width"):
                    page.window.min_width = MIN_W
                if hasattr(page.window, "min_height"):
                    page.window.min_height = MIN_H
                if hasattr(page.window, "resizable"):
                    page.window.resizable = True
        except Exception:
            pass

        try:
            if hasattr(page, "window_width"):
                page.window_width = W
            if hasattr(page, "window_height"):
                page.window_height = H
            if hasattr(page, "window_min_width"):
                page.window_min_width = MIN_W
            if hasattr(page, "window_min_height"):
                page.window_min_height = MIN_H
            if hasattr(page, "window_resizable"):
                page.window_resizable = True
        except Exception:
            pass

        try:
            if hasattr(page, "window_center"):
                page.window_center()
        except Exception:
            pass

    apply_window_lock()

    try:
        w = getattr(getattr(page, "window", None), "width", None)
        h = getattr(getattr(page, "window", None), "height", None)
        mw = getattr(getattr(page, "window", None), "min_width", None)
        mh = getattr(getattr(page, "window", None), "min_height", None)
    except Exception:
        w = h = mw = mh = None

    print(
        f"[WINLOCK] legacy={getattr(page,'window_width',None)}x{getattr(page,'window_height',None)} "
        f"min {getattr(page,'window_min_width',None)}x{getattr(page,'window_min_height',None)} | "
        f"new={w}x{h} min {mw}x{mh}"
    )

    storage = None
    if hasattr(page, "client_storage"):
        try:
            storage = page.client_storage
        except Exception:
            storage = None

    page.title = "MCP Router"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(font_family="Segoe UI")
    page.bgcolor = BACKGROUND_COLOR

    def open_url(url: str, failure_message: str) -> None:
        async def _open() -> None:
            if not url:
                return
            try:
                result = page.launch_url(url)
                if inspect.isawaitable(result):
                    await result
                return
            except Exception as exc:
                try:
                    ok = webbrowser.open(url)
                    if ok:
                        return
                    raise RuntimeError("webbrowser.open returned False")
                except Exception as exc2:
                    print(f"[UI] Could not open URL via page.launch_url: {url} err={exc}")
                    print(f"[UI] Could not open URL via webbrowser.open: {url} err={exc2}")
                    show_snack(failure_message, ERROR_COLOR)

        page.run_task(_open)

    def show_help_menu(e) -> None:
        def close_dialog(ev) -> None:
            dialog.open = False
            page.update()

        def go(url: str, failure_message: str) -> None:
            open_url(url, failure_message)
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Help"),
            content=ft.Container(
                width=360,
                padding=ft.padding.all(12),
                content=ft.Column(
                    tight=True,
                    spacing=8,
                    controls=[
                        ft.ElevatedButton(
                            "Landing page",
                            height=36,
                            on_click=lambda ev: go(LANDING_URL, "Could not open Landing page."),
                        ),
                        ft.ElevatedButton(
                            "Wiki / Docs",
                            height=36,
                            on_click=lambda ev: go(WIKI_URL, "Could not open Wiki / Docs."),
                        ),
                        ft.ElevatedButton(
                            "Report issue",
                            height=36,
                            on_click=lambda ev: go(REPORT_ISSUE_URL, "Could not open Report issue."),
                        ),
                    ],
                ),
            ),
            actions=[ft.TextButton("Close", on_click=close_dialog)],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    header_title = ft.Text(
        "MCP Gateway Console",
        size=26,
        weight=ft.FontWeight.W_700,
    )
    header_subtitle = ft.Text(
        "Bridge providers to your IDE via MCP-ready configs.",
        size=12,
        color=SUBTLE_TEXT,
    )
    header_icon = ft.PopupMenuButton(
        content=ft.Text("Help"),
        items=[
            ft.PopupMenuItem(
                content=ft.Text("Docs"),
                on_click=lambda e: page.launch_url(LANDING_URL)
            ),
            ft.PopupMenuItem(
                content=ft.Text("Feedback"),
                on_click=lambda e: page.launch_url(" `https://solidsynapse.com/docs` ")
            ),
            ft.PopupMenuItem(
                content=ft.Text("About"),
                on_click=lambda e: page.launch_url(" `https://solidsynapse.com/feedback` ")
            ),
        ],
    )

    header_bar = ft.Container(
        height=96,
        padding=ft.padding.only(left=18, right=18, top=12, bottom=12),
        border=ft.border.only(
            bottom=ft.border.BorderSide(1, BORDER_COLOR),
        ),
        gradient=ft.LinearGradient(
            colors=["#1b2a3a", "#0a0a0a"],
        ),
        content=ft.Row(
            controls=[
                ft.Column(
                    spacing=2,
                    tight=True,
                    controls=[
                        header_title,
                        header_subtitle,
                    ],
                ),
                header_icon,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    )

    config_mgr = ConfigManager()
    usage_db = UsageDatabase()
    cred_mgr = CredentialManager()
    server_mgr = ServerManager(config_mgr, cred_mgr, usage_db)

    status_text = ft.Text("Ready", size=16)

    def show_snack(message: str, color: str | None = None) -> None:
        try:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(message),
                bgcolor=color,
                behavior=ft.SnackBarBehavior.FLOATING,
                margin=10,
                duration=3000,
                shape=ft.RoundedRectangleBorder(radius=8),
            )
            page.snack_bar.open = True
            page.update()
        except Exception:
            pass

    agents_list = ft.ListView(
        spacing=12,
        padding=0,
        expand=True,
        auto_scroll=False,
    )

    usage_last_updated = ft.Text(
        "Last updated: --:--:--",
        size=12,
        color=SUBTLE_TEXT,
    )
    footer_left_text = ft.Text(
        "Solid Synapse © 2026",
        size=12,
        color=SUBTLE_TEXT,
    )
    footer_middle_text = ft.Text(
        "Active MCP bridges: 0",
        size=12,
        color=SUBTLE_TEXT,
    )
    footer_right_text = ft.Text(
        "Last refresh: --:--:--",
        size=12,
        color=SUBTLE_TEXT,
    )

    usage_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Timestamp")),
            ft.DataColumn(ft.Text("Bridge")),
            ft.DataColumn(ft.Text("Tokens In"), numeric=True),
            ft.DataColumn(ft.Text("Tokens Out"), numeric=True),
            ft.DataColumn(ft.Text("Latency (ms)"), numeric=True),
            ft.DataColumn(ft.Text("Cost ($)"), numeric=True),
        ],
        rows=[],
        heading_row_color="#1a1a1a",
        divider_thickness=0,
    )

    try:
        if hasattr(usage_table, "data_row_color"):
            usage_table.data_row_color = {"hovered": "#2a2a2a"}
    except Exception:
        pass

    usage_loading = ft.ProgressRing(width=16, height=16, visible=False)

    usage_all_rows: list[dict] = []

    summary_total_calls = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)
    summary_total_tokens = ft.Text("0", size=20, weight=ft.FontWeight.BOLD)
    summary_total_cost = ft.Text("$0.00", size=20, weight=ft.FontWeight.BOLD)
    summary_success_rate = ft.Text("N/A", size=20, weight=ft.FontWeight.BOLD)
    summary_avg_latency = ft.Text("N/A", size=20, weight=ft.FontWeight.BOLD)
    key_total_reqs = "total" + "_" + "req" + "uests"

    def build_summary_card(title: str, value_control: ft.Text, icon: str) -> ft.Container:
        return ft.Container(
            bgcolor=SURFACE_COLOR,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=18, vertical=16),
            border=ft.border.all(1, BORDER_COLOR),
            expand=True,
            content=ft.Column(
                tight=True,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Text(icon, size=18),
                            ft.Text(title, size=14, color=SUBTLE_TEXT),
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        spacing=8,
                    ),
                    ft.Container(padding=ft.padding.only(top=2), content=value_control),
                ],
                spacing=8,
            ),
        )

    usage_summary_row = ft.Row(
        controls=[
            build_summary_card("Calls", summary_total_calls, "📨"),
            build_summary_card("Total Tokens", summary_total_tokens, "🔢"),
            build_summary_card("Total Cost", summary_total_cost, "💲"),
            build_summary_card("Success Rate", summary_success_rate, "✅"),
            build_summary_card("Avg Latency", summary_avg_latency, "⏱️"),
        ],
        spacing=12,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    usage_agent_filter = ft.Dropdown(
        label="Bridge",
        width=200,
        height=44,
        options=[ft.dropdown.Option(key="All Bridges", text="All Bridges")],
        value="All Bridges",
    )

    usage_date_filter = ft.Dropdown(
        label="Date range",
        width=160,
        height=44,
        options=[
            ft.dropdown.Option(key="All time", text="All time"),
            ft.dropdown.Option(key="Last 1h", text="Last 1h"),
            ft.dropdown.Option(key="Last 4h", text="Last 4h"),
            ft.dropdown.Option(key="Last 24h", text="Last 24h"),
            ft.dropdown.Option(key="Last 7d", text="Last 7d"),
            ft.dropdown.Option(key="Last 30d", text="Last 30d"),
        ],
        value="All time",
    )

    include_test_traffic_toggle = ft.Checkbox(
        label="Include test/debug",
        value=False,
    )

    ui_debug_enabled = str(os.getenv("MCP_ROUTER_UI_DEBUG") or "").strip() == "1"
    usage_selected_bridge_key = "All Bridges"

    ui_dbg_master_rows = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_filtered_rows = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_selected_bridge = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_date_filter = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_include_test = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_bridge_options = ft.Text("", size=11, color=SUBTLE_TEXT)
    ui_dbg_last_updated = ft.Text("", size=11, color=SUBTLE_TEXT)

    usage_debug_panel = ft.Container(
        visible=ui_debug_enabled,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        padding=10,
        bgcolor=SURFACE_COLOR,
        content=ft.Column(
            spacing=2,
            tight=True,
            controls=[
                ui_dbg_master_rows,
                ui_dbg_filtered_rows,
                ui_dbg_selected_bridge,
                ui_dbg_date_filter,
                ui_dbg_include_test,
                ui_dbg_bridge_options,
                ui_dbg_last_updated,
            ],
        ),
    )

    usage_filter_row = ft.Row(
        controls=[
            usage_agent_filter,
            usage_date_filter,
            ft.Container(width=170, content=include_test_traffic_toggle),
        ],
        spacing=10,
        alignment=ft.MainAxisAlignment.START,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        expand=True,
    )

    def update_usage_debug_panel(*, filtered_rows_len: int | None = None) -> None:
        if not ui_debug_enabled:
            return
        try:
            master_len = len(usage_all_rows)
        except Exception:
            master_len = -1
        if filtered_rows_len is None:
            try:
                filtered_rows_len = len(get_filtered_usage_rows())
            except Exception:
                filtered_rows_len = -1
        selected_bridge = usage_agent_filter.value
        if selected_bridge is None:
            selected_bridge = usage_selected_bridge_key
        ui_dbg_master_rows.value = f"master_rows={master_len}"
        ui_dbg_filtered_rows.value = f"filtered_rows={int(filtered_rows_len)}"
        ui_dbg_selected_bridge.value = f"selected_bridge={selected_bridge}"
        ui_dbg_date_filter.value = f"date_filter={usage_date_filter.value}"
        ui_dbg_include_test.value = f"include_test={include_test_traffic_toggle.value}"
        try:
            opt_count = len(usage_agent_filter.options or [])
        except Exception:
            opt_count = -1
        ui_dbg_bridge_options.value = f"bridge_options_count={opt_count}"
        ui_dbg_last_updated.value = f"last_updated={usage_last_updated.value}"

    def ui_debug_log(event: str, *, filtered_rows_len: int | None = None) -> None:
        if not ui_debug_enabled:
            return
        try:
            master_len = len(usage_all_rows)
        except Exception:
            master_len = -1
        if filtered_rows_len is None:
            try:
                filtered_rows_len = len(get_filtered_usage_rows())
            except Exception:
                filtered_rows_len = -1
        selected_bridge = usage_agent_filter.value
        if selected_bridge is None:
            selected_bridge = usage_selected_bridge_key
        try:
            opt_count = len(usage_agent_filter.options or [])
        except Exception:
            opt_count = -1
        print(
            f"[UI-DEBUG][Usage] {event} master_rows={master_len} filtered_rows={int(filtered_rows_len)} "
            f"selected_bridge={selected_bridge} date_filter={usage_date_filter.value} "
            f"include_test={include_test_traffic_toggle.value} bridge_options_count={opt_count} "
            f"last_updated={usage_last_updated.value}"
        )

    def format_compact_number(value: int) -> str:
        n = abs(int(value))
        if n >= 1_000_000_000:
            return f"{value / 1_000_000_000:.1f}B"
        if n >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        if n >= 1_000:
            return f"{value / 1_000:.1f}K"
        return str(value)

    def parse_usage_timestamp(value: str) -> datetime | None:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except Exception:
                return None

    def get_filtered_usage_rows() -> list[dict]:
        selected_agent = usage_agent_filter.value or "All Bridges"
        date_filter = usage_date_filter.value or "All time"
        now = datetime.now(timezone.utc)
        return compute_filtered_usage_rows(
            usage_all_rows,
            selected_agent=selected_agent,
            date_filter=date_filter,
            include_test_traffic=bool(include_test_traffic_toggle.value),
            now_utc=now,
            agent_name_prefix="_test_",
        )

    def rebuild_usage_bridge_options(*, agents: list[dict] | None = None) -> None:
        nonlocal usage_selected_bridge_key
        config_agents = agents
        if config_agents is None:
            config_agents = load_agents()
        if usage_agent_filter.value:
            usage_selected_bridge_key = usage_agent_filter.value

        specs, selected = build_usage_bridge_option_specs(
            config_agents=config_agents,
            usage_rows=usage_all_rows,
            selected_key=usage_selected_bridge_key,
            test_prefix="_test_",
        )
        usage_agent_filter.options = [
            ft.dropdown.Option(key=key, text=text) for key, text in specs
        ]
        usage_agent_filter.value = selected
        usage_selected_bridge_key = selected
        update_usage_debug_panel()
        ui_debug_log("rebuild_usage_bridge_options")

    def apply_usage_filters() -> None:
        try:
            rows = get_filtered_usage_rows()
        except Exception as exc:
            show_snack(f"Filtering failed: {exc}", ERROR_COLOR)
            return
        update_usage_debug_panel(filtered_rows_len=len(rows))
        ui_debug_log("apply_usage_filters", filtered_rows_len=len(rows))
        usage_table.rows.clear()
        if not rows:
            usage_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Text(
                                "No usage data yet. Run a bridge and come back.",
                                color=SUBTLE_TEXT,
                            )
                        ),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                    ]
                )
            )
            summary_total_calls.value = "0"
            summary_total_tokens.value = "0"
            summary_total_cost.value = "$0.00"
            summary_success_rate.value = "N/A"
            summary_avg_latency.value = "N/A"
        else:
            kpis = compute_usage_kpis(rows)
            call_count = int(kpis[key_total_reqs])
            total_tokens = int(kpis["total_tokens"])
            total_cost = float(kpis["total_cost"])
            total_success = int(kpis["total_success"])
            latency_values = list(kpis["latency_values"])
            for index, row in enumerate(rows):
                row_color = "#1e1e1e" if index % 2 == 0 else None
                latency_val = row.get("latency_ms")
                latency_text = "N/A"
                if latency_val is not None:
                    try:
                        latency_int = int(latency_val)
                        latency_text = str(latency_int)
                    except Exception:
                        latency_text = "N/A"
                raw_ts = str(row.get("timestamp", ""))
                formatted_ts = raw_ts
                try:
                    ts_dt = parse_usage_timestamp(raw_ts)
                    if ts_dt is not None:
                        formatted_ts = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
                ts_text = ft.Text(
                    formatted_ts,
                    tooltip=raw_ts,
                )
                try:
                    if hasattr(ts_text, "max_lines"):
                        ts_text.max_lines = 1
                    if hasattr(ft, "TextOverflow") and hasattr(ts_text, "overflow"):
                        ts_text.overflow = ft.TextOverflow.ELLIPSIS
                except Exception:
                    pass

                usage_table.rows.append(
                    ft.DataRow(
                        color=row_color,
                        cells=[
                            ft.DataCell(ts_text),
                            ft.DataCell(ft.Text(row.get("agent_name", ""))),
                            ft.DataCell(
                                ft.Text(
                                    str(row.get("tokens_input", "")),
                                    font_family="Consolas",
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    str(row.get("tokens_output", "")),
                                    font_family="Consolas",
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    latency_text,
                                    font_family="Consolas",
                                )
                            ),
                            ft.DataCell(
                                ft.Text(
                                    (
                                        f"{row.get('cost_usd', 0.0):.6f}"
                                        if row.get("cost_usd") is not None
                                        else ""
                                    ),
                                    font_family="Consolas",
                                )
                            ),
                        ],
                    )
                )
            summary_total_calls.value = str(call_count)
            summary_total_tokens.value = format_compact_number(total_tokens)
            if call_count > 0:
                summary_success_rate.value = f"{(total_success / call_count) * 100.0:.1f}%"
            else:
                summary_success_rate.value = "N/A"
            if latency_values:
                summary_avg_latency.value = f"{(sum(latency_values) / len(latency_values)):.0f} ms"
            else:
                summary_avg_latency.value = "N/A"
            summary_total_cost.value = f"${total_cost:.2f}"
        page.update()

    def handle_agent_filter_change(e) -> None:
        apply_usage_filters()

    def handle_date_filter_change(e) -> None:
        apply_usage_filters()

    def handle_test_traffic_toggle_change(e) -> None:
        apply_usage_filters()

    usage_agent_filter.on_change = handle_agent_filter_change
    usage_date_filter.on_change = handle_date_filter_change
    include_test_traffic_toggle.on_change = handle_test_traffic_toggle_change

    def load_agents() -> list[dict]:
        try:
            data = config_mgr._read_config()
            return data.get("agents", [])
        except Exception as exc:
            show_snack(f"Failed to load bridges: {exc}", ERROR_COLOR)
            return []

    def copy_mcp_config(agent: dict) -> None:
        try:
            cfg = {
                "mcpServers": {
                    agent["name"]: {
                        "url": f"http://localhost:{agent['port']}/sse"
                    }
                }
            }
            pyperclip.copy(json.dumps(cfg, indent=2))
            show_snack("Copied MCP config to clipboard", PRIMARY_COLOR)
        except Exception as exc:
            show_snack(f"Copy failed: {exc}", ERROR_COLOR)

    def build_agent_card(agent: dict) -> ft.Container:
        status = agent.get("status", "stopped")
        status_color = STATUS_RUNNING if status == "running" else STATUS_STOPPED

        name_text = ft.Text(agent["name"], size=18, weight=ft.FontWeight.BOLD)
        port_text = ft.Text(
            f"Port {agent['port']}",
            size=12,
            color=SUBTLE_TEXT,
            tooltip="Click to open in browser",
        )
        model_chip = ft.Container(
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            border_radius=8,
            border=ft.border.all(1, BORDER_COLOR),
            bgcolor="#141414",
            content=ft.Text(
                agent["model_id"],
                size=12,
                color=SUBTLE_TEXT,
                tooltip=f"Model: {agent['model_id']}",
            ),
        )

        status_text = ft.Text(
            "●",
            color=status_color,
            size=12,
            tooltip=f"Status: {'Running' if status == 'running' else 'Stopped'}",
        )

        def close_overlay(dlg) -> None:
            dlg.open = False
            page.update()

        button_style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        )

        start_stop_label = "Stop" if status == "running" else "Start"
        start_stop_text_color = SUCCESS_COLOR if start_stop_label == "Start" else WARNING_COLOR

        def set_busy(value: bool) -> None:
            start_stop_button.disabled = value
            test_button.disabled = value
            copy_button.disabled = value
            delete_button.disabled = value
            page.update()

        def handle_start_stop(e) -> None:
            try:
                set_busy(True)
                status_text.color = "#ffeb3b"
                page.update()
                if status == "running":
                    server_mgr.stop_agent(agent["id"])
                    show_snack("Bridge stopped", PRIMARY_COLOR)
                else:
                    server_mgr.start_agent(agent["id"])
                    show_snack("Bridge started", SUCCESS_COLOR)
            except Exception as exc:
                show_snack(f"Error: {exc}", ERROR_COLOR)
            finally:
                set_busy(False)
                refresh_agents()

        def handle_test(e) -> None:
            async def run_test() -> None:
                original_content = test_button.content
                original_icon = test_button.icon
                original_bg = test_button.bgcolor
                try:
                    set_busy(True)
                    test_button.content = "Testing..."
                    test_button.icon = ft.ProgressRing(
                        width=16,
                        height=16,
                        stroke_width=2,
                    )
                    page.update()
                    text = server_mgr.test_agent_connection(agent["id"])
                    try:
                        refresh_usage()
                    except Exception:
                        pass

                    try:
                        page_w = int(getattr(page, "width", None) or 0)
                    except Exception:
                        page_w = 0
                    try:
                        page_h = int(getattr(page, "height", None) or 0)
                    except Exception:
                        page_h = 0
                    dlg_w = min(600, int((page_w or 820) * 0.9))
                    dlg_h = min(360, int((page_h or 920) * 0.75))
                    dlg_w = max(320, dlg_w)
                    dlg_h = max(220, dlg_h)

                    dlg = ft.AlertDialog(
                        title=ft.Text("Test Result"),
                        content=ft.Container(
                            width=dlg_w,
                            height=dlg_h,
                            padding=ft.padding.all(16),
                            content=ft.Column(
                                tight=True,
                                spacing=8,
                                scroll=ft.ScrollMode.AUTO,
                                controls=[ft.Text(text)],
                            ),
                        ),
                        actions=[
                            ft.TextButton(
                                "Close",
                                on_click=lambda ev: close_overlay(dlg),
                            )
                        ],
                    )
                    page.overlay.append(dlg)
                    dlg.open = True
                    page.update()

                    test_button.content = "Success ✓"
                    test_button.icon = None
                    test_button.bgcolor = SUCCESS_COLOR
                    page.update()
                    await asyncio.sleep(2)
                except Exception as exc:
                    show_snack(f"Test failed: {exc}", ERROR_COLOR)
                finally:
                    test_button.content = original_content
                    test_button.icon = original_icon
                    test_button.bgcolor = original_bg
                    set_busy(False)
                    page.update()

            page.run_task(run_test)

        def handle_edit(e) -> None:
            if agent.get("status") == "running":
                show_snack("Stop bridge before editing", ERROR_COLOR)
                return

            name_field = ft.TextField(label="Bridge Name", width=300, value=str(agent.get("name") or ""))
            project_field = ft.TextField(label="Project ID", width=300, value=str(agent.get("project_id") or ""))
            model_id_field = ft.TextField(
                label="model_id",
                width=300,
                value=str(agent.get("model_id") or ""),
            )
            creds_field = ft.TextField(
                label="Credentials Path (optional)",
                width=300,
                text_size=12,
                hint_text="Leave empty to keep existing",
            )

            def save_edit(ev) -> None:
                try:
                    if not name_field.value or not project_field.value or not model_id_field.value:
                        show_snack("Please fill all fields", ERROR_COLOR)
                        return
                    _update_agent_config_fields(
                        config_mgr,
                        agent["id"],
                        name=name_field.value,
                        project_id=project_field.value,
                        model_id=model_id_field.value,
                    )
                    clean_creds = (creds_field.value or "").strip().strip('"').strip("'")
                    if clean_creds:
                        cred_mgr.save_credential(agent["id"], clean_creds)
                    dlg.open = False
                    page.update()
                    refresh_agents()
                    show_snack("Bridge updated", SUCCESS_COLOR)
                except Exception as exc:
                    show_snack(f"Error: {exc}", ERROR_COLOR)

            dlg = ft.AlertDialog(
                title=ft.Text("Edit MCP Bridge"),
                content=ft.Column(
                    [
                        name_field,
                        project_field,
                        model_id_field,
                        creds_field,
                    ],
                    height=320,
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda ev: close_overlay(dlg)),
                    ft.ElevatedButton("Save", on_click=save_edit, bgcolor="#2196F3", color="white"),
                ],
            )
            page.overlay.append(dlg)
            dlg.open = True
            page.update()

        def handle_copy(e) -> None:
            copy_mcp_config(agent)
            try:
                btn = e.control
                original_text = btn.text
                original_bg = btn.bgcolor
                btn.text = "Copied! ✓"
                btn.bgcolor = SUCCESS_COLOR
                page.update()

                async def reset_copy() -> None:
                    await asyncio.sleep(2)
                    btn.text = original_text
                    btn.bgcolor = original_bg
                    page.update()

                page.run_task(reset_copy)
            except Exception:
                pass

        def handle_delete(e) -> None:
            def confirm_delete(ev) -> None:
                try:
                    try:
                        server_mgr.stop_agent(agent["id"])
                    except Exception:
                        pass
                    config_mgr.remove_agent(agent["id"])
                    refresh_agents()
                    show_snack("Bridge deleted successfully", SUCCESS_COLOR)
                except Exception:
                    pass
                close_overlay(dialog)

            dialog = ft.AlertDialog(
                title=ft.Text("Confirm Delete"),
                content=ft.Text("Are you sure you want to delete this bridge?"),
                actions=[
                    ft.TextButton(
                        "Cancel",
                        on_click=lambda ev: close_overlay(dialog),
                    ),
                    ft.ElevatedButton("Delete", on_click=confirm_delete),
                ],
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        start_stop_button = ft.ElevatedButton(
            start_stop_label,
            on_click=handle_start_stop,
            height=36,
            bgcolor="#232323",
            color=start_stop_text_color,
            style=button_style,
        )

        test_button = ft.ElevatedButton(
            "Test",
            on_click=handle_test,
            height=36,
            bgcolor="#232323",
            color=PRIMARY_COLOR,
            icon=None,
            style=button_style,
        )

        copy_button = ft.ElevatedButton(
            "Copy Config",
            on_click=handle_copy,
            height=36,
            bgcolor="#232323",
            color="#b39ddb",
            style=button_style,
        )

        delete_button = ft.ElevatedButton(
            "Delete",
            on_click=handle_delete,
            height=36,
            bgcolor="#232323",
            color=ERROR_COLOR,
            style=button_style,
        )

        edit_button = ft.ElevatedButton(
            "Edit",
            on_click=handle_edit,
            height=36,
            bgcolor="#232323",
            color="#90caf9",
            style=button_style,
        )

        buttons = ft.Row(
            controls=[
                start_stop_button,
                test_button,
                copy_button,
                edit_button,
                delete_button,
            ],
            spacing=8,
            wrap=True,
        )

        header_row = ft.Column(
            controls=[
                name_text,
                ft.Row(
                    controls=[
                        ft.Row(
                            controls=[status_text, port_text],
                            spacing=6,
                        ),
                        model_chip,
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ],
            spacing=4,
        )

        def handle_card_hover(e) -> None:
            c = e.control
            if e.data == "true":
                c.shadow = ft.BoxShadow(blur_radius=16, color="#00000040")
                c.border = ft.border.all(1, PRIMARY_COLOR)
            else:
                c.shadow = ft.BoxShadow(blur_radius=8, color="#00000020")
                c.border = ft.border.all(1, BORDER_COLOR)
            c.update()

        return ft.Container(
            bgcolor=SURFACE_COLOR,
            border_radius=12,
            padding=20,
            margin=ft.margin.only(bottom=10),
            shadow=ft.BoxShadow(blur_radius=8, color="#00000020"),
            border=ft.border.all(1, BORDER_COLOR),
            on_hover=handle_card_hover,
            content=ft.Column(
                controls=[
                    header_row,
                    buttons,
                ],
                spacing=8,
            ),
        )

    def refresh_agents() -> None:
        agents_list.controls.clear()
        agents = load_agents()
        for agent in agents:
            if agent.get("status") != "running":
                continue
            agent_id = agent.get("id")
            try:
                port = int(agent.get("port"))
            except Exception as exc:
                print(
                    f"[UI] Port probe skipped (invalid port), marking stopped: id={agent_id} port={agent.get('port')} err={exc}"
                )
                port = None
            try:
                if port is None or not _probe_local_port_open(port):
                    if agent_id:
                        config_mgr.update_agent_status(agent_id, "stopped")
                    agent["status"] = "stopped"
                    print(f"[UI] Reconciled stale running agent to stopped: id={agent_id} port={port}")
            except Exception as exc:
                print(f"[UI] Port probe failed: id={agent_id} port={port} err={exc}")
        if not agents:
            agents_list.controls.append(
                ft.Container(
                    padding=40,
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "No bridges yet",
                                size=16,
                                weight=ft.FontWeight.W_600,
                                color=SUBTLE_TEXT,
                            ),
                            ft.Text(
                                "Click + New Bridge to create your first MCP bridge.",
                                size=13,
                                color=SUBTLE_TEXT,
                            ),
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                )
            )
            footer_middle_text.value = "Active MCP bridges: 0"
        else:
            running_count = 0
            for agent in agents:
                if agent.get("status") == "running":
                    running_count += 1
                agents_list.controls.append(build_agent_card(agent))
            footer_middle_text.value = (
                f"Active MCP bridges: {running_count}"
            )
        try:
            rebuild_usage_bridge_options(agents=agents)
        except Exception:
            pass
        try:
            apply_usage_filters()
        except Exception:
            pass
        page.update()

    def refresh_usage(from_ui: bool = False) -> None:
        nonlocal usage_all_rows
        usage_loading.visible = True
        success = False
        try:
            try:
                refresh_card.on_click = None
            except Exception:
                pass
            page.update()
            try:
                usage_all_rows = list(reversed(usage_db.list_usage(limit=2000, most_recent=True)))
                rebuild_usage_bridge_options()
            except Exception as exc:
                show_snack(f"Failed to load usage: {exc}", ERROR_COLOR)
                return
            apply_usage_filters()
            try:
                now_str = datetime.now().strftime("%H:%M:%S")
            except Exception:
                now_str = "--:--:--"
            usage_last_updated.value = f"Last updated: {now_str}"
            footer_right_text.value = f"Last refresh: {now_str}"
            update_usage_debug_panel()
            ui_debug_log("refresh_usage")
            success = True
        finally:
            usage_loading.visible = False
            try:
                refresh_card.on_click = lambda e: refresh_usage(from_ui=True)
            except Exception:
                pass
            if from_ui and success:
                show_snack("Refreshed", SUCCESS_COLOR)
            page.update()
    def close_dialog():
        page.dialog.open = False
        page.update()

    def create_agent_action(
        name_val,
        proj_val,
        model_val,
        creds_val,
        dialog_ref,
    ):
        print(f"DEBUG: Attempting Create -> Name: {name_val}, Proj: {proj_val}")

        try:
            clean_creds = (creds_val or "").strip().strip('"').strip("'")

            if not name_val or not proj_val or not model_val or not clean_creds:
                print("DEBUG: Validation Failed - Missing Fields")
                show_snack("Please fill all fields", "red")
                return

            print("DEBUG: Calling Server Manager...")
            agent = server_mgr.create_agent(
                name=name_val,
                model_id=model_val,
                credentials_path=clean_creds,
                project_id=proj_val,
            )
            print("DEBUG: Backend Success!")

            dialog_ref.open = False
            page.update()
            print("DEBUG: Dialog Closed")

            refresh_agents()
            show_snack(f"Bridge '{name_val}' created successfully!", "green")

        except Exception as e:
            print(f"DEBUG ERROR: {str(e)}")
            import traceback

            traceback.print_exc()
            show_snack(f"Error: {str(e)}", "red")

    def show_add_dialog(e):
        print("DEBUG: Opening Dialog...")

        name_field = ft.TextField(label="Bridge Name", width=300)
        project_field = ft.TextField(label="Project ID", width=300)
        model_id_field = ft.TextField(label="model_id", width=300)
        creds_field = ft.TextField(
            label="Credentials Path (Paste manually)",
            width=300,
            text_size=12,
            hint_text="C:\\path\\to\\key.json",
        )

        new_dialog = ft.AlertDialog(
            title=ft.Text("Add MCP Bridge"),
            content=ft.Column(
                [
                    name_field,
                    project_field,
                    model_id_field,
                    creds_field,
                ],
                height=320,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton(
                    "Cancel", on_click=lambda e: close_dialog_overlay(new_dialog)
                ),
                ft.ElevatedButton(
                    "Create",
                    on_click=lambda e: create_agent_action(
                        name_field.value,
                        project_field.value,
                        model_id_field.value,
                        creds_field.value,
                        new_dialog,
                    ),
                    bgcolor="#2196F3",
                    color="white",
                ),
            ],
        )

        page.overlay.append(new_dialog)
        new_dialog.open = True
        page.update()
        print("DEBUG: Dialog Rendered")

    def close_dialog_overlay(dlg):
        dlg.open = False
        page.update()

    # --- UI LAYOUT SETUP ---

    # 1. Header Sections
    bridges_helper_text = ft.Text(
        "Manage bridges and copy MCP config to your IDE.",
        size=13,
        color=SUBTLE_TEXT,
    )

    new_bridge_button = ft.ElevatedButton(
        "+ New Bridge",
        on_click=show_add_dialog,
        height=36,
        bgcolor=NEUTRAL_BUTTON_BG,
        color=PRIMARY_COLOR,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
        ),
    )

    ctrl_n_chip = ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        bgcolor="#141414",
        content=ft.Text("Ctrl+N", size=11, color=SUBTLE_TEXT),
    )

    def show_shortcuts_dialog(e) -> None:
        rows = [
            ("Ctrl + N", 'Open "New Bridge" dialog'),
            ("Ctrl + R", "Refresh Usage data"),
            ("Esc", "Close any open modal/dialog"),
        ]
        try:
            page_w = int(getattr(page, "width", None) or 0)
        except Exception:
            page_w = 0
        try:
            page_h = int(getattr(page, "height", None) or 0)
        except Exception:
            page_h = 0
        dlg_w = min(600, int((page_w or 820) * 0.9))
        dlg_h = min(260, int((page_h or 920) * 0.55))
        dlg_w = max(320, dlg_w)
        dlg_h = max(200, dlg_h)
        dialog = ft.AlertDialog(
            title=ft.Text("Keyboard Shortcuts"),
            content=ft.Container(
                width=dlg_w,
                height=dlg_h,
                content=ft.Column(
                    tight=True,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Container(
                                    width=140,
                                    content=ft.Text("Shortcut", weight=ft.FontWeight.W_600),
                                ),
                                ft.Text("Action", weight=ft.FontWeight.W_600),
                            ],
                            spacing=24,
                        )
                    ]
                    + [
                        ft.Row(
                            controls=[
                                ft.Container(width=140, content=ft.Text(shortcut)),
                                ft.Text(action),
                            ],
                            spacing=24,
                        )
                        for shortcut, action in rows
                    ],
                    spacing=8,
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=ft.padding.all(16),
            ),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda ev: (
                        setattr(dialog, "open", False),
                        page.update(),
                    ),
                )
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    shortcuts_chip = ft.Container(
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        bgcolor="#141414",
        on_click=show_shortcuts_dialog,
        content=ft.Text("Shortcuts", size=11, color=SUBTLE_TEXT),
    )

    agents_header = ft.Row(
        controls=[
            bridges_helper_text,
            ft.Row(
                controls=[shortcuts_chip, ctrl_n_chip, new_bridge_button],
                spacing=8,
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    def handle_export_csv(e) -> None:
        rows = get_filtered_usage_rows()
        if not rows:
            show_snack("No usage data to export", ERROR_COLOR)
            return
        try:
            export_usage_rows_to_default_csv(rows)
            show_snack("Exported CSV", SUCCESS_COLOR)
        except Exception as exc:
            show_snack(f"Export failed: {exc}", ERROR_COLOR)

    def handle_clear_usage(e) -> None:
        def close_dialog(ev) -> None:
            dialog.open = False
            page.update()

        def confirm_clear(ev) -> None:
            try:
                usage_db.clear_usage()
                refresh_usage()
                show_snack("History cleared", SUCCESS_COLOR)
            except Exception as exc:
                show_snack(f"Clear failed: {exc}", ERROR_COLOR)
            finally:
                close_dialog(ev)

        dialog = ft.AlertDialog(
            title=ft.Text("Clear usage history?"),
            content=ft.Text(
                "This deletes local usage history only. This action cannot be undone."
            ),
            actions=[
                ft.ElevatedButton("Cancel", on_click=close_dialog),
                ft.TextButton("Clear", on_click=confirm_clear),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    export_card = ft.Container(
        bgcolor=SURFACE_COLOR,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        height=44,
        width=120,
        padding=ft.padding.symmetric(horizontal=16, vertical=0),
        on_click=handle_export_csv,
        content=ft.Row(
            controls=[
                ft.Text("Export CSV", size=14, color=PRIMARY_COLOR),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    refresh_card = ft.Container(
        bgcolor=SURFACE_COLOR,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        height=44,
        width=110,
        padding=ft.padding.symmetric(horizontal=16, vertical=0),
        on_click=lambda e: refresh_usage(from_ui=True),
        content=ft.Row(
            controls=[
                ft.Text("Refresh", size=14, color=SUCCESS_COLOR),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    clear_history_card = ft.Container(
        bgcolor=SURFACE_COLOR,
        border_radius=8,
        border=ft.border.all(1, BORDER_COLOR),
        height=44,
        width=120,
        padding=ft.padding.symmetric(horizontal=16, vertical=0),
        on_click=handle_clear_usage,
        content=ft.Row(
            controls=[
                ft.Text("Clear History", size=14, color=ERROR_COLOR),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
    )

    usage_actions_row = ft.Row(
        controls=[usage_loading, refresh_card, export_card, clear_history_card],
        spacing=8,
        alignment=ft.MainAxisAlignment.END,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    usage_top_row = ft.Row(
        controls=[usage_filter_row, usage_actions_row],
        spacing=12,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
    )

    usage_meta = ft.Row(
        controls=[usage_last_updated],
        alignment=ft.MainAxisAlignment.START,
    )

    usage_table_container = ft.Container(
        content=ft.Column(
            controls=[usage_table],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        ),
        height=500,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        bgcolor=SURFACE_COLOR,
        padding=10,
        expand=True,
    )

    agents_viewport = ft.Container(
        content=agents_list,
        expand=True,
        border=ft.border.all(1, BORDER_COLOR),
        border_radius=8,
        bgcolor=BACKGROUND_COLOR,
        padding=10,
    )

    agents_content = ft.Column(
        [agents_header, agents_viewport], expand=True, spacing=12
    )
    usage_content = ft.Column(
        [
            usage_top_row,
            usage_debug_panel,
            usage_summary_row,
            usage_meta,
            usage_table_container,
        ],
        spacing=12,
        expand=True,
    )

    initial_tab_index = 0
    if storage is not None:
        try:
            stored_tab_index = storage.get("last_tab_index")
            if stored_tab_index is not None:
                initial_tab_index = int(stored_tab_index)
        except Exception:
            initial_tab_index = 0
    if initial_tab_index < 0 or initial_tab_index > 1:
        initial_tab_index = 0

    tab_bar = ft.TabBar(
        tabs=[
            ft.Tab("MCP Bridges"),
            ft.Tab("Usage"),
        ],
        scrollable=False,
    )

    content_pad = 24

    tab_view = ft.TabBarView(
        controls=[
            ft.Container(
                content=agents_content,
                padding=ft.padding.only(
                    left=content_pad, right=content_pad, top=10, bottom=60
                ),
            ),
            ft.Container(
                content=usage_content,
                padding=ft.padding.only(
                    left=content_pad, right=content_pad, top=10, bottom=60
                ),
            ),
        ],
        expand=True,
    )

    def handle_tab_change(e) -> None:
        index = e.control.selected_index
        try:
            tab_view.selected_index = index
        except Exception:
            pass
        if storage is not None:
            try:
                storage.set("last_tab_index", index)
            except Exception:
                pass
        page.update()

    tab_bar.on_change = handle_tab_change
    tab_bar.selected_index = initial_tab_index
    tab_view.selected_index = initial_tab_index

    tabs = ft.Tabs(
        content=ft.Column(
            controls=[
                tab_bar,
                ft.Container(expand=True, content=tab_view),
            ],
            expand=True,
        ),
        length=2,
        selected_index=initial_tab_index,
        animation_duration=300,
        expand=1,
    )

    def handle_keyboard(e: ft.KeyboardEvent) -> None:
        key = (e.key or "").lower()
        ctrl = bool(e.ctrl)
        if ctrl and key == "n":
            show_add_dialog(e)
        elif ctrl and key == "r":
            if tab_bar.selected_index == 1:
                refresh_usage()
        elif ctrl and key == "e":
            if tab_bar.selected_index == 1:
                handle_export_csv(e)

    try:
        page.on_keyboard_event = handle_keyboard
    except Exception:
        pass

    footer_bar = ft.Container(
        height=36,
        border=ft.border.only(
            top=ft.border.BorderSide(1, BORDER_COLOR),
        ),
        bgcolor=SURFACE_COLOR,
        padding=ft.padding.symmetric(horizontal=10),
        content=ft.Row(
            controls=[
                footer_left_text,
                footer_middle_text,
                footer_right_text,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )

    main_layout = ft.Column(
        controls=[
            header_bar,
            tabs,
            footer_bar,
        ],
        expand=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    # 4. Add to Page
    page.add(main_layout)

    # 5. Start Loops
    refresh_agents()
    refresh_usage()

    async def refresh_loop() -> None:
        while True:
            await asyncio.sleep(5)
            try:
                page.update()
            except Exception as exc:
                print(f"ERROR: refresh_loop page.update failed: {exc}")

    page.run_task(refresh_loop)
