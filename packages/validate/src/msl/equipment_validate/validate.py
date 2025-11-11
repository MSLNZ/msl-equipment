"""Validate XML files against the schema."""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from GTC.persistence import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    loads_json,  # pyright: ignore[reportUnknownVariableType]
)
from GTC.xml_format import (  # type: ignore[import-untyped]  # pyright: ignore[reportMissingTypeStubs]
    xml_to_archive,  # pyright: ignore[reportUnknownVariableType]
)
from lxml import etree

if TYPE_CHECKING:
    from typing import Literal

    from lxml.etree import Element, ElementTree, XMLSchema

    URIScheme = Literal["vs", "vscode", "pycharm"] | None


log = logging.getLogger(__package__)

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
PURPLE = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

booleans = {"true", "True", "TRUE", "1", "false", "False", "FALSE", "0"}
namespace = "https://measurement.govt.nz/equipment-register"
ns_map = {"reg": namespace}

equation_map = {
    "pi": np.pi,
    "pow": np.power,
    "sqrt": np.sqrt,
    "sin": np.sin,
    "asin": np.arcsin,
    "cos": np.cos,
    "acos": np.arccos,
    "tan": np.tan,
    "atan": np.arctan,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
}


@dataclass
class Info:
    """Group common information that is passed around."""

    url: str
    exit_first: bool
    uri_scheme: URIScheme
    debug_name: str
    no_colour: bool


class Summary:
    """Keeps tracks of the number of files validated, issues, and elements."""

    num_issues: int = 0  # the total number of issues
    num_schema_issues: int = 0  # the number of issues that the schema catches
    num_skipped: int = 0
    num_register: int = 0
    num_equipment: int = 0
    num_connection: int = 0
    num_cvd: int = 0
    num_digital_report: int = 0
    num_equation: int = 0
    num_file: int = 0
    num_serialised: int = 0
    num_table: int = 0
    num_warnings: int = 0
    unchecked_equipment: tuple[str, ...] = ()
    unchecked_reports: tuple[str, ...] = ()
    unchecked_performance_checks: tuple[str, ...] = ()

    def __init__(self, *, exit_first: bool) -> None:
        """Keeps tracks of the number of files validated, errors, and elements that were skipped."""
        self.exit_first: bool = exit_first

    def check_exit(self) -> bool:
        """Check if validation should exit early."""
        return self.exit_first and self.num_issues > 0


def _bool(value: str) -> None:
    """A bool in the table data must only be allowed to have certain values."""
    if value not in booleans:
        expected = ", ".join(sorted(booleans))
        msg = f"Invalid bool value {value}, must be one of: {expected}"
        raise ValueError(msg)


def _int32(value: str) -> None:
    """An int in the table data must be in the int32 range."""
    int32 = int(value)
    if int32 < -2147483648 or int32 > 2147483647:  # noqa: PLR2004
        msg = f"Invalid int value {value}, must be in the range [-2147483648, 2147483647]"
        raise ValueError(msg)


def _double(value: str) -> None:
    """A double in the table data must be able to be converted to a float."""
    _ = float(value)


def _string(value: str) -> None:
    """No-op. A string in the table data is already a string."""
    _ = str(value)


dtype_value_check = {
    "bool": _bool,
    "int": _int32,
    "double": _double,
    "string": _string,
}


def log_debug(
    fmt: str,
    *args: object,
    no_colour: bool,
) -> None:
    """Log a DEBUG message."""
    if not log.isEnabledFor(logging.DEBUG):
        return

    msg = fmt % args
    (colour, reset) = ("", "") if no_colour else (CYAN, RESET)
    log.debug("%sDEBUG%s %s", colour, reset, msg)


def log_info(
    fmt: str,
    *args: object,
    no_colour: bool,
) -> None:
    """Log an INFO message."""
    if not log.isEnabledFor(logging.INFO):
        return

    msg = fmt % args
    (colour, reset) = ("", "") if no_colour else (BLUE, RESET)
    log.info("%sINFO%s  %s", colour, reset, msg)


def log_warn(
    fmt: str,
    *args: object,
    no_colour: bool,
) -> None:
    """Log a WARN message."""
    if not log.isEnabledFor(logging.WARNING):
        return

    msg = fmt % args
    (colour, reset) = ("", "") if no_colour else (YELLOW, RESET)
    log.warning("%sWARN%s  %s", colour, reset, msg)


