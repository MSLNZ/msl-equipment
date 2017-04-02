"""
This :class:`~.picoscope.PicoScope` subclass implements the common functions 
for the ps2000 and ps3000 PicoScopes.
"""
from ctypes import (c_int8, c_int16, c_int32, c_uint32, c_double,
                    byref, string_at, addressof)

from .picoscope import PicoScope
from .error_codes import PicoScopeError, ERROR_CODES


class PicoScope2k3k(PicoScope):

    def __init__(self, record, funcptrs):
        """
        Use the PicoScope SDK to communicate with ps2000 and ps3000 oscilloscopes.

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
        self.log.warning('The {} class has not been tested'.format(self.__class__.__name__))

    def _raise_error(self, message=None):
        """
        Raise an exception. Not tested.
        """
        conn = self.equipment_record.connection
        if message is None:
            code = int(self.get_unit_info(6))  # passing in line=6 returns one of the error codes
            error_name, msg = ERROR_CODES[code]
            error_msg = msg.format(
                model=conn.model,
                serial=conn.serial,
                sdk_filename=self._sdk_filename,
                sdk_filename_upper=self._sdk_filename.upper()
            )
            error_message = '{}: {}'.format(error_name, error_msg)
        else:
            error_message = '{}; {}\n{}'.format(self.__class__.__name__, conn, message)
        raise PicoScopeError(error_message)

    def flash_led(self):
        """
        Flashes the LED on the front of the oscilloscope three times and returns 
        within one second.
        """
        return self.FlashLed(self._handle)

    def get_streaming_last_values(self, lp_get_overview_buffers_max_min):
        """
        This function is used to collect the next block of values while fast streaming is
        running. You must call :meth:`run_streaming_ns` beforehand to set up fast
        streaming.
        """
        return self.GetStreamingValues(self._handle, lp_get_overview_buffers_max_min)

    def get_streaming_values(self, no_of_values, no_of_samples_per_aggregate):
        """
        This function is used after the driver has finished collecting data in fast streaming
        mode. It allows you to retrieve data with different aggregation ratios, and thus zoom
        in to and out of any region of the data.
        """
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
        ret = self.GetStreamingValues(self._handle, byref(start_time), byref(pbuffer_a_max),
                                      byref(pbuffer_a_min), byref(pbuffer_b_max), byref(pbuffer_b_min),
                                      byref(pbuffer_c_max), byref(pbuffer_c_min), byref(pbuffer_d_max),
                                      byref(pbuffer_d_min), byref(overflow), byref(trigger_at),
                                      byref(triggered), no_of_values, no_of_samples_per_aggregate)
        return ret, (start_time.value, pbuffer_a_max.value, pbuffer_a_min.value, pbuffer_b_max.value,
                pbuffer_b_min.value, pbuffer_c_max.value, pbuffer_c_min.value, pbuffer_d_max.value,
                pbuffer_d_min.value, overflow.value, trigger_at.value, triggered.value)

    def get_streaming_values_no_aggregation(self, no_of_values):
        """
        This function retrieves raw streaming data from the driver's data store after fast
        streaming has stopped.
        """
        start_time = c_double()
        pbuffer_a = c_int16()
        pbuffer_b = c_int16()
        pbuffer_c = c_int16()
        pbuffer_d = c_int16()
        overflow = c_int16()
        trigger_at = c_uint32()
        trigger = c_int16()
        ret = self.GetStreamingValuesNoAggregation(self._handle, byref(start_time), byref(pbuffer_a), byref(pbuffer_b),
                                                   byref(pbuffer_c), byref(pbuffer_d), byref(overflow),
                                                   byref(trigger_at), byref(trigger), no_of_values)
        return ret, (start_time.value, pbuffer_a.value, pbuffer_b.value, pbuffer_c.value, pbuffer_d.value,
                     overflow.value, trigger_at.value, trigger.value)

    def get_timebase(self, timebase, no_of_samples, oversample):
        """
        This function discovers which timebases are available on the oscilloscope. You should
        set up the channels using :meth:`set_channel` and, if required, ETS mode using
        :meth:`set_ets` first. Then call this function with increasing values of timebase,
        starting from 0, until you find a timebase with a sampling interval and sample count
        close enough to your requirements.
        """
        time_interval = c_int32()
        time_units = c_int16()
        max_samples = c_int32()
        ret = self.GetTimebase(self._handle, timebase, no_of_samples, byref(time_interval),
                               byref(time_units), oversample, byref(max_samples))
        return ret, (time_interval.value, time_units.value, max_samples.value)

    def get_times_and_values(self, time_units, no_of_values):
        """
        This function is used to get values and times in block mode after calling
        :meth:`run_block`.
        """
        times = c_int32()
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        ret = self.GetTimesAndValues(self._handle, byref(times), byref(buffer_a), byref(buffer_b),
                                     byref(buffer_c), byref(buffer_d), byref(overflow), time_units, no_of_values)
        return ret, (times.value, buffer_a.value, buffer_b.value, buffer_c.value, buffer_d.value, overflow.value)

    def get_unit_info(self, line):
        """
        This function writes oscilloscope information to a character string. If the oscilloscope
        failed to open, only line types 0 and 6 are available to explain why the last open unit
        call failed.
        """
        string = c_int8(127)
        ret = self.GetUnitInfo(self._handle, byref(string), string.value, line)
        if ret > 0:
            return string_at(addressof(string)).decode('utf-8')
        self._raise_error()

    def get_values(self, no_of_values):
        """
        This function is used to get values in compatible streaming mode after calling
        :meth:`run_streaming`, or in block mode after calling :meth:`run_block`.
        """
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        ret = self.GetValues(self._handle, byref(buffer_a), byref(buffer_b), byref(buffer_c), byref(buffer_d),
                             byref(overflow), no_of_values)
        return ret, (buffer_a.value, buffer_b.value, buffer_c.value, buffer_d.value, overflow.value)

    def open_unit(self):
        """
        This function opens a PicoScope 2000/3000 Series oscilloscope. The driver can support up to
        64 oscilloscopes.
        """
        ret = self.OpenUnit()
        if ret > 0:
            self._handle = c_int16(ret)
        else:
            self._raise_open_error()
        return ret

    def open_unit_async(self):
        """
        This function opens a PicoScope 2000/3000 Series oscilloscope without waiting for the
        operation to finish. You can find out when it has finished by periodically calling
        :meth:`open_unit_progress` until that function returns a non-zero value and a valid
        oscilloscope handle.
        
        The driver can support up to 64 oscilloscopes.
        """
        return self.OpenUnitAsync()

    def open_unit_progress(self):
        """
        This function checks on the progress of :meth:`open_unit_async`.
        
        The function will return a value from 0 to 100, where 100 implies 
        that the operation is complete.
        """
        handle = c_int16()
        progress_percent = c_int16()
        ret = self.OpenUnitProgress(byref(handle), byref(progress_percent))
        if ret > 0:
            if handle.value < 1:
                self._raise_open_error()
            self._handle = handle
            return 100
        elif ret == 0:
            return progress_percent.value
        else:
            self._raise_open_error()

    def overview_buffer_status(self):
        """
        This function indicates whether or not the overview buffers used by
        :meth:`run_streaming_ns` have overrun. If an overrun occurs, you can choose to
        increase the overview_buffer_size argument that you pass in the next call to
        :meth:`run_streaming_ns`.        
        """
        previous_buffer_overrun = c_int16()
        ret = self.OverviewBufferStatus(self._handle, byref(previous_buffer_overrun))
        return ret.value, previous_buffer_overrun.value

    def ready(self):
        """
        This function checks to see if the oscilloscope has finished the last data collection
        operation.
        """
        return self.Ready(self._handle)

    def run_block(self, no_of_values, timebase, oversample):
        """
        This function tells the oscilloscope to start collecting data in block mode.
        """
        time_indisposed_ms = c_int32()
        ret = self.RunBlock(self._handle, no_of_values, timebase, oversample, byref(time_indisposed_ms))
        return ret.value, time_indisposed_ms.value

    def run_streaming(self, sample_interval_ms, max_samples, windowed):
        """
        This function tells the oscilloscope to start collecting data in compatible streaming
        mode. If this function is called when a trigger has been enabled, the trigger settings
        will be ignored.
        """
        return self.RunStreaming(self._handle, sample_interval_ms, max_samples, windowed)

    def set_adv_trigger_channel_directions(self, channel_a, channel_b, channel_c, channel_d, ext):
        """
        This function sets the direction of the trigger for each channel.
        """
        return self.SetAdvTriggerChannelDirections(self._handle, channel_a, channel_b, channel_c, channel_d, ext)

    def set_adv_trigger_delay(self, delay, pre_trigger_delay):
        """
        This function sets the pre-trigger and post-trigger delays. The default action, when
        both these delays are zero, is to start capturing data beginning with the trigger event
        and to stop a specified time later. The start of capture can be delayed by using a nonzero
        value of ``delay``. Alternatively, the start of capture can be advanced to a time
        before the trigger event by using a negative value of ``pre_trigger_delay``. If both
        arguments are non-zero then their effects are added together.
        """
        return self.SetAdvTriggerDelay(self._handle, delay, pre_trigger_delay)

    def set_channel(self, channel, enabled, dc, range_enum):
        """
        Specifies if a channel is to be enabled, the AC/DC coupling mode and the input range.
        
        Note: The channels are not configured until capturing starts.
        """
        return self.SetChannel(self._handle, channel, enabled, dc, range_enum)

    def set_ets(self, mode, ets_cycles, ets_interleave):
        """
        This function is used to enable or disable ETS (equivalent time sampling) and to set
        the ETS parameters.
        """
        return self.SetEts(self._handle, mode, ets_cycles, ets_interleave)

    def set_trigger(self, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function is used to enable or disable basic triggering and its parameters.
        For oscilloscopes that support advanced triggering, see :meth:`set_adv_trigger_channel_conditions`, 
        :meth:`set_adv_trigger_delay` and related functions.
        """
        return self.SetTrigger(self._handle, source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger2(self, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function is used to enable or disable triggering and its parameters. It has the
        same behaviour as :meth:`set_trigger`, except that the delay parameter is a floating-point value.
        
        For oscilloscopes that support advanced triggering, see :meth:`set_adv_trigger_channel_conditions` 
        and related functions.
        """
        return self.SetTrigger2(self._handle, source, threshold, direction, delay, auto_trigger_ms)
