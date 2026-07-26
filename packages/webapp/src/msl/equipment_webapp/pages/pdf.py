"""PDF/A-3 page."""

# cSpell: ignore msword openxmlformats officedocument wordprocessingml
# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import base64
from typing import TYPE_CHECKING

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, dcc, html
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from typing import Any

dash.register_page(__name__, name="PDF/A-3", title=f"{cfg.nmi} | PDF/A-3")  # type: ignore[no-untyped-call]

app: dash.Dash = dash.get_app()  # type: ignore[no-untyped-call]

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Upload LaTeX or Word document", className="text-center my-4"),
                        dcc.Upload(
                            id="upload-data",
                            children=html.Div(
                                [
                                    html.I(className="bi bi-cloud-arrow-up fs-1 text-primary"),  # Optional Icon
                                    html.P(
                                        [
                                            "Drag and Drop or ",
                                            html.A("Select a File", href="#", className="alert-link"),
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            ),
                            style={
                                "width": "100%",
                                "height": "80px",
                                "lineHeight": "30px",
                                "borderWidth": "2px",
                                "borderStyle": "dashed",
                                "borderRadius": "10px",
                                "textAlign": "center",
                            },
                            className="border-primary bg-light p-4 shadow-sm",
                            multiple=False,
                        ),
                        html.Div(id="upload-status", className="mt-3"),
                    ],
                    width={"size": 8, "offset": 2},
                )
            ]
        )
    ],
    fluid=True,
)


@app.callback(
    Output("upload-status", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def read_file(contents: str | None, filename: str | None) -> Any:  # type: ignore[misc]  # noqa: ANN401
    """Read the contents of a MS Word or LaTeX file."""
    if not (contents and filename):
        return None

    if not filename.endswith((".doc", ".docx", ".tex")):
        return dbc.Alert("Unsupported file format.", color="danger")

    # For a Word document, the content type can be
    #   doc  -> data:application/msword;base64
    #   docx -> data:application/vnd.openxmlformats-officedocument.wordprocessingml.document;base64
    # For a LaTeX document, the content type can be
    #   tex  -> data:application/octet-stream;base64
    content_type, content_string = contents.split(",", maxsplit=1)  # pyright: ignore[reportUnusedVariable]  # noqa: RUF059
    data = base64.b64decode(content_string)  # pyright: ignore[reportUnusedVariable]  # noqa: F841
    return dbc.Alert(f"Successfully uploaded: {filename}", color="success")