def log_error(
    *,
    file: str | Path,
    line: int,
    no_colour: bool,
    uri_scheme: URIScheme,
    message: str,
    column: int = 0,
) -> None:
    """Log an ERROR message."""
    # errors are always shown, so no need to use % formatting
    if uri_scheme is None:
        msg = f"{file}:{line}:{column}\n  {message}"
    else:
        # https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
        label = f"{file}:{line}:{column}"
        resolved = Path(file).resolve()
        uri = f"{uri_scheme}://file/{resolved}:{line}:{column}"
        msg = f"\033]8;;{uri}\033\\{label}\033]8;;\033\\\n  {message}"

    (colour, reset) = ("", "") if no_colour else (RED, RESET)
    log.error("%sERROR%s %s", colour, reset, msg)
    Summary.num_issues += 1


def parse(*, file: Path, uri_scheme: URIScheme, no_colour: bool) -> ElementTree | None:
    """Parse an XML file into an ElementTree.

    Returns `None` if there was an error.
    """
    try:
        return etree.parse(file)
    except OSError:
        log_error(file=file, line=0, message=f"Cannot parse {file}", uri_scheme=uri_scheme, no_colour=no_colour)
    except etree.XMLSyntaxError as e:
        line, column = e.position
        log_error(file=file, line=line, column=column, message=e.msg, uri_scheme=uri_scheme, no_colour=no_colour)

    return None


def schema_validate(
    *, path: str, tree: ElementTree, schema: XMLSchema, exit_first: bool, uri_scheme: URIScheme, no_colour: bool
) -> bool:
    """Validate an XML file against a schema."""
    log_info("Validating %s", path, no_colour=no_colour)

    root = tree.getroot()
    if root.tag == "connections":
        Summary.num_connection += len(root)
    else:
        Summary.num_equipment += len(root)

    if schema.validate(tree):
        return True

    for error in schema.error_log:
        Summary.num_schema_issues += 1
        log_error(
            file=path,
            line=error.line,
            column=error.column,
            message=error.message.replace(f"{{{namespace}}}", ""),
            uri_scheme=uri_scheme,
            no_colour=no_colour,
        )
        if exit_first:
            break

    return False


def recursive_validate(  # noqa: C901, PLR0912, PLR0913
    *,
    files: list[Path],
    er_schema: XMLSchema,
    c_schema: XMLSchema,
    roots: list[str],
    exit_first: bool,
    uri_scheme: URIScheme,
    skip_checksum: bool,
    no_colour: bool,
) -> Summary:
    """Recursively validate files.

    Args:
        files: The files to validate.
        er_schema: Equipment-register schema.
        c_schema: Connections schema.
        roots: The root directory to use for <file> and <digitalReport> elements.
        exit_first: Whether to return on the first error.
        uri_scheme: Used for clickable links in the terminal.
        skip_checksum: Whether to skip <file> and <digitalReport> validations.
        no_colour: Suppress coloured output.
    """
    all_ids: dict[str, tuple[str, int]] = {}  # id: (file, sourceline)
    summary = Summary(exit_first=exit_first)
    for file in files:
        tree = parse(file=file, uri_scheme=uri_scheme, no_colour=no_colour)
        if tree is None:
            if summary.check_exit():
                return summary
            continue

        path = str(file)
        tag = str(tree.getroot().tag)
        if tag.endswith("register"):
            Summary.num_register += 1
            valid = schema_validate(
                path=path,
                tree=tree,
                schema=er_schema,
                exit_first=exit_first,
                uri_scheme=uri_scheme,
                no_colour=no_colour,
            )
            if summary.check_exit():
                return summary

            if not valid:
                continue

            find_unchecked(path, tree)

            ids = validate(
                path=path,
                tree=tree,
                roots=roots,
                exit_first=exit_first,
                uri_scheme=uri_scheme,
                skip_checksum=skip_checksum,
                no_colour=no_colour,
            )
            if summary.check_exit():
                return summary

            for id_, (file1, line1) in all_ids.items():
                if id_ in ids:
                    file2, line2 = ids[id_]
                    msg = f"Duplicate equipment ID '{id_}' also found in {file1}, line {line1}"
                    log_error(file=file2, line=line2, message=msg, uri_scheme=uri_scheme, no_colour=no_colour)
                    if summary.check_exit():
                        return summary

            all_ids.update(ids)

        elif tag == "connections":
            _ = schema_validate(
                path=path, tree=tree, schema=c_schema, exit_first=exit_first, uri_scheme=uri_scheme, no_colour=no_colour
            )
            if summary.check_exit():
                return summary
        else:
            log_debug("Ignoring unsupported msl-equipment XML file %s [root tag: %r]", file, tag, no_colour=no_colour)

    return summary


