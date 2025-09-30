"""Main CLI entry point."""

from __future__ import annotations

import logging
import sys
from argparse import SUPPRESS, ArgumentParser, RawTextHelpFormatter
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from ._version import __version__
from .osc8 import register_uri_scheme, schemes, unregister_uri_scheme
from .validate import parse, recursive_validate

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import NoReturn


IS_WINDOWS = sys.platform == "win32"


def recursive(directory: Path) -> list[Path]:
    """Recursively find XML files starting from a directory."""
    files: list[Path] = []
    if not directory.is_dir():
        return files

    for file in directory.rglob("*.xml"):
        # Ignore XML files in hidden directories (e.g., XML files in PyCharm's .idea directory)
        if any(part.startswith(".") for part in file.parts):
            continue
        files.append(file)

    return files


def configure_logging(*, quiet: bool, verbose: bool) -> logging.Logger:
    """Configure logging."""
    if (quiet and verbose) or (not (quiet or verbose)):
        level = logging.INFO
    elif quiet:
        level = logging.ERROR
    else:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(levelname)-5s: %(message)s",
    )

    return logging.getLogger(__package__)


def modify_windows_registry(*, log: logging.Logger, remove: bool, add: bool) -> int:
    """Modify the Windows Registry for clickable links."""
    if remove:
        for scheme in schemes:
            try:
                unregister_uri_scheme(scheme)
            except PermissionError:  # noqa: PERF203
                log.error("You must use an elevated (admin) terminal to modify the Windows Registry")  # noqa: TRY400
                return 1
            except FileNotFoundError:  # already removed
                continue
        return 0

    if add:
        for scheme in schemes:
            try:
                register_uri_scheme(scheme)
            except PermissionError:  # noqa: PERF203
                log.error("You must use an elevated (admin) terminal to modify the Windows Registry")  # noqa: TRY400
                return 1

    return 0


def cli(argv: Sequence[str] | None = None) -> int:  # noqa: PLR0911
    """CLI entry point."""
    parser = ArgumentParser(
        description="Validate equipment registers and connection files.",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
    )
    # fmt: off
    _ = parser.add_argument(
        "path",
        nargs="?",
        help=(
            "The path to an equipment-register file, a connections file or\n"
            "a directory containing multiple files to recursively validate.\n"
            "Default is to recursively validate XML files starting from the\n"
            "current working directory."
        ),
    )
    _ = parser.add_argument(
        "-s",
        "--schema",
        help=(
            "Path to an alternative equipment-register schema file to use\n"
            "for validation."
        ),
    )
    _ = parser.add_argument(
        "-r",
        "--root",
        default=[],
        action="append",
        help=(
            "Root directory to use when validating <file> or <digitalReport>\n"
            "elements and the <url> is a relative path. Can be specified\n"
            "multiple times if multiple roots are required."
        ),
    )
    _ = parser.add_argument(
        "-l",
        "--links",
        choices=schemes,
        help=(
            (
                "Use clickable (Ctrl + click) links to open VS, VSCode, PyCharm\n"
                "or Notepad++ to fix issues. You must first run with the\n"
                "--add-winreg-links flag from an elevated (admin) terminal\n"
                "before clickable links work and you must use a terminal that\n"
                "supports OSC-8 Hyperlinks (e.g., Windows Terminal)."
            )
            if IS_WINDOWS
            else SUPPRESS
        ),
    )
    _ = parser.add_argument(
        "-A",
        "--add-winreg-links",
        action="store_true",
        help=(
            (
                "Add Keys to the Windows Registry to open VS, VSCode, PyCharm\n"
                "or Notepad++ to fix issues and then exit (does not continue\n"
                "to validate files). You must run the command from an elevated\n"
                "(admin) terminal to modify the Windows Registry."
            )
            if IS_WINDOWS
            else SUPPRESS
        ),
    )
    _ = parser.add_argument(
        "-R",
        "--remove-winreg-links",
        action="store_true",
        help=(
            (
                "Remove the Keys from the Windows Registry that were added by\n"
                "--add-winreg-links and then exit (does not continue to validate\n"
                "files). You must run the command from an elevated (admin)\n"
                "terminal to modify the Windows Registry."
            )
            if IS_WINDOWS
            else SUPPRESS
        ),
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show more information while validating (include DEBUG messages).",
    )
    _ = parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Show less information while validating (only ERROR messages).",
    )
    _ = parser.add_argument(
        "-x",
        "--exit-first",
        action="store_true",
        help="Exit on first validation error.",
    )
    _ = parser.add_argument(
        "-c",
        "--skip-checksum",
        action="store_true",
        help="Skip <file> and <digitalReport> SHA-256 checksum validations.",
    )
    _ = parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show version information and exit.",
    )
    _ = parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
        default=SUPPRESS
    )
    # fmt: on

    args = parser.parse_args(argv)

    log = configure_logging(quiet=args.quiet, verbose=args.verbose)

    if args.remove_winreg_links or args.add_winreg_links:
        if not IS_WINDOWS:
            log.error("Creating clickable links is only valid on Windows")
            return 1
        return modify_windows_registry(log=log, remove=args.remove_winreg_links, add=args.add_winreg_links)

    schema_dir = Path(__file__).parent / "schema"
    er_tree = parse(file=args.schema or schema_dir / "equipment-register.xsd", uri_scheme=args.links)
    if er_tree is None:
        return 1

    c_tree = parse(file=schema_dir / "connections.xsd", uri_scheme=args.links)
    if c_tree is None:
        return 1

    log.info("%s validation starts %s", "=" * 30, "=" * 30)
    log.info("msl-equipment-validate: %s", __version__)
    log.info("lxml: %s", version("lxml"))
    log.info("GTC: %s", version("GTC"))
    log.info("equipment-register: %s", er_tree.getroot().get("version", "UNKNOWN"))
    log.info("connections: %s", c_tree.getroot().get("version", "UNKNOWN"))
    log.info("")
    if args.version:
        return 0

    path = Path(args.path or "").expanduser()
    if not path.exists():
        log.error("%s does not exist", path)
        return 1

    er_schema = etree.XMLSchema(er_tree)
    c_schema = etree.XMLSchema(c_tree)
    files = [path] if path.is_file() else recursive(path)
    summary = recursive_validate(
        files=files,
        er_schema=er_schema,
        c_schema=c_schema,
        roots=args.root,
        exit_first=args.exit_first,
        uri_scheme=args.links,
        skip_checksum=args.skip_checksum,
    )

    log.info("")
    log.info("%s summary %s", "=" * 35, "=" * 35)
    log.info("files: %d", summary.num_files)
    log.info("equipment: %d", summary.num_equipment)
    if summary.num_connection:
        log.info("connection: %d", summary.num_connection)
    log.info("errors: %d", summary.num_errors)
    log.info("skipped: %d", summary.num_skipped)
    return summary.num_errors


def main() -> NoReturn:
    """Main CLI entry point."""
    sys.exit(cli(sys.argv[1:]))
