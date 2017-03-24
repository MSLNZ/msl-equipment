import logging
from collections import namedtuple

from msl.equipment.database import Database
from msl.equipment.constants import Backend, MSLInterface
from msl.equipment.record_types import EquipmentRecord, ConnectionRecord
from msl.equipment.connection_demo import ConnectionDemo
from msl.equipment.connection_msl import ConnectionMSL
from msl.equipment.connection_pyvisa import PYVISA_RESOURCE_MANAGER, ConnectionPyVISA

__author__ = 'Joseph Borbely'
__copyright__ = '\xa9 2017, ' + __author__
__version__ = '0.1.0'

version_info = namedtuple('version_info', 'major minor micro')(*map(int, __version__.split('.')))
""":py:func:`~collections.namedtuple`: Contains the version information as a (major, minor, micro) tuple."""

logger = logging.getLogger(__name__)


def load(xml):
    """
    Load equipment and connection records (rows) from the databases specified in the configuration file.

    Args:
        xml (str): The path to a XML configuration file.

    Returns:
        :class:`Database`: The equipment and connection records in the database.
    """
    logger.debug('Loading databases from ' + xml)
    return Database(xml)


def connect(record, demo=False):
    """
    Factory method to establish a connection to the equipment.

    Args:
        record (:class:`.EquipmentRecord`): An equipment record (a row) from an equipment-register database.
            *NOTE: Can be a* :py:class:`list` *or* :py:class:`dict` *of equipment records and then the
            returned object will be a* :py:class:`dict` *of* :class:`~msl.equipment.connection.Connection`\'s.

        demo (bool): Whether to create a connection in demo mode.

    Returns:
        Either a :class:`~msl.equipment.connection.Connection` object if a single ``record`` were passed in
        or a :py:class:`dict` of :class:`~msl.equipment.connection.Connection`\'s if multiple ``record``s were
        passed in.

    Raises:
        TypeError: If data type of ``record`` is invalid.
        ValueError: If any of the properties in ``record.connection`` are invalid.
    """
    def _connect(_record):
        """Processes a single EquipmentRecord object"""
        def _raise(name):
            raise ValueError('The connection {} has not been set for {}'.format(name, _record))

        if not isinstance(_record, EquipmentRecord):
            raise TypeError('The "record" argument must be a {}.{} object. Got {}'.format(
                EquipmentRecord.__module__, EquipmentRecord.__name__, type(_record)))

        if demo:
            logger.debug('Connecting in DEMO mode to {}'.format(_record))
            return ConnectionDemo(_record)
        else:
            if _record.connection is None:
                _raise('object')
            if not _record.connection.address:
                _raise('address')
            if _record.connection.backend == Backend.UNKNOWN:
                _raise('backend')

            logger.debug('Connecting to {}'.format(_record))

            if _record.connection.backend == Backend.MSL:
                if _record.connection.interface == MSLInterface.NONE:
                    _raise('interface')
                return ConnectionMSL(_record)

            if _record.connection.backend == Backend.PyVISA:
                return ConnectionPyVISA(_record)

    if isinstance(record, dict):
        return {key: _connect(value) for key, value in record.items()}
    elif isinstance(record, (list, tuple)):
        if len(record) == 1:
            return _connect(record[0])
        else:
            conn = {}
            for r in record:
                key = r.alias if r.alias else 'conn{}'.format(len(conn) + 1)
                conn[key] = _connect(r)
            return conn
    return _connect(record)
