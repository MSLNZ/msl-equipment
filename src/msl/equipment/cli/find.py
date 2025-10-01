"""Command line interface."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import IntEnum
from threading import Thread
from typing import TYPE_CHECKING

from serial.tools.list_ports import comports

from msl.equipment.dns_service_discovery import find_lxi
from msl.equipment.interfaces.gpib import find_listeners
from msl.equipment.interfaces.prologix import find_prologix
from msl.equipment.interfaces.vxi11 import find_vxi11
from msl.equipment.utils import ipv4_addresses, logger

if TYPE_CHECKING:
    from argparse import Namespace
    from typing import ClassVar


class DeviceType(IntEnum):
    """Type of device."""

    ASRL = 0
    GPIB = 1
    PROLOGIX = 2
    LXI = 3
    VXI11 = 4


@dataclass
class Device:
    """Information about a device that can be interfaced with."""

    type: DeviceType
    addresses: list[str]
    description: str = ""
    webserver: str = ""


class PrologixThread(Thread):
    """Scan for Prologix GPIB-Ethernet Controllers."""

    devices: ClassVar[dict[str, Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Scan for Prologix GPIB-Ethernet Controllers."""

        def function() -> None:
            PrologixThread.devices = {
                k: Device(type=DeviceType.PROLOGIX, addresses=v.addresses, description=v.description)
                for k, v in find_prologix(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


class LXIThread(Thread):
    """Scan for LXI devices."""

    devices: ClassVar[dict[str, Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Scan for LXI devices."""

        def function() -> None:
            LXIThread.devices = {
                k: Device(type=DeviceType.LXI, addresses=v.addresses, description=v.description, webserver=v.webserver)
                for k, v in find_lxi(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


class VXI11Thread(Thread):
    """Scan for VXI-11 devices."""

    devices: ClassVar[dict[str, Device]] = {}

    def __init__(self, ips: list[str], timeout: float) -> None:
        """Scan for VXI-11 devices."""

        def function() -> None:
            VXI11Thread.devices = {
                k: Device(
                    type=DeviceType.VXI11, addresses=v.addresses, description=v.description, webserver=v.webserver
                )
                for k, v in find_vxi11(ip=ips, timeout=timeout).items()
            }

        super().__init__(target=function)


def find_equipment(  # noqa: C901
    *, ip: list[str] | None = None, timeout: float = 2, gpib_library: str = "", include_sad: bool = False
) -> list[Device]:
    """Returns information about equipment that are available.

    Args:
        ip: The IP address(es) on the local computer to use to search for network devices.
            If not specified, uses all network interfaces.
        timeout: The maximum number of seconds to wait for a reply from a network device.
        gpib_library: The path to a GPIB library file. The default file that is used is
            platform dependent. If a GPIB library cannot be found, GPIB devices will not
            be searched for.
        include_sad: Whether to scan for secondary GPIB addresses.

    Returns:
        The information about the devices that were found.
    """
    logger.debug("Start searching for devices")
    num_found = 0
    devices: dict[str, Device] = {}

    ips = ip if ip is not None else list(ipv4_addresses())
    threads: list[PrologixThread | LXIThread | VXI11Thread] = [
        PrologixThread(ips, timeout),
        LXIThread(ips, timeout),
        VXI11Thread(ips, timeout),
    ]
    for thread in threads:
        thread.start()

    logger.debug("Searching for Serial ports")
    for info in sorted(comports()):
        num_found += 1
        addresses: list[str] = []
        if info.device.startswith("COM"):
            addresses.append(info.device)
        elif info.device.startswith("/dev"):
            addresses.append(f"ASRL{info.device}")
        devices[info.device] = Device(type=DeviceType.ASRL, addresses=addresses, description=info.description)

    if gpib_library:
        os.environ["GPIB_LIBRARY"] = gpib_library

    gpib = find_listeners(include_sad=include_sad)
    if gpib:
        num_found += len(gpib)
        devices["GPIB"] = Device(type=DeviceType.GPIB, addresses=gpib)

    logger.debug("Waiting approximately %g second(s) for network devices to respond...", timeout)
    for thread in threads:
        thread.join()

    for thread in threads:
        for name, device in thread.devices.items():
            if name not in devices:
                num_found += 1
                devices[name] = device

    logger.debug("Found %d devices", num_found)
    return list(devices.values())


def print_stdout(found: list[Device]) -> None:
    """Print a summary of all equipment that are available to connect to."""
    devices = sorted(found, key=lambda v: v.description)
    types = sorted({d.type for d in devices})
    for typ in types:
        kind = "Ports" if typ == DeviceType.ASRL else "Devices"
        print(f"{typ.name} {kind}")
        for device in devices:
            if device.type != typ:
                continue
            if typ == DeviceType.GPIB:
                print("  " + "\n  ".join(device.addresses))
            elif typ == DeviceType.ASRL:
                print(f"  {device.addresses[0]} [{device.description}]")
            else:
                webserver = f" [webserver: {device.webserver}]" if device.webserver else ""
                print(f"  {device.description}{webserver}")
                if device.addresses:
                    print("    " + "\n    ".join(sorted(device.addresses)))


def run(ns: Namespace) -> int:
    """Run the `find` command."""
    if ns.verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s.%(msecs)03d %(message)s",
            datefmt="%H:%M:%S",
        )
        logging.getLogger("asyncio").setLevel(logging.WARNING)

    equipment = find_equipment(
        ip=ns.ip,
        timeout=ns.timeout,
        gpib_library=ns.gpib_library,
        include_sad=ns.include_sad,
    )

    if ns.json:
        print(
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
        print_stdout(equipment)

    return 0
