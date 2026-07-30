"""PDF/A-3 page."""

# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false, reportUnknownVariableType=false
from __future__ import annotations

import base64
from hashlib import md5
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, callback, dcc, html, no_update, register_page, set_props
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import cfg

register_page(__name__, name="PDF/A-3", title=f"{cfg.nmi} | PDF/A-3")  # type: ignore[no-untyped-call]

layout = dbc.Container(
    [
        dcc.Store(id="pdf-document", storage_type="memory"),
        dcc.Store(id="pdf-extra", storage_type="memory"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Markdown(
                            "## Upload a $\\LaTeX$ or Microsoft Word document",
                            mathjax=True,
                            className="text-center my-4",
                        ),
                        dcc.Upload(
                            html.Div(
                                [
                                    html.P(
                                        [
                                            html.I(
                                                className="bi bi-cloud-arrow-up fs-1 mx-3 text-primary align-middle"
                                            ),
                                            "Drag & Drop or ",
                                            html.A("Select a File", href="#", className="alert-link"),
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            ),
                            id="pdf-upload-document",
                            className="border-primary bg-light p-2 shadow-sm text-center webapp-upload",
                            multiple=False,
                        ),
                        html.Div(id="pdf-upload-document-status", className="mt-3"),
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
                        html.H2("Upload extra documents", className="text-center my-4"),
                        dcc.Upload(
                            html.Div(
                                [
                                    html.P(
                                        [
                                            html.I(
                                                className="bi bi-cloud-arrow-up fs-1 mx-3 text-primary align-middle"
                                            ),
                                            "Drag & Drop or ",
                                            html.A("Select Files", href="#", className="alert-link"),
                                        ],
                                        className="mb-0",
                                    ),
                                ]
                            ),
                            id="pdf-upload-extra",
                            className="border-primary bg-light p-2 shadow-sm text-center webapp-upload",
                            multiple=True,
                        ),
                        html.Div(id="pdf-upload-extra-status", className="mt-3"),
                    ],
                    width={"size": 8, "offset": 2},
                ),
                dbc.Col(
                    dbc.Button(
                        [html.I(className="bi bi-trash3 me-2"), "Clear"],
                        id="pdf-clear-button",
                        color="secondary",
                        className="mt-4",
                    )
                ),
                dbc.Tooltip(
                    "Remove all extra documents",
                    target="clear-button",
                ),
            ]
        ),
        html.Hr(),
        dbc.Row(
            dbc.Col(
                [
                    html.Div(
                        [
                            dbc.Button(
                                [html.I(className="bi bi-file-earmark-pdf me-2"), "Convert"],
                                id="pdf-convert-button",
                                className="w-100 fs-3",
                            ),
                            dbc.Spinner(
                                html.Div(id="pdf-spinner"),
                                color="secondary",
                                spinner_style={
                                    "width": "5rem",
                                    "height": "5rem",
                                    "position": "relative",
                                    "top": "-27px",
                                },
                            ),
                            dcc.Download(id="pdf-download"),
                            html.Div(id="pdf-convert-status", className="mt-3"),
                        ]
                    ),
                ],
                width={"size": 8, "offset": 2},
            ),
            style={"marginBottom": 100},
        ),
    ],
    fluid=True,
)


@callback(
    Output("pdf-document", "data"),
    Output("pdf-upload-document-status", "children"),
    Input("pdf-upload-document", "contents"),
    State("pdf-upload-document", "filename"),
)
def upload_document(content: str | None, filename: str | None) -> tuple[list[str], Any]:  # type: ignore[misc]
    """Get the content of a MS Word or LaTeX file.

    Args:
        content: The mime type and file data (base64 encoded) separated by a `,`.
        filename: The name of the uploaded file.

    Returns:
        The `[original filename, file content as base64]` and `dbc.Alert | None`.
    """
    if not (content and filename):
        return [], None

    if not filename.endswith((".docx", ".tex")):
        alert = dbc.Alert(
            "Unsupported file extension. Must be docx or tex.",
            color="danger",
            className="text-center",
        )
        return [], alert

    _, b64_string = content.split(",", maxsplit=1)
    alert = dbc.Alert(filename, color="success", className="text-center")
    return [filename, b64_string], alert


