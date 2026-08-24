"""Common `dash` components."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

from typing import TYPE_CHECKING

import dash_ag_grid as dag  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import dcc, html
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from dash.development.base_component import Component

    from .typing import AgGridColumns


def download_button(*, page: str) -> Component:
    """Create a button to download the table data in CSV format.

    Args:
        page: The name of the page.

    Returns:
        A `dbc.Button` wrapped in a `dbc.Col`.
    """
    c: Component = dbc.Col(
        [
            dbc.Button(
                "Download",
                id=f"{page}-download-button",
                n_clicks=0,
                style={"marginRight": 5},
            ),
            dbc.Tooltip(
                "Download the table data in CSV format",
                target=f"{page}-download-button",
            ),
        ],
        width="auto",
    )
    return c


def months_input(*, page: str, value: int, tip: str, maximum: int, minimum: int = 0) -> Component:
    """Create a `dbc.Input` to display a *months* field.

    Args:
        page: The name of the page.
        value: The initial value.
        tip: A text to include in the tooltip about what action the *months* value refers to.
        maximum: The maximum value allowed.
        minimum: The minimum value allowed.

    Returns:
        A `dbc.Input` to display a *months* field, wrapped in a `dbc.Col`.
    """
    c: Component = dbc.Col(
        [
            dbc.Label("Months:", className="me-2 mb-0"),
            dbc.Input(
                id=f"{page}-months-input",
                value=min(max(value, minimum), maximum),
                type="number",
                min=minimum,
                max=maximum,
                step=1,
                debounce=True,
                persistence=True,
                persistence_type="session",  # value kept on page reload, but cleared when browser closed
            ),
            dbc.Tooltip(
                f"Number of months from today's date that a {tip} is due",
                target=f"{page}-months-input",
            ),
        ],
        width="auto",
        className="d-flex align-items-center",
    )
    return c


def sync_checkbox(*, page: str, value: bool, tip: str, class_name: str = "me-auto") -> Component:
    """Create a Checkbox to choose whether to sync the registers.

    Args:
        page: The name of the page.
        value: The initial value.
        tip: A text to include in the tooltip about what action the *sync* checkbox refers to.
        class_name: The `className` to apply to the `dbc.Col`.
            The default value pushes all additional `dbc.Col` items to the far right in the layout.

    Returns:
        A `dbc.Checkbox` wrapped in a `dbc.Col`
    """
    c: Component = dbc.Col(
        html.Div(
            [
                dbc.Label(
                    "Sync:",
                    html_for=f"{page}-sync-checkbox",
                    className="me-2 mb-0",
                ),
                dbc.Checkbox(
                    id=f"{page}-sync-checkbox",
                    value=value,
                ),
                dbc.Tooltip(
                    f"Whether to sync a register with its main repository branch before {tip}",
                    target=f"{page}-sync-checkbox",
                ),
            ],
            className="d-flex align-items-center",
        ),
        width="auto",
        className=class_name,
    )
    return c


def table(*, page: str, columns: AgGridColumns, filename: str | None = None) -> html.Div:
    """Create an `AgGrid` table.

    Args:
        page: The name of the page.
        columns: The column definitions of the `AgGrid` table.
        filename: The name of the CSV file that can be download (without the `.csv` extension).
            Default is the `page` value.

    Returns:
        An `AgGrid` table wrapped in a `html.Div` component.
    """
    return html.Div(
        dag.AgGrid(
            id=f"{page}-table",
            columnDefs=columns,
            defaultColDef={"filter": True, "resizable": True},
            dashGridOptions={
                "pagination": True,
                "theme": "themeAlpine",
                "loading": False,
                "enableCellTextSelection": True,
                "ensureDomOrder": True,  # required for enableCellTextSelection=True
                "rowSelection": {"mode": "singleRow"},
            },
            csvExportParams={
                "fileName": f"{filename or page}.csv",
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
    )


def team_dropdown(*, page: str, value: list[str]) -> Component:
    """Create a dropdown component to select multiple teams.

    Args:
        page: The name of the page.
        value: The initial teams to select.
        tip: The

    Returns:
        A `dcc.Dropdown` component wrapped in a `dbc.Col`.
    """
    c: Component = dbc.Col(
        [
            dbc.Label("Team(s):", className="me-2 mb-0", style={"marginLeft": 25}),
            dcc.Dropdown(
                cfg.teams,
                multi=True,
                value=value,
                id=f"{page}-team-dropdown",
                className="flex-grow-1",
                style={
                    "minWidth": "300px",
                    "width": "auto",
                    "display": "inline-block",
                },
                debounce=True,
                persistence=True,
                persistence_type="session",  # value kept on page reload, but cleared when browser closed
            ),
        ],
        width="auto",
        className="d-flex align-items-center mb-2 mb-md-0",
    )
    return c


def view_button(*, page: str) -> Component:
    """Create a button that when clicked displays the XML source of the selected row in a table.

    Args:
        page: The name of the page.

    Returns:
        A `dbc.Button` with a `dbc.Modal` to display the XML source, wrapped in a `dbc.Col` component.
    """
    c: Component = dbc.Col(
        [
            dbc.Button("View", id=f"{page}-view-button", n_clicks=0),
            dbc.Modal(
                [
                    dbc.ModalHeader(),
                    dbc.ModalBody(id=f"{page}-view-modal-body"),
                ],
                id=f"{page}-view-modal",
                is_open=False,
                size="xl",
            ),
            dbc.Tooltip(
                "View the XML source of the selected row",
                target=f"{page}-view-button",
                trigger="hover",
            ),
        ],
        width="auto",
    )
    return c
