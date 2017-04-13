"""
Base class for PicoScopes from Pico Technology.
"""
import os
import re
import time
import logging
from ctypes import c_int8, c_int16, c_int32, c_uint32, byref, c_void_p, string_at, addressof
c_enum = c_uint32

from msl.loadlib import IS_WINDOWS, LoadLibrary

from msl.equipment.connection_msl import ConnectionSDK
from .channel import PicoScopeChannel
from .errors import PicoScopeError
from . import structs
from . import enums
from . import callbacks

picoscope_logger = logging.getLogger(__name__)

ALLOWED_SDKs = ('ps2000', 'ps2000a', 'ps3000', 'ps3000a', 'ps4000', 'ps4000a', 'ps5000', 'ps5000a', 'ps6000')


def enumerate_units():
    """
    This function counts the number of PicoScopes connected to the
    computer, and returns a list of serial numbers as a string.
    
    It seems as though you cannot call this function after you have 
    opened a connection to a PicoScope.
    """
    count = c_int16()
    serials = c_int8()
    serial_length = c_int16(4096)
    libtype = 'windll' if IS_WINDOWS else 'cdll'
    sdk = LoadLibrary('ps5000a', libtype)
    result = sdk.lib.ps5000aEnumerateUnits(byref(count), byref(serials), byref(serial_length))
    if result != 0:
        msg = 'Cannot enumerate units. This function does not function properly if ' \
              'you opened a connection to a PicoScope already'
        raise PicoScopeError(msg)
    return string_at(addressof(serials)).decode('utf-8').strip().split(',')


