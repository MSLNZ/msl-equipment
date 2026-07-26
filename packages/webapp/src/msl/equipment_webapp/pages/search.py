"""Search page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import asyncio
from collections import deque
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote

import dash
import dash_ag_grid as dag  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, dcc, html, set_props
from msl.equipment_webapp.config import cfg

from msl import equipment_validate as ev
from msl.equipment import Register

if TYPE_CHECKING:
    from typing import Literal

dash.register_page(__name__, name="Search", title=f"{cfg.nmi} | Search")  # type: ignore[no-untyped-call]

app: dash.Dash = dash.get_app()  # type: ignore[no-untyped-call]


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
            dbc.Stack(
                [
                    html.Div("Team(s): "),
                    dcc.Dropdown(cfg.teams, multi=True, value=team, id="team-dropdown", style={"width": "50%"}),
                    dbc.Input(
                        id="search-input",
                        placeholder="Enter search text (can be regular-expression pattern)",
                        type="text",
                        debounce=len(text) == 0,  # if `text` is a URL query parameter, trigger callback on page load
                        value=text,
                    ),
                    html.Div(
                        [
                            dbc.Label("Sync: ", html_for="sync-checkbox", className="me-2 mt-1"),
                            dbc.Checkbox(id="sync-checkbox", value=sync),
                        ],
                        className="d-flex justify-content-end align-items-center",
                    ),
                    dbc.Tooltip(
                        "Whether to sync a register with its repository before searching",
                        target="sync-checkbox",
                    ),
                    dcc.Clipboard(
                        id="clipboard",
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
                    {"field": "ID", "width": 150},
                    {"field": "Team", "width": 110},
                    {"field": "Location", "width": 110},
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
            ),
            html.Pre(id="log-display", className="webapp-log-display"),
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
    Output("clipboard", "content"),
    Input("clipboard", "n_clicks"),
    State("team-dropdown", "value"),
    State("search-input", "value"),
    State("sync-checkbox", "value"),
    State("url", "href"),
)
def custom_copy(_: int, teams: list[str], text: str | None, sync: bool, url: str) -> str:  # type: ignore[misc]  # noqa: FBT001
    """Copy the URL and query parameters to the clipboard."""
    root = url.split("?", maxsplit=1)[0]
    params: list[str] = []
    if teams:
        params.append("team=" + "+".join(teams))
    if text:
        params.append(f"text={quote(text)}")
    if sync:
        params.append("sync=1")
    return root + "?" + "&".join(params)


@app.callback(
    Output("search-input", "debounce"),
    Input("team-dropdown", "value"),
    Input("search-input", "value"),
    Input("sync-checkbox", "value"),
    running=[
        [Output("team-dropdown", "disabled"), True, False],
        [Output("search-input", "disabled"), True, False],
        [Output("sync-checkbox", "disabled"), True, False],
    ],
)
async def update_table(teams: list[str], text: str | None, sync: bool) -> Literal[True]:  # type: ignore[misc]  # noqa: FBT001
    """Update the table data.

    Always force `debounce=True` when returning. When initially loading the page,
    defining `debounce=False` is necessary to trigger a callback if `text=...` is
    specified as a URL query parameter. Afterwards we only want the callback to be
    triggered when ENTER is pressed or the Input component looses focus.
    """
    log_buffer: deque[str] = deque()
    data: list[dict[str, str]] = []

    async def update(msg: str = "") -> None:
        """Uses Dash(websocket_callbacks=True) to update properties in real time."""
        if msg:
            log_buffer.append(msg)
        set_props("log-display", {"children": "\n".join(log_buffer)})
        set_props("table", {"rowData": data})
        await asyncio.sleep(0.01)

    if (not teams) or (not text):
        await update()
        return True

    registers = [t for t in cfg.registers if t.team in teams]
    for register in registers:
        if sync and (register.dir / ".git").exists():
            await update(f"Syncing {register.team!r} repository")
            error_msg = register.git_pull()
            if error_msg:
                await update(error_msg)

        files = ev.recursive(register.dir)
        await update(f"Validating {register.team!r} register")
        num_issues = ev.cli([str(f) for f in files] + ["--skip-checksum", "--exit-first", "-qqq"])
        if num_issues > 0:
            await update(f"ERROR! There are {num_issues} issues, skipping {register.team!r} register")
            continue

        reg = Register(*files)
        for equipment in reg.find(text):
            data.append(
                {
                    "ID": equipment.id,
                    "Team": reg.team,
                    "Location": equipment.location,
                    "Description": equipment.description,
                    "Manufacturer": equipment.manufacturer,
                    "Model": equipment.model,
                    "Serial": equipment.serial,
                }
            )
            await update()

    return True
