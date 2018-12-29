"""
Base class for the ps2000 and ps3000 PicoScopes.
"""
from ctypes import c_int16, c_int32, c_uint32, c_double, byref

from msl.equipment.exceptions import PicoTechError
from .enums import PS2000Info
from .picoscope import PicoScope
from ..errors import ERROR_CODES


class PicoScope2k3k(PicoScope):

    def __init__(self, record, func_ptrs):
        """Use the PicoScope SDK to communicate with ps2000 and ps3000 oscilloscopes.        

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment_database`.
        func_ptrs : :mod:`.functions`
            The appropriate function-pointer list for the SDK. 
        """
        super(PicoScope2k3k, self).__init__(record, func_ptrs)
        self.enPicoScopeInfo = PS2000Info  # PS2000Info enum == PS3000Info enum

        # check the equipment_record.connection.properties dictionary to see how to initialize the PicoScope
        properties = self.equipment_record.connection.properties

        open_unit = properties.get('open', True)
        open_unit_async = properties.get('open_async', None)

        if open_unit and open_unit_async is None:
            self.open_unit()
        elif open_unit_async:
            self.open_unit_async()

        raise PicoTechError('The {} class has not yet been tested with a PicoScope'.format(self.__class__.__name__))

    def errcheck_zero(self, result, func, args):
        """If the SDK function returns 0 then raise an exception."""
        self.log_errcheck(result, func, args)
        if result == 0:
            self._raise()
        return result

    def errcheck_one(self, result, func, args):
        """If the SDK function returns 1 then raise an exception."""
        self.log_errcheck(result, func, args)
        if result == 1:
            self._raise()
        return result

    def errcheck_negative_one(self, result, func, args):
        """If the SDK function returns -1 then raise an exception."""
        self.log_errcheck(result, func, args)
        if result == -1:
            self._raise()
        return result

    def _raise(self, msg=None, error_code=None):
        """
        Raise an exception.
        
        If ``msg`` is not :py:data:`None` then display this message.
        
        If ``error_code`` is not :py:data:`None` then display the corrseponding error message 
        that is specified in the programmers manual.
        
        If both ``msg`` and ``error_code`` are :py:data:`None` then calls the :meth:`get_unit_info`
        method to get the last error message from the PicoScope *(this has not been tested yet)*.
        
        Parameters
        ----------
        msg : :class:`str`, optional
            The error message.
        error_code : :class:`int`, optional
            A number from 0 to 7 (see the programmers manual).
        """
        conn = self.equipment_record.connection

        if msg is not None:
            self.raise_exception(msg)

        if error_code is not None:
            if error_code < 0 or error_code > 7:
                msg = 'Invalid error code of {}. The value must be from 0 to 7. ' \
                      'See the programmers guide for details.'. format(error_code)
                self.raise_exception(msg)
        else:
            if self._handle is None:
                msg = 'A connection has not been opened yet. Call open_unit()'
                self.raise_exception(msg)
            error_code = int(self.get_unit_info(6))  # passing in line=6 returns one of the error codes

        error_name, message = ERROR_CODES.get(error_code, ('UnhandledError', 'Error code 0x{:x}'.format(error_code)))
        message = message.format(
            model=conn.model,
            serial=conn.serial,
            sdk_filename=self.SDK_FILENAME,
            sdk_filename_upper=self.SDK_FILENAME.upper()
        )
        msg = '{}: {}'.format(error_name, message)
        self.raise_exception(msg)

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

    def get_timebase(self, timebase, no_of_samples, oversample=0):
        """
        This function discovers which timebases are available on the oscilloscope. You should
        set up the channels using :meth:`~.PicoScope.set_channel` and, if required, ETS mode using
        :meth:`set_ets` first. Then call this function with increasing values of timebase,
        starting from 0, until you find a timebase with a sampling interval and sample count
        close enough to your requirements.
        """
        time_interval = c_int32()
        time_units = c_int16()
        max_samples = c_int32()
        ret = self.GetTimebase(self._handle, timebase, no_of_samples, byref(time_interval),
                               byref(time_units), oversample, byref(max_samples))
        if ret == 0:
            self._raise()
        return time_interval.value*1e-9, max_samples.value, time_units.value

    def get_times_and_values(self, time_units, no_of_values):
        """
        This function is used to get values and times in block mode after calling
        :meth:`~.PicoScope.run_block`.
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

    def get_values(self, num_values):
        """
        This function is used to get values in compatible streaming mode after calling
        :meth:`~.PicoScope.run_streaming`, or in block mode after calling :meth:`~.PicoScope.run_block`.
        """
        buffer_a = c_int16()
        buffer_b = c_int16()
        buffer_c = c_int16()
        buffer_d = c_int16()
        overflow = c_int16()
        ret = self.GetValues(self._handle, byref(buffer_a), byref(buffer_b), byref(buffer_c), byref(buffer_d),
                             byref(overflow), num_values)
        return ret, (buffer_a.value, buffer_b.value, buffer_c.value, buffer_d.value, overflow.value)

    def open_unit(self):
        """
        This function opens a PicoScope 2000/3000 Series oscilloscope. The driver can support up to
        64 oscilloscopes.
        """
        if self._handle is not None:
            return

        ret = self.OpenUnit()
        if ret > 0:
            self._handle = c_int16(ret)
        else:
            self._raise(error_code=3)
        return ret

    def open_unit_async(self):
        """
        This function opens a PicoScope 2000/3000 Series oscilloscope without waiting for the
        operation to finish. You can find out when it has finished by periodically calling
        :meth:`open_unit_progress`, which returns a value of 100 when the scope is open.
        
        The driver can support up to 64 oscilloscopes.
        """
        if self._handle is not None:
            return

        ret = self.OpenUnitAsync()
        if ret == 0:
            self.raise_exception('A previous open operation is already in progress.')
        return ret

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
            if handle.value > 0:
                self._handle = handle
                return 100
            self._raise(error_code=3)
        elif ret == 0:
            return progress_percent.value
        else:
            self._raise(error_code=3)

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

    def _is_ready(self):
        """
        This function checks to see if the oscilloscope has finished the last data collection
        operation.
        """
        ret = self.Ready(self._handle)
        if ret > 0:
            return True
        elif ret == 0:
            return False
        else:
            self._raise()

    def _run_streaming(self, sample_interval_ms, max_samples, windowed):
        """
        This function tells the oscilloscope to start collecting data in compatible streaming
        mode. If this function is called when a trigger has been enabled, the trigger settings
        will be ignored.
        """
        return self.RunStreaming(self._handle, sample_interval_ms, max_samples, windowed)

    def run_streaming_ns(self, sample_interval, time_units, max_samples, auto_stop, no_of_samples_per_aggregate,
                         overview_buffer_size):
        """
        This function tells the scope unit to start collecting data in fast streaming mode .
        The function returns immediately without waiting for data to be captured. After calling
        this function, you should next call :meth:`get_streaming_last_values` to copy the
        data to your application's buffer.
        """
        return self.RunStreamingNs(self._handle, sample_interval, time_units, max_samples, auto_stop,
                                   no_of_samples_per_aggregate, overview_buffer_size)

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

    def set_ets(self, mode, ets_cycles, ets_interleave):
        """
        This function is used to enable or disable ETS (equivalent time sampling) and to set
        the ETS parameters.
        """
        return self.SetEts(self._handle, mode, ets_cycles, ets_interleave)

    def set_trigger(self, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function just calls :meth:`set_trigger2`, since Python supports a 
        floating-point value for defining the ``delay`` parameter.
        """
        return self.set_trigger2(source, threshold, direction, delay, auto_trigger_ms)

    def set_trigger2(self, source, threshold, direction, delay, auto_trigger_ms):
        """
        This function is used to enable or disable triggering and its parameters. It has the
        same behaviour as :meth:`set_trigger`, except that the delay parameter is a floating-point value.
        
        For oscilloscopes that support advanced triggering, see :meth:`set_adv_trigger_channel_conditions` 
        and related functions.
        """
        return self.SetTrigger2(self._handle, source, threshold, direction, delay, auto_trigger_ms)

    def set_adv_trigger_channel_properties(self, channel_properties, auto_trigger_milliseconds):
        """This function is used to enable or disable triggering and set its parameters."""
        return self.SetAdvTriggerChannelProperties(self._handle, byref(channel_properties),
                                                   len(channel_properties), auto_trigger_milliseconds)

    def set_adv_trigger_channel_conditions(self, conditions):
        """
        This function sets up trigger conditions on the scope's inputs. The trigger is set up by
        defining a list of ``TriggerConditions`` structures, which are found in the
        :mod:`~msl.equipment.resources.picotech.picoscope.structs` module. Each structure
        is the ``AND`` of the states of one scope input.
        """
        return self.SetAdvTriggerChannelConditions(self._handle, byref(conditions), len(conditions))
