"""
This :class:`~.picoscope.PicoScope` subclass implements the common functions 
for the PicoScopes that have a header file which ends with *Api.h, namely,
ps2000aApi, ps3000aApi, ps4000Api, ps4000aApi, ps5000Api, ps5000aApi and ps6000Api
"""
from ctypes import (c_int8, c_int16, c_uint16, c_int32, c_uint32, c_int64,
                    c_float, c_void_p, byref, cast, POINTER, string_at, addressof)

from .picoscope import PicoScope
from .picoscope_enums import PS5000ADeviceResolution, PicoScopeInfo
from .error_codes import (PicoScopeError, c_enum,
                          PICO_OK, ERROR_CODES_API,
                          PICO_POWER_SUPPLY_CONNECTED,
                          PICO_POWER_SUPPLY_NOT_CONNECTED)


class PicoScopeApi(PicoScope):

    def __init__(self, record, funcptrs):
        """
        Use the PicoScope SDK to communicate with the ps2000a, ps3000a, ps4000, ps4000a, 
        ps5000, ps5000a and ps6000 oscilloscopes.

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
        PicoScope.__init__(self, record, funcptrs)
        self._auto_select_power = False

    def _errcheck(self, result, func, args):
        """The SDK functions return PICO_OK if the function call was successful."""
        self.log.debug('{}.{}{}'.format(self.__class__.__name__, func.__name__, args))
        if result != PICO_OK:
            conn = self.equipment_record.connection
            error_name, msg = ERROR_CODES_API[result]
            error_msg = msg.format(
                model=conn.model,
                serial=conn.serial,
                sdk_filename=self._sdk_filename,
                sdk_filename_upper=self._sdk_filename.upper()
            )
            error_message = '\n{}: {}\n\t{}\n'.format(error_name, error_msg, conn)
            error_message += '\t{}.{}{}'.format(self.__class__.__name__, func.__name__, args)
            raise PicoScopeError(error_message)
        return result

    def change_power_source(self, power_state):
        """
        This function selects the power supply mode. You must call this function if any of the
        following conditions arises:
            * USB power is required
            * the AC power adapter is connected or disconnected during use
            * a USB 3.0 scope is plugged into a USB 2.0 port (indicated if any function returns
              the ``PICO_USB3_0_DEVICE_NON_USB3_0_PORT`` status code)
        
        This function is only valid for ps3000a, ps4000a and ps5000a. 
        """
        return self.ChangePowerSource(self._handle, power_state)

    def current_power_source(self):
        """
        This function returns the current power state of the device.

        This function is only valid for ps3000a, ps4000a and ps5000a. 
        """
        return self.CurrentPowerSource(self._handle)

    def enumerate_units(self):
        """
        This function counts the number of PicoScopes connected to the
        computer, and returns a list of serial numbers as a string.
        
        Not valid for ps5000.
        """
        count = c_int16()
        serials = c_int8()
        serial_length = c_int16()
        self.EnumerateUnits(byref(count), byref(serials), byref(serial_length))
        return count.value, serials.value, serial_length.value  # TODO get string from pointer

    def flash_led(self, start):
        """
        This function flashes the LED on the front of the scope without blocking the calling
        thread. Calls to :meth:`run_streaming` and :meth:`run_block` cancel any flashing
        started by this function. It is not possible to set the LED to be constantly illuminated,
        as this state is used to indicate that the scope has not been initialized.
        """
        return self.FlashLed(self._handle, start)

    def get_analogue_offset(self, voltage_range, coupling):
        """
        This function is used to get the maximum and minimum allowable analog offset for a
        specific voltage range.
        
        This function is invalid for ps4000 and ps5000.
        """
        maximum_voltage = c_float()
        minimum_voltage = c_float()
        self.GetAnalogueOffset(self._handle, voltage_range, coupling, byref(maximum_voltage), byref(minimum_voltage))
        return maximum_voltage.value, minimum_voltage.value

    def get_channel_information(self, info, probe, channels=-1):
        """
        This function queries which ranges are available on a scope device.
        
        The ``channels`` argument is ignored for ps4000a.
        
        This function is invalid for ps5000 and ps6000.        
        """
        ranges = c_int32()
        length = c_int32()
        if self._sdk_filename == 'ps4000a':
            self.sdk.ps4000aGetChannelInformation(self._handle, info, probe, byref(ranges), byref(length))
        else:
            self.GetChannelInformation(self._handle, info, probe, byref(ranges), byref(length), channels)
        return ranges.value, length.value

    def get_max_down_sample_ratio(self, no_of_unaggreated_samples, down_sample_ratio_mode, segment_index):
        """
        This function returns the maximum down-sampling ratio that can be used for a given
        number of samples in a given down-sampling mode.
        """
        max_down_sample_ratio = c_uint32()
        self.GetMaxDownSampleRatio(self._handle, no_of_unaggreated_samples, byref(max_down_sample_ratio),
                                   down_sample_ratio_mode, segment_index)
        return max_down_sample_ratio.value

    def get_max_segments(self):
        """
        This function returns the maximum number of segments allowed for the opened
        device. This number is the maximum value of ``nsegments`` that can be passed to
        :meth:`memory_segments`.
        
        This function is valid for ps2000a, ps3000a, ps4000a and ps5000a.
        """
        max_segments = c_uint16() if self._sdk_filename == 'ps2000a' else c_uint32()
        self.GetMaxSegments(self._handle, byref(max_segments))
        return max_segments.value

    def get_no_of_captures(self):
        """
        This function finds out how many captures are available in rapid block mode after
        :meth:`run_block` has been called when either the collection completed or the
        collection of waveforms was interrupted by calling :meth:`stop`. The returned value
        (``nCaptures``) can then be used to iterate through the number of segments using
        :meth:`get_values`, or in a single call to :meth:`get_values_bulk` where it is used
        to calculate the ``toSegmentIndex`` parameter.

        Not valid for ps5000.
        """
        n_captures = c_uint16() if self._sdk_filename == 'ps4000' else c_uint32()
        self.GetNoOfCaptures(self._handle, byref(n_captures))
        return n_captures.value

    def get_no_of_processed_captures(self):
        """
        This function finds out how many captures in rapid block mode have been processed
        after :meth:`run_block has been called when either the collection completed or the
        collection of waveforms was interrupted by calling :meth:`stop`. The returned value
        (``nCaptures``) can then be used to iterate through the number of segments using
        :meth:`get_values`, or in a single call to :meth:`get_values_bulk` where it is used
        to calculate the ``toSegmentIndex`` parameter.        

        Not valid for ps4000 and ps5000.
        """
        n_processed_captures = c_uint32()
        self.GetNoOfProcessedCaptures(self._handle, byref(n_processed_captures))
        return n_processed_captures.value

    def get_streaming_latest_values(self, lp_ps):
        """
        This function instructs the driver to return the next block of values to your
        :meth:`streaming_ready` callback. You must have previously called
        :meth:`run_streaming` beforehand to set up streaming.        
        """
        p_parameter = c_void_p()
        self.GetStreamingLatestValues(self._handle, lp_ps, byref(p_parameter))
        return p_parameter.value  # TODO get pointer data

    def get_timebase(self, timebase, no_samples, segment_index, oversample=-1):
        """
        This function calculates the sampling rate and maximum number of samples for a
        given timebase under the specified conditions. The result will depend on the number of
        channels enabled by the last call to :meth:`set_channel`.
        
        The ``oversample`` argument is ignored for ps4000a and ps5000a.
        """
        time_interval_nanoseconds = c_int32()
        if self._sdk_filename in ('ps4000a', 'ps5000a'):
            max_samples = c_int32()
            self.GetTimebase(self._handle, timebase, no_samples, byref(time_interval_nanoseconds),
                             byref(max_samples), segment_index)
        else:
            max_samples = c_uint32() if self._sdk_filename == 'ps6000' else c_int32()
            self.GetTimebase(self._handle, timebase, no_samples, byref(time_interval_nanoseconds),
                             oversample, byref(max_samples), segment_index)
        return time_interval_nanoseconds.value, max_samples.value

    def get_timebase2(self, timebase, no_samples, segment_index, oversample=-1):
        """
        This function is an upgraded version of :meth:`get_timebase`, and returns the time
        interval as a ``float`` rather than an ``int32_t``. This allows it to return 
        sub-nanosecond time intervals. See :meth:`get_timebase` for a full description.
        
        The ``oversample`` argument is ignored for ps4000a and ps5000a.
        """
        time_interval_nanoseconds = c_float()
        if self._sdk_filename in ('ps4000a', 'ps5000a'):
            max_samples = c_int32()
            self.GetTimebase2(self._handle, timebase, no_samples, byref(time_interval_nanoseconds),
                                         byref(max_samples), segment_index)
        else:
            max_samples = c_uint32() if self._sdk_filename == 'ps6000' else c_int32()
            self.GetTimebase2(self._handle, timebase, no_samples, byref(time_interval_nanoseconds),
                                         oversample, byref(max_samples), segment_index)
        return time_interval_nanoseconds.value, max_samples.value

    def get_trigger_time_offset(self, segment_index):
        """
        This function gets the time, as two 4-byte values, at which the trigger occurred. Call it
        after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture. A 64-bit version of this function,
        :meth:`get_trigger_time_offset64`, is also available.
        """
        time_upper = c_uint32()
        time_lower = c_uint32()
        time_units = c_enum()
        self.GetTriggerTimeOffset(self._handle, byref(time_upper), byref(time_lower), byref(time_units), segment_index)
        return time_upper.value, time_lower.value, time_units.value

    def get_trigger_time_offset64(self, segment_index):
        """
        This function gets the time, as a single 64-bit value, at which the trigger occurred. Call
        it after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture. A 32-bit version of this function,
        :meth:`get_trigger_time_offset`, is also available.
        """
        time = c_int64()
        time_units = c_enum()
        self.GetTriggerTimeOffset64(self._handle, byref(time), byref(time_units), segment_index)
        return time.value, time_units.value

    def get_unit_info(self, info):
        """
        This function retrieves information about the specified oscilloscope. If the device fails
        to open, or no device is opened only the driver version is available.
        
        Args:
            info(:class:`~.picoscope_enums.PicoScopeInfo`): An enum from 
                :class:`~.picoscope_enums.PicoScopeInfo`.
        """
        string = c_int8(127)
        required_size = c_int16()
        self.GetUnitInfo(self._handle, byref(string), string.value, byref(required_size), PicoScopeInfo(info))
        return '{}: {}'.format(PicoScopeInfo(info).name, string_at(addressof(string)).decode('utf-8'))

    def get_values(self, start_index, down_sample_ratio, down_sample_ratio_mode, segment_index):
        """
        This function returns block-mode data, with or without down sampling, starting at the
        specified sample number. It is used to get the stored data from the driver after data
        collection has stopped.
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValues(self._handle, start_index, byref(no_of_samples), down_sample_ratio,
                       down_sample_ratio_mode, segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_async(self, start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode, segment_index):
        """
        This function returns data either with or without down sampling, starting at the
        specified sample number. It is used to get the stored data from the scope after data
        collection has stopped. It returns the data using a callback.
        """
        lp_data_ready = c_void_p()
        p_parameter = c_void_p()
        self.GetValuesAsync(self._handle, start_index, no_of_samples, down_sample_ratio, down_sample_ratio_mode,
                            segment_index, byref(lp_data_ready), byref(p_parameter))
        return lp_data_ready.value, p_parameter.value  # TODO get pointer values

    def get_values_bulk(self, from_segment_index, to_segment_index, down_sample_ratio=-1, down_sample_ratio_mode=-1):
        """
        This function retrieves waveforms captured using rapid block mode. The waveforms
        must have been collected sequentially and in the same run.
        
        The ``down_sample_ratio`` and ``down_sample_ratio_mode`` arguments are ignored for 
        ps4000 and ps5000.
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        if self._sdk_filename in ('ps4000', 'ps5000'):
            self.GetValuesBulk(self._handle, byref(no_of_samples), from_segment_index,
                               to_segment_index, byref(overflow))
        else:
            self.GetValuesBulk(self._handle, byref(no_of_samples), from_segment_index,
                               to_segment_index, down_sample_ratio, down_sample_ratio_mode, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_overlapped(self, start_index, down_sample_ratio, down_sample_ratio_mode, segment_index):
        """
        This function allows you to make a deferred data-collection request, which will later be
        executed, and the arguments validated, when you call :meth:`run_block` in block
        mode. The advantage of this function is that the driver makes contact with the scope
        only once, when you call :meth:`run_block`, compared with the two contacts that
        occur when you use the conventional :meth:`run_block`, :meth:`get_values` calling
        sequence. This slightly reduces the dead time between successive captures in block
        mode.
        
        This function is invalid for ps4000 and ps5000.
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValuesOverlapped(self._handle, start_index, byref(no_of_samples), down_sample_ratio,
                                 down_sample_ratio_mode, segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_overlapped_bulk(self, start_index, down_sample_ratio, down_sample_ratio_mode,
                                   from_segment_index, to_segment_index):
        """
        This function allows you to make a deferred data-collection request, which will later be
        executed, and the arguments validated, when you call :meth:`run_block` in rapid
        block mode. The advantage of this method is that the driver makes contact with the
        scope only once, when you call :meth:`run_block`, compared with the two contacts
        that occur when you use the conventional :meth:`run_block`,
        :meth:`get_values_bulk` calling sequence. This slightly reduces the dead time
        between successive captures in rapid block mode.
        
        This function is invalid for ps4000 and ps5000.
        """
        no_of_samples = c_uint32()
        overflow = c_int16()
        self.GetValuesOverlappedBulk(self._handle, start_index, byref(no_of_samples), down_sample_ratio,
                                     down_sample_ratio_mode, from_segment_index, to_segment_index, byref(overflow))
        return no_of_samples.value, overflow.value

    def get_values_trigger_time_offset_bulk(self, from_segment_index, to_segment_index):
        """
        This function retrieves the time offsets, as lower and upper 32-bit values, for
        waveforms obtained in rapid block mode.
        This function is provided for use in programming environments that do not support 64-
        bit integers. If your programming environment supports this data type, it is easier to
        use :meth:`get_values_trigger_time_offset_bulk64`.
        """
        times_upper = c_uint32()
        times_lower = c_uint32()
        time_units = c_enum()
        self.sdk.ps2000aGetValuesTriggerTimeOffsetBulk(self._handle, byref(times_upper), byref(times_lower),
                                                       byref(time_units), from_segment_index, to_segment_index)
        return times_upper.value, times_lower.value, time_units.value

    def get_values_trigger_time_offset_bulk64(self, from_segment_index, to_segment_index):
        """
        This function retrieves the 64-bit time offsets for waveforms captured in rapid block mode.
        
        A 32-bit version of this function, :meth:`get_values_trigger_time_offset_bulk`, is
        available for use with programming languages that do not support 64-bit integers
        """
        times = c_int64()
        time_units = c_enum()
        self.GetValuesTriggerTimeOffsetBulk64(self._handle, byref(times), byref(time_units),
                                              from_segment_index, to_segment_index)
        return times.value, time_units.value

    def hold_off(self, holdoff, holdoff_type):
        """
        This function is for backward compatibility only and is not currently used.
        
        This function is only defined for ps2000a, ps3000a and ps4000.
        """
        return self.HoldOff(self._handle, holdoff, holdoff_type)

    def is_led_flashing(self):
        """
        This function reports whether or not the LED is flashing.
        
        This function is only defined for ps4000, ps4000a, ps5000 and ps5000a.
        """
        status = c_int16()
        self.IsLedFlashing(self._handle, byref(status))
        return status.value

    def is_ready(self):
        """
        This function may be used instead of a callback function to receive data from
        :meth:`run_block`. To use this method, pass a NULL pointer as the lpReady
        argument to :meth:`run_block`. You must then poll the driver to see if it has finished
        collecting the requested samples.
        """
        ready = c_int16()
        self.IsReady(self._handle, byref(ready))
        return ready.value

    def is_trigger_or_pulse_width_qualifier_enabled(self):
        """
        This function discovers whether a trigger, or pulse width triggering, is enabled.
        """
        trigger_enabled = c_int16()
        pulse_width_qualifier_enabled = c_int16()
        self.IsTriggerOrPulseWidthQualifierEnabled(self._handle, byref(trigger_enabled),
                                                   byref(pulse_width_qualifier_enabled))
        return trigger_enabled.value, pulse_width_qualifier_enabled.value

    def maximum_value(self):
        """
        This function returns the maximum ADC count returned by calls to get values.
        
        This function is only valid for ps2000a, ps3000a, ps4000a and ps5000a.
        """
        max_value = c_int16()
        self.MaximumValue(self._handle, byref(max_value))
        return max_value.value

    def memory_segments(self, n_segments):
        """
        This function sets the number of memory segments that the scope will use.
        When the scope is opened, the number of segments defaults to 1, meaning that each
        capture fills the scopes available memory. This function allows you to divide the
        memory into a number of segments so that the scope can store several waveforms
        sequentially.
        """
        n_max_samples = c_uint32() if self._sdk_filename == 'ps6000' else c_int32()
        self.MemorySegments(self._handle, n_segments, byref(n_max_samples))
        return n_max_samples.value

    def minimum_value(self):
        """
        This function returns the minimum ADC count returned by calls to :meth:`get_values`
        and related functions.
        
        This function is only valid for ps2000a, ps3000a, ps4000a and ps5000a.
        """
        min_value = c_int16()
        self.MinimumValue(self._handle, byref(min_value))
        return min_value.value

    def no_of_streaming_values(self):
        """
        This function returns the number of samples available after data collection in
        streaming mode. Call it after calling :meth:`stop`.
        """
        no_of_values = c_uint32()
        self.NoOfStreamingValues(self._handle, byref(no_of_values))
        return no_of_values.value

    def _get_optional_open_args(self, resolution):
        """Helper function for open_unit and open_unit_async"""
        if self.equipment_record.serial:
            serial_ptr = cast(self.equipment_record.serial.encode('utf-8'), POINTER(c_int8))
        else:
            serial_ptr = None

        args = ()  # all scopes take a handle as the first argument
        if self._sdk_filename not in ('ps4000', 'ps5000'):
            args += (serial_ptr,)  # these scopes take the serial as the second argument
        if self._sdk_filename == 'ps5000a':
            args += (resolution,)  # the ps5000a takes a resolution as the third argument

        return args

    def open_unit(self, auto_select_power=True, resolution=PS5000ADeviceResolution.DR_8BIT):
        """
        This function opens a PicoScope attached to the computer. The maximum number of 
        units that can be opened depends on the operating system, the kernel driver 
        and the computer.

        The ``resolution`` argument is only used by ps5000a and it is ignored for other 
        PicoScope Series.  
        """
        self._auto_select_power = auto_select_power
        handle = c_int16()
        args = (byref(handle), ) + self._get_optional_open_args(resolution)
        ret = self.OpenUnit(*args)

        if handle.value > 0:
            self._handle = handle

        if ret == PICO_OK:
            self.log.debug('{}.open_unit{}'.format(self.__class__.__name__, args))
            return ret

        if auto_select_power and ret in (PICO_POWER_SUPPLY_CONNECTED, PICO_POWER_SUPPLY_NOT_CONNECTED):
            self.log.debug('{}.open_unit{}'.format(self.__class__.__name__, args))
            return self.change_power_source(ret)

        # raise the exception
        self._errcheck(ret, self.open_unit, args)

    def open_unit_async(self, auto_select_power=True, resolution=PS5000ADeviceResolution.DR_8BIT):
        """
        This function opens a scope without blocking the calling thread. You can find out when
        it has finished by periodically calling :meth:`open_unit_progress` until that function
        returns a value of 100%.

        The ``resolution`` argument is only used by ps5000a and it is ignored for other 
        PicoScope Series.  
        """
        self._auto_select_power = auto_select_power
        status = c_int16()
        opts = self._get_optional_open_args(resolution)
        self.OpenUnitAsync(byref(status), *opts)
        return status.value

    def open_unit_progress(self):
        """
        This function checks on the progress of a request made to :meth:`open_unit_async` to
        open a scope. The return value is from 0 to 100, where 100 implies 
        that the operation is complete.
        """
        handle = c_int16()
        progress_percent = c_int16()
        complete = c_int16()
        ret = self.OpenUnitProgress(byref(handle), byref(progress_percent), byref(complete))

        if handle.value > 0:
            self._handle = handle

        if self._auto_select_power and ret in (PICO_POWER_SUPPLY_CONNECTED, PICO_POWER_SUPPLY_NOT_CONNECTED):
            ret = self.change_power_source(ret)

        if ret == PICO_OK:
            return 100 if complete.value else progress_percent.value
        else:
            # raise the exception
            self._errcheck(ret, self.open_unit_progress, ())

    def run_block(self, no_of_pre_trigger_samples, no_of_post_trigger_samples, timebase,
                  segment_index, lp_ready, oversample=-1):
        """
        This function starts collecting data in block mode. For a step-by-step guide to this
        process, see Using block mode.
        
        The number of samples is determined by ``noOfPreTriggerSamples`` and
        ``noOfPostTriggerSamples`` (see manual for details). The total number of samples
        must not be more than the size of the segment referred to by ``segmentIndex``.
        
        The ``oversample`` argument is not used for ps4000a and ps5000a.
        """
        time_indisposed_ms = c_int32()
        p_parameter = c_void_p()
        if self._sdk_filename in ('ps4000a', 'ps5000a'):
            self.RunBlock(self._handle, no_of_pre_trigger_samples, no_of_post_trigger_samples, timebase,
                          byref(time_indisposed_ms), segment_index, lp_ready, byref(p_parameter))
        else:
            self.RunBlock(self._handle, no_of_pre_trigger_samples, no_of_post_trigger_samples, timebase,
                          oversample, byref(time_indisposed_ms), segment_index, lp_ready, byref(p_parameter))
        return time_indisposed_ms.value, p_parameter.value  # TODO get the pointer value

    def run_streaming(self, sample_interval_time_units, max_pre_trigger_samples, max_post_trigger_samples,
                      auto_stop, down_sample_ratio, overview_buffer_size, down_sample_ratio_mode=-1):
        """
        This function tells the oscilloscope to start collecting data in streaming mode. When
        data has been collected from the device it is down sampled if necessary and then
        delivered to the application. Call :meth:`get_streaming_latest_values` to retrieve the
        data. See Using streaming mode for a step-by-step guide to this process.
        
        When a trigger is set, the total number of samples stored in the driver is the sum of
        ``max_pre_trigger_samples`` and ``max_post_trigger_samples``. If autoStop is false then
        this will become the maximum number of samples without down sampling.
        
        The ``down_sample_ratio_mode`` argument is ignored for ps4000 and ps5000.
        """
        sample_interval = c_uint32()
        if self._sdk_filename in ('ps4000', 'ps5000'):
            self.RunStreaming(self._handle, byref(sample_interval), sample_interval_time_units,
                              max_pre_trigger_samples, max_post_trigger_samples, auto_stop, down_sample_ratio,
                              overview_buffer_size)
        else:
            self.RunStreaming(self._handle, byref(sample_interval), sample_interval_time_units,
                              max_pre_trigger_samples, max_post_trigger_samples, auto_stop, down_sample_ratio,
                              down_sample_ratio_mode, overview_buffer_size)
        return sample_interval.value

    def set_bandwidth_filter(self, channel, bandwidth):
        """
        This function is reserved for future use.
        
        This function is only valid for ps3000a, ps4000a and ps5000a.        
        """
        return self.SetBandwidthFilter(self._handle, channel, bandwidth)

    def set_channel(self, channel, enabled, typ, measurement_range, analog_offset=-1, bandwidth=-1):
        """
        This function specifies whether an input channel is to be enabled, its input coupling
        type, voltage range, analog offset and bandwidth limit. Some of the arguments within
        this function have model-specific values. Please consult the manual according to the 
        model you have.
        
        The ``analog_offset`` and ``bandwidth`` arguments are ignored for ps4000 and ps5000.
         
        The ``bandwidth`` argument is ignored for ps2000a, ps3000a, ps4000a and ps5000a.
        """
        if self._sdk_filename in ('ps4000', 'ps5000'):
            return self.SetChannel(self._handle, channel, enabled, typ, measurement_range)
        elif self._sdk_filename == 'ps6000':
            return self.sdk.ps6000SetChannel(self._handle, channel, enabled, typ, measurement_range,
                                             analog_offset, bandwidth)
        else:
            return self.SetChannel(self._handle, channel, enabled, typ, measurement_range, analog_offset)

    def set_data_buffer(self, channel, buffer_length, mode=-1, segment_index=-1):
        """
        This function registers your data buffer, for non-aggregated data, with the PicoScope
        driver. You need to allocate the buffer before calling this function.
        
        The ``mode`` argument is ignored for ps4000 and ps5000.
        
        The ``segment_index`` argument is ignored for ps4000, ps5000 and ps6000.
        """
        buffer = c_int16()
        if self._sdk_filename in ('ps4000', 'ps5000'):
            self.SetDataBuffer(self._handle, channel, byref(buffer), buffer_length)
        elif self._sdk_filename == 'ps6000':
            self.sdk.ps6000SetDataBuffer(self._handle, channel, byref(buffer), buffer_length, mode)
        else:
            self.SetDataBuffer(self._handle, channel, byref(buffer), buffer_length, segment_index, mode)
        return buffer.value

    def set_data_buffer_bulk(self, channel, buffer_length, waveform, down_sample_ratio_mode=-1):
        """
        This function allows you to associate a buffer with a specified waveform number and
        input channel in rapid block mode. The number of waveforms captured is determined
        by the ``nCaptures`` argument sent to :meth:`set_no_of_captures`. There is only one
        buffer for each waveform because the only down-sampling mode that requires two
        buffers, aggregation mode, is not available in rapid block mode. Call one of the
        GetValues functions to retrieve the data after capturing.

        This function is only valid for ps4000, ps5000 and ps6000.

        The ``down_sample_ratio_mode`` argument is ignored for ps4000 and ps5000.
        """
        buffer = c_int16()
        if self._sdk_filename in ('ps4000', 'ps5000'):
            self.SetDataBufferBulk(self._handle, channel, byref(buffer), buffer_length, waveform)
        else:
            self.sdk.ps6000SetDataBufferBulk(self._handle, channel, byref(buffer), buffer_length, waveform,
                                             down_sample_ratio_mode)
        return buffer.value

    def set_data_buffers(self, channel, buffer_length, mode=-1, segment_index=-1):
        """
        This function tells the driver where to store the data, either unprocessed or
        down sampled, that will be returned after the next call to one of the GetValues
        functions. The function allows you to specify only a single buffer, so for aggregation
        mode, which requires two buffers, you need to call :meth:`set_data_buffers` instead.
        
        You must allocate memory for the buffer before calling this function.

        The ``mode`` argument is ignored for ps4000 and ps5000.

        The ``segment_index`` argument is ignored for ps4000, ps5000 and ps6000.
        """
        buffer_max = c_int16()
        buffer_min = c_int16()
        if self._sdk_filename in ('ps4000', 'ps5000'):
            self.SetDataBuffers(self._handle, channel, byref(buffer_max), byref(buffer_min), buffer_length)
        elif self._sdk_filename == 'ps6000':
            self.SetDataBuffers(self._handle, channel, byref(buffer_max), byref(buffer_min), buffer_length, mode)
        else:
            self.SetDataBuffers(self._handle, channel, byref(buffer_max), byref(buffer_min), buffer_length,
                                segment_index, mode)
        return buffer_max.value, buffer_min.value

    def set_digital_port(self, port, enabled, logic_level):
        """
        This function is used to enable the digital port and set the logic level (the voltage at
        which the state transitions from 0 to 1).
        
        This function is only used by ps2000a and ps3000a.
        """
        return self.SetDigitalPort(self._handle, port, enabled, logic_level)

    def set_ets(self, mode, ets_cycles, ets_interleave):
        """
        This function is used to enable or disable ETS (equivalent-time sampling) and to set
        the ETS parameters. See ETS overview for an explanation of ETS mode.
        """
        sample_time_picoseconds = c_int32()
        self.SetEts(self._handle, mode, ets_cycles, ets_interleave, byref(sample_time_picoseconds))
        return sample_time_picoseconds.value

    def set_ets_time_buffer(self, buffer_length):
        """
        This function tells the driver where to find your applications ETS time buffers. These
        buffers contain the 64-bit timing information for each ETS sample after you run a
        block-mode ETS capture.
        """
        buffer = c_int64()
        self.SetEtsTimeBuffer(self._handle, byref(buffer), buffer_length)
        return buffer.value

    def set_ets_time_buffers(self, buffer_length):
        """
        This function tells the driver where to find your applications ETS time buffers. These
        buffers contain the timing information for each ETS sample after you run a blockmode
        ETS capture. There are two buffers containing the upper and lower 32-bit parts
        of the timing information, to allow programming languages that do not support 64-bit
        data to retrieve the timings.
        """
        time_upper = c_uint32()
        time_lower = c_uint32()
        self.SetEtsTimeBuffers(self._handle, byref(time_upper), byref(time_lower), buffer_length)
        return time_upper.value, time_lower.value

    def set_frequency_counter(self, channel, enabled, range, threshold_major, threshold_minor):
        """
        This function is only define in the header file and it is not in the manual.
        This function is only valid for ps4000 and ps4000a.        
        """
        return self.SetFrequencyCounter(self._handle, channel, enabled, range, threshold_major, threshold_minor)

    def set_no_of_captures(self, n_captures):
        """
        This function sets the number of captures to be collected in one run of rapid block
        mode. If you do not call this function before a run, the driver will capture only one
        waveform. Once a value has been set, the value remains constant unless changed.
        """
        return self.SetNoOfCaptures(self._handle, n_captures)

    def set_sig_gen_arbitrary(self, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase,
                              delta_phase_increment, dwell_count, arbitrary_waveform_size, sweep_type,
                              operation, index_mode, shots, sweeps, trigger_type, trigger_source, ext_in_threshold):
        """
        This function programs the signal generator to produce an arbitrary waveform.
        """
        arbitrary_waveform = c_int16()
        self.SetSigGenArbitrary(self._handle, offset_voltage, pk_to_pk, start_delta_phase, stop_delta_phase,
                                delta_phase_increment, dwell_count, byref(arbitrary_waveform), arbitrary_waveform_size,
                                sweep_type, operation, index_mode, shots, sweeps, trigger_type, trigger_source,
                                ext_in_threshold)
        return arbitrary_waveform.value

    def set_sig_gen_built_in(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment,
                             dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source,
                             ext_in_threshold):
        """
        This function sets up the signal generator to produce a signal from a list of built-in
        waveforms. If different start and stop frequencies are specified, the device will sweep
        either up, down or up and down.
        """
        return self.SetSigGenBuiltIn(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency,
                                     stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps,
                                     trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_built_in_v2(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment,
                                dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source,
                                ext_in_threshold):
        """
        This function is an upgraded version of :meth:`set_sig_gen_built_in` with double-precision
        frequency arguments for more precise control at low frequencies.
        
        This function is invalid for ps4000 and ps4000a.
        """
        return self.SetSigGenBuiltInV2(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency,
                                       stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps,
                                       trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_properties_arbitrary(self, start_delta_phase, stop_delta_phase, delta_phase_increment,
                                         dwell_count, sweep_type, shots, sweeps, trigger_type, trigger_source,
                                         ext_in_threshold, offset_voltage=-1, pk_to_pk=-1):
        """
        This function reprograms the arbitrary waveform generator. All values can be
        reprogrammed while the signal generator is waiting for a trigger.

        The ``offset_voltage`` and ``pk_to_pk`` arguments are only used for ps6000.

        This function is invalid for ps4000 and ps5000.
        """
        if self._sdk_filename == 'ps6000':
            return self.sdk.ps6000SetSigGenPropertiesArbitrary(self._handle, offset_voltage, pk_to_pk,
                                                               start_delta_phase, stop_delta_phase,
                                                               delta_phase_increment, dwell_count,
                                                               sweep_type, shots, sweeps, trigger_type, trigger_source,
                                                               ext_in_threshold)
        else:
            return self.SetSigGenPropertiesArbitrary(self._handle, start_delta_phase, stop_delta_phase,
                                                     delta_phase_increment, dwell_count,
                                                     sweep_type, shots, sweeps, trigger_type, trigger_source,
                                                     ext_in_threshold)

    def set_sig_gen_properties_built_in(self, start_frequency, stop_frequency, increment, dwell_time,
                                        sweep_type, shots, sweeps, trigger_type, trigger_source,
                                        ext_in_threshold, offset_voltage=-1, pk_to_pk=-1):
        """
        This function reprograms the signal generator. Values can be changed while the signal
        generator is waiting for a trigger.
        
        The ``offset_voltage`` and ``pk_to_pk`` arguments are only used for ps6000.

        This function is invalid for ps4000 and ps5000.
        """
        if self._sdk_filename == 'ps6000':
            return self.sdk.ps6000SetSigGenPropertiesBuiltIn(self._handle, offset_voltage, pk_to_pk, start_frequency,
                                                             stop_frequency, increment, dwell_time, sweep_type, shots,
                                                             sweeps, trigger_type, trigger_source, ext_in_threshold)
        else:
            return self.SetSigGenPropertiesBuiltIn(self._handle, start_frequency,
                                                   stop_frequency, increment, dwell_time, sweep_type, shots,
                                                   sweeps, trigger_type, trigger_source, ext_in_threshold)

    def set_simple_trigger(self, enable, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function simplifies arming the trigger. It supports only the LEVEL trigger types
        and does not allow more than one channel to have a trigger applied to it. Any previous
        pulse width qualifier is cancelled.
        """
        return self.SetSimpleTrigger(self._handle, enable, source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger_delay(self, delay):
        """
        This function sets the post-trigger delay, which causes capture to start a defined time
        after the trigger event.
        """
        return self.SetTriggerDelay(self._handle, delay)

    def sig_gen_arbitrary_min_max_values(self):
        """
        This function returns the range of possible sample values and waveform buffer sizes
        that can be supplied to :meth:`set_sign_gen_arbitrary` for setting up the arbitrary
        waveform generator (AWG).
        """
        min_arbitrary_waveform_value = c_int16()
        max_arbitrary_waveform_value = c_int16()
        min_arbitrary_waveform_size = c_uint32()
        max_arbitrary_waveform_size = c_uint32()
        self.SigGenArbitraryMinMaxValues(self._handle,
                                         byref(min_arbitrary_waveform_value), byref(max_arbitrary_waveform_value),
                                         byref(min_arbitrary_waveform_size), byref(max_arbitrary_waveform_size))
        return (min_arbitrary_waveform_value.value, max_arbitrary_waveform_value.value,
                min_arbitrary_waveform_size.value, max_arbitrary_waveform_size.value)

    def sig_gen_frequency_to_phase(self, frequency, index_mode, buffer_length):
        """
        This function converts a frequency to a phase count for use with the arbitrary
        waveform generator (AWG). The value returned depends on the length of the buffer,
        the index mode passed and the device model. The phase count can then be sent to the
        driver through :meth:`set_sig_gen_arbitrary` or :meth:`set_sig_gen_properties_arbitrary`.
        """
        phase = c_uint32()
        self.SigGenFrequencyToPhase(self._handle, frequency, index_mode, buffer_length, byref(phase))
        return phase.value

    def sig_gen_software_control(self, state):
        """
        This function causes a trigger event, or starts and stops gating. It is used when the
        signal generator is set to SIGGEN_SOFT_TRIG.
        """
        return self.SigGenSoftwareControl(self._handle, state)

    def trigger_within_pre_trigger_samples(self, state):
        """
        This function is in the header file, but it is not in the manual.
        
        This function is only valid for ps4000 and ps5000a.        
        """
        return self.TriggerWithinPreTriggerSamples(self._handle, state)
