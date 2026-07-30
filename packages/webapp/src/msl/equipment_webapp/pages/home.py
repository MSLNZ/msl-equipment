"""Home page."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false
from __future__ import annotations

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]
from dash import dcc, html
from msl.equipment_webapp.config import cfg

dash.register_page(__name__, path="/", name="Home", title=f"{cfg.nmi} | Home")  # type: ignore[no-untyped-call]

recalibrations_help = """
##### Check for equipment that needs to be recalibrated

Select the register(s) of the team(s) that you are interested in and specify the
number of months in the future to check if a recalibration is due.

You can also pre-populate the fields in the URL. This allows you to bookmark a
URL with custom settings, for example,

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
##### Search for equipment

Select the register(s) of the team(s) that you are interested in and enter text to search for.
The values in an equipment register that are included in the search are specified
[here](https://mslnz.github.io/msl-equipment/dev/schema/register/#msl.equipment.schema.Register.find).
The search text supports a [regular-expression pattern](https://regexr.com/).

You can also pre-populate the fields in the URL. This allows you to bookmark a
URL with custom settings, for example,

specify a `team`,
  - <dccLink href="/search?team=Light" />

specify a `team` and the `text` parameter (each `name=value` pair is separated by the `&` symbol),
  - <dccLink href="/search?team=Light&text=laser" />

specify `text` to search for equipment that is either a `Hygrometer` or a `Barometer`
(using the URL escape character `%7C` as a replacement for the regular-expression
character `|`, which means *OR*),
  - <dccLink href="/search?team=Length&text=Hygrometer%7CBarometer" />

specify `text` to return all equipment by specifying a `.` (which is a
regular-expression pattern that matches any character &mdash; except for line terminators),
  - <dccLink href="/search?team=Length&text=." />

specify the `sync` parameter (a *checked* value can be one of `1`, `yes` or `true`),
  - <dccLink href="/search?sync=1" />

specify multiple `team`s by separating each value with the `+` sign.
  - <dccLink href="/search?team=Light+Length" />
"""

pdf_help = """
##### Create a PDF/A-3 document

Upload a $\\LaTeX$ or Microsoft Word document to convert it to PDF/A-3 with digital files embedded.
After conversion, the [veraPDF](https://verapdf.org/) tool validates the PDF file, the MD5
checksum of the PDF file is displayed and you are prompted to download the PDF file.

When converting a Microsoft Word document, all extra files that are uploaded are embedded in the
PDF file.

When converting a $\\LaTeX$ document, all uploaded files are saved to the same temporary directory
before running the conversion script. As such, when converting a $\\LaTeX$ document, all external
file references must be set appropriately (i.e., references to files in subdirectories or different
parent directories should not be used). The $\\LaTeX$ document must specify which files are to be
embedded in the PDF file and which files are used only for the build process.
"""

layout = html.Div(
    [
        html.H3(
            "Manage information about equipment",
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
                    dcc.Markdown(pdf_help, dangerously_allow_html=True, mathjax=True),
                    title="PDF/A-3",
                ),
            ],
            flush=True,
        ),
    ]
)
