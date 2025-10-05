"""Main CLI entry point."""

from __future__ import annotations

import logging
import os
import sys
from argparse import SUPPRESS, ArgumentParser, RawTextHelpFormatter
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from ._version import __version__
from .osc8 import register_uri_scheme, schemes, unregister_uri_scheme
from .validate import GREEN, RED, RESET, YELLOW, parse, recursive_validate

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

    logging.basicConfig(level=level, format="%(message)s")
    return logging.getLogger(__package__)


def modify_windows_registry(*, log: logging.Logger, remove: bool, add: bool) -> int:
    """Modify the Windows Registry to support clickable hyperlinks."""
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


def maybe_enable_ansi() -> None:
    """Maybe enable ANSI escape sequences."""
    # ANSI escape sequences have worked properly in UNIX terminals for many years. Only Windows has
    # been an issue for a while, but, in Windows 11 22H2, the default app used to host console windows
    # has been changed to Windows Terminal (which does support ANSI escape sequences). After the
    # October 2022 update, Command Prompt, Windows PowerShell, and other console apps appear
    # inside an instance of Windows Terminal.
    # https://support.microsoft.com/en-us/windows/command-prompt-and-windows-powershell-6453ce98-da91-476f-8651-5c14d5777c20
    if (
        (sys.platform != "win32")  # UNIX terminal
        or ("WT_SESSION" in os.environ)  # Windows Terminal
        or ("PYCHARM_HOSTED" in os.environ)  # PyCharm terminal
        or (os.getenv("TERMINAL_EMULATOR", "").startswith("JetBrains"))  # PyCharm terminal
        or (os.getenv("TERM_PROGRAM") == "vscode")  # VS Code terminal
    ):
        return

    # The following fixes ANSI escape sequences if Windows PowerShell or Command Prompt
    # is still being used outside of Windows Terminal
    # https://bugs.python.org/issue30075
    _ = os.system("")  # noqa: S605, S607


def cli(argv: Sequence[str] | None = None) -> int:  # noqa: PLR0911, PLR0915
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
        "-o",
        "--open",
        choices=schemes,
        help=(
            (
                "Use clickable (Ctrl + click) hyperlinks to open Visual Studio\n"
                "(VS), VS Code, PyCharm or Notepad++ to fix issues. You must first\n"
                "run with the --add-winreg-keys flag from an elevated (admin)\n"
                "terminal before clickable links work and you must use a terminal\n"
                "that supports OSC-8 hyperlinks (e.g., Windows Terminal)."
            )
            if IS_WINDOWS
            else SUPPRESS
        ),
    )
    _ = parser.add_argument(
        "-A",
        "--add-winreg-keys",
        action="store_true",
        help=(
            (
                "Add Keys to the Windows Registry to open VS, VS Code, PyCharm\n"
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
        "--remove-winreg-keys",
        action="store_true",
        help=(
            (
                "Remove the Keys from the Windows Registry that were added by\n"
                "--add-winreg-keys and then exit (does not continue to validate\n"
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
        "-n",
        "--no-colour",
        action="store_true",
        help="Suppress coloured output.",
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

    if not args.no_colour:
        maybe_enable_ansi()

    if args.remove_winreg_keys or args.add_winreg_keys:
        if not IS_WINDOWS:
            log.error("Creating clickable links is only valid on Windows")
            return 1
        return modify_windows_registry(log=log, remove=args.remove_winreg_keys, add=args.add_winreg_keys)

    schema_dir = Path(__file__).parent / "schema"
    er_tree = parse(
        file=args.schema or schema_dir / "equipment-register.xsd", uri_scheme=args.open, no_colour=args.no_colour
    )
    if er_tree is None:
        return 1

    c_tree = parse(file=schema_dir / "connections.xsd", uri_scheme=args.open, no_colour=args.no_colour)
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
        uri_scheme=args.open,
        skip_checksum=args.skip_checksum,
        no_colour=args.no_colour,
    )

    log.info("")
    log.info("%s summary %s", "=" * 35, "=" * 35)
    log.info("errors: %d", summary.num_errors)
    log.info("skipped: %d", summary.num_skipped)
    log.info("registers: %d", summary.num_registers)
    log.info("equipment: %d", summary.num_equipment)
    log.info("connections: %d", summary.num_connection)
    log.info("cvdCoefficients: %d", summary.num_cvd)
    log.info("digitalReports: %d", summary.num_digital_report)
    log.info("equations: %d", summary.num_equation)
    log.info("files: %d", summary.num_file)
    log.info("serialised: %d", summary.num_serialised)
    log.info("tables: %d", summary.num_table)
    log.info("")

    if summary.num_errors == 0:
        green, yellow, reset = ("", "", "") if args.no_colour else (GREEN, YELLOW, RESET)
        msg = "Success, no errors found!"
        if summary.num_skipped == 0:
            print(f"{green}{msg}{reset}")  # noqa: T201
        else:
            print(f"{green}{msg}{reset} [{yellow}skipped: {summary.num_skipped}{reset}]")  # noqa: T201
    else:
        colour, reset = ("", "") if args.no_colour else (RED, RESET)
        print(f"{colour}Found {summary.num_errors} errors{reset}")  # noqa: T201

    return summary.num_errors


def main() -> NoReturn:
    """Main CLI entry point."""
    sys.exit(cli(sys.argv[1:]))
