"""
Base class for a PicoScope from Pico Technology.
"""
from __future__ import annotations

import os
import re
import time
from ctypes import addressof
from ctypes import byref
from ctypes import c_int16
from ctypes import c_int32
from ctypes import c_int8
from ctypes import c_void_p
from ctypes import string_at

from msl.loadlib import LoadLibrary

from msl.equipment.connection_sdk import ConnectionSDK
from msl.equipment.constants import IS_WINDOWS
from msl.equipment.exceptions import PicoTechError
from . import callbacks
from . import enums
from . import structs
from .channel import PicoScopeChannel
from ..errors import ERROR_CODES_API
from ..errors import PICO_NOT_FOUND
from ..errors import PICO_OK

ALLOWED_SDKs = ('ps2000', 'ps2000a', 'ps3000', 'ps3000a', 'ps4000', 'ps4000a', 'ps5000', 'ps5000a', 'ps6000')


def enumerate_units():
    """Find the PicoScopes that are connected to the computer.

    This function counts the number of PicoScopes connected to the
    computer, and returns a list of serial numbers as a string.

    Note
    ----
    You cannot call this function after you have opened a connection to a PicoScope.

    Returns
    -------
    :class:`list` of :class:`str`
        A list of serial numbers of the PicoScopes that were found.
    """
    count = c_int16()
    size = c_int16(1023)
    serials = (c_int8 * size.value)()
    libtype = 'windll' if IS_WINDOWS else 'cdll'
    sdk = LoadLibrary('ps5000a', libtype)
    result = sdk.lib.ps5000aEnumerateUnits(byref(count), byref(serials), byref(size))
    if result != PICO_OK:
        if result == PICO_NOT_FOUND:
            err_name, err_msg = 'PICO_NOT_FOUND', 'Are you sure that a PicoScope is connected to the computer?'
        else:
            err_name, err_msg = ERROR_CODES_API.get(result, ('UnhandledError', 'Error code 0x{:x}'.format(result)))
        raise PicoTechError('Cannot enumerate units.\n{}: {}'.format(err_name, err_msg))
    return string_at(addressof(serials)).decode('utf-8').split(',')


