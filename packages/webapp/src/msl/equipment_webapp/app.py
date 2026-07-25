"""Main web application."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnusedFunction=false, reportMissingTypeStubs=false
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
import uvicorn
from dash import Dash, Input, Output, State, html

from .config import cfg

if TYPE_CHECKING:
    from fastapi import FastAPI


def create_app() -> FastAPI:
    """Create the web application."""
    logger = logging.getLogger("uvicorn")
    logger.info("%s", cfg.logo)
    logger.info("%s", cfg.navbar)
    logger.info("theme=%r, assets=%s", cfg.theme, cfg.assets)

    app = Dash(
        __name__,
        use_pages=True,
        assets_folder=str(cfg.assets),
        backend="fastapi",
        title=f"{cfg.nmi} | Home",
        external_stylesheets=[getattr(dbc.themes, cfg.theme.upper())],
        websocket_callbacks=True,  # required for dash.set_props to work in a callback
    )

    app.logger.setLevel(logging.WARNING)  # Dash internal logger, not logger used in FastAPI

    app.layout = html.Div(
        [
            dbc.Navbar(
                dbc.Container(
                    [
                        dbc.Row(
                            html.Img(src=cfg.logo.src, height=cfg.logo.height),
                            style={"marginLeft": cfg.logo.margin_left, "marginRight": cfg.logo.margin_right},
                        ),
                        dbc.Row(
                            [
                                dbc.NavbarToggler(id="navbar-toggler", style={"borderWidth": "0"}),
                                dbc.Collapse(
                                    dbc.Nav(
                                        [
                                            dbc.NavItem(dbc.NavLink("Recalibrations", href="/recalibrations")),
                                            dbc.NavItem(dbc.NavLink("Search")),
                                            dbc.NavItem(
                                                dbc.NavLink("PDF-A/3"),
                                                className="me-auto",  # forces `Home` link to the right
                                            ),
                                            dbc.NavItem(dbc.NavLink("Home", href="/")),
                                            dbc.NavItem(dbc.NavLink("Help", href="/help")),
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

    server: FastAPI = app.server
    return server


def run(*, host: str, port: int, reload: bool) -> None:
    """Run the web application.

    Args:
        host: The network interface to run the web app on.
        port: The port number to use for the web app.
        reload: Whether to enable auto-reload. When enabled, the values in the configuration file are not used.
    """
    uvicorn.run("msl.equipment_webapp.app:create_app", host=host, port=port, reload=reload, factory=True)
