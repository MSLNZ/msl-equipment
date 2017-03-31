import logging

from msl.equipment.connection_msl import ConnectionSDK
from msl.equipment.resources.pico_technology import pico_status
from msl.equipment.resources.pico_technology.exceptions import PicoScopeError

logger = logging.getLogger(__name__)


class PicoScope(ConnectionSDK):

    def __init__(self, record, funcptrs):
        """
        Use the PicoScope SDK to communicate with the oscilloscope.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.
        
        The SDK version that was initially used to create this base class was
        *Pico Technology SDK 64-bit v10.6.10.24*

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~.database.Database`.
            
            funcptrs: The appropriate function-pointer list from .picoscope_function_pointers.py
        """
        ConnectionSDK.__init__(self, record, 'windll')

        self._handle = None

    def _errcheck(self, status, func, args):
        self._return_status = status
        # pyvisa.ctwrapper.types creates a reference to ctypes objects and therefore
        # the ctypes class names are referenced to the definitions in the pyvisa.ctwrapper.types module
        # don't want people thinking that pyvisa has anything to with the PicoScope
        s = '{}'.format(args).replace('pyvisa.ctwrapper.', 'c')
        logger.debug('{}.{}({})'.format(self.equipment_record.connection, func.__name__, s))
        if status != 0:
            base, msg = pico_status.ERROR_CODES[status]
            message = msg.replace('XXXX', self.equipment_record.model)
            raise PicoScopeError('{}: {}'.format(base, message))

    @property
    def handle(self):
        """Returns the handle to the SDK function."""
        return self._handle

    def disconnect(self):
        """Shut down the PicoScope."""
        if self._handle is not None:
            self.close_unit()
            self._handle = None
