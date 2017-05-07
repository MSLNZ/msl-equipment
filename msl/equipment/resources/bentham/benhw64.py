"""
A wrapper around the Bentham SDK benhw32_cdecl.dll.
"""
import os
import inspect

from msl.loadlib import Client64

from msl.equipment.connection import Connection
from .errors import BI_OK, ERROR_CODES
from .tokens import MonochromatorCurrentWL, BenMono


class Bentham(Connection, Client64):

    def __init__(self, record):
        """A wrapper around the :class:`.benhw32.Bentham32` class.

        This class can be used with either a 32-bit or 64-bit Python interpreter
        to call the 32-bit functions in ``benhw32_cdecl.dll``.

        The :obj:`record.connection.properties <msl.equipment.record_types.ConnectionRecord.properties>`
        dictionary for a Bentham device supports the following key-value pairs::
        
            'model': 'C:\path\\to\System.cfg',  # default is '' 
            'setup': 'C:\path\\to\System.atr',  # default is ''
        
        If both properties are not defined in the **Connections** 
        :class:`~msl.equipment.database.Database` then you will have to call 
        :meth:`build_system_model`, :meth:`load_setup` and :meth:`initialise` 
        to configure the SDK.

        Do not instantiate this class directly. Use the factory method, 
        :obj:`msl.equipment.factory.connect`, or the `record` object itself, 
        :obj:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`,
        to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            An equipment record from an **Equipment-Register** 
            :class:`~msl.equipment.database.Database`.
            
        Note
        ----
        The paths to ``benhw32_cdecl.dll`` and ``IEEE_32M.dll`` **MUST** be in your 
        environment ``PATH`` in order for the shared library to be loaded.
        """
        Connection.__init__(self, record)
        path = os.path.dirname(record.connection.address.split('::')[2])
        self.log_debug('Starting 32-bit Python server for "benhw32"')
        Client64.__init__(self, 'benhw32', append_path=[os.path.dirname(__file__), path])

        self._hw_id = None

        cfg_path = record.connection.properties.get('model', '')
        atr_path = record.connection.properties.get('setup', '')
        if cfg_path and atr_path:
            self.build_system_model(cfg_path)
            self.load_setup(atr_path)
            self.initialise()

    def auto_measure(self):
        ret, reading = self.request32('auto_measure')
        self.errcheck(ret)
        return reading

    def build_system_model(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError('Cannot find {}'.format(path))
        ret, error_report = self.request32('build_system_model', path)
        self.errcheck(ret, path, append_msg=error_report)
        return ret

    def disconnect(self):
        self.errcheck(self.request32('close'))
        self.shutdown_server32()

    def errcheck(self, result, *args, append_msg=''):
        frame = inspect.getouterframes(inspect.currentframe())[1]
        self.log_debug('{}.{}{} -> {}'.format(self.__class__.__name__, frame.function, args, result))
        if result != BI_OK:
            self.raise_exception('{}: {} {}'.format(*ERROR_CODES[result], append_msg))
        return result

    def get(self, hw_id, token, index):
        ret, value = self.request32('get', hw_id, token, index)
        self.errcheck(ret, hw_id, token, index)
        return value

    def get_component_list(self):
        ret, components = self.request32('get_component_list')
        self.errcheck(ret)
        return components

    def get_hardware_type(self, hw_id):
        ret, hardware_type = self.request32('get_hardware_type', hw_id)
        self.errcheck(ret, hw_id)
        return hardware_type

    def get_mono_items(self, hw_id):
        ret, items = self.request32('get_mono_items', hw_id)
        self.errcheck(ret, hw_id)
        return items

    @property
    def wavelength(self):
        if self._hw_id is None:
            for item in self.get_component_list():
                if self.get_hardware_type(item) == BenMono:
                    self._hw_id = item
                    break
            if self._hw_id is None:
                raise ValueError('Cannot get wavelength. BenMono is not a hardware type.')
        return self.get(self._hw_id, MonochromatorCurrentWL, 0)

    @wavelength.setter
    def wavelength(self, wavelength):
        self.select_wavelength(wavelength)

    def initialise(self):
        return self.errcheck(self.request32('initialise'))

    def load_setup(self, path):
        if not os.path.isfile(path):
            raise FileNotFoundError('Cannot find {}'.format(path))
        return self.errcheck(self.request32('load_setup', path), path)

    def park(self):
        return self.errcheck(self.request32('park'))

    def select_wavelength(self, wavelength):
        ret, recommended_delay_ms = self.request32('select_wavelength', wavelength)
        self.errcheck(ret, wavelength)
        return recommended_delay_ms

    def set(self, hw_id, token, index, value):
        ret = self.request32('set', hw_id, token, index, value)
        return self.errcheck(ret, hw_id, token, index, value)

    def version(self):
        version = self.request32('get_version')
        self.log_debug('{}.version() -> {}'.format(self.__class__.__name__, version))
        return version

    def zero_calibration(self, start_wavelength, stop_wavelength):
        ret = self.request32('zero_calibration', start_wavelength, stop_wavelength)
        return self.errcheck(ret, start_wavelength, stop_wavelength)
