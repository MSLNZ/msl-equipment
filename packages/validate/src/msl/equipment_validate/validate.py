"""Validate XML files against the schema."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

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

booleans = {"true", "True", "TRUE", "1", "false", "False", "FALSE", "0"}
namespace = "https://measurement.govt.nz/equipment-register"

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
    uri_scheme: URIScheme = None
    debug_name: str = ""


class Summary:
    """Keeps tracks of the number of files validated, errors, and elements that were skipped."""

    num_files: int = 0
    num_errors: int = 0
    num_skipped: int = 0

    def __init__(self, *, exit_first: bool) -> None:
        """Keeps tracks of the number of files validated, errors, and elements that were skipped."""
        self.exit_first: bool = exit_first

    def check_exit(self) -> bool:
        """Check if validation should exit early."""
        return self.exit_first and self.num_errors > 0


def _bool(value: str) -> None:
    """A bool in the table data must only be allowed to have certain values."""
    if value not in booleans:
        expected = ", ".join(booleans)
        msg = f"Invalid bool value {value}, must be one of: {expected}"
        raise ValueError(msg)


def _int32(value: str) -> None:
    """An int in the table data must be in the int32 range."""
    int32 = int(value)
    if int32 < -2147483648 or int32 > 2147483647:  # noqa: PLR2004
        msg = f"Invalid int value {value}, must be in range [-2147483648, 2147483647]"
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


def log_error(
    *,
    file: str | Path,
    line: int,
    column: int = 0,
    message: str = "",
    uri_scheme: URIScheme,
) -> None:
    """Log an ERROR message."""
    # errors are always shown, so no need to use % formatting
    if uri_scheme is None:
        msg = f"{file}:{line}:{column}\n  {message}"
    else:
        # https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
        if uri_scheme == "vscode":
            uri = f"vscode://file/{file}:{line}:{column}"
        else:
            uri = f"{uri_scheme}://open?file={file}&line={line}&column={column}"

        label = f"{file}:{line}:{column}"
        msg = f"\033]8;;{uri}\033\\{label}\033]8;;\033\\\n  {message}"

    log.error(msg)
    Summary.num_errors += 1


def parse(*, file: Path, uri_scheme: URIScheme) -> ElementTree | None:
    """Parse an XML file into an ElementTree.

    Returns `None` if there was an error.
    """
    try:
        return etree.parse(file)
    except OSError:
        log_error(file=file, line=0, message=f"Cannot parse {file}", uri_scheme=uri_scheme)
    except etree.XMLSyntaxError as e:
        line, column = e.position
        log_error(file=file, line=line, column=column, message=e.msg, uri_scheme=uri_scheme)

    return None


def schema_validate(*, path: str, xml: ElementTree, schema: XMLSchema, exit_first: bool, uri_scheme: URIScheme) -> None:
    """Validate an XML file against a schema."""
    log.info("Validating %s", path)
    Summary.num_files += 1

    if schema.validate(xml):
        return

    for error in schema.error_log:
        log_error(
            file=path,
            line=error.line,
            column=error.column,
            message=error.message.replace(f"{namespace}", ""),
            uri_scheme=uri_scheme,
        )
        if exit_first:
            break

    return


def recursive_validate(  # noqa: C901, PLR0913
    *,
    files: list[Path],
    er_schema: XMLSchema,
    c_schema: XMLSchema,
    roots: list[str],
    exit_first: bool,
    uri_scheme: URIScheme,
    skip_checksum: bool,
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
    """
    all_ids: dict[str, tuple[str, int]] = {}  # id: (file, sourceline)
    summary = Summary(exit_first=exit_first)
    for file in files:
        tree = parse(file=file, uri_scheme=uri_scheme)
        if tree is None:
            if summary.check_exit():
                return summary
            continue

        path = str(file)
        tag = tree.getroot().tag
        if tag == f"{{{namespace}}}register":
            schema_validate(path=path, xml=tree, schema=er_schema, exit_first=exit_first, uri_scheme=uri_scheme)
            if summary.check_exit():
                return summary

            ids = validate(
                path=path,
                tree=tree,
                roots=roots,
                exit_first=exit_first,
                uri_scheme=uri_scheme,
                skip_checksum=skip_checksum,
            )
            if summary.check_exit():
                return summary

            for id_, (file1, line1) in all_ids.items():
                if id_ in ids:
                    file2, line2 = ids[id_]
                    msg = f"Duplicate equipment ID ({id_}) also found in {file1}, line {line1}"
                    log_error(file=file2, line=line2, message=msg, uri_scheme=uri_scheme)
                    if summary.check_exit():
                        return summary

            all_ids.update(ids)

        elif tag == "connections":
            schema_validate(path=path, xml=tree, schema=c_schema, exit_first=exit_first, uri_scheme=uri_scheme)
            if summary.check_exit():
                return summary
        else:
            log.debug("Ignoring unsupported msl-equipment XML file %s [root tag: %r]", file, tag)

    return summary