class PicoScope(ConnectionSDK):

    def __init__(self, record, func_ptrs):
        """Use the PicoScope SDK to communicate with the oscilloscope.

        The :attr:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a PicoScope connection supports the following key-value pairs in the
        :ref:`connections-database`::

            'open': bool, Whether to open the connection synchronously [default: True]
            'open_async': bool, Whether to open the connection asynchronously [default: False]
            'auto_select_power': bool, For devices that can be powered by an AC adaptor or a USB cable [default: True]
            'resolution': str, Only valid for ps5000a [default: '8bit']

        The SDK version that was initially used to create this base class and the PicoScope
        subclasses was *Pico Technology SDK 64-bit v10.6.10.24*

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~.EquipmentRecord`
            A record from an :ref:`equipment-database`.
        func_ptrs : :mod:`.functions`
            The appropriate function-pointer list for the SDK.
        """
        self._handle = None
        libtype = 'windll' if IS_WINDOWS else 'cdll'
        super(PicoScope, self).__init__(record, libtype)
        self.set_exception_class(PicoTechError)

        # check that the Python class matches the SDK
        self.SDK_FILENAME = os.path.splitext(os.path.basename(record.connection.address[5:]))[0]
        if self.SDK_FILENAME != self.__class__.__name__.replace('PicoScope', 'ps').lower():
            msg = 'Using the wrong PicoScope SDK file {} for {}.'.format(self.SDK_FILENAME, self.__class__.__name__)
            self.raise_exception(msg)

        if self.SDK_FILENAME not in ALLOWED_SDKs:
            msg = "Invalid SDK '{}'\nMust be one of {}".format(self.SDK_FILENAME, ALLOWED_SDKs)
            self.raise_exception(msg)

        # initialize parameters and constants
        self.ENCODING = 'utf-8'
        self.IS_PS2000  = self.SDK_FILENAME == 'ps2000'
        self.IS_PS2000A = self.SDK_FILENAME == 'ps2000a'
        self.IS_PS3000  = self.SDK_FILENAME == 'ps3000'
        self.IS_PS3000A = self.SDK_FILENAME == 'ps3000a'
        self.IS_PS4000  = self.SDK_FILENAME == 'ps4000'
        self.IS_PS4000A = self.SDK_FILENAME == 'ps4000a'
        self.IS_PS5000  = self.SDK_FILENAME == 'ps5000'
        self.IS_PS5000A = self.SDK_FILENAME == 'ps5000a'
        self.IS_PS6000  = self.SDK_FILENAME == 'ps6000'

        self._channels_dict = {}  # a dictionary of PicoScopeChannel objects

        # the following are re-defined by calling set_timebase()
        self._sampling_interval = None
        self._streaming_sampling_interval = None
        self._max_samples = None
        self._num_samples = None
        self._timebase_index = None
        self._oversample = None
        self._time_units = None
        self._streaming_time_units = None

        self._num_captures = 1
        self._pre_trigger = 0.0

        # set the PicoScope SDK function signatures
        self._func_ptrs = func_ptrs
        for item in func_ptrs:
            name, alias, res, err, args = item
            func = getattr(self.sdk, name)
            func.restype = res
            if err is not None:
                func.errcheck = getattr(self, err)
            func.argtypes = [value[0] for value in args]
            # The following allows for code re-usability by solving the "problem" that
            # the SDK functions have a different name but do the same task. A
            # solution is to use the 'alias' that was created to call each SDK function.
            #
            # For example, all PicoScopes have a "close unit" function but the SDK
            # function signatures are:
            #   ps2000_close_unit(int16_t handle)
            #   ps2000aCloseUnit(int16_t handle)
            #   ps3000_close_unit(int16_t handle)
            #   ps3000aCloseUnit(int16_t handle)
            #   ps4000CloseUnit(int16_t handle)
            #   ps4000aCloseUnit(int16_t handle)
            #   ps5000CloseUnit(int16_t handle)
            #   ps5000aCloseUnit(int16_t handle)
            #   ps6000CloseUnit(int16_t handle)
            # where, in this case, alias='CloseUnit' and the Python-to-SDK implementation
            # is simply to use self.CloseUnit(int16_t handle)
            setattr(self, alias, func)

        # Similarly, set an alias for the structs and enums
        name = self.SDK_FILENAME.upper()
        for item in dir(enums):
            if item.startswith(name):
                setattr(self, 'en'+item.replace(name, ''), getattr(enums, item))
        for item in dir(structs):
            if item.startswith(name):
                setattr(self, 'st'+item.replace(name, ''), getattr(structs, item))

        # Similarly, set the callbacks
        for item in dir(callbacks):
            if item.startswith(self.SDK_FILENAME):
                setattr(self, item.replace(self.SDK_FILENAME, ''), getattr(callbacks, item))

        conn = self.equipment_record.connection
        self._base_msg = 'PicoScope<model={}, serial={}>'.format(conn.model, conn.serial)

    @property
    def handle(self):
        """:class:`int`: Returns the handle to the SDK library."""
        return self._handle

    @property
    def channel(self):
        """:class:`dict` of :class:`~.channel.PicoScopeChannel`: The information about each channel."""
        return self._channels_dict

    @property
    def dt(self):
        """:class:`float`: The time between voltage samples (i.e., delta t)."""
        return self._sampling_interval

    @property
    def pre_trigger(self):
        """:class:`float`: The number of seconds that data was acquired for before the trigger event."""
        return self._pre_trigger

    def _allocate_buffer_memory(self):
        """Allocate memory for the numpy array for each channel."""
        for channel in self._channels_dict.values():
            if channel.enabled:
                channel.allocate(self._num_captures, self._num_samples)

    def close_unit(self):
        """Disconnect from the PicoScope."""
        self.disconnect()

    def disconnect(self):
        """Disconnect from the PicoScope."""
        if self._handle is not None:
            self.CloseUnit(self._handle)
            self.log_debug('Disconnected from %s', self.equipment_record.connection)
            self._handle = None

    def get_unit_info(self, info=None, include_name=True):
        """Retrieves information about the PicoScope.

        This function retrieves information about the specified oscilloscope. If the device
        fails to open, or no device is opened only the driver version is available.

        Parameters
        ----------
        info : :class:`~.enums.PicoScopeInfoApi`, :class:`~.enums.PS2000Info` or :class:`~.enums.PS3000Info`, optional
            An enum value, or if :data:`None` then request all information from the PicoScope.
            The enum depends on the model number of the PicoScope that you are connected to.
        include_name : :class:`bool`, optional
            If :data:`True` then includes the enum member name as a prefix.
            For example, returns ``'CAL_DATE: 09Aug16'`` if `include_name` is :data:`True` else ``'09Aug16'``.

        Returns
        -------
        :class:`str`
            The requested information from the PicoScope.
        """
        if info is None:
            values = [self.enPicoScopeInfo(i) for i in range(len(self.enPicoScopeInfo))]
        else:
            values = [self.convert_to_enum(info, self.enPicoScopeInfo, to_upper=True)]

        string = c_int8(127)
        required_size = c_int16()

        msg = ''
        for value in values:
            name = '{}: '.format(value.name) if include_name else ''
            if self.IS_PS2000 or self.IS_PS3000:
                self.GetUnitInfo(self._handle, byref(string), string.value, value)
            else:
                self.GetUnitInfo(self._handle, byref(string), string.value, byref(required_size), value)
            msg += '{}{}\n'.format(name, string_at(addressof(string)).decode(self.ENCODING))
        return msg[:-1]

    def is_ready(self):
        """Has the PicoScope collecting the requested number of samples?

        This function may be used instead of a callback function to receive data from
        :meth:`run_block`. To use this method, pass :data:`None` as the callback parameter
        in :meth:`run_block`. You must then poll the driver to see if it has finished
        collecting the requested samples.

        Returns
        -------
        :class:`bool`
            Whether the PicoScope has collected the requested number of samples.
        """
        return self._is_ready()

    def maximum_value(self):
        """:class:`int`: This function returns the maximum ADC count."""
        try:
            max_value = c_int16()
            self.MaximumValue(self._handle, byref(max_value))
            return max_value.value
        except AttributeError:
            return self.MAX_VALUE

    def minimum_value(self):
        """:class:`int`: This function returns the minimum ADC count."""
        try:
            min_value = c_int16()
            self.MinimumValue(self._handle, byref(min_value))
            return min_value.value
        except AttributeError:
            return self.MIN_VALUE

    def ping_unit(self):
        """Ping the PicoScope.

        This function can be used to check that the already opened device is still
        connected to the USB port and communication is successful.
        """
        return self.PingUnit(self._handle)

    def run_block(self, pre_trigger=0.0, callback=None, segment_index=0):
        """Start collecting data in block mode.

        All input arguments are ignored for ps2000 and ps3000.

        Parameters
        ----------
        pre_trigger : :class:`float`, optional
            The number of seconds before the trigger event to start acquiring data.
        segment_index : :class:`int`, optional
            Specifies which memory segment to save the data to (see manual).
        callback : :class:`~msl.equipment.resources.picotech.picoscope.callbacks.BlockReady`, optional
            A BlockReady callback function.
        """
        if len(self._channels_dict) == 0:
            self.raise_exception('Must call set_channel(...) before starting a run block')

        time_ms = c_int32()
        if self.IS_PS2000 or self.IS_PS3000:
            self.RunBlock(self._handle, self._num_samples, self._timebase_index, self._oversample, byref(time_ms))
        else:
            if pre_trigger < 0:
                self.raise_exception('The pre-trigger value cannot be negative.')

            self._pre_trigger = pre_trigger

            n_pre = int(round(pre_trigger / self._sampling_interval))
            n_post = self._num_samples - n_pre

            if callback is None:
                callback = self.BlockReady(0, '', None)  # a dummy callback

            p_parameter = c_void_p()

            if self.IS_PS4000A or self.IS_PS5000A:
                self.RunBlock(self._handle, n_pre, n_post, self._timebase_index, byref(time_ms),
                              segment_index, callback, byref(p_parameter))
            else:
                self.RunBlock(self._handle, n_pre, n_post, self._timebase_index, self._oversample, byref(time_ms),
                              segment_index, callback, byref(p_parameter))
        return time_ms.value

    def run_streaming(self, pre_trigger=0.0, auto_stop=True, factor=1, ratio_mode='NONE'):
        """Start collecting data in streaming mode.

        This function tells the oscilloscope to start collecting data in streaming mode. When
        data has been collected from the device it is down sampled if necessary and then
        delivered to the application. Call :meth:`~.picoscope_api.PicoScopeApi.get_streaming_latest_values`
        to retrieve the data.

        When a trigger is set, the total number of samples stored in the driver is the sum of
        `max_pre_trigger_samples` and `max_post_trigger_samples`. If `auto_stop` is false then
        this will become the maximum number of samples without down sampling.

        The `ratio_mode` argument is ignored for ps4000 and ps5000.

        Parameters
        ----------
        pre_trigger : :class:`float`, optional
            The number of seconds before the trigger event to start acquiring data.
        auto_stop : :class:`bool`, optional
            A flag that specifies if the streaming should stop when all of
            samples have been captured.
        factor : :class:`int`, optional
            The down-sampling factor that will be applied to the raw data.
        ratio_mode : :class:`enum.IntEnum`, optional
            Which down-sampling mode to use.
        """
        if len(self._channels_dict) == 0:
            self.raise_exception('Must call set_channel(...) before starting a run block')

        if pre_trigger < 0:
            self.raise_exception('The pre-trigger value cannot be negative.')

        self._pre_trigger = pre_trigger

        n_pre = int(round(pre_trigger / self._sampling_interval))  # don't use self._streaming_sampling_interval
        n_post = self._num_samples - n_pre

        interval = self._run_streaming(self._streaming_sampling_interval, self._streaming_time_units,
                                       n_pre, n_post, auto_stop, factor, ratio_mode)

        if interval != self._streaming_sampling_interval:
            time_factor = 10**(3*self._streaming_time_units) * 1e-15
            msg = 'The streaming sampling interval is {0:.6e} seconds, requested {1:.6e} seconds'.\
                format(interval*time_factor, self._streaming_sampling_interval*time_factor)
            self.raise_exception(msg)
        return interval

    def set_channel(self, channel, coupling='dc', scale='10V', offset=0.0, bandwidth='full', enabled=True):
        """Configure a channel.

        This function specifies whether an input channel is to be enabled, its input coupling
        type, voltage range, analog offset and bandwidth limit. Some of the arguments within
        this function have model-specific values. Please consult the manual according to the
        model you have.

        The `bandwidth` argument is only used for ps6000.

        The `offset` and `bandwidth` arguments are ignored for ps2000, ps3000, ps4000 and ps5000.

        Parameters
        ----------
        channel : :class:`enum.IntEnum`
            The channel to be configured
        coupling : :class:`enum.IntEnum`, optional
            The impedance and coupling type.
        scale : :class:`enum.IntEnum`, optional
            The input voltage range.
        offset : :class:`float`, optional
            A voltage to add to the input channel before digitization. The allowable range of
            offsets depends on the input range selected for the channel, as obtained from
            :meth:`.get_analogue_offset`.
        bandwidth : :class:`enum.IntEnum`, optional
            The bandwidth limiter to use.
        enabled : :class:`bool`, optional
            Whether to enable the channel.
        """
        channel = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        coupling = self.convert_to_enum(coupling, self.enCoupling, to_upper=True)
        scale = self.convert_to_enum(scale, self.enRange, prefix='R_', to_upper=True)

        try:  # not all PicoScopes have a BandwidthLimiter enum
            bandwidth = self.convert_to_enum(bandwidth, self.enBandwidthLimiter, prefix='BW_', to_upper=True)
        except:
            bandwidth = None

        if self.IS_PS2000 or self.IS_PS3000 or self.IS_PS4000 or self.IS_PS5000:
            self.SetChannel(self._handle, channel, enabled, coupling, scale)
        elif self.IS_PS6000:
            self.SetChannel(self._handle, channel, enabled, coupling, scale, offset, bandwidth)
        else:
            self.SetChannel(self._handle, channel, enabled, coupling, scale, offset)

        # get the voltage range as a floating-point number
        voltage_range = float(re.findall(r'\d+', scale.name)[0])
        if 'M' in scale.name:
            voltage_range *= 1e-3  # milli volts

        # create/update the PicoScopeChannel in the dictionary
        self._channels_dict[channel.name] = PicoScopeChannel(channel, bool(enabled), coupling, voltage_range,
                                                             offset, bandwidth, self.maximum_value())

    def set_timebase(self, dt, duration, segment_index=0, oversample=0):
        """Set the timebase information.

        The `segment_index` is ignored for ps2000 and ps3000.

        The `oversample` argument is ignored by ps2000a, ps3000a, ps4000a and ps5000a.

        Parameters
        ----------
        dt : :class:`float`
            The sampling interval, in seconds.
        duration : :class:`float`
            The number of seconds to acquire data for.
        segment_index : :class:`int`, optional
            Which memory segment to save the data to.
        oversample : :class:`int`, optional
            The amount of over-sample required.

        Returns
        -------
        :class:`float`
            The sampling interval, i.e. dt.
        :class:`int`
            The number of samples that will be acquired.

        Raises
        ------
        ~msl.equipment.exceptions.PicoTechError
            If the timebase or duration is invalid.
        """
        if len(self._channels_dict) == 0:
            self.raise_exception('Must call set_channel(...) before setting the timebase')

        self._oversample = oversample
        self._timebase_index = int(round(self._get_timebase_index(float(dt))))
        num_samples_requested = int(round(duration/dt))
        if self.IS_PS2000 or self.IS_PS3000:
            ret = self.get_timebase(self._timebase_index, num_samples_requested, oversample)
            self._sampling_interval, self._max_samples, self._time_units = ret
        else:
            ret = self.get_timebase2(self._timebase_index, num_samples_requested, segment_index, oversample)
            self._sampling_interval, self._max_samples = ret

        self._num_samples = int(round(duration/self._sampling_interval))

        # determine the TimeUnits enum from the sample interval
        for unit in enums.PS5000ATimeUnits:
            num_seconds_float = self._sampling_interval / (10 ** (3 * unit.value) * 1e-15)
            if num_seconds_float < 1e9:  # use <9 digits to specify the streaming sampling interval
                self._streaming_sampling_interval = int(round(num_seconds_float))
                self._streaming_time_units = unit
                break

        self._allocate_buffer_memory()

        if abs(dt - self._sampling_interval) / dt > 1e-6:
            self.log_warning('The sampling interval is %.6e seconds, requested %.6e seconds',
                             self._sampling_interval, dt)

        return self._sampling_interval, self._num_samples

    def set_trigger(self, channel, threshold, delay=0.0, direction='rising', timeout=0.1, enable=True):
        """Set up the trigger.

        Parameters
        ----------
        channel : :class:`enum.IntEnum`
            The trigger channel.
        threshold : :class:`float`
            The threshold voltage to signal a trigger event.
        delay : :class:`float`, optional
            The time, in seconds, between the trigger occurring and the first sample.
        direction : :class:`enum.IntEnum`, optional
            The direction in which the signal must move to cause a trigger.
        timeout : :class:`float`, optional
            The time, in seconds, to wait to automatically create a trigger event if no
            trigger event occurs. If `timeout` <= 0 then wait indefinitely for a trigger.
            Only accurate to the nearest millisecond.
        enable : :class:`bool`, optional
            Set to :data:`False` to disable the trigger for this channel.
            Not used for ps2000 or ps3000.
        """
        ch = self.convert_to_enum(channel, self.enChannel, to_upper=True)
        if ch.name not in self._channels_dict:
            msg = "Must call set_channel(channel='{0}', ...) before enabling a trigger with channel {0}".format(ch.name)
            self.raise_exception(msg)

        if self._sampling_interval is None:
            self.raise_exception('Must call set_timebase(...) before setting the trigger')

        if ch == self.enChannel.EXT:
            threshold_adu = int(round(self.EXT_MAX_VALUE * threshold/float(self.EXT_MAX_VOLTAGE)))
        else:
            voltage_offset = self._channels_dict[ch.name].voltage_offset
            adu_per_volt = 1.0/self._channels_dict[ch.name].volts_per_adu
            threshold_adu = int(round(adu_per_volt * (threshold + voltage_offset)))

        delay_ = int(round(delay / self._sampling_interval))
        if delay < 0:
            msg = 'The trigger delay must be >=0 seconds, requested a delay of {} seconds'.format(delay)
            self.raise_exception(msg)
        elif delay_ > self.MAX_DELAY_COUNT:
            msg = 'The maximum allowed trigger delay is {} seconds, ' \
                  'requested a delay of {} seconds'.format(self.MAX_DELAY_COUNT*self._sampling_interval, delay)
            self.raise_exception(msg)

        trig_dir = self.convert_to_enum(direction, self.enThresholdDirection, to_upper=True)
        auto_trigger_ms = int(round(max(0.0, timeout*1e3)))
        return self.SetSimpleTrigger(self._handle, enable, ch, threshold_adu, trig_dir, delay_, auto_trigger_ms)

    def stop(self):
        """Stop the oscilloscope from sampling data.

        If this function is called before a trigger event occurs, then the
        oscilloscope may not contain valid data.
        """
        return self.Stop(self._handle)

    def wait_until_ready(self):
        """Blocking function to wait for the scope to finish acquiring data."""
        while not self.is_ready():
            time.sleep(0.01)

    def set_pulse_width_qualifier(self, conditions, direction, lower, upper, pulse_width_type):
        """
        This function sets up pulse width qualification, which can be used on its own for pulse
        width triggering or combined with other triggering to produce more complex triggers.
        The pulse width qualifier is set by defining a list of ``PwqConditions`` structures,
        which are found in the :mod:`~msl.equipment.resources.picotech.picoscope.structs`
        module.
        """
        return self.SetPulseWidthQualifier(self._handle, byref(conditions), len(conditions),
                                           direction, lower, upper, pulse_width_type)
