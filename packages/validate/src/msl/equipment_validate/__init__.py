"""Main CLI entry point."""

from __future__ import annotations

import logging
import os
import platform
import sys
from argparse import SUPPRESS, ArgumentParser, RawTextHelpFormatter
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING

from lxml import etree

from ._version import __version__
from .osc8 import register_uri_scheme, schemes, unregister_uri_scheme
from .validate import GREEN, RED, RESET, YELLOW, log, log_error, log_warn, parse, recursive_validate

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import NoReturn

    from .validate import URIScheme

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

    return sorted(files)


def configure_logging(*, quiet: int, verbose: int) -> logging.Logger:
    """Configure logging."""
    n = verbose - quiet
    if n > 0:
        level = logging.DEBUG
    elif n == 0:
        level = logging.INFO
    elif n == -1:
        level = logging.WARNING
    elif n == -2:  # noqa: PLR2004
        level = logging.ERROR
    else:
        level = logging.CRITICAL

    logging.basicConfig(level=level, format="%(message)s")
    logger = logging.getLogger(__package__)
    logger.setLevel(level)
    return logger


def modify_windows_registry(*, log: logging.Logger, remove: bool, add: bool) -> int:
    """Modify the Windows Registry to support clickable hyperlinks."""
    if remove:
        for scheme in schemes:
            try:
                _ = unregister_uri_scheme(scheme)
            except PermissionError:  # noqa: PERF203
                log.error("You must use an elevated (admin) terminal to modify the Windows Registry")  # noqa: TRY400
                return 1
            except ModuleNotFoundError:
                log.error("Unregistering a URI Scheme is only supported on Windows")  # noqa: TRY400
                return 1
            except FileNotFoundError:  # already removed
                continue
        return 0

    if add:
        for scheme in schemes:
            try:
                _ = register_uri_scheme(scheme)
            except PermissionError:  # noqa: PERF203
                log.error("You must use an elevated (admin) terminal to modify the Windows Registry")  # noqa: TRY400
                return 1
            except ModuleNotFoundError:
                log.error("Registering a URI Scheme is only supported on Windows")  # noqa: TRY400
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
        (not IS_WINDOWS)  # UNIX terminal
        or ("WT_SESSION" in os.environ)  # Windows Terminal
        or ("PYCHARM_HOSTED" in os.environ)  # PyCharm terminal
        or (os.getenv("TERMINAL_EMULATOR", "").startswith("JetBrains"))  # PyCharm terminal
        or (os.getenv("TERM_PROGRAM") == "vscode")  # VS Code terminal
    ):
        return

    # The following fixes ANSI escape sequences if Windows PowerShell or Command Prompt
    # is still being used outside of Windows Terminal (prefer to not have a dependency on colorama)
    # https://bugs.python.org/issue30075
    _ = os.system("")  # noqa: S605, S607


def log_unchecked(
    *,
    message: str,
    uri_scheme: URIScheme,
    no_colour: bool,
    name: str,
) -> None:
    """Log an message as a WARNING for an element that has not been 'checkedBy' someone."""
    if uri_scheme is None:
        msg = message
    else:
        # https://gist.github.com/egmontkob/eb114294efbcd5adb1944c9f3cb5feda
        uri = f"{uri_scheme}://file/{message}"
        msg = f"\033]8;;{uri}\033\\{message}\033]8;;\033\\"

    (colour, reset) = ("", "") if no_colour else (YELLOW, RESET)
    log.warning("  %sUnchecked <%s>%s %s", colour, name, reset, msg)