def validate(  # noqa: C901, PLR0911, PLR0912, PLR0913
    *, path: str, tree: ElementTree, roots: list[str], exit_first: bool, uri_scheme: URIScheme, skip_checksum: bool
) -> dict[str, tuple[str, int]]:
    """Validate an equipment register for things that the schema does not validate.

    Args:
        path: File path.
        tree: The element tree.
        roots: The root directory to use for <file> and <digitalReport> elements.
        exit_first: Whether to return on the first error.
        uri_scheme: Used for clickable links in the terminal.
        skip_checksum: Whether to skip <file> and <digitalReport> validations.

    Returns:
        A mapping between the equipment id and (sourceline of the equipment id, file path).
    """
    ns_map = {"reg": namespace}
    ids: dict[str, tuple[str, int]] = {}
    for equipment in tree.xpath("//reg:equipment", namespaces=ns_map):
        id_, manufacturer, model, serial = equipment[:4]  # schema forces order
        ids[id_.text] = (path, id_.sourceline)
        name = f"{manufacturer.text} {model.text} {serial.text}"
        info = Info(url=path, exit_first=exit_first, uri_scheme=uri_scheme, debug_name=name)
        for digital_report in equipment.xpath(".//reg:digitalReport", namespaces=ns_map):
            if skip_checksum:
                Summary.num_skipped += 1
                continue
            ok = validate_file(digital_report, roots=roots, info=info, name="digitalReport")
            if (not ok) and exit_first:
                return ids
        for equation in equipment.xpath(".//reg:equation", namespaces=ns_map):
            ok = validate_equation(equation, ns_map=ns_map, info=info)
            if (not ok) and exit_first:
                return ids
        for file in equipment.xpath(".//reg:file", namespaces=ns_map):
            if skip_checksum:
                Summary.num_skipped += 1
                continue
            ok = validate_file(file, roots=roots, info=info, name="file")
            if (not ok) and exit_first:
                return ids
        for serialised in equipment.xpath(".//reg:serialised", namespaces=ns_map):
            ok = validate_serialised(serialised, info=info)
            if (not ok) and exit_first:
                return ids
        for table in equipment.xpath(".//reg:table", namespaces=ns_map):
            ok = validate_table(table, info=info)
            if (not ok) and exit_first:
                return ids
        for coefficients in equipment.xpath(".//reg:cvdCoefficients", namespaces=ns_map):
            ok = validate_cvd(coefficients, info=info)
            if (not ok) and exit_first:
                return ids
    return ids


def validate_equation(equation: Element, *, ns_map: dict[str, str], info: Info) -> bool:
    """Validates that the equations are valid.

    Returns whether the element is valid.
    """
    log.debug("[%s] Validating <equation> element", info.debug_name)
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
        msg = f"The names of the range variables are not unique for {info.debug_name!r}: {sorted(range_names)}"
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme)
        is_valid = False
        if info.exit_first:
            return False

    if len(names) != len(range_names) or names_set.difference(range_name_set):
        msg = (
            f"The equation variables and the range variables are not the same for {info.debug_name!r}\n"
            f"  equation variables: {', '.join(sorted(names))}\n"
            f"  range variables   : {', '.join(sorted(range_names))}"
        )
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme)
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
        _ = eval(text, None, _locals)  # noqa: S307
    except (SyntaxError, NameError) as e:
        msg = f"Invalid equation syntax for {info.debug_name!r} [equation={text!r}]: {e}"
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme)
        return False
    except ZeroDivisionError:  # valid equation, using value=1.0 was unlucky
        pass

    return True


