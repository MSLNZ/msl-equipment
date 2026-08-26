"""Common utility functions."""

# cSpell: ignore nonstopmode localname doseq
from __future__ import annotations

import asyncio
import logging
import mimetypes
import re
from datetime import date, datetime
from hashlib import md5
from itertools import chain
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from urllib.parse import quote, unquote, urlencode, urlsplit

from dash import html
from lxml import etree
from msl.equipment_validate import DEFAULT_SCHEMA_DIR, recursive_validate
from msl.equipment_webapp.app import scope_ctx
from msl.equipment_webapp.config import SHA256Validation, cfg
from msl.loadlib import LoadLibrary
from pikepdf import Array, AttachedFileSpec, Name, Pdf
from pikepdf.models.metadata import encode_pdf_date

from msl.equipment import Register, Status

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable
    from xml.etree.ElementTree import Element

    from dash.development.base_component import Component
    from typing_extensions import Unpack

    from .config import EquipmentRegister
    from .typing import AgGridColumns, AgGridData, PDFFile, QueryParams, RegisterValidity, Scope


er_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "equipment-register.xsd"))
c_schema = etree.XMLSchema(etree.parse(DEFAULT_SCHEMA_DIR / "connections.xsd"))
word_app: str | LoadLibrary | None = None

logger = logging.getLogger("uvicorn.error")


ASSETS_COLUMNS: AgGridColumns = [
    {"field": "ID", "width": 140},
    {"field": "Team", "flex": 1},
    {"field": "Asset Number", "flex": 1, "wrapHeaderText": True, "autoHeaderHeight": True},
    {"field": "Depreciation Start Date", "width": 130, "wrapHeaderText": True, "autoHeaderHeight": True},
    {"field": "Depreciation End Date", "width": 130, "wrapHeaderText": True, "autoHeaderHeight": True},
    {"field": "Depreciated?", "width": 130},
    {"field": "Price", "flex": 1, "valueFormatter": {"function": cfg.price.format_locale}, "type": "numericColumn"},
    {"field": "Currency", "width": 105},
    {"field": "Manufacturer", "flex": 1},
    {"field": "Model", "flex": 1},
]

MAINTENANCE_COLUMNS: AgGridColumns = [
    {"field": "ID", "width": 150},
    {"field": "Team", "flex": 1},
    {"field": "Due Date", "flex": 1},
    {"field": "Overdue?", "flex": 1},
    {"field": "Task", "flex": 3},
    {"field": "Performed By", "flex": 2},
    {"field": "Manufacturer", "flex": 2},
    {"field": "Model", "flex": 1},
    {"field": "Serial", "flex": 1},
]


RECALIBRATIONS_COLUMNS: AgGridColumns = [
    {"field": "ID", "width": 150},
    {"field": "Team", "flex": 1},
    {"field": "Due Date", "flex": 1},
    {"field": "Overdue?", "flex": 1},
    {"field": "Description", "flex": 3},
    {"field": "Manufacturer", "flex": 2},
    {"field": "Model", "flex": 1},
    {"field": "Serial", "flex": 1},
]

SEARCH_COLUMNS: AgGridColumns = [
    {"field": "ID", "width": 150},
    {"field": "Team", "flex": 1},
    {"field": "Location", "flex": 2},
    {"field": "Description", "flex": 3},
    {"field": "Manufacturer", "flex": 2},
    {"field": "Model", "flex": 1},
    {"field": "Serial", "flex": 1},
]

CONVERT_EXTENSIONS: tuple[str, ...] = (".docx", ".tex")


class DashQueryParams:
    """Parse the URL query parameters to initialise dash components in the layout."""

    def __init__(self, default_months: str = "6", **params: Unpack[QueryParams]) -> None:
        """Parse the URL query parameters to initialise dash components in the layout."""
        teams: str | list[str] = params.get("team", [])
        if isinstance(teams, str):
            teams = [teams]

        cfg_teams = cfg.teams
        self.teams: list[str] = [t for t in teams if t in cfg_teams]
        """Specified teams."""

        try:
            months = int(params.get("months", default_months))
        except ValueError:
            months = int(default_months)

        self.months: int = months
        """The number of months in the future to check if an action must be performed."""

        # Support same "truthy" values as pydantic
        # https://pydantic.dev/docs/validation/latest/concepts/conversion_table/
        self.sync: bool = params.get("sync", "0").lower() in {"1", "on", "t", "true", "y", "yes"}
        """Whether to sync repositories."""

        self.search: str = unquote(params.get("text", ""))
        """Search text."""


