"""Help page."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false
from __future__ import annotations

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import dcc, html
from msl.equipment_webapp.config import cfg

dash.register_page(__name__, name="Help", title=f"{cfg.nmi} | Help")  # type: ignore[no-untyped-call]

recalibrations_help = """
##### Check for equipment that needs to be recalibrated.

Select the team(s) and specify the number of months in the future to check if a recalibration is due.
You can also pre-populate the fields in the URL, this allows you to bookmark a URL with custom settings,
for example,

specify a `team`,
  - <dccLink href="/recalibrations?team=Light" />

specify a `team` and the `months` parameter (each `name=value` pair is separated by the `&` symbol),
  - <dccLink href="/recalibrations?team=Light&months=12" />

specify the `sync` parameter (a *checked* value can be one of `1`, `yes` or `true`),
  - <dccLink href="/recalibrations?sync=1" />

specify multiple `team`s by separating each value with the `+` sign.
  - <dccLink href="/recalibrations?team=Light+Length" />
"""

search_help = """
##### Search for equipment.

Work in progress...
"""

pdf_help = """
##### Create a PDF/A-3 document.

Work in progress...
"""

layout = html.Div(
    [
        html.H3(
            "Click on a title to show/hide the help for a particular page",
            style={"margin": 25},
        ),
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    dcc.Markdown(recalibrations_help, dangerously_allow_html=True),
                    title="Recalibrations",
                ),
                dbc.AccordionItem(
                    dcc.Markdown(search_help, dangerously_allow_html=True),
                    title="Search",
                ),
                dbc.AccordionItem(
                    dcc.Markdown(pdf_help, dangerously_allow_html=True),
                    title="PDF/A-3",
                ),
            ],
            flush=True,
        ),
    ]
)
