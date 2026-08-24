"""Search page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportMissingTypeStubs=false
from __future__ import annotations

import contextlib
import re
from collections import deque
from typing import TYPE_CHECKING
from urllib.parse import unquote

import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import Input, Output, State, callback, dcc, exceptions, html, register_page, set_props
from msl.equipment_webapp import components, utils
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from dash.development.base_component import Component
    from msl.equipment_webapp.typing import AgGridData, Scope


PAGE = "search"

with contextlib.suppress(exceptions.PageError):  # required when running tests
    register_page(__name__, name="Search", title=f"{cfg.nmi} | Search")  # type: ignore[no-untyped-call]


def layout(**kwargs: str) -> html.Div:
    """Dynamically serve the layout when the page is loaded.

    Args:
        kwargs: URL query parameters, e.g., /search?team=Light&text=laser&sync=1
    """
    scope = utils.get_scope()
    params = utils.DashQueryParams(**kwargs)
    return html.Div(
        [
            dbc.Row(
                [
                    components.view_button(page=PAGE),
                    components.team_dropdown(page=PAGE, value=params.teams),
                    dbc.Col(
                        [
                            dbc.Input(
                                id=f"{PAGE}-input",
                                placeholder="Search pattern",
                                type="text",
                                debounce=True,
                                value=unquote(params.search),
                                className="flex-grow-1",
                                persistence=True,
                                persistence_type="session",  # value kept on page reload, cleared when browser closed
                                style={
                                    "minWidth": "150px",
                                    "fieldSizing": "content",
                                },
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader(dbc.ModalTitle("Invalid Syntax")),
                                    dbc.ModalBody(id=f"{PAGE}-modal-body"),
                                ],
                                id=f"{PAGE}-modal",
                                is_open=False,
                            ),
                        ],
                        width="auto",
                        className="d-flex mb-2 mb-md-0",
                    ),
                    components.sync_checkbox(page=PAGE, value=params.sync, tip="checking"),
                    components.download_button(page=PAGE),
                ],
                className="g-2 align-items-center my-4 mx-0",
            ),
            components.table(page=PAGE, columns=utils.SEARCH_COLUMNS),
            html.Pre(id=f"{PAGE}-log-display", className="webapp-log-display"),
            dcc.Store(id=f"{PAGE}-scope", storage_type="memory", data=scope),  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
            dcc.Location(id=f"{PAGE}-url", refresh=False),
        ],
        style={"maxWidth": "100vw", "overflowX": "hidden", "padding": "0 5px"},
    )


@callback(
    Output(f"{PAGE}-table", "exportDataAsCsv"),
    Input(f"{PAGE}-download-button", "n_clicks"),
    prevent_initial_call=True,
)
async def export_data_as_csv(n_clicks: int) -> bool:  # type: ignore[misc]
    """Export the data in the table as a CSV file."""
    return n_clicks > 0


@callback(
    Output(f"{PAGE}-url", "href"),
    Output(f"{PAGE}-modal", "is_open"),
    Output(f"{PAGE}-modal-body", "children"),
    Input(f"{PAGE}-team-dropdown", "value"),
    Input(f"{PAGE}-input", "value"),
    Input(f"{PAGE}-sync-checkbox", "value"),
    State(f"{PAGE}-scope", "data"),
    State(f"{PAGE}-url", "href"),
    running=[
        (Output(f"{PAGE}-team-dropdown", "disabled"), True, False),
        (Output(f"{PAGE}-input", "disabled"), True, False),
        (Output(f"{PAGE}-sync-checkbox", "disabled"), True, False),
    ],
    persistent=True,
    websocket=True,
)
async def update_table(  # type: ignore[misc]
    teams: list[str],
    text: str | None,
    sync: bool,  # noqa: FBT001
    scope: Scope,
    href: str,
) -> tuple[str, bool, str | None]:
    """Update the table data."""
    log_buffer: deque[str] = deque()

    async def update(data: AgGridData, msg: str = "") -> None:
        """Requires `websocket=True` for set_props to work."""
        if msg:
            log_buffer.append(msg)
        set_props(f"{PAGE}-log-display", {"children": "\n".join(log_buffer)})
        set_props(f"{PAGE}-table", {"rowData": data})
        await utils.process_events()

    pattern: str | re.Pattern[str] = "."
    if text:
        try:
            pattern = re.compile(text)
        except re.error as e:
            return href, True, f"{e.__class__.__name__}: {e}"

    if (not teams) or (not text):
        await update([])
        return href, False, None

    _ = await utils.search(teams=teams, text=pattern, sync=sync, update=update)
    return utils.log_and_href(scope, href, team=teams, text=text, sync=str(sync).lower()), False, None


@callback(
    Output(f"{PAGE}-view-modal", "is_open"),
    Output(f"{PAGE}-view-modal-body", "children"),
    Input(f"{PAGE}-view-button", "n_clicks"),
    State(f"{PAGE}-table", "selectedRows"),
    State(f"{PAGE}-scope", "data"),
    prevent_initial_call=True,
)
def view_selected_row(_n_clicks: int, selected: AgGridData | None, scope: Scope) -> tuple[bool, Component | None]:
    """View the XML source of the selected row."""
    _ = utils.log_and_href(scope, f"/{PAGE}/view")
    if not selected:
        return False, None

    s = selected[0]
    return True, utils.view(team=s["Team"], equipment_id=s["ID"])
