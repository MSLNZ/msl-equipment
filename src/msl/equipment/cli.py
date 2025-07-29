"""Command line interface."""

from __future__ import annotations


def find_equipment(
    *, ip: list[str] | None = None, timeout: float = 2, gpib_library: str = "", include_sad: bool = True
) -> ValuesView:
    """Returns information about equipment that are available.

    :param ip:
        The IP address(es) on the local computer to use to search for network
        devices. If not specified, uses all network interfaces.

    :param timeout:
        The maximum number of seconds to wait for a reply from a network device.

    :param gpib_library:
        The path to a GPIB library file. The default file that is used is
        platform dependent. If a GPIB library cannot be found, GPIB devices
        will not be searched for.

    :param include_sad:
        Whether to scan all secondary GPIB addresses.

    :return: The information about the devices that were found.
    """
    from threading import Thread
    from msl.equipment.connection_gpib import find_listeners
    from msl.equipment.connection_prologix import find_prologix
    from msl.equipment.dns_service_discovery import find_lxi
    from msl.equipment.utils import logger
    from msl.equipment.vxi11 import find_vxi11
    from serial.tools.list_ports import comports

    class NetworkThread(Thread):
        def __init__(self, target):
            """Allows for capturing the return value from the target function."""
            self.devices = {}

            def function():
                self.devices = target(ip=ip, timeout=timeout)

            super(NetworkThread, self).__init__(target=function)

    logger.debug("start finding devices")
    devices = {}

    threads = [
        NetworkThread(target=find_lxi),
        NetworkThread(target=find_vxi11),
        NetworkThread(target=find_prologix),
    ]
    for thread in threads:
        thread.start()

    num_found = 0

    logger.debug("find ASRL ports")
    for port, desc, _ in sorted(comports()):
        num_found += 1
        addresses = []
        if port.startswith("COM"):
            addresses.append(port)
        elif port.startswith("/dev/"):
            addresses.append(f"ASRL{port}")
        devices[port] = {"type": "Serial", "addresses": addresses, "description": desc}

    Config.GPIB_LIBRARY = gpib_library
    gpib = find_listeners(include_sad=include_sad)
    if gpib:
        num_found += len(gpib)
        devices["gpib"] = {"type": "GPIB", "addresses": gpib, "description": ""}

    for thread in threads:
        thread.join()
    for thread in threads:
        for ipv4, device in thread.devices.items():
            description = device.get("description", "Unknown device")
            if ipv4 not in devices:
                num_found += 1
                devices[ipv4] = {
                    "type": "Network",
                    "addresses": device["addresses"],
                    "description": description,
                }
                if not description.startswith("Prologix"):
                    # Prologix ENET-GPIB does not have a webserver
                    devices[ipv4]["webserver"] = device["webserver"]
            else:
                if devices[ipv4]["description"] == "Unknown device" and description != "Unknown device":
                    devices[ipv4]["description"] = description
                for address in device["addresses"]:
                    if address not in devices[ipv4]["addresses"]:
                        devices[ipv4]["addresses"].append(address)

    logger.debug("found %d devices", num_found)
    return devices.values()


def _print_stdout(equipment: ValuesView) -> None:
    """Print a summary of all equipment that are available to connect to."""
    devices = sorted(equipment, key=lambda v: v["description"])
    types = sorted(set(d["type"] for d in devices))
    for typ in types:
        print(f"{typ} Devices")
        for device in devices:
            if device["type"] != typ:
                continue
            if typ == "GPIB":
                print("  " + "\n  ".join(device["addresses"]))
            elif typ == "Serial":
                print(f"  {device['addresses'][0]} [{device['description']}]")
            elif typ == "Network":
                print(f"  {device['description']}")
                if "webserver" in device:
                    print(f"    webserver {device['webserver']}")
                if device["addresses"]:
                    print(f"    " + "\n    ".join(sorted(device["addresses"])))


def _find_cli() -> None:
    """Console script entry point to find equipment."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(
        add_help=False,
        description="Find equipment that can be connected to.",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit.",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--ip",
        nargs="*",
        help="The IP address(es) on the local computer to search for network\n"
        "devices. If not specified, uses all network interfaces.",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=2,
        help="Maximum number of seconds to wait for a reply from a network\ndevice. Default is 2 seconds.",
    )
    parser.add_argument(
        "-g",
        "--gpib-library",
        default="",
        help="The path to a GPIB library file. The default file that is used\n"
        "is platform dependent. If a GPIB library cannot be found, GPIB\n"
        "devices will not be searched for.",
    )
    parser.add_argument("--debug", action="store_true", default=False, help="Whether to show DEBUG log messages.")
    parser.add_argument(
        "--ignore-sad", action="store_true", default=False, help="Do not scan for secondary GPIB addresses."
    )
    parser.add_argument("--json", action="store_true", default=False, help="Print the results as a JSON string.")

    parsed = parser.parse_args(sys.argv[1:])

    if parsed.debug:
        import logging

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
        print(json.dumps(list(equipment), indent=2))
    else:
        _print_stdout(equipment)
