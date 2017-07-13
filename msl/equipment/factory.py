"""
Establish a connection to the equipment to send and receive messages.
"""
import logging

from .config import Config
from .constants import Backend, MSLInterface
from .record_types import EquipmentRecord
from .connection_demo import ConnectionDemo
from .connection_pyvisa import ConnectionPyVISA
from . import resources
from . import connection_msl

logger = logging.getLogger(__name__)


def connect(record, demo=None):
    """Factory function to establish a connection to the equipment.

    Parameters
    ----------
    record : :class:`~.record_types.EquipmentRecord`
        An equipment record from an **Equipment-Register** 
        :class:`~.database.Database`.

    demo : :obj:`bool` or :obj:`None`
        Whether to simulate a connection to the equipment by opening
        a connection in demo mode. This allows you run your code if the 
        equipment is not physically connected to the computer.
        
        If :data:`None` then the `demo` value is read from a configuration
        variable. See :obj:`msl.equipment.config.Config` for more details.

    Returns
    -------
    :class:`~msl.equipment.connection.Connection` 
        A :class:`~msl.equipment.connection.Connection`-type object.

    Raises
    ------
    ValueError
        If any of the property values in
        :obj:`record.connection.properties <.record_types.ConnectionRecord.properties>`
        are invalid.
    """
    def _connect(_record):
        """Processes a single EquipmentRecord object"""
        def _raise(name):
            raise ValueError('The connection {} has not been set for {}'.format(name, _record))

        if not isinstance(_record, EquipmentRecord):
            raise TypeError('The "record" argument must be a {}.{} object. Got {}'.format(
                EquipmentRecord.__module__, EquipmentRecord.__name__, type(_record)))

        conn = _record.connection

        if conn is None:
            _raise('object')
        if not conn.address:
            _raise('address')
        if conn.backend == Backend.UNKNOWN:
            _raise('backend')

        cls = None
        if conn.backend == Backend.MSL:
            if conn.interface == MSLInterface.NONE:
                _raise('interface')
            elif conn.interface == MSLInterface.SDK:
                cls = resources.find_sdk_class(conn)
            elif conn.interface == MSLInterface.ASRL:
                cls = resources.find_serial_class(conn)
                if cls is None:
                    cls = connection_msl.ConnectionSerial
            else:
                cls = connection_msl.ConnectionMessageBased
        elif conn.backend == Backend.PyVISA:
            if demo:
                cls = ConnectionPyVISA.resource_pyclass(conn)
            else:
                cls = ConnectionPyVISA

        assert cls is not None, 'The Connection class is None'

        logger.debug('Connecting to {} using {}'.format(conn, conn.backend.name))
        if demo:
            return ConnectionDemo(_record, cls)
        else:
            return cls(_record)

    if demo is None:
        demo = Config.DEMO_MODE

    if isinstance(record, dict) and len(record) == 1:
        key = list(record.keys())[0]
        return _connect(record[key])
    elif isinstance(record, (list, tuple)) and len(record) == 1:
        return _connect(record[0])
    return _connect(record)
