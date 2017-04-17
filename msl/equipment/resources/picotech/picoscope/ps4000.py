from ctypes import c_int8, c_int16, c_uint32, c_int64, byref

from .picoscope import c_enum
from .picoscope_api import PicoScopeApi
from .functions import ps4000Api_funcptrs
from .structs import (
    PS4000PwqConditions,
    PS4000TriggerConditions,
    PS4000TriggerChannelProperties
)


class PicoScope4000(PicoScopeApi):

    MAX_OVERSAMPLE_12BIT = 16
    MAX_OVERSAMPLE_8BIT = 256
    PS4XXX_MAX_ETS_CYCLES = 400
    PS4XXX_MAX_INTERLEAVE = 80
    PS4262_MAX_VALUE = 32767
    PS4262_MIN_VALUE = -32767
    MAX_VALUE = 32764
    MIN_VALUE = -32764
    LOST_DATA = -32768
    EXT_MAX_VALUE = 32767
    EXT_MIN_VALUE = -32767
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_DELAY_COUNT = 8388607
    MIN_SIG_GEN_FREQ = 0.0
    MAX_SIG_GEN_FREQ = 100000.0
    MAX_SIG_GEN_FREQ_4262 = 20000.0
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MAX_SIG_GEN_BUFFER_SIZE = 8192
    MIN_DWELL_COUNT = 10
    PS4262_MAX_WAVEFORM_BUFFER_SIZE = 4096
    PS4262_MIN_DWELL_COUNT = 3
    MAX_SWEEPS_SHOTS = ((1 << 30) - 1)

    # EXT_MAX_VOLTAGE = ?

    def __init__(self, record):
        """
        A wrapper around the PicoScope ps4000 SDK.

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
        """
        PicoScopeApi.__init__(self, record, ps4000Api_funcptrs)

    def get_probe(self):
        """
        This function is in the header file, but it is not in the manual.
        """
        probe = c_enum()
        self.sdk.ps4000GetProbe(self._handle, byref(probe))
        return probe.value

    def get_trigger_channel_time_offset(self, segment_index, channel):
        """
        This function gets the time, as two 4-byte values, at which the trigger occurred,
        adjusted for the time skew of the specified channel relative to the trigger source. Call
        it after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture.
        """
        time_upper = c_uint32()
        time_lower = c_uint32()
        time_units = c_enum()
        self.sdk.ps4000GetTriggerChannelTimeOffset(self._handle, byref(time_upper), byref(time_lower),
                                                   byref(time_units), segment_index, channel)
        return time_upper.value, time_lower.value, time_units.value

    def get_trigger_channel_time_offset64(self, segment_index, channel):
        """
        This function gets the time, as a single 8-byte value, at which the trigger occurred,
        adjusted for the time skew of the specified channel relative to the trigger source. Call
        it after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture.
        """
        time = c_int64()
        time_units = c_enum()
        self.sdk.ps4000GetTriggerChannelTimeOffset64(self._handle, byref(time), byref(time_units),
                                                     segment_index, channel)
        return time.value, time_units.value

    def get_values_trigger_channel_time_offset_bulk(self, from_segment_index, to_segment_index, channel):
        """
        This function retrieves the time offset, as lower and upper 32-bit values, for a group of
        waveforms obtained in rapid block mode, adjusted for the time skew relative to the
        trigger source. The array size for ``timesUpper`` and ``timesLower`` must be greater
        than or equal to the number of waveform time offsets requested. The segment indexes
        are inclusive.
        """
        times_upper = c_uint32()
        times_lower = c_uint32()
        time_units = c_enum()
        self.sdk.ps4000GetValuesTriggerChannelTimeOffsetBulk(self._handle, byref(times_upper), byref(times_lower),
                                                             byref(time_units), from_segment_index, to_segment_index,
                                                             channel)
        return times_upper.value, times_lower.value, time_units.value

    def get_values_trigger_channel_time_offset_bulk64(self, from_segment_index, to_segment_index, channel):
        """
        This function retrieves the time offset, as a 64-bit integer, for a group of waveforms
        captured in rapid block mode, adjusted for the time skew relative to the trigger source.
        The array size of ``times`` must be greater than or equal to the number of waveform
        time offsets requested. The segment indexes are inclusive.
        """
        times = c_int64()
        time_units = c_enum()
        self.sdk.ps4000GetValuesTriggerChannelTimeOffsetBulk64(self._handle, byref(times), byref(time_units),
                                                               from_segment_index, to_segment_index, channel)
        return times.value, time_units.value

    def open_unit_async_ex(self):
        """
        This function opens a scope device selected by serial number without blocking the
        calling thread. You can find out when it has finished by periodically calling
        :meth:`open_unit_progress` until that function returns a non-zero value.
        """
        status = c_int16()
        serial = c_int8()
        self.sdk.ps4000OpenUnitAsyncEx(byref(status), byref(serial))
        return status.value, serial.value

    def open_unit_ex(self):
        """
        This function opens a scope device. The maximum number of units that can be opened
        is determined by the operating system, the kernel driver and the PC's hardware.
        """
        handle = c_int16()
        serial = c_int8()
        self.sdk.ps4000OpenUnitEx(byref(handle), byref(serial))
        if handle.value > 0:
            self._handle = handle
        return serial.value  # TODO the the serial as a string

    def run_streaming_ex(self, sample_interval_time_units, max_pre_trigger_samples, max_post_pre_trigger_samples,
                         auto_stop, down_sample_ratio, down_sample_ratio_mode, overview_buffer_size):
        """
        This function tells the oscilloscope to start collecting data in streaming mode and with
        a specified data reduction mode. When data has been collected from the device it is
        aggregated and the values returned to the application. Call
        :meth:`get_streaming_latest_values` to retrieve the data.
        """
        sample_interval = c_uint32()
        self.sdk.ps4000RunStreamingEx(self._handle, byref(sample_interval), sample_interval_time_units,
                                      max_pre_trigger_samples, max_post_pre_trigger_samples, auto_stop,
                                      down_sample_ratio, down_sample_ratio_mode, overview_buffer_size)
        return sample_interval.value

    def set_bw_filter(self, channel, enable):
        """
        This function enables or disables the bandwidth-limiting filter on the specified channel.
        """
        return self.sdk.ps4000SetBwFilter(self._handle, channel, enable)

    def set_data_buffer_with_mode(self, channel, buffer_length, mode):
        """
        This function registers your data buffer, for non-aggregated data, with the PicoScope
        4000 driver. You need to allocate the buffer before calling this function.
        """
        buffer = c_int16()
        self.sdk.ps4000SetDataBufferWithMode(self._handle, channel, byref(buffer), buffer_length, mode)
        return buffer.value

    def set_data_buffers_with_mode(self, channel, buffer_length, mode):
        """
        This function registers your data buffers, for receiving aggregated data, with the
        PicoScope 4000 driver. You need to allocate memory for the buffers before calling this
        function.
        """
        buffer_max = c_int16()
        buffer_min = c_int16()
        self.sdk.ps4000SetDataBuffersWithMode(self._handle, channel, byref(buffer_max), byref(buffer_min),
                                              buffer_length, mode)
        return buffer_max.value, buffer_min.value

    def set_ext_trigger_range(self, ext_range):
        """
        This function sets the range of the external trigger.
        """
        return self.sdk.ps4000SetExtTriggerRange(self._handle, ext_range)

    def set_probe(self, probe, range_):
        """
        This function is in the header file, but it is not in the manual.
        """
        return self.sdk.ps4000SetProbe(self._handle, probe, range_)

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse width qualification, which can be used on its own for pulse
        width triggering or combined with window triggering to produce more complex
        triggers. The pulse width qualifier is set by defining one or more conditions structures
        that are then ORed together. Each structure is itself the AND of the states of one or
        more of the inputs. This AND-OR logic allows you to create any possible Boolean
        function of the scope's inputs.

        Populates the :class:`~.picoscope_structs.PS4000PwqConditions` structure.
        """
        conditions = PS4000PwqConditions()
        self.sdk.ps4000SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction,
                                              lower, upper, pulse_width_type)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_conditions(self, n_conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is set up by
        defining one or more :class:`~.picoscope_structs.PS4000TriggerConditions` structures that 
        are then ORed together. Each structure is itself the AND of the states of one or more of 
        the inputs. This ANDORlogic allows you to create any possible Boolean function of the 
        scope's inputs.
        """
        conditions = PS4000TriggerConditions()
        self.sdk.ps4000SetTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value  # TODO return structure values

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        """
        This function is used to enable or disable triggering and set its parameters.

        Populates the :class:`~.picoscope_structs.PS4000TriggerChannelProperties` structure.
        """
        channel_properties = PS4000TriggerChannelProperties()
        self.sdk.ps4000SetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties,
                                                   aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value  # TODO return structure values
