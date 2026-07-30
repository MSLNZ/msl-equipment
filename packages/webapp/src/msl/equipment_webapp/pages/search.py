"""Search page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportMissingTypeStubs=false
from __future__ import annotations

import re
from collections import deque
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote

import dash_ag_grid as dag  # type: ignore[import-untyped]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import Input, Output, State, callback, dcc, html, register_page, set_props
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import cfg

from msl.equipment import Register

if TYPE_CHECKING:
    from typing import Literal

register_page(__name__, name="Search", title=f"{cfg.nmi} | Search")  # type: ignore[no-untyped-call]


def layout(**params: str) -> html.Div:
    """Dynamically serve the layout when the page is opened.

    Args:
        params: Query parameters in the URL, e.g., /search?team=Light&text=laser&sync=1
            Can specify multiple teams via `team=Light+Length`.
    """
    team = params.get("team", "").split()
    text = unquote(params.get("text", ""))
    sync = params.get("sync", "no").lower() in {"1", "yes", "true"}
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Team(s):", className="me-2 mb-0", style={"marginLeft": 25}),
                            dcc.Dropdown(
                                cfg.teams,
                                multi=True,
                                value=team,
                                id="search-team-dropdown",
                                className="flex-grow-1",
                                style={
                                    "minWidth": "150px",
                                    "width": "auto",
                                    "display": "inline-block",
                                },
                            ),
                        ],
                        width="auto",
                        className="d-flex align-items-center mb-2 mb-md-0",
                    ),
                    dbc.Col(
                        [
                            dbc.Input(
                                id="search-input",
                                placeholder="Search pattern",
                                type="text",
                                debounce=len(text) == 0,
                                value=text,
                                className="flex-grow-1",
                                style={
                                    "minWidth": "150px",
                                    "fieldSizing": "content",
                                },
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(dbc.ModalTitle("Invalid Syntax")),
                                    dbc.ModalBody(id="search-modal-body"),
                                ],
                                id="search-modal",
                                is_open=False,
                            ),
                        ],
                        width="auto",
                        className="d-flex mb-2 mb-md-0",
                    ),
                    dbc.Col(
                        html.Div(
                            [
                                dbc.Label(
                                    "Sync:",
                                    html_for="search-sync-checkbox",
                                    className="me-2 mb-0",
                                ),
                                dbc.Checkbox(
                                    id="search-sync-checkbox",
                                    value=sync,
                                ),
                            ],
                            className="d-flex align-items-center",
                        ),
                        width="auto",
                    ),
                    dbc.Col(
                        dcc.Clipboard(
                            id="search-clipboard",
                            style={"fontSize": 20},
                        ),
                        width="auto",
                        className="me-auto",  # Pushes the Download button to the far right
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Download CSV",
                            id="search-csv-button",
                            n_clicks=0,
                            style={"marginRight": 25},
                        ),
                        width="auto",
                    ),
                    dbc.Tooltip(
                        "Whether to sync a register with its repository before searching",
                        target="search-sync-checkbox",
                    ),
                    dbc.Tooltip(
                        "Copy URL parameters to clipboard",
                        target="search-clipboard",
                    ),
                ],
                className="g-2 align-items-center my-4 mx-0",
            ),
            html.Div(
                dag.AgGrid(
                    id="search-table",
                    columnDefs=[
                        {"field": "ID", "width": 150},
                        {"field": "Team", "flex": 1},
                        {"field": "Location", "flex": 2},
                        {"field": "Description", "flex": 3},
                        {"field": "Manufacturer", "flex": 2},
                        {"field": "Model", "flex": 1},
                        {"field": "Serial", "flex": 1},
                    ],
                    defaultColDef={"filter": True, "resizable": True},
                    dashGridOptions={
                        "pagination": True,
                        "theme": "themeAlpine",
                        "loading": False,
                        "enableCellTextSelection": True,
                        "ensureDomOrder": True,  # required for enableCellTextSelection=True
                    },
                    csvExportParams={
                        "fileName": "equipment.csv",
                    },
                    getRowStyle={
                        "styleConditions": [
                            {
                                "condition": "params.rowIndex % 2 === 0",
                                "style": {"background-color": "#F3F2F1", "color": "black"},
                            },
                        ]
                    },
                    style={"width": "100%", "height": "65vh"},
                ),
                style={"width": "100%", "overflowX": "auto"},
            ),
            html.Pre(id="search-log-display", className="webapp-log-display"),
            dcc.Location(id="search-url", refresh=False),
        ],
        style={"maxWidth": "100vw", "overflowX": "hidden", "padding": "0 5px"},
    )


@callback(
    Output("search-table", "exportDataAsCsv"),
    Input("search-csv-button", "n_clicks"),
    prevent_initial_call=True,
)
def export_data_as_csv(n_clicks: int) -> bool:
    """Export the data in the table as a CSV file."""
    return n_clicks > 0


@callback(
    Output("search-clipboard", "content"),
    Input("search-clipboard", "n_clicks"),
    State("search-team-dropdown", "value"),
    State("search-input", "value"),
    State("search-sync-checkbox", "value"),
    State("search-url", "href"),
    prevent_initial_call=True,
)
def clipboard_copy(_: int, teams: list[str], text: str | None, sync: bool, url: str) -> str:  # noqa: FBT001
    """Copy the URL with query parameters to the clipboard."""
    root = url.split("?", maxsplit=1)[0]
    params: list[str] = []
    if teams:
        params.append("team=" + "+".join(teams))
    if text:
        params.append(f"text={quote(text)}")
    if sync:
        params.append("sync=1")
    return root + "?" + "&".join(params)


@callback(
    Output("search-input", "debounce"),
    Output("search-modal", "is_open"),
    Output("search-modal-body", "children"),
    Input("search-team-dropdown", "value"),
    Input("search-input", "value"),
    Input("search-sync-checkbox", "value"),
    running=[
        (Output("search-team-dropdown", "disabled"), True, False),
        (Output("search-input", "disabled"), True, False),
        (Output("search-sync-checkbox", "disabled"), True, False),
    ],
    persistent=True,
)
async def update_table(teams: list[str], text: str | None, sync: bool) -> tuple[Literal[True], bool, str | None]:  # type: ignore[misc]  # noqa: FBT001
    """Update the table data.

    Always force `debounce=True` when returning. When initially loading the page,
    defining `debounce=False` is necessary to trigger a callback if `text=...` is
    specified as a URL query parameter. Afterwards we only want the callback to be
    triggered when ENTER is pressed or the Input component looses focus.
    """

    async def update(msg: str = "") -> None:
        """Requires the app to be created with Dash(websocket_callbacks=True, ...) for set_props to work."""
        if msg:
            log_buffer.append(msg)
        set_props("search-log-display", {"children": "\n".join(log_buffer)})
        set_props("search-table", {"rowData": data})
        await utils.process_events()

    log_buffer: deque[str] = deque()
    data: list[dict[str, str]] = []

    pattern: str | re.Pattern[str] = "."
    if text:
        try:
            pattern = re.compile(text)
        except re.PatternError as e:
            return True, True, f"{e.__class__.__name__}: {e}"

    if (not teams) or (not text):
        await update()
        return True, False, None

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
            await update(f"  \u274c ERROR! {register.team} register invalid (skipping)")
            continue

        reg = Register(*files)
        await update(f"Searching {len(reg)} equipment entries from {register.team}")
        data.extend(
            {
                "ID": equipment.id,
                "Team": reg.team,
                "Location": equipment.location,
                "Description": equipment.description,
                "Manufacturer": equipment.manufacturer,
                "Model": equipment.model,
                "Serial": equipment.serial,
            }
            for equipment in reg.find(pattern)
        )
        await update()

    return True, False, None
