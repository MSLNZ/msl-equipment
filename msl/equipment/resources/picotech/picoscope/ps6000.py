"""
A wrapper around the PicoScope ps6000 SDK.
"""
from ctypes import c_int16, c_uint32, byref

from msl.equipment.resources import register
from .picoscope_api import PicoScopeApi
from .functions import ps6000Api_funcptrs


@register(manufacturer='Pico\s*Tech', model='6\d{3}')
class PicoScope6000(PicoScopeApi):

    MAX_OVERSAMPLE_8BIT = 256
    MAX_VALUE = 32512
    MIN_VALUE = -32512
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_SIG_GEN_BUFFER_SIZE = 16384
    PS640X_C_D_MAX_SIG_GEN_BUFFER_SIZE = 65536
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    MAX_WAVEFORMS_PER_SECOND = 1000000
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.500
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.500
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    MAX_ETS_CYCLES = 250
    MAX_INTERLEAVE = 50
    PRBS_MAX_FREQUENCY = 20000000.
    SINE_MAX_FREQUENCY = 20000000.
    SQUARE_MAX_FREQUENCY = 20000000.
    TRIANGLE_MAX_FREQUENCY = 20000000.
    SINC_MAX_FREQUENCY = 20000000.
    RAMP_MAX_FREQUENCY = 20000000.
    HALF_SINE_MAX_FREQUENCY = 20000000.
    GAUSSIAN_MAX_FREQUENCY = 20000000.
    MIN_FREQUENCY = 0.03

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """A wrapper around the PicoScope ps6000 SDK.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        """
        PicoScopeApi.__init__(self, record, ps6000Api_funcptrs)

    def get_values_bulk_asyc(self, start_index, down_sample_ratio, down_sample_ratio_mode, from_segment_index,
                             to_segment_index):
        """
        This function is in the header file, but it is not in the manual.
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.sdk.ps6000GetValuesBulkAsyc(self._handle, start_index, byref(no_of_samples), down_sample_ratio,
                                         down_sample_ratio_mode, from_segment_index, to_segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def set_data_buffers_bulk(self, channel, buffer_length, waveform, down_sample_ratio_mode):
        """
        This function tells the driver where to find the buffers for aggregated data for each
        waveform in rapid block mode. The number of waveforms captured is determined by
        the ``nCaptures`` argument sent to :meth:`~.PicoScopeApi.set_no_of_captures`. Call
        one of the GetValues functions to retrieve the data after capture. If you do not need
        two buffers, because you are not using aggregate mode, then you can optionally use
        :meth:`~.PicoScopeApi.set_data_buffer_bulk` instead.
        """
        buffer_max = c_int16()
        buffer_min = c_int16()
        self.sdk.ps6000SetDataBuffersBulk(self._handle, channel, byref(buffer_max), byref(buffer_min),
                                          buffer_length, waveform, down_sample_ratio_mode)
        return buffer_max.value, buffer_min.value

    def set_external_clock(self, frequency, threshold):
        """
        This function tells the scope whether or not to use an external clock signal fed into the
        AUX input. The external clock can be used to synchronise one or more PicoScope 6000
        units to an external source.
        
        When the external clock input is enabled, the oscilloscope relies on the clock signal for
        all of its timing. The driver checks that the clock is running before starting a capture,
        but if the clock signal stops after the initial check, the oscilloscope will not respond to
        any further commands until it is powered down and back up again.
        
        Note: if the AUX input is set as an external clock input then it cannot also be used as
        an external trigger input.
        """
        return self.sdk.ps6000SetExternalClock(self._handle, frequency, threshold)

    def set_waveform_limiter(self, n_waveforms_per_second):
        """
        This function is in the header file, but it is not in the manual.
        """
        return self.sdk.ps6000SetWaveformLimiter(self._handle, n_waveforms_per_second)
