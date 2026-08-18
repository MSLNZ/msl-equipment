"""Custom type annotations."""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from pathlib import Path

    RegisterValidity = dict[str, bool]
    AgGridData = list["AgGridDataItem"]
    AgGridColumns = list[dict[str, str | int | dict[str, str]]]


AgGridDataItem = TypedDict(
    "AgGridDataItem",
    {
        "Asset Number": NotRequired[str],
        "Currency": NotRequired[str],
        "Depreciated?": NotRequired[str],
        "Depreciation End Date": NotRequired[str],
        "Depreciation Start Date": NotRequired[str],
        "Description": NotRequired[str],
        "Due Date": NotRequired[str],
        "ID": str,
        "Location": NotRequired[str],
        "Manufacturer": str,
        "Model": str,
        "Overdue?": NotRequired[str],
        "Performed By": NotRequired[str],
        "Price": NotRequired[float],
        "Serial": NotRequired[str],
        "Task": NotRequired[str],
        "Team": str,
    },
)


class QueryParams(TypedDict):
    """Query parameters that can be passed to a `dash` layout function."""

    team: NotRequired[str | list[str]]
    months: NotRequired[str]
    sync: NotRequired[str]
    text: NotRequired[str]


class Scope(TypedDict):
    """Stores some items in a `scope` of a [starlette.Request](https://starlette.dev/requests/)."""

    client: str
    http_version: str


class PDFFile(TypedDict):
    """Information about a PDF file."""

    path: Path
    content: bytes
    checksum: str
    mime_type: str
