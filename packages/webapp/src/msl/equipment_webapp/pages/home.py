"""Home page."""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations

import contextlib

import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import dcc, exceptions, html, register_page  # pyright: ignore[reportUnknownVariableType]
from msl.equipment_webapp.config import cfg

with contextlib.suppress(exceptions.PageError):  # required when running tests
    register_page(__name__, path="/", name="Home", title=f"{cfg.nmi} | Home")  # type: ignore[no-untyped-call]

assets_help = """
##### Find equipment that is a capital asset

Select the register(s) of the team(s) that you are interested in displaying assets for.

You can also pre-populate the fields in the URL. This allows you to bookmark a
URL with custom settings, for example,

specify a `team`,
  - <dccLink href="/assets?team=Light" />

specify the `sync` parameter (a *checked* value can be one of `1`, `on`, `yes` or `true`),
  - <dccLink href="/assets?sync=true" />

specify multiple `team`s by repeating the `team=value` pair (each `team=value` pair is separated by the `&` character),
  - <dccLink href="/assets?team=Light&team=Length" />
"""

maintenance_help = """
##### Find equipment that has planned maintenance

Select the register(s) of the team(s) that you are interested in and specify the
number of months in the future to check if a maintenance task is due.

You can also pre-populate the fields in the URL. This allows you to bookmark a
URL with custom settings, for example,

specify a `team`,
  - <dccLink href="/maintenance?team=Light" />

specify a `team` and the `months` parameter (each `name=value` pair is separated by the `&` character),
  - <dccLink href="/maintenance?team=Light&months=1" />

specify the `sync` parameter (a *checked* value can be one of `1`, `on`, `yes` or `true`),
  - <dccLink href="/maintenance?sync=true" />

specify multiple `team`s by repeating the `team=value` pair.
  - <dccLink href="/maintenance?team=Light&team=Length" />
"""

recalibrations_help = """
##### Find equipment that needs to be recalibrated

Select the register(s) of the team(s) that you are interested in and specify the
number of months in the future to check if a recalibration is due. Equipment that
is flagged as needing a recalibration satisfies the following criteria:

* the *traceable* value is `true`, and
* the *status* value is `Active`, and
* a *measurand* has a non-zero `calibrationInterval`, and
* a *component* has no *report* or *performanceCheck* elements (the equipment is uncalibrated), or
* the date in the latest *report* or *performanceCheck* indicates that a recalibration is due
  within the specified months.

You can also pre-populate the fields in the URL. This allows you to bookmark a
URL with custom settings, for example,

specify a `team`,
  - <dccLink href="/recalibrations?team=Light" />

specify a `team` and the `months` parameter (each `name=value` pair is separated by the `&` character),
  - <dccLink href="/recalibrations?team=Light&months=12" />

specify the `sync` parameter (a *checked* value can be one of `1`, `on`, `yes` or `true`),
  - <dccLink href="/recalibrations?sync=true" />

specify multiple `team`s by repeating the `team=value` pair.
  - <dccLink href="/recalibrations?team=Light&team=Length" />
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

specify a `team` and the `text` parameter (each `name=value` pair is separated by the `&` character),
  - <dccLink href="/search?team=Light&text=laser" />

specify `text` to search for equipment that is either a `Hygrometer` or a `Barometer`
&mdash; where the URL escape character `%7C` is used as a replacement for the regular-expression
character `|`, which means *OR*,
  - <dccLink href="/search?team=Length&text=Hygrometer%7CBarometer" />

specify `text` to return all equipment by specifying the `.` (a dot) character &mdash; which is a
regular-expression pattern that matches any character (except for line terminators),
  - <dccLink href="/search?team=Length&text=." />

specify the `sync` parameter (a *checked* value can be one of `1`, `on`, `yes` or `true`),
  - <dccLink href="/search?sync=true" />

specify multiple `team`s by repeating the `team=value` pair.
  - <dccLink href="/search?team=Light&team=Length" />
"""

pdf_help = """
##### Create a PDF/A-3 document

Upload a $\\LaTeX$ or Microsoft Word document to convert it to PDF/A-3 with digital files embedded.
After conversion, the [veraPDF](https://verapdf.org/) tool validates the PDF file, the MD5
checksum of the PDF file is calculated and the PDF file is available to download.

When converting a Microsoft Word document, all extra files that are uploaded are embedded in the
PDF file.

When converting a $\\LaTeX$ document, all uploaded files are saved to the same temporary directory
before running `pdflatex`. As such, when converting a $\\LaTeX$ document, all external file
references must be set appropriately (i.e., references to files in subdirectories or different
parent directories should not be used). The $\\LaTeX$ document must specify which of the extra files
that are uploaded are to be embedded in the PDF file and which files (if any) are required (but missing)
for the build process. Typically, you would only upload extra files that are to be embedded in the PDF,
as the build requirements *should* already be available on the web server.
"""


def layout(**_: str) -> html.Div:
    """Dynamically serve the layout when the page is loaded.

    All query parameters that are specified are silently ignored.
    """
    return html.Div(
        [
            html.H3(
                "Manage information about equipment",
                style={"margin": 25},
            ),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        dcc.Markdown(assets_help, dangerously_allow_html=True),
                        title="Assets",
                    ),
                    dbc.AccordionItem(
                        dcc.Markdown(maintenance_help, dangerously_allow_html=True),
                        title="Maintenance",
                    ),
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
