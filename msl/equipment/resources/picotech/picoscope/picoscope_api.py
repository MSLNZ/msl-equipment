"""
Base class for the PicoScopes that have a header file which ends with \\*Api.h.

Namely, ps2000aApi, ps3000aApi, ps4000Api, ps4000aApi, ps5000Api, ps5000aApi and ps6000Api.
"""
from __future__ import annotations

from ctypes import POINTER
from ctypes import byref
from ctypes import c_float
from ctypes import c_int16
from ctypes import c_int32
from ctypes import c_int64
from ctypes import c_int8
from ctypes import c_uint16
from ctypes import c_uint32
from ctypes import c_void_p
from ctypes import cast

import numpy as np

from .enums import PicoScopeInfoApi
from .picoscope import PicoScope
from .. import c_enum
from ..errors import ERROR_CODES_API
from ..errors import PICO_BUSY
from ..errors import PICO_OK
from ..errors import PICO_POWER_SUPPLY_CONNECTED
from ..errors import PICO_POWER_SUPPLY_NOT_CONNECTED


class PicoScopeApi(PicoScope):

    def __init__(self, record, func_ptrs):
        """Base class for the PicoScopes that have a header file which ends with \\*Api.h.

        Use the PicoScope SDK to communicate with the ps2000a, ps3000a, ps4000, ps4000a,
        ps5000, ps5000a and ps6000 oscilloscopes.

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        func_ptrs : :mod:`.functions`
            The appropriate function-pointer list for the SDK.
        """
        super(PicoScopeApi, self).__init__(record, func_ptrs)
        self.enPicoScopeInfo = PicoScopeInfoApi

        self._buffer_size = None

        # check the equipment_record.connection.properties dictionary to see how to initialize the PicoScope
        properties = self.equipment_record.connection.properties

        self._auto_select_power = properties.get('auto_select_power', True)
        resolution = properties.get('resolution', '8BIT')
        open_unit = properties.get('open', True)
        open_unit_async = properties.get('open_async', None)

        if open_unit and open_unit_async is None:
            self.open_unit(self._auto_select_power, resolution)
        elif open_unit_async:
            self.open_unit_async(self._auto_select_power, resolution)

    def errcheck_api(self, result, func, args):
        """The SDK function returns PICO_OK if the function call was successful."""
        self.log_errcheck(result, func, args)
        if result == PICO_BUSY:
            self.log_info('%s is busy...', self._base_msg)
            return result
        if result != PICO_OK:
            conn = self.equipment_record.connection
            error_name, msg = ERROR_CODES_API.get(result, ('UnhandledError', 'Error code 0x{:x}'.format(result)))
            error_msg = msg.format(
                model=conn.model,
                serial=conn.serial,
                sdk_filename=self.SDK_FILENAME,
                sdk_filename_upper=self.SDK_FILENAME.upper()
            )
            self.raise_exception('{}: {}'.format(error_name, error_msg))
        return result

    def change_power_source(self, power_state):
        """Change the power source.

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
        ret = self.CurrentPowerSource(self._handle)
        if ret == PICO_POWER_SUPPLY_CONNECTED:
            return 'AC adaptor'
        elif ret == PICO_POWER_SUPPLY_NOT_CONNECTED:
            return 'USB cable'
        else:
            self.errcheck_api(ret, self.current_power_source, ())

    def flash_led(self, action):
        """
        This function flashes the LED on the front of the scope without blocking the calling
        thread. Calls to :meth:`~.PicoScope.run_streaming` and :meth:`~.PicoScope.run_block` cancel any flashing
        started by this function. It is not possible to set the LED to be constantly illuminated,
        as this state is used to indicate that the scope has not been initialized.
        """
        return self.FlashLed(self._handle, action)

    def get_analogue_offset(self, voltage_range, coupling):
        """
        This function is used to get the maximum and minimum allowable analog offset for a
        specific voltage range.

        This function is invalid for ps4000 and ps5000.
        """
        coupling_ = self.convert_to_enum(coupling, self.enCoupling, to_upper=True)
        v_range = self.convert_to_enum(voltage_range, self.enRange, prefix='R_', to_upper=True)
        maximum_voltage = c_float()
        minimum_voltage = c_float()
        self.GetAnalogueOffset(self._handle, v_range, coupling_, byref(maximum_voltage), byref(minimum_voltage))
        return maximum_voltage.value, minimum_voltage.value

    def get_channel_information(self, channel, info='ranges'):
        """
        This function queries which ranges are available on a scope device.

        This function is invalid for ps5000 and ps6000.

        Parameters
        ----------
        channel : :class:`enum.IntEnum`
            0=ChannelA, 1=ChannelB, ...
        info : :class:`enum.IntEnum`, optional
            A ``ChannelInfo`` enum value or enum member name.
        """
        ch = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        info_ = self.convert_to_enum(info, self.enChannelInfo, to_upper=True)
        n = 43  # The PS4000Range enum contains the maximum number of constants = 43
        ranges = (c_int32 * n)()
        length = c_int32(n)
        probe = 0  # not used, must be set to 0.
        self.GetChannelInformation(self._handle, info_, probe, ranges, byref(length), ch)
        return [self.enRange(ranges[i]) for i in range(length.value)]

    def get_max_down_sample_ratio(self, num_unaggreated_samples, mode='None', segment_index=0):
        """
        Returns
        -------
        :class:`int`
            This function returns the maximum down-sampling ratio that can be used for a given
            number of samples in a given down-sampling mode.
        """
        mode_ = self.convert_to_enum(mode, self.enRatioMode, to_upper=True)
        max_down_sample_ratio = c_uint32()
        self.GetMaxDownSampleRatio(self._handle, num_unaggreated_samples, byref(max_down_sample_ratio),
                                   mode_, segment_index)
        return max_down_sample_ratio.value

    def get_max_segments(self):
        """This function is valid for ps2000a, ps3000a, ps4000a and ps5000a.

        Returns
        -------
        :class:`int`
            This function returns the maximum number of segments allowed for the opened
            device. This number is the maximum value of ``nsegments`` that can be passed to
            :meth:`memory_segments`.
        """
        max_segments = c_uint16() if self.IS_PS2000A else c_uint32()
        self.GetMaxSegments(self._handle, byref(max_segments))
        return max_segments.value

    def get_no_of_captures(self):
        """
        This function finds out how many captures are available in rapid block mode after
        :meth:`~.PicoScope.run_block` has been called when either the collection completed or the
        collection of waveforms was interrupted by calling :meth:`~.PicoScope.stop`. The returned value
        (``nCaptures``) can then be used to iterate through the number of segments using
        :meth:`get_values`, or in a single call to :meth:`get_values_bulk` where it is used
        to calculate the ``toSegmentIndex`` parameter.

        Not valid for ps5000.
        """
        n_captures = c_uint16() if self.IS_PS4000 else c_uint32()
        self.GetNoOfCaptures(self._handle, byref(n_captures))
        return n_captures.value

    def get_num_of_processed_captures(self):
        """
        This function finds out how many captures in rapid block mode have been processed
        after :meth:`~.PicoScope.run_block` has been called when either the collection completed or the
        collection of waveforms was interrupted by calling :meth:`~.PicoScope.stop`. The returned value
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
        :mod:`StreamingReady callback <msl.equipment.resources.picotech.picoscope.callbacks>`.
        You must have previously called :meth:`~.PicoScope.run_streaming` beforehand to set up streaming.
        """
        p_parameter = c_void_p()
        self.GetStreamingLatestValues(self._handle, lp_ps, byref(p_parameter))

    def get_timebase(self, timebase, num_samples=0, segment_index=0, oversample=0):
        """
        Since Python supports the :class:`float` data type, this function returns
        :meth:`get_timebase2`. The timebase that is returned is in **seconds** (not ns).

        This function calculates the sampling rate and maximum number of samples for a
        given timebase under the specified conditions. The result will depend on the number of
        channels enabled by the last call to :meth:`~.PicoScope.set_channel`.

        The `oversample` argument is only used by ps4000, ps5000 and ps6000.
        """
        return self.get_timebase2(timebase, num_samples, segment_index, oversample)

    def get_timebase2(self, timebase, num_samples=0, segment_index=0, oversample=0):
        """
        This function is an upgraded version of :meth:`get_timebase`, and returns the time
        interval as a :class:`float` rather than an :class:`int`. This allows it to return
        sub-nanosecond time intervals. See :meth:`get_timebase` for a full description.

        The timebase that is returned is in **seconds** (not ns).

        The `oversample` argument is only used by ps4000, ps5000 and ps6000.
        """
        num_samples = int(num_samples)
        time_interval_nanoseconds = c_float()
        max_samples = c_uint32() if self.IS_PS6000 else c_int32()
        if self.IS_PS4000A or self.IS_PS5000A:
            self.GetTimebase2(self._handle, timebase, num_samples, byref(time_interval_nanoseconds),
                              byref(max_samples), segment_index)
        else:
            self.GetTimebase2(self._handle, timebase, num_samples, byref(time_interval_nanoseconds),
                              oversample, byref(max_samples), segment_index)
        return time_interval_nanoseconds.value*1e-9, max_samples.value

    def get_trigger_time_offset(self, segment_index=0):
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
        return time_upper.value, time_lower.value, self.enTimeUnits(time_units.value)

    def get_trigger_time_offset64(self, segment_index=0):
        """
        This function gets the time, as a single 64-bit value, at which the trigger occurred. Call
        it after block-mode data has been captured or when data has been retrieved from a
        previous block-mode capture. A 32-bit version of this function,
        :meth:`get_trigger_time_offset`, is also available.
        """
        time = c_int64()
        time_units = c_enum()
        self.GetTriggerTimeOffset64(self._handle, byref(time), byref(time_units), segment_index)
        return time.value, self.enTimeUnits(time_units.value)

    def get_values(self, num_samples=None, start_index=0, factor=1, ratio_mode='None', segment_index=0):
        """
        This function returns block-mode data, with or without down sampling, starting at the
        specified sample number. It is used to get the stored data from the driver after data
        collection has stopped.

        Parameters
        ----------
        num_samples : :class:`int` or :data:`None`, optional
            The number of samples required. If :data:`None` then automatically determine the
            number of samples to retrieve.
        start_index : :class:`int`, optional
            A zero-based index that indicates the start point for data collection.
            It is measured in sample intervals from the start of the buffer.
        factor : :class:`int`, optional
            The down-sampling factor that will be applied to the raw data.
        ratio_mode : :class:`enum.IntEnum`, optional
            Which down-sampling mode to use. A ``RatioMode`` enum.
        segment_index : :class:`int`, optional
            The zero-based number of the memory segment where the data is stored.
        """
        overflow = c_int16()
        if num_samples is None:
            num_samples = self._num_samples
        n_samples = c_uint32(num_samples)
        mode = self.convert_to_enum(ratio_mode, self.enRatioMode, to_upper=True)
        self.GetValues(self._handle, start_index, byref(n_samples), factor, mode, segment_index, byref(overflow))
        return n_samples.value, overflow.value

    def get_values_async(self, lp_data_ready, num_samples=None, start_index=0, factor=1, ratio_mode='None',
                         segment_index=0):
        """
        This function returns data either with or without down sampling, starting at the
        specified sample number. It is used to get the stored data from the scope after data
        collection has stopped. It returns the data using the ``lp_data_ready`` callback.

        Parameters
        ----------
        lp_data_ready : :mod:`callback <msl.equipment.resources.picotech.picoscope.callbacks>`
            A :mod:`DataReady callback <msl.equipment.resources.picotech.picoscope.callbacks>` function.
        num_samples : :class:`int`, optional
            The number of samples required. If :data:`None` then automatically determine the
            number of samples to retrieve.
        start_index : :class:`int`, optional
            A zero-based index that indicates the start point for data collection.
            It is measured in sample intervals from the start of the buffer.
        factor : :class:`int`, optional
            The downsampling factor that will be applied to the raw data.
        ratio_mode : :class:`enum.IntEnum`, optional
            Which down-sampling mode to use. A ``RatioMode`` enum.
        segment_index : :class:`int`, optional
            The zero-based number of the memory segment where the data is stored.
        """
        p_parameter = c_void_p()
        if num_samples is None:
            num_samples = self._num_samples
        mode = self.convert_to_enum(ratio_mode, self.enRatioMode, to_upper=True)
        self.GetValuesAsync(self._handle, start_index, num_samples, factor, mode,
                            segment_index, lp_data_ready, byref(p_parameter))

    def get_values_bulk(self, from_segment_index=0, to_segment_index=None, factor=1, ratio_mode='None'):
        """
        This function retrieves waveforms captured using rapid block mode. The waveforms
        must have been collected sequentially and in the same run.

        The `down_sample_ratio` and `down_sample_ratio_mode` arguments are ignored for
        ps4000 and ps5000.
        """
        assert self.get_no_of_captures() == self._num_captures
        if to_segment_index is None:
            to_segment_index = self._num_captures - 1
        num_segments = to_segment_index - from_segment_index + 1
        no_of_samples = c_uint32(self._num_samples * self._num_captures)
        overflow = (c_int16 * num_segments)()
        mode = self.convert_to_enum(ratio_mode, self.enRatioMode, to_upper=True)
        if self.IS_PS4000 or self.IS_PS5000:
            self.GetValuesBulk(self._handle, byref(no_of_samples), from_segment_index,
                               to_segment_index, overflow)
        else:
            self.GetValuesBulk(self._handle, byref(no_of_samples), from_segment_index,
                               to_segment_index, factor, mode, overflow)
        return no_of_samples.value, [v for v in overflow]

    def get_values_overlapped(self, start_index, down_sample_ratio, down_sample_ratio_mode, segment_index):
        """
        This function allows you to make a deferred data-collection request, which will later be
        executed, and the arguments validated, when you call :meth:`~.PicoScope.run_block` in block
        mode. The advantage of this function is that the driver makes contact with the scope
        only once, when you call :meth:`~.PicoScope.run_block`, compared with the two contacts that
        occur when you use the conventional :meth:`~.PicoScope.run_block`, :meth:`get_values` calling
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
        executed, and the arguments validated, when you call :meth:`~.PicoScope.run_block` in rapid
        block mode. The advantage of this method is that the driver makes contact with the
        scope only once, when you call :meth:`~.PicoScope.run_block`, compared with the two contacts
        that occur when you use the conventional :meth:`~.PicoScope.run_block`,
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
        self.GetValuesTriggerTimeOffsetBulk(self._handle, byref(times_upper), byref(times_lower),
                                            byref(time_units), from_segment_index, to_segment_index)
        return times_upper.value, times_lower.value, self.enTimeUnits(time_units.value)

    def get_values_trigger_time_offset_bulk64(self, from_segment_index=0, to_segment_index=None):
        """
        This function retrieves the 64-bit time offsets for waveforms captured in rapid block mode.

        A 32-bit version of this function, :meth:`get_values_trigger_time_offset_bulk`, is
        available for use with programming languages that do not support 64-bit integers
        """
        if to_segment_index is None:
            to_segment_index = self.get_no_of_captures() - 1
        n = to_segment_index - from_segment_index + 1
        times = (c_int64 * n)()
        units = (c_enum * n)()
        self.GetValuesTriggerTimeOffsetBulk64(self._handle, times, units, from_segment_index, to_segment_index)
        return list(times), [self.enTimeUnits(u) for u in units]

    def hold_off(self, holdoff, holdoff_type):
        """
        This function is for backward compatibility only and is not currently used.

        This function is only defined for ps2000a, ps3000a and ps4000.
        """
        return self.HoldOff(self._handle, holdoff, holdoff_type)

    def is_led_flashing(self):
        """
        This function reports whether or not the LED is flashing.

        This function is supported by ps4000, ps4000a and ps5000.
        """
        status = c_int16()
        self.IsLedFlashing(self._handle, byref(status))
        return status.value

    def _is_ready(self):
        """
        This function may be used instead of a callback function to receive data from
        :meth:`~.PicoScope.run_block`. To use this method, pass a NULL pointer as the lpReady
        argument to :meth:`~.PicoScope.run_block`. You must then poll the driver to see if it has finished
        collecting the requested samples.
        """
        ready = c_int16()
        self.IsReady(self._handle, byref(ready))
        return bool(ready.value)

    def is_trigger_or_pulse_width_qualifier_enabled(self):
        """
        This function discovers whether a trigger, or pulse width triggering, is enabled.
        """
        trigger_enabled = c_int16()
        pulse_width_qualifier_enabled = c_int16()
        self.IsTriggerOrPulseWidthQualifierEnabled(self._handle, byref(trigger_enabled),
                                                   byref(pulse_width_qualifier_enabled))
        return trigger_enabled.value, pulse_width_qualifier_enabled.value

    def memory_segments(self, num_segments):
        """
        This function sets the number of memory segments that the scope will use.
        When the scope is opened, the number of segments defaults to 1, meaning that each
        capture fills the scopes available memory. This function allows you to divide the
        memory into a number of segments so that the scope can store several waveforms
        sequentially.
        """
        num_max_samples = c_uint32() if self.IS_PS6000 else c_int32()
        self.MemorySegments(self._handle, num_segments, byref(num_max_samples))
        return num_max_samples.value

    def no_of_streaming_values(self):
        """
        This function returns the number of samples available after data collection in
        streaming mode. Call it after calling :meth:`~.PicoScope.stop`.
        """
        no_of_values = c_uint32()
        self.NoOfStreamingValues(self._handle, byref(no_of_values))
        return no_of_values.value

    def _get_optional_open_args(self, resolution):
        """Helper function for open_unit and open_unit_async"""

        # must call "convert_to_enum" before the "serial_ptr cast", otherwise we corrupt the pointer's memory
        if self.IS_PS5000A:
            res_enum = self.convert_to_enum(resolution, self.enDeviceResolution, prefix='RES_', to_upper=True)

        if self.equipment_record.serial:
            serial_ptr = cast(self.equipment_record.serial.encode(self.ENCODING), POINTER(c_int8))
        else:
            serial_ptr = None

        args = ()
        if not (self.IS_PS4000 or self.IS_PS5000):
            args += (serial_ptr,)  # these scopes take the serial as the second argument
        if self.IS_PS5000A:
            args += (res_enum,)  # the ps5000a takes a resolution as the third argument

        return args

    def open_unit(self, auto_select_power=True, resolution='8Bit'):
        """Open the PicoScope for communication.

        This function opens a PicoScope attached to the computer. The maximum number of
        units that can be opened depends on the operating system, the kernel driver
        and the computer.

        Parameters
        ----------
        auto_select_power : :class:`bool`, optional
            PicoScopes that can be powered by either DC power
            or by USB power may raise ``PICO_POWER_SUPPLY_NOT_CONNECTED`` if the DC power
            supply is not connected. Passing in :data:`True` will automatically switch to
            the USB power source.
        resolution : :class:`str`, optional
            The ADC resolution: 8, 12, 14, 15 or 16Bit. Only used by the PS5000A Series
            and it is ignored for all other PicoScope Series.
        """
        if self._handle is not None:
            self.log_warning('%s is already open', self._base_msg)
            return

        handle = c_int16()
        args = (byref(handle), ) + self._get_optional_open_args(resolution)
        ret = self.OpenUnit(*args)

        if handle.value > 0:
            self._handle = handle

        if ret == PICO_OK:
            self.log_debug('%s.open_unit%s', self.__class__.__name__, args)
            return ret

        if auto_select_power and ret == PICO_POWER_SUPPLY_NOT_CONNECTED:
            self.log_debug('%s.open_unit%s', self.__class__.__name__, args)
            return self.change_power_source(ret)  # the ret value is the correct power_state value

        # raise the exception
        self.errcheck_api(ret, self.open_unit, args)

    def open_unit_async(self, auto_select_power=True, resolution='8Bit'):
        """
        This function opens a scope without blocking the calling thread. You can find out when
        it has finished by periodically calling :meth:`open_unit_progress` until that function
        returns a value of 100.

        Parameters
        ----------
        auto_select_power : :class:`bool`, optional
            PicoScopes that can be powered by either DC power
            or by USB power may raise ``PICO_POWER_SUPPLY_NOT_CONNECTED`` if the DC power
            supply is not connected. Passing in :data:`True` will automatically switch to
            the USB power source.
        resolution : :class:`str`, optional
            The ADC resolution: 8, 12, 14, 15 or 16Bit. Only used by the PS5000A Series
            and it is ignored for all other PicoScope Series.
        """
        if self._handle is not None:
            self.log_warning('%s is already open', self._base_msg)
            return

        status = c_int16()
        opts = self._get_optional_open_args(resolution)
        self.OpenUnitAsync(byref(status), *opts)
        self._auto_select_power = auto_select_power
        if status.value == 0:
            self.raise_exception(
                'The open async operation was disallowed because another open operation is in progress'
            )
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

        if self._auto_select_power and ret == PICO_POWER_SUPPLY_NOT_CONNECTED:
            ret = self.change_power_source(ret)  # the ret value is the correct power_state value

        if ret == PICO_OK:
            return 100 if complete.value else progress_percent.value
        else:
            # raise the exception
            self.errcheck_api(ret, self.open_unit_progress, ())

    def _run_streaming(self, sample_interval, time_units, max_pre_trigger_samples, max_post_trigger_samples,
                       auto_stop, down_sample_ratio, down_sample_ratio_mode):
        """
        This function tells the oscilloscope to start collecting data in streaming mode. When
        data has been collected from the device it is down sampled if necessary and then
        delivered to the application. Call :meth:`get_streaming_latest_values` to retrieve the
        data. See Using streaming mode for a step-by-step guide to this process.

        When a trigger is set, the total number of samples stored in the driver is the sum of
        `max_pre_trigger_samples` and `max_post_trigger_samples`. If `auto_stop` is false then
        this will become the maximum number of samples without down sampling.

        The `down_sample_ratio_mode` argument is ignored for ps4000 and ps5000.
        """
        units = self.convert_to_enum(time_units, self.enTimeUnits, to_upper=True)
        mode = self.convert_to_enum(down_sample_ratio_mode, self.enRatioMode, to_upper=True)
        interval = c_uint32(sample_interval)
        if self.IS_PS4000 or self.IS_PS5000:
            self.RunStreaming(self._handle, byref(interval), units,
                              max_pre_trigger_samples, max_post_trigger_samples, auto_stop, down_sample_ratio,
                              self._buffer_size)
        else:
            self.RunStreaming(self._handle, byref(interval), units,
                              max_pre_trigger_samples, max_post_trigger_samples, auto_stop, down_sample_ratio,
                              mode, self._buffer_size)
        return interval.value

    def set_bandwidth_filter(self, channel, bandwidth):
        """
        This function is reserved for future use.

        This function is only valid for ps3000a, ps4000a and ps5000a.
        """
        ch = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        bw = self.convert_to_enum(bandwidth, self.enBandwidthLimiter, prefix='BW_', to_upper=True)
        return self.SetBandwidthFilter(self._handle, ch, bw)

    def set_data_buffer(self, channel, buffer=None, mode='None', segment_index=0):
        """Set the data buffer for the specified channel.

        The `mode` argument is ignored for ps4000 and ps5000.
        The `segment_index` argument is ignored for ps4000, ps5000 and ps6000.

        Parameters
        ----------
        channel : :class:`enum.IntEnum`
            An enum value or member name from ``Channel``.
        buffer : :class:`numpy.ndarray`, optional
            A int16, numpy array. If :data:`None` then use a pre-allocated array.
        mode : :class:`enum.IntEnum`, optional
            An enum value or member name from ``RatioMode``.
        segment_index : :class:`int`, optional
            The zero-based number of the memory segment where the data is stored.
        """
        ch = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        ratio_mode = self.convert_to_enum(mode, self.enRatioMode, to_upper=True)
        if buffer is None:
            buffer = self.channel[ch.name].buffer
            self._buffer_size = buffer.size

        if self.IS_PS4000 or self.IS_PS5000:
            return self.SetDataBuffer(self._handle, ch, buffer, buffer.size)
        elif self.IS_PS6000:
            return self.SetDataBuffer(self._handle, ch, buffer, buffer.size, ratio_mode)
        else:
            return self.SetDataBuffer(self._handle, ch, buffer, buffer.size, segment_index, ratio_mode)

    def set_data_buffer_bulk(self, channel, buffer, waveform, mode='None'):
        """
        This function allows you to associate a buffer with a specified waveform number and
        input channel in rapid block mode. The number of waveforms captured is determined
        by the ``nCaptures`` argument sent to :meth:`set_no_of_captures`. There is only one
        buffer for each waveform because the only down-sampling mode that requires two
        buffers, aggregation mode, is not available in rapid block mode. Call one of the
        GetValues functions to retrieve the data after capturing.

        This function is only valid for ps4000, ps5000 and ps6000.

        The `down_sample_ratio_mode` argument is ignored for ps4000 and ps5000.
        """
        ch = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        ratio_mode = self.convert_to_enum(mode, self.enRatioMode, to_upper=True)
        if self.IS_PS4000 or self.IS_PS5000:
            return self.SetDataBufferBulk(self._handle, ch, buffer, buffer.size, waveform)
        else:
            return self.SetDataBufferBulk(self._handle, ch, buffer, buffer.size, waveform, ratio_mode)

    def set_data_buffers(self, channel, buffer_length, mode, segment_index):
        """
        This function tells the driver where to store the data, either unprocessed or
        down sampled, that will be returned after the next call to one of the GetValues
        functions. The function allows you to specify only a single buffer, so for aggregation
        mode, which requires two buffers, you need to call :meth:`set_data_buffers` instead.

        You must allocate memory for the buffer before calling this function.

        The `mode` argument is ignored for ps4000 and ps5000.

        The `segment_index` argument is ignored for ps4000, ps5000 and ps6000.
        """
        buffer_max = c_int16()
        buffer_min = c_int16()
        if self.IS_PS4000 or self.IS_PS5000:
            self.SetDataBuffers(self._handle, channel, byref(buffer_max), byref(buffer_min), buffer_length)
        elif self.IS_PS6000:
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
        mode_ = self.convert_to_enum(mode, self.enEtsMode, to_upper=True)
        sample_time_picoseconds = c_int32()
        self.SetEts(self._handle, mode_, ets_cycles, ets_interleave, byref(sample_time_picoseconds))
        return sample_time_picoseconds.value

    def set_ets_time_buffer(self, buffer):
        """
        This function tells the driver where to find your applications ETS time buffers. These
        buffers contain the 64-bit timing information for each ETS sample after you run a
        block-mode ETS capture.

        Parameters
        ----------
        buffer : :class:`ctypes.c_longlong`
            An array of 64-bit words (:class:`ctypes.c_int64`), each representing the time,
            in picoseconds, at which the sample was captured.
        """
        return self.SetEtsTimeBuffer(self._handle, byref(buffer), len(buffer))

    def set_ets_time_buffers(self, time_upper, time_lower):
        """
        This function tells the driver where to find your applications ETS time buffers. These
        buffers contain the timing information for each ETS sample after you run a blockmode
        ETS capture. There are two buffers containing the upper and lower 32-bit parts
        of the timing information, to allow programming languages that do not support 64-bit
        data to retrieve the timings.
        """
        if len(time_upper) != len(time_lower):
            msg = 'len(time_upper) != len(time_lower) -- {} != {}'.format(len(time_upper) != len(time_lower))
            self.raise_exception(msg)
        return self.SetEtsTimeBuffers(self._handle, byref(time_upper), byref(time_lower), len(time_upper))

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
        ret = self.SetNoOfCaptures(self._handle, n_captures)
        self._num_captures = n_captures
        self._allocate_buffer_memory()
        return ret

    def set_sig_gen_arbitrary(self, waveform, repetition_rate=None, offset_voltage=0.0, pk_to_pk=None,
                              start_delta_phase=None, stop_delta_phase=None, delta_phase_increment=0,
                              dwell_count=None, sweep_type='up', operation='off', index_mode='single',
                              shots=None, sweeps=None, trigger_type='rising', trigger_source='None',
                              ext_in_threshold=0):
        """
        This function programs the signal generator to produce an arbitrary waveform.

        Parameters
        ----------
        waveform : :class:`numpy.ndarray`
            The arbitrary waveform, in volts.
        repetition_rate : :class:`float`, optional
            The requested repetition rate (frequency) of the entire arbitrary waveform. The actual
            repetition rate that is used may be different based on the specifications of the AWG.
            If specified then the :meth:`sig_gen_frequency_to_phase` method is called to determine
            the value of `start_delta_phase`.
        offset_voltage : :class:`float`, optional
            The voltage offset, in volts, to be applied to the waveform.
        pk_to_pk : :class:`float`, optional
            The peak-to-peak voltage, in volts, of the waveform signal. If :data:`None` then uses
            the maximum value of the waveform to determine the peak-to-peak voltage.
        start_delta_phase : :class:`int`, optional
            The initial value added to the phase accumulator as the generator begins
            to step through the waveform buffer.
        stop_delta_phase : :class:`int`, optional
            The final value added to the phase accumulator before the generator restarts or reverses
            the sweep. When frequency sweeping is not required, set equal to `start_delta_phase`.
        delta_phase_increment : :class:`int`, optional
            The amount added to the delta phase value every time the `dwell_count` period expires.
            This determines the amount by which the generator sweeps the output frequency in each
            dwell period. When frequency sweeping is not required, set to zero.
        dwell_count : :class:`int`, optional
            The time, in units of ``dacPeriod``, between successive additions of `delta_phase_increment`
            to the delta phase accumulator. This determines the rate at which the generator sweeps the
            output frequency.
        sweep_type : :class:`enum.IntEnum`, optional
            Whether the frequency will sweep from `start_frequency` to `stop_frequency`, or
            in the opposite direction, or repeatedly reverse direction. One of:  ``UP``, ``DOWN``,
            ``UPDOWN``, ``DOWNUP``
        operation : :class:`enum.IntEnum`, optional
            The type of waveform to be produced, specified by one of the following enumerated
            types (B models only): ``OFF``, ``WHITENOISE``, ``PRBS``
        index_mode : :class:`enum.IntEnum`, optional
            Specifies how the signal will be formed from the arbitrary waveform data. Possible values
            are ``SINGLE`` or ``DUAL``.
        shots : :class:`int`, optional
            If :data:`None` then start and run continuously after trigger occurs.
        sweeps : :class:`int`, optional
            If :data:`None` then start a sweep and continue after trigger occurs.
        trigger_type : :class:`enum.IntEnum`, optional
            The type of trigger that will be applied to the signal generator.
            One of: ``RISING``, ``FALLING``, ``GATE_HIGH``, ``GATE_LOW``.
        trigger_source : :class:`enum.IntEnum`, optional
            The source that will trigger the signal generator. If :data:`None` then run
            without waiting for trigger.
        ext_in_threshold : :class:`int`, optional
            Used to set trigger level for external trigger.

        Returns
        -------
        :class:`numpy.ndarray`
            The arbitrary waveform, in ADU.

        Raises
        ------
        ~msl.equipment.exceptions.PicoTechError
            If the value of an input parameter is invalid.
        """
        min_value, max_value, min_size, max_size = self.sig_gen_arbitrary_min_max_values()
        if waveform.size < min_size:
            self.raise_exception('The waveform size is {}, must be >= {}'.format(waveform.size, min_size))
        if waveform.size > max_size:
            self.raise_exception('The waveform size is {}, must be <= {}'.format(waveform.size, max_size))

        sweep_typ = self.convert_to_enum(sweep_type, self.enSweepType, to_upper=True)
        extra_ops = self.convert_to_enum(operation, self.enExtraOperations, to_upper=True)
        mode = self.convert_to_enum(index_mode, self.enIndexMode, to_upper=True)
        trig_typ = self.convert_to_enum(trigger_type, self.enSigGenTrigType, to_upper=True)
        trig_source = self.convert_to_enum(trigger_source, self.enSigGenTrigSource, to_upper=True)

        if start_delta_phase is None and repetition_rate is None:
            self.raise_exception('Must specify either "start_delta_phase" or "repetition_rate"')
        if start_delta_phase is None:
            start_delta_phase = self.sig_gen_frequency_to_phase(repetition_rate, mode, waveform.size)
        if stop_delta_phase is None:
            stop_delta_phase = start_delta_phase
        if dwell_count is None:
            dwell_count = self.MIN_DWELL_COUNT
        if shots is None:
            shots = self.SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN
        if sweeps is None:
            sweeps = self.SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN

        # convert the waveform from volts to analog-to-digital units
        waveform = waveform.copy()
        max_waveform_value = np.max(np.absolute(waveform))
        waveform /= max_waveform_value  # the waveform must be within the range -1.0 to 1.0
        waveform *= max_value
        waveform.round(out=waveform)
        waveform = waveform.astype(np.int16)

        if pk_to_pk is None:
            pk_to_pk = max_waveform_value * 2.0

        offset = int(round(offset_voltage * 1e6))
        pk2pk = int(round(pk_to_pk * 1e6))

        self.SetSigGenArbitrary(self._handle, offset, pk2pk, start_delta_phase, stop_delta_phase,
                                delta_phase_increment, dwell_count, waveform, waveform.size,
                                sweep_typ, extra_ops, mode, shots, sweeps, trig_typ, trig_source,
                                ext_in_threshold)
        return waveform

    def set_sig_gen_builtin(self, offset_voltage, pk_to_pk, wave_type, start_frequency, stop_frequency, increment,
                             dwell_time, sweep_type, operation, shots, sweeps, trigger_type, trigger_source,
                             ext_in_threshold):
        """
        This function sets up the signal generator to produce a signal from a list of built-in
        waveforms. If different start and stop frequencies are specified, the device will sweep
        either up, down or up and down. Call :meth:`set_sig_gen_builtin_v2` instead, which uses
        double-precision arguments.
        """
        return self.SetSigGenBuiltIn(self._handle, offset_voltage, pk_to_pk, wave_type, start_frequency,
                                     stop_frequency, increment, dwell_time, sweep_type, operation, shots, sweeps,
                                     trigger_type, trigger_source, ext_in_threshold)

    def set_sig_gen_builtin_v2(self, offset_voltage=0.0, pk_to_pk=1.0, wave_type='sine',
                                start_frequency=1.0, stop_frequency=None, increment=0.1, dwell_time=1.0,
                                sweep_type='up', operation='off', shots=None, sweeps=None,
                                trigger_type='rising', trigger_source='None', ext_in_threshold=0):
        """
        This function is an upgraded version of :meth:`set_sig_gen_builtin` with double-precision
        frequency arguments for more precise control at low frequencies.

        This function is invalid for ps4000 and ps4000a.

        Parameters
        ----------
        offset_voltage : :class:`float`, optional
            The voltage offset, in volts, to be applied to the waveform.
        pk_to_pk : :class:`float`, optional
            The peak-to-peak voltage, in volts, of the waveform signal.
        wave_type : :class:`enum.IntEnum`, optional
            The type of waveform to be generated. A ``WaveType`` enum.
        start_frequency : :class:`float`, optional
            The frequency that the signal generator will initially produce.
        stop_frequency : :class:`float`, optional
            The frequency at which the sweep reverses direction or returns to the initial frequency.
        increment : :class:`float`, optional
            The amount of frequency increase or decrease in sweep mode.
        dwell_time : :class:`float`, optional
            The time, in seconds, for which the sweep stays at each frequency.
        sweep_type : :class:`enum.IntEnum`, optional
            Whether the frequency will sweep from `start_frequency` to `stop_frequency`, or
            in the opposite direction, or repeatedly reverse direction. One of:  ``UP``, ``DOWN``,
            ``UPDOWN``, ``DOWNUP``
        operation : :class:`enum.IntEnum`, optional
            The type of waveform to be produced, specified by one of the following enumerated
            types (B models only): ``OFF``, ``WHITENOISE``, ``PRBS``
        shots : :class:`int`, optional
            If :data:`None` then start and run continuously after trigger occurs.
        sweeps : :class:`int`, optional
            If :data:`None` then start a sweep and continue after trigger occurs.
        trigger_type : :class:`enum.IntEnum`, optional
            The type of trigger that will be applied to the signal generator.
            One of: ``RISING``, ``FALLING``, ``GATE_HIGH``, ``GATE_LOW``.
        trigger_source : :class:`enum.IntEnum`, optional
            The source that will trigger the signal generator. If :data:`None` then run
            without waiting for trigger.
        ext_in_threshold : :class:`int`, optional
            Used to set trigger level for external trigger.
        """
        offset = int(round(offset_voltage*1e6))
        pk2pk = int(round(pk_to_pk*1e6))

        wave_typ = self.convert_to_enum(wave_type, self.enWaveType, to_upper=True)
        sweep_typ = self.convert_to_enum(sweep_type, self.enSweepType, to_upper=True)
        extra_ops = self.convert_to_enum(operation, self.enExtraOperations, to_upper=True)
        trig_typ = self.convert_to_enum(trigger_type, self.enSigGenTrigType, to_upper=True)
        trig_source = self.convert_to_enum(trigger_source, self.enSigGenTrigSource, to_upper=True)

        if stop_frequency is None:
            stop_frequency = start_frequency
        if shots is None:
            shots = self.SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN
        if sweeps is None:
            sweeps = self.SHOT_SWEEP_TRIGGER_CONTINUOUS_RUN

        return self.SetSigGenBuiltInV2(self._handle, offset, pk2pk, wave_typ, start_frequency,
                                       stop_frequency, increment, dwell_time, sweep_typ, extra_ops, shots, sweeps,
                                       trig_typ, trig_source, ext_in_threshold)

    def set_sig_gen_properties_arbitrary(self, start_delta_phase, stop_delta_phase, delta_phase_increment,
                                         dwell_count, sweep_type, shots, sweeps, trigger_type, trigger_source,
                                         ext_in_threshold, offset_voltage=0, pk_to_pk=-1):
        """
        This function reprograms the arbitrary waveform generator. All values can be
        reprogrammed while the signal generator is waiting for a trigger.

        The `offset_voltage` and `pk_to_pk` arguments are only used for ps6000.

        This function is invalid for ps4000 and ps5000.
        """
        if self.IS_PS6000:
            return self.SetSigGenPropertiesArbitrary(self._handle, offset_voltage, pk_to_pk,
                                                     start_delta_phase, stop_delta_phase, delta_phase_increment,
                                                     dwell_count, sweep_type, shots, sweeps, trigger_type,
                                                     trigger_source, ext_in_threshold)
        else:
            return self.SetSigGenPropertiesArbitrary(self._handle,
                                                     start_delta_phase, stop_delta_phase, delta_phase_increment,
                                                     dwell_count, sweep_type, shots, sweeps, trigger_type,
                                                     trigger_source, ext_in_threshold)

    def set_sig_gen_properties_builtin(self, start_frequency, stop_frequency, increment, dwell_time,
                                        sweep_type, shots, sweeps, trigger_type, trigger_source,
                                        ext_in_threshold, offset_voltage=0, pk_to_pk=-1):
        """
        This function reprograms the signal generator. Values can be changed while the signal
        generator is waiting for a trigger.

        The `offset_voltage` and `pk_to_pk` arguments are only used for ps6000.

        This function is invalid for ps4000 and ps5000.
        """
        if self.IS_PS6000:
            return self.SetSigGenPropertiesBuiltIn(self._handle, offset_voltage, pk_to_pk,
                                                   start_frequency, stop_frequency, increment, dwell_time,
                                                   sweep_type, shots, sweeps, trigger_type, trigger_source,
                                                   ext_in_threshold)
        else:
            return self.SetSigGenPropertiesBuiltIn(self._handle,
                                                   start_frequency, stop_frequency, increment, dwell_time,
                                                   sweep_type, shots, sweeps, trigger_type, trigger_source,
                                                   ext_in_threshold)

    def set_simple_trigger(self, enable, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function simplifies arming the trigger. It supports only the LEVEL trigger types
        and does not allow more than one channel to have a trigger applied to it. Any previous
        pulse width qualifier is cancelled.
        """
        return self.SetSimpleTrigger(self._handle, enable, source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger_channel_directions(self, a='rising', b='rising', c='rising', d='rising',
                                       ext='rising', aux='rising'):
        """
        This function sets the direction of the trigger for each channel.

        ps4000a overrides this method because it has a different implementation.
        """
        a_ = self.convert_to_enum(a, self.enThresholdDirection, to_upper=True)
        b_ = self.convert_to_enum(b, self.enThresholdDirection, to_upper=True)
        c_ = self.convert_to_enum(c, self.enThresholdDirection, to_upper=True)
        d_ = self.convert_to_enum(d, self.enThresholdDirection, to_upper=True)
        ext_ = self.convert_to_enum(ext, self.enThresholdDirection, to_upper=True)
        aux_ = self.convert_to_enum(aux, self.enThresholdDirection, to_upper=True)
        return self.SetTriggerChannelDirections(self._handle, a_, b_, c_, d_, ext_, aux_)

    def set_trigger_delay(self, delay):
        """
        This function sets the post-trigger delay, which causes capture to start a defined time
        after the trigger event.
        """
        return self.SetTriggerDelay(self._handle, delay)

    def sig_gen_arbitrary_min_max_values(self):
        """
        This function returns the range of possible sample values and waveform buffer sizes
        that can be supplied to :meth:`set_sig_gen_arbitrary` for setting up the arbitrary
        waveform generator (AWG).
        """
        min_value = c_int16()
        max_value = c_int16()
        min_size = c_uint32()
        max_size = c_uint32()
        self.SigGenArbitraryMinMaxValues(self._handle, byref(min_value), byref(max_value),
                                         byref(min_size), byref(max_size))
        return min_value.value, max_value.value, min_size.value, max_size.value

    def sig_gen_frequency_to_phase(self, repetition_rate, index_mode, buffer_length):
        """
        This function converts a frequency to a phase count for use with the arbitrary
        waveform generator (AWG). The value returned depends on the length of the buffer,
        the index mode passed and the device model. The phase count can then be sent to the
        driver through :meth:`set_sig_gen_arbitrary` or :meth:`set_sig_gen_properties_arbitrary`.

        Parameters
        ----------
        repetition_rate : :class:`float`
            The requested repetition rate (frequency) of the entire arbitrary waveform.
        index_mode : :class:`enum.IntEnum`
            An ``IndexMode`` enum value or member name.
        buffer_length : :class:`int`
            The size (number of samples) of the waveform.

        Returns
        -------
        :class:`int`
            The phase count.

        Raises
        ------
        ~msl.equipment.exceptions.PicoTechError
            If the value of an input parameter is invalid.
        """
        mode = self.convert_to_enum(index_mode, self.enIndexMode, to_upper=True)

        phase = c_uint32()
        self.SigGenFrequencyToPhase(self._handle, repetition_rate, mode, buffer_length, byref(phase))
        if phase.value < 1:
            self.raise_exception('The delta phase value is < 1. Increase the repetition rate value.')
        return phase.value

    def sig_gen_software_control(self, state):
        """
        This function causes a trigger event, or starts and stops gating. It is used when the
        signal generator is set to ``SOFT_TRIG``.
        """
        return self.SigGenSoftwareControl(self._handle, state)

    def trigger_within_pre_trigger_samples(self, state):
        """
        This function is in the header file, but it is not in the manual.

        This function is only valid for ps4000 and ps5000a.
        """
        return self.TriggerWithinPreTriggerSamples(self._handle, state)

    def set_trigger_channel_conditions(self, conditions, info='clear'):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is defined by
        one or more ``TriggerConditions`` structures, which are found in the
        :mod:`~msl.equipment.resources.picotech.picoscope.structs` module, that are then ``ORed``
        together. Each structure is itself the ``AND`` of the states of one or more of the inputs.
        This ``AND-OR`` logic allows you to create any possible Boolean function of the scope's
        inputs.

        The `info` parameter is only used for ps4000a and it is a ``PS4000AConditionsInfo`` enum.
        """
        if self.IS_PS4000A:
            info = self.convert_to_enum(info, self.enConditionsInfo, to_upper=True)
            ret = self.sdk.ps4000aSetTriggerChannelConditions(self._handle, byref(conditions),
                                                              len(conditions), info)
        else:
            ret = self.SetTriggerChannelConditions(self._handle, byref(conditions), len(conditions))
        return ret

    def set_trigger_channel_properties(self, channel_properties, timeout=0.1, aux_output_enable=0):
        """
        This function is used to enable or disable triggering and set its parameters.

        Parameters
        ----------
        channel_properties : :class:`list` of ``TriggerChannelProperties`` :mod:`~msl.equipment.resources.picotech.picoscope.structs`
            A list of ``TriggerChannelProperties`` structures describing the requested properties.
        timeout : :class:`float`, optional
            The time, in seconds, for which the scope device will wait before collecting data
            if no trigger event occurs. If this is set to zero, the scope device will wait
            indefinitely for a trigger.
        aux_output_enable : :class:`int`, optional
            Zero configures the AUXIO connector as a trigger input. Any other value configures
            it as a trigger output. Only used by ps5000.
        """
        auto_trigger_ms = int(round(max(0.0, timeout * 1e3)))
        return self.SetTriggerChannelProperties(self._handle, byref(channel_properties),
                                                len(channel_properties), aux_output_enable, auto_trigger_ms)
