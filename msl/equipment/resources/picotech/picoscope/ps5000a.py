"""
A wrapper around the PicoScope ps5000a SDK.
"""
import math
from ctypes import byref

from msl.equipment.resources import register
from .picoscope_api import PicoScopeApi
from .functions import ps5000aApi_funcptrs
from .structs import PS5000ATriggerInfo
from .. import c_enum


@register(manufacturer=r'Pico\s*Tech', model=r'5\d{3}[AB]')
class PicoScope5000A(PicoScopeApi):

    MAX_VALUE_8BIT = 32512
    MIN_VALUE_8BIT = -32512
    MAX_VALUE_16BIT = 32767
    MIN_VALUE_16BIT = -32767
    LOST_DATA = -32768
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    PS5X42A_MAX_SIG_GEN_BUFFER_SIZE = 16384
    PS5X43A_MAX_SIG_GEN_BUFFER_SIZE = 32768
    PS5X44A_MAX_SIG_GEN_BUFFER_SIZE = 49152
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    AWG_DAC_FREQUENCY = 200e6
    AWG_PHASE_ACCUMULATOR = 4294967296.0
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    PS5244A_MAX_ETS_CYCLES = 500
    PS5244A_MAX_ETS_INTERLEAVE = 40
    PS5243A_MAX_ETS_CYCLES = 250
    PS5243A_MAX_ETS_INTERLEAVE = 20
    PS5242A_MAX_ETS_CYCLES = 125
    PS5242A_MAX_ETS_INTERLEAVE = 10
    SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    SINE_MAX_FREQUENCY = 20000000.
    SQUARE_MAX_FREQUENCY = 20000000.
    TRIANGLE_MAX_FREQUENCY = 20000000.
    SINC_MAX_FREQUENCY = 20000000.
    RAMP_MAX_FREQUENCY = 20000000.
    HALF_SINE_MAX_FREQUENCY = 20000000.
    GAUSSIAN_MAX_FREQUENCY = 20000000.
    MIN_FREQUENCY = 0.03

    EXT_MAX_VOLTAGE = 5.0

    def __init__(self, record):
        """A wrapper around the PicoScope ps5000a SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        """
        super(PicoScope5000A, self).__init__(record, ps5000aApi_funcptrs)

    def get_device_resolution(self):
        """
        Returns
        -------
        :class:`~.enums.PS5000ADeviceResolution`
            This function retrieves the resolution the specified device will run in.
        """
        resolution = c_enum()
        self.sdk.ps5000aGetDeviceResolution(self._handle, byref(resolution))
        return self.enDeviceResolution(resolution.value)

    def _get_timebase_index(self, dt):
        """
        See the manual for the sample interval formula as a function of device resolution.
        """
        resolution = self.get_device_resolution()
        if resolution == self.enDeviceResolution.RES_8BIT:
            if dt < 8e-9:
                return math.log(1e9 * dt, 2)
            else:
                return 125e6 * dt + 2
        elif resolution == self.enDeviceResolution.RES_12BIT:
            if dt < 16e-9:
                return math.log(500e6 * dt, 2) + 1
            else:
                return 62.5e6 * dt + 3
        elif resolution == self.enDeviceResolution.RES_16BIT:
            return 62.5e6 * dt + 3
        else:  # 14- and 15-bit resolution
            return 125e6 * dt + 2

    def get_trigger_info_bulk(self, from_segment_index, to_segment_index):
        """
        This function is in the header file, but it is not in the manual.

        Populates the :class:`~.structs.PS5000ATriggerInfo` structure.
        """
        trigger_info = PS5000ATriggerInfo()
        self.sdk.ps5000aGetTriggerInfoBulk(self._handle, byref(trigger_info), from_segment_index, to_segment_index)
        return trigger_info

    def set_device_resolution(self, resolution):
        """
        This function sets the new resolution. When using 12 bits or more the memory is
        halved. When using 15-bit resolution only 2 channels can be enabled to capture data,
        and when using 16-bit resolution only one channel is available. If resolution is
        changed, any data captured that has not been saved will be lost. If
        :meth:`~.PicoScope.set_channel` is not called, :meth:`~.PicoScope.run_block`
        and :meth:`~.PicoScope.run_streaming` may fail.
        """
        r = self.convert_to_enum(resolution, self.enDeviceResolution, prefix='RES_', to_upper=True)
        return self.sdk.ps5000aSetDeviceResolution(self._handle, r)
