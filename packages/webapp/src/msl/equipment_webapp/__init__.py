"""Web application to help manage information about equipment."""

from __future__ import annotations

import contextlib
from argparse import SUPPRESS, ArgumentParser
from typing import TYPE_CHECKING

from ._version import __version__
from .app import run
from .config import cfg

if TYPE_CHECKING:
    from collections.abc import Sequence


def configure_parser() -> ArgumentParser:
    """Create and configure the argument parser."""
    parser = ArgumentParser(
        prog="msl-equipment-webapp",
        description="Run the web application to help manage information about equipment.",
        add_help=False,
    )
    _ = parser.add_argument(
        "config",
        help="Path to a JSON configuration file (can use ~ as the user's home directory).",
    )
    _ = parser.add_argument(
        "-H",
        "--host",
        help=(
            "The network interface to use. Specifying in the command line takes "
            f"precedence if also defined in the configuration file (default {cfg.host})."
        ),
    )
    _ = (
        parser.add_argument(
            "-p",
            "--port",
            type=int,
            help=(
                "The port number to use. Specifying in the command line takes "
                f"precedence if also defined in the configuration file (default {cfg.port})."
            ),
        ),
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


def main(argv: Sequence[str] | None = None) -> None:
    """Main CLI entry point for the web application."""
    parser = configure_parser()
    ns = parser.parse_args(argv)
    cfg.load(ns.config, host=ns.host, port=ns.port)
    with contextlib.suppress(KeyboardInterrupt):
        run(host=cfg.host, port=cfg.port)
