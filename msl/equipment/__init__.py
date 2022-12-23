"""
Manage and connect to equipment in the laboratory.
"""
import re
from collections import namedtuple

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
__copyright__ = '\xa9 2017 - 2022, ' + __author__
__version__ = '0.1.0.dev0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""


def list_resources(hosts=None, timeout=2):
    """Returns a dictionary of all devices that were found.

    Parameters
    ----------
    hosts : :class:`list` of :class:`str`, optional
        The IP address(es) on the computer to use to find network devices.
        If not specified, then find devices on all network interfaces.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for a reply from a network device.

    Returns
    -------
    :class:`dict`
        The information about the devices that were found.
    """
    from threading import Thread
    from msl.equipment.connection_prologix import find_prologix
    from msl.equipment.dns_service_discovery import find_lxi
    from msl.equipment.vxi11 import find_vxi11
    from serial.tools.list_ports import comports

    class NetworkThread(Thread):

        def __init__(self, target):
            """Allows for capturing the return value from the target function."""
            self.devices = {}

            def function():
                self.devices = target(hosts=hosts, timeout=timeout)

            super(NetworkThread, self).__init__(target=function)

    threads = [
        NetworkThread(target=find_lxi),
        NetworkThread(target=find_vxi11),
        NetworkThread(target=find_prologix),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    devices = {}
    for thread in threads:
        for ipv4, device in thread.devices.items():
            if ipv4 not in devices:
                devices[ipv4] = {}
                devices[ipv4]['addresses'] = set(device['addresses'])
                devices[ipv4]['description'] = device['description']
                devices[ipv4]['webserver'] = device['webserver']
            else:
                if not devices[ipv4]['description']:
                    devices[ipv4]['description'] = devices['description']
                for address in device['addresses']:
                    devices[ipv4]['addresses'].add(address)

    for port, desc, _ in sorted(comports()):
        addresses = {port}
        if port.startswith('COM'):
            match = re.search(r'(\d+)', port)
            if match:
                addresses.add('ASRL{}::INSTR'.format(match.group(1)))
        elif port.startswith('/dev/'):
            addresses.add('ASRL{}::INSTR'.format(port))

        devices[port] = {}
        devices[port]['addresses'] = addresses
        devices[port]['description'] = desc

    return devices.values()


def print_resources(hosts=None, timeout=2):
    """Print the information about the devices that were found.

    Parameters
    ----------
    hosts : :class:`list` of :class:`str`, optional
        The IP address(es) on the computer to use to find network devices.
        If not specified, then find devices on all network interfaces.
    timeout : :class:`float`, optional
        The maximum number of seconds to wait for a reply from a network device.
    """
    devices = list_resources(hosts=hosts, timeout=timeout)
    for item in sorted(devices, key=lambda v: v['description']):
        print(item['description'])
        if 'webserver' in item:
            print('  webserver -> ' + item['webserver'])
        print('  ' + '\n  '.join(sorted(item['addresses'])))
        print('')
