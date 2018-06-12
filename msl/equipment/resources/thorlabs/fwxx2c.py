"""
Wrapper around Thorlabs ``FilterWheel102.dll``, v4.0.0.

Thorlabs FW102C Series and FW212C Series Motorized Filter Wheels.
"""
from ctypes import c_char_p, c_int, POINTER, byref, create_string_buffer
from enum import IntEnum

from msl.equipment.resources import register
from msl.equipment.exceptions import ThorlabsError
from msl.equipment.connection_sdk import ConnectionSDK

ERROR_CODES = {
    0x00: ('SUCCESS', 'Function call successful.'),
    0xEA: ('CMD_NOT_DEFINED', 'Command not defined.'),
    0xEB: ('TIME_OUT', 'Operation timed out.'),
    0xEC: ('TIME_OUT', 'Operation timed out.'),
    0xED: ('INVALID_STRING_BUFFER', 'Invalid string buffer.'),
}


class FilterCount(IntEnum):
    """The number of filter positions that the filter wheel has."""
    SIX = 6
    TWELVE = 12


class SensorMode(IntEnum):
    """Sensor modes of the filter wheel."""
    ON = 0
    OFF = 1


class SpeedMode(IntEnum):
    """Speed modes of the filter wheel."""
    SLOW = 0
    FAST = 1


class TriggerMode(IntEnum):
    """Trigger modes of the filter wheel."""
    INPUT = 0  #: Respond to an active-low pulse by advancing the position by 1
    OUTPUT = 1  #: Generate an active-high pulse when the position changes


