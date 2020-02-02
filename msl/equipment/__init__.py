"""
Manage and connect to equipment in the laboratory.
"""
import re
from collections import namedtuple

from msl.equipment.config import Config
from msl.equipment.record_types import (
    EquipmentRecord,
    ConnectionRecord,
    CalibrationRecord,
    MaintenanceRecord,
    MeasurandRecord,
)
from msl.equipment.constants import Backend
from msl.equipment.exceptions import (
    MSLConnectionError,
    MSLTimeoutError,
)
from msl.equipment import resources

__author__ = 'Measurement Standards Laboratory of New Zealand'
__copyright__ = '\xa9 2017 - 2020, ' + __author__
__version__ = '0.1.0.dev0'

_v = re.search(r'(\d+)\.(\d+)\.(\d+)[.-]?(.*)', __version__).groups()

version_info = namedtuple('version_info', 'major minor micro releaselevel')(int(_v[0]), int(_v[1]), int(_v[2]), _v[3])
""":obj:`~collections.namedtuple`: Contains the version information as a (major, minor, micro, releaselevel) tuple."""
