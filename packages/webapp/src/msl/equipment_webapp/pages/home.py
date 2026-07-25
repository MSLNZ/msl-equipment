"""Home page."""

from __future__ import annotations

import dash
from dash import dcc
from msl.equipment_webapp.config import cfg

dash.register_page(__name__, path="/", name="Home", title=f"{cfg.nmi} | Home")  # type: ignore[no-untyped-call]  # pyright: ignore[reportUnknownMemberType]

body = """
### Manage information about equipment

View the [help](/help) to get started.
"""

layout = dcc.Markdown(body, dangerously_allow_html=True, style={"margin": 50})
