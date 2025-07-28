"""
Base class for equipment that use the SDK provided by the manufacturer for the connection.
"""
from __future__ import annotations

from msl.loadlib import LoadLibrary

from .connection import Connection
from .constants import REGEX_SDK


class ConnectionSDK(Connection):

    def __init__(self, record, libtype, path=None):
        """Base class for equipment that use the SDK provided by the manufacturer
        for the connection.

        The :data:`~msl.equipment.record_types.ConnectionRecord.backend`
        value must be equal to :data:`~msl.equipment.constants.Backend.MSL`
        to use this class for the communication system. This is achieved by
        setting the value in the **Backend** field for a connection record
        in the :ref:`connections-database` to be ``MSL``.

        Do not instantiate this class directly. Use the
        :meth:`~.EquipmentRecord.connect` method to connect to the equipment.

        Parameters
        ----------
        record : :class:`.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        libtype : :class:`str`
            The library type. See :class:`~msl.loadlib.load_library.LoadLibrary`
            for more information.
        path : :class:`str`, optional
            The path to the SDK (if `record.connection.address` does not contain
            this information).

        Raises
        ------
        OSError
            If the shared library cannot be loaded.
        TypeError
            If either `record` or `libtype` is invalid.
        """
        super(ConnectionSDK, self).__init__(record)

        if path is None:
            info = ConnectionSDK.parse_address(record.connection.address)
            if info is None:
                self.raise_exception('Invalid address for {!r}'.format(self.__class__.__name__))
            path = info['path']

        self._lib = LoadLibrary(path, libtype)
        self._path = self._lib.path
        self._sdk = self._lib.lib
        self._assembly = self._lib.assembly
        self._gateway = self._lib.gateway

        self.log_debug('Connected to %s', record.connection)

    @property
    def assembly(self):
        """:attr:`~msl.loadlib.load_library.LoadLibrary.assembly`: The reference to the .NET assembly."""
        return self._assembly

    @property
    def gateway(self):
        """:attr:`~msl.loadlib.load_library.LoadLibrary.gateway`: The reference to the JAVA gateway."""
        return self._gateway

    @property
    def path(self):
        """:class:`str`: The path to the SDK file."""
        return self._path

    @property
    def sdk(self):
        """:attr:`~msl.loadlib.load_library.LoadLibrary.lib`: The reference to the SDK object."""
        return self._sdk

    def log_errcheck(self, result, func, arguments):
        """Convenience method for logging an :attr:`~ctypes._FuncPtr.errcheck`"""
        self.log_debug('%s.%s%s -> %s', self.__class__.__name__, func.__name__, arguments, result)
        return result

    @staticmethod
    def parse_address(address):
        """Get the file path from an address.

        Parameters
        ----------
        address : :class:`str`
            The address of a :class:`~msl.equipment.record_types.ConnectionRecord`.

        Returns
        -------
        :class:`dict` or :data:`None`
            The file path or :data:`None` if `address` is not valid for an SDK.
        """
        match = REGEX_SDK.match(address)
        if match:
            return match.groupdict()
