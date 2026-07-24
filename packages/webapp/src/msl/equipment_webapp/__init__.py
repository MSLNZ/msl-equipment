"""Web application to manage information about equipment."""

from __future__ import annotations

import contextlib
import json
import logging
from argparse import SUPPRESS, ArgumentParser
from pathlib import Path
from typing import TYPE_CHECKING

from . import config
from ._version import __version__
from .app import run

if TYPE_CHECKING:
    from collections.abc import Sequence


def configure_parser() -> ArgumentParser:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        prog="msl-equipment-webapp",
        description="Run the web application to manage information about equipment.",
        add_help=False,
    )
    _ = parser.add_argument(
        "config",
        help="Path to a JSON configuration file (can use ~ as the user's home directory).",
    )
    _ = parser.add_argument(
        "-H",
        "--host",
        default="0.0.0.0",  # noqa: S104
        help="The network interface to run the web app on. If unspecified, listen on all network interfaces.",
    )
    _ = parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=17025,
        help="The port number to use for the web app. Default is 17025.",
    )
    _ = parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Show more information.",
    )
    _ = parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="Show less information (option is additive and can be used up to 3 times).",
    )
    _ = parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=__version__,
        help="Show version and exit.",
    )
    _ = parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
        default=SUPPRESS,
    )
    return parser


def get_logging_level(*, quiet: int, verbose: int) -> int:
    """Get the logging level from command-line flags.

    Args:
        quiet: The number of times the `--quiet` flag is specified.
        verbose: The number of times the `--verbose` flag is specified.

    Returns:
        The logging level.
    """
    level = 10 * (quiet - verbose) + logging.INFO
    return max(10, min(level, 50))


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point."""
    parser = configure_parser()
    ns = parser.parse_args(argv)

    with Path(ns.config).expanduser().open("rb") as fp:
        config.teams.extend(config.Team(team=k, url=Path(v)) for k, v in json.load(fp).items())

    level = get_logging_level(quiet=ns.quiet, verbose=ns.verbose)
    with contextlib.suppress(KeyboardInterrupt):
        run(host=ns.host, port=ns.port, log_level=level)