def validate(  # noqa: C901, PLR0911, PLR0912
    *,
    path: str,
    tree: ElementTree,
    roots: list[str],
    exit_first: bool,
    uri_scheme: URIScheme,
    skip_checksum: bool,
    no_colour: bool,
) -> dict[str, tuple[str, int]]:
    """Validate an equipment register for things that the schema does not validate.

    Args:
        path: File path.
        tree: The element tree.
        roots: The root directory to use for <file> and <digitalReport> elements.
        exit_first: Whether to return on the first error.
        uri_scheme: Used for clickable links in the terminal.
        skip_checksum: Whether to skip <file> and <digitalReport> validations.
        no_colour: Whether to suppress coloured output.

    Returns:
        A mapping between the equipment id and `(file path, sourceline of the equipment id)`.
    """
    ids: dict[str, tuple[str, int]] = {}
    for equipment in tree.xpath("//reg:equipment", namespaces=ns_map):
        id_, manufacturer, model, serial = equipment[:4]  # schema forces order
        ids[id_.text] = (path, id_.sourceline)
        name = f"{manufacturer.text}|{model.text}|{serial.text}"
        info = Info(url=path, exit_first=exit_first, uri_scheme=uri_scheme, debug_name=name, no_colour=no_colour)
        for digital_report in equipment.xpath(".//reg:digitalReport", namespaces=ns_map):
            Summary.num_digital_report += 1
            if skip_checksum:
                Summary.num_skipped += 1
                log_warn("Skipped validation of <digitalReport> for %r", name, no_colour=no_colour)
                continue
            ok = validate_file(digital_report, roots=roots, info=info, name="digitalReport")
            if (not ok) and exit_first:
                return ids
        for equation in equipment.xpath(".//reg:equation", namespaces=ns_map):
            Summary.num_equation += 1
            ok = validate_equation(equation, ns_map=ns_map, info=info)
            if (not ok) and exit_first:
                return ids
        for file in equipment.xpath(".//reg:file", namespaces=ns_map):
            Summary.num_file += 1
            if skip_checksum:
                Summary.num_skipped += 1
                log_warn("Skipped validation of <file> for %r", name, no_colour=no_colour)
                continue
            ok = validate_file(file, roots=roots, info=info, name="file")
            if (not ok) and exit_first:
                return ids
        for serialised in equipment.xpath(".//reg:serialised", namespaces=ns_map):
            Summary.num_serialised += 1
            ok = validate_serialised(serialised, info=info)
            if (not ok) and exit_first:
                return ids
        for table in equipment.xpath(".//reg:table", namespaces=ns_map):
            Summary.num_table += 1
            ok = validate_table(table, info=info)
            if (not ok) and exit_first:
                return ids
        for coefficients in equipment.xpath(".//reg:cvdCoefficients", namespaces=ns_map):
            Summary.num_cvd += 1
            ok = validate_cvd(coefficients, info=info)
            if (not ok) and exit_first:
                return ids
    return ids


def validate_equation(equation: Element, *, ns_map: dict[str, str], info: Info) -> bool:
    """Validates that the equations are valid.

    Returns whether the element is valid.
    """
    log_debug("Validating <equation> for %r", info.debug_name, no_colour=info.no_colour)
    line = equation.sourceline or 0
    is_valid = True

    value, uncertainty = equation[:2]  # schema forces order

    val_names = value.attrib["variables"].split()
    un_names = uncertainty.attrib["variables"].split()

    names = val_names + un_names
    names_set = set(names)

    range_names = equation.xpath(".//reg:range/@variable", namespaces=ns_map)
    range_name_set = set(range_names)
    if len(range_names) != len(range_name_set):
        ranges_line = equation[3].sourceline or line
        msg = f"The names of the range variables are not unique for {info.debug_name!r}: {range_names}"
        log_error(file=info.url, line=ranges_line, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour)
        is_valid = False
        if info.exit_first:
            return False

    if len(names) != len(range_names) or names_set.difference(range_name_set):
        msg = (
            f"The equation variables and the range variables are not the same for {info.debug_name!r}\n"
            f"  equation variables: {', '.join(names)}\n"
            f"  range variables   : {', '.join(range_names)}"
        )
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour)
        is_valid = False
        if info.exit_first:
            return False

    for el, names in ((value, val_names), (uncertainty, un_names)):
        assert el.text is not None  # noqa: S101
        ok = _eval(text=el.text, names=names, info=info, line=el.sourceline or 0)
        if not ok:
            is_valid = False
            if info.exit_first:
                return False

    return is_valid


