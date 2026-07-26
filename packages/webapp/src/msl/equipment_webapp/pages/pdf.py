"""PDF/A-3 page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import dash
import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, dcc, html
from msl.equipment_webapp.config import cfg

dash.register_page(__name__, name="PDF/A-3", title=f"{cfg.nmi} | PDF/A-3")  # type: ignore[no-untyped-call]

app: dash.Dash = dash.get_app()  # type: ignore[no-untyped-call]

layout = dbc.Container(
    [
        dcc.Store(id="latex-word-data", storage_type="memory"),
        dcc.Store(id="attachments-data", storage_type="memory"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Upload LaTeX or Word document", className="text-center my-4"),
                        dcc.Upload(
                            id="upload-latex-word",
                            children=html.Div(
                                [
                                    html.I(className="bi bi-cloud-arrow-up fs-1 text-primary"),  # Optional Icon
                                    html.P(
                                        [
                                            "Drag & Drop or ",
                                            html.A("Select a File", href="#", className="alert-link"),
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            ),
                            className="webapp-upload border-primary bg-light p-4 shadow-sm",
                            multiple=False,
                        ),
                        html.Div(id="upload-latex-word-status", className="mt-3"),
                    ],
                    width={"size": 8, "offset": 2},
                )
            ]
        ),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H2("Upload attachment documents", className="text-center my-4"),
                        dcc.Upload(
                            id="upload-attachments",
                            children=html.Div(
                                [
                                    html.I(className="bi bi-cloud-arrow-up fs-1 text-primary"),  # Optional Icon
                                    html.P(
                                        [
                                            "Drag & Drop or ",
                                            html.A("Select Files", href="#", className="alert-link"),
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            ),
                            className="webapp-upload border-primary bg-light p-4 shadow-sm",
                            multiple=True,
                        ),
                        html.Div(id="upload-attachments-status", className="mt-3"),
                    ],
                    width={"size": 8, "offset": 2},
                )
            ]
        ),
        html.Hr(),
        dbc.Container(
            html.Div(
                [
                    dbc.Button("Convert", id="convert-button", className="w-100"),
                    dcc.Download(id="download"),
                    html.Div(id="convert-status", className="mt-3"),
                ],
                className="d-grid col-6 mx-auto mt-4",
            ),
            style={"marginTop": 25, "marginBottom": 25},
        ),
    ],
    fluid=True,
)


@app.callback(
    Output("upload-latex-word-status", "children"),
    Output("latex-word-data", "data"),
    Input("upload-latex-word", "contents"),
    State("upload-latex-word", "filename"),
)
def read_latex_word(content: str | None, filename: str | None) -> tuple[Any, Any]:  # type: ignore[misc]
    """Read the contents of a MS Word or LaTeX file."""
    if not (content and filename):
        return None, None

    if not filename.endswith((".doc", ".docx", ".tex")):
        return dbc.Alert("Unsupported file format", color="danger"), None

    filename = Path(filename).stem + ".pdf"
    _, b64_string = content.split(",", maxsplit=1)
    alert = dbc.Alert(["Successfully uploaded", html.Hr(), filename], color="success")
    return alert, [filename, b64_string]


@app.callback(
    Output("upload-attachments-status", "children"),
    Output("attachments-data", "data"),
    Input("upload-attachments", "contents"),
    State("upload-attachments", "filename"),
)
def read_attachments(contents: list[str] | None, filenames: list[str] | None) -> tuple[Any, dict[str, str]]:  # type: ignore[misc]
    """Read the contents of the attachment files."""
    if not (contents and filenames):
        return None, {}

    data: dict[str, str] = {}
    message: list[str | html.Br | html.Hr] = ["Successfully uploaded", html.Hr()]
    for content, filename in zip(contents, filenames):
        _, b64_string = content.split(",", maxsplit=1)
        data[filename] = b64_string
        message.extend([filename, html.Br()])

    return dbc.Alert(message[:-1], color="success"), data


@app.callback(
    Output("download", "data"),
    Output("convert-status", "children"),
    Input("convert-button", "n_clicks"),
    State("latex-word-data", "data"),
    State("attachments-data", "data"),
    prevent_initial_call=True,
)
def convert(_: int, doc: list[str] | None, attachments: dict[str, str]) -> tuple[Any, Any]:  # type: ignore[misc]  # pyright: ignore[reportUnusedParameter]  # noqa: ARG001
    """Convert the documents."""
    if doc is None:
        alert = dbc.Alert("Must upload a LaTeX or Word document to convert", color="danger", duration=4000)
        return dash.no_update, alert

    filename, b64_string = doc
    data = base64.b64decode(b64_string)
    content = base64.b64encode(data).decode()

    # attachments is a filename -> b64_string mapping

    out = {"content": content, "filename": filename, "type": "application/pdf", "base64": True}
    return out, dbc.Alert("Success!", color="success")
