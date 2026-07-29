"""Common utility functions."""

from __future__ import annotations

import asyncio
import base64
from typing import TYPE_CHECKING

from lxml import etree
from msl.equipment_validate import DEFAULT_SCHEMA_DIR, find_xml_files, recursive_validate
from msl.equipment_webapp.config import cfg

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from .config import EquipmentRegister


__all__: list[str] = ["find_xml_files"]

er_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "equipment-register.xsd"))
c_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "connections.xsd"))


async def subprocess_run(cmd: Sequence[str], cwd: Path | None = None) -> tuple[int, bytes, bytes]:
    """Asynchronously run a subprocess command.

    Args:
        cmd: The command to run.
        cwd: Change the working directory before running `cmd`.

    Returns:
        The `(returncode, stdout, stderr)` after `cmd` completes.
    """
    proc = await asyncio.create_subprocess_shell(
        " ".join(cmd), cwd=cwd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout, stderr


async def git_pull(registers: list[EquipmentRegister]) -> str:
    """Perform a `git pull` for each register directory that is also a repository.

    Ignores a directory if it does not contain a `.git` subdirectory.

    Args:
        registers: The registers that are of interest.

    Returns:
        An error message, if an error occurred.
    """
    results = await asyncio.gather(
        *(subprocess_run(["git", "pull"], cwd=r.dir) for r in registers if (r.dir / ".git").exists())
    )
    for code, _, stderr in results:
        if code != 0:
            # only expect a "git not installed" or a "no internet access" error, so if
            # an error does occur it will occur for every task so return the first error
            return f"  \u21b3 ERROR! Cannot sync: {stderr.decode()}"
    return ""


def is_register_valid(*files: Path) -> bool:
    """Check if the specified files are valid against the schema."""
    summary = recursive_validate(
        files=files,
        er_schema=er_schema,
        c_schema=c_schema,
        roots=[],
        exit_first=True,
        uri_scheme=None,
        skip_checksum=True,
        no_colour=True,
    )
    ok = summary.num_issues == 0
    summary.reset()
    return ok


async def latex_to_pdf(tex: Path) -> str:
    """Use `pdflatex` to convert a `.tex` file.

    Args:
        tex: The path to a `.tex` file.

    Returns:
        An error message, if an error occurred.
    """
    # resolve() is required on Windows
    path = f'"{tex.resolve()}"'  # noqa: ASYNC240
    code, stdout, stderr = await subprocess_run(
        [cfg.pdflatex, "-halt-on-error", "--max-print-line=1000", path], cwd=tex.parent
    )
    if code == 0:
        return ""

    if stderr:
        return (
            "ERROR! `pdflatex` cannot be found.\n"
            "If it is installed, specify the path to the executable in the configuration file.\n\n"
            '  "pdflatex": "path/to/pdflatex"'
        )

    log_file = tex.with_suffix(".log")
    msg = log_file.read_text() if log_file.exists() else stdout.decode()
    return f"ERROR! Cannot convert.\n\n{msg}"


def word_to_pdf(docx: Path, extra: dict[str, str]) -> str:  # pyright: ignore[reportUnusedParameter]  # noqa: ARG001
    """Use the Microsoft Word API (COM object) to export the `.docx` file.

    Requires Word to be installed in the computer running the web application.
    Could consider using [Adobe's PDF Services API](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/)
    if installing Microsoft Word is not possible. See [docx2pdf](https://github.com/softwareone-platform/docx2pdf)
    for a workflow that uses the CLIENT_ID and CLIENT_SECRET provided by Adobe.

    Args:
        docx: The path to a `.docx` file.
        extra: Extra files that were uploaded for the conversion.
            A mapping between the uploaded filename and the file content (base64 encoded).

    Returns:
        An error message, if an error occurred.
    """
    return "Converting docx files is not implemented yet."


async def to_pdf(document: Path, extra: dict[str, str]) -> tuple[Path, str]:
    """Convert a file to PDF.

    Args:
        document: The path to the document to convert.
        extra: Extra files that were uploaded for the conversion.
            A mapping between the uploaded filename and the file content (base64 encoded).

    Returns:
        The path to the PDF that was created and an error message, if an error occurred.
    """
    pdf = document.with_suffix(".pdf")
    if document.suffix == ".tex":
        for k, v in extra.items():
            _ = (document.parent / k).write_bytes(base64.b64decode(v))
        error = await latex_to_pdf(document)
        if error:
            return pdf, error

        # rerun pdflatex again to make sure all references have been updated
        return pdf, await latex_to_pdf(document)

    return pdf, word_to_pdf(document, extra)


async def vera_check(path: Path) -> str:
    """Use `veraPDF` to check that a PDF file is valid.

    Args:
        path: The path to the pdf file.

    Returns:
        An error message, if an error occurred.
    """
    code, stdout, stderr = await subprocess_run([cfg.verapdf, "--format", "xml", f'"{path}"'])
    if code == 0:
        return ""

    if stderr:
        return (
            "ERROR! `veraPDF` cannot be found.\n"
            "If it is installed, specify the path to the executable in the configuration file.\n\n"
            '  "verapdf": "path/to/verapdf"'
        )

    return f"ERROR! Invalid PDF file.\n```xml\n{stdout.decode()}\n```"


async def process_events(sleep: float = 0.01) -> None:
    """Sleep, in seconds, the asyncio event loop.

    The duration should be as short as possible that the operating system supports
    such that the properties of the web components are actually updated. On Windows,
    this seems to be 10 ms.
    """
    await asyncio.sleep(sleep)