def _eval(*, text: str, names: list[str], info: Info, line: int) -> bool:
    """Calls the builtin eval() function."""
    _locals: dict[str, object] = dict.fromkeys(names, 1.0)
    _locals.update(equation_map)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=RuntimeWarning)
            _ = eval(text, None, _locals)  # noqa: S307
    except (SyntaxError, NameError) as e:
        msg = f"Invalid equation syntax for {info.debug_name!r} [equation={text}]: {e}"
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour)
        return False
    except ZeroDivisionError:  # valid equation, but using value=1.0 was an unlucky choice
        pass

    return True


def validate_file(file: Element, *, roots: list[str], info: Info, name: str) -> bool:  # noqa: C901, PLR0912
    """Validates that the file exists and that the SHA-256 checksum is correct.

    Returns whether the element is valid.
    """
    log_debug("Validating <%s> for %r", info.debug_name, name, no_colour=info.no_colour)

    url, checksum = file[:2]  # schema forces order
    assert isinstance(url.text, str)  # noqa: S101

    index = url.text.find(":")
    if (index == -1) or (
        index == 1 and len(url.text) > 2 and url.text[2] in ("/", "\\")  # noqa: PLR2004
    ):
        scheme, text = "", url.text  # assume Windows drive letter
    else:
        scheme, text = url.text[:index], url.text[index + 1 :]
        if text[:2] == "//":
            text = text[2:]

        # Check for "/c:/path/to/file.txt", which could come from "file:///c:/path/to/file.txt"
        # https://www.rfc-editor.org/rfc/rfc8089.html#appendix-E.2
        if text.startswith("/") and len(text) > 3 and text[2] == ":" and text[3] in ("/", "\\"):  # noqa: PLR2004
            text = text.lstrip("/")

    if scheme and scheme != "file":
        msg = f"The url scheme {scheme!r} is not yet supported for validation [url={url.text}]"
        log_error(
            file=info.url, line=url.sourceline or 0, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour
        )
        return False

    path = Path(text)
    if not path.is_file():
        for root in roots:
            p = Path(root) / path
            if p.is_file():
                path = p
                break

    if not path.is_file():
        msg = f"Cannot find '{url.text}'"
        if roots:
            msg += f", using the roots: {', '.join(roots)}"
        else:
            msg += ", include --root arguments if the url is a relative path"
        log_error(
            file=info.url, line=url.sourceline or 0, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour
        )
        return False

    sha = sha256()
    with path.open("rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            sha.update(data)

    assert checksum.text is not None  # noqa: S101
    specified = checksum.text.lower()
    expected = sha.hexdigest()
    if expected != specified:
        msg = (
            f"The SHA-256 checksum of {path} does not match for {info.debug_name!r}\n"
            f"  expected: {expected}\n"
            f"  <sha256>: {specified}"
        )
        log_error(
            file=info.url,
            line=checksum.sourceline or 0,
            message=msg,
            uri_scheme=info.uri_scheme,
            no_colour=info.no_colour,
        )
        return False

    return True


def validate_serialised(serialised: Element, *, info: Info) -> bool:
    """Validates that the serialised content is a valid GTC Archive.

    Returns whether the element is valid.
    """
    fmt = serialised[0]
    line = fmt.sourceline or 0
    tag = fmt.tag
    assert isinstance(tag, str)  # noqa: S101
    try:
        if tag.endswith("gtcArchive"):
            log_debug("Validating <gtcArchive> for %r", info.debug_name, no_colour=info.no_colour)
            xml_to_archive(fmt)
        elif tag.endswith("gtcArchiveJSON"):
            log_debug("Validating <gtcArchiveJSON> for %r", info.debug_name, no_colour=info.no_colour)
            loads_json(fmt.text)
        else:
            msg = f"Don't know how to deserialize {tag!r}"
            log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour)
            return False
    except Exception as e:  # noqa: BLE001
        msg = f"Invalid serialised {tag!r} for {info.debug_name!r}: {e}"
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme, no_colour=info.no_colour)
        return False
    else:
        return True


