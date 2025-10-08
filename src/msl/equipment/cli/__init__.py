"""Main entry point to the CLI argument parser."""

from __future__ import annotations

import errno
import subprocess
import sys
from argparse import SUPPRESS, ArgumentParser, RawTextHelpFormatter
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import NoReturn


def add_help(parser: ArgumentParser) -> None:
    """Add a `--help` option to an argument parser."""
    _ = parser.add_argument("-h", "--help", action="help", help="Show this help message and exit.", default=SUPPRESS)


def configure_find(parser: ArgumentParser) -> None:
    """Configure the `find` command."""
    parser.usage = "msl-equipment find [-i [IP ...]] [-t TIMEOUT] [-g GPIB_LIBRARY] [-v] [-s] [-j] [-h]"
    # fmt: off
    _ = parser.add_argument(
        "-i",
        "--ip",
        nargs="*",
        help=(
            "IP address(es) of the network adaptor(s) on the local computer\n"
            "to use to search for network devices (e.g., VXI, LXI devices).\n"
            "If not specified, all network adaptors are used."
        ),
    )
    _ = parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=2,
        help=(
            "Number of seconds to wait for a reply from a network device.\n"
            "Default is 2 seconds."
        ),
    )
    _ = parser.add_argument(
        "-g",
        "--gpib-library",
        default="",
        help=(
            "The path to a GPIB library file to use instead of the default\n"
            "GPIB library file. If a GPIB library file cannot be found, \n"
            "GPIB devices will not be searched for. You may also define\n"
            "the library file path as a GPIB_LIBRARY environment variable."
        ),
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Show more information during the search process."
    )
    _ = parser.add_argument(
        "-s",
        "--include-sad",
        action="store_true",
        default=False,
        help="Include secondary GPIB addresses."
    )
    _ = parser.add_argument(
        "-j",
        "--json",
        action="store_true",
        default=False,
        help="Display the results as a JSON string."
    )
    add_help(parser)
    # fmt: on


def configure_parser() -> tuple[ArgumentParser, ArgumentParser]:
    """Configure the main parser."""
    parser = ArgumentParser(
        prog="msl-equipment",
        add_help=False,  # add later so that capitalization and periods are consistent in the help
        description="Manage information about equipment and find equipment that support computer control.",
        formatter_class=RawTextHelpFormatter,
        usage="%(prog)s [OPTIONS] COMMAND [ARGS]...",
    )

    subparser = parser.add_subparsers(dest="command", title=SUPPRESS, metavar="\b\bCommands:")

    find = subparser.add_parser(
        "find",
        help="Find equipment that can be computer controlled.",
        description="Find equipment that can be computer controlled.",
        add_help=False,
        formatter_class=RawTextHelpFormatter,
    )
    configure_find(find)

    for _parser in (parser, find):
        _parser._optionals.title = "Options"  # noqa: SLF001

    _help = subparser.add_parser("help", help="Show help for a command and exit.")
    _ = _help.add_argument("on", nargs="?", choices=("find", "validate", "webapp"))

    _ = subparser.add_parser("validate", help="Validate equipment registers and connection files.", add_help=False)
    _ = subparser.add_parser("webapp", help="Start the web application.", add_help=False)

    add_help(parser)
    return parser, find


def run_external(name: str, *args: str) -> int:
    """Run an `msl-equipment-NAME` executable with `args`."""
    try:
        out = subprocess.run((f"msl-equipment-{name}", *args), check=False)  # noqa: S603
    except FileNotFoundError as e:
        msg = (
            f"Please install the `msl-equipment-{name}` package.\n\n"
            f"If you have installed the package, add the directory to where the\n"
            f"msl-equipment-{name} executable is located to the PATH environment variable."
        )
        _ = sys.stdout.write(msg)
        return e.errno or errno.ENOENT
    else:
        return out.returncode


def cli(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    if not argv:
        argv = ["--help"]

    main, find = configure_parser()
    (args, sub_args) = main.parse_known_args(argv)

    if args.command == "help":
        if args.on is None:
            main.print_help()
            return 0

        if args.on == "find":
            find.print_help()
            return 0

        return run_external(args.on, *("--help",))

    if args.command == "find":
        from .find import run  # noqa: PLC0415

        return run(args)

    return run_external(args.command, *sub_args)


def main(argv: Sequence[str] | None = None) -> NoReturn:
    """Main CLI entry point."""
    sys.exit(cli(argv or sys.argv[1:]))
