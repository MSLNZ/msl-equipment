"""Main web application."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnusedFunction=false, reportMissingTypeStubs=false
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
import uvicorn
from dash import Dash, Input, Output, State, html
from uvicorn.config import LOGGING_CONFIG

from .config import cfg

if TYPE_CHECKING:
    from fastapi import FastAPI

try:
    datefmt = "%d-%m-%Y %H:%M:%S"
    formatters = LOGGING_CONFIG["formatters"]
    formatters["default"]["fmt"] = "%(levelprefix)s [%(asctime)s] %(message)s"
    formatters["default"]["datefmt"] = datefmt
    formatters["access"]["fmt"] = '%(levelprefix)s [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s'
    formatters["access"]["datefmt"] = datefmt
except KeyError:
    pass


def create_app() -> Dash:
    """Create the web application."""
    app = Dash(
        __name__,
        use_pages=True,
        assets_folder=cfg.assets,
        assets_url_path=cfg.assets,
        backend="fastapi",
        title=f"{cfg.nmi} | Home",
        update_title=f"{cfg.nmi} | Updating...",
        external_stylesheets=[getattr(dbc.themes, cfg.theme.upper()), dbc.icons.BOOTSTRAP],
        websocket_callbacks=True,  # required for dash.set_props to work in callbacks
    )

    app.logger.setLevel(logging.WARNING)  # dash internal logger, not logger used in FastAPI

    app.layout = html.Div(
        [
            dbc.Navbar(
                dbc.Container(
                    [
                        html.A(
                            dbc.Row(
                                html.Img(src=cfg.logo.src, height=cfg.logo.height),
                                style=cfg.logo.style,
                            ),
                            href="/",
                            style={"textDecoration": "none"},
                        ),
                        dbc.Row(
                            [
                                dbc.NavbarToggler(id="navbar-toggler", style={"borderWidth": "0"}),
                                dbc.Collapse(
                                    dbc.Nav(
                                        [
                                            dbc.NavItem(dbc.NavLink("Recalibrations", href="/recalibrations")),
                                            dbc.NavItem(dbc.NavLink("Search", href="/search")),
                                            dbc.NavItem(
                                                dbc.NavLink("PDF-A/3", href="/pdf"),
                                                className="me-auto",  # forces any following links to the right
                                            ),
                                        ],
                                        className="w-100",  # nav uses full screen width for auto margin to get applied
                                    ),
                                    id="navbar-collapse",
                                    is_open=False,
                                    navbar=True,
                                ),
                            ],
                            className="flex-grow-1",  # the row expands to fill the available horizontal space
                        ),
                    ],
                    fluid=True,
                ),
                dark=cfg.navbar.dark,
                color=cfg.navbar.color,
                sticky="top",
            ),
            dash.page_container,
        ]
    )

    @app.callback(
        Output("navbar-collapse", "is_open"),
        Input("navbar-toggler", "n_clicks"),
        State("navbar-collapse", "is_open"),
    )
    async def toggle_navbar_collapse(n: int, is_open: bool) -> bool:  # type: ignore[misc]  # noqa: FBT001
        """Callback for toggling the collapse on small screens."""
        if n:
            return not is_open
        return is_open

    return app


def get_server() -> FastAPI:
    """Create the Dash app and return the FastAPI server."""
    logging.getLogger("uvicorn").info("%s", cfg)
    app = create_app()
    server: FastAPI = app.server
    return server


def run(*, host: str, port: int) -> None:
    """Run the web application.

    Args:
        host: The network interface to run the web app on.
        port: The port number to use for the web app.
    """
    uvicorn.run("msl.equipment_webapp.app:get_server", host=host, port=port, factory=True)
