"""
Establish a connection to the equipment to send and receive messages.
"""
import logging

from msl.equipment.constants import Backend, MSLInterface
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.connection_demo import ConnectionDemo
from msl.equipment.connection_msl import ConnectionMSL
from msl.equipment.connection_pyvisa import ConnectionPyVISA

logger = logging.getLogger(__name__)


def connect(record, demo=False):
    """
    Factory function to establish a connection to the equipment.

    Args:
        record (:class:`.EquipmentRecord`): An equipment record (a row) from an
            Equipment-Register database.

        demo (bool): Whether to simulate a connection to the equipment by opening 
            a connection in demo mode. This allows you to call :meth:`~.Connection.write` 
            and :meth:`~.Connection.read` methods even if the equipment is not connected 
            to the computer. 

    Returns:
        A :class:`~msl.equipment.connection.Connection` object.

    Raises:
        TypeError: If the data type of ``record`` is not :class:`.EquipmentRecord`.
        ValueError: If any of the property values in
            :data:`record.connection.properties <msl.equipment.record_types.ConnectionRecord.properties>`
            are invalid.
    """
    def _connect(_record):
        """Processes a single EquipmentRecord object"""
        def _raise(name):
            raise ValueError('The connection {} has not been set for {}'.format(name, _record))

        if not isinstance(_record, EquipmentRecord):
            raise TypeError('The "record" argument must be a {}.{} object. Got {}'.format(
                EquipmentRecord.__module__, EquipmentRecord.__name__, type(_record)))

        if _record.connection is None:
            _raise('object')

        if demo:
            logger.demo('Connecting to {} in DEMO mode'.format(_record.connection))
            return ConnectionDemo(_record)
        else:
            if not _record.connection.address:
                _raise('address')
            if _record.connection.backend == Backend.UNKNOWN:
                _raise('backend')

            logger.debug('Connecting to {}'.format(_record.connection))

            if _record.connection.backend == Backend.MSL:
                if _record.connection.interface == MSLInterface.NONE:
                    _raise('interface')
                return ConnectionMSL(_record)

            if _record.connection.backend == Backend.PyVISA:
                return ConnectionPyVISA(_record)

    if isinstance(record, dict) and len(record) == 1:
        key = list(record.keys())[0]
        return _connect(record[key])
    elif isinstance(record, (list, tuple)) and len(record) == 1:
        return _connect(record[0])
    return _connect(record)
