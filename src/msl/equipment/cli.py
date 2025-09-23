"""Command line interface."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass
from enum import IntEnum
from threading import Thread
from typing import TYPE_CHECKING

from serial.tools.list_ports import comports

from .dns_service_discovery import find_lxi
from .interfaces.gpib import find_listeners
from .interfaces.prologix import find_prologix
from .interfaces.vxi11 import find_vxi11
from .utils import ipv4_addresses, logger

if TYPE_CHECKING:
    from collections.abc import ValuesView
    from typing import ClassVar


class _DeviceType(IntEnum):
    ASRL = 0
    GPIB = 1
    PROLOGIX = 2
    LXI = 3
    VXI11 = 4


@dataclass
class _Device:
    type: _DeviceType
    addresses: list[str]
    description: str = ""
    webserver: str = ""


class _PrologixThread(Thread):
    devices: ClassVar[dict[str, _Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Allows for capturing the return value from the target function."""

        def function() -> None:
            _PrologixThread.devices = {
                k: _Device(type=_DeviceType.PROLOGIX, addresses=v.addresses, description=v.description)
                for k, v in find_prologix(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


class _LXIThread(Thread):
    devices: ClassVar[dict[str, _Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Allows for capturing the return value from the target function."""

        def function() -> None:
            _LXIThread.devices = {
                k: _Device(
                    type=_DeviceType.LXI, addresses=v.addresses, description=v.description, webserver=v.webserver
                )
                for k, v in find_lxi(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


class _VXI11Thread(Thread):
    devices: ClassVar[dict[str, _Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Allows for capturing the return value from the target function."""

        def function() -> None:
            _VXI11Thread.devices = {
                k: _Device(
                    type=_DeviceType.VXI11, addresses=v.addresses, description=v.description, webserver=v.webserver
                )
                for k, v in find_vxi11(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


def find_equipment(  # noqa: C901
    *, ip: list[str] | None = None, timeout: float = 2, gpib_library: str = "", include_sad: bool = True
) -> ValuesView[_Device]:
    """Returns information about equipment that are available.

    Args:
        ip: The IP address(es) on the local computer to use to search for network devices.
            If not specified, uses all network interfaces.
        timeout: The maximum number of seconds to wait for a reply from a network device.
        gpib_library: The path to a GPIB library file. The default file that is used is
            platform dependent. If a GPIB library cannot be found, GPIB devices will not
            be searched for.
        include_sad: Whether to scan all secondary GPIB addresses.

    Returns:
        The information about the devices that were found.
    """
    logger.debug("start finding devices")
    num_found = 0
    devices: dict[str, _Device] = {}

    ips = ip if ip is not None else list(ipv4_addresses())
    threads: list[_PrologixThread | _LXIThread | _VXI11Thread] = [
        _PrologixThread(ips, timeout),
        _LXIThread(ips, timeout),
        _VXI11Thread(ips, timeout),
    ]
    for thread in threads:
        thread.start()

    logger.debug("find ASRL ports")
    for info in sorted(comports()):
        num_found += 1
        addresses: list[str] = []
        if info.device.startswith("COM"):
            addresses.append(info.device)
        elif info.device.startswith("/dev"):
            addresses.append(f"ASRL{info.device}")
        devices[info.device] = _Device(type=_DeviceType.ASRL, addresses=addresses, description=info.description)

    if gpib_library:
        os.environ["GPIB_LIBRARY"] = gpib_library

    gpib = find_listeners(include_sad=include_sad)
    if gpib:
        num_found += len(gpib)
        devices["GPIB"] = _Device(type=_DeviceType.GPIB, addresses=gpib)

    for thread in threads:
        thread.join()

    for thread in threads:
        for name, device in thread.devices.items():
            if name not in devices:
                num_found += 1
                devices[name] = device

    logger.debug("found %d devices", num_found)
    return devices.values()


def _print_stdout(found: ValuesView[_Device]) -> None:
    """Print a summary of all equipment that are available to connect to."""
    devices = sorted(found, key=lambda v: v.description)
    types = sorted({d.type for d in devices})
    for typ in types:
        print(f"{typ.name} Devices")  # noqa: T201
        for device in devices:
            if device.type != typ:
                continue
            if typ == _DeviceType.GPIB:
                print("  " + "\n  ".join(device.addresses))  # noqa: T201
            elif typ == _DeviceType.ASRL:
                print(f"  {device.addresses[0]} [{device.description}]")  # noqa: T201
            elif typ in (_DeviceType.PROLOGIX, _DeviceType.LXI, _DeviceType.VXI11):
                webserver = f" [webserver: {device.webserver}]" if device.webserver else ""
                print(f"  {device.description}{webserver}")  # noqa: T201
                if device.addresses:
                    print("    " + "\n    ".join(sorted(device.addresses)))  # noqa: T201


def cli() -> None:
    """Console script entry point to find equipment."""
    parser = argparse.ArgumentParser(
        add_help=False,
        description="Find equipment that can be connected to.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    _ = parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
        default=argparse.SUPPRESS,
    )
    _ = parser.add_argument(
        "--ip",
        nargs="*",
        help=(
            "The IP address(es) on the local computer to search for network\n"
            "devices. If not specified, uses all network interfaces."
        ),
    )
    _ = parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=2,
        help=("Maximum number of seconds to wait for a reply from a network\ndevice. Default is 2 seconds."),
    )
    _ = parser.add_argument(
        "-g",
        "--gpib-library",
        default="",
        help=(
            "The path to a GPIB library file. The default file that is used\n"
            "is platform dependent. If a GPIB library cannot be found, GPIB\n"
            "devices will not be searched for."
        ),
    )
    _ = parser.add_argument("--debug", action="store_true", default=False, help="Whether to show DEBUG log messages.")
    _ = parser.add_argument(
        "--ignore-sad", action="store_true", default=False, help="Do not scan for secondary GPIB addresses."
    )
    _ = parser.add_argument("--json", action="store_true", default=False, help="Print the results as a JSON string.")

    parsed = parser.parse_args(sys.argv[1:])

    if parsed.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s %(message)s",
            datefmt="%H:%M:%S",
        )

    equipment = find_equipment(
        ip=parsed.ip,
        timeout=parsed.timeout,
        gpib_library=parsed.gpib_library,
        include_sad=not parsed.ignore_sad,
    )

    if parsed.json:
        print(  # noqa: T201
            json.dumps(
                [
                    {
                        "type": e.type.name,
                        "addresses": e.addresses,
                        "description": e.description,
                        "webserver": e.webserver,
                    }
                    for e in equipment
                ],
                indent=2,
            )
        )
    else:
        _print_stdout(equipment)
