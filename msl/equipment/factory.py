"""
Establish a connection to the equipment to send and receive messages.
"""
import logging

from msl.equipment.config import Config
from msl.equipment.constants import Backend, MSLInterface
from msl.equipment.exceptions import ResourceClassNotFound
from msl.equipment.record_types import EquipmentRecord
from msl.equipment.resources import find_resource_class
from msl.equipment.resources.dmm import dmm_factory
from msl.equipment.connection_demo import ConnectionDemo
from msl.equipment.connection_pyvisa import ConnectionPyVISA
from msl.equipment.connection_serial import ConnectionSerial
from msl.equipment.connection_socket import ConnectionSocket
from msl.equipment.connection_nidaq import ConnectionNIDAQ

logger = logging.getLogger(__name__)


def connect(record, demo=None):
    """Factory function to establish a connection to the equipment.

    This function should not be called directly. Use the
    :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
    to connect to the equipment after a :class:`~.config.Config` object has
    been created.

    Parameters
    ----------
    record : :class:`~.record_types.EquipmentRecord`
        A record from an :ref:`equipment_database`.

    demo : :obj:`bool` or :obj:`None`
        Whether to simulate a connection to the equipment by opening
        a connection in demo mode. This allows you run your code if the 
        equipment is not physically connected to a computer.
        
        If :data:`None` then the `demo` value is determined from the
        :obj:`~.config.Config.DEMO_MODE` variable.

    Returns
    -------
    A :class:`~.connection.Connection` subclass.

    Raises
    ------
    ValueError
        If any of the property values in
        :obj:`record.connection.properties <.record_types.ConnectionRecord.properties>`
        are invalid.
    TypeError
        If the `record` is not an :class:`~.record_types.EquipmentRecord`.
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
        if not conn.address and conn.backend != Backend.NIDAQ:
            _raise('address')
        if conn.backend == Backend.UNKNOWN:
            _raise('backend')

        cls = None
        if conn.backend == Backend.MSL:
            if conn.interface == MSLInterface.NONE:
                _raise('interface')
            cls = find_resource_class(conn)
            if cls is None:
                if conn.interface == MSLInterface.SDK:
                    raise ResourceClassNotFound(record)
                elif conn.interface == MSLInterface.SERIAL:
                    cls = ConnectionSerial
                elif conn.interface == MSLInterface.SOCKET:
                    cls = ConnectionSocket
                else:
                    raise NotImplementedError('The {} interface has not be written yet'.format(conn.interface.name))
        elif conn.backend == Backend.PyVISA:
            if demo:
                cls = ConnectionPyVISA.resource_class(conn)
            else:
                cls = ConnectionPyVISA
        elif conn.backend == Backend.NIDAQ:
            if demo:
                raise NotImplementedError('NIDAQ cannot be run in demo mode...')
            else:
                cls = ConnectionNIDAQ

        assert cls is not None, 'The Connection class is None'

        if _record.category == 'DMM':
           cls = dmm_factory(conn, cls)

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
