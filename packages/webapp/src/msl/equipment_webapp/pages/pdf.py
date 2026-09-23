"""PDF/A-3 page."""

# cSpell: ignore clientside webkitdirectory
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false
from __future__ import annotations

import base64
import contextlib
from typing import TYPE_CHECKING

import dash_bootstrap_components as dbc  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
from dash import Input, Output, State, callback, dcc, exceptions, get_app, html, no_update, register_page, set_props
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from typing import Any

    from dash.development.base_component import Component
    from msl.equipment_webapp.typing import Scope


with contextlib.suppress(exceptions.PageError):  # required when running tests
    register_page(__name__, name="PDF/A-3", title=f"{cfg.nmi} | PDF/A-3")  # type: ignore[no-untyped-call]


def layout(**_: str) -> Component:
    """Dynamically serve the layout when the page is opened.

    All query parameters that are specified are silently ignored.
    """
    c: Component = dbc.Container(
        [
            dcc.Store(id="pdf-document", storage_type="memory"),
            dcc.Store(id="pdf-extra", storage_type="memory"),
            dcc.Store(id="pdf-scope", storage_type="memory", data=utils.get_scope()),  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]
            dcc.Store(id="pdf-paths-prompt", storage_type="memory"),
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
                                                "Drag & Drop a file or ",
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
                            dcc.Markdown(
                                "## Upload attachments (and missing $\\LaTeX$ files)",
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
                                                "Drag & Drop a file/folder or ",
                                                html.A("Select a Folder", href="#", className="alert-link"),
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
                        "Remove all attachments",
                        target="pdf-clear-button",
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

    # Injects HTML5 directory attributes and intercepts file selections
    get_app().clientside_callback(  # type: ignore[no-untyped-call]
        """
        function(id) {
            // Wait briefly for Dash to render the component into the DOM
            setTimeout(() => {
                const el = document.getElementById(id);
                if (el) {
                    const input = el.querySelector('input[type="file"]');
                    if (input) {
                        // Force the browser to accept folder picks
                        input.setAttribute('webkitdirectory', '');
                        input.setAttribute('directory', '');

                        // Listen to the native selection change
                        input.addEventListener('change', function(e) {
                            const files = e.target.files;
                            const paths = [];

                            for (let i = 0; i < files.length; i++) {
                                // webkitRelativePath contains "FolderName/Subfolder/file.ext"
                                paths.push(files[i].webkitRelativePath);
                            }

                            // Dynamically update our hidden dcc.Store component
                            dash_clientside.set_props('pdf-paths-prompt', {data: paths});
                        });
                    }
                }
            }, 500);
            return window.dash_clientside.no_update;
        }
        """,
        Output("pdf-upload-extra", "id"),
        Input("pdf-upload-extra", "id"),
    )

    return c


@callback(
    Output("pdf-document", "data"),
    Output("pdf-upload-document-status", "children"),
    Input("pdf-upload-document", "contents"),
    State("pdf-upload-document", "filename"),
    prevent_initial_call=True,
)
def upload_document(content: str, filename: str) -> tuple[list[str], Component]:
    """Get the content of a MS Word or LaTeX file.

    Args:
        content: The mime type and file data (base64 encoded) separated by a `,`.
        filename: The name of the uploaded file.

    Returns:
        The `[original filename, file content as base64]` and `dbc.Alert`.
    """
    if not filename.endswith(utils.CONVERT_EXTENSIONS):
        alert = dbc.Alert(
            f"Unsupported file extension. Must be one of {' or '.join(utils.CONVERT_EXTENSIONS)}.",
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
    Output("pdf-paths-prompt", "data"),
    Input("pdf-upload-extra", "contents"),
    State("pdf-upload-extra", "filename"),
    State("pdf-extra", "data"),
    State("pdf-paths-prompt", "data"),
    prevent_initial_call=True,
)
def upload_extra(
    contents: list[str], paths: list[str], extra: dict[str, str] | None, prompt_paths: list[str] | None
) -> tuple[dict[str, str], Component, None]:
    """Read the contents of the attachment files.

    Args:
        contents: The file content (base64 encoded) for each file.
        paths: The path of each file.
        extra: The extra files that have already been uploaded.
            A mapping between the uploaded filename and the file content (base64 encoded).
        prompt_paths: When a Drag 'n Drop is performed this value is `None`, however, when a
            directory is chosen using the web browser's "open dialog" prompt this value contains
            the file paths with the parent-directory information included and the `paths` value
            only contains the file names (without the parent-directory information).

    Returns:
        The `extra` updated to include the newly uploaded files, a `dbc.Alert` and `None`.
    """
    if extra is None:
        extra = {}

    filepaths = prompt_paths or paths
    for content, file in zip(contents, filepaths):
        _, b64_string = content.split(",", maxsplit=1)
        extra[file] = b64_string

    message = [item for file in extra for item in (file, html.Br())]
    alert = dbc.Alert(message[:-1], color="success", className="text-center")
    return extra, alert, None


@callback(
    Output("pdf-extra", "data"),
    Input("pdf-clear-button", "n_clicks"),
)
async def clear_extra(_n_clicks: int) -> dict[str, str]:  # type: ignore[misc]
    """Clear all extra files.

    Args:
        _n_clicks: Ignored. The number of times the `pdf-clear-button` has been clicked.

    Returns:
        An empty `dict`.
    """
    # Dash raised an exception when Output("pdf-upload-extra-status", "children") was defined as a callback argument
    # Using set_props is a workaround
    set_props("pdf-upload-extra-status", {"children": None})
    await utils.process_events()
    return {}


@callback(
    Output("pdf-download", "data"),
    Output("pdf-convert-status", "children"),
    Output("pdf-spinner", "children"),
    Input("pdf-convert-button", "n_clicks"),
    State("pdf-document", "data"),
    State("pdf-extra", "data"),
    State("pdf-scope", "data"),
    running=[
        (Output("pdf-convert-button", "disabled"), True, False),
        (Output("pdf-convert-status", "children"), None, None),
    ],
    prevent_initial_call=True,
    persistent=True,
)
async def convert(  # type: ignore[misc]
    _n_clicks: int, document: list[str] | None, extra: dict[str, str] | None, scope: Scope
) -> tuple[Any, Component, None]:
    """Convert the uploaded files to a PDF.

    Args:
        _n_clicks: Ignored. The number of times the `pdf-convert-button` has been clicked.
        document: The LaTeX or Word document to convert. The first item is the filename of the
            original file and the second item is the file content (base64 encoded).
        extra: The extra files required to convert the `document` to PDF.
            A mapping between the uploaded filename and the file content (base64 encoded).
        scope: Information about the request.

    Returns:
        The information for the web browser to download the PDF file (or `no_update`),
            a `dbc.Alert` component describing the outcome of the conversion and
            `None` to tell the `dcc.Loading` animation to stop.
    """
    if not document:
        alert = dbc.Alert(
            dcc.Markdown("Must upload a $\\LaTeX$ or Microsoft Word document to convert.", mathjax=True),
            color="danger",
            duration=4000,
            className="text-center",
        )
        return no_update, alert, None

    filename, b64_string = document
    _ = utils.log_and_href(scope, href=f"/pdf/{filename}", method="POST")

    if extra is None:
        extra = {}

    pdf, error = await utils.convert_to_pdf(
        filename,
        content=base64.b64decode(b64_string),
        extra={k: base64.b64decode(v) for k, v in extra.items()},
    )

    if error:
        child = dcc.Markdown(error) if error.endswith("```") else html.Pre(error)
        alert = dbc.Alert(child, color="danger")
        return no_update, alert, None

    reply = {
        "content": base64.b64encode(pdf["content"]).decode(),
        "filename": pdf["path"].name,
        "type": pdf["mime_type"],
        "base64": True,
    }

    alert = dbc.Alert(f"MD5: {pdf['checksum']}", color="success", className="text-center")

    return reply, alert, None
