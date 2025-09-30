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
from .validate import parse, recursive_validate

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import NoReturn


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


def cli(argv: Sequence[str] | None = None) -> int:
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
            "multiple times."
        ),
    )
    _ = parser.add_argument(
        "-l",
        "--links",
        choices=("vs", "vscode", "pycharm"),
        help=(
            "Use clickable links to open VS, VSCode or PyCharm to fix issues."
            if sys.platform == "win32" else SUPPRESS
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
        help="Show schema version information and exit.",
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

    schema_dir = Path(__file__).parent / "schema"
    er_tree = parse(file=args.schema or schema_dir / "equipment-register.xsd", uri_scheme=args.links)
    if er_tree is None:
        return 1

    c_tree = parse(file=schema_dir / "connections.xsd", uri_scheme=args.links)
    if c_tree is None:
        return 1

    log.info("%s validation starts %s", "=" * 30, "=" * 30)
    log.info("msl-equipment-validate: %s", __version__)
    log.info("lxml: %s", version("GTC"))
    log.info("GTC: %s", version("lxml"))
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
    log.info("errors: %d", summary.num_errors)
    log.info("skipped: %d", summary.num_skipped)
    return summary.num_errors


def main() -> NoReturn:
    """Main CLI entry point."""
    sys.exit(cli(sys.argv[1:]))