@register(manufacturer='Thorlabs', model='FW(10|21)2C')
class FilterWheelXX2C(ConnectionSDK):

    def __init__(self, record):
        """Wrapper around Thorlabs ``FilterWheel102.dll``, v4.0.0.

        Connects to the Thorlabs FW102C Series and FW212C Series Motorized Filter Wheels.
        
        A 64-bit version of the library can be download from here_ and it is 
        located in **AppNotes_FW102C/LabVIEW/Thorlabs_FW102C/Library/FilterWheel102_win64.dll**.

        The :obj:`~msl.equipment.record_types.ConnectionRecord.properties`
        for a FilterWheelXX2C connection supports the following key-value pairs in the
        :ref:`connection_database`::

            'port': str,  # mandatory, example 'COM3'
            'baud_rate': int,  # optional, default is 115200 
            'timeout': int,  # optional, default is 10
        
        .. _here:
            https://www.thorlabs.com/software_pages/viewsoftwarepage.cfm?code=FW102C&viewtab=2

        Do not instantiate this class directly. Use the :meth:`~.EquipmentRecord.connect`
        method to connect to the equipment.

        Parameters
        ----------
        record : :class:`~msl.equipment.record_types.EquipmentRecord`
            A record from an :ref:`equipment_database`.

        Raises
        ------
        :exc:`.ThorlabsError`
            If a connection to the filter wheel cannot be established.
        """
        self._handle = None
        ConnectionSDK.__init__(self, record, 'cdll')
        self.set_exception_class(ThorlabsError)

        self.sdk.GetPorts.restype = c_int
        self.sdk.GetPorts.argtypes = [c_char_p]
        self.sdk.GetPorts.errcheck = self.errcheck_negative
        self.sdk.Open.restype = c_int
        self.sdk.Open.argtypes = [c_char_p, c_int, c_int]
        self.sdk.Open.errcheck = self.errcheck_negative
        self.sdk.IsOpen.restype = c_int
        self.sdk.IsOpen.argtypes = [c_char_p]
        self.sdk.IsOpen.errcheck = self.log_errcheck
        self.sdk.Close.restype = c_int
        self.sdk.Close.argtypes = [c_int]
        self.sdk.Close.errcheck = self.errcheck_negative
        # the SetTimeout function is in the header file but it is not exported to the DLL
        # self.sdk.SetTimeout.restype = c_int
        # self.sdk.SetTimeout.argtypes = [c_int, c_int]
        # self.sdk.SetTimeout.errcheck = self.errcheck_non_zero
        self.sdk.SetPosition.restype = c_int
        self.sdk.SetPosition.argtypes = [c_int, c_int]
        self.sdk.SetPosition.errcheck = self.errcheck_code
        self.sdk.SetPositionCount.restype = c_int
        self.sdk.SetPositionCount.argtypes = [c_int, c_int]
        self.sdk.SetPositionCount.errcheck = self.errcheck_code
        self.sdk.SetSpeed.restype = c_int
        self.sdk.SetSpeed.argtypes = [c_int, c_int]
        self.sdk.SetSpeed.errcheck = self.errcheck_code
        self.sdk.SetTriggerMode.restype = c_int
        self.sdk.SetTriggerMode.argtypes = [c_int, c_int]
        self.sdk.SetTriggerMode.errcheck = self.errcheck_code
        self.sdk.SetMinVelocity.restype = c_int
        self.sdk.SetMinVelocity.argtypes = [c_int, c_int]
        self.sdk.SetMinVelocity.errcheck = self.errcheck_code
        self.sdk.SetMaxVelocity.restype = c_int
        self.sdk.SetMaxVelocity.argtypes = [c_int, c_int]
        self.sdk.SetMaxVelocity.errcheck = self.errcheck_code
        self.sdk.SetAcceleration.restype = c_int
        self.sdk.SetAcceleration.argtypes = [c_int, c_int]
        self.sdk.SetAcceleration.errcheck = self.errcheck_code
        self.sdk.SetSensorMode.restype = c_int
        self.sdk.SetSensorMode.argtypes = [c_int, c_int]
        self.sdk.SetSensorMode.errcheck = self.errcheck_code
        self.sdk.Save.restype = c_int
        self.sdk.Save.argtypes = [c_int]
        self.sdk.Save.errcheck = self.errcheck_code
        self.sdk.GetPosition.restype = c_int
        self.sdk.GetPosition.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetPosition.errcheck = self.errcheck_code
        self.sdk.GetPositionCount.restype = c_int
        self.sdk.GetPositionCount.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetPositionCount.errcheck = self.errcheck_code
        self.sdk.GetSpeed.restype = c_int
        self.sdk.GetSpeed.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetSpeed.errcheck = self.errcheck_code
        self.sdk.GetTriggerMode.restype = c_int
        self.sdk.GetTriggerMode.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetTriggerMode.errcheck = self.errcheck_code
        self.sdk.GetMinVelocity.restype = c_int
        self.sdk.GetMinVelocity.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetMinVelocity.errcheck = self.errcheck_code
        self.sdk.GetMaxVelocity.restype = c_int
        self.sdk.GetMaxVelocity.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetMaxVelocity.errcheck = self.errcheck_code
        self.sdk.GetAcceleration.restype = c_int
        self.sdk.GetAcceleration.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetAcceleration.errcheck = self.errcheck_code
        self.sdk.GetSensorMode.restype = c_int
        self.sdk.GetSensorMode.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetSensorMode.errcheck = self.errcheck_code
        self.sdk.GetTimeToCurrentPos.restype = c_int
        self.sdk.GetTimeToCurrentPos.argtypes = [c_int, POINTER(c_int)]
        self.sdk.GetTimeToCurrentPos.errcheck = self.errcheck_code
        self.sdk.GetId.restype = c_int
        self.sdk.GetId.argtypes = [c_int, c_char_p]
        self.sdk.GetId.errcheck = self.errcheck_code

        baud = record.connection.properties.get('baud_rate', 115200)
        timeout = record.connection.properties.get('timeout', 10)
        port = record.connection.properties.get('port', None)

        if port is None:
            msg = 'You must specify the port, e.g. port=COM3, in the Properties field of the Connections database'
            self.raise_exception(msg)

        ports = self.get_ports()
        if port not in ports:
            self.raise_exception('Invalid port {}. Available ports: {}'.format(port, ', '.join(ports.keys())))

        self.open(port, baud, timeout)
        self._max_position = int(self.get_position_count())

    def close(self):
        """Close the opened COM port."""
        if self._handle is not None:
            self.sdk.Close(self._handle)
            self._handle = None

    def disconnect(self):
        """Close the opened COM port."""
        self.close()

    def errcheck_code(self, result, func, arguments):
        """The SDK function returns OK if the function call was successful."""
        self.log_errcheck(result, func, arguments)
        if result != 0:
            self.raise_exception('{}: {}'.format(*ERROR_CODES[result]))
        return result

    def errcheck_negative(self, result, func, arguments):
        """The SDK function returns a positive number if the call was successful."""
        self.log_errcheck(result, func, arguments)
        if result < 0:
            self.raise_exception('FW102C_ERROR: Function call not successful.')
        return result

    def errcheck_non_zero(self, result, func, arguments):
        """The SDK function returns 0 if the call was successful."""
        self.log_errcheck(result, func, arguments)
        if result != 0:
            self.raise_exception('FW102C_ERROR: Function call not successful.')
        return result

    def get_acceleration(self):
        """
        Returns
        -------
        :obj:`int`
            The current acceleration value of the filter wheel.
        """
        acceleration = c_int()
        self.sdk.GetAcceleration(self._handle, byref(acceleration))
        return acceleration.value

    def get_id(self):
        """        
        Returns
        -------
        :obj:`str`
            The id of the filter wheel.
        """
        identity = create_string_buffer(256)
        self.sdk.GetId(self._handle, identity)
        return identity.raw.decode()

    def get_max_velocity(self):
        """
        Returns
        -------
        :obj:`int`
            The current maximum velocity value of the filter wheel.
        """
        velocity = c_int()
        self.sdk.GetMaxVelocity(self._handle, byref(velocity))
        return velocity.value

    def get_min_velocity(self):
        """
        Returns
        -------
        :obj:`int`
            The current minimum velocity value of the filter wheel.
        """
        velocity = c_int()
        self.sdk.GetMinVelocity(self._handle, byref(velocity))
        return velocity.value

    def get_ports(self):
        """List all the COM ports on the computer.
        
        Returns
        -------
        :obj:`dict` of :obj:`str`
            A dictionary where the keys are the port numbers, e.g. COM1, COM3,
            and the values are a description about each device connected to the 
            port.
        """
        ports_ptr = create_string_buffer(256)
        self.sdk.GetPorts(ports_ptr)
        ports_list = ports_ptr.raw.decode().rstrip('\x00').rstrip(',').split(',')
        ports = {}
        for i in range(0, len(ports_list), 2):
            ports[ports_list[i]] = ports_list[i+1]
        return ports

    def get_position(self):
        """        
        Returns
        -------
        :obj:`int`
            The current position of the filter wheel.
        """
        pos = c_int()
        self.sdk.GetPosition(self._handle, byref(pos))
        return pos.value

    def get_position_count(self):
        """
        Returns
        -------
        :class:`.FilterCount`
            The number of filter positions that the filter wheel has.
        """
        count = c_int()
        self.sdk.GetPositionCount(self._handle, byref(count))
        return FilterCount(count.value)

    def get_sensor_mode(self):
        """
        Returns
        -------
        :class:`.SensorMode`
            The current sensor mode of the filter wheel. 
        """
        mode = c_int()
        self.sdk.GetSensorMode(self._handle, byref(mode))
        return SensorMode(mode.value)

    def get_speed_mode(self):
        """
        Returns
        -------
        :class:`.SpeedMode`
            The current speed mode of the filter wheel. 
        """
        mode = c_int()
        self.sdk.GetSpeed(self._handle, byref(mode))
        return SpeedMode(mode.value)

    def get_time_to_current_pos(self):
        """
        Returns
        -------
        :obj:`int`
            The time from last position to current position.
        """
        time = c_int()
        self.sdk.GetTimeToCurrentPos(self._handle, byref(time))
        return time.value

    def get_trigger_mode(self):
        """
        Returns
        -------
        :class:`.TriggerMode`
            The current trigger mode of the filter wheel.
        """
        mode = c_int()
        self.sdk.GetTriggerMode(self._handle, byref(mode))
        return TriggerMode(mode.value)

    def is_open(self, port):
        """Check if the COM port is open.

        Parameters
        ----------
        port : :obj:`str`
            The port to be checked, e.g. ``COM3``.

        Returns
        -------
        :obj:`bool`
            :obj:`True` if the port is opened; :obj:`False` if the port is closed.
        """
        return bool(self.sdk.IsOpen(port.encode()))

    def open(self, port, baud_rate, timeout):
        """Open a COM port for communication.
        
        Parameters
        ----------
        port : :obj:`str`
            The port to be opened, use the :meth:`get_ports` 
            function to get a list of available ports.
        baud_rate : :obj:`int`
            The number of bits per second to use for the communication protocol.        
        timeout : :obj:`int`
            Set the timeout value, in seconds. 
        """
        if self._handle is None:
            self._handle = self.sdk.Open(port.encode(), baud_rate, timeout)

    def save(self):
        """Save the current settings as the default settings on power up."""
        self.sdk.Save(self._handle)

    def set_acceleration(self, acceleration):
        """Set the filter wheel's acceleration.

        Parameters
        ----------
        acceleration : :obj:`int`
            The filter wheel's acceleration value.
        """
        self.sdk.SetAcceleration(self._handle, acceleration)

    def set_max_velocity(self, maximum):
        """Set the filter wheel's maximum velocity.

        Parameters
        ----------
        maximum : :obj:`int`
            The filter wheel's maximum velocity value.
        """
        self.sdk.SetMaxVelocity(self._handle, maximum)

    def set_min_velocity(self, minimum):
        """Set the filter wheel's minimum velocity.

        Parameters
        ----------
        minimum : :obj:`int`
            The filter wheel's minimum velocity value.
        """
        self.sdk.SetMinVelocity(self._handle, minimum)

    def set_position(self, position):
        """Set the filter wheel's position.
        
        Parameters
        ----------
        position : :obj:`int`
           The position number to set the filter wheel to.

        Raises
        ------
        ValueError
            If the value of `position` is invalid.
        """
        if position < 1 or position > self._max_position:
            msg = 'Invalid position of {}. Must be 1 <= position <= {}'.format(position, self._max_position)
            raise ValueError(msg)
        self.sdk.SetPosition(self._handle, position)

    def set_position_count(self, count):
        """Set the filter wheel's position count.
        
        This is the number of filter positions that the filter wheel has. 

        Parameters
        ----------
        count : :class:`.FilterCount`
            The number of filters in the filter wheel as a :class:`.FilterCount`
            enum value or member name.
        
        Raises
        ------
        ValueError
            If the value of `count` is invalid.
        """
        c = self.convert_to_enum(count, FilterCount, to_upper=True)
        self.sdk.SetPositionCount(self._handle, c)
        self._max_position = int(c)

    def set_sensor_mode(self, mode):
        """Set the filter wheel's sensor mode.

        Parameters
        ----------
        mode : :class:`.SensorMode`
            The filter wheel's sensor mode as a :class:`.SensorMode`
            enum value or member name.

        Raises
        ------
        ValueError
            If the value of `mode` is invalid.
        """
        m = self.convert_to_enum(mode, SensorMode, to_upper=True)
        self.sdk.SetSensorMode(self._handle, m)

    def set_speed_mode(self, mode):
        """Set the filter wheel's speed mode.
 
        Parameters
        ----------
        mode : :class:`.SpeedMode`
            The speed mode of the filter wheel as a :class:`SpeedMode`
            enum value or member name.
        
        Raises
        ------
        ValueError
            If the value of `mode` is invalid.
        """
        m = self.convert_to_enum(mode, SpeedMode, to_upper=True)
        self.sdk.SetSpeed(self._handle, m)

    def set_trigger_mode(self, mode):
        """Set the filter wheel's trigger mode.

        Parameters
        ----------
        mode : :class:`.TriggerMode`
            The filter wheel's trigger mode as a :class:`TriggerMode`
            enum value or member name.            
        
        Raises
        ------
        ValueError
            If the value of `mode` is invalid.
        """
        m = self.convert_to_enum(mode, TriggerMode, to_upper=True)
        self.sdk.SetTriggerMode(self._handle, m)

    # def set_timeout(self, timeout):
    #     """Set the filter wheel's timeout value.
    #
    #     Parameters
    #     ----------
    #     timeout : :obj:`int`
    #         The timeout value, in seconds.
    #     """
    #     self.sdk.SetTimeout(self._handle, timeout)