@callback(
    Output("pdf-extra", "data"),
    Output("pdf-upload-extra-status", "children"),
    Input("pdf-upload-extra", "contents"),
    State("pdf-upload-extra", "filename"),
    State("pdf-extra", "data"),
)
def upload_extra(  # type: ignore[misc]
    contents: list[str] | None, filenames: list[str] | None, extra: dict[str, str] | None
) -> tuple[dict[str, str], Any]:
    """Read the contents of the attachment files.

    Args:
        contents: The file content (base64 encoded) for each file.
        filenames: The filenames of each file.
        extra: The extra files that have already been uploaded.
            A mapping between the uploaded filename and the file content (base64 encoded).

    Returns:
        The `extra` updated to include the newly uploaded files and `dbc.Alert | None`.
    """
    if extra is None:
        extra = {}

    if not (contents and filenames):
        return extra, None

    for content, filename in zip(contents, filenames):
        _, b64_string = content.split(",", maxsplit=1)
        extra[filename] = b64_string

    message = [item for a in extra for item in (a, html.Br())]
    return extra, dbc.Alert(message[:-1], color="success", className="text-center")


@callback(
    Output("pdf-extra", "data"),
    Input("pdf-clear-button", "n_clicks"),
)
def clear_extra(_: int) -> dict[str, str]:
    """Clear all extra files.

    Args:
        _: Ignored. The number of times the `clear-button` has been clicked.

    Returns:
        An empty `dict`.
    """
    # Dash raised exceptions when Output("upload-document-status", "children") was defined as a callback argument
    # Using set_props is a workaround
    set_props("pdf-upload-extra-status", {"children": None})
    return {}


@callback(
    Output("pdf-download", "data"),
    Output("pdf-convert-status", "children"),
    Output("pdf-spinner", "children"),
    State("pdf-document", "data"),
    State("pdf-extra", "data"),
    Input("pdf-convert-button", "n_clicks"),
    running=[
        (Output("pdf-convert-button", "disabled"), True, False),
    ],
    prevent_initial_call=True,
    persistent=True,
)
async def convert(document: list[str], extra: dict[str, str], _: int) -> tuple[Any, Any, None]:  # type: ignore[misc]
    """Convert the uploaded files to a PDF.

    Args:
        document: The LaTeX or Word document to convert. The first item is the filename of the
            original file and the second item is the file content (base64 encoded).
        extra: The extra files required to convert the `document` to PDF.
            A mapping between the uploaded filename and the file content (base64 encoded).
        _: Ignored. The number of times the `convert-button` has been clicked.

    Returns:
        The information for the web browser to download the PDF file, a `dbc.Alert` component
            describing the outcome of the conversion and `None` to tell the `dcc.Loading`
            animation to stop.
    """
    if not document:
        alert = dbc.Alert(
            dcc.Markdown("Must upload a $\\LaTeX$ or Microsoft Word document to convert.", mathjax=True),
            color="danger",
            duration=4000,
            className="text-center",
        )
        return no_update, alert, None

    set_props("pdf-convert-status", {"children": None})
    await utils.process_events()

    filename, b64_string = document
    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src_filename = tmp_dir / filename
        _ = src_filename.write_bytes(base64.b64decode(b64_string))

        pdf_filename, error = await utils.to_pdf(src_filename, extra)
        if error:
            alert = dbc.Alert(html.Pre(error), color="danger")
            return no_update, alert, None

        error = await utils.vera_check(pdf_filename)
        if error:
            alert = dbc.Alert(dcc.Markdown(error), color="danger")
            return no_update, alert, None

        pdf_data = pdf_filename.read_bytes()
        checksum = md5(pdf_data).hexdigest()  # noqa: S324
        content = base64.b64encode(pdf_data).decode()
        out = {"content": content, "filename": pdf_filename.name, "type": "application/pdf", "base64": True}
        return out, dbc.Alert(f"MD5: {checksum}", color="success", className="text-center"), None