def validate_table(table: Element, *, info: Info) -> bool:  # noqa: C901, PLR0911, PLR0912, PLR0915
    """Validates that the data types, header and data are valid.

    Returns whether the element is valid.
    """
    log_debug("Validating <table> for %r", info.debug_name, no_colour=info.no_colour)

    e_types, e_unit, e_header, e_data = table[:4]  # schema forces order
    assert e_types.text is not None  # noqa: S101
    assert e_unit.text is not None  # noqa: S101
    assert e_header.text is not None  # noqa: S101
    assert e_data.text is not None  # noqa: S101

    types = [t.strip() for t in e_types.text.split(",")]
    units = [u.strip() for u in e_unit.text.split(",")]
    header = [h.strip() for h in e_header.text.split(",")]
    is_valid = True

    if len(types) != len(units):
        msg = (
            f"The table <type> and <unit> have different lengths for {info.debug_name!r}\n"
            f"  type: {types}\n"
            f"  unit: {units}"
        )
        log_error(
            file=info.url,
            line=e_unit.sourceline or 0,
            message=msg,
            uri_scheme=info.uri_scheme,
            no_colour=info.no_colour,
        )
        is_valid = False
        if info.exit_first:
            return False

    if len(types) != len(header):
        msg = (
            f"The table <type> and <header> have different lengths for {info.debug_name!r}\n"
            f"  type  : {types}\n"
            f"  header: {header}"
        )
        log_error(
            file=info.url,
            line=e_header.sourceline or 0,
            message=msg,
            uri_scheme=info.uri_scheme,
            no_colour=info.no_colour,
        )
        is_valid = False
        if info.exit_first:
            return False

    len_types = len(types)
    sourceline = e_data.sourceline or 0
    all_rows = e_data.text.split("\n")

    # it's ok to have empty rows before and after the table data but not in-between rows
    start, stop = None, None
    for i, row_data in enumerate(all_rows):
        if row_data.strip():
            if start is None:
                start = i
            stop = i + 1

    sourceline += start or 0
    for row_data in all_rows[start:stop]:
        row_stripped = row_data.strip()
        if not row_stripped:
            log_error(
                file=info.url,
                line=sourceline,
                message=f"The table <data> cannot have an empty row for {info.debug_name!r}",
                uri_scheme=info.uri_scheme,
                no_colour=info.no_colour,
            )
            is_valid = False
            if info.exit_first:
                return False
            continue

        row = [col.strip() for col in row_stripped.split(",")]
        if len_types != len(row):
            msg = (
                f"The table <data> does not have the expected number of columns for {info.debug_name!r}\n"
                f"  Expected {len_types} columns, row data is {row_stripped!r}"
            )
            log_error(
                file=info.url,
                line=sourceline,
                message=msg,
                uri_scheme=info.uri_scheme,
                no_colour=info.no_colour,
            )
            is_valid = False
            if info.exit_first:
                return False

        for typ, col in zip(types, row):
            try:
                dtype_value_check[typ](col)
            except ValueError as e:  # noqa: PERF203
                msg = f"Invalid table <data> for {info.debug_name!r}: {e}"
                log_error(
                    file=info.url,
                    line=sourceline,
                    message=msg,
                    uri_scheme=info.uri_scheme,
                    no_colour=info.no_colour,
                )
                is_valid = False
                if info.exit_first:
                    return False
            except KeyError:
                allowed = ", ".join(dtype_value_check)
                msg = f"Invalid table <type> {typ!r} for {info.debug_name!r}, must be one of: {allowed}"
                log_error(
                    file=info.url,
                    line=e_types.sourceline or 0,
                    message=msg,
                    uri_scheme=info.uri_scheme,
                    no_colour=info.no_colour,
                )
                is_valid = False
                if info.exit_first:
                    return False

        sourceline += 1

    return is_valid


def validate_cvd(coefficients: Element, info: Info) -> bool:
    """Validates that the uncertainty equation is valid.

    Returns whether the element is valid.
    """
    uncertainty = coefficients[5]  # schema forces order
    names = uncertainty.attrib["variables"].split()
    assert uncertainty.text is not None  # noqa: S101
    return _eval(text=uncertainty.text, names=names, info=info, line=uncertainty.sourceline or 0)


def find_unchecked(path: str, tree: ElementTree) -> None:
    """Find equipment, report and performanceCheck elements that have not been 'checkedBy'.

    Args:
        path: File path.
        tree: The element tree.
    """
    unchecked_equipment = tuple(
        f"{path}:{element.sourceline}"
        for element in tree.xpath("//reg:equipment", namespaces=ns_map)
        if not element.get("checkedBy")
    )

    unchecked_reports = tuple(
        f"{path}:{element.sourceline}"
        for element in tree.xpath("//reg:report", namespaces=ns_map)
        if not element.get("checkedBy")
    )

    unchecked_performance_checks = tuple(
        f"{path}:{element.sourceline}"
        for element in tree.xpath("//reg:performanceCheck", namespaces=ns_map)
        if not element.get("checkedBy")
    )

    Summary.num_warnings += len(unchecked_equipment) + len(unchecked_reports) + len(unchecked_performance_checks)
    Summary.unchecked_equipment += unchecked_equipment
    Summary.unchecked_reports += unchecked_reports
    Summary.unchecked_performance_checks += unchecked_performance_checks
