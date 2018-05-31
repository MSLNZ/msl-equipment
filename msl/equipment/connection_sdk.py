"""
Base class for equipment that use the SDK provided by the manufacturer for the connection.
"""
from msl.loadlib import LoadLibrary

from msl.equipment.connection import Connection


class ConnectionSDK(Connection):

    def __init__(self, record, libtype):
        """Base class for equipment that use the SDK provided by the manufacturer
        for the connection.

        The :data:`record.connection.backend <msl.equipment.record_types.ConnectionRecord.backend>`
        value must be equal to :data:`Backend.MSL <msl.equipment.constants.Backend.MSL>`
        to use this class for the communication system. This is achieved by setting the
        value in the **Backend** field for a connection record in the :ref:`connection_database`
        to be ``MSL``.

        Do not instantiate this class directly. Use the
        :obj:`record.connect() <.record_types.EquipmentRecord.connect>` method
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.

        libtype : :class:`str`
            The library type to use for the calling convention.
            See :class:`~msl.loadlib.load_library.LoadLibrary` for more information.

        Raises
        ------
        IOError
            If the shared library cannot be loaded.
        TypeError
            If either `record` or `libtype` is invalid.
        """
        Connection.__init__(self, record)
        lib_path = str(record.connection.address.split('::')[-1])  # the last item must be the path
        self._lib = LoadLibrary(lib_path, libtype)
        self.log_debug('Connected to {}'.format(self.equipment_record.connection))

    @property
    def sdk_path(self):
        """:class:`str`: The path to the shared library file."""
        return self._lib.path

    @property
    def sdk(self):
        """:obj:`~msl.loadlib.load_library.LoadLibrary.lib`: The reference to the shared library."""
        return self._lib.lib

    def log_errcheck(self, result, func, arguments):
        """Convenience method for logging an errcheck_ when calling an SDK function.

        .. _errcheck: https://docs.python.org/2/library/ctypes.html#ctypes._FuncPtr.errcheck
        """
        self.log_debug('{}.{}{} -> {}'.format(self.__class__.__name__, func.__name__, arguments, result))
        return result
