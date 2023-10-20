"""
Establish a connection to the equipment.
"""
from __future__ import annotations

from .config import Config
from .connection_demo import ConnectionDemo
from .connection_gpib import ConnectionGPIB
from .connection_nidaq import ConnectionNIDAQ
from .connection_prologix import ConnectionPrologix
from .connection_pyvisa import ConnectionPyVISA
from .connection_sdk import ConnectionSDK
from .connection_serial import ConnectionSerial
from .connection_socket import ConnectionSocket
from .connection_tcpip_hislip import ConnectionTCPIPHiSLIP
from .connection_tcpip_vxi11 import ConnectionTCPIPVXI11
from .connection_zeromq import ConnectionZeroMQ
from .constants import Backend
from .constants import Interface
from .exceptions import ResourceClassNotFound
from .resources import find_resource_class
from .utils import logger

_interface_map = {
    Interface.SERIAL: ConnectionSerial,
    Interface.SOCKET: ConnectionSocket,
    Interface.PROLOGIX: ConnectionPrologix,
    Interface.TCPIP_VXI11: ConnectionTCPIPVXI11,
    Interface.TCPIP_HISLIP: ConnectionTCPIPHiSLIP,
    Interface.ZMQ: ConnectionZeroMQ,
    Interface.GPIB: ConnectionGPIB,
}


def connect(record, demo=None):
    """Factory function to establish a connection to the equipment.

    Parameters
    ----------
    record : :class:`~.record_types.EquipmentRecord`
        A record from an :ref:`equipment-database`.

    demo : :class:`bool`, optional
        Whether to simulate a connection to the equipment by opening
        a connection in demo mode. This allows you to test your code
        if the equipment is not physically connected to a computer.

        If :data:`None` then the `demo` value is determined from the
        :attr:`~.config.Config.DEMO_MODE` attribute.

    Returns
    -------
    A :class:`~.connection.Connection` subclass.
    """
    def _connect(_record):
        """Processes a single EquipmentRecord object"""
        def _raise(name):
            raise ValueError(f'The connection {name} has not been set for {_record}')

        conn = _record.connection

        if conn is None:
            _raise('object')
        if not conn.address and conn.backend != Backend.NIDAQ:
            _raise('address')
        if conn.backend == Backend.UNKNOWN:
            _raise('backend')

        cls = None
        if conn.backend == Backend.MSL:
            if conn.interface == Interface.NONE:
                _raise('interface')
            cls = find_resource_class(conn)
            if cls is None:
                if conn.interface == Interface.SDK:
                    raise ResourceClassNotFound(record)
                cls = _interface_map.get(conn.interface, None)
                if cls is None:
                    raise NotImplementedError(f'The {conn.interface.name!r} interface '
                                              f'has not be implemented yet')
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

        logger.debug('Connecting to %s using %s', conn, conn.backend.name)
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


def find_interface(address: str) -> Interface:
    """Find the interface for `address`.

    :param address:
        The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.
    """
    if ConnectionSDK.parse_address(address):
        return Interface.SDK

    # this check must come before the SERIAL and SOCKET checks
    if ConnectionPrologix.parse_address(address):
        return Interface.PROLOGIX

    if ConnectionSerial.parse_address(address):
        return Interface.SERIAL

    if ConnectionSocket.parse_address(address):
        return Interface.SOCKET

    if ConnectionTCPIPVXI11.parse_address(address):
        return Interface.TCPIP_VXI11

    if ConnectionTCPIPHiSLIP.parse_address(address):
        return Interface.TCPIP_HISLIP

    if ConnectionGPIB.parse_address(address):
        return Interface.GPIB

    if ConnectionZeroMQ.parse_address(address):
        return Interface.ZMQ

    raise ValueError(f'Cannot determine the Interface from address {address!r}')
