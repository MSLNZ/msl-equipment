from ctypes import c_int8, c_int16, c_int32, c_uint32, c_double, byref

from .picoscope import PicoScope
from .picoscope_functions import ps3000_funcptrs
from .picoscope_structs import PS3000TriggerConditions, PS3000TriggerChannelProperties, PS3000PwqConditions


class PicoScope3000(PicoScope):

    PS3000_FIRST_USB = 1
    PS3000_LAST_USB = 127
    PS3000_MAX_UNITS = (PS3000_LAST_USB - PS3000_FIRST_USB + 1)
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
    PS3000_MAX_OVERSAMPLE = 256
    PS3000_MAX_VALUE = 32767
    PS3000_MIN_VALUE = -32767
    PS3000_LOST_DATA = -32768
    PS3000_MIN_SIGGEN_FREQ = 0.093
    PS3000_MAX_SIGGEN_FREQ = 1000000
    PS3206_MAX_ETS_CYCLES = 500
    PS3206_MAX_ETS_INTERLEAVE = 100
    PS3205_MAX_ETS_CYCLES = 250
    PS3205_MAX_ETS_INTERLEAVE = 50
    PS3204_MAX_ETS_CYCLES = 125
    PS3204_MAX_ETS_INTERLEAVE = 25
    PS3000_MAX_ETS_CYCLES_INTERLEAVE_RATIO = 10
    PS3000_MIN_ETS_CYCLES_INTERLEAVE_RATIO = 1
    PS300_MAX_ETS_SAMPLES = 100000
    MAX_PULSE_WIDTH_QUALIFIER_COUNT = 16777215
    MAX_HOLDOFF_COUNT = 8388607

    def __init__(self, record):
        PicoScope.__init__(self, record, ps3000_funcptrs)
        raise NotImplementedError('The {} class has not been tested'.format(self.__class__.__name__))

    def close_unit(self):
        ret = self.sdk.ps3000_close_unit(self._handle)
        return ret.value

    def flash_led(self):
        ret = self.sdk.ps3000_flash_led(self._handle)
        return ret.value

    def get_streaming_last_values(self, lp_get_overview_buffers_max_min):
        ret = self.sdk.ps3000_get_streaming_last_values(self._handle, lp_get_overview_buffers_max_min)
        return ret.value

    def get_streaming_values(self, no_of_values, no_of_samples_per_aggregate):
        start_time = c_double()
        pbuffer_a_max = c_int16()
        pbuffer_a_min = c_int16()
        pbuffer_b_max = c_int16()
        pbuffer_b_min = c_int16()
        pbuffer_c_max = c_int16()
        pbuffer_c_min = c_int16()
        pbuffer_d_max = c_int16()
        pbuffer_d_min = c_int16()
        overflow = c_int16()
        trigger_at = c_uint32()
        triggered = c_int16()
        ret = self.sdk.ps3000_get_streaming_values(self._handle, byref(start_time), byref(pbuffer_a_max),
                                                   byref(pbuffer_a_min), byref(pbuffer_b_max),
                                                   byref(pbuffer_b_min), byref(pbuffer_c_max),
                                                   byref(pbuffer_c_min), byref(pbuffer_d_max),
                                                   byref(pbuffer_d_min), byref(overflow),
                                                   byref(trigger_at), byref(triggered), no_of_values,
                                                   no_of_samples_per_aggregate)
        return ret.value

    def get_streaming_values_no_aggregation(self, no_of_values):
        start_time = c_double()
        pbuffer_a = c_int16()
        pbuffer_b = c_int16()
        pbuffer_c = c_int16()
        pbuffer_d = c_int16()
        overflow = c_int16()
        trigger_at = c_uint32()
        trigger = c_int16()
        ret = self.sdk.ps3000_get_streaming_values_no_aggregation(self._handle, byref(start_time),
                                                                  byref(pbuffer_a), byref(pbuffer_b),
                                                                  byref(pbuffer_c), byref(pbuffer_d),
                                                                  byref(overflow), byref(trigger_at),
                                                                  byref(trigger), no_of_values)
        return ret.value

    def get_timebase(self, timebase, no_of_samples, oversample):
        time_interval = c_int32()
        time_units = c_int16()
        max_samples = c_int32()
        ret = self.sdk.ps3000_get_timebase(self._handle, timebase, no_of_samples, byref(time_interval),
                                           byref(time_units), oversample, byref(max_samples))
        return ret.value

    def get_times_and_values(self, time_units, no_of_values):
        times = c_int32()
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        ret = self.sdk.ps3000_get_times_and_values(self._handle, byref(times), byref(buffer_a),
                                                   byref(buffer_b), byref(buffer_c), byref(buffer_d),
                                                   byref(overflow), time_units, no_of_values)
        return ret.value

    def get_unit_info(self, string_length, line):
        string = c_int8()
        ret = self.sdk.ps3000_get_unit_info(self._handle, byref(string), string_length, line)
        return ret.value

    def get_values(self, no_of_values):
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        ret = self.sdk.ps3000_get_values(self._handle, byref(buffer_a), byref(buffer_b), byref(buffer_c),
                                         byref(buffer_d), byref(overflow), no_of_values)
        return ret.value

    def open_unit(self):
        self._handle = self.sdk.ps3000_open_unit()
        return self._handle.value

    def open_unit_async(self):
        ret = self.sdk.ps3000_open_unit_async()
        return ret.value

    def open_unit_progress(self):
        handle = c_int16()
        progress_percent = c_int16()
        ret = self.sdk.ps3000_open_unit_progress(byref(handle), byref(progress_percent))
        if handle.value > 0:
            self._handle = handle
        return progress_percent.value

    def overview_buffer_status(self):
        previous_buffer_overrun = c_int16()
        ret = self.sdk.ps3000_overview_buffer_status(self._handle, byref(previous_buffer_overrun))
        return ret.value

    def ping_unit(self):
        ret = self.sdk.ps3000PingUnit(self._handle)
        return ret.value

    def ready(self):
        ret = self.sdk.ps3000_ready(self._handle)
        return ret.value

    def release_stream_buffer(self):
        ret = self.sdk.ps3000_release_stream_buffer(self._handle)
        return ret.value

    def run_block(self, no_of_values, timebase, oversample):
        time_indisposed_ms = c_int32()
        ret = self.sdk.ps3000_run_block(self._handle, no_of_values, timebase, oversample, byref(time_indisposed_ms))
        return ret.value

    def run_streaming(self, sample_interval_ms, max_samples, windowed):
        ret = self.sdk.ps3000_run_streaming(self._handle, sample_interval_ms, max_samples, windowed)
        return ret.value

    def run_streaming_ns(self, sample_interval, time_units, max_samples, auto_stop,
                         no_of_samples_per_aggregate, overview_buffer_size):
        ret = self.sdk.ps3000_run_streaming_ns(self._handle, sample_interval, time_units, max_samples,
                                               auto_stop, no_of_samples_per_aggregate, overview_buffer_size)
        return ret.value

    def save_streaming_data(self, lp_callback_func, data_buffer_size):
        data_buffers = c_int16()
        ret = self.sdk.ps3000_save_streaming_data(self._handle, lp_callback_func, byref(data_buffers),
                                                  data_buffer_size)
        return ret.value

    def set_adv_trigger_channel_conditions(self, n_conditions):
        conditions = PS3000TriggerConditions()
        ret = self.sdk.ps3000SetAdvTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return ret.value

    def set_adv_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext):
        ret = self.sdk.ps3000SetAdvTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c,
                                                            channel_d, ext)
        return ret.value

    def set_adv_trigger_channel_properties(self, n_channel_properties, auto_trigger_milliseconds):
        channel_properties = PS3000TriggerChannelProperties()
        ret = self.sdk.ps3000SetAdvTriggerChannelProperties(self._handle, byref(channel_properties),
                                                            n_channel_properties, auto_trigger_milliseconds)
        return ret.value

    def set_adv_trigger_delay(self, delay, pre_trigger_delay):
        ret = self.sdk.ps3000SetAdvTriggerDelay(self._handle, delay, pre_trigger_delay)
        return ret.value

    def set_channel(self, channel, enabled, dc, range_):
        ret = self.sdk.ps3000_set_channel(self._handle, channel, enabled, dc, range_)
        return ret.value

    def set_ets(self, mode, ets_cycles, ets_interleave):
        ret = self.sdk.ps3000_set_ets(self._handle, mode, ets_cycles, ets_interleave)
        return ret.value

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, type_):
        conditions = PS3000PwqConditions()
        ret = self.sdk.ps3000SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions,
                                                    direction, lower, upper, type_)
        return ret.value

    def set_siggen(self, wave_type, start_frequency, stop_frequency, increment, dwell_time, repeat, dual_slope):
        ret = self.sdk.ps3000_set_siggen(self._handle, wave_type, start_frequency, stop_frequency, increment,
                                         dwell_time, repeat, dual_slope)
        return ret.value

    def set_trigger(self, source, threshold, direction, delay, auto_trigger_ms):
        ret = self.sdk.ps3000_set_trigger(self._handle, source, threshold, direction, delay, auto_trigger_ms)
        return ret.value

    def set_trigger2(self, source, threshold, direction, delay, auto_trigger_ms):
        ret = self.sdk.ps3000_set_trigger2(self._handle, source, threshold, direction, delay, auto_trigger_ms)
        return ret.value

    def stop(self):
        ret = self.sdk.ps3000_stop(self._handle)
        return ret.value

    def streaming_ns_get_interval_stateless(self, n_channels):
        sample_interval = c_uint32()
        ret = self.sdk.ps3000_streaming_ns_get_interval_stateless(self._handle, n_channels, byref(sample_interval))
        return ret.value
