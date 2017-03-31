"""
Manage and connect to equipment in the laboratory.
"""
from collections import namedtuple

from msl.equipment.factory import connect
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord
from msl.equipment.connection_pyvisa import PYVISA_RESOURCE_MANAGER

__author__ = 'Joseph Borbely'
__copyright__ = '\xa9 2017, ' + __author__
__version__ = '0.1.0'

version_info = namedtuple('version_info', 'major minor micro')(*map(int, __version__.split('.')))
""":py:func:`~collections.namedtuple`: Contains the version information as a (major, minor, micro) tuple."""