def configure_parser() -> ArgumentParser:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        prog="msl-equipment-validate",
        description="Validate equipment registers and connection files.",
        formatter_class=RawTextHelpFormatter,
        add_help=False,
    )
    # fmt: off
    _ = parser.add_argument(
        "paths",
        nargs="*",
        help=(
            "Path to an equipment-register file, a connections file\n"
            "or a directory containing multiple files to recursively\n"
            "validate. Can specify multiple paths. Default is to\n"
            "recursively validate XML files starting from the current\n"
            "working directory."
        ),
    )
    _ = parser.add_argument(
        "-s",
        "--schema",
        help=(
            "Path to an alternative equipment-register schema file\n"
            "to use for validation."
        ),
    )
    _ = parser.add_argument(
        "-r",
        "--root",
        default=[],
        action="extend",
        nargs="*",
        type=str,
        help=(
            "Root directory to use when validating <digitalReport>\n"
            "or <file> elements and the <url> is a relative path.\n"
            "Can be specified multiple times if multiple roots are\n"
            "required. If a directory contains whitespace, surround\n"
            r'the value with quotes, e.g., --root "C:\Path\With Space"'
        ),
    )
    _ = parser.add_argument(
        "-l",
        "--link",
        choices=schemes,
        help=(
            (
                "Use clickable (Ctrl + click) hyperlinks to open Visual\n"
                "Studio, Visual Studio Code, PyCharm or Notepad++ to fix\n"
                "issues. You must first run with the --add-winreg-keys\n"
                "flag from an elevated (admin) terminal before clickable\n"
                "links work and you must use a terminal that supports\n"
                "OSC-8 hyperlinks, e.g., Windows Terminal."
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
                "Add Keys to the Windows Registry to open Visual Studio,\n"
                "Visual Studio Code, PyCharm or Notepad++ to fix issues\n"
                "and exit (does not continue to validate files). You\n"
                "must run the command from an elevated (admin) terminal\n"
                "to modify the Windows Registry."
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
                "Remove the Keys from the Windows Registry that were added\n"
                "by --add-winreg-keys and exit (does not continue to\n"
                "validate files). You must run the command from an elevated\n"
                "(admin) terminal to modify the Windows Registry."
            )
            if IS_WINDOWS
            else SUPPRESS
        ),
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Show more information while validating.",
    )
    _ = parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help=("Show less information while validating. Option is additive\n"
              "and can be used up to 3 times (suppressing INFO, WARN and\n"
              "ERROR logging levels)."
        ),
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
        help="Skip <file> and <digitalReport> SHA256 checksum validation.",
    )
    _ = parser.add_argument(
        "-u",
        "--show-unchecked",
        action="store_true",
        help="Show the list of elements that have not been 'checkedBy'.",
    )
    _ = parser.add_argument(
        "-n",
        "--no-colour",
        action="store_true",
        help="Suppress coloured output.",
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
    return parser


def cli(argv: Sequence[str] | None = None) -> int:  # noqa: C901, PLR0912, PLR0915
    """CLI entry point."""
    parser = configure_parser()
    args = parser.parse_args(argv)

    log = configure_logging(quiet=args.quiet, verbose=args.verbose)

    if not args.no_colour:
        maybe_enable_ansi()

    if args.remove_winreg_keys or args.add_winreg_keys:
        if not IS_WINDOWS:
            log.error("Modifying the Windows Registry is only valid on Windows")
            return 1
        return modify_windows_registry(log=log, remove=args.remove_winreg_keys, add=args.add_winreg_keys)

    schema_dir = Path(__file__).parent / "schema"
    er_tree = parse(
        file=args.schema or schema_dir / "equipment-register.xsd", uri_scheme=args.link, no_colour=args.no_colour
    )
    if er_tree is None:
        return 1

    c_tree = parse(file=schema_dir / "connections.xsd", uri_scheme=args.link, no_colour=args.no_colour)
    assert c_tree is not None  # noqa: S101

    log.info("%s Validation Starts %s", "=" * 30, "=" * 30)
    log.info("platform: Python %s (%s)", platform.python_version(), platform.system())
    log.info("msl-equipment-validate: %s", __version__)
    log.info("lxml: %s", version("lxml"))
    log.info("GTC: %s", version("GTC"))
    log.info("equipment-register: %s", er_tree.getroot().get("version", "UNKNOWN"))
    log.info("connections: %s", c_tree.getroot().get("version", "UNKNOWN"))
    if args.root:
        log.info("roots: %s", "\n       ".join(args.root))
    log.info("")
    if args.version:
        return 0

    paths = [Path(p).expanduser() for p in args.paths]
    if not paths:
        files: list[Path] = recursive(Path())
    else:
        files = []
        for path in paths:
            if path.suffix:
                files.append(path)
            elif path.is_dir():
                files.extend(recursive(path))
            else:
                log_error(
                    file=path,
                    line=0,
                    no_colour=args.no_colour,
                    uri_scheme=args.link,
                    message="Directory not found",
                )

    er_schema = etree.XMLSchema(er_tree)
    c_schema = etree.XMLSchema(c_tree)
    summary = recursive_validate(
        files=files,
        er_schema=er_schema,
        c_schema=c_schema,
        roots=args.root,
        exit_first=args.exit_first,
        uri_scheme=args.link,
        skip_checksum=args.skip_checksum,
        no_colour=args.no_colour,
    )

    log.info("")
    log.info("%s Summary %s", "=" * 35, "=" * 35)
    log.info("<connection> %d", summary.num_connection)
    log.info("<cvdCoefficients> %d", summary.num_cvd)
    log.info("<digitalReport> %d", summary.num_digital_report)
    log.info("<equation> %d", summary.num_equation)
    log.info("<equipment> %d", summary.num_equipment)
    log.info("<file> %d", summary.num_file)
    log.info("<register> %d", summary.num_register)
    log.info("<serialised> %d", summary.num_serialised)
    log.info("<table> %d", summary.num_table)
    log.info("")

    for name, tup in [
        ("equipment", summary.unchecked_equipment),
        ("report", summary.unchecked_reports),
        ("performanceCheck", summary.unchecked_performance_checks),
    ]:
        if tup:
            log_warn(
                "%d <%s> element%s not been 'checkedBy' someone",
                len(tup),
                name,
                " has" if len(tup) == 1 else "s have",
                no_colour=args.no_colour,
            )
            if args.show_unchecked:
                for item in tup:
                    log_unchecked(message=item, uri_scheme=args.link, no_colour=args.no_colour, name=name)

    if (
        summary.unchecked_equipment or summary.unchecked_reports or summary.unchecked_performance_checks
    ) and not args.show_unchecked:
        log_warn("include --show-unchecked to show the list of unchecked elements", no_colour=args.no_colour)

    if summary.num_issues == 0:
        green, yellow, reset = ("", "", "") if args.no_colour else (GREEN, YELLOW, RESET)
        msg = "Success, no issues found!"
        if summary.num_skipped == 0:
            print(f"{green}{msg}{reset}")  # noqa: T201
        else:
            print(f"{green}{msg}{reset} [{yellow}skipped: {summary.num_skipped}{reset}]")  # noqa: T201
    else:
        colour, reset = ("", "") if args.no_colour else (RED, RESET)
        n = summary.num_issues - summary.num_schema_issues
        issues = "issue" if summary.num_issues == 1 else "issues"
        print(  # noqa: T201
            f"{colour}Found {summary.num_issues} {issues} [{summary.num_schema_issues} schema, {n} additional]{reset}"
        )

    return summary.num_issues


def main(argv: Sequence[str] | None = None) -> NoReturn:
    """Main CLI entry point."""
    sys.exit(cli(argv))