class PicoScope(ConnectionSDK):

    def __init__(self, record, func_ptrs):
        """
        Use the PicoScope SDK to communicate with the oscilloscope.

        Do not instantiate this class directly. Use :func:`msl.equipment.factory.connect`
        or :meth:`record.connect() <msl.equipment.record_types.EquipmentRecord.connect>`
        to connect to the equipment.
        
        The :class:`ConnectionRecord.properties <msl.equipment.record_types.ConnectionRecord.properties>`
        dictionary supports the following:
        
        {
        'open_unit': bool,  # the default is True 
         'open_unit_async': bool,  # The default is False
         'resolution': '8bit',  # only valid for ps5000a
         'auto_select_power': bool  # for PicoScopes that can be powered by an AC adaptor or a USB cable
        }
        
        The SDK version that was initially used to create this base class and the PicoScope
        subclasses was *Pico Technology SDK 64-bit v10.6.10.24*

        Args:
            record (:class:`~msl.equipment.record_types.EquipmentRecord`): An equipment 
                record (a row) from the :class:`~msl.equipment.database.Database`.
            
            func_ptrs: The appropriate function-pointer list from :mod:`.picoscope_functions`
        """
        self._handle = None
        libtype = 'windll' if IS_WINDOWS else 'cdll'
        ConnectionSDK.__init__(self, record, libtype)

        # check that the Python class matches the SDK
        self.SDK_FILENAME = os.path.splitext(os.path.basename(record.connection.address.split('::')[2]))[0]
        if self.SDK_FILENAME != self.__class__.__name__.replace('PicoScope', 'ps').lower():
            msg = 'Using the wrong PicoScope SDK file {} for {}.'.format(self.SDK_FILENAME, self.__class__.__name__)
            self.raise_exception(msg)

        if self.SDK_FILENAME not in ALLOWED_SDKs:
            msg = "Invalid SDK '{}'\nMust be one of {}".format(self.SDK_FILENAME, ALLOWED_SDKs)
            raise PicoScopeError(msg)

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
        self._base_msg = 'PicoScope<model={}, serial={}>\n'.format(conn.model, conn.serial)

        self.log.debug('Connected to {}'.format(self.equipment_record.connection))

    def convert_to_enum(self, member, enum, prefix=None):
        """
        Get the ``enum`` value from ``value``.
        
        Args:
            member (int, str): If :py:class:`str` then the name of the enum member. 
                If :py:class:`int` then the value of the enum member.
                
            enum (IntEnum): An integer enum object
             
            prefix (str): A prefix to include with the ``enum_name``, for example 'R_' for a 
                Range(IntEnum).
        """
        if member is None:
            member = 'NONE'

        if isinstance(member, int):
            try:
                return enum(member)
            except ValueError:
                msg = 'Invalid value {} in {}. Must be one of {}'.format(member, enum, list(map(int, enum)))
                self.raise_exception(msg)

        if not isinstance(member, str):
            msg = 'The parameter must either be an enum name (as a string) or an enum value (as an integer)'
            self.raise_exception('{} -> {}. Got {} as {}'.format(enum, msg, member, type(member)))

        upper = member.upper().replace(' ', '_')
        if prefix is not None and not upper.startswith(prefix):
            upper = prefix + upper

        if upper in enum.__members__:
            return enum[upper]
        else:
            msg = "Invalid name '{}' in {}. Must be one of {}".format(upper, enum, list(enum.__members__))
            self.raise_exception(msg)

    @property
    def handle(self):
        """
        Returns the handle to the SDK library.
        """
        return self._handle

    @property
    def log(self):
        """The :py:mod:`logger <logging>` to use for all PicoScopes."""
        return picoscope_logger

    @property
    def channel(self):
        return self._channels_dict

    @property
    def dt(self):
        """
        :py:class:`float`: The time between voltage samples (i.e., delta t).
        """
        return self._sampling_interval

    def allocate_buffer_memory(self):
        # allocate memory for the numpy array for each channel
        for channel in self._channels_dict.values():
            if channel.enabled:
                channel.allocate(self._num_captures, self._num_samples)

    def close_unit(self):
        """Shutdown the PicoScope."""
        return self.disconnect()

    def disconnect(self):
        """Shutdown the PicoScope."""
        if self._handle is not None:
            ret = self.CloseUnit(self._handle)
            self.log.debug('Disconnected from {}'.format(self.equipment_record.connection))
            self._handle = None
            return ret

        # # Loading the SDK creates "Pipe_inOut" and "Pipe_inOutFifo" files, delete them.
        # # The files cannot be deleted without unloading the PicoScope shared library first.
        # # http://stackoverflow.com/questions/21770419/free-the-opened-ctypes-library-in-python
        # import os
        # import _ctypes
        # if IS_WINDOWS:
        #     _ctypes.FreeLibrary(self.sdk._handle)
        # else:
        #     _ctypes.dlclose(self.sdk._handle)
        # for filename in ('Pipe_inOut', 'Pipe_inOutFifo'):
        #     try:
        #         os.remove(os.path.join(os.getcwd(), filename))
        #     except:
        #         pass

    def get_unit_info(self, info=None, include_name=True):
        """
        This function retrieves information about the specified oscilloscope. If the device 
        fails to open, or no device is opened only the driver version is available.

        Args:
            info (:class:`~.picoscope_enums.PicoScopeInfo`, optional): An enum value, or if 
                :py:data:`None` then request all information from the PicoScope.

            include_name (bool): If :py:data:`True` then includes the enum member name as a prefix.
                For example, return ``CAL_DATE: 09Aug16`` if :py:data:`True` else ``09Aug16``.

        Returns:
            :py:class:`str`: The requested information from the PicoScope.
        """
        if info is None:
            values = [self.enPicoScopeInfo(i) for i in range(len(self.enPicoScopeInfo))]
        else:
            values = [self.convert_to_enum(info, self.enPicoScopeInfo)]

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
        """
        This function may be used instead of a callback function to receive data from
        :meth:`run_block`. To use this method, pass a NULL pointer as the lpReady
        argument to :meth:`run_block`. You must then poll the driver to see if it has finished
        collecting the requested samples.
        """
        return self._is_ready()

    def maximum_value(self):
        """
        This function returns the maximum ADC count.
        """
        try:
            max_value = c_int16()
            self.MaximumValue(self._handle, byref(max_value))
            return max_value.value
        except AttributeError:
            return self.MAX_VALUE

    def minimum_value(self):
        """
        This function returns the minimum ADC count.
        """
        try:
            min_value = c_int16()
            self.MinimumValue(self._handle, byref(min_value))
            return min_value.value
        except AttributeError:
            return self.MIN_VALUE

    def ping_unit(self):
        """
        This function can be used to check that the already opened device is still 
        connected to the USB port and communication is successful.
        """
        return self.PingUnit(self._handle)

    def run_block(self, pre_trigger=0.0, callback=None, segment_index=0):
        """
        Starts collecting data in block mode.
        
        All input arguments are ignored for ps2000 and ps3000.
        
        Args:
            pre_trigger (float): The number of seconds before the trigger event to start acquiring data.
            segment_index (int): Specifies which memory segment to save the data to (see manual).
            callback: A ``BlockReady`` callback. Not working yet, keep None.
        """
        if len(self._channels_dict) == 0:
            self.raise_exception('Must call set_channel(...) before starting a run block')

        time_ms = c_int32()
        if self.IS_PS2000 or self.IS_PS3000:
            self.RunBlock(self._handle, self._num_samples, self._timebase_index, self._oversample, byref(time_ms))
        else:
            if pre_trigger < 0:
                self.raise_exception('The pre-trigger value cannot be negative.')

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

    def run_streaming(self, pre_trigger=0.0, auto_stop=True, factor=1, ratio_mode=None):
        """
        This function tells the oscilloscope to start collecting data in streaming mode. When
        data has been collected from the device it is down sampled if necessary and then
        delivered to the application. Call :meth:`get_streaming_latest_values` to retrieve the
        data. See Using streaming mode for a step-by-step guide to this process.

        When a trigger is set, the total number of samples stored in the driver is the sum of
        ``max_pre_trigger_samples`` and ``max_post_trigger_samples``. If autoStop is false then
        this will become the maximum number of samples without down sampling.

        The ``ratio_mode`` argument is ignored for ps4000 and ps5000.
        """
        if len(self._channels_dict) == 0:
            self.raise_exception('Must call set_channel(...) before starting a run block')

        if pre_trigger < 0:
            self.raise_exception('The pre-trigger value cannot be negative.')

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
        """
        This function specifies whether an input channel is to be enabled, its input coupling
        type, voltage range, analog offset and bandwidth limit. Some of the arguments within
        this function have model-specific values. Please consult the manual according to the 
        model you have.

        The ``bandwidth`` argument is only used for ps6000.

        The ``offset`` and ``bandwidth`` arguments are ignored for ps2000, ps3000, ps4000 and ps5000.
        """
        channel = self.convert_to_enum(channel, self.enChannel)
        coupling = self.convert_to_enum(coupling, self.enCoupling)
        scale = self.convert_to_enum(scale, self.enRange, 'R_')

        try:  # not all PicoScopes have a BandwidthLimiter enum
            bandwidth = self.convert_to_enum(bandwidth, self.enBandwidthLimiter, 'BW_')
        except PicoScopeError:
            bandwidth = None

        if self.IS_PS2000 or self.IS_PS3000 or self.IS_PS4000 or self.IS_PS5000:
            self.SetChannel(self._handle, channel, enabled, coupling, scale)
        elif self.IS_PS6000:
            self.SetChannel(self._handle, channel, enabled, coupling, scale, offset, bandwidth)
        else:
            self.SetChannel(self._handle, channel, enabled, coupling, scale, offset)

        # get the voltage range as a floating-point number
        voltage_range = float(re.findall('\d+', scale.name)[0])
        if 'M' in scale.name:
            voltage_range *= 1e-3  # milli volts

        # create/update the PicoScopeChannel in the dictionary
        self._channels_dict[channel.name] = PicoScopeChannel(channel, enabled, coupling, voltage_range,
                                                             offset, bandwidth, self.maximum_value())

    def set_timebase(self, dt, duration, segment_index=0, oversample=0):
        """
        Set the timebase information.
        
        The ``segment_index`` is ignored for ps2000 and ps3000.
        
        The ``oversample`` argument is ignored by ps2000a, ps3000a, ps4000a and ps5000a.
        
        Args:
            dt (float): The sampling interval, in seconds. 
            duration (float): The number of seconds to acquire data.  
            segment_index (int): Which memory segment to save the data to.
            oversample (int): The amount of oversample required.

        Raises:
            PicoScopeError: If the timebase or duration is invalid.
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
            num_seconds_float = dt / (10 ** (3 * unit.value) * 1e-15)
            if num_seconds_float < 1e9:  # use <9 digits to specify the streaming sampling interval
                self._streaming_sampling_interval = int(round(num_seconds_float))
                self._streaming_time_units = unit
                break

        self.allocate_buffer_memory()

        if abs(dt - self._sampling_interval) / dt > 1e-6:
            msg = 'The sampling interval is {0:.6e} seconds, requested {1:.6e} seconds'\
                .format(self._sampling_interval, dt)
            self.log.warning(msg)

        return self._sampling_interval, self._num_samples

    def set_trigger(self, channel, threshold, delay=0.0, direction='rising', timeout=0.1, enable=True):
        """
        Set up the trigger.
        
        Args:
            channel (str, int): The trigger channel.
            threshold (float): The threshold voltage to signal a trigger event.
            delay (float): The time, in seconds, between the trigger occurring and the first sample.
            direction (str, int): The direction in which the signal must move to cause a trigger. 
            timeout (float): The time, in seconds, to wait to automatically create a trigger event if no 
                trigger event occurs. If ``timeout <= 0`` then wait indefinitely for a trigger. Only accurate 
                to the nearest millisecond. 
            enable (bool): Set to :py:data:`False` to disable the trigger for this channel. 
                Not used for ps2000 or ps3000.
        """
        ch = self.convert_to_enum(channel, self.enChannel)
        if ch.name not in self._channels_dict:
            msg = "Must call set_channel(channel='{0}', ...) before enabling a trigger with channel {0}".format(ch.name)
            self.raise_exception(msg)

        if self._sampling_interval is None:
            self.raise_exception('Must call set_timebase(...) before setting the trigger')

        if ch == self.enChannel.EXT:
            threshold_adu = round(self.EXT_MAX_VALUE * threshold/float(self.EXT_MAX_VOLTAGE))
        else:
            voltage_offset = self._channels_dict[ch.name].voltage_offset
            adu_per_volt = 1.0/self._channels_dict[ch.name].volts_per_adu
            threshold_adu = round(adu_per_volt * (threshold + voltage_offset))

        delay_ = round(delay / self._sampling_interval)
        if delay < 0:
            msg = 'The trigger delay must be >=0 seconds, requested a delay of {} seconds'.format(delay)
            self.raise_exception(msg)
        elif delay_ > self.MAX_DELAY_COUNT:
            msg = 'The maximum allowed trigger delay is {} seconds, ' \
                  'requested a delay of {} seconds'.format(self.MAX_DELAY_COUNT*self._sampling_interval, delay)
            self.raise_exception(msg)

        trig_dir = self.convert_to_enum(direction, self.enThresholdDirection)
        auto_trigger_ms = round(max(0, timeout*1e3))
        return self.SetSimpleTrigger(self._handle, enable, ch, threshold_adu, trig_dir, delay_, auto_trigger_ms)

    def stop(self):
        """
        Stop the oscilloscope from sampling data. If this function is called 
        before a trigger event occurs, the oscilloscope may not contain valid data.
        """
        return self.Stop(self._handle)

    def wait_until_ready(self):
        """Blocking function to wait for the scope data to be collected."""
        while not self.is_ready():
            time.sleep(0.01)
