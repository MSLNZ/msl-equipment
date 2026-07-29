"""Recalibrations page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

from collections import deque
from datetime import date

import dash_ag_grid as dag  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, callback, dcc, html, register_page, set_props
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import cfg

from msl.equipment import Register, Status

register_page(__name__, name="Recalibrations", title=f"{cfg.nmi} | Recalibrations")  # type: ignore[no-untyped-call]

MONTHS_MIN = 0
MONTHS_MAX = 120


def layout(**params: str) -> html.Div:
    """Dynamically serve the layout when the page is opened.

    Args:
        params: Query parameters in the URL, e.g., /recalibrations?team=Light&months=6&sync=1
            Can specify multiple teams via `team=Light+Length`.
    """
    team = params.get("team", "").split()
    months = min(max(int(params.get("months", 6)), MONTHS_MIN), MONTHS_MAX)
    sync = params.get("sync", "no").lower() in {"1", "yes", "true"}
    return html.Div(
        [
            dbc.Stack(
                [
                    html.Div("Team(s): "),
                    dcc.Dropdown(
                        cfg.teams,
                        multi=True,
                        value=team,
                        id="rec-team-dropdown",
                        style={"width": "50%"},
                    ),
                    html.Div("Months: "),
                    html.Div(
                        dbc.Input(
                            id="rec-months-input",
                            value=months,
                            type="number",
                            min=MONTHS_MIN,
                            max=MONTHS_MAX,
                            step=1,
                            debounce=True,
                        )
                    ),
                    dbc.Tooltip(
                        "Number of months from today's date that a recalibration is due",
                        target="months-input",
                    ),
                    html.Div(
                        [
                            dbc.Label("Sync: ", html_for="sync-checkbox", className="me-2 mt-1"),
                            dbc.Checkbox(id="rec-sync-checkbox", value=sync),
                        ],
                        className="d-flex justify-content-end align-items-center",
                    ),
                    dbc.Tooltip(
                        "Whether to sync a register with its repository before checking",
                        target="sync-checkbox",
                    ),
                    dcc.Clipboard(
                        id="rec-clipboard",
                        style={
                            "fontSize": 20,
                            "verticalAlign": "top",
                            "marginLeft": 10,
                        },
                        className="me-auto",  # Push remaining components to the right
                    ),
                    dbc.Tooltip(
                        "Copy URL parameters to clipboard",
                        target="clipboard",
                    ),
                    dbc.Button(
                        "Download CSV",
                        id="rec-csv-button",
                        n_clicks=0,
                    ),
                ],
                gap=2,
                direction="horizontal",
                style={"margin": 25, "justifyContent": "center", "display": "flex"},
            ),
            dag.AgGrid(
                id="rec-table",
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
            html.Pre(id="rec-log-display", className="webapp-log-display"),
            html.Div(id="rec-hidden-div"),  # forces calling update_table() on page loading
            dcc.Location(id="rec-url", refresh=False),
        ],
    )


@callback(
    Output("rec-table", "exportDataAsCsv"),
    Input("rec-csv-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_data_as_csv(n_clicks: int) -> bool:
    """Export the data in the table as a CSV file."""
    return n_clicks > 0


@callback(
    Output("rec-months-input", "invalid"),
    Input("rec-months-input", "value"),
    prevent_initial_call=True,
)
def check_months_range(value: int | None) -> bool:
    """Check if the months value is out of range."""
    return value is None


@callback(
    Output("rec-clipboard", "content"),
    Input("rec-clipboard", "n_clicks"),
    State("rec-team-dropdown", "value"),
    State("rec-months-input", "value"),
    State("rec-sync-checkbox", "value"),
    State("rec-url", "href"),
    prevent_initial_call=True,
)
def clipboard_copy(_: int, teams: list[str], months: int | None, sync: bool, url: str) -> str:  # noqa: FBT001
    """Copy the URL with query parameters to the clipboard."""
    root = url.split("?", maxsplit=1)[0]
    params: list[str] = []
    if teams:
        params.append("team=" + "+".join(teams))
    if months is not None:  # can be None if the value is not in the specified [min, max] range
        params.append(f"months={months}")
    if sync:
        params.append("sync=1")
    return root + "?" + "&".join(params)


@callback(
    Output("rec-hidden-div", "children"),
    Input("rec-team-dropdown", "value"),
    Input("rec-months-input", "value"),
    Input("rec-sync-checkbox", "value"),
    running=[
        (Output("rec-team-dropdown", "disabled"), True, False),
        (Output("rec-months-input", "disabled"), True, False),
        (Output("rec-sync-checkbox", "disabled"), True, False),
    ],
    persistent=True,
)
async def update_table(teams: list[str], months: int | None, sync: bool) -> None:  # type: ignore[misc]  # noqa: C901, FBT001
    """Update the table data."""

    async def update(msg: str = "") -> None:
        """Requires the app to be created with Dash(websocket_callbacks=True, ...) for set_props to work."""
        if msg:
            log_buffer.append(msg)
        set_props("rec-log-display", {"children": "\n".join(log_buffer)})
        set_props("rec-table", {"rowData": data})
        await utils.process_events()

    log_buffer: deque[str] = deque()
    data: list[dict[str, str]] = []

    if (not teams) or (months is None):  # months is None when the value is out of the [MIN, MAX] range
        await update()
        return

    today = date.today()  # noqa: DTZ011
    registers = cfg.equipment_registers(teams)

    if sync:
        await update(f"Syncing register for {', '.join(teams)}")
        error_msg = await utils.git_pull(registers)
        if error_msg:
            await update(error_msg)

    for register in registers:
        await update(f"Validating {register.team} register (skipping sha256 checksums)")
        files = utils.find_xml_files(register.dir)
        if not utils.is_register_valid(*files):
            await update(f"  \u21b3 ERROR! {register.team} register invalid (skipping)")
            continue

        reg = Register(*files)
        await update(f"Checking {len(reg)} equipment entries for {register.team}")
        for equipment in reg:
            if equipment.traceable and equipment.status == Status.Active:
                for report in equipment.latest_reports(date="start"):
                    if report.is_calibration_due(months):
                        data.append(
                            {
                                "Team": reg.team,
                                "Due Date": report.next_calibration_date.isoformat(),
                                "Overdue?": "Yes" if report.next_calibration_date < today else "No",
                                "ID": equipment.id,
                                "Description": equipment.description,
                                "Manufacturer": equipment.manufacturer,
                                "Model": equipment.model,
                                "Serial": equipment.serial,
                            }
                        )
                        break  # no need to check other reports, since the equipment needs to be recalibrated
        await update()
