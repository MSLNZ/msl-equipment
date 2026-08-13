"""API routes."""

from __future__ import annotations

import socket
from enum import Enum
from textwrap import dedent
from typing import Dict, List, Optional  # pyright: ignore[reportDeprecated]

from dash import exceptions, get_app
from dash import register_page as _  # pyright: ignore[reportUnknownVariableType]  # noqa: F401
from fastapi import FastAPI, File, HTTPException, Query, Response, UploadFile
from msl.equipment_webapp import utils
from msl.equipment_webapp.config import cfg
from pydantic import BaseModel, WithJsonSchema
from typing_extensions import Annotated

try:
    server: FastAPI = get_app().server  # type: ignore[no-untyped-call]
except exceptions.AppNotFoundError:  # required when running tests
    server = FastAPI()


scheme = "https" if cfg.port == 443 else "http"  # noqa: PLR2004
port = "" if cfg.port == 80 else f":{cfg.port}"  # noqa: PLR2004
host = socket.gethostname() if cfg.host == "0.0.0.0" else cfg.host  # noqa: S104
base_url = f"{scheme}://{host}{port}"

AllowedTeams = Enum("AllowedTeams", {t: t for t in cfg.teams})  # type: ignore[misc]
Teams = Annotated[List[AllowedTeams], Query(description="The team(s) to include.")]  # pyright: ignore[reportDeprecated]

Sync = Annotated[
    bool, Query(description="Whether to sync a register with its main repository branch before performing the request.")
]


class Table(BaseModel):
    """Response for the `/api/recalibrations` and `/api/search` routes."""

    synced: bool
    """Whether the register was synced with its repository."""

    is_valid: Dict[str, bool]  # pyright: ignore[reportDeprecated]  # noqa: UP006
    """Whether the register is valid."""

    header: List[str]  # pyright: ignore[reportDeprecated]  # noqa: UP006
    """The table header."""

    data: List[List[str]]  # pyright: ignore[reportDeprecated]  # noqa: UP006
    """The table data."""


@server.get(
    "/api/recalibrations",
    tags=["Equipment Registers"],
    summary="Find equipment that needs to be recalibrated",
    description=dedent(f"""
    Find equipment that needs to be recalibrated.

    Example Python script (requires the [requests](https://pypi.org/project/requests/) package):

    ```python
    import requests

    response = requests.get("{base_url}/api/recalibrations", params={{"team": ["Light", "Length"]}}, timeout=10)
    response.raise_for_status()
    print(response.json())
    ```
    """),
)
async def recalibrations(
    *,
    team: Teams,
    months: Annotated[int, Query(description="Number of months in the future to check if a recalibration is due.")] = 6,
    sync: Sync = False,
) -> Table:
    """Find equipment that needs to be recalibrated."""
    data, is_valid, synced = await utils.recalibrations(teams=[t.value for t in team], months=months, sync=sync)
    return Table(
        synced=synced,
        is_valid=is_valid,
        header=[str(item["field"]) for item in utils.RECALIBRATIONS_COLUMNS],
        data=[list(row.values()) for row in data],
    )


@server.get(
    "/api/search",
    tags=["Equipment Registers"],
    summary="Search for equipment",
    description=dedent(f"""
    Search for equipment.

    Example Python script (requires the [requests](https://pypi.org/project/requests/) package):

    ```python
    import requests

    response = requests.get("{base_url}/api/search", params={{"team": "Light", "text": "Laser"}}, timeout=10)
    response.raise_for_status()
    print(response.json())
    ```
    """),
)
async def search(
    *,
    team: Teams,
    text: Annotated[
        str, Query(description="The text to search for (supports a [regular-expression pattern](https://regexr.com/))")
    ],
    sync: Sync = False,
) -> Table:
    """Search for equipment."""
    data, is_valid, synced, error = await utils.search(teams=[t.value for t in team], text=text, sync=sync)
    if error:
        raise HTTPException(status_code=400, detail=error)

    return Table(
        synced=synced,
        is_valid=is_valid,
        header=[str(item["field"]) for item in utils.SEARCH_COLUMNS],
        data=[list(row.values()) for row in data],
    )


ext = [f"`{e}`" for e in utils.CONVERT_EXTENSIONS]


@server.post(
    "/api/pdf",
    tags=["Report Generation"],
    summary="Create a PDF/A-3 document (with embedded attachments)",
    description=dedent(f"""
    Create a PDF/A-3 document (with embedded attachments).

    Example Python script (requires the [requests](https://pypi.org/project/requests/) package):

    ```python
    import requests

    files = [
        ("source", ("CalibrationReport.tex", open("path/to/CalibrationReport.tex", "rb"))),
        ("attach", ("summary.xlsx", open("path/to/summary.xlsx", "rb"))),
        ("attach", ("irradiance.csv", open("path/to/irradiance.csv", "rb"))),
    ]

    response = requests.post("{base_url}/api/pdf", files=files, timeout=30)
    if response.ok:
        print("MD5 checksum:", response.headers["md5-checksum"])
        print("PDF saved to:", response.headers["filename"])
        with open(response.headers["filename"], "wb") as file:
            file.write(response.content)
    else:
        error = response.json()
        print("ERROR!", error["detail"])
    ```
    """),
)
async def pdf(
    *,
    source: Annotated[UploadFile, File(description=f"A {' or '.join(ext)} file to convert.")],
    attach: Annotated[
        Optional[List[UploadFile]],  # pyright: ignore[reportDeprecated]  # noqa: UP006, UP045
        File(description="Attachments to embed in the PDF (and missing LaTeX files)."),
        WithJsonSchema(
            {  # https://github.com/fastapi/fastapi/discussions/14975
                "type": "array",
                "items": {"type": "string", "format": "binary"},
                "nullable": True,
            }
        ),
    ] = None,
) -> Response:
    """Create a PDF/A-3 document (with embedded attachments)."""
    if not source.filename:
        detail = "Must include the `source` filename in the Content-Disposition header"
        raise HTTPException(status_code=400, detail=detail)

    if not source.filename.endswith(utils.CONVERT_EXTENSIONS):
        detail = f"Unsupported file extension. Must be one of {' or '.join(utils.CONVERT_EXTENSIONS)}"
        raise HTTPException(status_code=415, detail=detail)

    content = await source.read()

    additional: dict[str, bytes] = {}
    for file in attach or []:
        if not file.filename:
            detail = "Must include the `attach` filename in the Content-Disposition header"
            raise HTTPException(status_code=400, detail=detail)
        additional[file.filename] = await file.read()

    pdf, error = await utils.convert_to_pdf(source.filename, content, additional)
    if error:
        raise HTTPException(status_code=400, detail=error)

    return Response(
        content=pdf["content"],
        media_type=pdf["mime_type"],
        headers={
            "Content-Disposition": f'attachment; filename="{pdf["path"].name}"',
            "MD5-Checksum": pdf["checksum"],
            "Filename": pdf["path"].name,
        },
    )
