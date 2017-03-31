from ctypes import c_int8, c_int16, c_int32, c_uint32, c_int64, c_float, c_void_p, byref

from .picoscope import PicoScope
from .pico_status import c_enum
from .picoscope_function_pointers import ps3000aApi_funcptrs
from .picoscope_structs import (PS3000ATriggerInfo, PS3000ADigitalChannelDirections,
                                PS3000APwqConditions, PS3000APwqConditionsV2, PS3000ATriggerConditions,
                                PS3000ATriggerConditionsV2, PS3000ATriggerChannelProperties)


class PicoScope3000A(PicoScope):

    PS3000A_MAX_OVERSAMPLE = 256
    PS3207A_MAX_ETS_CYCLES = 500
    PS3207A_MAX_INTERLEAVE = 40
    PS3206A_MAX_ETS_CYCLES = 500
    PS3206A_MAX_INTERLEAVE = 40
    PS3206MSO_MAX_INTERLEAVE = 80
    PS3205A_MAX_ETS_CYCLES = 250
    PS3205A_MAX_INTERLEAVE = 20
    PS3205MSO_MAX_INTERLEAVE = 40
    PS3204A_MAX_ETS_CYCLES = 125
    PS3204A_MAX_INTERLEAVE = 10
    PS3204MSO_MAX_INTERLEAVE = 20
    PS3000A_EXT_MAX_VALUE = 32767
    PS3000A_EXT_MIN_VALUE = -32767
    PS3000A_MAX_LOGIC_LEVEL = 32767
    PS3000A_MIN_LOGIC_LEVEL = -32767
    MIN_SIG_GEN_FREQ = 0.0
    MAX_SIG_GEN_FREQ = 20000000.0
    PS3207B_MAX_SIG_GEN_BUFFER_SIZE = 32768
    PS3206B_MAX_SIG_GEN_BUFFER_SIZE = 16384
    MAX_SIG_GEN_BUFFER_SIZE = 8192
    MIN_SIG_GEN_BUFFER_SIZE = 1
    MIN_DWELL_COUNT = 3
    # MAX_SWEEPS_SHOTS = ((1 << 30) - 1)
    MAX_ANALOGUE_OFFSET_50MV_200MV = 0.250
    MIN_ANALOGUE_OFFSET_50MV_200MV = -0.250
    MAX_ANALOGUE_OFFSET_500MV_2V = 2.500
    MIN_ANALOGUE_OFFSET_500MV_2V = -2.500
    MAX_ANALOGUE_OFFSET_5V_20V = 20.
    MIN_ANALOGUE_OFFSET_5V_20V = -20.
    PS3000A_SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN = 0xFFFFFFFF
    PS3000A_SINE_MAX_FREQUENCY = 1000000.
    PS3000A_SQUARE_MAX_FREQUENCY = 1000000.
    PS3000A_TRIANGLE_MAX_FREQUENCY = 1000000.
    PS3000A_SINC_MAX_FREQUENCY = 1000000.
    PS3000A_RAMP_MAX_FREQUENCY = 1000000.
    PS3000A_HALF_SINE_MAX_FREQUENCY = 1000000.
    PS3000A_GAUSSIAN_MAX_FREQUENCY = 1000000.
    PS3000A_PRBS_MAX_FREQUENCY = 1000000.
    PS3000A_PRBS_MIN_FREQUENCY = 0.03
    PS3000A_MIN_FREQUENCY = 0.03

    def __init__(self, record):
        PicoScope.__init__(self, record, ps3000aApi_funcptrs)

    def change_power_source(self, power_state):
        self.ChangePowerSource(self._handle, power_state)

    def close_unit(self):
        self.CloseUnit(self._handle)

    def current_power_source(self):
        self.CurrentPowerSource(self._handle)

    def enumerate_units(self):
        count = c_int16()
        serials = c_int8()
        serial_lth = c_int16()
        self.EnumerateUnits(byref(count), byref(serials), byref(serial_lth))
        return count.value, serials.value, serial_lth.value

    def flash_led(self, start):
        self.FlashLed(self._handle, start)

    def get_analogue_offset(self, range, coupling):
        maximum_voltage = c_float()
        minimum_voltage = c_float()
        self.GetAnalogueOffset(self._handle, range, coupling, byref(maximum_voltage), byref(minimum_voltage))
        return maximum_voltage.value, minimum_voltage.value

    def get_channel_information(self, info, probe, channels):
        ranges = c_int32()
        length = c_int32()
        self.GetChannelInformation(self._handle, info, probe, byref(ranges), byref(length), channels)
        return ranges.value, length.value

    def get_max_down_sample_ratio(self, no_of_unaggreated_samples, down_sample_ratio_mode, segment_index):
        max_down_sample_ratio = c_uint32()
        self.GetMaxDownSampleRatio(self._handle, no_of_unaggreated_samples, byref(max_down_sample_ratio), down_sample_ratio_mode, segment_index)
        return max_down_sample_ratio.value

    def get_max_ets_values(self):
        ets_cycles = c_int16()
        ets_interleave = c_int16()
        self.GetMaxEtsValues(self._handle, byref(ets_cycles), byref(ets_interleave))
        return ets_cycles.value, ets_interleave.value

    def get_max_segments(self):
        max_segments = c_uint32()
        self.GetMaxSegments(self._handle, byref(max_segments))
        return max_segments.value

    def get_no_of_captures(self):
        n_captures = c_uint32()
        self.GetNoOfCaptures(self._handle, byref(n_captures))
        return n_captures.value

    def get_no_of_processed_captures(self):
        n_processed_captures = c_uint32()
        self.GetNoOfProcessedCaptures(self._handle, byref(n_processed_captures))
        return n_processed_captures.value

    def get_streaming_latest_values(self, lp_ps):
        p_parameter = c_void_p()
        self.GetStreamingLatestValues(self._handle, lp_ps, byref(p_parameter))
        return p_parameter.value

    def get_timebase(self, timebase, no_samples, oversample, segment_index):
        time_interval_nanoseconds = c_int32()
        max_samples = c_int32()
        self.GetTimebase(self._handle, timebase, no_samples, byref(time_interval_nanoseconds), oversample, byref(max_samples), segment_index)
        return time_interval_nanoseconds.value, max_samples.value

    def get_timebase2(self, timebase, no_samples, oversample, segment_index):
        time_interval_nanoseconds = c_float()
        max_samples = c_int32()
        self.GetTimebase2(self._handle, timebase, no_samples, byref(time_interval_nanoseconds), oversample, byref(max_samples), segment_index)
        return time_interval_nanoseconds.value, max_samples.value

    def get_trigger_info_bulk(self, from_segment_index, to_segment_index):
        trigger_info = PS3000ATriggerInfo()
        self.GetTriggerInfoBulk(self._handle, byref(trigger_info), from_segment_index, to_segment_index)
        return trigger_info.value

    def get_trigger_time_offset(self, segment_index):
        time_upper = c_uint32()
        time_lower = c_uint32()
        time_units = c_enum()
        self.GetTriggerTimeOffset(self._handle, byref(time_upper), byref(time_lower), byref(time_units), segment_index)
        return time_upper.value, time_lower.value, time_units.value

    def get_trigger_time_offset64(self, segment_index):
        time = c_int64()
        time_units = c_enum()
        self.GetTriggerTimeOffset64(self._handle, byref(time), byref(time_units), segment_index)
        return time.value, time_units.value

    def get_unit_info(self, string_length, info):
        string = c_int8()
        required_size = c_int16()
        self.GetUnitInfo(self._handle, byref(string), string_length, byref(required_size), info)
        return string.value, required_size.value

    def get_values(self, start_index, down_sample_ratio, down_sample_ratio_mode, segment_index):
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValues(self._handle, start_index, byref(no_of_samples), down_sample_ratio, down_sample_ratio_mode, segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_async(self, start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode, segment_index):
        lp_data_ready = c_void_p()
        p_parameter = c_void_p()
        self.GetValuesAsync(self._handle, start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode, segment_index, byref(lp_data_ready), byref(p_parameter))
        return lp_data_ready.value, p_parameter.value

    def get_values_bulk(self, from_segment_index, to_segment_index, down_sample_ratio, down_sample_ratio_mode):
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValuesBulk(self._handle, byref(no_of_samples), from_segment_index, to_segment_index, down_sample_ratio, down_sample_ratio_mode, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_overlapped(self, start_index, down_sample_ratio, down_sample_ratio_mode, segment_index):
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValuesOverlapped(self._handle, start_index, byref(no_of_samples), down_sample_ratio, down_sample_ratio_mode, segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_overlapped_bulk(self, start_index, down_sample_ratio, down_sample_ratio_mode, from_segment_index, to_segment_index):
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValuesOverlappedBulk(self._handle, start_index, byref(no_of_samples), down_sample_ratio, down_sample_ratio_mode, from_segment_index, to_segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_trigger_time_offset_bulk(self, from_segment_index, to_segment_index):
        times_upper = c_uint32()
        times_lower = c_uint32()
        time_units = c_enum()
        self.GetValuesTriggerTimeOffsetBulk(self._handle, byref(times_upper), byref(times_lower), byref(time_units), from_segment_index, to_segment_index)
        return times_upper.value, times_lower.value, time_units.value

    def get_values_trigger_time_offset_bulk64(self, from_segment_index, to_segment_index):
        times = c_int64()
        time_units = c_enum()
        self.GetValuesTriggerTimeOffsetBulk64(self._handle, byref(times), byref(time_units), from_segment_index, to_segment_index)
        return times.value, time_units.value

    def hold_off(self, holdoff, type):
        self.HoldOff(self._handle, holdoff, type)

    def is_ready(self):
        ready = c_int16()
        self.IsReady(self._handle, byref(ready))
        return ready.value

    def is_trigger_or_pulse_width_qualifier_enabled(self):
        trigger_enabled = c_int16()
        pulse_width_qualifier_enabled = c_int16()
        self.IsTriggerOrPulseWidthQualifierEnabled(self._handle, byref(trigger_enabled), byref(pulse_width_qualifier_enabled))
        return trigger_enabled.value, pulse_width_qualifier_enabled.value

    def maximum_value(self):
        value = c_int16()
        self.MaximumValue(self._handle, byref(value))
        return value.value

    def memory_segments(self, n_segments):
        n_max_samples = c_int32()
        self.MemorySegments(self._handle, n_segments, byref(n_max_samples))
        return n_max_samples.value

    def minimum_value(self):
        value = c_int16()
        self.MinimumValue(self._handle, byref(value))
        return value.value

    def no_of_streaming_values(self):
        no_of_values = c_uint32()
        self.NoOfStreamingValues(self._handle, byref(no_of_values))
        return no_of_values.value

    def open_unit(self):
        handle = c_int16()
        serial = c_int8()
        self.OpenUnit(byref(self._handle), byref(serial))
        return handle.value, serial.value

    def open_unit_async(self):
        status = c_int16()
        serial = c_int8()
        self.OpenUnitAsync(byref(status), byref(serial))
        return status.value, serial.value

    def open_unit_progress(self):
        handle = c_int16()
        progress_percent = c_int16()
        complete = c_int16()
        self.OpenUnitProgress(byref(self._handle), byref(progress_percent), byref(complete))
        return handle.value, progress_percent.value, complete.value

    def ping_unit(self):
        self.PingUnit(self._handle)

    def run_block(self, no_of_pre_trigger_samples, no_of_post_trigger_samples, timebase, oversample, segment_index, lp_ready):
        time_indisposed_ms = c_int32()
        p_parameter = c_void_p()
        self.RunBlock(self._handle, no_of_pre_trigger_samples, no_of_post_trigger_samples, timebase, oversample, byref(time_indisposed_ms), segment_index, lp_ready, byref(p_parameter))
        return time_indisposed_ms.value, p_parameter.value

    def run_streaming(self, sample_interval_time_units, max_pre_trigger_samples, max_post_pre_trigger_samples, auto_stop, down_sample_ratio, down_sample_ratio_mode, overview_buffer_size):
        sample_interval = c_uint32()
        self.RunStreaming(self._handle, byref(sample_interval), sample_interval_time_units, max_pre_trigger_samples, max_post_pre_trigger_samples, auto_stop, down_sample_ratio, down_sample_ratio_mode, overview_buffer_size)
        return sample_interval.value

    def set_bandwidth_filter(self, channel, bandwidth):
        self.SetBandwidthFilter(self._handle, channel, bandwidth)

    def set_channel(self, channel, enabled, type, range, analog_offset):
        self.SetChannel(self._handle, channel, enabled, type, range, analog_offset)

    def set_data_buffer(self, channel_or_port, buffer_lth, segment_index, mode):
        buffer = c_int16()
        self.SetDataBuffer(self._handle, channel_or_port, byref(buffer), buffer_lth, segment_index, mode)
        return buffer.value

    def set_data_buffers(self, channel_or_port, buffer_lth, segment_index, mode):
        buffer_max = c_int16()
        buffer_min = c_int16()
        self.SetDataBuffers(self._handle, channel_or_port, byref(buffer_max), byref(buffer_min), buffer_lth, segment_index, mode)
        return buffer_max.value, buffer_min.value

    def set_digital_port(self, port, enabled, logic_level):
        self.SetDigitalPort(self._handle, port, enabled, logic_level)

    def set_ets(self, mode, ets_cycles, ets_interleave):
        sample_time_picoseconds = c_int32()
        self.SetEts(self._handle, mode, ets_cycles, ets_interleave, byref(sample_time_picoseconds))
        return sample_time_picoseconds.value

    def set_ets_time_buffer(self, buffer_lth):
        buffer = c_int64()
        self.SetEtsTimeBuffer(self._handle, byref(buffer), buffer_lth)
        return buffer.value

    def set_ets_time_buffers(self, buffer_lth):
        time_upper = c_uint32()
        time_lower = c_uint32()
        self.SetEtsTimeBuffers(self._handle, byref(time_upper), byref(time_lower), buffer_lth)
        return time_upper.value, time_lower.value

    def set_no_of_captures(self, n_captures):
        self.SetNoOfCaptures(self._handle, n_captures)

    def set_pulse_width_digital_port_properties(self, n_directions):
        directions = PS3000ADigitalChannelDirections()
        self.SetPulseWidthDigitalPortProperties(self._handle, byref(directions), n_directions)
        return directions.value

    def set_pulse_width_qualifier(self, n_conditions, direction, lower, upper, type):
        conditions = PS3000APwqConditions()
        self.SetPulseWidthQualifier(self._handle, byref(conditions), n_conditions, direction, lower, upper, type)
        return conditions.value

    def set_pulse_width_qualifier_v2(self, n_conditions, direction, lower, upper, type):
        conditions = PS3000APwqConditionsV2()
        self.SetPulseWidthQualifierV2(self._handle, byref(conditions), n_conditions, direction, lower, upper, type)
        return conditions.value

    def set_sig_gen_arbitrary(self, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, arbitrary_waveform_size, sweep_type, operation, index_mode, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        arbitrary_waveform = c_int16()
        self.SetSigGenArbitrary(self._handle, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, byref(arbitrary_waveform), arbitrary_waveform_size, sweep_type, operation, index_mode, shots, sweeps, trigger_type, trigger_source, ext_in_threshold)
        return arbitrary_waveform.value

    def set_sig_gen_built_in(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        self.SetSigGenBuiltIn(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_built_in_v2(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        self.SetSigGenBuiltInV2(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_properties_arbitrary(self, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, sweep_type, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        self.SetSigGenPropertiesArbitrary(self._handle, start_delta_phase, stop_delta_phase, delta_phase_increment, dwell_count, sweep_type, shots, sweeps, trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_properties_built_in(self, start_frequency, stop_frequency, increment, dwell_time, sweep_type, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        self.SetSigGenPropertiesBuiltIn(self._handle, start_frequency, stop_frequency, increment, dwell_time, sweep_type, shots, sweeps, trigger_type, trigger_source, ext_in_threshold)

    def set_simple_trigger(self, enable, source, threshold, direction, delay, auto_trigger_ms):
        self.SetSimpleTrigger(self._handle, enable, source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger_channel_conditions(self, n_conditions):
        conditions = PS3000ATriggerConditions()
        self.SetTriggerChannelConditions(self._handle, byref(conditions), n_conditions)
        return conditions.value

    def set_trigger_channel_conditions_v2(self, n_conditions):
        conditions = PS3000ATriggerConditionsV2()
        self.SetTriggerChannelConditionsV2(self._handle, byref(conditions), n_conditions)
        return conditions.value

    def set_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext, aux):
        self.SetTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c, channel_d, ext, aux)

    def set_trigger_channel_properties(self, n_channel_properties, aux_output_enable, auto_trigger_milliseconds):
        channel_properties = PS3000ATriggerChannelProperties()
        self.SetTriggerChannelProperties(self._handle, byref(channel_properties), n_channel_properties, aux_output_enable, auto_trigger_milliseconds)
        return channel_properties.value

    def set_trigger_delay(self, delay):
        self.SetTriggerDelay(self._handle, delay)

    def set_trigger_digital_port_properties(self, n_directions):
        directions = PS3000ADigitalChannelDirections()
        self.SetTriggerDigitalPortProperties(self._handle, byref(directions), n_directions)
        return directions.value

    def sig_gen_arbitrary_min_max_values(self):
        min_arbitrary_waveform_value = c_int16()
        max_arbitrary_waveform_value = c_int16()
        min_arbitrary_waveform_size = c_uint32()
        max_arbitrary_waveform_size = c_uint32()
        self.SigGenArbitraryMinMaxValues(self._handle, byref(min_arbitrary_waveform_value), byref(max_arbitrary_waveform_value), byref(min_arbitrary_waveform_size), byref(max_arbitrary_waveform_size))
        return min_arbitrary_waveform_value.value, max_arbitrary_waveform_value.value, min_arbitrary_waveform_size.value, max_arbitrary_waveform_size.value

    def sig_gen_frequency_to_phase(self, frequency, index_mode, buffer_length):
        phase = c_uint32()
        self.SigGenFrequencyToPhase(self._handle, frequency, index_mode, buffer_length, byref(phase))
        return phase.value

    def sig_gen_software_control(self, state):
        self.SigGenSoftwareControl(self._handle, state)

    def stop(self):
        self.Stop(self._handle)