def get_scope() -> Scope:
    """Returns some items in a `scope` of a [starlette.Request](https://starlette.dev/requests/)."""
    scope = scope_ctx.get() or {}
    return {
        "client": "%s:%d" % scope.get("client", ("Unknown", 0)),  # noqa: UP031
        "http_version": scope.get("http_version", "1.1"),
    }


def log_and_href(scope: Scope, href: str, method: str = "GET", **params: object) -> str:
    """Log an INFO message in a `dash` callback and return the updated `href` based on the `params`."""
    split = urlsplit(href)
    route = split.path if not params else split.path + "?" + urlencode(params, doseq=True, quote_via=quote)
    logger.info('%s - "%s %s HTTP/%s" \x1b[32m200 OK\x1b[0m', scope["client"], method, route, scope["http_version"])
    return f"{split.scheme}://{split.netloc}{route}"


async def subprocess_run(cmd: Iterable[str], cwd: Path | None = None) -> tuple[int, bytes, bytes]:
    """Asynchronously run a subprocess command.

    Args:
        cmd: The command to run.
        cwd: Change the working directory before running `cmd`.

    Returns:
        The `(returncode, stdout, stderr)` after `cmd` completes.
    """
    proc = await asyncio.create_subprocess_shell(
        " ".join(cmd),
        cwd=cwd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    return proc.returncode or 0, stdout, stderr


async def git_pull(
    registers: list[EquipmentRegister], update: Callable[[AgGridData, str], Awaitable[None]] | None = None
) -> bool:
    """Perform a `git pull` for each register directory that is also a repository.

    Ignores a directory if it does not contain a `.git` subdirectory.

    Args:
        registers: The registers that are of interest.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        Whether an error occurred.
    """
    if update is not None:
        teams = [r.team for r in registers]
        await update([], f"Syncing register for {', '.join(teams)}")

    results = await asyncio.gather(
        *(subprocess_run([cfg.git, "pull"], cwd=r.directory) for r in registers if (r.directory / ".git").exists())
    )
    for code, _, stderr in results:
        if code != 0:
            # only expect a "git not installed" or a "no internet access" error, so if
            # an error does occur it will occur for every task so return on the first error
            if update is not None:
                msg = f"  \u274c ERROR! Cannot sync: {' '.join(stderr.decode().splitlines())}"
                await update([], msg)
            return False
    return True


async def convert_to_pdf(filename: str, content: bytes, extra: dict[str, bytes]) -> tuple[PDFFile, str]:
    """Convert a LaTeX or Word document to PDF.

    Args:
        filename: The file name of the source document to convert.
        content: The content of the source document.
        extra: The extra files required to convert the source document to a PDF.
            A mapping between file names and file content.

    Returns:
        Information about the converted PDF and an error message (if an error occurred).
    """
    with TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src_filename = tmp_dir / filename
        _ = src_filename.write_bytes(content)

        pdf_filename, error = await to_pdf(src_filename, extra)
        pdf: PDFFile = {"path": pdf_filename, "mime_type": "application/pdf", "content": b"", "checksum": ""}
        if error:
            return pdf, error

        error = await vera_check(pdf_filename)
        if error:
            return pdf, error

        pdf["content"] = pdf_filename.read_bytes()
        pdf["checksum"] = md5(pdf["content"]).hexdigest()  # noqa: S324
        return pdf, ""


async def latex_to_pdf(tex: Path) -> str:
    """Use `pdflatex` to convert a `.tex` file.

    Args:
        tex: The path to a `.tex` file.

    Returns:
        An error message, if an error occurred.
    """
    code, stdout, stderr = await subprocess_run(
        [
            cfg.pdflatex,
            "-halt-on-error",
            "-interaction=nonstopmode",
            "-max-print-line=1000",
            f'"{tex.name}"',
        ],
        cwd=tex.parent,
    )

    if code == 0:
        return ""

    if stderr and not stderr.startswith(b"pdflatex: unrecognized option"):  # -max-print-line is a MiKTeX option
        return (
            "ERROR! `pdflatex` cannot be found. "
            "If it is installed, specify the path to the executable in the configuration file.\n"
            "```json\n"
            '  "pdflatex": "path/to/pdflatex"\n'
            "```"
        )

    log_file = tex.with_suffix(".log")
    msg = log_file.read_text() if log_file.exists() else (stdout or stderr).decode()
    return f"ERROR! Cannot convert.\n\n{msg}"


def word_to_pdf(docx: Path, extra: dict[str, bytes]) -> str:
    """Use the Microsoft Word API (COM object) to export the `.docx` file.

    Requires Word to be installed in the computer running the web application.
    Could consider using [Adobe's PDF Services API](https://developer.adobe.com/document-services/docs/overview/pdf-services-api/)
    if installing Microsoft Word is not possible. See [docx2pdf](https://github.com/softwareone-platform/docx2pdf)
    for a workflow that uses a CLIENT_ID and CLIENT_SECRET provided by Adobe.

    Args:
        docx: The path to a `.docx` file.
        extra: Extra files that were uploaded to be embedded as attachments.
            A mapping between the uploaded filename and the file content.

    Returns:
        An error message, if an error occurred.
    """
    global word_app  # noqa: PLW0603
    if word_app is None:
        try:
            word_app = LoadLibrary(cfg.wordapp, "com")
        except OSError:
            word_app = "Converting a docx file is not supported by the server. Microsoft Word is not installed."
        else:
            word_app.lib.Visible = False

    if isinstance(word_app, str):
        return word_app

    resolved = docx.resolve()
    tmp = resolved.with_name("tmp.pdf")

    try:
        # https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat
        doc = word_app.lib.Documents.Open(resolved.as_posix())
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
    except Exception as e:  # noqa: BLE001
        return f"ERROR! Microsoft Word: {e.args[2][0]}"

    try:
        add_attachments(resolved, tmp, extra)
    except Exception as e:  # noqa: BLE001
        return f"ERROR! {e}"
    else:
        return ""


def add_attachments(docx: Path, tmp: Path, extra: dict[str, bytes]) -> None:
    """Add attachments to a PDF.

    Args:
        docx: The path to the `.docx` file. Only used to create a filename of the PDF.
        tmp: The path to the temporary PDF file that was exported by Word.
        extra: Extra files that were uploaded to be embedded as attachments.
            A mapping between the uploaded filename and the file content.
    """
    now = encode_pdf_date(datetime.now().astimezone())
    with Pdf.open(tmp) as pdf:
        af_entries = list(pdf.Root.get("/AF", Array()))
        for filename, content in extra.items():
            afs = AttachedFileSpec(
                pdf,
                content,
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


async def to_pdf(document: Path, extra: dict[str, bytes]) -> tuple[Path, str]:
    """Convert a file to PDF.

    Args:
        document: The path to the document to convert.
        extra: Extra files that were uploaded for the conversion.
            A mapping between the uploaded filename and the file content.

    Returns:
        The path to the PDF that was created and an error message, if an error occurred.
    """
    pdf = document.with_suffix(".pdf")
    if document.suffix == ".tex":
        for filename, content in extra.items():
            _ = (document.parent / filename).write_bytes(content)

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


async def process_events() -> None:
    """Sleep, in seconds, the asyncio event loop.

    This allows the property of a `dash` component to update properly while a callback is running.

    The duration should be as short as possible that the operating system supports
    such that the properties of the web components are actually updated.
    """
    await asyncio.sleep(cfg.set_props_delay)


async def assets(
    *,
    teams: list[str],
    sync: bool,
    update: Callable[[AgGridData, str], Awaitable[None]] | None = None,
) -> tuple[AgGridData, dict[str, bool], bool]:
    """Search for equipment that are a capital asset.

    Args:
        teams: The teams to check the equipment register of.
        sync: Whether to perform a `git pull` on the register's repository before checking.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        The table data, the validity of each register and whether syncing the repositories was performed.
    """
    synced: bool = sync
    is_valid: RegisterValidity = {}
    data: AgGridData = []

    today = date.today()  # noqa: DTZ011
    registers = cfg.equipment_registers(*teams)

    if sync:
        synced = await git_pull(registers, update)

    for register in registers:
        files = register.files()
        is_valid[register.team] = await validate_register(files, register.team, data, update)
        if not is_valid[register.team]:
            continue

        reg = Register(*files)
        if update is not None:
            await update(data, f"Searching {len(reg)} equipment entries from {register.team}")

        for equipment in reg:
            ce = equipment.quality_manual.financial.capital_expenditure
            if ce is not None:
                data.append(
                    {
                        "ID": equipment.id,
                        "Team": reg.team,
                        "Asset Number": ce.asset_number,
                        "Depreciation Start Date": ce.depreciation_start_date.isoformat(),
                        "Depreciation End Date": ce.depreciation_end_date.isoformat(),
                        "Depreciated?": "No" if ce.depreciation_end_date > today else "Yes",
                        "Price": ce.price,
                        "Currency": ce.currency,
                        "Manufacturer": equipment.manufacturer,
                        "Model": equipment.model,
                    }
                )

        if update is not None:
            await update(data, "")

    return data, is_valid, synced


async def maintenance(
    *,
    teams: list[str],
    months: int,
    sync: bool,
    update: Callable[[AgGridData, str], Awaitable[None]] | None = None,
) -> tuple[AgGridData, dict[str, bool], bool]:
    """Find equipment that needs maintenance.

    Args:
        teams: The teams to check the equipment register of.
        months: The number of months in the future to check if maintenance is due.
        sync: Whether to perform a `git pull` on the register's repository before checking.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        The table data, the validity of each register and whether syncing the repositories was performed.
    """
    data: AgGridData = []
    is_valid: RegisterValidity = {}
    synced: bool = sync

    today = date.today()  # noqa: DTZ011
    registers = cfg.equipment_registers(*teams)

    if sync:
        synced = await git_pull(registers, update)

    for register in registers:
        files = register.files()
        is_valid[register.team] = await validate_register(files, register.team, data, update)
        if not is_valid[register.team]:
            continue

        reg = Register(*files)
        if update is not None:
            await update(data, f"Checking {len(reg)} equipment entries for {register.team}")

        data.extend(
            {
                "ID": equipment.id,
                "Team": reg.team,
                "Due Date": planned.due_date.isoformat(),
                "Overdue?": "Yes" if planned.due_date < today else "No",
                "Task": planned.task,
                "Performed By": planned.performed_by,
                "Manufacturer": equipment.manufacturer,
                "Model": equipment.model,
                "Serial": equipment.serial,
            }
            for equipment in reg
            for planned in equipment.maintenance.planned
            if planned.is_task_due(months)
        )

        if update is not None:
            await update(data, "")

    return data, is_valid, synced


async def recalibrations(  # noqa: C901
    *,
    teams: list[str],
    months: int,
    sync: bool,
    update: Callable[[AgGridData, str], Awaitable[None]] | None = None,
) -> tuple[AgGridData, dict[str, bool], bool]:
    """Find equipment that must be recalibrated.

    Args:
        teams: The teams to check the equipment register of.
        months: The number of months in the future to check if a recalibration is due.
        sync: Whether to perform a `git pull` on the register's repository before checking.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        The table data, the validity of each register and whether syncing the repositories was performed.
    """
    data: AgGridData = []
    is_valid: RegisterValidity = {}
    synced: bool = sync

    today = date.today()  # noqa: DTZ011
    registers = cfg.equipment_registers(*teams)

    if sync:
        synced = await git_pull(registers, update)

    for register in registers:
        files = register.files()
        is_valid[register.team] = await validate_register(files, register.team, data, update)
        if not is_valid[register.team]:
            continue

        reg = Register(*files)
        if update is not None:
            await update(data, f"Checking {len(reg)} equipment entries for {register.team}")

        for equipment in reg:
            if equipment.traceable and equipment.status == Status.Active:
                due, overdue, uncalibrated = "", "", True
                for item in chain(equipment.latest_reports(), equipment.latest_performance_checks()):
                    uncalibrated = False
                    if item.is_calibration_due(months):
                        due = item.next_calibration_date.isoformat()
                        overdue = "Yes" if item.next_calibration_date < today else "No"
                        break  # no need to check other items, since the equipment must be recalibrated

                # If there are no reports and no performance checks, then check
                # if every measurand is specified as being calibrated on demand
                if (
                    uncalibrated
                    and equipment.calibrations
                    and all(measurand.calibration_interval == 0 for measurand in equipment.calibrations)
                ):
                    continue

                if due or uncalibrated:  # A recalibrations is due or the equipment is uncalibrated
                    data.append(
                        {
                            "ID": equipment.id,
                            "Team": reg.team,
                            "Due Date": due or today.isoformat(),
                            "Overdue?": overdue or "Yes (uncalibrated)",
                            "Description": equipment.description,
                            "Manufacturer": equipment.manufacturer,
                            "Model": equipment.model,
                            "Serial": equipment.serial,
                        }
                    )

        if update is not None:
            await update(data, "")

    return data, is_valid, synced


async def search(
    *,
    teams: list[str],
    text: str | re.Pattern[str],
    sync: bool,
    update: Callable[[AgGridData, str], Awaitable[None]] | None = None,
) -> tuple[AgGridData, dict[str, bool], bool, str]:
    """Search for equipment.

    Args:
        teams: The teams to check the equipment register of.
        text: The text to search for.
        sync: Whether to perform a `git pull` on the register's repository before checking.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        The table data, the validity of each register and whether syncing the repositories
            was performed and an error message if `text` is not a valid regex pattern.
    """
    synced: bool = sync
    is_valid: RegisterValidity = {}
    data: AgGridData = []

    try:
        pattern = re.compile(text)
    except re.error as e:
        return data, is_valid, synced, f"{e.__class__.__name__}: {e}"

    registers = cfg.equipment_registers(*teams)

    if sync:
        synced = await git_pull(registers, update)

    for register in registers:
        files = register.files()
        is_valid[register.team] = await validate_register(files, register.team, data, update)
        if not is_valid[register.team]:
            continue

        reg = Register(*files)
        if update is not None:
            await update(data, f"Searching {len(reg)} equipment entries from {register.team}")

        data.extend(
            {
                "ID": equipment.id,
                "Team": reg.team,
                "Location": equipment.location,
                "Description": equipment.description,
                "Manufacturer": equipment.manufacturer,
                "Model": equipment.model,
                "Serial": equipment.serial,
            }
            for equipment in reg.find(pattern)
        )

        if update is not None:
            await update(data, "")

    return data, is_valid, synced, ""


async def validate_register(
    files: list[Path], team: str, data: AgGridData, update: Callable[[AgGridData, str], Awaitable[None]] | None = None
) -> bool:
    """Check if an equipment register is valid.

    Args:
        files: The list of file path that compose the equipment register.
        team: The name of the team that the equipment register belongs to.
        data: The data in the table. Only used if `update` is specified.
        update: A function to call if calling this method from within a `dash` callback.

    Returns:
        Whether the register is valid.
    """
    sha256_validation = cfg.sha256_validation.get(team, SHA256Validation())
    if update is not None:
        msg = (
            f"Validating {team} register (skipping sha256 checksums)"
            if sha256_validation.skip
            else f"Validating {team} register"
        )
        await update(data, msg)

    summary = recursive_validate(
        files=files,
        er_schema=er_schema,
        c_schema=c_schema,
        roots=sha256_validation.roots,
        exit_first=True,
        uri_scheme=None,
        skip_checksum=sha256_validation.skip,
        no_colour=True,
    )
    ok = summary.num_issues == 0
    summary.reset()

    if update is not None and not ok:
        await update(data, f"  \u274c ERROR! {team} register invalid (skipping)")

    return ok


def view(team: str, equipment_id: str) -> Component:
    """Create a `dash` component that displays the XML source of an `<equipment>` element.

    Args:
        team: The team that is responsible for the equipment.
        equipment_id: The equipment ID.

    Returns:
        A `dash` component.
    """
    er = cfg.equipment_registers(team)
    r = Register(*er[0].files())
    return element_to_component(r[equipment_id].to_xml())


def element_to_component(element: Element[str]) -> Component:
    """Recursively converts an XML element into a `dash` component."""
    tag = element.tag
    components: list[Component] = [html.Span(f"<{tag}", className="xml-tag")]
    for name, value in element.attrib.items():
        components.extend(
            [
                html.Span(f" {name}=", className="xml-attribute-name"),
                html.Span(f'"{value}"', className="xml-attribute-value"),
            ]
        )

    text = element.text.strip() if element.text else ""
    if len(element) == 0:  # No children
        if not text:  # Use Short Notation (<tag />)
            components.append(html.Span(" />", className="xml-tag"))
            return html.Div(components, className="xml-element xml-inline")

        components.append(html.Span(">", className="xml-tag"))
        if tag == "data":  # Preserve line terminators
            components.append(html.Pre(text, className="xml-table-data"))
        else:  # Put on a single line, <tag>text</tag>
            components.append(html.Span(text, className="xml-text"))
        components.append(html.Span(f"</{tag}>", className="xml-tag"))
        return html.Div(components, className="xml-element xml-inline")

    # Use Details/Summary dropdown tree and process child elements recursively
    components.append(html.Span(">", className="xml-tag"))
    details: list[Component] = [html.Summary(components, style={"cursor": "pointer"})]
    details.extend(element_to_component(child) for child in element)
    details.append(html.Div(f"</{tag}>", className="xml-tag", style={"marginLeft": "15px"}))
    return html.Details(details, open=True, className="xml-element")
