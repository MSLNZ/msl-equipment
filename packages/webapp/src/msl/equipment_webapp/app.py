"""Main app."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import logging

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
import uvicorn
from dash import Dash, html

app = Dash(
    __name__,
    use_pages=True,
    backend="fastapi",
    title="MSL | Home",
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

page_info: dict[str, str] = {page["name"]: page["relative_path"] for page in dash.page_registry.values()}

app.layout = html.Div(
    [
        dbc.NavbarSimple(
            children=[dbc.NavItem(dbc.NavLink(name, href=href)) for name, href in page_info.items()],
            brand="MSL Equipment Registry",
            color="dark",
            dark=True,
            class_name="mb-2",
            links_left=True,
        ),
        dash.page_container,
    ]
)


def run(host: str, port: int, log_level: int) -> None:
    """Run the web app.

    Args:
        host: The network interface to run the web app on.
        port: The port number to use for the web app.
        log_level: Logging level of the web app.
    """
    app.logger.setLevel(logging.WARNING)  # Dash internal logger
    uvicorn.run(app.server, host=host, port=port, log_level=log_level)
