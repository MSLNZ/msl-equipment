from ctypes import c_int8, c_uint8, c_int16, c_int32, c_uint32, c_double, byref

from .picoscope import PicoScope
from .picoscope_function_pointers import ps2000_funcptrs
from .picoscope_structs import PS2000TriggerChannelProperties, PS2000TriggerConditions, PS2000PwqConditions
from .picoscope_callbacks import GetOverviewBuffersMaxMin


class PicoScope2000(PicoScope):

    PS2000_FIRST_USB = 1
    PS2000_LAST_USB = 127
    PS2000_MAX_UNITS = (PS2000_LAST_USB - PS2000_FIRST_USB + 1)
    PS2000_MAX_TIMEBASE = 19
    PS2105_MAX_TIMEBASE = 20
    PS2104_MAX_TIMEBASE = 19
    PS2200_MAX_TIMEBASE = 23
    PS2000_MAX_OVERSAMPLE = 256
    PS2105_MAX_ETS_CYCLES = 250
    PS2105_MAX_ETS_INTERLEAVE = 50
    PS2104_MAX_ETS_CYCLES = 125
    PS2104_MAX_ETS_INTERLEAVE = 25
    PS2203_MAX_ETS_CYCLES = 250
    PS2203_MAX_ETS_INTERLEAVE = 50
    PS2204_MAX_ETS_CYCLES = 250
    PS2204_MAX_ETS_INTERLEAVE = 40
    PS2205_MAX_ETS_CYCLES = 250
    PS2205_MAX_ETS_INTERLEAVE = 40
    PS2000_MIN_ETS_CYCLES_INTERLEAVE_RATIO = 1
    PS2000_MAX_ETS_CYCLES_INTERLEAVE_RATIO = 10
    PS2000_MIN_SIGGEN_FREQ = 0.0
    PS2000_MAX_SIGGEN_FREQ = 100000.0
    PS2000_MAX_VALUE = 32767
    PS2000_MIN_VALUE = -32767
    PS2000_LOST_DATA = -32768

    def __init__(self, record):
        PicoScope.__init__(self, record, ps2000_funcptrs)

    def close_unit(self):
        self.CloseUnit(self._handle)

    def flash_led(self):
        self.FlashLed(self._handle)

    def get_streaming_last_values(self):
        self.GetStreamingLastValues(self._handle, GetOverviewBuffersMaxMin)

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
        self.GetStreamingValues(self._handle, byref(start_time), byref(pbuffer_a_max), byref(pbuffer_a_min), byref(pbuffer_b_max), byref(pbuffer_b_min), byref(pbuffer_c_max), byref(pbuffer_c_min), byref(pbuffer_d_max), byref(pbuffer_d_min), byref(overflow), byref(trigger_at), byref(triggered), no_of_values, no_of_samples_per_aggregate)
        return start_time.value, pbuffer_a_max.value, pbuffer_a_min.value, pbuffer_b_max.value, pbuffer_b_min.value, pbuffer_c_max.value, pbuffer_c_min.value, pbuffer_d_max.value, pbuffer_d_min.value, overflow.value, trigger_at.value, triggered.value

    def get_streaming_values_no_aggregation(self, no_of_values):
        start_time = c_double()
        pbuffer_a = c_int16()
        pbuffer_b = c_int16()
        pbuffer_c = c_int16()
        pbuffer_d = c_int16()
        overflow = c_int16()
        trigger_at = c_uint32()
        trigger = c_int16()
        self.GetStreamingValuesNoAggregation(self._handle, byref(start_time), byref(pbuffer_a), byref(pbuffer_b), byref(pbuffer_c), byref(pbuffer_d), byref(overflow), byref(trigger_at), byref(trigger), no_of_values)
        return start_time.value, pbuffer_a.value, pbuffer_b.value, pbuffer_c.value, pbuffer_d.value, overflow.value, trigger_at.value, trigger.value

    def get_timebase(self, timebase, no_of_samples, oversample):
        time_interval = c_int32()
        time_units = c_int16()
        max_samples = c_int32()
        self.GetTimebase(self._handle, timebase, no_of_samples, byref(time_interval), byref(time_units), oversample, byref(max_samples))
        return time_interval.value, time_units.value, max_samples.value

    def get_times_and_values(self, time_units, no_of_values):
        times = c_int32()
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        self.GetTimesAndValues(self._handle, byref(times), byref(buffer_a), byref(buffer_b), byref(buffer_c), byref(buffer_d), byref(overflow), time_units, no_of_values)
        return times.value, buffer_a.value, buffer_b.value, buffer_c.value, buffer_d.value, overflow.value

    def get_unit_info(self, string_length, line):
        string = c_int8()
        self.GetUnitInfo(self._handle, byref(string), string_length, line)
        return string.value

    def get_values(self, no_of_values):
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        self.GetValues(self._handle, byref(buffer_a), byref(buffer_b), byref(buffer_c), byref(buffer_d), byref(overflow), no_of_values)
        return buffer_a.value, buffer_b.value, buffer_c.value, buffer_d.value, overflow.value

    def last_button_press(self):
        self.LastButtonPress(self._handle)

    def open_unit(self):
        self.OpenUnit()

    def open_unit_async(self):
        self.OpenUnitAsync()

    def open_unit_progress(self):
        handle = c_int16()
        progress_percent = c_int16()
        self.OpenUnitProgress(byref(self._handle), byref(progress_percent))
        return handle.value, progress_percent.value

    def overview_buffer_status(self):
        previous_buffer_overrun = c_int16()
        self.OverviewBufferStatus(self._handle, byref(previous_buffer_overrun))
        return previous_buffer_overrun.value

    def ping_unit(self):
        self.PingUnit(self._handle)

    def ready(self):
        self.Ready(self._handle)

    def run_block(self, no_of_values, timebase, oversample):
        time_indisposed_ms = c_int32()
        self.RunBlock(self._handle, no_of_values, timebase, oversample, byref(time_indisposed_ms))
        return time_indisposed_ms.value

    def run_streaming(self, sample_interval_ms, max_samples, windowed):
        self.RunStreaming(self._handle, sample_interval_ms, max_samples, windowed)

    def run_streaming_ns(self, sample_interval, time_units, max_samples, auto_stop, no_of_samples_per_aggregate):
        self.RunStreamingNs(self._handle, sample_interval, time_units, max_samples, auto_stop, no_of_samples_per_aggregate)

    def set_adv_trigger_channel_conditions(self, n_conditions):
        conditions = PS2000TriggerConditions()
        self.SetAdvTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value

    def set_adv_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext):
        self.SetAdvTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c, channel_d, ext)

    def set_adv_trigger_channel_properties(self, n_channel_properties, auto_trigger_milliseconds):
        channel_properties = PS2000TriggerChannelProperties()
        self.SetAdvTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties, auto_trigger_milliseconds)
        return channel_properties.value

    def set_adv_trigger_delay(self, delay, pre_trigger_delay):
        self.SetAdvTriggerDelay(self._handle, delay, pre_trigger_delay)

    def set_channel(self, channel, enabled, dc, range):
        self.SetChannel(self._handle, channel, enabled, dc, range)

    def set_ets(self, mode, ets_cycles, ets_interleave):
        self.SetEts(self._handle, mode, ets_cycles, ets_interleave)

    def set_led(self, state):
        self.SetLed(self._handle, state)

    def set_light(self, state):
        self.SetLight(self._handle, state)

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, type):
        conditions = PS2000PwqConditions()
        self.SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction, lower, upper, type)
        return conditions.value

    def set_sig_gen_arbitrary(self, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, arbitrary_waveform_size, sweep_type, sweeps):
        arbitrary_waveform = c_uint8()
        self.SetSigGenArbitrary(self._handle, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, byref(arbitrary_waveform), arbitrary_waveform_size, sweep_type, sweeps)
        return arbitrary_waveform.value

    def set_sig_gen_built_in(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, sweeps):
        self.SetSigGenBuiltIn(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, sweeps)

    def set_trigger(self, source, threshold, direction, delay, auto_trigger_ms):
        self.SetTrigger(self._handle, source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger2(self, source, threshold, direction, delay, auto_trigger_ms):
        self.SetTrigger2(self._handle, source, threshold, direction, delay, auto_trigger_ms)

    def stop(self):
        self.Stop(self._handle)
