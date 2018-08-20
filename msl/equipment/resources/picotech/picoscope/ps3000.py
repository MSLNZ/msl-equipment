"""
A wrapper around the PicoScope ps3000 SDK.
"""
from ctypes import c_int16, c_uint32, byref

from msl.equipment.resources import register
from .picoscope_2k3k import PicoScope2k3k
from .functions import ps3000_funcptrs


@register(manufacturer='Pico\s*Tech', model='3[24][02][456](?<! MSO)$')
class PicoScope3000(PicoScope2k3k):

    FIRST_USB = 1
    LAST_USB = 127
    MAX_UNITS = (LAST_USB - FIRST_USB + 1)
    PS3206_MAX_TIMEBASE = 21
    PS3205_MAX_TIMEBASE = 20
    PS3204_MAX_TIMEBASE = 19
    PS3224_MAX_TIMEBASE = 19
    PS3223_MAX_TIMEBASE = 19
    PS3424_MAX_TIMEBASE = 19
    PS3423_MAX_TIMEBASE = 19
    PS3225_MAX_TIMEBASE = 18
    PS3226_MAX_TIMEBASE = 19
    PS3425_MAX_TIMEBASE = 19
    PS3426_MAX_TIMEBASE = 19
    MAX_OVERSAMPLE = 256
    MAX_VALUE = 32767
    MIN_VALUE = -32767
    LOST_DATA = -32768
    MIN_SIGGEN_FREQ = 0.093
    MAX_SIGGEN_FREQ = 1000000
    PS3206_MAX_ETS_CYCLES = 500
    PS3206_MAX_ETS_INTERLEAVE = 100
    PS3205_MAX_ETS_CYCLES = 250
    PS3205_MAX_ETS_INTERLEAVE = 50
    PS3204_MAX_ETS_CYCLES = 125
    PS3204_MAX_ETS_INTERLEAVE = 25
    MAX_ETS_CYCLES_INTERLEAVE_RATIO = 10
    MIN_ETS_CYCLES_INTERLEAVE_RATIO = 1
    PS300_MAX_ETS_SAMPLES = 100000
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_HOLDOFF_COUNT = 8388607

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """A wrapper around the PicoScope ps3000 SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        super(PicoScope3000, self).__init__(record, ps3000_funcptrs)

    def release_stream_buffer(self):
        """Not found in the manual, but it is in the header file."""
        return self.sdk.ps3000_release_stream_buffer(self._handle)

    def save_streaming_data(self, lp_callback_func, data_buffer_size):
        """
        This function sends all available streaming data to the ``lp_callback_func``
        callback function in your application. Your callback function decides what to do with
        the data.
        """
        data_buffers = c_int16()
        ret = self.sdk.ps3000_save_streaming_data(self._handle, lp_callback_func, byref(data_buffers), data_buffer_size)
        return ret.value, data_buffers.value

    def set_siggen(self, wave_type, start_frequency, stop_frequency, increment, dwell_time, repeat, dual_slope):
        """
        This function is used to enable or disable the signal generator and sweep functions.
        """
        return self.sdk.ps3000_set_siggen(self._handle, wave_type, start_frequency, stop_frequency, increment,
                                          dwell_time, repeat, dual_slope)

    def streaming_ns_get_interval_stateless(self, n_channels):
        """Not found in the manual, but it is in the header file."""
        sample_interval = c_uint32()
        ret = self.sdk.ps3000_streaming_ns_get_interval_stateless(self._handle, n_channels, byref(sample_interval))
        return ret.value, sample_interval.value
