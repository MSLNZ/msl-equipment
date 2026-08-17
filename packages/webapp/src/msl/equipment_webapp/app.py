"""Main web application."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnusedFunction=false, reportMissingTypeStubs=false
from __future__ import annotations

import contextlib
import logging
from contextvars import ContextVar
from pathlib import Path
from typing import TYPE_CHECKING

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import Dash, Input, Output, State, html
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from uvicorn.config import LOGGING_CONFIG

from ._version import __version__

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response
    from starlette.types import Scope

    from .config import Config

with contextlib.suppress(KeyError):
    # include %(asctime)s to each uvicorn log message
    datefmt = "%d-%m-%Y %H:%M:%S"
    formatters = LOGGING_CONFIG["formatters"]
    formatters["default"]["fmt"] = "%(levelprefix)s [%(asctime)s] %(message)s"
    formatters["default"]["datefmt"] = datefmt
    formatters["access"]["fmt"] = '%(levelprefix)s [%(asctime)s] %(client_addr)s - "%(request_line)s" %(status_code)s'
    formatters["access"]["datefmt"] = datefmt


scope_ctx: ContextVar[Scope | None] = ContextVar("scope", default=None)


class SuppressDashFilter(logging.Filter):
    """Filter (uninformative) Dash routes from being logged.

    These routes correspond to log messages like

        GET /_dash-layout HTTP/1.1
        GET /_dash-dependencies HTTP/1.1
        GET /_dash-component-suites/dash/dcc/async-markdown.js HTTP/1.1
        GET /_dash-component-suites/dash/dcc/async-highlight.js HTTP/1.1
        GET /_dash-component-suites/dash/dcc/async-mathjax.js HTTP/1.1

    when interacting with the application via a web browser.
    """

    def filter(self, record: logging.LogRecord) -> bool:  # pyright: ignore[reportImplicitOverride]
        """Returns `True` if the record should be logged."""
        return "/_dash" not in record.getMessage()


def create_app(cfg: Config) -> Dash:
    """Create the web application."""
    server = FastAPI(
        docs_url=None,
        title="MSL Equipment API",
        version=__version__,
    )

    app = Dash(
        __name__,
        use_pages=True,
        assets_folder=cfg.static,
        assets_url_path=cfg.static,
        server=server,  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
        title=f"{cfg.nmi} | Home",
        update_title=f"{cfg.nmi} | Updating...",
        external_stylesheets=[getattr(dbc.themes, cfg.theme.upper()), dbc.icons.BOOTSTRAP],
    )

    logging.getLogger("uvicorn.access").addFilter(SuppressDashFilter())
    logging.getLogger("uvicorn.error").addFilter(SuppressDashFilter())
    logging.getLogger("msl.equipment_validate").setLevel(logging.CRITICAL)

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
                                dbc.NavbarToggler(id="navbar-toggler", style={"borderWidth": "0"}, n_clicks=0),
                                dbc.Collapse(
                                    dbc.Nav(
                                        [
                                            dbc.NavItem(dbc.NavLink("Assets", href="/assets")),
                                            dbc.NavItem(dbc.NavLink("Recalibrations", href="/recalibrations")),
                                            dbc.NavItem(dbc.NavLink("Search", href="/search")),
                                            dbc.NavItem(
                                                dbc.NavLink("PDF-A/3", href="/pdf"),
                                                className="me-auto",  # forces any following links to the right
                                            ),
                                            dbc.NavItem(
                                                dbc.NavLink(
                                                    "API",
                                                    href="/api/docs",
                                                    external_link=True,
                                                    target="_blank",
                                                )
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

    static = Path(__file__).parent / "static" if cfg.static == "static" else cfg.static
    server.mount("/static", StaticFiles(directory=static), name="static")

    @server.get("/api/docs", include_in_schema=False)
    async def custom_swagger() -> Response:
        return get_swagger_ui_html(
            openapi_url=app.server.openapi_url,
            swagger_favicon_url="/static/favicon.ico",
            swagger_ui_parameters={
                "defaultModelsExpandDepth": -1,
            },
            title="MSL | API",
        )

    @server.middleware("http")
    async def update_scope_ctx(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        """Allow each `dash` page to have access to the `request.scope` when `layout()` is called."""
        _ = scope_ctx.set(request.scope)
        return await call_next(request)

    @app.callback(
        Output("navbar-collapse", "is_open"),
        Input("navbar-toggler", "n_clicks"),
        State("navbar-collapse", "is_open"),
    )
    async def toggle_navbar_collapse(n_clicks: int, is_open: bool) -> bool:  # type: ignore[misc]  # noqa: FBT001
        """Callback for toggling the NavBar collapse/expansion on small screens."""
        return False if n_clicks == 0 else not is_open

    return app
