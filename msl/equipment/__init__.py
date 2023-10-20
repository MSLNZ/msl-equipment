"""
Manage and connect to equipment in the laboratory.
"""
from __future__ import annotations

import re
from collections import namedtuple
from typing import ValuesView

from msl.equipment import resources
from msl.equipment.config import Config
from msl.equipment.constants import Backend
from msl.equipment.exceptions import MSLConnectionError
from msl.equipment.exceptions import MSLTimeoutError
from msl.equipment.record_types import CalibrationRecord
from msl.equipment.record_types import ConnectionRecord
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.record_types import MaintenanceRecord
from msl.equipment.record_types import MeasurandRecord

__author__ = 'Measurement Standards Laboratory of New Zealand'
__copyright__ = '\xa9 2017 - 2023, ' + __author__
__version__ = '0.2.0.dev0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""


def list_resources(
        *,
        hosts: list[str] | None = None,
        timeout: float = 2,
        include_sad: bool = True,
        gpib_library: str = '') -> ValuesView:
    """Returns information about equipment that are available.

    :param hosts:
        The IP address(es) on the computer to use to find network devices.
        If not specified, then find devices on all network interfaces.

    :param timeout:
        The maximum number of seconds to wait for a reply from a network device.

    :param include_sad:
        Whether to scan all secondary GPIB addresses.

    :param gpib_library:
        The path to a GPIB library file. The default file that is loaded is
        platform dependent. If a library cannot be loaded, GPIB devices cannot
        be found.

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
                self.devices = target(hosts=hosts, timeout=timeout)

            super(NetworkThread, self).__init__(target=function)

    logger.debug('start finding devices')
    devices = {}

    threads = [
        NetworkThread(target=find_lxi),
        NetworkThread(target=find_vxi11),
        NetworkThread(target=find_prologix),
    ]
    for thread in threads:
        thread.start()

    num_found = 0

    logger.debug('find ASRL ports')
    for port, desc, _ in sorted(comports()):
        num_found += 1
        addresses = []
        if port.startswith('COM'):
            addresses.append(port)
        elif port.startswith('/dev/'):
            addresses.append(f'ASRL{port}')
        devices[port] = {
            'type': 'ASRL',
            'addresses': addresses,
            'description': desc
        }

    Config.GPIB_LIBRARY = gpib_library
    gpib = find_listeners(include_sad=include_sad)
    if gpib:
        num_found += len(gpib)
        devices['gpib'] = {
            'type': 'GPIB',
            'addresses': gpib,
            'description': ''
        }

    for thread in threads:
        thread.join()
    for thread in threads:
        for ipv4, device in thread.devices.items():
            description = device.get('description', 'Unknown device')
            if ipv4 not in devices:
                num_found += 1
                devices[ipv4] = {
                    'type': 'Network',
                    'addresses': set(device['addresses']),
                    'description': description,
                }
                if not description.startswith('Prologix'):
                    # Prologix ENET-GPIB does not have a webserver
                    devices[ipv4]['webserver'] = device['webserver']
            else:
                devices[ipv4]['description'] = description
                for address in device['addresses']:
                    devices[ipv4]['addresses'].add(address)

    logger.debug('found %d devices', num_found)
    return devices.values()


def print_resources(**kwargs) -> None:
    """Print a summary of all equipment that are available to connect to.

    All keyword arguments are passed to :func:`.list_resources`.
    """
    devices = sorted(list_resources(**kwargs), key=lambda v: v['description'])
    types = sorted(set(d['type'] for d in devices))
    for typ in types:
        print(f'{typ} Devices')
        for device in devices:
            if device['type'] != typ:
                continue
            if typ == 'GPIB':
                print('  ' + '\n  '.join(device['addresses']))
            elif typ == 'ASRL':
                print(f"  {device['addresses'][0]} [{device['description']}]")
            elif typ == 'Network':
                print(f"  {device['description']}")
                print(f"    webserver {device['webserver']}")
                if device['addresses']:
                    print(f'    ' + '\n    '.join(sorted(device['addresses'])))