if __name__ == '__main__':
    from msl.equipment.resources.utils import CHeader, camelcase_to_underscore

    header = CHeader(r'C:\Users\j.borbely\Desktop\AppNotes_FW102C_v400\AppNotes_FW102C\msvc\fw_cmd_library.h')
    fcns = header.functions(r'DllExport\s+(\w+)\s+(\w+)')

    for key, value in fcns.items():
        print('        self.sdk.{name}.restype = {res}'.format(name=key, res=value[0]))
        print('        self.sdk.{name}.argtypes = [{args}]'.format(
            name=key, args=', '.join([item[0] for item in value[1] if item[0] is not None])))
        print('        self.sdk.{name}.errcheck = self.errcheck_code'.format(name=key))

    print()

    for key, value in fcns.items():
        args_p = [camelcase_to_underscore(item[1]) for item in value[1]
                  if item[0] is not None and not item[0].startswith('POINTER') and item[1] != 'hdl']
        args_c = [camelcase_to_underscore(item[1]) for item in value[1]]
        pointers = [[camelcase_to_underscore(item[1]), item[0]] for item in value[1]
                    if item[0] is not None and item[0].startswith('POINTER')]
        if args_p:
            print('    def {}(self, {}):'.format(camelcase_to_underscore(key), ', '.join(args_p)))
            for p in pointers:
                print('        {} = {}()'.format(p[0], p[1][8:-1]))
            if not pointers:
                print('        return self.sdk.{}({})'.format(key, ', '.join(args_c).replace('hdl', 'self._handle')))
            else:
                print('        ret = self.sdk.{}({})'.format(key, ', '.join(args_c).replace('hdl', 'self._handle')))
                print('        return ret, {}.value'.format('.value, '.join(p[0] for p in pointers)))
        else:
            print('    def {}(self):'.format(camelcase_to_underscore(key), ', '.join(args_p)))
            print('        return self.sdk.{}(self._handle)'.format(key))
        print()
