"""Maintenance page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import contextlib
from collections import deque
from typing import TYPE_CHECKING

import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, callback, dcc, exceptions, html, register_page, set_props
from msl.equipment_webapp import components, utils
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from dash.development.base_component import Component
    from msl.equipment_webapp.typing import AgGridData, Scope


MONTHS_MAX = 120
PAGE = "maintenance"

with contextlib.suppress(exceptions.PageError):  # required when running tests
    register_page(__name__, name="Maintenance", title=f"{cfg.nmi} | Maintenance")  # type: ignore[no-untyped-call]


def layout(**kwargs: str) -> html.Div:
    """Dynamically serve the layout when the page is loaded.

    Args:
        kwargs: URL query parameters, e.g., /maintenance?team=Light&months=2&sync=1
    """
    scope = utils.get_scope()
    params = utils.DashQueryParams(default_months="2", **kwargs)
    return html.Div(
        [
            dbc.Row(
                [
                    components.view_button(page=PAGE),
                    components.team_dropdown(page=PAGE, value=params.teams),
                    components.months_input(page=PAGE, value=params.months, tip="maintenance", maximum=MONTHS_MAX),
                    components.sync_checkbox(page=PAGE, value=params.sync, tip="checking"),
                    components.download_button(page=PAGE),
                ],
                className="g-2 align-items-center my-4 mx-0",
            ),
            components.table(page=PAGE, columns=utils.MAINTENANCE_COLUMNS),
            html.Pre(id=f"{PAGE}-log-display", className="webapp-log-display"),
            dcc.Store(id=f"{PAGE}-scope", storage_type="memory", data=scope),  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
            dcc.Location(id=f"{PAGE}-url", refresh=False),
        ],
        style={"maxWidth": "100vw", "overflowX": "hidden", "padding": "0 5px"},
    )


@callback(
    Output(f"{PAGE}-months-input", "invalid"),
    Input(f"{PAGE}-months-input", "value"),
    prevent_initial_call=True,
)
async def check_months_range(value: int | None) -> bool:  # type: ignore[misc]
    """Check if the months value is out of range."""
    return value is None


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
    Input(f"{PAGE}-team-dropdown", "value"),
    Input(f"{PAGE}-months-input", "value"),
    Input(f"{PAGE}-sync-checkbox", "value"),
    State(f"{PAGE}-scope", "data"),
    State(f"{PAGE}-url", "href"),
    running=[
        (Output(f"{PAGE}-team-dropdown", "disabled"), True, False),
        (Output(f"{PAGE}-months-input", "disabled"), True, False),
        (Output(f"{PAGE}-sync-checkbox", "disabled"), True, False),
    ],
    persistent=True,
    websocket=True,
)
async def update_table(teams: list[str], months: int | None, sync: bool, scope: Scope, href: str) -> str:  # type: ignore[misc]  # noqa: FBT001
    """Update the table data."""
    log_buffer: deque[str] = deque()

    async def update(data: AgGridData, msg: str = "") -> None:
        """Requires `websocket=True` for set_props to work."""
        if msg:
            log_buffer.append(msg)
        set_props(f"{PAGE}-log-display", {"children": "\n".join(log_buffer)})
        set_props(f"{PAGE}-table", {"rowData": data})
        await utils.process_events()

    if (not teams) or (months is None):  # months is None if the value is not in the [0, MONTHS_MAX] range
        await update([])
        return href

    _ = await utils.maintenance(teams=teams, months=months, sync=sync, update=update)
    return utils.log_and_href(scope, href, team=teams, months=months, sync=str(sync).lower())


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
