"""Recalibrations page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import asyncio
from collections import deque
from datetime import date

import dash
import dash_ag_grid as dag  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, dcc, html, set_props
from msl.equipment_webapp.config import cfg

from msl import equipment_validate as ev
from msl.equipment import Register, Status

dash.register_page(__name__, name="Recalibrations", title=f"{cfg.nmi} | Recalibrations")  # type: ignore[no-untyped-call]

app: dash.Dash = dash.get_app()  # type: ignore[no-untyped-call]


def layout(**params: str) -> html.Div:
    """Dynamically serve the layout when the page is opened.

    Args:
        params: Query parameters in the URL, e.g., /recalibrations?team=Light&months=6&sync=1
            Can specify multiple teams via `team=Light+Length`.
    """
    team = params.get("team", "").split()
    months = int(params.get("months", 6))
    sync = params.get("sync", "no").lower() in {"1", "yes", "true"}
    return html.Div(
        [
            dbc.Stack(
                [
                    html.Div("Team(s): "),
                    dcc.Dropdown(cfg.teams, multi=True, value=team, id="team-dropdown", style={"width": "50%"}),
                    html.Div("Months: "),  # , style={"marginLeft": 25}),
                    html.Div(dbc.Input(value=months, type="number", min=0, max=100, step=1, id="months-input")),
                    dbc.Tooltip(
                        "Number of months from today's date that a recalibration is due", target="months-input"
                    ),
                    dbc.Checklist(
                        id="sync-checkbox",
                        options=[{"label": "Sync", "value": "sync"}],
                        value=["sync"] if sync else [],
                    ),
                    dbc.Tooltip(
                        "Whether to sync a register with its repository before checking",
                        target="sync-checkbox",
                    ),
                    dcc.Clipboard(
                        id="clipboard",
                        style={
                            "fontSize": 20,
                            "verticalAlign": "top",
                        },
                        className="me-auto",  # Push remaining components to the right
                    ),
                    dbc.Tooltip(
                        "Copy URL parameters to clipboard",
                        target="clipboard",
                    ),
                    dbc.Button(
                        "Download CSV",
                        id="csv-button",
                        n_clicks=0,
                    ),
                ],
                gap=2,
                direction="horizontal",
                style={"margin": 25, "justifyContent": "center", "display": "flex"},
            ),
            dag.AgGrid(
                id="table",
                columnDefs=[
                    {"field": "Team", "width": 110},
                    {"field": "Due Date", "width": 110},
                    {"field": "Overdue?", "width": 110},
                    {"field": "ID", "width": 150},
                    {"field": "Description"},
                    {"field": "Manufacturer"},
                    {"field": "Model"},
                    {"field": "Serial", "flex": 1},
                ],
                defaultColDef={"filter": True},
                dashGridOptions={
                    "pagination": True,
                    "theme": "themeAlpine",
                    "loading": False,
                    "enableCellTextSelection": True,
                    "ensureDomOrder": True,  # required for enableCellTextSelection=True
                },
                csvExportParams={
                    "fileName": "recalibrations.csv",
                },
                getRowStyle={
                    "styleConditions": [
                        {
                            "condition": "params.rowIndex % 2 === 0",
                            "style": {"background-color": "#F3F2F1", "color": "black"},
                        },
                    ]
                },
            ),
            html.Pre(
                id="log-display",
                style={
                    "backgroundColor": "#1e1e1e",
                    "color": "#ffffff",
                    "padding": "15px",
                    "overflowY": "auto",
                    "fontFamily": "monospace",
                    "borderRadius": "5px",
                },
            ),
            html.Div(id="hidden-div"),  # forces calling update_table() on page loading
            dcc.Location(id="url", refresh=False),
        ],
    )


@app.callback(
    Output("table", "exportDataAsCsv"),
    Input("csv-button", "n_clicks"),
)
def export_data_as_csv(n_clicks: int) -> bool:  # type: ignore[misc]
    """Export the data in the table as a CSV file."""
    return n_clicks > 0


@app.callback(
    Output("months-input", "invalid"),
    Input("months-input", "value"),
)
def check_months_range(value: int | None) -> bool:  # type: ignore[misc]
    """Check if the months value is out of range."""
    return value is None


@app.callback(
    Output("clipboard", "content"),
    Input("clipboard", "n_clicks"),
    State("team-dropdown", "value"),
    State("months-input", "value"),
    State("sync-checkbox", "value"),
    State("url", "href"),
)
def custom_copy(_: int, teams: list[str], months: int | None, sync: list[str], url: str) -> str:  # type: ignore[misc]
    """Copy the URL and query parameters to the clipboard."""
    root = url.split("?", maxsplit=1)[0]
    params: list[str] = []
    if teams:
        params.append("team=" + "+".join(teams))
    if months is not None:
        params.append(f"months={months}")
    if sync:
        params.append("sync=1")
    return root + "?" + "&".join(params)


@app.callback(
    Output("hidden-div", "children"),
    Input("team-dropdown", "value"),
    Input("months-input", "value"),
    Input("sync-checkbox", "value"),
)
async def update_table(teams: list[str], months: int | None, sync: list[str]) -> None:  # type: ignore[misc]  # noqa: C901
    """Update the table data."""
    log_buffer: deque[str] = deque()
    data: list[dict[str, str]] = []

    async def update(msg: str = "") -> None:
        """Uses Dash(websocket_callbacks=True) to update properties in real time."""
        if msg:
            log_buffer.append(msg)
        set_props("log-display", {"children": "\n".join(log_buffer)})
        set_props("table", {"rowData": data})
        await asyncio.sleep(0.01)

    if (not teams) or (months is None):  # months is None when value is out of [min, max] range
        await update()
        return

    today = date.today()  # noqa: DTZ011
    registers = [t for t in cfg.registers if t.team in teams]
    for register in registers:
        if sync and (register.dir / ".git").exists():
            await update(f"Syncing {register.team!r} repository")
            error_msg = register.git_pull()
            if error_msg:
                await update(error_msg)

        for file in ev.recursive(register.dir):
            file_name = file.name
            await update(f"Validating {register.team!r} register file {file_name!r}")
            num_issues = ev.cli([str(file), "--skip-checksum", "--exit-first", "-qqq"])
            if num_issues > 0:
                await update(f"ERROR! There are {num_issues} issues, skipping {file_name!r}")
                continue

            await update(f"Checking {register.team!r} reports in {file_name!r}")
            for equipment in Register(file):
                if equipment.traceable and equipment.status == Status.Active:
                    for report in equipment.latest_reports(date="start"):
                        if report.is_calibration_due(months):
                            data.append(
                                {
                                    "Team": register.team,
                                    "Due Date": report.next_calibration_date.isoformat(),
                                    "Overdue?": "Yes" if report.next_calibration_date < today else "No",
                                    "ID": equipment.id,
                                    "Description": equipment.description,
                                    "Manufacturer": equipment.manufacturer,
                                    "Model": equipment.model,
                                    "Serial": equipment.serial,
                                }
                            )
                            await update()
                            break
