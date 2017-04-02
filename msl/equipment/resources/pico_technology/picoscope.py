"""
Base class for PicoScopes from Pico Technology.
"""
import os
import logging

from msl.loadlib import IS_WINDOWS
from msl.equipment.connection_msl import ConnectionSDK
from .error_codes import PicoScopeError

picoscope_logger = logging.getLogger(__name__)

ALLOWED_SDKs = ('ps2000', 'ps2000a', 'ps3000', 'ps3000a', 'ps4000', 'ps4000a', 'ps5000', 'ps5000a', 'ps6000')


class PicoScope(ConnectionSDK):

    def __init__(self, record, funcptrs):
        """
        Use the PicoScope SDK to communicate with the oscilloscope.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.
        
        The SDK version that was initially used to create this base class and the PicoScope
        subclasses was *Pico Technology SDK 64-bit v10.6.10.24*

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
            
            funcptrs: The appropriate function-pointer list from :mod:`.picoscope_functions`
        """
        self._handle = None
        libtype = 'windll' if IS_WINDOWS else 'cdll'
        ConnectionSDK.__init__(self, record, libtype)

        self._sdk_filename = os.path.basename(os.path.splitext(self.sdk_path)[0])
        if self._sdk_filename not in ALLOWED_SDKs:
            msg = "Invalid SDK '{}'\nMust be one of {}".format(self._sdk_filename, ALLOWED_SDKs)
            raise PicoScopeError(msg)

        # set the PicoScope SDK function signatures
        for item in funcptrs:
            func = getattr(self.sdk, item[0])
            func.restype = item[2]
            if item[3]:
                func.errcheck = self._errcheck
            func.argtypes = [args[0] for args in item[4]]

            # The following allows for code re-usability by solving the "problem" that
            # the SDK functions have a different name but do the same task. A
            # solution is to use the 'alias' that was created to call each SDK function.
            #
            # For example, all PicoScopes have a "close unit" function but the SDK
            # function signatures are:
            #   ps2000_close_unit(int16_t handle)
            #   ps2000aCloseUnit(int16_t handle)
            #   ps3000_close_unit(int16_t handle)
            #   ps3000aCloseUnit(int16_t handle)
            #   ps4000CloseUnit(int16_t handle)
            #   ps4000aCloseUnit(int16_t handle)
            #   ps5000CloseUnit(int16_t handle)
            #   ps5000aCloseUnit(int16_t handle)
            #   ps6000CloseUnit(int16_t handle)
            # where, in this case, alias='CloseUnit' and the Python-to-SDK implementation
            # is simply to use self.CloseUnit(int16_t handle)
            setattr(self, item[1], func)

        self.log.debug('Connected to {}'.format(self.equipment_record.connection))

    @property
    def handle(self):
        """
        Returns the handle to the SDK library.
        """
        return self._handle

    @property
    def log(self):
        """The :py:mod:`logger <logging>` to use for all PicoScopes."""
        return picoscope_logger

    def close_unit(self):
        """Shutdown the PicoScope."""
        return self.CloseUnit(self._handle)

    def stop(self):
        """
        Stop the oscilloscope from sampling data. If this function is called 
        before a trigger event occurs, the oscilloscope may not contain valid data.
        """
        return self.Stop(self._handle)

    def ping_unit(self):
        """
        This function can be used to check that the already opened device is still 
        connected to the USB port and communication is successful.
        """
        return self.PingUnit(self._handle)

    def disconnect(self):
        """Shutdown the PicoScope."""
        if self._handle is not None:
            self.close_unit()
            self._handle = None
            self.log.debug('Disconnected from {}'.format(self.equipment_record.connection))

        # # Loading the SDK creates "Pipe_inOut" and "Pipe_inOutFifo" files, delete them.
        # # The files cannot be deleted without unloading the PicoScope shared library first.
        # # http://stackoverflow.com/questions/21770419/free-the-opened-ctypes-library-in-python
        # import os
        # import _ctypes
        # if IS_WINDOWS:
        #     _ctypes.FreeLibrary(self.sdk._handle)
        # else:
        #     _ctypes.dlclose(self.sdk._handle)
        # for filename in ('Pipe_inOut', 'Pipe_inOutFifo'):
        #     try:
        #         os.remove(os.path.join(os.getcwd(), filename))
        #     except:
        #         pass
