"""Common utility functions."""

# cSpell: ignore nonstopmode
from __future__ import annotations

import asyncio
import base64
import mimetypes
from datetime import datetime
from typing import TYPE_CHECKING

from lxml import etree
from msl.equipment_validate import DEFAULT_SCHEMA_DIR, find_xml_files, recursive_validate
from msl.equipment_webapp.config import cfg
from msl.loadlib import LoadLibrary
from pikepdf import Array, AttachedFileSpec, Name, Pdf
from pikepdf.models.metadata import encode_pdf_date

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from .config import EquipmentRegister


__all__: list[str] = ["find_xml_files"]

er_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "equipment-register.xsd"))
c_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "connections.xsd"))
word_app: str | LoadLibrary | None = None


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


async def subprocess_run(cmd: Iterable[str], cwd: Path | None = None) -> tuple[int, bytes, bytes]:
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
        *(subprocess_run([cfg.git, "pull"], cwd=r.dir) for r in registers if (r.dir / ".git").exists())
    )
    for code, _, stderr in results:
        if code != 0:
            # only expect a "git not installed" or a "no internet access" error, so if
            # an error does occur it will occur for every task so return the first error
            return f"  \u274c ERROR! Cannot sync: {' '.join(stderr.decode().splitlines())}"
    return ""


async def latex_to_pdf(tex: Path) -> str:
    """Use `pdflatex` to convert a `.tex` file.

    Args:
        tex: The path to a `.tex` file.

    Returns:
        An error message, if an error occurred.
    """
    code, stdout, stderr = await subprocess_run(
        [cfg.pdflatex, "-halt-on-error", "-interaction=nonstopmode", "-max-print-line=1000", f'"{tex.name}"'],
        cwd=tex.parent,
    )

    if code == 0:
        return ""

    if stderr:
        return (
            "ERROR! `pdflatex` cannot be found. "
            "If it is installed, specify the path to the executable in the configuration file.\n"
            "```json\n"
            '  "pdflatex": "path/to/pdflatex"\n'
            "```"
        )

    log_file = tex.with_suffix(".log")
    msg = log_file.read_text() if log_file.exists() else stdout.decode()
    return f"ERROR! Cannot convert.\n\n{msg}"


def word_to_pdf(docx: Path, extra: dict[str, str]) -> str:
    """Use the Microsoft Word API (COM object) to export the `.docx` file.

    Requires Word to be installed in the computer running the web application.
    Could consider using [Adobe's PDF Services API](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/)
    if installing Microsoft Word is not possible. See [docx2pdf](https://github.com/softwareone-platform/docx2pdf)
    for a workflow that uses a CLIENT_ID and CLIENT_SECRET provided by Adobe.

    Args:
        docx: The path to a `.docx` file.
        extra: Extra files that were uploaded to be embedded as attachments.
            A mapping between the uploaded filename and the file content (base64 encoded).

    Returns:
        An error message, if an error occurred.
    """
    global word_app  # noqa: PLW0603
    if word_app is None:
        try:
            word_app = LoadLibrary("Word.Application", "com")
        except ModuleNotFoundError:
            word_app = "Converting a docx file is not supported by the server. The server is not running on Windows."
        except OSError:
            word_app = "Converting a docx file is not supported by the server. Microsoft Word is not installed."
        else:
            word_app.lib.Visible = False

    if isinstance(word_app, str):
        return word_app

    tmp = docx.with_name("tmp.pdf")

    # https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat
    doc = word_app.lib.Documents.Open(docx.resolve().as_posix())
    doc.ExportAsFixedFormat(
        OutputFileName=str(tmp),
        ExportFormat=17,  # wdExportFormatPDF
        OpenAfterExport=False,
        OptimizeFor=0,  # wdExportOptimizeForPrint
        Range=0,  # wdExportAllDocument
        Item=0,  # wdExportDocumentContent
        IncludeDocProps=True,
        KeepIRM=True,
        CreateBookmarks=1,  # wdExportCreateHeadingBookmarks
        DocStructureTags=True,
        BitmapMissingFonts=True,
        UseISO19005_1=True,  # Required for PDF/A
    )
    doc.Close()

    try:
        add_attachments(docx, tmp, extra)
    except Exception as e:  # noqa: BLE001
        return f"ERROR! {e}"
    else:
        return ""


def add_attachments(docx: Path, tmp: Path, extra: dict[str, str]) -> None:
    """Add attachments to a PDF.

    Args:
        docx: The path to the `.docx` file.
        tmp: The path to the PDF file that was exported by Word.
        extra: Extra files that were uploaded to be embedded as attachments.
            A mapping between the uploaded filename and the file content (base64 encoded).
    """
    now = encode_pdf_date(datetime.now().astimezone())
    with Pdf.open(tmp) as pdf:
        af_entries = list(pdf.Root.get("/AF", Array()))
        for filename, b64 in extra.items():
            afs = AttachedFileSpec(
                pdf,
                base64.b64decode(b64),
                description="",  # this is what a pdflatex-generated report does
                filename=filename,
                mime_type=mimetypes.guess_type(filename)[0] or "text/plain",
                creation_date=now,
                mod_date=now,
            )
            afs.relationship = Name.Data
            pdf.attachments[filename] = afs
            af_entries.append(afs.obj)

        if extra:
            pdf.Root.PageMode = Name.UseAttachments
        pdf.Root.AF = pdf.make_indirect(Array(af_entries))
        pdf.save(docx.with_suffix(".pdf"))


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
    code, stdout, stderr = await subprocess_run(
        [cfg.verapdf, "--format", "xml", f'"{path.name}"'],
        cwd=path.parent,
    )

    if code == 0:
        return ""

    if stderr:
        return (
            "ERROR! `veraPDF` cannot be found. "
            "If it is installed, specify the path to the executable in the configuration file.\n"
            "```json\n"
            '  "verapdf": "path/to/verapdf"\n'
            "```"
        )

    return f"ERROR! Invalid PDF file.\n```xml\n{stdout.decode()}\n```"


async def process_events(sleep: float = 0.01) -> None:
    """Sleep, in seconds, the asyncio event loop.

    The duration should be as short as possible that the operating system supports
    such that the properties of the web components are actually updated. On Windows,
    this seems to be 10 ms.
    """
    await asyncio.sleep(sleep)