def validate_file(file: Element, *, roots: list[str], info: Info, name: str) -> bool:  # noqa: C901, PLR0912
    """Validates that the file exists and that the SHA-256 checksum is correct.

    Returns whether the element is valid.
    """
    log.debug("[%s] Validating <%s> element", info.debug_name, name)

    url, checksum = file[:2]  # schema forces order
    assert isinstance(url.text, str)  # noqa: S101
    u = urlparse(url.text)

    # check len() > 1 to ignore a Windows drive letter being interpreted as a scheme
    if len(u.scheme) > 1 and u.scheme != "file":
        msg = f"The url scheme {u.scheme!r} is not yet supported for validation [url={url.text!r}]"
        log_error(file=info.url, line=url.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
        return False

    path: Path | None = Path(url.text)
    if not path or not path.is_file():
        path = None
        for root in roots:
            path = Path(root)
            if u.netloc:
                if ":" in u.netloc:
                    path /= u.netloc
                else:
                    path /= f"//{u.netloc}"
            path /= u.path.lstrip("/") if sys.platform == "win32" else u.path
            if path.is_file():
                break
            path = None

    if path is None:
        msg = f"Cannot find {url.text!r}"
        if roots:
            msg += f", using the roots: {', '.join(roots)}"
        else:
            msg += ", include --root arguments if the url is a relative path"
        log_error(file=info.url, line=url.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
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
        log_error(file=info.url, line=checksum.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
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
            log.debug("[%s] Validating gtcArchive", info.debug_name)
            xml_to_archive(fmt)
        elif tag.endswith("gtcArchiveJSON"):
            log.debug("[%s] Validating gtcArchiveJSON", info.debug_name)
            loads_json(fmt.text)
        else:
            msg = f"Don't know how to deserialize {tag!r}"
            log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme)
            return False
    except Exception as e:  # noqa: BLE001
        msg = f"Invalid serialised {tag!r} for {info.debug_name!r}: {e}"
        log_error(file=info.url, line=line, message=msg, uri_scheme=info.uri_scheme)
        return False
    else:
        return True


def validate_table(table: Element, *, info: Info) -> bool:  # noqa: C901, PLR0912
    """Validates that the data types, header and data are valid.

    Returns whether the element is valid.
    """
    log.debug("[%s] Validating <table> element", info.debug_name)

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
        log_error(file=info.url, line=e_unit.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
        is_valid = False
        if info.exit_first:
            return False

    if len(types) != len(header):
        msg = (
            f"The table <type> and <header> have different lengths for {info.debug_name!r}\n"
            f"  type  : {types}\n"
            f"  header: {header}"
        )
        log_error(file=info.url, line=e_header.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
        is_valid = False
        if info.exit_first:
            return False

    len_types = len(types)
    for row_line in e_data.text.split("\n"):
        row_stripped = row_line.strip()
        if not row_stripped:
            continue
        row = [col.strip() for col in row_stripped.split(",")]
        if len_types != len(row):
            msg = (
                f"The table <data> does not have the expected number of columns for {info.debug_name!r}\n"
                f"  Expected {len_types} columns, row data is {row_stripped!r}"
            )
            log_error(file=info.url, line=e_data.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
            is_valid = False
            if info.exit_first:
                return False

        for typ, col in zip(types, row):
            try:
                dtype_value_check[typ](col)
            except ValueError as e:  # noqa: PERF203
                msg = f"Invalid table <data> for {info.debug_name!r}: {e}"
                log_error(file=info.url, line=e_data.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
                is_valid = False
                if info.exit_first:
                    return False
            except KeyError:
                allowed = ", ".join(dtype_value_check)
                msg = f"Invalid table <type> {typ!r} for {info.debug_name!r}, must be one of: {allowed}"
                log_error(file=info.url, line=e_data.sourceline or 0, message=msg, uri_scheme=info.uri_scheme)
                is_valid = False
                if info.exit_first:
                    return False

    return is_valid


def validate_cvd(coefficients: Element, info: Info) -> bool:
    """Validates that the uncertainty equation is valid.

    Returns whether the element is valid.
    """
    uncertainty = coefficients[5]  # schema forces order
    names = uncertainty.attrib["variables"].split()
    assert uncertainty.text is not None  # noqa: S101
    return _eval(text=uncertainty.text, names=names, info=info, line=uncertainty.sourceline or 0)
